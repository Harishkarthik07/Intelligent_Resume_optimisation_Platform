from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Request
from sqlalchemy.orm import Session
import os
import uuid
import logging

from app.core.database import get_db
from app.core.config import settings
from app.models.models import Resume
from app.schemas.schemas import ResumeOut
from app.services.parser import resume_parser
from app.services.ats_engine import extract_skills
from app.api.routes.auth import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter()

ALLOWED_TYPES = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "text/plain",
}

EXTENSION_CONTENT_TYPES = {
    ".pdf": "application/pdf",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ".txt": "text/plain",
}


@router.post("/upload", response_model=ResumeOut, status_code=201)
def upload_resume(
    request: Request,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """Upload a PDF/DOCX/TXT resume. Extracts text and detects skills."""
    current_user = get_current_user(request, db)

    # Validate file type. Some browsers/tools send uploads as octet-stream, so
    # fall back to the extension when the MIME type is generic.
    ext = os.path.splitext(file.filename or "")[1].lower()
    content_type = file.content_type or EXTENSION_CONTENT_TYPES.get(ext)
    if content_type == "application/octet-stream":
        content_type = EXTENSION_CONTENT_TYPES.get(ext, content_type)
    if content_type not in ALLOWED_TYPES:
        raise HTTPException(415, f"Unsupported file type: {file.content_type or ext or 'unknown'}. Use PDF, DOCX, or TXT.")

    # Read and validate size
    file_bytes = file.file.read()
    max_bytes = settings.MAX_FILE_SIZE_MB * 1024 * 1024
    if len(file_bytes) > max_bytes:
        raise HTTPException(413, f"File too large. Max {settings.MAX_FILE_SIZE_MB}MB allowed.")

    # Parse text
    try:
        raw_text = resume_parser.parse(file_bytes, content_type)
    except Exception as e:
        logger.error(f"Parsing failed for {file.filename}: {e}")
        raise HTTPException(422, f"Could not extract text from file: {e}")

    if len(raw_text.strip()) < 50:
        raise HTTPException(422, "Extracted text is too short. Please check the file.")

    # Save file to disk
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    ext = ext or ".txt"
    saved_name = f"{current_user.id}_{uuid.uuid4().hex[:8]}{ext}"
    saved_path = os.path.join(settings.UPLOAD_DIR, saved_name)
    with open(saved_path, "wb") as f:
        f.write(file_bytes)

    # Detect skills
    skills = extract_skills(raw_text)
    word_count = len(raw_text.split())

    resume = Resume(
        user_id=current_user.id,
        title=os.path.splitext(file.filename or "Resume")[0],
        original_filename=file.filename,
        file_path=saved_path,
        raw_text=raw_text,
        word_count=word_count,
        detected_skills=skills,
    )
    db.add(resume)
    db.commit()
    db.refresh(resume)

    logger.info(f"Resume uploaded: {resume.id} by {current_user.email} ({word_count} words, {len(skills)} skills)")
    return resume


@router.get("/", response_model=list[ResumeOut])
def list_resumes(request: Request, db: Session = Depends(get_db)):
    """List all resumes for the current user."""
    current_user = get_current_user(request, db)
    resumes = (
        db.query(Resume)
        .filter(Resume.user_id == current_user.id)
        .order_by(Resume.created_at.desc())
        .all()
    )
    return resumes


@router.get("/{resume_id}", response_model=ResumeOut)
def get_resume(resume_id: str, request: Request, db: Session = Depends(get_db)):
    current_user = get_current_user(request, db)
    resume = db.query(Resume).filter(Resume.id == resume_id, Resume.user_id == current_user.id).first()
    if not resume:
        raise HTTPException(404, "Resume not found.")
    return resume


@router.delete("/{resume_id}", status_code=204)
def delete_resume(resume_id: str, request: Request, db: Session = Depends(get_db)):
    current_user = get_current_user(request, db)
    resume = db.query(Resume).filter(Resume.id == resume_id, Resume.user_id == current_user.id).first()
    if not resume:
        raise HTTPException(404, "Resume not found.")
    # Delete file
    if resume.file_path and os.path.exists(resume.file_path):
        os.remove(resume.file_path)
    db.delete(resume)
    db.commit()
