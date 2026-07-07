#!/bin/bash
# ─────────────────────────────────────────────────────────────────────────────
# ResumeIQ — EC2 Deployment Script (Ubuntu 22.04 LTS)
# Run on your EC2 instance as ubuntu user:
#   chmod +x scripts/deploy_ec2.sh && sudo ./scripts/deploy_ec2.sh
# ─────────────────────────────────────────────────────────────────────────────

set -e
GREEN='\033[0;32m'; YELLOW='\033[1;33m'; RED='\033[0;31m'; NC='\033[0m'

log() { echo -e "${GREEN}[$(date '+%H:%M:%S')] $1${NC}"; }
warn() { echo -e "${YELLOW}[WARN] $1${NC}"; }

log "Starting ResumeIQ EC2 deployment..."

# ── System update ─────────────────────────────────────────────────────────────
log "Updating system packages..."
apt-get update -qq && apt-get upgrade -y -qq

# ── Install Docker ─────────────────────────────────────────────────────────────
if ! command -v docker &>/dev/null; then
  log "Installing Docker..."
  curl -fsSL https://get.docker.com | sh
  usermod -aG docker ubuntu
  systemctl enable docker
  systemctl start docker
else
  log "Docker already installed: $(docker --version)"
fi

# ── Install Docker Compose ─────────────────────────────────────────────────────
if ! command -v docker compose &>/dev/null; then
  log "Installing Docker Compose..."
  apt-get install -y docker-compose-plugin
else
  log "Docker Compose already installed."
fi

# ── Install monitoring tools ───────────────────────────────────────────────────
log "Installing monitoring utilities..."
apt-get install -y -qq htop curl wget unzip logrotate fail2ban

# ── Setup application directory ───────────────────────────────────────────────
APP_DIR="/opt/resumeiq"
log "Setting up app directory at $APP_DIR..."
mkdir -p $APP_DIR
cd $APP_DIR

# ── Copy env if not exists ──────────────────────────────────────────────────
if [ ! -f .env ]; then
  warn ".env not found — please copy and configure it:"
  warn "  scp .env ubuntu@<EC2-IP>:/opt/resumeiq/.env"
  warn "  Then re-run: cd /opt/resumeiq && docker compose up -d"
fi

# ── Setup log rotation ─────────────────────────────────────────────────────────
cat > /etc/logrotate.d/resumeiq << 'EOF'
/opt/resumeiq/logs/*.log {
    daily
    rotate 14
    compress
    delaycompress
    missingok
    notifempty
    sharedscripts
}
EOF
log "Log rotation configured."

# ── Setup systemd service ──────────────────────────────────────────────────────
cat > /etc/systemd/system/resumeiq.service << 'EOF'
[Unit]
Description=ResumeIQ SaaS Platform
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/opt/resumeiq
ExecStart=/usr/bin/docker compose up -d --build
ExecStop=/usr/bin/docker compose down
TimeoutStartSec=300

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable resumeiq
log "Systemd service created. ResumeIQ will auto-start on reboot."

# ── Setup fail2ban ─────────────────────────────────────────────────────────────
cat > /etc/fail2ban/jail.d/nginx.conf << 'EOF'
[nginx-http-auth]
enabled = true
maxretry = 5
bantime = 3600
EOF
systemctl enable fail2ban && systemctl restart fail2ban
log "fail2ban configured."

# ── Health check cron ─────────────────────────────────────────────────────────
(crontab -l 2>/dev/null; echo "*/5 * * * * curl -sf http://localhost/health > /dev/null || systemctl restart resumeiq") | crontab -
log "Health check cron configured."

echo ""
log "═══════════════════════════════════════════════════════════"
log "  EC2 setup complete!"
log "═══════════════════════════════════════════════════════════"
echo ""
echo "  Next steps:"
echo "  1. Upload your project: rsync -av ./ ubuntu@<EC2-IP>:/opt/resumeiq/"
echo "  2. Upload .env:         scp .env ubuntu@<EC2-IP>:/opt/resumeiq/.env"
echo "  3. Deploy:              cd /opt/resumeiq && docker compose up -d --build"
echo "  4. Check health:        curl http://<EC2-IP>/health"
echo "  5. View logs:           docker compose logs -f api"
echo ""
echo "  EC2 Security Group — open ports: 22 (SSH), 80 (HTTP), 443 (HTTPS)"
echo ""
