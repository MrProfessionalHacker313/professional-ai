"""
Professional AI - Email Service
Handles transactional emails: login alerts, password resets, notifications.
"""

from typing import Optional
from loguru import logger
import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.config import settings


class EmailService:
    """Async email service using SMTP."""

    async def send_email(self, to_email: str, subject: str, html_content: str, text_content: str):
        """Send email via SMTP."""
        if not settings.SMTP_HOST or not settings.SMTP_USER:
            logger.warning("SMTP not configured - email not sent")
            return

        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = settings.SMTP_FROM or settings.SMTP_USER
        msg["To"] = to_email

        msg.attach(MIMEText(text_content, "plain"))
        msg.attach(MIMEText(html_content, "html"))

        try:
            await aiosmtplib.send(
                msg,
                hostname=settings.SMTP_HOST,
                port=settings.SMTP_PORT,
                username=settings.SMTP_USER,
                password=settings.SMTP_PASSWORD,
                use_tls=True,
            )
            logger.info(f"Email sent to {to_email}: {subject}")
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {e}")

    async def send_login_alert(self, to_email: str, ip_address: str, user_agent: str, timestamp: str):
        """Send login alert email."""
        subject = "New login to your Professional AI account"
        text_content = f"""
New login detected on your Professional AI account.

Time: {timestamp}
IP Address: {ip_address}
Device: {user_agent}

If this was you, no action is needed.
If you didn't log in, please secure your account immediately.
        """.strip()
        html_content = f"""
<html>
<body>
    <h2>New Login Detected</h2>
    <p>A new login was detected on your Professional AI account:</p>
    <ul>
        <li><strong>Time:</strong> {timestamp}</li>
        <li><strong>IP Address:</strong> {ip_address}</li>
        <li><strong>Device:</strong> {user_agent}</li>
    </ul>
    <p>If this was you, no action is needed.</p>
    <p>If you didn't log in, please secure your account immediately.</p>
</body>
</html>
        """.strip()
        await self.send_email(to_email, subject, html_content, text_content)

    async def send_password_reset(self, to_email: str, reset_token: str):
        """Send password reset email."""
        reset_url = f"{settings.FRONTEND_URL}/reset-password?token={reset_token}"
        subject = "Reset your Professional AI password"
        text_content = f"""
You requested a password reset for your Professional AI account.

Click this link to reset your password:
{reset_url}

This link expires in 1 hour.
If you didn't request this, please ignore this email.
        """.strip()
        html_content = f"""
<html>
<body>
    <h2>Password Reset Request</h2>
    <p>You requested a password reset for your Professional AI account.</p>
    <p><a href="{reset_url}">Click here to reset your password</a></p>
    <p>This link expires in 1 hour.</p>
    <p>If you didn't request this, please ignore this email.</p>
</body>
</html>
        """.strip()
        await self.send_email(to_email, subject, html_content, text_content)

    async def send_security_alert(self, to_email: str, subject: str, body: str):
        """Send security alert email."""
        html_content = f"""
<html>
<body>
    <h2>Security Alert</h2>
    <p>{body.replace(chr(10), '<br>')}</p>
    <p>If this was not you, please secure your account immediately.</p>
    <p>Contact support if you need assistance.</p>
</body>
</html>
        """.strip()
        await self.send_email(to_email, subject, html_content, body)
