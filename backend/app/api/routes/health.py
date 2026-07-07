from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import datetime
import logging

from app.core.database import get_db
from app.core.redis_client import get_redis
from app.core.config import settings

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/health")
def health_check(db: Session = Depends(get_db)):
    """Comprehensive health check for load balancer / monitoring."""
    checks = {
        "status": "ok",
        "version": "1.0.0",
        "environment": settings.APP_ENV,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "database": "unknown",
        "redis": "unknown",
    }

    # Database check
    try:
        db.execute(text("SELECT 1"))
        checks["database"] = "ok"
    except Exception as e:
        checks["database"] = f"error: {e}"
        checks["status"] = "degraded"
        logger.error(f"Health check DB failed: {e}")

    # Redis check
    try:
        r = get_redis()
        if r:
            r.ping()
            checks["redis"] = "ok"
        else:
            checks["redis"] = "unavailable (in-memory fallback active)"
    except Exception as e:
        checks["redis"] = f"error: {e}"
        logger.warning(f"Health check Redis failed: {e}")

    return checks


@router.get("/health/live")
def liveness():
    """Kubernetes liveness probe — just checks process is alive."""
    return {"status": "alive"}


@router.get("/health/ready")
def readiness(db: Session = Depends(get_db)):
    """Kubernetes readiness probe — checks DB connectivity."""
    try:
        db.execute(text("SELECT 1"))
        return {"status": "ready"}
    except Exception as e:
        from fastapi import HTTPException
        raise HTTPException(503, f"Not ready: {e}")
