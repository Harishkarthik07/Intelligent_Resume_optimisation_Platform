import sys, os
sys.path.insert(0, os.path.abspath('backend'))

from app.core import database
from app.core.security import hash_password, create_access_token
from app.models.models import User, Resume

# Create a dev user and resume in the DB
database.init_db()
session = database.SessionLocal()
try:
    email = 'dev@example.com'
    user = session.query(User).filter(User.email == email).first()
    if not user:
        user = User(email=email, hashed_pw=hash_password('password123'), full_name='Dev User', is_verified=True, status='active')
        session.add(user)
        session.commit()
        session.refresh(user)

    # Create a sample resume if not exists
    resume = session.query(Resume).filter(Resume.user_id == user.id).first()
    if not resume:
        sample_text = '''Dev User\nSoftware Engineer\n\nPROFESSIONAL SUMMARY\nExperienced developer with backend experience in Python and cloud deployments.\n\nWORK EXPERIENCE\nCompany A — Backend Engineer\n- Built APIs\n\nPROJECTS\n- Internal tool\n\nEDUCATION\nBS Computer Science\n\nTECHNICAL SKILLS\nPython, Docker, AWS, PostgreSQL'''
        resume = Resume(user_id=user.id, raw_text=sample_text, original_filename='dev_resume.txt')
        session.add(resume)
        session.commit()
        session.refresh(resume)

    token = create_access_token(user.id)
    print('ACCESS_TOKEN=' + token)
    print('USER_ID=' + user.id)
    print('RESUME_ID=' + resume.id)
finally:
    session.close()
