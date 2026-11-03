from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from typing import List
from app.schemas import UserProfileRequest, ProductResponse
from app.ml_engine import run_recommendations_pipeline

app = FastAPI(title="Makeup Recommendation API")

# Allow React app requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Update to React production domain in prod
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/api/recommendations", response_model=List[ProductResponse])
def get_recommendations(req: UserProfileRequest):
    return run_recommendations_pipeline(req)