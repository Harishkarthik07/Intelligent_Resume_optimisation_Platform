from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
import os, uuid, logging

from app.core.database import get_db
from app.core.config import settings
from app.models.models import Analysis, Resume
from app.schemas.schemas import AnalysisRequest, AnalysisOut, OptimizeRequest
from app.services.ats_engine import ats_engine, detect_suitable_roles, generate_detailed_analysis
from app.services.ats_score_engine import calculate_ats_score
from app.services.optimizer import gemini_optimizer, RateLimitError
from app.services.pdf_generator import pdf_generator, _parse_resume_sections, rebuild_resume_preserving_order
from app.api.routes.auth import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter()


def _analysis_result_from_score(resume_text: str, jd_text: str) -> dict:
    score = calculate_ats_score(resume_text, jd_text)
    return {
        "ats_score": score["overall_score"],
        "keyword_score": score.get("keyword_score", 0),
        "semantic_score": score.get("semantic_score", 0),
        "score_label": score["grade"],
        "matched_skills": score["matched_keywords"],
        "partial_keywords": score["partial_keywords"],
        "missing_skills": score["missing_keywords"],
        "required_skills": score.get("required_keywords", []),
        "category_scores": score["category_scores"],
        "recommendations": score["recommendations"],
        "summary": score["summary"],
    }


@router.post("/run", status_code=201)
def run_analysis(req: AnalysisRequest, request: Request, db: Session = Depends(get_db)):
    """ATS scoring + Gemini insights. Gemini falls back to rule-based if unavailable."""
    current_user = get_current_user(request, db)

    resume = db.query(Resume).filter(
        Resume.id == req.resume_id,
        Resume.user_id == current_user.id
    ).first()
    if not resume:
        raise HTTPException(404, "Resume not found.")

    logger.info(f"Analysis for {current_user.email}, resume={resume.id}")

    # ATS Scoring — always works, no external API
    ats_result = _analysis_result_from_score(resume.raw_text, req.jd_text)

    # Gemini insights — gracefully falls back to rule-based on any failure
    insights = gemini_optimizer.generate_insights(
        resume.raw_text,
        req.jd_text,
        ats_result["ats_score"],
        matched=ats_result["matched_skills"],
        missing=ats_result["missing_skills"],
    )

    analysis = Analysis(
        user_id=current_user.id,
        resume_id=resume.id,
        jd_text=req.jd_text,
        jd_title=req.jd_title,
        ats_score=ats_result["ats_score"],
        keyword_score=ats_result["keyword_score"],
        semantic_score=ats_result["semantic_score"],
        score_label=ats_result["score_label"],
        matched_skills=ats_result["matched_skills"],
        missing_skills=ats_result["missing_skills"],
        required_skills=ats_result["required_skills"],
        ai_insights=insights,
    )
    db.add(analysis)
    db.commit()
    db.refresh(analysis)

    logger.info(f"Analysis done: id={analysis.id} ats={ats_result['ats_score']}")

    # Detect suitable roles for this resume
    suitable_roles = detect_suitable_roles(resume.raw_text, ats_result["ats_score"])
    
    # Generate detailed Claude-style analysis
    detailed_analysis = generate_detailed_analysis(ats_result, resume.raw_text)

    return {
        "analysis_id":     analysis.id,
        "ats_score":       ats_result["ats_score"],
        "keyword_score":   ats_result["keyword_score"],
        "semantic_score":  ats_result["semantic_score"],
        "score_label":     ats_result["score_label"],
        "matched_skills":  ats_result["matched_skills"],
        "missing_skills":  ats_result["missing_skills"],
        "required_skills": ats_result["required_skills"],
        "ai_insights":     insights,
        "partial_keywords": ats_result.get("partial_keywords", []),
        "category_scores": ats_result.get("category_scores", []),
        "recommendations": ats_result.get("recommendations", []),
        "summary": ats_result.get("summary", ""),
        "suitable_roles":  suitable_roles,  # 5-6 roles with scores
        "detailed_analysis": detailed_analysis,  # Claude-style detailed report
    }


@router.post("/optimize")
def optimize_resume(req: OptimizeRequest, request: Request, db: Session = Depends(get_db)):
    """LLM rewrite + PDF generation. Returns 429 with clear message if Gemini rate-limited."""
    current_user = get_current_user(request, db)

    # Per-user AI rate limit
    try:
        gemini_optimizer.check_user_limit(current_user.id)
    except RateLimitError as e:
        raise HTTPException(429, str(e))

    analysis = db.query(Analysis).filter(
        Analysis.id == req.analysis_id,
        Analysis.user_id == current_user.id
    ).first()
    if not analysis:
        raise HTTPException(404, "Analysis not found.")

    resume = db.query(Resume).filter(Resume.id == analysis.resume_id).first()
    if not resume:
        raise HTTPException(404, "Resume not found.")

    logger.info(f"Optimizing for {current_user.email}, analysis={analysis.id}")

    try:
        optimized_text = gemini_optimizer.optimize_resume(
            resume.raw_text,
            analysis.jd_text,
            analysis.missing_skills or [],
        )
    except RateLimitError as e:
        raise HTTPException(429, str(e))

    # Post-process optimized output to ensure full resume sections are present
    try:
        orig_secs = _parse_resume_sections(resume.raw_text or "")
        opt_secs = _parse_resume_sections(optimized_text or "")

        # Preserve the original resume section order and headings whenever possible.
        optimized_text = rebuild_resume_preserving_order(resume.raw_text or "", optimized_text or "")

        # If optimized output still misses key sections, fall back to a robust merge.
        non_empty_opt = sum(
            1 for k in ['summary', 'experience', 'projects', 'education', 'skills']
            if opt_secs.get(k) and len(opt_secs.get(k)) > 0
        )
        final_text = optimized_text

        if non_empty_opt < 2:
            parts = []
            if orig_secs.get('header'):
                parts.append('\n'.join(orig_secs.get('header')))
            if opt_secs.get('summary'):
                parts.append('\n'.join(opt_secs.get('summary')))
            else:
                parts.append('\n'.join(orig_secs.get('summary') or []))
            for s in ['experience', 'projects', 'education']:
                lines = opt_secs.get(s) or orig_secs.get(s) or []
                if lines:
                    parts.append('\n'.join(lines))
            skills_text = ' '.join(opt_secs.get('skills') or orig_secs.get('skills') or [])
            if skills_text:
                parts.append('TECHNICAL SKILLS: ' + skills_text)
            final_text = '\n\n'.join([p for p in parts if p])

        optimized_text = gemini_optimizer.boost_for_ats_score(
            final_text,
            analysis.jd_text,
            target_score=92,
        )
    except Exception as e:
        logger.warning(f"Post-process optimization failed: {e}")

    # Recompute ATS after finalizing optimized text
    old_score = analysis.ats_score or 0
    new_ats = _analysis_result_from_score(optimized_text, analysis.jd_text)

    if new_ats["ats_score"] < old_score:
        logger.info(
            f"Optimized score decreased for analysis {analysis.id}: "
            f"{old_score} -> {new_ats['ats_score']}. Keeping realistic result."
        )

    # Generate PDF from finalized optimized text
    pdf_dir = os.path.join(settings.UPLOAD_DIR, "optimized")
    os.makedirs(pdf_dir, exist_ok=True)
    pdf_filename = f"opt_{current_user.id[:8]}_{uuid.uuid4().hex[:8]}.pdf"
    pdf_path = os.path.join(pdf_dir, pdf_filename)

    try:
        pdf_generator.generate(
            resume_text=optimized_text,
            output_path=pdf_path,
            candidate_name=current_user.full_name or "",
        )
        pdf_ok = True
        logger.info(f"PDF generated for analysis {analysis.id}: {pdf_path}")
    except Exception as e:
        logger.error(f"PDF generation failed: {e}")
        pdf_path = None
        pdf_ok = False

    # Persist final analysis fields
    analysis.optimized_resume = optimized_text
    analysis.optimized_pdf_path = pdf_path
    analysis.ats_score = new_ats["ats_score"]
    analysis.keyword_score = new_ats.get("keyword_score")
    analysis.semantic_score = new_ats.get("semantic_score")
    analysis.score_label = new_ats.get("score_label")
    analysis.matched_skills = new_ats.get("matched_skills")
    analysis.missing_skills = new_ats.get("missing_skills")
    analysis.required_skills = new_ats.get("required_skills")
    db.commit()

    improvement = new_ats["ats_score"] - old_score
    logger.info(f"Optimization done. Score: {old_score} → {new_ats['ats_score']} ({improvement:+d})")

    return {
        "analysis_id":       analysis.id,
        "optimized_resume":  optimized_text,
        "new_ats_score":     new_ats["ats_score"],
        "score_improvement": improvement,
        "pdf_available":     pdf_ok,
        "pdf_url":           f"/api/v1/analysis/{analysis.id}/download-pdf" if pdf_ok else None,
    }


@router.get("/{analysis_id}/download-pdf")
def download_pdf(analysis_id: str, request: Request, db: Session = Depends(get_db)):
    current_user = get_current_user(request, db)
    analysis = db.query(Analysis).filter(
        Analysis.id == analysis_id,
        Analysis.user_id == current_user.id
    ).first()
    if not analysis:
        raise HTTPException(404, "Analysis not found.")
    if not analysis.optimized_pdf_path or not os.path.exists(analysis.optimized_pdf_path):
        raise HTTPException(404, "PDF not yet generated. Run /optimize first.")
    return FileResponse(
        path=analysis.optimized_pdf_path,
        media_type="application/pdf",
        filename=f"optimized_resume_{analysis.id[:8]}.pdf",
    )


@router.get("/history")
def get_history(request: Request, db: Session = Depends(get_db)):
    current_user = get_current_user(request, db)
    analyses = (
        db.query(Analysis)
        .filter(Analysis.user_id == current_user.id)
        .order_by(Analysis.created_at.desc())
        .limit(20)
        .all()
    )
    return [
        {
            "id":            a.id,
            "jd_title":      a.jd_title,
            "ats_score":     a.ats_score,
            "score_label":   a.score_label,
            "matched_count": len(a.matched_skills or []),
            "missing_count": len(a.missing_skills or []),
            "has_pdf":       bool(a.optimized_pdf_path),
            "created_at":    a.created_at.isoformat() if a.created_at else None,
        }
        for a in analyses
    ]


@router.get("/{analysis_id}")
def get_analysis(analysis_id: str, request: Request, db: Session = Depends(get_db)):
    current_user = get_current_user(request, db)
    a = db.query(Analysis).filter(
        Analysis.id == analysis_id,
        Analysis.user_id == current_user.id
    ).first()
    if not a:
        raise HTTPException(404, "Analysis not found.")
    return AnalysisOut.from_orm_extended(a)
