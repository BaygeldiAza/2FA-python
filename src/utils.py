import smtplib
import ssl
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from .config import settings


logger = logging.getLogger(__name__)


def send_email(to_email: str, subject: str, body: str) -> None:
    try:
        logger.info(f"Sending email to {to_email}...")

        message = MIMEMultipart()
        message["From"] = settings.SENDER_EMAIL
        message["To"] = to_email
        message["Subject"] = subject

        message.attach(MIMEText(body, "plain"))
        
        context = ssl.create_default_context()
        
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=60) as server:
            server.ehlo()
            server.starttls(context=context)
            server.ehlo()
            server.login(settings.SENDER_EMAIL, settings.SENDER_PASSWORD)

            server.sendmail(
                settings.SENDER_EMAIL,
                to_email,
                message.as_string(),
            )

        logger.info(f"Email sent successfully to {to_email}")

    except Exception as e:
        logger.error(f"Failed to send email to {to_email}: {type(e).__name__}: {str(e)}")
        raise




def send_otp_email(to_email: str, otp: str) -> None:
    try:
        send_email(
            to_email=to_email,
            subject="Your OTP for Login",
            body=(
                f"Your One-Time Passcode (OTP) is: {otp}\n\n"
                f"It expires in {settings.OTP_TTL_SECONDS} seconds."
            )
        )
    except Exception as e:
        logger.error(f"Failed to send OTP to {to_email}: {str(e)}")
        raise


def send_login_notification_email(to_email: str, ip: str, user_agent: str) -> None:
    from datetime import datetime
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")

    try:
        send_email(
            to_email=to_email,
            subject="Login Notification",
            body=(
                f"New login detected.\n\n"
                f"Time: {now}\n"
                f"IP: {ip}\n"
                f"Device: {user_agent}\n\n"
                "If this wasn't you, please change your password immediately."
            )
        )
    except Exception as e:
        logger.warning(
            f"Failed to send login notification to {to_email}: {str(e)}"
        )
