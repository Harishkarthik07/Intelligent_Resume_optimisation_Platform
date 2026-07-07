"""
Resume templates API endpoint for SaaS product.
Users can view and download ATS-friendly templates.
"""
from fastapi import APIRouter, HTTPException, Request
from app.services.templates import TEMPLATES, INDUSTRY_ROLES

router = APIRouter()


@router.get("/list")
def list_templates(request: Request):
    """List all available resume templates."""
    templates_list = []
    for template_id, template_data in TEMPLATES.items():
        templates_list.append({
            "id": template_data["id"],
            "name": template_data["name"],
            "description": template_data["description"],
            "difficulty": template_data["difficulty"],
            "ats_score": template_data["ats_score"],
            "pros": template_data["pros"],
            "cons": template_data["cons"],
        })
    
    return {
        "templates": templates_list,
        "total": len(templates_list),
    }


@router.get("/industry-roles")
def get_industry_roles(request: Request):
    """Get role suggestions by industry."""
    return {
        "industries": {
            industry: {"roles": roles}
            for industry, roles in INDUSTRY_ROLES.items()
        },
    }


@router.get("/{template_id}")
def get_template(template_id: str, request: Request):
    """Get detailed template with example."""
    if template_id not in TEMPLATES:
        raise HTTPException(404, "Template not found")
    
    template = TEMPLATES[template_id]
    return {
        "id": template["id"],
        "name": template["name"],
        "description": template["description"],
        "difficulty": template["difficulty"],
        "ats_score": template["ats_score"],
        "pros": template["pros"],
        "cons": template["cons"],
        "example": template["example"],
        "recommendations": f"""
TIPS FOR USING THIS TEMPLATE:

1. CUSTOMIZE YOUR DATA
   - Replace all example information with your actual details
   - Keep the same structure and section headings
   - Maintain consistent formatting throughout

2. ATS OPTIMIZATION
   - Use standard fonts: Arial, Calibri, or Times New Roman
   - Avoid tables, images, and graphics
   - Use simple bullet points (-, •)
   - Keep margins consistent: 0.5-1 inch

3. CONTENT QUALITY
   - Start bullet points with action verbs: Led, Built, Designed, etc.
   - Include quantified metrics: 50% improvement, $2M savings
   - Use industry keywords relevant to your target role
   - Keep each bullet to 1-2 lines maximum

4. BEFORE SUBMITTING
   - Save as PDF (maintains formatting)
   - Test upload in our tool to check ATS compatibility
   - Review for typos and grammatical errors
   - Ensure dates and titles are accurate

5. CUSTOMIZATION FOR EACH JOB
   - Reorder bullet points by relevance to job description
   - Add metrics and outcomes where possible
   - Emphasize skills listed in the job posting
   - Keep to 1 page if you have <5 years experience

DOWNLOAD THIS TEMPLATE:
- Copy the example text above
- Paste into Google Docs, Word, or your editor
- Customize with your information
- Export as PDF
- Upload to ResumeIQ to check ATS compatibility
"""
    }


@router.post("/download-example/{template_id}")
def download_template_example(template_id: str, request: Request):
    """Download template example as text file."""
    if template_id not in TEMPLATES:
        raise HTTPException(404, "Template not found")
    
    template = TEMPLATES[template_id]
    content = f"""
{template['name'].upper()}
{'='*70}

{template['description']}

ATS SCORE: {template['ats_score']}/100

PROS:
{chr(10).join('• ' + p for p in template['pros'])}

CONS:
{chr(10).join('• ' + c for c in template['cons'])}

{'='*70}
TEMPLATE EXAMPLE:

{template['example']}

{'='*70}

To use this template:
1. Copy this entire text
2. Open Google Docs or Word
3. Paste the content
4. Replace with your own information
5. Save as PDF
6. Upload to ResumeIQ to check ATS compatibility
"""
    
    return {
        "template_id": template_id,
        "name": template["name"],
        "content": content,
        "format": "text/plain",
    }
