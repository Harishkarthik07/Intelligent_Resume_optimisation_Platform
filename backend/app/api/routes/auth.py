from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from datetime import datetime
import logging

from app.core.database import get_db
from app.core.security import (
    hash_password, verify_password,
    create_access_token, create_refresh_token, decode_token,
    generate_otp,
)
from app.core.redis_client import OTPStore
from app.models.models import User, UserStatus
from app.schemas.schemas import (
    RegisterRequest, OTPVerifyRequest, ResendOTPRequest,
    LoginRequest, TokenResponse, RefreshRequest, UserOut,
)
from app.services.email_service import email_service

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(req: RegisterRequest, db: Session = Depends(get_db)):
    """Register a new user and send OTP for email verification."""
    existing = db.query(User).filter(User.email == req.email.lower()).first()
    if existing:
        if existing.is_verified:
            raise HTTPException(400, "Email already registered.")
        # Resend OTP for unverified accounts
        otp = generate_otp()
        OTPStore.set(req.email.lower(), otp, ttl_seconds=600)
        email_service.send_otp(req.email, existing.full_name or req.full_name, otp)
        return {"message": "Account exists but unverified. New OTP sent to your email.", "email": req.email}

    user = User(
        email=req.email.lower(),
        hashed_pw=hash_password(req.password),
        full_name=req.full_name,
        status=UserStatus.PENDING,
        is_verified=False,
    )
    db.add(user)
    db.commit()

    otp = generate_otp()
    OTPStore.set(req.email.lower(), otp, ttl_seconds=600)
    sent = email_service.send_otp(req.email, req.full_name, otp)

    logger.info(f"User registered: {req.email} (email_sent={sent})")
    return {
        "message": "Registration successful. Please check your email for the OTP.",
        "email": req.email,
        "email_sent": sent,
    }


@router.post("/verify-otp")
def verify_otp(req: OTPVerifyRequest, db: Session = Depends(get_db)):
    """Verify email OTP and activate account."""
    user = db.query(User).filter(User.email == req.email.lower()).first()
    if not user:
        raise HTTPException(404, "User not found.")
    if user.is_verified:
        raise HTTPException(400, "Email already verified.")

    # Check OTP attempts
    attempts = OTPStore.increment_attempts(req.email.lower())
    if attempts > 5:
        raise HTTPException(429, "Too many OTP attempts. Please request a new OTP.")

    stored_otp = OTPStore.get(req.email.lower())
    if not stored_otp:
        raise HTTPException(400, "OTP has expired. Please request a new one.")
    if stored_otp != req.otp.strip():
        raise HTTPException(400, f"Invalid OTP. Attempts remaining: {max(0, 5 - attempts)}")

    user.is_verified = True
    user.status = UserStatus.ACTIVE
    db.commit()
    OTPStore.delete(req.email.lower())

    logger.info(f"Email verified: {req.email}")
    return {"message": "Email verified successfully. You can now log in."}


@router.post("/resend-otp")
def resend_otp(req: ResendOTPRequest, db: Session = Depends(get_db)):
    """Resend OTP to email."""
    user = db.query(User).filter(User.email == req.email.lower()).first()
    if not user:
        raise HTTPException(404, "User not found.")
    if user.is_verified:
        raise HTTPException(400, "Email already verified.")

    otp = generate_otp()
    OTPStore.set(req.email.lower(), otp, ttl_seconds=600)
    sent = email_service.send_otp(req.email, user.full_name or "", otp)
    return {"message": "OTP resent.", "email": req.email, "email_sent": sent}


@router.post("/login", response_model=TokenResponse)
def login(req: LoginRequest, db: Session = Depends(get_db)):
    """Authenticate user and return JWT tokens."""
    user = db.query(User).filter(User.email == req.email.lower()).first()
    if not user or not verify_password(req.password, user.hashed_pw):
        raise HTTPException(401, "Invalid email or password.")
    if not user.is_verified:
        raise HTTPException(403, "Email not verified. Please verify your OTP first.")
    if user.status == UserStatus.SUSPENDED:
        raise HTTPException(403, "Account suspended. Contact support.")

    user.last_login = datetime.utcnow()
    db.commit()

    access  = create_access_token(user.id)
    refresh = create_refresh_token(user.id)

    logger.info(f"User logged in: {user.email}")
    return TokenResponse(
        access_token=access,
        refresh_token=refresh,
        user_id=user.id,
        email=user.email,
        full_name=user.full_name or "",
        is_verified=user.is_verified,
    )


@router.post("/refresh", response_model=TokenResponse)
def refresh_token(req: RefreshRequest, db: Session = Depends(get_db)):
    """Refresh JWT access token."""
    try:
        payload = decode_token(req.refresh_token)
    except ValueError as e:
        raise HTTPException(401, str(e))

    if payload.get("type") != "refresh":
        raise HTTPException(401, "Invalid token type.")

    user = db.query(User).filter(User.id == payload["sub"]).first()
    if not user or not user.is_verified:
        raise HTTPException(401, "User not found or not verified.")

    access  = create_access_token(user.id)
    refresh = create_refresh_token(user.id)
    return TokenResponse(
        access_token=access,
        refresh_token=refresh,
        user_id=user.id,
        email=user.email,
        full_name=user.full_name or "",
        is_verified=user.is_verified,
    )


@router.get("/me", response_model=UserOut)
def me(request: Request, db: Session = Depends(get_db)):
    """Get current user info."""
    user = _get_current_user(request, db)
    return user


# ─── Dependency ───────────────────────────────────────────────────────────────

def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    return _get_current_user(request, db)


def _get_current_user(request: Request, db: Session) -> User:
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        raise HTTPException(401, "Missing or invalid Authorization header.")
    token = auth.split(" ", 1)[1]
    try:
        payload = decode_token(token)
    except ValueError as e:
        raise HTTPException(401, str(e))

    if payload.get("type") != "access":
        raise HTTPException(401, "Invalid token type.")

    user = db.query(User).filter(User.id == payload["sub"]).first()
    if not user:
        raise HTTPException(401, "User not found.")
    if not user.is_verified:
        raise HTTPException(403, "Email not verified.")
    return user
