from pydantic import BaseModel
from typing import Dict, List

class UserProfileRequest(BaseModel):
    age_range: str
    skin_type: str
    experience_level: str
    coverage: str
    max_budget: float
    selected_skin_tone: str
    conditions: Dict[str, bool]
    lifestyle_options: List[str]
    active_options: str

class ProductResponse(BaseModel):
    category: str
    product_name: str
    price: str
    url: str