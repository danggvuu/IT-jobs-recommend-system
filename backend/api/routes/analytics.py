from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from sqlalchemy import func
from backend.api.deps import get_db
from backend.api.models.database import Job, User, SearchHistory

router = APIRouter(prefix="/api/v1/analytics", tags=["analytics"])

@router.get("/summary")
def get_summary(db: Session = Depends(get_db)):
    total_jobs = db.query(func.count(Job.job_id)).scalar()
    total_users = db.query(func.count(User.id)).scalar()
    total_searches = db.query(func.count(SearchHistory.id)).scalar()
    
    return {
        "total_jobs": total_jobs,
        "total_users": total_users,
        "total_searches": total_searches
    }
