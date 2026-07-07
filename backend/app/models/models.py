from sqlalchemy import (
    Column, String, Integer, Float, Boolean, DateTime, Text,
    ForeignKey, JSON, Enum as SAEnum
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
import uuid
import enum


def gen_uuid():
    return str(uuid.uuid4())


class UserStatus(str, enum.Enum):
    PENDING   = "pending"    # email not verified
    ACTIVE    = "active"
    SUSPENDED = "suspended"


class User(Base):
    __tablename__ = "users"

    id           = Column(String(36), primary_key=True, default=gen_uuid)
    email        = Column(String(255), unique=True, nullable=False, index=True)
    hashed_pw    = Column(String(255), nullable=False)
    full_name    = Column(String(255))
    status       = Column(SAEnum(UserStatus), default=UserStatus.PENDING, nullable=False)
    is_verified  = Column(Boolean, default=False, nullable=False)
    created_at   = Column(DateTime(timezone=True), server_default=func.now())
    updated_at   = Column(DateTime(timezone=True), onupdate=func.now())
    last_login   = Column(DateTime(timezone=True))

    resumes   = relationship("Resume",   back_populates="user", cascade="all, delete-orphan")
    analyses  = relationship("Analysis", back_populates="user", cascade="all, delete-orphan")


class Resume(Base):
    __tablename__ = "resumes"

    id           = Column(String(36), primary_key=True, default=gen_uuid)
    user_id      = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    title        = Column(String(255), default="My Resume")
    original_filename = Column(String(255))
    file_path    = Column(String(500))       # stored on disk / S3
    raw_text     = Column(Text, nullable=False)
    word_count   = Column(Integer)
    detected_skills = Column(JSON, default=list)
    created_at   = Column(DateTime(timezone=True), server_default=func.now())

    user      = relationship("User",     back_populates="resumes")
    analyses  = relationship("Analysis", back_populates="resume", cascade="all, delete-orphan")


class Analysis(Base):
    __tablename__ = "analyses"

    id                  = Column(String(36), primary_key=True, default=gen_uuid)
    user_id             = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    resume_id           = Column(String(36), ForeignKey("resumes.id"), nullable=False)

    jd_text             = Column(Text, nullable=False)
    jd_title            = Column(String(255))

    ats_score           = Column(Integer)
    keyword_score       = Column(Integer)
    semantic_score      = Column(Float)
    score_label         = Column(String(50))

    matched_skills      = Column(JSON, default=list)
    missing_skills      = Column(JSON, default=list)
    required_skills     = Column(JSON, default=list)

    ai_insights         = Column(Text)
    optimized_resume    = Column(Text)
    optimized_pdf_path  = Column(String(500))

    created_at          = Column(DateTime(timezone=True), server_default=func.now())

    user   = relationship("User",   back_populates="analyses")
    resume = relationship("Resume", back_populates="analyses")
