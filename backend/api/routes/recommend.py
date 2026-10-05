from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
import time
from backend.api.deps import get_db, get_current_user
from backend.api.models.database import User, CV, SearchHistory
from backend.api.models.schemas import RecommendRequest, RecommendResponse, JobResult

router = APIRouter(prefix="/api/v1/recommend", tags=["recommend"])

@router.post("", response_model=RecommendResponse)
async def recommend_jobs(
    req: RecommendRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    start_time = time.time()
    cv_text = req.cv_text
    
    if req.cv_id:
        cv = db.query(CV).filter(CV.id == req.cv_id, CV.user_id == current_user.id).first()
        if not cv:
            raise HTTPException(status_code=404, detail="CV không tồn tại")
        cv_text = cv.extracted_text
        
    if not cv_text:
        raise HTTPException(status_code=400, detail="Vui lòng cung cấp cv_text hoặc cv_id hợp lệ")
        
    recommender = request.app.state.recommender
    res_df = recommender.recommend_from_cv_text(
        cv_text=cv_text,
        top_k=req.top_k,
        location_filter=req.location_filter,
        level_filter=req.level_filter,
        salary_min_filter=req.salary_min_filter
    )
    
    jobs_list = []
    for _, row in res_df.iterrows():
        jobs_list.append(JobResult(
            rank=int(row['rank']),
            score=float(row['score']),
            job_id=str(row['job_id']),
            title=str(row['title']),
            company_name=str(row['company_name']),
            salary_min=float(row['salary_min']) if not pd.isna(row['salary_min']) else None,
            salary_max=float(row['salary_max']) if not pd.isna(row['salary_max']) else None,
            location=str(row['location']),
            level=str(row['level']),
            platforms=row['platforms'] if isinstance(row['platforms'], list) else [],
            url=str(row['url']) if 'url' in row and not pd.isna(row['url']) else None
        ))
        
    query_time_ms = (time.time() - start_time) * 1000
    
    # Save search history
    history = SearchHistory(
        user_id=current_user.id,
        cv_id=req.cv_id,
        query_text=cv_text[:5000], # Trucate if too long
        location_filter=req.location_filter,
        level_filter=req.level_filter,
        salary_filter=req.salary_min_filter,
        top_k=req.top_k,
        results_json=[j.dict() for j in jobs_list],
        top_score=jobs_list[0].score if jobs_list else 0.0,
        result_count=len(jobs_list),
        query_time_ms=query_time_ms
    )
    db.add(history)
    db.commit()
    db.refresh(history)
    
    return RecommendResponse(
        jobs=jobs_list,
        total=len(jobs_list),
        query_time_ms=query_time_ms,
        search_id=history.id
    )

import pandas as pd # Ensure pandas is available
