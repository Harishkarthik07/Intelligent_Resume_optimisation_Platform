import os
import sys
import time

sys.path.insert(0, os.path.abspath('backend'))

import requests
from app.core import database
from app.core.security import hash_password, create_access_token
from app.models.models import User, Resume

BASE_URL = 'http://127.0.0.1:8000'


def seed_user_and_resume():
    database.init_db()
    session = database.SessionLocal()
    try:
        email = 'dev_e2e@example.com'
        user = session.query(User).filter(User.email == email).first()
        if not user:
            user = User(
                email=email,
                hashed_pw=hash_password('password123'),
                full_name='Dev E2E User',
                is_verified=True,
                status='active',
            )
            session.add(user)
            session.commit()
            session.refresh(user)

        resume = session.query(Resume).filter(Resume.user_id == user.id).first()
        if not resume:
            sample_text = '''Dev E2E User\nSoftware Engineer\n\nPROFESSIONAL SUMMARY\nExperienced backend engineer with strong Python and cloud experience.\n\nWORK EXPERIENCE\nAcme Corp — Backend Engineer (2021-Present)\n- Built web APIs using Python and Flask\n- Managed Postgres databases\n- Supported AWS deployments\n\nPROJECTS\n- Created internal automation tooling\n- Built data ingestion pipelines\n\nEDUCATION\nBS Computer Science, State University\n\nTECHNICAL SKILLS\nPython, AWS, PostgreSQL, Docker, FastAPI, Flask'''
            resume = Resume(
                user_id=user.id,
                raw_text=sample_text,
                original_filename='dev_e2e_resume.txt',
                word_count=len(sample_text.split()),
            )
            session.add(resume)
            session.commit()
            session.refresh(resume)

        token = create_access_token(user.id)
        return token, user.id, resume.id
    finally:
        session.close()


def run_request(method, path, token=None, **kwargs):
    url = BASE_URL + path
    headers = kwargs.pop('headers', {})
    if token:
        headers['Authorization'] = f'Bearer {token}'
    response = requests.request(method, url, headers=headers, timeout=30, **kwargs)
    return response


def main():
    print('Checking server...')
    try:
        r = requests.get(BASE_URL + '/')
        print('root status', r.status_code, r.text)
    except Exception as e:
        print('server check failed:', e)
        sys.exit(1)

    token, user_id, resume_id = seed_user_and_resume()
    print('SEED TOKEN', token)
    print('USER_ID', user_id)
    print('RESUME_ID', resume_id)

    jd_text = 'Looking for a Senior Software Engineer with experience in Python, FastAPI, Docker, AWS, PostgreSQL, and microservices architecture.'
    body = {
        'resume_id': resume_id,
        'jd_text': jd_text,
        'jd_title': 'Senior Software Engineer'
    }
    print('\nRunning analysis...')
    analysis_resp = run_request('POST', '/api/v1/analysis/run', token=token, json=body)
    print('analysis status', analysis_resp.status_code)
    print('analysis body', analysis_resp.text)
    if analysis_resp.status_code != 201:
        sys.exit(2)
    analysis_id = analysis_resp.json().get('analysis_id')

    print('\nRunning optimize...')
    optim_resp = run_request('POST', '/api/v1/analysis/optimize', token=token, json={'analysis_id': analysis_id})
    print('optimize status', optim_resp.status_code)
    print('optimize body', optim_resp.text[:4000])
    if optim_resp.status_code != 200:
        sys.exit(3)

    pdf_url = optim_resp.json().get('pdf_url')
    if not pdf_url:
        print('No pdf_url in response')
        sys.exit(4)

    print('\nDownloading PDF...')
    pdf_resp = run_request('GET', pdf_url, token=token, stream=True)
    print('pdf status', pdf_resp.status_code)
    if pdf_resp.status_code == 200:
        out_path = os.path.abspath('scripts/optimized_resume_test.pdf')
        with open(out_path, 'wb') as f:
            for chunk in pdf_resp.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        print('PDF saved to', out_path)
    else:
        print('PDF request failed:', pdf_resp.text)
        sys.exit(5)

    print('\nCompleted end-to-end flow successfully.')


if __name__ == '__main__':
    main()
