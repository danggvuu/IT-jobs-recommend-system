from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from jose import jwt
from datetime import datetime, timedelta
from backend.api.deps import get_db, get_current_user
from backend.api.models.database import User
from backend.api.models.schemas import RegisterRequest, LoginRequest, TokenResponse, UserProfile
from backend.config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES, REFRESH_TOKEN_EXPIRE_DAYS

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def create_access_token(data: dict, expires_delta: timedelta):
    to_encode = data.copy()
    expire = datetime.utcnow() + expires_delta
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

@router.post("/register")
def register(req: RegisterRequest, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == req.email).first():
        raise HTTPException(status_code=400, detail="Email đã tồn tại")
    
    new_user = User(
        email=req.email,
        hashed_password=pwd_context.hash(req.password),
        full_name=req.full_name,
        phone=req.phone
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {"message": "Đăng ký thành công", "user_id": new_user.id}

@router.post("/login", response_model=TokenResponse)
def login(req: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == req.email).first()
    if not user or not pwd_context.verify(req.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Email hoặc mật khẩu không đúng")
        
    user.last_login = datetime.utcnow()
    db.commit()
    
    access_token = create_access_token({"sub": str(user.id)}, timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    refresh_token = create_access_token({"sub": str(user.id)}, timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS))
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user=UserProfile(
            id=user.id, email=user.email, full_name=user.full_name, phone=user.phone,
            desired_position=user.desired_position, desired_location=user.desired_location,
            desired_level=user.desired_level, desired_salary=user.desired_salary,
            years_experience=user.years_experience, created_at=user.created_at, last_login=user.last_login
        )
    )

@router.get("/me", response_model=UserProfile)
def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user
