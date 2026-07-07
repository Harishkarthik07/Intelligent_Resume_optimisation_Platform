# ResumeIQ — Intelligent Resume Optimization Platform

> A production-level SaaS that analyzes resumes against job descriptions using ATS logic, generates AI-powered insights with Gemini, rewrites resumes, and outputs downloadable PDFs — with full user authentication including email OTP verification.

---

## Architecture

```
                        ┌──────────────────────────────────┐
                        │           Nginx                  │
                        │   (reverse proxy + rate limit)   │
                        └────────┬─────────────┬───────────┘
                                 │             │
                    ┌────────────▼───┐   ┌─────▼──────────┐
                    │  Frontend      │   │  FastAPI        │
                    │  (HTML/JS)     │   │  (Python 3.11)  │
                    │  index.html    │   │  REST API       │
                    └────────────────┘   └─────┬──────┬────┘
                                               │      │
                          ┌────────────────────┘      └──────────────┐
                          │                                           │
                   ┌──────▼──────┐                          ┌────────▼───────┐
                   │ PostgreSQL  │                          │  Services      │
                   │  (RDS/local)│                          │  ─ ATS Engine  │
                   └─────────────┘                          │  ─ Gemini AI   │
                                         ┌──────────┐       │  ─ PDF Gen     │
                                         │  Redis   │       │  ─ Parser      │
                                         │  (OTP +  │       └────────────────┘
                                         │  cache)  │
                                         └──────────┘
```

## Features

| Feature | Details |
|---|---|
| **Authentication** | JWT (access + refresh tokens), email OTP verification via SMTP |
| **Resume Upload** | PDF, DOCX, TXT — pdfplumber + python-docx parsing |
| **ATS Scoring** | Keyword match (60%) + TF-IDF semantic similarity (40%) |
| **Skill Extraction** | 200+ skills across languages, frameworks, cloud, ML, soft skills |
| **AI Insights** | Gemini 1.5 Flash — strengths, gaps, quick wins |
| **Resume Optimization** | Gemini-powered rewrite targeting the specific JD |
| **PDF Generation** | ReportLab — professional, ATS-friendly formatted PDF |
| **History** | All analyses stored per user in PostgreSQL |
| **Monitoring** | Structured JSON logging, health check endpoints, Prometheus-ready |
| **Deployment** | Dockerized, EC2-ready, systemd service, auto-restart |

---

## Quick Start — Local

### Prerequisites
- Python 3.10+
- PostgreSQL 14+ (or use Docker)
- Redis (or use Docker)
- Gemini API Key ([get one free](https://makersuite.google.com/app/apikey))
- Gmail App Password (for OTP emails)

### Option A — With Docker (Recommended)

```bash
# 1. Clone / unzip the project
cd resumeiq

# 2. Configure environment
cp .env.example .env
nano .env   # Add GEMINI_API_KEY, SMTP_USER, SMTP_PASSWORD

# 3. Start everything
docker compose up --build

# 4. Open browser
open http://localhost
# API docs: http://localhost/api/docs
```

### Option B — Without Docker

```bash
# 1. Setup
chmod +x scripts/setup_local.sh
./scripts/setup_local.sh

# 2. Start PostgreSQL & Redis separately (or via Docker)
docker compose up -d db redis

# 3. Configure
cp .env.example .env
# Edit .env — set DATABASE_URL=postgresql://resumeiq:changeme123@localhost:5432/resumeiq

# 4. Run API
cd backend
source venv/bin/activate
uvicorn main:app --reload --port 8000

# 5. Serve frontend
cd ../frontend
python3 -m http.server 3000
open http://localhost:3000
```

---

## Deploy to AWS EC2

### One-time server setup

```bash
# 1. Launch EC2 (Ubuntu 22.04 LTS, t3.small or larger)
# 2. Open ports: 22, 80, 443 in Security Group
# 3. SSH in and run:
sudo bash scripts/deploy_ec2.sh
```

### Deploy application

```bash
# From your local machine:
rsync -av --exclude='.git' --exclude='venv' --exclude='__pycache__' \
  ./ ubuntu@<EC2-IP>:/opt/resumeiq/

scp .env ubuntu@<EC2-IP>:/opt/resumeiq/.env

# On the EC2 instance:
ssh ubuntu@<EC2-IP>
cd /opt/resumeiq
docker compose up -d --build

# Verify
curl http://localhost/health
```

### AWS RDS (Optional)

```bash
# Create RDS PostgreSQL instance (t3.micro is enough for early users)
# Then update .env:
DATABASE_URL=postgresql://resumeiq:<password>@<rds-endpoint>:5432/resumeiq
```

---

## API Reference

### Authentication

| Endpoint | Method | Description |
|---|---|---|
| `/api/v1/auth/register` | POST | Register (sends OTP) |
| `/api/v1/auth/verify-otp` | POST | Verify email OTP |
| `/api/v1/auth/resend-otp` | POST | Resend OTP |
| `/api/v1/auth/login` | POST | Login → JWT |
| `/api/v1/auth/refresh` | POST | Refresh JWT |
| `/api/v1/auth/me` | GET | Current user |

### Resumes

| Endpoint | Method | Description |
|---|---|---|
| `/api/v1/resumes/upload` | POST | Upload PDF/DOCX/TXT |
| `/api/v1/resumes/` | GET | List user's resumes |
| `/api/v1/resumes/{id}` | GET | Get resume |
| `/api/v1/resumes/{id}` | DELETE | Delete resume |

### Analysis

| Endpoint | Method | Description |
|---|---|---|
| `/api/v1/analysis/run` | POST | Run ATS analysis |
| `/api/v1/analysis/optimize` | POST | AI rewrite + PDF |
| `/api/v1/analysis/{id}/download-pdf` | GET | Download optimized PDF |
| `/api/v1/analysis/history` | GET | Analysis history |

### Health

| Endpoint | Description |
|---|---|
| `/health` | Full health check (DB + Redis) |
| `/health/live` | Liveness probe |
| `/health/ready` | Readiness probe |

---

## ATS Scoring Algorithm

```
Composite ATS Score = (Keyword Score × 0.60) + (Semantic Score × 0.40)

Keyword Score:
  skill_db = 200+ skills (languages, frameworks, cloud, ML, soft skills)
  jd_skills = regex-match all skills in job description
  resume_skills = regex-match all skills in resume
  score = len(resume_skills ∩ jd_skills) / len(jd_skills) × 100

Semantic Score (TF-IDF Cosine):
  tokenize both texts, remove stopwords
  build TF-IDF frequency vectors
  score = cosine_similarity(resume_vec, jd_vec) × 600 (normalized to 0-100)
  (sentence-transformers upgrade: uncomment in requirements.txt)

Labels: 0-39 = Needs Work, 40-59 = Fair, 60-79 = Good, 80-100 = Excellent
```

---

## Environment Variables

```env
# Required
GEMINI_API_KEY=...          # Gemini 1.5 Flash API key
DATABASE_URL=...            # PostgreSQL connection string
SECRET_KEY=...              # JWT secret (min 32 chars, random)
SMTP_USER=...               # Gmail address
SMTP_PASSWORD=...           # Gmail App Password (not your account password)

# Optional
REDIS_URL=redis://...       # OTP storage (in-memory fallback if unavailable)
EMAIL_FROM=...              # From address in OTP emails
UPLOAD_DIR=./uploads        # Where uploaded files are saved
MAX_FILE_SIZE_MB=5          # Max resume upload size
OTP_EXPIRE_MINUTES=10       # OTP TTL
```

---

## Project Structure

```
resumeiq/
├── backend/
│   ├── main.py                     # FastAPI app + middleware
│   ├── requirements.txt
│   ├── Dockerfile
│   ├── alembic.ini
│   ├── alembic/env.py
│   └── app/
│       ├── core/
│       │   ├── config.py           # Settings from env
│       │   ├── database.py         # SQLAlchemy engine + session
│       │   ├── security.py         # JWT, bcrypt, OTP
│       │   ├── logging_config.py   # Structured JSON logging
│       │   └── redis_client.py     # Redis + OTP store
│       ├── models/
│       │   └── models.py           # User, Resume, Analysis tables
│       ├── schemas/
│       │   └── schemas.py          # Pydantic request/response models
│       ├── services/
│       │   ├── ats_engine.py       # Keyword + semantic scoring
│       │   ├── optimizer.py        # Gemini AI rewriter
│       │   ├── parser.py           # PDF/DOCX text extraction
│       │   ├── pdf_generator.py    # ReportLab PDF creation
│       │   └── email_service.py    # SMTP OTP + PDF emails
│       └── api/routes/
│           ├── auth.py             # Auth + JWT endpoints
│           ├── resumes.py          # Upload + CRUD
│           ├── analysis.py         # ATS analysis + optimize
│           └── health.py           # Health checks
├── frontend/
│   └── index.html                  # Complete SPA (zero dependencies)
├── nginx/
│   └── nginx.conf                  # Reverse proxy + rate limiting
├── monitoring/
│   └── prometheus.yml              # Prometheus scrape config
├── scripts/
│   ├── setup_local.sh              # One-command local setup
│   ├── deploy_ec2.sh               # EC2 bootstrap script
│   └── init.sql                    # PostgreSQL init
├── docker-compose.yml
├── .env.example
└── README.md
```

---

## Monitoring & Observability

- **Structured logs**: JSON-formatted, rotating at 10MB, 5 backups
- **Request logging**: Every request logged with ID, method, path, status, duration
- **Health endpoints**: `/health`, `/health/live`, `/health/ready`
- **Cron health check**: Auto-restarts via systemd if health check fails
- **Docker healthchecks**: Container-level liveness for all services

## Tech Stack

| Layer | Technology |
|---|---|
| API Framework | FastAPI 0.115 + Uvicorn |
| Database | PostgreSQL 15 + SQLAlchemy 2.0 |
| Cache / OTP | Redis 7 |
| AI | Google Gemini 1.5 Flash |
| PDF Parsing | pdfplumber + pypdf + python-docx |
| PDF Generation | ReportLab |
| Auth | JWT (python-jose) + bcrypt (passlib) |
| Frontend | Vanilla HTML/CSS/JS (zero build step) |
| Proxy | Nginx |
| Containerization | Docker + Docker Compose |
| Deployment | AWS EC2 + systemd |
