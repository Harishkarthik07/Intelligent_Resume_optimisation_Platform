"""
ResumeIQ — Intelligent Resume Optimization Platform
Production FastAPI Application Entry Point
"""
import os
import sys
import time
import logging
import uuid
from contextlib import asynccontextmanager
from pathlib import Path

# Allow imports like `from app.core.config import settings` when running
# from the repository root with `uvicorn backend.main:app`.
ROOT_DIR = Path(__file__).resolve().parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.core.config import settings
from app.core.database import init_db
from app.core.logging_config import setup_logging
from app.api.routes import auth, resumes, analysis, health, admin, templates, ats

# Setup logging before anything else
setup_logging(settings.APP_ENV)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # ── Startup ───────────────────────────────────────────────────
    logger.info(f"Starting ResumeIQ API [{settings.APP_ENV}]")
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    os.makedirs(os.path.join(settings.UPLOAD_DIR, "optimized"), exist_ok=True)
    os.makedirs("logs", exist_ok=True)
    init_db()
    logger.info("ResumeIQ API ready.")
    yield
    # ── Shutdown ──────────────────────────────────────────────────
    logger.info("ResumeIQ API shutting down.")


app = FastAPI(
    title="ResumeIQ API",
    description=(
        "Intelligent Resume Optimization Platform — "
        "AI-powered ATS scoring, skill gap analysis, and resume rewriting."
    ),
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    lifespan=lifespan,
)

# ─── Middleware ───────────────────────────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(GZipMiddleware, minimum_size=500)


@app.middleware("http")
async def request_logging_middleware(request: Request, call_next):
    """Log every request with timing and a unique request ID."""
    request_id = str(uuid.uuid4())[:8]
    start = time.time()

    logger.info(
        f"[{request_id}] {request.method} {request.url.path} "
        f"from {request.client.host if request.client else 'unknown'}"
    )

    response: Response = await call_next(request)
    duration_ms = round((time.time() - start) * 1000)

    logger.info(
        f"[{request_id}] {response.status_code} in {duration_ms}ms"
    )
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Response-Time"] = f"{duration_ms}ms"
    return response


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception on {request.url.path}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal server error occurred. Please try again."},
    )


# ─── Routes ───────────────────────────────────────────────────────────────────

app.include_router(health.router,   tags=["Health"])
app.include_router(ats.router,      prefix="/api/ats",          tags=["ATS Score"])
app.include_router(auth.router,     prefix="/api/v1/auth",      tags=["Authentication"])
app.include_router(resumes.router,  prefix="/api/v1/resumes",   tags=["Resumes"])
app.include_router(analysis.router, prefix="/api/v1/analysis",  tags=["Analysis"])
app.include_router(templates.router, prefix="/api/v1/templates", tags=["Templates"])
app.include_router(admin.router,    prefix="/api/v1/admin",     tags=["Admin Dashboard"])

# Serve uploaded files (dev only — use Nginx/S3 in prod)
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
if settings.APP_ENV == "development":
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")


@app.get("/", tags=["Root"])
def root():
    return {
        "service": "ResumeIQ API",
        "version": "1.0.0",
        "docs": "/api/docs",
        "health": "/health",
    }
