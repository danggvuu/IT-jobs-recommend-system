from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime

# --- Auth ---
class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    phone: Optional[str] = None

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class UserProfile(BaseModel):
    id: int
    email: str
    full_name: Optional[str]
    phone: Optional[str]
    desired_position: Optional[str]
    desired_location: Optional[str]
    desired_level: Optional[str]
    desired_salary: Optional[float]
    years_experience: Optional[int]
    created_at: datetime
    last_login: Optional[datetime]

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserProfile

# --- CV ---
class CVResponse(BaseModel):
    cv_id: int
    original_filename: str
    extracted_text: Optional[str] = None
    detected_skills: Optional[list[str]] = None
    word_count: Optional[int] = 0
    file_type: str
    is_primary: bool
    created_at: datetime

# --- Recommend ---
class RecommendRequest(BaseModel):
    cv_text: Optional[str] = None
    cv_id: Optional[int] = None
    location_filter: Optional[str] = None
    level_filter: Optional[str] = None
    salary_min_filter: Optional[float] = None
    top_k: int = 10

class JobResult(BaseModel):
    rank: int
    score: float
    job_id: str
    title: str
    company_name: str
    salary_min: Optional[float] = None
    salary_max: Optional[float] = None
    location: str
    level: str
    platforms: List[str]
    url: Optional[str] = None

class RecommendResponse(BaseModel):
    jobs: List[JobResult]
    total: int
    query_time_ms: float
    search_id: int

# --- History ---
class SearchHistoryItem(BaseModel):
    search_id: int
    cv_filename: Optional[str] = None
    filters: dict
    top_score: Optional[float] = None
    result_count: int
    query_time_ms: Optional[float] = None
    created_at: datetime
