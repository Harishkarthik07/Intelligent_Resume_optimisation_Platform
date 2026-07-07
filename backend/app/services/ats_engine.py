import re
import math
import logging
from collections import Counter
from typing import List, Dict
from app.core.config import settings

logger = logging.getLogger(__name__)

# ─── Skill Dictionary (200+ skills) ──────────────────────────────────────────
SKILLS_DB = [
    # Languages
    "Python","JavaScript","TypeScript","Java","C++","C#","Go","Rust","Ruby","PHP",
    "Swift","Kotlin","Scala","R","MATLAB","Bash","Shell","Perl","Haskell","Erlang",
    # Frontend
    "React","Angular","Vue","Next.js","Svelte","HTML","CSS","Tailwind","SASS",
    "Webpack","Vite","jQuery","Bootstrap","Material UI","Redux","GraphQL",
    # Backend
    "Node.js","Express","Django","FastAPI","Flask","Spring Boot","Rails","Laravel",
    "NestJS","gRPC","REST API","Microservices","WebSockets","Celery","RabbitMQ","Kafka",
    # Databases
    "PostgreSQL","MySQL","MongoDB","Redis","Elasticsearch","DynamoDB","Firebase",
    "Cassandra","SQLite","Oracle","SQL Server","Snowflake","BigQuery","dbt",
    # Cloud & DevOps
    "AWS","GCP","Azure","Docker","Kubernetes","Terraform","Ansible","Helm",
    "CI/CD","Jenkins","GitHub Actions","GitLab CI","ArgoCD","Linux","Nginx",
    "EC2","S3","RDS","Lambda","ECS","EKS","CloudFormation","Prometheus","Grafana",
    # Data & ML
    "Machine Learning","Deep Learning","TensorFlow","PyTorch","Scikit-learn",
    "Pandas","NumPy","Matplotlib","Seaborn","NLP","Computer Vision","LLMs","RAG",
    "Hugging Face","OpenAI API","Gemini API","Langchain","Vector Database",
    "Spark","Hadoop","Airflow","MLflow","Feature Engineering","EDA","Statistics",
    # Practices
    "System Design","Agile","Scrum","Kanban","TDD","BDD","OOP","Functional Programming",
    "Data Structures","Algorithms","Problem Solving","Design Patterns","SOLID",
    # Tools
    "Git","GitHub","JIRA","Confluence","Postman","Swagger","VS Code","IntelliJ",
    "Jupyter","Streamlit","Grafana","Kibana","Datadog","New Relic","Sentry",
    # Soft skills
    "Leadership","Communication","Teamwork","Critical Thinking","Project Management",
    "Stakeholder Management","Mentoring","Analytical","Strategic","Cross-functional",
]


def extract_skills(text: str) -> List[str]:
    if not text:
        return []
    found = []
    for skill in SKILLS_DB:
        pattern = r'\b' + re.escape(skill) + r'\b'
        if re.search(pattern, text, re.IGNORECASE):
            found.append(skill)
    return found


def keyword_score(resume_text: str, jd_text: str) -> Dict:
    jd_skills     = extract_skills(jd_text)
    resume_skills = extract_skills(resume_text)

    if not jd_skills:
        return {"score": 0, "matched": [], "missing": [], "jd_skills": []}

    matched = [s for s in jd_skills if s in resume_skills]
    missing = [s for s in jd_skills if s not in resume_skills]

    return {
        "score":    round(len(matched) / len(jd_skills) * 100),
        "matched":  matched,
        "missing":  missing,
        "jd_skills": jd_skills,
    }


def tfidf_cosine(text_a: str, text_b: str) -> float:
    """TF-IDF cosine similarity fallback (no external ML model required).
    Returns realistic 0-100 score."""
    STOPWORDS = {
        "the","and","for","are","but","with","this","that","have","from",
        "they","will","been","your","their","said","each","which","about",
        "more","when","make","like","time","just","know","take","into",
        "also","here","well","only","over","after","work","used","way",
        "many","data","team","experience","skills","strong","role",
    }

    def tokenize(t):
        return [w.lower() for w in re.findall(r'\b[a-z]{3,}\b', t.lower())
                if w not in STOPWORDS]

    def tfidf_vec(tokens):
        freq = Counter(tokens)
        total = len(tokens) or 1
        return {w: c / total for w, c in freq.items()}

    va = tfidf_vec(tokenize(text_a))
    vb = tfidf_vec(tokenize(text_b))
    common = set(va) & set(vb)
    if not common:
        return 0.0

    dot   = sum(va[w] * vb[w] for w in common)
    mag_a = math.sqrt(sum(v**2 for v in va.values()))
    mag_b = math.sqrt(sum(v**2 for v in vb.values()))
    if not mag_a or not mag_b:
        return 0.0

    raw = dot / (mag_a * mag_b)
    # Scale more realistically: typical TF-IDF gives 0-0.5 range
    # 0.4+ = 80+ score, 0.3-0.4 = 60-80, 0.2-0.3 = 40-60, etc.
    if raw >= 0.4:
        score = round(80 + (raw - 0.4) * 400)  # 80-100, capped at 90
    elif raw >= 0.3:
        score = round(60 + (raw - 0.3) * 200)  # 60-80
    elif raw >= 0.2:
        score = round(40 + (raw - 0.2) * 200)  # 40-60
    else:
        score = round(raw * 200)                 # 0-40
    
    return round(max(0, min(90, score)), 1)  # Cap at 90 for TF-IDF


def semantic_score(resume_text: str, jd_text: str) -> float:
    """
    Try sentence-transformers (all-MiniLM-L6-v2) for semantic similarity.
    Falls back to TF-IDF cosine if model not available.
    Returns realistic 0-100 score with proper bounds.
    """
    if not settings.ENABLE_TRANSFORMER_SCORING:
        return tfidf_cosine(resume_text, jd_text)

    try:
        from sentence_transformers import SentenceTransformer
        import numpy as np
        model = SentenceTransformer("all-MiniLM-L6-v2")
        embs  = model.encode([resume_text[:2000], jd_text[:1500]])
        cos   = float(np.dot(embs[0], embs[1]) /
                      (np.linalg.norm(embs[0]) * np.linalg.norm(embs[1])))
        
        # Ensure realistic bounds based on similarity levels
        # 0.9+ similarity = 85-95 (excellent semantic match)
        # 0.7-0.9 similarity = 70-85 (good match)
        # 0.5-0.7 similarity = 50-70 (moderate)
        # <0.5 similarity = <50 (poor match)
        if cos >= 0.9:
            score = round(85 + (cos - 0.9) * 500)  # 85-100, capped at 95
        elif cos >= 0.7:
            score = round(70 + (cos - 0.7) * 75)   # 70-85
        elif cos >= 0.5:
            score = round(50 + (cos - 0.5) * 100)  # 50-70
        else:
            score = round(max(0, cos * 100))        # 0-50
        
        return max(0, min(95, score))  # Cap at 95 for semantic (never 100)
    except Exception as e:
        logger.debug(f"sentence-transformers unavailable ({e}), using TF-IDF.")
        return tfidf_cosine(resume_text, jd_text)


def resume_quality_score(resume_text: str) -> int:
    """Score ATS-friendly resume substance with realistic standards."""
    text = resume_text or ""
    lowered = text.lower()
    words = re.findall(r'\b\w+\b', lowered)
    word_count = len(words)

    # ── Section completeness ──────────────────────────────────────────
    section_checks = [
        r'\b(summary|profile|objective)\b',
        r'\b(experience|employment|work history|professional experience)\b',
        r'\b(projects?)\b',
        r'\b(education|degree)\b',
        r'\b(skills|technical skills|technologies)\b',
    ]
    sections_found = sum(1 for pattern in section_checks if re.search(pattern, lowered))
    section_score = (sections_found / len(section_checks)) * 35
    
    # ── Bullet points (ATS-critical) ──────────────────────────────────
    bullet_count = len(re.findall(r'(?m)^\s*(?:[-*•]|\d+[.)])\s+', text))
    if bullet_count >= 12:
        bullet_score = 20
    elif bullet_count >= 8:
        bullet_score = 15
    elif bullet_count >= 5:
        bullet_score = 10
    elif bullet_count >= 2:
        bullet_score = 5
    else:
        bullet_score = 0
    
    # ── Quantified metrics (impact indicators) ──────────────────────
    metric_patterns = [
        r'\b\d+%\b',                    # Percentages: 50%, 100%
        r'\b\d+(?:\+|x|times)\b',       # Multipliers: 5x, 10+
        r'\b(?:reduced|increased|improved|scaled|optimized|grew|expanded)\s+\w+\s+(?:by\s+)?\d+',  # Metric phrases
        r'\b\$?\d+(?:k|m|bn)\b',        # Numbers with scale: $5M, 100K
    ]
    metric_count = sum(len(re.findall(pattern, lowered)) for pattern in metric_patterns)
    metric_score = min(15, metric_count * 2)
    
    # ── Word count expectations ──────────────────────────────────────
    if 400 <= word_count <= 800:
        length_score = 15
    elif 250 <= word_count < 400 or 800 < word_count <= 1000:
        length_score = 10
    elif 150 <= word_count < 250:
        length_score = 5
    else:
        length_score = 0
    
    # ── Vocabulary diversity ──────────────────────────────────────────
    unique_ratio = len(set(words)) / max(1, word_count)
    if unique_ratio >= 0.40:
        repetition_score = 15
    elif unique_ratio >= 0.30:
        repetition_score = 10
    elif unique_ratio >= 0.20:
        repetition_score = 5
    else:
        repetition_score = 0
    
    # ── Keyword stuffing penalty ─────────────────────────────────────
    stuffing_penalty = 0
    for line in text.splitlines():
        line_skills = extract_skills(line)
        words_in_line = len(line.split())
        if len(line_skills) >= 8 and words_in_line < 45 and words_in_line > 0:
            stuffing_penalty += 10
    
    # Check overall skill density (>15% is likely stuffing)
    skill_density = len(extract_skills(text)) / max(1, word_count)
    if skill_density > 0.15:
        stuffing_penalty += min(15, (skill_density - 0.15) * 50)

    stuffing_penalty = min(stuffing_penalty, 25)
    total = section_score + bullet_score + metric_score + length_score + repetition_score - stuffing_penalty

    return max(0, min(100, round(total)))


def score_label(score: int) -> str:
    if score >= 80: return "Excellent"
    if score >= 60: return "Good"
    if score >= 40: return "Fair"
    return "Needs Work"


class ATSScoringEngine:
    KW_WEIGHT      = 0.50
    SEM_WEIGHT     = 0.30
    QUALITY_WEIGHT = 0.20

    def analyze(self, resume_text: str, jd_text: str) -> Dict:
        kw  = keyword_score(resume_text, jd_text)
        sem = semantic_score(resume_text, jd_text)
        quality = resume_quality_score(resume_text)

        # Weighted composite: Keywords (50%) + Semantic (30%) + Quality (20%)
        composite = round(
            kw["score"] * self.KW_WEIGHT +
            sem * self.SEM_WEIGHT +
            quality * self.QUALITY_WEIGHT
        )

        # Realistic penalties — never allow a perfect 100
        # Missing skills significantly hurt ATS compatibility
        if kw["missing"]:
            missing_penalty = min(25, len(kw["missing"]) * 2)
            composite = max(0, min(composite, 85 - len(kw["missing"]) // 2))
        
        # If keywords aren't 100% match, cap at 89 (realistic for partial matches)
        if kw["score"] < 100:
            composite = min(composite, 89)
        
        # If keywords are 100% but semantic match is low, something's off
        if kw["score"] == 100 and sem < 60:
            composite = min(composite, 75)
        
        # Semantic gap = resume and JD aren't conceptually aligned
        if sem < 75:
            composite = min(composite, 90)
        if sem < 60:
            composite = min(composite, 85)
        if sem < 50:
            composite = min(composite, 75)
        
        # Resume quality is critical for ATS parsing
        if quality < 75:
            composite = min(composite, 92)
        if quality < 60:
            composite = min(composite, 85)
        if quality < 50:
            composite = min(composite, 78)
        
        # Final cap: no perfect scores unless absolutely everything aligns
        # At least one of these must be slightly imperfect to keep it real
        if composite >= 95:
            if kw["score"] < 100 or sem < 95 or quality < 95:
                composite = min(composite, 94)
        
        # Never allow 100 in real scenarios - there's always room for improvement
        composite = min(composite, 98)
        composite = max(0, composite)  # No negative scores

        logger.info(f"ATS score: {composite} (kw={kw['score']}, sem={sem}, quality={quality}, missing={len(kw['missing'])} skills)")

        return {
            "ats_score":       composite,
            "keyword_score":   kw["score"],
            "semantic_score":  round(sem, 1),
            "quality_score":   quality,
            "matched_skills":  kw["matched"],
            "missing_skills":  kw["missing"],
            "required_skills": kw["jd_skills"],
            "score_label":     score_label(composite),
        }


def detect_suitable_roles(resume_text: str, ats_score: int) -> List[Dict]:
    """
    Detect which industry roles this resume is suitable for.
    Returns top 5-6 roles with ATS scores adjusted for role fit.
    """
    text_lower = resume_text.lower()
    skills = extract_skills(resume_text)
    
    # Role detection heuristics
    role_indicators = {
        "Backend Engineer": {
            "keywords": ["backend", "api", "server", "database", "microservices", "django", "fastapi", "node.js", "spring"],
            "skills": ["Python", "Java", "Node.js", "Go", "PostgreSQL", "MongoDB", "FastAPI", "Django", "REST API"],
            "weight": 0.3,
        },
        "Frontend Engineer": {
            "keywords": ["frontend", "ui", "ux", "react", "vue", "angular", "responsive", "css", "javascript"],
            "skills": ["React", "TypeScript", "Vue", "Next.js", "HTML", "CSS", "Tailwind", "Redux", "GraphQL"],
            "weight": 0.3,
        },
        "Full-Stack Engineer": {
            "keywords": ["full-stack", "end-to-end", "full stack", "frontend and backend"],
            "skills": ["React", "Python", "PostgreSQL", "Node.js", "Django", "FastAPI", "REST API"],
            "weight": 0.25,
        },
        "DevOps Engineer": {
            "keywords": ["devops", "infrastructure", "deployment", "cloud", "ci/cd", "kubernetes", "docker"],
            "skills": ["Docker", "Kubernetes", "AWS", "Terraform", "CI/CD", "Jenkins", "GitHub Actions", "Linux"],
            "weight": 0.25,
        },
        "Data Scientist": {
            "keywords": ["data science", "machine learning", "ml", "analytics", "data analysis", "statistics"],
            "skills": ["Python", "Machine Learning", "TensorFlow", "PyTorch", "Pandas", "R", "Statistics", "SQL"],
            "weight": 0.25,
        },
        "Machine Learning Engineer": {
            "keywords": ["ml engineer", "machine learning engineer", "mlops", "deep learning", "neural"],
            "skills": ["Python", "TensorFlow", "PyTorch", "Machine Learning", "Deep Learning", "Scikit-learn"],
            "weight": 0.25,
        },
        "Site Reliability Engineer": {
            "keywords": ["sre", "reliability", "monitoring", "observability", "infrastructure"],
            "skills": ["Kubernetes", "Docker", "Prometheus", "Grafana", "AWS", "Linux", "Python", "Go"],
            "weight": 0.25,
        },
        "Engineering Manager": {
            "keywords": ["manager", "lead", "leadership", "team lead", "engineering manager", "director"],
            "skills": ["Leadership", "Communication", "Project Management", "Agile", "Mentoring"],
            "weight": 0.2,
        },
    }
    
    role_scores = []
    
    for role_name, role_data in role_indicators.items():
        # Calculate keyword match
        keyword_matches = sum(1 for kw in role_data["keywords"] if kw in text_lower)
        keyword_score = (keyword_matches / len(role_data["keywords"])) * 40 if role_data["keywords"] else 0
        
        # Calculate skill match
        role_skills = role_data["skills"]
        skill_matches = sum(1 for s in role_skills if s in skills)
        skill_score = (skill_matches / len(role_skills)) * 40 if role_skills else 0
        
        # Years of experience indicator (rough estimate)
        experience_matches = len(re.findall(r'\b(5\+|\d+\+|years?|year)\b', text_lower, re.IGNORECASE))
        experience_score = min(20, experience_matches * 5)
        
        # Combined score
        role_fit = keyword_score + skill_score + experience_score
        
        # Adjust final score based on ATS and role weight
        final_score = min(98, round((ats_score * 0.7) + (role_fit * 0.3) * role_data["weight"]))
        
        if final_score >= 45:  # Only include roles with reasonable fit
            role_scores.append({
                "role": role_name,
                "ats_score": final_score,
                "fit_reasons": {
                    "keywords": f"{keyword_matches}/{len(role_data['keywords'])}",
                    "skills_match": f"{skill_matches}/{len(role_skills)}",
                    "experience_indicators": experience_matches,
                },
                "match_percentage": min(100, round((keyword_score + skill_score + experience_score) / 100 * 100)),
            })
    
    # Sort by score and return top 6
    return sorted(role_scores, key=lambda x: x["ats_score"], reverse=True)[:6]


def generate_detailed_analysis(analyze_result: Dict, resume_text: str) -> str:
    """
    Generate Claude-style detailed analysis output.
    """
    score = analyze_result["ats_score"]
    kw_score = analyze_result["keyword_score"]
    sem_score = analyze_result["semantic_score"]
    matched = analyze_result["matched_skills"]
    missing = analyze_result["missing_skills"]
    
    # Assess tier
    if score >= 85:
        tier = "🟢 STRONG MATCH - High probability of ATS pass"
        advice = "Your resume is well-aligned. Proceed with submission."
    elif score >= 70:
        tier = "🟡 GOOD MATCH - Likely to pass ATS"
        advice = "Minor optimizations recommended. Consider adding more metrics."
    elif score >= 55:
        tier = "🟠 MODERATE MATCH - May pass ATS"
        advice = "Significant improvements needed. Review missing skills section."
    else:
        tier = "🔴 POOR MATCH - Risk of ATS rejection"
        advice = "Major revisions required. Consider using AI optimization."
    
    analysis = f"""
RESUME ANALYSIS - ATS COMPATIBILITY REPORT
{'='*60}

OVERALL SCORE: {score}/100
{tier}

{'─'*60}
BREAKDOWN:
• Keyword Matching: {kw_score}/100 (Resume contains keywords from job description)
• Semantic Alignment: {sem_score}/100 (Content relevance and concept match)
• Resume Quality: {analyze_result.get('quality_score', 'N/A')}/100 (Structure, formatting, completeness)

{'─'*60}
KEY FINDINGS:

✓ STRENGTHS ({len(matched)} matched skills):
  {', '.join(matched[:8]) if matched else 'No matched skills detected'}

✗ GAPS ({len(missing)} missing skills):
  {', '.join(missing[:8]) if missing else 'All keywords present!'}

{'─'*60}
RECOMMENDATIONS:
• {advice}
• Focus on: {missing[0] if missing else 'Your resume matches well'}
• Quantify achievements where possible
• Use industry-standard terminology
• Maintain consistent formatting throughout

"""
    return analysis.strip()


ats_engine = ATSScoringEngine()
