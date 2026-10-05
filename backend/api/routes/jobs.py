from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from backend.api.deps import get_db
from backend.api.models.database import Job

router = APIRouter(prefix="/api/v1/jobs", tags=["jobs"])

@router.get("")
def get_jobs(page: int = 1, limit: int = 20, location: str = None, level: str = None, keyword: str = None, db: Session = Depends(get_db)):
    query = db.query(Job)
    if location:
        query = query.filter(Job.location.ilike(f"%{location}%"))
    if level:
        query = query.filter(Job.level.ilike(f"%{level}%"))
    if keyword:
        query = query.filter(Job.title.ilike(f"%{keyword}%"))
        
    total = query.count()
    jobs = query.offset((page - 1) * limit).limit(limit).all()
    
    return {
        "total": total,
        "page": page,
        "total_pages": (total + limit - 1) // limit,
        "jobs": jobs
    }

@router.get("/{job_id}")
def get_job(job_id: str, db: Session = Depends(get_db)):
    job = db.query(Job).filter(Job.job_id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job
