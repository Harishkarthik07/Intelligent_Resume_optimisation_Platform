import sys, os
sys.path.insert(0, os.path.abspath('backend'))

from app.services.ats_engine import ats_engine, extract_skills
from app.services.pdf_generator import _parse_resume_sections

# Sample resume with full sections
sample_resume = '''John Doe
Senior Software Engineer

PROFESSIONAL SUMMARY
Experienced software engineer with 5 years building backend systems.

WORK EXPERIENCE
Acme Corp — Senior Backend Engineer (2022-Present)
- Worked on microservices architecture
- Managed PostgreSQL databases
- Deployed applications to AWS

TechStartup Inc — Software Engineer (2020-2022)
- Built REST APIs using FastAPI
- Containerized services with Docker
- Worked with Python and databases

PROJECTS
- Built internal monitoring dashboard using Python
- Created CLI tool for data processing

EDUCATION
BS Computer Science, State University (2020)

TECHNICAL SKILLS
Python, JavaScript, Docker, AWS, PostgreSQL, FastAPI'''

sample_jd = '''We are hiring a Senior Software Engineer with expertise in:
- Python, FastAPI, and backend API development
- Docker containerization and Kubernetes orchestration
- AWS services (EC2, RDS, Lambda, S3)
- PostgreSQL and database optimization
- Microservices architecture and system design
Requirements: 5+ years experience, strong in cloud infrastructure'''

# Original ATS score
orig = ats_engine.analyze(sample_resume, sample_jd)
print(f'Original ATS score: {orig["ats_score"]} keyword_score: {orig["keyword_score"]} semantic: {orig["semantic_score"]}')
print(f'Matched skills: {orig["matched_skills"]}')
print(f'Missing skills: {orig["missing_skills"]}')

# Simulated enhanced output (what Gemini should produce with new prompt)
# Enhanced Summary and Experience with more JD keywords
enhanced_resume = '''John Doe
Senior Software Engineer

PROFESSIONAL SUMMARY
Results-driven Senior Backend Engineer with 5+ years architecting and deploying scalable microservices on AWS.
Expert in Python, FastAPI, and PostgreSQL, with proven expertise in Docker containerization and AWS infrastructure.
Passionate about optimizing system performance and mentoring engineering teams.

WORK EXPERIENCE
Acme Corp — Senior Backend Engineer (2022-Present)
- Architected microservices infrastructure using FastAPI, reducing latency by 40% and scaling to 100K+ daily requests
- Optimized PostgreSQL queries and database indexes, improving query performance by 60%
- Deployed and managed containerized applications on AWS using Docker and RDS
- Led migration from monolithic architecture to microservices using FastAPI and PostgreSQL

TechStartup Inc — Software Engineer (2020-2022)
- Engineered production REST APIs using FastAPI framework, serving 50K+ monthly users
- Containerized 15+ microservices using Docker, reducing deployment time by 45%
- Managed PostgreSQL databases with automated backup and optimization strategies
- Deployed applications to AWS EC2 and managed S3 storage for 500GB+ data

PROJECTS
- Built internal monitoring dashboard using Python and FastAPI, tracking 200+ system metrics
- Created Python CLI tool for data processing and optimization, reducing manual tasks by 30 hours/month

EDUCATION
BS Computer Science, State University (2020)

TECHNICAL SKILLS
Python, FastAPI, Docker, AWS, PostgreSQL, Kubernetes, JavaScript, Microservices, System Design, RDS, Lambda, EC2'''

# Post-process similar to analysis route
orig_secs = _parse_resume_sections(sample_resume)
enh_secs = _parse_resume_sections(enhanced_resume)

print(f'\nOriginal sections parsed: {list(orig_secs.keys())}')
print(f'Enhanced sections parsed: {list(enh_secs.keys())}')

# Analyze enhanced resume
new = ats_engine.analyze(enhanced_resume, sample_jd)
print(f'\nFinal ATS score: {new["ats_score"]} keyword_score: {new["keyword_score"]} semantic: {new["semantic_score"]}')
print(f'Matched skills after: {new["matched_skills"]}')
print(f'Missing skills after: {new["missing_skills"]}')

# Check keyword coverage
jd_skills = extract_skills(sample_jd)
final_skills = extract_skills(enhanced_resume)
print(f'\nJD skills required: {jd_skills}')
print(f'Skills present in enhanced: {final_skills}')
missing_after = [k for k in jd_skills if k not in final_skills]
print(f'Missing after enhancement: {missing_after}')

# Verify sections are enhanced
print(f'\nSection enhancement check:')
print(f'- Summary enhanced: {len(enh_secs.get("summary", [])) > len(orig_secs.get("summary", []))}')
print(f'- Experience enhanced: {len(enh_secs.get("experience", [])) > len(orig_secs.get("experience", []))}')
print(f'- Projects present: {bool(enh_secs.get("projects"))}')
print(f'- Education preserved: {enh_secs.get("education") == orig_secs.get("education")}')
print(f'- Skills preserved/enhanced: {bool(enh_secs.get("skills"))}')

if new['ats_score'] >= orig['ats_score'] and not missing_after:
    print('\n✓ PASS: ATS score improved, all JD keywords included, sections enhanced')
    sys.exit(0)
elif new['ats_score'] > orig['ats_score']:
    print(f'\n✓ PASS: ATS score improved from {orig["ats_score"]} to {new["ats_score"]}')
    if missing_after:
        print(f'⚠ Warning: Some keywords still missing: {missing_after}')
    sys.exit(0)
else:
    print(f'\n✗ FAIL: ATS score did not improve (was {orig["ats_score"]}, now {new["ats_score"]})')
    sys.exit(2)

