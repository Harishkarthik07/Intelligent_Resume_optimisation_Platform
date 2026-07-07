import os
import re
import logging
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor, black, white
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, HRFlowable,
    KeepTogether, Table, TableStyle,
)
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from reportlab.lib import colors

logger = logging.getLogger(__name__)

# ─── Color Palette ────────────────────────────────────────────────────────────
INDIGO     = HexColor("#4f46e5")
INDIGO_LT  = HexColor("#e0e7ff")
GRAY_DARK  = HexColor("#1f2937")
GRAY_MED   = HexColor("#4b5563")
GRAY_LIGHT = HexColor("#9ca3af")
GRAY_BG    = HexColor("#f9fafb")


def _build_styles():
    styles = getSampleStyleSheet()

    custom = {
        "Name": ParagraphStyle(
            "Name",
            fontSize=20, fontName="Helvetica-Bold",
            textColor=GRAY_DARK, spaceAfter=2,
            leading=22,
        ),
        "ContactLine": ParagraphStyle(
            "ContactLine",
            fontSize=8, fontName="Helvetica",
            textColor=GRAY_MED, spaceAfter=1,
        ),
        "SectionHeader": ParagraphStyle(
            "SectionHeader",
            fontSize=10, fontName="Helvetica-Bold",
            textColor=INDIGO, spaceBefore=8, spaceAfter=3,
            leading=12,
        ),
        "JobTitle": ParagraphStyle(
            "JobTitle",
            fontSize=9, fontName="Helvetica-Bold",
            textColor=GRAY_DARK, spaceBefore=4, spaceAfter=0,
        ),
        "CompanyLine": ParagraphStyle(
            "CompanyLine",
            fontSize=8, fontName="Helvetica-Oblique",
            textColor=GRAY_MED, spaceAfter=2,
        ),
        "BulletItem": ParagraphStyle(
            "BulletItem",
            fontSize=8, fontName="Helvetica",
            textColor=GRAY_MED, leftIndent=10,
            spaceAfter=1, leading=11,
            bulletIndent=2,
        ),
        "BodyText": ParagraphStyle(
            "BodyText",
            fontSize=8, fontName="Helvetica",
            textColor=GRAY_MED, spaceAfter=2,
            leading=11, alignment=TA_JUSTIFY,
        ),
        "SkillChip": ParagraphStyle(
            "SkillChip",
            fontSize=9, fontName="Helvetica",
            textColor=GRAY_MED,
        ),
        "Footer": ParagraphStyle(
            "Footer",
            fontSize=8, fontName="Helvetica",
            textColor=GRAY_LIGHT, alignment=TA_CENTER,
        ),
    }
    return custom


def _section_divider(styles):
    return HRFlowable(width="100%", thickness=0.5, color=INDIGO_LT, spaceAfter=4)


def _parse_resume_sections(text: str) -> dict:
    """
    Parse plain-text resume into named sections.
    Returns dict: {section_name: [lines], '_order': [...], '_titles': {...}}
    """
    SECTION_KEYWORDS = {
        "summary":     r"^(summary|professional summary|profile|objective)",
        "experience":  r"^(experience|work experience|employment|professional experience)",
        "projects":    r"^(projects|key projects|personal projects|portfolio)",
        "education":   r"^(education|academic|qualifications)",
        "skills":      r"^(skills|technical skills|core skills|competencies|technologies)",
        "courses":     r"^(courses|certifications|certificates|training)",
    }

    sections = {
        "header": [],
        "summary": [],
        "experience": [],
        "projects": [],
        "education": [],
        "skills": [],
        "courses": [],
        "other": [],
    }
    section_titles = {}
    section_order = []

    lines = text.split('\n')
    current = "header"

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue

        matched_key = None
        for section_key, pattern in SECTION_KEYWORDS.items():
            if re.match(pattern, stripped, re.IGNORECASE) and len(stripped) < 80:
                current = section_key
                matched_key = section_key
                section_titles.setdefault(section_key, stripped.upper())
                if section_key not in section_order:
                    section_order.append(section_key)
                break

        if matched_key:
            continue

        sections[current].append(stripped)

    sections["_order"] = section_order
    sections["_titles"] = section_titles
    return sections


class ResumePDFGenerator:
    MARGIN = 14 * mm

    def generate(self, resume_text: str, output_path: str, candidate_name: str = "") -> str:
        """Generate a professionally formatted PDF from plain resume text."""
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        styles = _build_styles()
        sections = _parse_resume_sections(resume_text)

        doc = SimpleDocTemplate(
            output_path,
            pagesize=A4,
            leftMargin=self.MARGIN,
            rightMargin=self.MARGIN,
            topMargin=10 * mm,
            bottomMargin=10 * mm,
            title=f"{candidate_name} - Optimized Resume",
            author="ResumeIQ",
        )

        story = []
        story += self._build_header(sections["header"], styles, candidate_name)

        section_order = sections.get("_order", [])
        if not section_order:
            section_order = ["summary", "experience", "projects", "education", "skills", "courses"]

        default_titles = {
            "summary": "PROFESSIONAL SUMMARY",
            "experience": "EXPERIENCE",
            "projects": "PROJECTS",
            "education": "EDUCATION",
            "skills": "TECHNICAL SKILLS",
            "courses": "CERTIFICATIONS",
            "other": "ADDITIONAL INFORMATION",
        }

        for section_key in section_order:
            if section_key == "header":
                continue
            lines = sections.get(section_key) or []
            if not any(l.strip() for l in lines):
                continue
            heading = sections.get("_titles", {}).get(section_key) or default_titles.get(section_key, section_key.upper())
            if section_key == "skills":
                story += self._build_skills_section(lines, styles, title=heading)
            else:
                story += self._build_section(heading, lines, styles)

        # Add any extra sections not included in the original section order
        for section_key in ["summary", "experience", "projects", "education", "skills", "courses", "other"]:
            if section_key in section_order:
                continue
            lines = sections.get(section_key) or []
            if lines:
                heading = sections.get("_titles", {}).get(section_key) or default_titles.get(section_key, section_key.upper())
                if section_key == "skills":
                    story += self._build_skills_section(lines, styles, title=heading)
                else:
                    story += self._build_section(heading, lines, styles)

        # Watermark footer
        story.append(Spacer(1, 6 * mm))
        story.append(Paragraph(
            f"Optimized by ResumeIQ · {datetime.now().strftime('%B %Y')}",
            styles["Footer"]
        ))

        doc.build(story)
        logger.info(f"PDF generated: {output_path}")
        return output_path

    def _build_header(self, lines: list, styles: dict, fallback_name: str) -> list:
        story = []
        name = fallback_name or (lines[0] if lines else "Candidate")
        story.append(Paragraph(name, styles["Name"]))

        contact_lines = [l for l in lines[1:6] if l.strip()]
        if contact_lines:
            story.append(Paragraph(" · ".join(contact_lines), styles["ContactLine"]))

        story.append(Spacer(1, 3 * mm))
        story.append(HRFlowable(width="100%", thickness=1.5, color=INDIGO, spaceAfter=6))
        return story

    def _build_section(self, title: str, lines: list, styles: dict) -> list:
        if not any(l.strip() for l in lines):
            return []

        story = []
        story.append(Paragraph(title, styles["SectionHeader"]))
        story.append(_section_divider(styles))

        current_block = []

        def flush_block():
            if current_block:
                story.append(KeepTogether(current_block[:]))
                current_block.clear()

        for line in lines:
            line = line.strip()
            if not line:
                flush_block()
                continue

            if line.startswith(("-", "•", "*", "·")):
                bullet_text = line.lstrip("-•*· ").strip()
                current_block.append(Paragraph(f"• {bullet_text}", styles["BulletItem"]))
            elif self._is_section_title(line):
                flush_block()
                story.append(Paragraph(line, styles["JobTitle"]))
                current_block = []
            elif self._is_date_line(line):
                current_block.append(Paragraph(line, styles["CompanyLine"]))
            else:
                current_block.append(Paragraph(line, styles["BodyText"]))

        flush_block()
        return story

    def _build_skills_section(self, lines: list, styles: dict, title: str = "TECHNICAL SKILLS") -> list:
        if not any(l.strip() for l in lines):
            return []

        story = []
        story.append(Paragraph(title, styles["SectionHeader"]))
        story.append(_section_divider(styles))

        all_skills_text = " ".join(l.strip() for l in lines if l.strip())
        story.append(Paragraph(all_skills_text, styles["BodyText"]))
        return story

    @staticmethod
    def _is_section_title(line: str) -> bool:
        return (
            len(line) < 80 and
            not line.startswith(("-", "•", "*")) and
            (line.istitle() or (line[0].isupper() and not line.endswith(".")))
        )

    @staticmethod
    def _is_date_line(line: str) -> bool:
        date_patterns = [
            r'\b(20\d{2}|19\d{2})\b',
            r'\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\b',
            r'\bPresent\b',
        ]
        return any(re.search(p, line, re.IGNORECASE) for p in date_patterns)


def rebuild_resume_preserving_order(original_text: str, optimized_text: str) -> str:
    orig = _parse_resume_sections(original_text)
    opt = _parse_resume_sections(optimized_text)

    section_order = orig.get("_order", [])
    if not section_order:
        section_order = ["summary", "experience", "projects", "education", "skills", "courses"]

    default_titles = {
        "summary": "PROFESSIONAL SUMMARY",
        "experience": "EXPERIENCE",
        "projects": "PROJECTS",
        "education": "EDUCATION",
        "skills": "TECHNICAL SKILLS",
        "courses": "CERTIFICATIONS",
        "other": "ADDITIONAL INFORMATION",
    }

    parts = []
    if orig.get("header"):
        parts.append("\n".join(orig["header"]))

    seen = set()
    for section_key in section_order:
        if section_key == "header":
            continue
        lines = opt.get(section_key) or orig.get(section_key) or []
        if not any(l.strip() for l in lines):
            continue
        heading = opt.get("_titles", {}).get(section_key) or orig.get("_titles", {}).get(section_key) or default_titles.get(section_key, section_key.upper())
        parts.append(heading)
        parts.append("\n".join(lines))
        seen.add(section_key)

    for section_key in opt.get("_order", []):
        if section_key in seen or section_key == "header":
            continue
        lines = opt.get(section_key) or []
        if not any(l.strip() for l in lines):
            continue
        heading = opt.get("_titles", {}).get(section_key) or default_titles.get(section_key, section_key.upper())
        parts.append(heading)
        parts.append("\n".join(lines))

    return "\n\n".join([p for p in parts if p])

pdf_generator = ResumePDFGenerator()
