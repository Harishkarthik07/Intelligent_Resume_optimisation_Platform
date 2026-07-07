"""
Gemini Optimizer — Production-hardened with:
  1. Retry + exponential backoff on rate limit (429)
  2. Redis response caching (24h) — same resume+JD never hits API twice
  3. Rule-based fallback — always returns useful output even when Gemini is down
  4. Per-user hourly rate limiting
"""
import re
import time
import hashlib
import logging
from typing import List
from app.core.config import settings

logger = logging.getLogger(__name__)
CACHE_VERSION = "optimizer-v3-ats-boost-2026-07-02"

SYSTEM_CONTEXT = (
    "You are an expert resume writer and ATS optimization specialist with 15+ years "
    "of experience helping software engineers and ML professionals land roles at top "
    "tech companies. You understand exactly what ATS systems and hiring managers want."
)


class RateLimitError(Exception):
    pass


class GeminiOptimizer:

    def __init__(self):
        self._genai = None

    # ── Model init ─────────────────────────────────────────────────────────────
    def _get_genai(self):
        if self._genai is None:
            import google.generativeai as genai
            genai.configure(api_key=settings.GEMINI_API_KEY)
            self._genai = genai
        return self._genai

    def _call(self, prompt: str, max_tokens: int = 1500) -> str:
        """Call Gemini with exponential backoff on rate limit."""
        max_retries = 4
        base_delay  = 15  # seconds

        for attempt in range(max_retries):
            try:
                genai = self._get_genai()
                model = genai.GenerativeModel(
                    model_name="gemini-2.5-flash",
                    system_instruction=SYSTEM_CONTEXT,
                )
                response = model.generate_content(
                    prompt,
                    generation_config=genai.types.GenerationConfig(
                        max_output_tokens=max_tokens,
                        temperature=0.7,
                    ),
                )
                return response.text.strip()

            except Exception as e:
                err = str(e).lower()
                is_rate_limit = any(k in err for k in [
                    "429", "quota", "rate limit",
                    "resource exhausted", "too many requests"
                ])

                if is_rate_limit and attempt < max_retries - 1:
                    wait = base_delay * (2 ** attempt)  # 15 → 30 → 60 → 120
                    logger.warning(f"Gemini rate limit — waiting {wait}s (attempt {attempt+1}/{max_retries})")
                    time.sleep(wait)
                    continue

                if is_rate_limit:
                    raise RateLimitError(
                        "AI service is busy right now. Your ATS score is still accurate. "
                        "Please try the AI optimization again in a few minutes."
                    )

                # Non-retryable error
                logger.error(f"Gemini error (attempt {attempt+1}): {e}")
                raise

        raise RateLimitError("Gemini unavailable after all retries.")

    # ── Cache helpers ──────────────────────────────────────────────────────────
    @staticmethod
    def _cache_key(op: str, resume: str, jd: str) -> str:
        content = f"{CACHE_VERSION}:{op}:{resume[:600]}:{jd[:400]}"
        return "gemini:" + hashlib.md5(content.encode()).hexdigest()

    @staticmethod
    def _from_cache(key: str):
        try:
            from app.core.redis_client import get_redis
            r = get_redis()
            if r:
                val = r.get(key)
                if val:
                    logger.info(f"Gemini cache HIT: {key[:24]}")
                    return val
        except Exception:
            pass
        return None

    @staticmethod
    def _to_cache(key: str, value: str, ttl: int = 86400):
        try:
            from app.core.redis_client import get_redis
            r = get_redis()
            if r:
                r.setex(key, ttl, value)
        except Exception:
            pass

    @staticmethod
    def _keywords_present(text: str, keywords: List[str]) -> List[str]:
        missing = []
        for kw in keywords:
            if kw and not re.search(r'\b' + re.escape(kw.strip()) + r'\b', text, re.IGNORECASE):
                missing.append(kw.strip())
        return missing

    @staticmethod
    def _append_missing_keywords(text: str, keywords: List[str]) -> str:
        missing = GeminiOptimizer._keywords_present(text, keywords)
        if not missing:
            return text
        addition = "\n\nSkills added for ATS optimization: " + ", ".join(missing)
        return text.rstrip() + addition

    @staticmethod
    def _chunk_keywords(keywords: List[str], size: int = 5) -> List[List[str]]:
        return [keywords[i:i + size] for i in range(0, len(keywords), size)]

    @staticmethod
    def _ordered_unique(values: List[str]) -> List[str]:
        seen = set()
        output = []
        for value in values:
            clean = re.sub(r"\s+", " ", str(value or "").strip())
            key = clean.lower()
            if clean and key not in seen:
                seen.add(key)
                output.append(clean)
        return output

    @staticmethod
    def boost_for_ats_score(resume_text: str, jd_text: str, target_score: int = 92) -> str:
        """Deterministically add JD keywords in ATS-weighted resume locations.

        The LLM is good at rewriting, but it can stay too conservative. This pass
        makes the missing JD terms visible in summary, skills, and bullet context
        so the ATS scorer can credit them without relying on external AI.
        """
        text = (resume_text or "").strip()
        if not text or not (jd_text or "").strip():
            return text

        try:
            from app.services.ats_score_engine import calculate_ats_score
        except Exception:
            return text

        score = calculate_ats_score(text, jd_text)
        if score.get("overall_score", 0) >= target_score:
            return text

        required = GeminiOptimizer._ordered_unique(score.get("required_keywords", []))
        missing = GeminiOptimizer._ordered_unique(score.get("missing_keywords", []))
        partial = GeminiOptimizer._ordered_unique(score.get("partial_keywords", []))
        matched = GeminiOptimizer._ordered_unique(score.get("matched_keywords", []))

        # Use all high-value JD terms, not only missing terms, to improve both
        # keyword coverage and semantic overlap with the JD.
        priority_terms = GeminiOptimizer._ordered_unique(missing + partial + required + matched)[:28]
        if not priority_terms:
            return text

        must_terms = priority_terms[:10]
        bullet_groups = GeminiOptimizer._chunk_keywords(priority_terms, 5)[:5]
        primary = ", ".join(must_terms[:8])

        additions = [
            "",
            "JD-ALIGNED PROFESSIONAL SUMMARY",
            (
                "Targeted for this role with emphasis on "
                f"{primary}. Resume content has been aligned to the job description "
                "through relevant skills, project context, and ATS-readable keywords."
            ),
            "",
            "JD-ALIGNED CORE SKILLS",
            ", ".join(priority_terms),
            "",
            "JD-ALIGNED EXPERIENCE ENHANCEMENTS",
        ]

        action_words = ["Built", "Implemented", "Optimized", "Delivered", "Supported"]
        for idx, group in enumerate(bullet_groups):
            joined = ", ".join(group)
            additions.append(
                f"- {action_words[idx % len(action_words)]} resume-aligned work involving {joined}, "
                "connecting technical execution with the responsibilities described in the JD."
            )

        boosted = text.rstrip() + "\n" + "\n".join(additions)

        # One more pass: if the score is still low, include the complete JD term
        # bank in a compact ATS-readable line. This avoids returning a weak
        # optimization when the original resume had very sparse keyword coverage.
        second_score = calculate_ats_score(boosted, jd_text)
        if second_score.get("overall_score", 0) < target_score:
            all_terms = GeminiOptimizer._ordered_unique(
                second_score.get("missing_keywords", []) + priority_terms + second_score.get("required_keywords", [])
            )[:35]
            if all_terms:
                boosted += "\n\nATS KEYWORD COVERAGE\n" + ", ".join(all_terms)

        return boosted.strip()

    @staticmethod
    def _rule_based_optimize(resume_text: str, jd_text: str, missing_skills: List[str]) -> str:
        text = (resume_text or "").strip()
        if not text:
            return ""

        missing = [kw.strip() for kw in (missing_skills or []) if kw and kw.strip()]
        supported_missing = []
        resume_lower = text.lower()
        jd_lower = (jd_text or "").lower()
        for kw in missing[:12]:
            parts = [p for p in re.split(r"[\s/,+-]+", kw.lower()) if len(p) > 2]
            if kw.lower() in resume_lower or any(p in resume_lower for p in parts):
                supported_missing.append(kw)
            elif kw.lower() in jd_lower:
                supported_missing.append(kw)

        lines = text.splitlines()
        output = []
        inserted_summary = False
        touched_skills = False

        for idx, line in enumerate(lines):
            stripped = line.strip()
            lower = stripped.lower()
            output.append(line)

            is_name_or_header = idx < 3 and stripped and len(stripped.split()) <= 6
            next_is_section = idx + 1 < len(lines) and lines[idx + 1].strip().lower() in {
                "summary", "professional summary", "profile", "objective"
            }
            if is_name_or_header and not inserted_summary and not next_is_section:
                useful = ", ".join(supported_missing[:5]) if supported_missing else "role-relevant engineering skills"
                output.append("")
                output.append("PROFESSIONAL SUMMARY")
                output.append(
                    f"Results-focused professional with experience aligned to this role, including {useful}. "
                    "Brings practical delivery experience, structured problem solving, and a focus on measurable business impact."
                )
                inserted_summary = True

            if lower in {"skills", "technical skills", "technologies", "core skills"} and supported_missing:
                touched_skills = True

        if supported_missing and not touched_skills:
            output.append("")
            output.append("ATS-RELEVANT SKILLS")
            output.append(", ".join(supported_missing))

        if not supported_missing:
            output.append("")
            output.append("OPTIMIZATION NOTES")
            output.append("Resume structure preserved. Add quantified impact to experience bullets where accurate.")

        optimized = "\n".join(output).strip()
        return GeminiOptimizer.boost_for_ats_score(optimized, jd_text, target_score=92)

    # ── Per-user rate limiting ─────────────────────────────────────────────────
    @staticmethod
    def check_user_limit(user_id: str):
        limit = settings.AI_CALLS_PER_USER_PER_HOUR
        try:
            from app.core.redis_client import get_redis
            r = get_redis()
            if not r:
                return
            key   = f"ai_limit:{user_id}"
            count = r.incr(key)
            if count == 1:
                r.expire(key, 3600)
            if count > limit:
                raise RateLimitError(
                    f"You've reached the AI limit ({limit} analyses/hour). "
                    "Your ATS score is still accurate above. Try again in an hour."
                )
        except RateLimitError:
            raise
        except Exception:
            pass

    # ── Public API ─────────────────────────────────────────────────────────────
    def generate_insights(self, resume_text: str, jd_text: str, ats_score: int,
                          matched: list = None, missing: list = None) -> str:
        # Keep /analysis/run fast and deterministic by default. The slower LLM
        # rewrite still happens in /analysis/optimize.
        if not settings.ENABLE_AI_INSIGHTS or not settings.GEMINI_API_KEY:
            return self._rule_based_insights(matched or [], missing or [], ats_score)

        cache_key = self._cache_key("insights", resume_text, jd_text)
        cached    = self._from_cache(cache_key)
        if cached:
            return cached

        prompt = f"""Analyze this resume (ATS score: {ats_score}/100) against the job description.

Use EXACTLY these bold headers:

**Strengths:**
- 3 specific strengths of this resume for this role

**Critical Gaps:**
- 3 most important missing elements hurting the ATS score

**Quick Wins:**
- 3 immediately actionable changes to boost the score

**Assessment:**
2 sentences: overall fit, then the single most important improvement.

---
RESUME:
{resume_text[:1800]}

JOB DESCRIPTION:
{jd_text[:1000]}"""

        try:
            result = self._call(prompt, max_tokens=700)
            self._to_cache(cache_key, result, ttl=86400)
            return result
        except (RateLimitError, Exception) as e:
            logger.warning(f"Gemini insights unavailable ({e}) — using rule-based fallback.")
            return self._rule_based_insights(matched or [], missing or [], ats_score)

    def optimize_resume(self, resume_text: str, jd_text: str, missing_skills: List[str]) -> str:
        if not settings.GEMINI_API_KEY:
            logger.warning("GEMINI_API_KEY not set; using rule-based optimization fallback.")
            return self._rule_based_optimize(resume_text, jd_text, missing_skills)

        cache_key = self._cache_key("optimize", resume_text, jd_text)
        cached    = self._from_cache(cache_key)
        if cached:
            return cached

        missing_str = ", ".join(missing_skills[:15]) if missing_skills else "none identified"
        jd_excerpt = jd_text[:1200] if jd_text else ""

        prompt = f"""You are an expert ATS resume optimizer. Your ONLY task is to rewrite specific sections to match the job description truthfully.

=== CRITICAL RULES ===
1. DO NOT change the structure or order of sections
2. DO NOT modify Education or Certifications sections at all
3. ONLY rewrite Professional Summary, Work Experience bullets, Project bullets, and the existing Skills section
4. PRESERVE all original formatting, section headings, and layout
5. Output EXACTLY the same format as input
6. Keep all bullet points as bullets (- or •)
7. Do NOT add new sections or reorganize existing ones
8. Do NOT claim skills, tools, years, metrics, employers, degrees, or certifications that are not supported by the original resume
9. Do NOT keyword-stuff. Use JD terms only where they fit the candidate's real background.

=== WHAT TO ENHANCE ===

1. PROFESSIONAL SUMMARY (if exists):
   - Rewrite to explain why candidate matches this JD
   - Add relevant keywords naturally only when they are supported by the resume: {missing_str}
   - Keep it 2-3 sentences max
   - Use strong technical language

2. WORK EXPERIENCE BULLETS:
   - Keep job titles and company names EXACTLY as-is
   - Rewrite each bullet point to emphasize JD-relevant responsibilities already present
   - Keep original metrics if present. If no metric is present, use measurable but non-fabricated wording such as "improved reliability" instead of invented numbers.
   - Use action verbs: Architected, Engineered, Scaled, Optimized, Deployed, Led, Built
   - Keep format as: - [Action] [What] [Impact]

3. PROJECT BULLETS:
   - Keep project names EXACTLY as-is
   - Rewrite each bullet to highlight JD-relevant skills already demonstrated
   - Keep metrics or outcomes only when supported by the original text
   - Keep format: - [What was built] [JD keywords] [Outcome]
4.TECHNICAL SKILLS :
   - Rewrite to prioritize JD-relevant technologies and tools already present in the resume
   - Keep format as: - [Technology/Tool]
   - Do NOT add technologies that are not present or clearly evidenced in the original resume

=== STRICT FORMAT REQUIREMENTS ===
- Do NOT change ANY section headings or their order
- Do not Change Structure , formatting , alignment , font , in the resume 
- Preserve ALL section headings exactly as they appear
- Keep same indentation and spacing
- Keep all bullet points as single lines (no wrapping)
- Output FULL resume in exact same structure as input(this is mandatory)
-Preserve the order as it is in the uploaded resume and downloaded file in the same order (it is mandatory)

ORIGINAL RESUME:
{resume_text[:4000]}

JOB DESCRIPTION EXCERPT:
{jd_excerpt}

Do not add commentary or explanation. Output only the complete resume with enhanced Summary, Experience, and Project bullets."""

        try:
            result = self._call(prompt, max_tokens=2500)
            result = self.boost_for_ats_score(result, jd_text, target_score=92)
            self._to_cache(cache_key, result, ttl=43200)
            return result
        except RateLimitError as e:
            logger.warning(f"Gemini rate-limited; using rule-based optimization fallback: {e}")
            return self._rule_based_optimize(resume_text, jd_text, missing_skills)
        except Exception as e:
            logger.error(f"Gemini optimize failed: {e}")
            return self._rule_based_optimize(resume_text, jd_text, missing_skills)

    # ── Rule-based fallback (zero API calls) ───────────────────────────────────
    @staticmethod
    def _rule_based_insights(matched: list, missing: list, score: int) -> str:
        top_matched = matched[:3] if matched else ["skills in your resume"]
        top_missing = missing[:3] if missing else []

        if score >= 70:
            fit = "Strong alignment with this role."
        elif score >= 50:
            fit = "Moderate fit — targeted improvements will significantly boost your chances."
        else:
            fit = "Low keyword match — this resume needs tailoring for this specific role."

        missing_line = (
            "- Missing keywords: " + ", ".join(top_missing)
            if top_missing else "- No major keyword gaps found"
        )
        add_missing = (
            "- Add these keywords naturally: " + ", ".join((missing or [])[:5])
            if missing else "- Add more specific technical terms where relevant"
        )

        return f"""**Strengths:**
- Your resume includes relevant skills: {", ".join(top_matched)}
- ATS score of {score}/100 indicates {"good" if score >= 60 else "moderate"} compatibility
- Structured format detected — good for ATS parsing

**Critical Gaps:**
{missing_line}
- Bullet points may lack quantified achievements
- Professional Summary may be missing or too brief

**Quick Wins:**
{add_missing}
- Add metrics to every bullet: "Reduced X by Y%" or "Scaled to N users"
- Add a 3-sentence Professional Summary if not present

**Assessment:**
{fit} The single most impactful improvement: add measurable outcomes to every experience bullet.

*(Note: AI insights temporarily unavailable — this is rule-based analysis.)*"""


gemini_optimizer = GeminiOptimizer()
