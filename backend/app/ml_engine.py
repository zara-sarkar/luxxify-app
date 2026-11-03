import os
import pickle
import pandas as pd
from ortools.linear_solver import pywraplp
from app.database import get_product_data

MODEL_PATH = os.getenv("MODEL_PATH", "models/random_forest_model.pkl")

# Load model into memory when server starts
with open(MODEL_PATH, "rb") as f:
    model = pickle.load(f)

def run_recommendations_pipeline(req):
    # 1. Build user profile feature vector
    user_profile = {
        'professional_review': 1 if 'Working Professional' in req.lifestyle_options else 0,
        'vibe_review': 1 if 'Retired' in req.lifestyle_options or req.age_range in ['40-50', '50+'] else 0,
        'redness_review': 1 if req.conditions.get('Redness/Rosacea', False) else 0,
        'dry_review': 1 if req.skin_type == 'Dry' else 0.5 if req.skin_type == 'Combination' else 0,
        'light_coverage_review': 1 if req.coverage == 'Light' else 0,
        'young_review': 1 if req.age_range in ['Under 20', '20-30'] or 'Student' in req.lifestyle_options else 0,
        'mother_review': 1 if 'Mom/Parent' in req.lifestyle_options else 0,
        'skin_concerns_review': 1 if any(req.conditions.values()) else 0,
        'white_review': 1 if req.selected_skin_tone == 'Light' else 0,
        'tan_review': 1 if req.selected_skin_tone == 'Medium' else 0,
        'acne_review': 1 if req.conditions.get('Acne', False) or req.skin_type == 'Oily' else 0.5 if req.skin_type == 'Combination' else 0,
        'black_review': 1 if req.selected_skin_tone == 'Deep' else 0,
        'comfortable_wear_review': 1 if 'Working Professional' in req.lifestyle_options or req.active_options == '3 - Super Busy/Active' else 0.5 if req.active_options == '2 - Moderately Busy/Active' else 0,
        'coverage_review': 0 if req.coverage in ['Medium', 'Full'] else 1,
        'medium_coverage_review': 1 if req.coverage == 'Medium' else 0,
        'full_coverage_review': 1 if req.coverage == 'Full' else 0,
        'easy_use_review': 1 if req.experience_level == 'Beginner' else 0,
        'wrinkles_review': 1 if req.conditions.get('Wrinkles', False) else 0,
    }

    # 2. Retrieve data from Postgres on OCI
    product_data, product_info = get_product_data()

    product_copy = product_data.copy().drop(columns=['product_link_id', 'overall_product_rating'], errors='ignore')

    for col, val in user_profile.items():
        product_copy[col] = val

    # 3. Predict scores
    feature_names = model.feature_names_in_
    X = product_copy[feature_names]
    predictions = model.predict_proba(X)
    
    product_data['predicted_score'] = (
        predictions[:, 0] + 2 * predictions[:, 1] + 3 * predictions[:, 2] 
        + 4 * predictions[:, 3] + 5 * predictions[:, 4]
    )

    # 4. Merge product info
    product_budget = pd.merge(product_data, product_info, how='inner', on='product_link_id')

    # 5. Define Category Restrictions based on user features
    skin_categories = ['Foundation', 'Tinted Moisturizer', 'BB & CC Creams']
    allowed_skin_categories = []
    allowed_makeup_products = []

    if user_profile['light_coverage_review']:
        allowed_makeup_products = ['Blush', 'Concealer', 'Makeup Remover', 'Setting Spray & Powder']
        if user_profile['easy_use_review']:
            allowed_skin_categories = ['Foundation', 'Tinted Moisturizer']
        elif user_profile['acne_review']:
            allowed_skin_categories = ['Foundation', 'BB & CC Creams']
        elif user_profile['comfortable_wear_review']:
            allowed_skin_categories = ['Tinted Moisturizer', 'BB & CC Creams']
        else: 
            allowed_skin_categories = ['Foundation', 'Tinted Moisturizer', 'BB & CC Creams']
    elif user_profile['medium_coverage_review']:
        allowed_makeup_products = ['Face Primer', 'Blush', 'Bronzer', 'Concealer', 'Makeup Remover', 'Setting Spray & Powder']
        allowed_skin_categories = ['Foundation', 'BB & CC Creams']
    elif user_profile['full_coverage_review']:
        allowed_makeup_products = ['Face Primer', 'Blush', 'Bronzer', 'Contouring', 'Highlighter', 'Color Correcting', 'Concealer', 'Makeup Remover', 'Setting Spray & Powder']
        allowed_skin_categories = ['Foundation']

    # 6. OR-Tools Optimization Solver
    solver = pywraplp.Solver.CreateSolver('SCIP')
    if not solver:
        return []

    product_vars = {i: solver.BoolVar(f'p_{row["product_link_id"]}') for i, row in product_budget.iterrows()}

    # Budget Constraint
    for i, row in product_budget.iterrows():
        c = solver.Constraint(0, req.max_budget)
        c.SetCoefficient(product_vars[i], float(row['price']))

    # Category Constraints
    categories = product_budget['category_name'].unique()
    allowed_skin_constraint = solver.Constraint(0, 1)
    disallowed_constraint = solver.Constraint(0, 0)

    for cat in allowed_skin_categories:
        for i, row in product_budget[product_budget['category_name'] == cat].iterrows():
            allowed_skin_constraint.SetCoefficient(product_vars[i], 1)

    for cat in skin_categories:
        if cat not in allowed_skin_categories:
            for i, row in product_budget[product_budget['category_name'] == cat].iterrows():
                disallowed_constraint.SetCoefficient(product_vars[i], 1)

    for cat in categories:
        if cat not in allowed_makeup_products and cat not in allowed_skin_categories:
            for i, row in product_budget[product_budget['category_name'] == cat].iterrows():
                disallowed_constraint.SetCoefficient(product_vars[i], 1)

    for cat in categories:
        if cat not in skin_categories and cat in allowed_makeup_products:
            cat_constraint = solver.Constraint(0, 1)
            for i, row in product_budget[product_budget['category_name'] == cat].iterrows():
                cat_constraint.SetCoefficient(product_vars[i], 1)

    # Objective
    objective = solver.Objective()
    for i, row in product_budget.iterrows():
        objective.SetCoefficient(product_vars[i], float(row['predicted_score']))
    objective.SetMaximization()

    status = solver.Solve()

    # 7. Format output list
    selected = []
    if status == pywraplp.Solver.OPTIMAL:
        for i, row in product_budget.iterrows():
            if product_vars[i].solution_value() == 1:
                selected.append({
                    "category": row['category_name'],
                    "product_name": row['product_name'],
                    "price": f"${float(row['price']):,.2f}",
                    "url": row['product_link']
                })

    return selected