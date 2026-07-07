"""
Real-time metrics and analytics for SaaS product monitoring.
Tracks: active users, analyses run, subscriptions, feature usage.
"""
from sqlalchemy import Column, String, Integer, Float, DateTime, Boolean, Text
from sqlalchemy.sql import func
from app.core.database import Base
import uuid
from datetime import datetime


class UserMetric(Base):
    """Real-time user activity tracking."""
    __tablename__ = "user_metrics"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, index=True)
    event_type = Column(String)  # "login", "upload", "analyze", "optimize", "download"
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    event_metadata = Column(Text)  # JSON: browser, ip, device type, etc.


class AnalysisMetric(Base):
    """Analysis performance tracking."""
    __tablename__ = "analysis_metrics"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    analysis_id = Column(String, index=True)
    user_id = Column(String, index=True)
    resume_word_count = Column(Integer)
    jd_word_count = Column(Integer)
    ats_score = Column(Integer)
    keyword_score = Column(Integer)
    semantic_score = Column(Float)
    quality_score = Column(Integer)
    processing_time_ms = Column(Integer)  # How long analysis took
    optimizer_used = Column(Boolean, default=False)
    optimizer_time_ms = Column(Integer, nullable=True)
    pdf_generated = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)


class SubscriptionMetric(Base):
    """Subscription and pricing metrics."""
    __tablename__ = "subscription_metrics"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, unique=True, index=True)
    plan = Column(String)  # "free", "pro", "enterprise"
    analyses_this_month = Column(Integer, default=0)
    analyses_limit = Column(Integer)  # Free: 5, Pro: 50, Enterprise: unlimited
    ai_optimizations_this_month = Column(Integer, default=0)
    ai_optimizations_limit = Column(Integer)
    template_used = Column(String, nullable=True)  # Which template user used
    started_at = Column(DateTime, default=datetime.utcnow)
    last_active_at = Column(DateTime, default=datetime.utcnow)


class DailyStats(Base):
    """Daily aggregated statistics for dashboard."""
    __tablename__ = "daily_stats"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    date = Column(String, unique=True, index=True)  # YYYY-MM-DD
    
    # User stats
    total_active_users = Column(Integer, default=0)
    new_users = Column(Integer, default=0)
    returning_users = Column(Integer, default=0)
    
    # Usage stats
    total_resumes_uploaded = Column(Integer, default=0)
    total_analyses_run = Column(Integer, default=0)
    total_optimizations_run = Column(Integer, default=0)
    total_pdfs_generated = Column(Integer, default=0)
    
    # Performance stats
    avg_ats_score = Column(Float, default=0)
    avg_processing_time_ms = Column(Float, default=0)
    
    # Revenue (if applicable)
    pro_users = Column(Integer, default=0)
    enterprise_users = Column(Integer, default=0)
    
    created_at = Column(DateTime, default=datetime.utcnow)
