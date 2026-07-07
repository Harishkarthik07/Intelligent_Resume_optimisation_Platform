from pydantic import BaseModel, EmailStr, field_validator
from typing import Literal, Optional, List
from datetime import datetime


# ─── Auth ─────────────────────────────────────────────────────────────────────

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: str

    @field_validator("password")
    @classmethod
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters.")
        return v

    @field_validator("full_name")
    @classmethod
    def validate_name(cls, v):
        if len(v.strip()) < 2:
            raise ValueError("Full name must be at least 2 characters.")
        return v.strip()


class OTPVerifyRequest(BaseModel):
    email: EmailStr
    otp: str


class ResendOTPRequest(BaseModel):
    email: EmailStr


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user_id: str
    email: str
    full_name: str
    is_verified: bool


class RefreshRequest(BaseModel):
    refresh_token: str


# ─── User ─────────────────────────────────────────────────────────────────────

class UserOut(BaseModel):
    id: str
    email: str
    full_name: Optional[str]
    is_verified: bool
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


# ─── Resume ───────────────────────────────────────────────────────────────────

class ResumeOut(BaseModel):
    id: str
    title: str
    original_filename: Optional[str]
    word_count: Optional[int]
    detected_skills: List[str]
    created_at: datetime

    class Config:
        from_attributes = True


# ─── Analysis ─────────────────────────────────────────────────────────────────

class AnalysisRequest(BaseModel):
    resume_id: str
    jd_text: str
    jd_title: Optional[str] = None

    @field_validator("jd_text")
    @classmethod
    def validate_jd(cls, v):
        if len(v.strip()) < 50:
            raise ValueError("Job description is too short (min 50 characters).")
        return v.strip()


class AnalysisOut(BaseModel):
    id: str
    resume_id: str
    jd_title: Optional[str]
    ats_score: Optional[int]
    keyword_score: Optional[int]
    semantic_score: Optional[float]
    score_label: Optional[str]
    matched_skills: List[str]
    missing_skills: List[str]
    required_skills: List[str]
    ai_insights: Optional[str]
    optimized_resume: Optional[str]
    has_optimized_pdf: bool
    created_at: datetime

    class Config:
        from_attributes = True

    @classmethod
    def from_orm_extended(cls, obj):
        d = {
            "id": obj.id,
            "resume_id": obj.resume_id,
            "jd_title": obj.jd_title,
            "ats_score": obj.ats_score,
            "keyword_score": obj.keyword_score,
            "semantic_score": obj.semantic_score,
            "score_label": obj.score_label,
            "matched_skills": obj.matched_skills or [],
            "missing_skills": obj.missing_skills or [],
            "required_skills": obj.required_skills or [],
            "ai_insights": obj.ai_insights,
            "optimized_resume": obj.optimized_resume,
            "has_optimized_pdf": bool(obj.optimized_pdf_path),
            "created_at": obj.created_at,
        }
        return cls(**d)


class OptimizeRequest(BaseModel):
    analysis_id: str


# ─── ATS Score Engine ─────────────────────────────────────────────────────────

class ATSScoreRequest(BaseModel):
    resume_text: str
    jd_text: str

    @field_validator("resume_text", "jd_text")
    @classmethod
    def validate_text(cls, v):
        return (v or "").strip()


class CategoryScore(BaseModel):
    category: str
    score: int
    color: Literal["green", "yellow", "red"]


class Recommendation(BaseModel):
    priority: Literal["high", "medium"]
    text: str
    border_color: str


class ATSScoreResult(BaseModel):
    overall_score: int
    grade: Literal["Excellent", "Strong", "Good", "Needs Improvement"]
    matched_keywords: List[str]
    partial_keywords: List[str]
    missing_keywords: List[str]
    category_scores: List[CategoryScore]
    recommendations: List[Recommendation]
    summary: str


# ─── Health ───────────────────────────────────────────────────────────────────

class HealthResponse(BaseModel):
    status: str
    version: str
    environment: str
    database: str
    redis: str
    timestamp: str
