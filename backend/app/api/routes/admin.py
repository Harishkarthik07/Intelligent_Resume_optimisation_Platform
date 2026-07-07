"""
Admin routes for real-time SaaS metrics and dashboard data.
Protected by admin authentication.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta
import logging

from app.core.database import get_db
from app.api.routes.auth import get_current_user
from app.models.models import User, Resume, Analysis
from app.models.metrics import UserMetric, AnalysisMetric, SubscriptionMetric, DailyStats

logger = logging.getLogger(__name__)
router = APIRouter()


def is_admin(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Check if user is admin. For now, check if user_id matches admin ID."""
    # In production, add admin_role to User model
    admin_emails = ["admin@resumeiq.com", "rhak19is@cmrit.ac.in"]
    if user.email not in admin_emails:
        raise HTTPException(403, "Admin access required")
    return user


@router.get("/dashboard/realtime")
def get_realtime_stats(db: Session = Depends(get_db), admin=Depends(is_admin)):
    """Get real-time dashboard metrics for admin."""
    
    # Active users in last 24 hours
    last_24h = datetime.utcnow() - timedelta(hours=24)
    active_users = db.query(func.count(func.distinct(UserMetric.user_id))).filter(
        UserMetric.timestamp >= last_24h
    ).scalar() or 0
    
    # Total users
    total_users = db.query(func.count(User.id)).scalar() or 0
    
    # Analyses in last 24h
    analyses_24h = db.query(func.count(Analysis.id)).filter(
        Analysis.created_at >= last_24h
    ).scalar() or 0
    
    # Total resumes
    total_resumes = db.query(func.count(Resume.id)).scalar() or 0
    
    # Average ATS score
    avg_ats = db.query(func.avg(Analysis.ats_score)).scalar() or 0
    
    # Subscriptions
    pro_users = db.query(func.count(SubscriptionMetric.id)).filter(
        SubscriptionMetric.plan == "pro"
    ).scalar() or 0
    
    enterprise_users = db.query(func.count(SubscriptionMetric.id)).filter(
        SubscriptionMetric.plan == "enterprise"
    ).scalar() or 0
    
    free_users = total_users - pro_users - enterprise_users
    
    return {
        "timestamp": datetime.utcnow().isoformat(),
        "users": {
            "total": total_users,
            "active_24h": active_users,
            "by_plan": {
                "free": free_users,
                "pro": pro_users,
                "enterprise": enterprise_users,
            },
        },
        "usage": {
            "resumes_total": total_resumes,
            "analyses_24h": analyses_24h,
            "avg_ats_score": round(avg_ats, 1),
        },
    }


@router.get("/dashboard/users")
def get_user_metrics(db: Session = Depends(get_db), admin=Depends(is_admin)):
    """Get detailed user metrics."""
    
    # Last 7 days user growth
    last_7d = datetime.utcnow() - timedelta(days=7)
    new_users_7d = db.query(func.count(User.id)).filter(
        User.created_at >= last_7d
    ).scalar() or 0
    
    # Most active users (by analysis count)
    active_users = db.query(
        User.email,
        User.full_name,
        func.count(Analysis.id).label("analysis_count")
    ).outerjoin(Analysis).group_by(User.id).order_by(
        func.count(Analysis.id).desc()
    ).limit(10).all()
    
    return {
        "new_users_7d": new_users_7d,
        "most_active_users": [
            {
                "email": user[0],
                "name": user[1],
                "analyses_run": user[2],
            }
            for user in active_users
        ],
    }


@router.get("/dashboard/analyses")
def get_analysis_metrics(db: Session = Depends(get_db), admin=Depends(is_admin)):
    """Get analysis performance metrics."""
    
    # Analysis distribution by score range
    score_ranges = {
        "excellent": db.query(func.count(Analysis.id)).filter(Analysis.ats_score >= 80).scalar() or 0,
        "good": db.query(func.count(Analysis.id)).filter(
            Analysis.ats_score >= 60, Analysis.ats_score < 80
        ).scalar() or 0,
        "fair": db.query(func.count(Analysis.id)).filter(
            Analysis.ats_score >= 40, Analysis.ats_score < 60
        ).scalar() or 0,
        "needs_work": db.query(func.count(Analysis.id)).filter(
            Analysis.ats_score < 40
        ).scalar() or 0,
    }
    
    # Top matched skills
    all_analyses = db.query(Analysis.matched_skills).all()
    all_skills = []
    for row in all_analyses:
        if row[0]:
            all_skills.extend(row[0])
    
    from collections import Counter
    skill_counts = Counter(all_skills)
    top_skills = skill_counts.most_common(10)
    
    # Top missing skills
    all_analyses_missing = db.query(Analysis.missing_skills).all()
    missing_skills = []
    for row in all_analyses_missing:
        if row[0]:
            missing_skills.extend(row[0])
    
    missing_counts = Counter(missing_skills)
    top_missing = missing_counts.most_common(10)
    
    return {
        "score_distribution": score_ranges,
        "top_matched_skills": [{"skill": s, "count": c} for s, c in top_skills],
        "top_missing_skills": [{"skill": s, "count": c} for s, c in top_missing],
    }


@router.get("/dashboard/growth")
def get_growth_metrics(db: Session = Depends(get_db), admin=Depends(is_admin)):
    """Get product growth metrics."""
    
    # Daily stats for last 30 days
    last_30d = datetime.utcnow() - timedelta(days=30)
    daily_stats = db.query(DailyStats).filter(
        DailyStats.created_at >= last_30d
    ).order_by(DailyStats.date).all()
    
    # Calculate MoM growth
    total_analyses_30d = sum(s.total_analyses_run for s in daily_stats) if daily_stats else 0
    
    # Last 7 days vs previous 7 days
    last_7d = datetime.utcnow() - timedelta(days=7)
    prev_7d_start = datetime.utcnow() - timedelta(days=14)
    
    current_7d = db.query(func.count(Analysis.id)).filter(
        Analysis.created_at >= last_7d
    ).scalar() or 0
    
    previous_7d = db.query(func.count(Analysis.id)).filter(
        Analysis.created_at >= prev_7d_start,
        Analysis.created_at < last_7d
    ).scalar() or 0
    
    growth_percent = 0
    if previous_7d > 0:
        growth_percent = round(((current_7d - previous_7d) / previous_7d) * 100, 1)
    
    return {
        "total_analyses_30d": total_analyses_30d,
        "analyses_current_week": current_7d,
        "analyses_previous_week": previous_7d,
        "growth_percent": growth_percent,
        "daily_stats": [
            {
                "date": s.date,
                "analyses": s.total_analyses_run,
                "active_users": s.total_active_users,
            }
            for s in daily_stats
        ],
    }


@router.get("/dashboard/revenue")
def get_revenue_metrics(db: Session = Depends(get_db), admin=Depends(is_admin)):
    """Get subscription and revenue metrics."""
    
    subscriptions = db.query(
        SubscriptionMetric.plan,
        func.count(SubscriptionMetric.id).label("count")
    ).group_by(SubscriptionMetric.plan).all()
    
    plan_breakdown = {plan: count for plan, count in subscriptions}
    
    # Calculate MRR (Mock - in production, use actual payment data)
    mrr = (
        plan_breakdown.get("free", 0) * 0 +
        plan_breakdown.get("pro", 0) * 29 +
        plan_breakdown.get("enterprise", 0) * 199
    )
    
    return {
        "subscriptions": plan_breakdown,
        "mrr": mrr,
        "arpu": round(mrr / max(1, sum(plan_breakdown.values())), 2),
    }


@router.post("/track-event")
def track_user_event(
    event_type: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Track user events for analytics (called by frontend)."""
    try:
        metric = UserMetric(
            user_id=user.id,
            event_type=event_type,
            metadata=str(request.headers.get("user-agent", ""))[:500],
        )
        db.add(metric)
        db.commit()
        return {"status": "tracked"}
    except Exception as e:
        logger.error(f"Event tracking failed: {e}")
        return {"status": "error"}
