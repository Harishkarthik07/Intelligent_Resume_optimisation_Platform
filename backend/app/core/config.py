from pydantic_settings import BaseSettings
from typing import List
import json
import re


class Settings(BaseSettings):
    APP_ENV:  str = "development"
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8000
    SECRET_KEY:   str = "dev-secret-key-change-in-production"
    FRONTEND_URL: str = "http://localhost:3000"

    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS:   int = 7

    DATABASE_URL: str = "postgresql://resumeiq:changeme123@localhost:5432/resumeiq"
    REDIS_URL:    str = "redis://localhost:6379/0"

    # ── AI ──────────────────────────────────────────────────────────────────
    GEMINI_API_KEY: str = ""
    ENABLE_AI_INSIGHTS: bool = False
    ENABLE_TRANSFORMER_SCORING: bool = False

    # ── Email — use ONE of the three options below ──────────────────────────
    # Option 1: Resend (recommended — resend.com, free, no Gmail needed)
    RESEND_API_KEY: str = ""

    # Option 2: Gmail App Password
    SMTP_HOST:     str = "smtp.gmail.com"
    SMTP_PORT:     int = 587
    SMTP_USER:     str = ""
    SMTP_PASSWORD: str = ""

    EMAIL_FROM:      str = "onboarding@resend.dev"   # resend default sender (works without domain)
    EMAIL_FROM_NAME: str = "ResumeIQ"

    # ── Files ────────────────────────────────────────────────────────────────
    UPLOAD_DIR:       str = "./uploads"
    MAX_FILE_SIZE_MB: int = 5

    # ── OTP ──────────────────────────────────────────────────────────────────
    OTP_EXPIRE_MINUTES: int = 10

    # ── CORS ─────────────────────────────────────────────────────────────────
    CORS_ORIGINS: str = '["http://localhost:3000","http://localhost:8080","http://localhost"]'

    @property
    def cors_origins_list(self) -> List[str]:
        origins = []
        try:
            parsed = json.loads(self.CORS_ORIGINS)
            if isinstance(parsed, list):
                origins.extend(str(origin).strip().rstrip("/") for origin in parsed if str(origin).strip())
        except Exception:
            origins.extend(
                origin.strip().rstrip("/")
                for origin in self.CORS_ORIGINS.split(",")
                if origin.strip()
            )

        origins.extend(
            origin.strip().rstrip("/")
            for origin in re.split(r"[\s,]+", self.FRONTEND_URL or "")
            if origin.strip().startswith(("http://", "https://"))
        )

        origins.extend([
            "http://localhost",
            "http://localhost:3000",
            "http://localhost:5500",
            "http://localhost:8080",
            "http://127.0.0.1",
            "http://127.0.0.1:3000",
            "http://127.0.0.1:5500",
            "http://127.0.0.1:8080",
        ])
        return sorted(set(origins))

    # ── Rate limiting ─────────────────────────────────────────────────────────
    AI_CALLS_PER_USER_PER_HOUR: int = 5

    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"


settings = Settings()
