import os
import pandas as pd
from sqlalchemy import create_engine
from dotenv import load_dotenv

load_dotenv()

DB_USER = os.getenv("DB_USER")
DB_PASS = os.getenv("DB_PASS")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

engine = create_engine(DATABASE_URL)

def get_product_data():
    """Fetches product tables directly from PostgreSQL on OCI."""
    product_data = pd.read_sql("SELECT * FROM reddit_product_embeddings", engine)
    product_info = pd.read_sql("SELECT * FROM cleaned_makeup_products", engine)
    return product_data, product_info