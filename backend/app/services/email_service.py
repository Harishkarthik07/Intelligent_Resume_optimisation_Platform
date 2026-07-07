"""
Email Service
Priority: Resend API → SMTP → Console (dev fallback)
OTP is ALWAYS printed to terminal logs so dev never blocks.
"""
import logging, json, smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from app.core.config import settings

logger = logging.getLogger(__name__)

OTP_HTML = """<!DOCTYPE html><html><head><meta charset="utf-8"></head>
<body style="font-family:Arial,sans-serif;background:#f4f4f5;margin:0;padding:40px 0">
<table width="100%" cellpadding="0" cellspacing="0"><tr><td align="center">
<table width="480" style="background:#fff;border-radius:14px;overflow:hidden;box-shadow:0 4px 20px rgba(0,0,0,0.1)">
<tr><td style="background:linear-gradient(135deg,#5b4cff,#7c6dff);padding:32px;text-align:center">
  <h1 style="color:#fff;margin:0;font-size:22px;font-weight:800;letter-spacing:-0.5px">ResumeIQ</h1>
  <p style="color:rgba(255,255,255,0.75);margin:4px 0 0;font-size:13px">Intelligent Resume Optimization Platform</p>
</td></tr>
<tr><td style="padding:36px 40px">
  <h2 style="color:#0a0a0f;margin:0 0 10px;font-size:20px;font-weight:700">Verify your email address</h2>
  <p style="color:#6b6b80;font-size:14px;line-height:1.65;margin:0 0 28px">
    Hi {name}! Use this one-time code to complete your registration.
    It expires in <strong>{ttl} minutes</strong>.
  </p>
  <div style="background:#f5f3ff;border:2px solid #e0e7ff;border-radius:12px;padding:24px;text-align:center;margin:0 0 28px">
    <span style="font-size:40px;font-weight:800;letter-spacing:12px;color:#5b4cff;font-family:monospace">{otp}</span>
  </div>
  <p style="color:#9898aa;font-size:12px;margin:0">If you didn&apos;t sign up for ResumeIQ, you can ignore this email.</p>
</td></tr>
<tr><td style="background:#f7f7fb;padding:18px 40px;text-align:center">
  <p style="color:#9898aa;font-size:12px;margin:0">&copy; 2025 ResumeIQ &middot; Bangalore, India</p>
</td></tr>
</table></td></tr></table>
</body></html>"""


def _resend_send(to: str, subject: str, html: str, attachment: dict = None) -> bool:
    """Send via Resend API. No extra package needed — uses stdlib urllib."""
    if not settings.RESEND_API_KEY:
        return False
    try:
        import urllib.request, base64
        payload = {
            "from":    f"{settings.EMAIL_FROM_NAME} <{settings.EMAIL_FROM}>",
            "to":      [to],
            "subject": subject,
            "html":    html,
        }
        if attachment:
            payload["attachments"] = [attachment]

        data = json.dumps(payload).encode()
        req  = urllib.request.Request(
            "https://api.resend.com/emails",
            data=data,
            headers={
                "Authorization": f"Bearer {settings.RESEND_API_KEY}",
                "Content-Type":  "application/json",
            },
        )
        with urllib.request.urlopen(req, timeout=12) as r:
            resp = json.loads(r.read())
            logger.info(f"Resend OK → {to} (id={resp.get('id')})")
            return True
    except Exception as e:
        logger.warning(f"Resend failed: {e}")
        return False


def _smtp_send(to: str, subject: str, html: str, pdf_path: str = None) -> bool:
    """Send via SMTP. Fallback when Resend not configured."""
    if not (settings.SMTP_USER and settings.SMTP_PASSWORD):
        return False
    try:
        msg = MIMEMultipart("mixed" if pdf_path else "alternative")
        msg["Subject"] = subject
        msg["From"]    = f"{settings.EMAIL_FROM_NAME} <{settings.EMAIL_FROM}>"
        msg["To"]      = to
        msg.attach(MIMEText(html, "html"))
        if pdf_path:
            with open(pdf_path, "rb") as f:
                part = MIMEBase("application", "octet-stream")
                part.set_payload(f.read())
            encoders.encode_base64(part)
            part.add_header("Content-Disposition", "attachment; filename=optimized_resume.pdf")
            msg.attach(part)
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=10) as s:
            s.ehlo(); s.starttls()
            s.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            s.sendmail(settings.EMAIL_FROM, to, msg.as_string())
        logger.info(f"SMTP OK → {to}")
        return True
    except Exception as e:
        logger.warning(f"SMTP failed: {e}")
        return False


class EmailService:
    def send_otp(self, to_email: str, full_name: str, otp: str) -> bool:
        first   = (full_name or "there").split()[0]
        subject = f"{otp} — Your ResumeIQ verification code"
        html    = OTP_HTML.format(name=first, otp=otp, ttl=settings.OTP_EXPIRE_MINUTES)

        sent = _resend_send(to_email, subject, html) or _smtp_send(to_email, subject, html)

        # ── ALWAYS log OTP ── critical for dev/test when email not configured ──
        border = "=" * 58
        if sent:
            logger.info(f"OTP email sent to {to_email}")
        else:
            logger.warning(border)
            logger.warning(f"  EMAIL NOT SENT — OTP for {to_email}:")
            logger.warning(f"  >>>  {otp}  <<<   (valid {settings.OTP_EXPIRE_MINUTES} min)")
            logger.warning(f"  Use this code to verify your account.")
            logger.warning(border)
        return sent

    def send_optimized_pdf(self, to_email: str, full_name: str, pdf_path: str) -> bool:
        first   = (full_name or "there").split()[0]
        subject = "Your Optimized Resume — ResumeIQ"
        html    = f"""<div style="font-family:Arial,sans-serif;max-width:520px;margin:0 auto;padding:28px">
<h2 style="color:#5b4cff">Your optimized resume is ready!</h2>
<p>Hi {first}, your AI-optimized resume is attached.</p>
<ul style="color:#6b6b80;font-size:14px;line-height:1.8">
<li>Review every bullet — only keep achievements you can speak to</li>
<li>Replace [X%] placeholders with your real numbers</li>
</ul>
<p style="color:#9898aa;font-size:12px;margin-top:20px">— The ResumeIQ Team</p>
</div>"""

        # Resend with attachment
        if settings.RESEND_API_KEY and pdf_path:
            try:
                import base64
                with open(pdf_path, "rb") as f:
                    enc = base64.b64encode(f.read()).decode()
                attachment = {"filename": "optimized_resume.pdf", "content": enc}
                if _resend_send(to_email, subject, html, attachment):
                    return True
            except Exception as e:
                logger.warning(f"Resend PDF attachment failed: {e}")

        # SMTP with attachment
        return _smtp_send(to_email, subject, html, pdf_path)


email_service = EmailService()
