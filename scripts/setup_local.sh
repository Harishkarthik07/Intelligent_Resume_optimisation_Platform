#!/bin/bash
# ─────────────────────────────────────────────────────────────────────────────
# ResumeIQ — Local Development Setup Script
# Run: chmod +x scripts/setup_local.sh && ./scripts/setup_local.sh
# ─────────────────────────────────────────────────────────────────────────────

set -e
GREEN='\033[0;32m'; YELLOW='\033[1;33m'; RED='\033[0;31m'; NC='\033[0m'

echo -e "${GREEN}╔══════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║     ResumeIQ — Local Dev Setup           ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════╝${NC}"

# ── Check Python ────────────────────────────────────────────────────────────
if ! command -v python3 &>/dev/null; then
  echo -e "${RED}✗ Python 3 not found. Please install Python 3.10+${NC}"; exit 1
fi
echo -e "${GREEN}✓ Python: $(python3 --version)${NC}"

# ── Check PostgreSQL ─────────────────────────────────────────────────────────
if ! command -v psql &>/dev/null; then
  echo -e "${YELLOW}⚠ PostgreSQL not found. You can use Docker: docker-compose up db${NC}"
else
  echo -e "${GREEN}✓ PostgreSQL: $(psql --version)${NC}"
fi

# ── Setup .env ───────────────────────────────────────────────────────────────
if [ ! -f .env ]; then
  cp .env.example .env
  echo -e "${YELLOW}⚠ Created .env from .env.example — please fill in your API keys!${NC}"
  echo -e "${YELLOW}  Required: GEMINI_API_KEY, SMTP_USER, SMTP_PASSWORD${NC}"
fi

# ── Create virtualenv ─────────────────────────────────────────────────────────
cd backend
if [ ! -d "venv" ]; then
  echo "Creating virtual environment..."
  python3 -m venv venv
fi
source venv/bin/activate
echo -e "${GREEN}✓ Virtual environment activated${NC}"

# ── Install deps ─────────────────────────────────────────────────────────────
echo "Installing Python dependencies..."
pip install --upgrade pip -q
pip install -r requirements.txt -q
echo -e "${GREEN}✓ Dependencies installed${NC}"

# ── Create directories ────────────────────────────────────────────────────────
mkdir -p uploads/optimized logs
echo -e "${GREEN}✓ Directories created${NC}"

cd ..

echo ""
echo -e "${GREEN}═══════════════════════════════════════════════════${NC}"
echo -e "${GREEN}  Setup complete! Next steps:                      ${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════${NC}"
echo ""
echo -e "  1. Edit ${YELLOW}.env${NC} and add your API keys"
echo -e "  2. Start PostgreSQL:  ${YELLOW}docker-compose up -d db redis${NC}"
echo -e "  3. Run the API:       ${YELLOW}cd backend && source venv/bin/activate && uvicorn main:app --reload${NC}"
echo -e "  4. Open the frontend: ${YELLOW}open frontend/index.html${NC}"
echo -e "     or serve it:       ${YELLOW}cd frontend && python3 -m http.server 3000${NC}"
echo ""
echo -e "  API Docs: ${YELLOW}http://localhost:8000/api/docs${NC}"
echo -e "  Health:   ${YELLOW}http://localhost:8000/health${NC}"
echo ""
