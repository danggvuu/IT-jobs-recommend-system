from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text, ForeignKey, JSON, UniqueConstraint
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.sql import func

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    
    id              = Column(Integer, primary_key=True, autoincrement=True)
    email           = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name       = Column(String(255), nullable=True)
    phone           = Column(String(20), nullable=True)
    
    # Profile
    desired_position = Column(String(255), nullable=True)
    desired_location = Column(String(100), nullable=True)
    desired_level    = Column(String(50), nullable=True)
    desired_salary   = Column(Float, nullable=True)
    years_experience = Column(Integer, nullable=True)
    
    # Metadata
    is_active    = Column(Boolean, default=True)
    created_at   = Column(DateTime, default=func.now())
    updated_at   = Column(DateTime, default=func.now(), onupdate=func.now())
    last_login   = Column(DateTime, nullable=True)
    
    # Relationships
    cvs             = relationship("CV", back_populates="user")
    search_history  = relationship("SearchHistory", back_populates="user")
    saved_jobs      = relationship("SavedJob", back_populates="user")


class CV(Base):
    __tablename__ = "cvs"
    
    id              = Column(Integer, primary_key=True, autoincrement=True)
    user_id         = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # File info
    original_filename = Column(String(255), nullable=False)
    file_path         = Column(String(500), nullable=False)
    file_size_bytes   = Column(Integer, nullable=False)
    file_type         = Column(String(10), nullable=False)
    
    # Extracted content
    extracted_text    = Column(Text, nullable=True)
    detected_skills   = Column(JSON, nullable=True)
    word_count        = Column(Integer, nullable=True)
    
    # Status
    is_primary    = Column(Boolean, default=False)
    is_processed  = Column(Boolean, default=False)
    
    created_at    = Column(DateTime, default=func.now())
    updated_at    = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    user          = relationship("User", back_populates="cvs")
    searches      = relationship("SearchHistory", back_populates="cv")


class SearchHistory(Base):
    __tablename__ = "search_history"
    
    id              = Column(Integer, primary_key=True, autoincrement=True)
    user_id         = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    cv_id           = Column(Integer, ForeignKey("cvs.id"), nullable=True)
    
    # Query info
    query_text      = Column(Text, nullable=False)
    location_filter = Column(String(100), nullable=True)
    level_filter    = Column(String(50), nullable=True)
    salary_filter   = Column(Float, nullable=True)
    top_k           = Column(Integer, default=10)
    
    # Results
    results_json    = Column(JSON, nullable=True)
    top_score       = Column(Float, nullable=True)
    result_count    = Column(Integer, nullable=True)
    query_time_ms   = Column(Float, nullable=True)
    
    created_at      = Column(DateTime, default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="search_history")
    cv   = relationship("CV", back_populates="searches")


class SavedJob(Base):
    __tablename__ = "saved_jobs"
    
    id         = Column(Integer, primary_key=True, autoincrement=True)
    user_id    = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    job_id     = Column(String(255), nullable=False, index=True)
    note       = Column(Text, nullable=True)
    saved_at   = Column(DateTime, default=func.now())
    
    user = relationship("User", back_populates="saved_jobs")
    
    __table_args__ = (UniqueConstraint("user_id", "job_id", name="uq_user_job"),)

# Định nghĩa bảng `jobs` để SQLAlchemy nhận dạng, nhưng sẽ không tạo lại (tồn tại sẵn)
class Job(Base):
    __tablename__ = "jobs"
    __table_args__ = {'extend_existing': True}
    
    job_id = Column(String(255), primary_key=True)
    title = Column(String(500))
    company_name = Column(String(500))
    industry = Column(String(255))
    salary = Column(String(255))
    location = Column(String(500))
    experience_required = Column(String(255))
    level = Column(String(255))
    job_status = Column(String(50))
    scraped_at = Column(DateTime)
    url = Column(Text)
    job_description = Column(Text)
    requirements = Column(Text)
    benefits = Column(Text)
    skills = Column(Text)
