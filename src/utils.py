import resend
import logging
from .config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

resend.api_key = settings.RESEND_API_KEY 

def send_email(to_email: str, subject: str, body: str) -> None:
    try:
        if not settings.SENDER_EMAIL or not settings.RESEND_API_KEY:
            raise RuntimeError("Missing SENDER_EMAIL or RESEND_API_KEY in .env")

        logger.info(f"Sending email to {to_email}...")

        params ={
            "from": settings.SENDER_EMAIL,
            "to": [to_email],
            "subject": subject,
            "text": body,
        }
    
        email = resend.Emails.send(params)
        logger.info(f"Email sent successfully to {to_email} (ID: {email['id']})")

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
