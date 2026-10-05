from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
import os
import uuid
import pickle
from backend.api.deps import get_db, get_current_user
from backend.api.models.database import User, CV
from backend.api.models.schemas import CVResponse
from backend.config import UPLOAD_DIR
from backend.ml.cv_parser import parse_cv

router = APIRouter(prefix="/api/v1/cvs", tags=["cv"])

# Load skill_vocab
skill_vocab = {}
try:
    with open("database/skill_vocab.pkl", "rb") as f:
        skill_vocab = pickle.load(f)
except Exception:
    print("Warning: Could not load skill_vocab.pkl")

@router.post("/upload", response_model=CVResponse)
async def upload_cv(
    file: UploadFile = File(...), 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    ext = file.filename.rsplit(".", 1)[-1].lower()
    if ext not in ("pdf", "docx", "jpg", "jpeg", "png"):
        raise HTTPException(status_code=400, detail="Chỉ hỗ trợ PDF, DOCX, JPG, PNG")
        
    file_bytes = await file.read()
    if len(file_bytes) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File quá lớn (>10MB)")
        
    user_dir = os.path.join(UPLOAD_DIR, f"user_{current_user.id}")
    os.makedirs(user_dir, exist_ok=True)
    
    file_id = str(uuid.uuid4())
    file_path = os.path.join(user_dir, f"{file_id}.{ext}")
    
    with open(file_path, "wb") as f:
        f.write(file_bytes)
        
    try:
        parsed = parse_cv(file_bytes, file.filename, skill_vocab)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Lỗi extract file: {str(e)}")
        
    is_primary = db.query(CV).filter(CV.user_id == current_user.id, CV.is_primary == True).count() == 0
    
    new_cv = CV(
        user_id=current_user.id,
        original_filename=file.filename,
        file_path=file_path,
        file_size_bytes=len(file_bytes),
        file_type=ext,
        extracted_text=parsed["extracted_text"],
        detected_skills=parsed["detected_skills"],
        word_count=parsed["word_count"],
        is_primary=is_primary,
        is_processed=True
    )
    db.add(new_cv)
    db.commit()
    db.refresh(new_cv)
    
    return CVResponse(
        cv_id=new_cv.id, original_filename=new_cv.original_filename,
        extracted_text=new_cv.extracted_text, detected_skills=new_cv.detected_skills,
        word_count=new_cv.word_count, file_type=new_cv.file_type,
        is_primary=new_cv.is_primary, created_at=new_cv.created_at
    )
