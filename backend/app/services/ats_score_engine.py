import math
import re
from collections import Counter, defaultdict
from typing import Dict, List, Tuple

from app.services.ats_engine import SKILLS_DB


STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "for", "from", "has",
    "have", "in", "is", "it", "of", "on", "or", "our", "that", "the",
    "their", "this", "to", "with", "will", "you", "your", "we", "work",
    "experience", "candidate", "role", "team", "using", "required",
}

GENERIC_KEYWORDS = {
    "target", "guests", "guest", "passion", "commitment", "every", "what",
    "ideas", "deliver", "support", "contribute", "people", "online",
    "stores", "business", "landscape", "business landscape", "latest", "latest tools",
    "the latest tools", "tools", "systems", "value", "mission", "brightest",
    "behind-the-scenes", "powerhouse", "retailers", "retailer",
}

TECH_ANCHORS = {
    "api", "software", "engineering", "engineer", "technology", "technical",
    "cloud", "data", "database", "backend", "frontend", "fullstack",
    "automation", "testing", "debugging", "architecture", "design",
    "algorithms", "agile", "devops", "security", "machine", "learning",
    "model", "analytics", "services", "microservices", "infrastructure",
}

CATEGORY_KEYWORDS = {
    "Programming Languages": [
        "python", "javascript", "typescript", "java", "c++", "c#", "go",
        "rust", "ruby", "php", "swift", "kotlin", "scala", "r", "sql",
    ],
    "Backend Engineering": [
        "fastapi", "django", "flask", "node.js", "express", "spring boot",
        "rest api", "api", "microservices", "grpc", "websockets",
    ],
    "Frontend Engineering": [
        "react", "angular", "vue", "next.js", "html", "css", "tailwind",
        "redux", "graphql", "ui", "ux",
    ],
    "Databases": [
        "postgresql", "mysql", "mongodb", "redis", "elasticsearch",
        "sqlite", "oracle", "sql server", "dynamodb",
    ],
    "Cloud Platforms": [
        "aws", "gcp", "azure", "ec2", "s3", "rds", "lambda", "ecs",
        "eks", "cloud", "docker", "kubernetes", "terraform",
    ],
    "Machine Learning": [
        "machine learning", "deep learning", "tensorflow", "pytorch",
        "scikit-learn", "nlp", "computer vision", "llm", "rag", "pandas",
        "numpy", "model",
    ],
    "Testing & Quality": [
        "unit testing", "integration testing", "tdd", "bdd", "pytest",
        "jest", "test coverage", "quality", "ci/cd",
    ],
    "Leadership & Process": [
        "leadership", "mentoring", "stakeholder", "agile", "scrum",
        "project management", "communication", "cross-functional",
    ],
}

SYNONYMS = {
    "ci cd": "ci/cd",
    "cicd": "ci/cd",
    "postgres": "postgresql",
    "postgre sql": "postgresql",
    "rest": "rest api",
    "apis": "api",
    "ml": "machine learning",
    "llms": "llm",
    "gen ai": "generative ai",
    "js": "javascript",
    "ts": "typescript",
}


def _known_terms() -> List[str]:
    terms = [_canonical(skill) for skill in SKILLS_DB]
    for category_terms in CATEGORY_KEYWORDS.values():
        terms.extend(_canonical(term) for term in category_terms)
    return sorted(set(terms), key=len, reverse=True)


def _clean(text: str) -> str:
    text = (text or "").lower()
    text = text.replace("–", "-").replace("—", "-")
    text = re.sub(r"[^a-z0-9+#./%\-\s]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def _canonical(term: str) -> str:
    term = _clean(term).strip(" .-/")
    term = re.sub(r"\b(experience|skills?|knowledge|proficiency)\b$", "", term).strip()
    return SYNONYMS.get(term, term)


def _is_generic_keyword(term: str) -> bool:
    term = _canonical(term)
    if not term or term in GENERIC_KEYWORDS:
        return True
    words = term.split()
    if any(word in GENERIC_KEYWORDS for word in words):
        return True
    return False


def _has_technical_anchor(term: str) -> bool:
    words = set(_canonical(term).split())
    return bool(words & TECH_ANCHORS)


def _contains(text: str, phrase: str) -> bool:
    phrase = _canonical(phrase)
    if not phrase:
        return False
    pattern = r"(?<![a-z0-9+#])" + re.escape(phrase) + r"(?![a-z0-9+#])"
    return re.search(pattern, _clean(text)) is not None


def _tokens(text: str) -> List[str]:
    return [
        t.strip(" .-/") for t in re.findall(r"[a-z][a-z0-9+#./-]*", _clean(text))
        if len(t.strip(" .-/")) > 1 and t.strip(" .-/") not in STOPWORDS
    ]


def _ngrams(tokens: List[str], max_n: int = 3) -> List[str]:
    phrases = []
    for n in range(1, max_n + 1):
        for i in range(0, max(0, len(tokens) - n + 1)):
            phrase = " ".join(tokens[i:i + n])
            if phrase.split()[0] not in STOPWORDS and phrase.split()[-1] not in STOPWORDS:
                phrases.append(_canonical(phrase))
    return phrases


def _extract_must_haves(jd_text: str) -> List[str]:
    jd = (jd_text or "").lower()
    patterns = [
        r"(?:must have|required|mandatory|proficiency in|strong experience with|experience with)[:\s]+([^.\n;]+)",
        r"(?:requirements?|qualifications?)[:\s]+([^.\n]+)",
    ]
    phrases = []
    for pattern in patterns:
        for match in re.findall(pattern, jd, flags=re.IGNORECASE):
            parts = re.split(r",|/|\band\b|\bor\b", match)
            for part in parts:
                value = _canonical(part)
                if len(value) < 3 or _is_generic_keyword(value):
                    continue
                words = value.split()
                if len(words) > 3:
                    found_known = [term for term in _known_terms() if _contains(value, term)]
                    phrases.extend(found_known[:8])
                else:
                    phrases.append(value)
    return _dedupe(phrases)[:12]


def _extract_keywords(jd_text: str, limit: int = 35) -> List[str]:
    jd_clean = _clean(jd_text)
    jd_tokens = _tokens(jd_text)
    candidates = []

    for skill in SKILLS_DB:
        if _contains(jd_clean, skill):
            candidates.append(_canonical(skill))

    for category_terms in CATEGORY_KEYWORDS.values():
        for term in category_terms:
            if _contains(jd_clean, term):
                candidates.append(_canonical(term))

    strong_candidates = len(_dedupe(candidates))
    counts = Counter(_ngrams(jd_tokens, 3))
    known_phrases = set(_known_terms())

    for phrase, count in counts.most_common(80):
        words = phrase.split()
        if not words or len(phrase) < 3:
            continue
        if len(words) == 1 and (count < 2 or len(phrase) < 4):
            continue
        if any(w in STOPWORDS for w in words):
            continue
        if _is_generic_keyword(phrase):
            continue
        if len(words) >= 3 and phrase not in known_phrases:
            continue
        if count < 2 and phrase not in known_phrases:
            continue
        if phrase in known_phrases or _has_technical_anchor(phrase) or strong_candidates < 8:
            candidates.append(phrase)

    must_haves = _extract_must_haves(jd_text)
    return _dedupe(must_haves + candidates)[:limit]


def _dedupe(items: List[str]) -> List[str]:
    seen = set()
    out = []
    for item in items:
        value = _canonical(item)
        if value and not _is_generic_keyword(value) and value not in seen:
            seen.add(value)
            out.append(value)
    compact = []
    for value in out:
        is_redundant = any(
            value != other and len(value) <= len(other) and re.search(r"\b" + re.escape(value) + r"\b", other)
            for other in out
        )
        if not is_redundant or len(value.split()) > 1:
            compact.append(value)
    return compact


def _context_score(resume_text: str, keyword: str) -> int:
    lines = [line.strip() for line in (resume_text or "").splitlines() if line.strip()]
    for line in lines:
        if _contains(line, keyword):
            lower = line.lower()
            if re.match(r"^\s*(?:[-*•]|\d+[.)])\s+", line):
                return 100
            if any(h in lower for h in ["experience", "project", "summary", "built", "led", "developed", "implemented"]):
                return 88
            if any(h in lower for h in ["skills", "technologies", "tools"]):
                return 72
            return 80
    return 0


def _partial_match(resume_text: str, keyword: str) -> bool:
    resume = _clean(resume_text)
    keyword = _canonical(keyword)
    if _contains(resume, keyword):
        return False
    parts = [p for p in keyword.split() if p not in STOPWORDS]
    if len(parts) >= 2 and any(_contains(resume, p) for p in parts):
        return True
    singular = keyword[:-1] if keyword.endswith("s") else keyword + "s"
    return _contains(resume, singular)


def _cosine_score(a: str, b: str) -> int:
    toks_a = _tokens(a)
    toks_b = _tokens(b)
    if not toks_a or not toks_b:
        return 0
    va = Counter(_ngrams(toks_a, 2))
    vb = Counter(_ngrams(toks_b, 2))
    common = set(va) & set(vb)
    if not common:
        return 0
    dot = sum(va[t] * vb[t] for t in common)
    mag_a = math.sqrt(sum(v * v for v in va.values()))
    mag_b = math.sqrt(sum(v * v for v in vb.values()))
    if not mag_a or not mag_b:
        return 0
    return max(0, min(100, round((dot / (mag_a * mag_b)) * 100)))


def _category_for(keyword: str) -> str:
    keyword = _canonical(keyword)
    for category, terms in CATEGORY_KEYWORDS.items():
        if any(keyword == _canonical(term) or keyword in _canonical(term) or _canonical(term) in keyword for term in terms):
            return category
    return "Role Keywords"


def _grade(score: int) -> str:
    if score >= 85:
        return "Excellent"
    if score >= 72:
        return "Strong"
    if score >= 55:
        return "Good"
    return "Needs Improvement"


def _color(score: int) -> str:
    if score >= 75:
        return "green"
    if score >= 45:
        return "yellow"
    return "red"


def calculate_ats_score(resume_text: str, jd_text: str) -> Dict:
    resume_text = resume_text or ""
    jd_text = jd_text or ""
    keywords = _extract_keywords(jd_text)
    must_haves = set(_extract_must_haves(jd_text))

    matched: List[str] = []
    partial: List[str] = []
    missing: List[str] = []
    weighted_hits = 0.0
    weighted_total = 0.0
    category_points: Dict[str, List[Tuple[float, float]]] = defaultdict(list)

    for keyword in keywords:
        weight = 2.0 if keyword in must_haves else 1.0
        weighted_total += weight
        context = _context_score(resume_text, keyword)
        category = _category_for(keyword)

        if context:
            matched.append(keyword)
            credit = weight * (0.72 + (context / 100) * 0.28)
        elif _partial_match(resume_text, keyword):
            partial.append(keyword)
            credit = weight * 0.45
        else:
            missing.append(keyword)
            credit = 0.0

        weighted_hits += credit
        category_points[category].append((credit, weight))

    keyword_score = round((weighted_hits / weighted_total) * 100) if weighted_total else 0
    semantic_score = _cosine_score(resume_text, jd_text)

    missing_must = [kw for kw in missing if kw in must_haves]
    penalty = min(22, len(missing_must) * 8 + max(0, len(missing) - len(missing_must)) * 1)
    overall = round((keyword_score * 0.72) + (semantic_score * 0.28) - penalty)
    if matched and keyword_score >= 25:
        overall = max(overall, min(55, 18 + len(matched) * 4 + len(partial) * 2))
    if not missing and keyword_score >= 90:
        overall = max(overall, 94 if semantic_score >= 55 else 91)
    elif not missing_must and keyword_score >= 85:
        overall = max(overall, 88)
    overall = max(0, min(100, overall))

    category_scores = []
    for category, values in category_points.items():
        score = round(sum(v for v, _ in values) / max(1.0, sum(w for _, w in values)) * 100)
        category_scores.append({
            "category": category,
            "score": max(0, min(100, score)),
            "color": _color(score),
        })
    category_scores = sorted(category_scores, key=lambda item: item["score"])[:8]

    recommendations = []
    for keyword in missing_must[:4]:
        recommendations.append({
            "priority": "high",
            "text": f"Add '{keyword}' to a relevant experience or project bullet if you have used it.",
            "border_color": "#ef4444",
        })
    for keyword in (missing[:6] + partial[:4]):
        if len(recommendations) >= 8:
            break
        if any(keyword in r["text"] for r in recommendations):
            continue
        recommendations.append({
            "priority": "medium",
            "text": f"Mention '{keyword}' naturally in the summary, skills, or a project bullet.",
            "border_color": "#f59e0b",
        })
    if not recommendations:
        recommendations.append({
            "priority": "medium",
            "text": "Add quantified outcomes to your strongest matching bullets to improve context strength.",
            "border_color": "#22c55e",
        })

    grade = _grade(overall)
    summary = (
        f"{grade} fit: {len(matched)} exact keyword matches, "
        f"{len(partial)} partial matches, and {len(missing)} important gaps found."
    )

    return {
        "overall_score": overall,
        "grade": grade,
        "matched_keywords": matched[:24],
        "partial_keywords": partial[:16],
        "missing_keywords": missing[:16],
        "category_scores": category_scores,
        "recommendations": recommendations,
        "summary": summary,
        "keyword_score": keyword_score,
        "semantic_score": semantic_score,
        "required_keywords": keywords,
    }
