import logging

from fastapi import APIRouter

from app.schemas.schemas import ATSScoreRequest, ATSScoreResult
from app.services.ats_score_engine import calculate_ats_score

logger = logging.getLogger(__name__)
router = APIRouter()


def _fallback_result(message: str) -> dict:
    return {
        "overall_score": 0,
        "grade": "Needs Improvement",
        "matched_keywords": [],
        "partial_keywords": [],
        "missing_keywords": [],
        "category_scores": [],
        "recommendations": [
            {
                "priority": "high",
                "text": message,
                "border_color": "#ef4444",
            }
        ],
        "summary": message,
    }


@router.post("/score", response_model=ATSScoreResult)
def score_ats(req: ATSScoreRequest):
    if not req.resume_text or not req.jd_text:
        return _fallback_result("Provide both resume_text and jd_text to calculate an ATS score.")

    try:
        result = calculate_ats_score(req.resume_text, req.jd_text)
        return {
            "overall_score": result["overall_score"],
            "grade": result["grade"],
            "matched_keywords": result["matched_keywords"],
            "partial_keywords": result["partial_keywords"],
            "missing_keywords": result["missing_keywords"],
            "category_scores": result["category_scores"],
            "recommendations": result["recommendations"],
            "summary": result["summary"],
        }
    except Exception as exc:
        logger.exception("ATS score engine failed: %s", exc)
        return _fallback_result("ATS scoring could not complete for this input. Try simplifying the pasted text.")
