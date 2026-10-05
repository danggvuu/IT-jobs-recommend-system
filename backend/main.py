from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.ml.recommender import JobRecommender
from backend.api.routes import auth, upload, recommend, user, jobs, analytics

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Loading Job Recommender...")
    try:
        app.state.recommender = JobRecommender()
        print("Model loaded successfully!")
    except Exception as e:
        print(f"Error loading model: {e}")
        app.state.recommender = None
    yield
    print("Shutting down...")

app = FastAPI(title="IT Job Recommender API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # For dev
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(upload.router)
app.include_router(recommend.router)
app.include_router(user.router)
app.include_router(jobs.router)
app.include_router(analytics.router)

@app.get("/api/v1/health")
def health_check():
    return {
        "status": "ok",
        "model_loaded": app.state.recommender is not None
    }

if __name__ == "__main__":
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
