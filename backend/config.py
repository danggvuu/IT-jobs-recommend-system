import os

SECRET_KEY = os.getenv("SECRET_KEY", "super-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60
REFRESH_TOKEN_EXPIRE_DAYS = 7
UPLOAD_DIR = os.getenv("UPLOAD_DIR", "backend/uploads/cvs")
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///database/job_market.sqlite")

os.makedirs(UPLOAD_DIR, exist_ok=True)
