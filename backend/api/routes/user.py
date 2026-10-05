from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.api.deps import get_db, get_current_user
from backend.api.models.database import User, CV, SearchHistory, SavedJob
from backend.api.models.schemas import UserProfile, CVResponse, SearchHistoryItem
from pydantic import BaseModel

router = APIRouter(prefix="/api/v1/user", tags=["user"])

class ProfileUpdate(BaseModel):
    full_name: str = None
    phone: str = None
    desired_position: str = None
    desired_location: str = None
    desired_level: str = None
    desired_salary: float = None
    years_experience: int = None

@router.put("/profile", response_model=UserProfile)
def update_profile(req: ProfileUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    for key, value in req.dict(exclude_unset=True).items():
        setattr(current_user, key, value)
    db.commit()
    db.refresh(current_user)
    return current_user

@router.get("/my-cvs")
def get_my_cvs(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    cvs = db.query(CV).filter(CV.user_id == current_user.id).order_by(CV.created_at.desc()).all()
    res = []
    for cv in cvs:
        res.append(CVResponse(
            cv_id=cv.id, original_filename=cv.original_filename,
            extracted_text=cv.extracted_text, detected_skills=cv.detected_skills,
            word_count=cv.word_count, file_type=cv.file_type,
            is_primary=cv.is_primary, created_at=cv.created_at
        ))
    return res

@router.get("/my-history")
def get_my_history(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    history = db.query(SearchHistory).filter(SearchHistory.user_id == current_user.id).order_by(SearchHistory.created_at.desc()).limit(50).all()
    res = []
    for h in history:
        cv_name = h.cv.original_filename if h.cv else None
        res.append(SearchHistoryItem(
            search_id=h.id, cv_filename=cv_name,
            filters={"location": h.location_filter, "level": h.level_filter, "salary": h.salary_filter},
            top_score=h.top_score, result_count=h.result_count,
            query_time_ms=h.query_time_ms, created_at=h.created_at
        ))
    return {"searches": res, "total": len(res)}
