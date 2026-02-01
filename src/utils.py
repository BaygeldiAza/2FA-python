import smtplib 
from email.mime.multipart import MIMEMultipart 
from email.mime.text import MIMEText
import ssl
import logging
from .config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def send_email(to_email: str, subject: str, body: str) -> None:
    try:
        if not settings.SENDER_EMAIL or not settings.SENDER_PASSWORD:
            raise RuntimeError("Missing SENDER_EMAIL or SENDER_PASSWORD in .env")
        
        msg = MIMEMultipart()
        msg["From"] = settings.SENDER_EMAIL
        msg["To"] = to_email
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))

        logger.info(f"Sending email to {to_email}...")
        context = ssl.create_default_context()
        
        with smtplib.SMTP("smtp.gmail.com", 587, timeout=60) as server:
            server.ehlo()
            logger.debug("EHLO sent")
            
            server.starttls(context=context)
            logger.debug("TLS started")
            
            server.ehlo()
            server.login(settings.SENDER_EMAIL, settings.SENDER_PASSWORD)
            logger.debug("Login successful")
            
            server.sendmail(settings.SENDER_EMAIL, to_email, msg.as_string())
            logger.info(f"Email sent successfully to {to_email}")
            
    except smtplib.SMTPAuthenticationError as e:
        logger.error(f"SMTP Authentication failed: {str(e)}")
        logger.error(f"Check SENDER_EMAIL ({settings.SENDER_EMAIL}) and SENDER_PASSWORD")
        logger.error("If using Gmail: Enable 2FA and create an App Password")
        raise  # Re-raise so caller knows it failed
        
    except smtplib.SMTPException as e:
        logger.error(f"SMTP error sending to {to_email}: {str(e)}")
        raise
        
    except TimeoutError as e:
        logger.error(f"Timeout connecting to Gmail SMTP: {str(e)}")
        raise
        
    except Exception as e:
        logger.error(f"Unexpected error sending email to {to_email}: {type(e).__name__}: {str(e)}")
        raise


def send_otp_email(to_email: str, otp: str) -> None:
    try:
        send_email(
            to_email=to_email,
            subject="Your OTP for Login",
            body=f"Your One-Time Passcode (OTP) is: {otp}\n\nIt expires in {settings.OTP_TTL_SECONDS} seconds."
        )
    except Exception as e:
        logger.error(f"Failed to send OTP to {to_email}: {str(e)}")
        raise  # Let the caller handle it


def send_login_notification_email(to_email: str, ip: str, user_agent: str) -> None:
    from datetime import datetime
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")
    
    try:
        send_email(
            to_email=to_email,
            subject="Login Notification",
            body=(
                f"New login detected.\n\n"
                f"Time: {now}\n"
                f"IP: {ip}\n"
                f"Device: {user_agent}\n\n"
                "If this wasn't you, please change your password."
            )
        )
    except Exception as e:
        # Login notifications are non-critical, just log the error
        logger.warning(f"Failed to send login notification to {to_email}: {str(e)}")
        # Don't raise - notification failure shouldn't block login