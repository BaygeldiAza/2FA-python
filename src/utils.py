import smtplib 
from email.mime.multipart import MIMEMultipart 
from email.mime.text import MIMEText
import ssl
from .config import settings

def send_email(to_email: str, subject: str, body: str) -> None:
    try:
        if not settings.SENDER_EMAIL or not settings.SENDER_PASSWORD:
            raise RuntimeError("Missing SENDER_EMAIL or SENDER_PASSWORD in .env")
        
        msg = MIMEMultipart()
        msg["From"] = settings.SENDER_EMAIL
        msg["To"] = to_email
        msg["Subject"] =subject
        msg.attach(MIMEText(body,"plain"))

        context = ssl.create_default_context()
        with smtplib.SMTP("smtp.gmail.com", 587, timeout=60) as server:
            server.ehlo()
            server.starttls(context=context)
            server.ehlo()
            server.login(settings.SENDER_EMAIL,settings.SENDER_PASSWORD)
            server.sendmail(settings.SENDER_EMAIL, to_email, msg.as_string())
    except Exception as e:
        print(f"error sending email to {to_email}")

def send_otp_email(to_email: str, otp: str) -> None:
    send_email(
        to_email=to_email,
        subject="Your OTP for Login",
        body=f"Your One-Time Passcode (OTP) is: {otp}\n\nIt expires in {settings.OTP_TTL_SECONDS} seconds."
    )


def send_login_notification_email(to_email: str, ip: str, user_agent: str)-> None:
    from datetime import datetime
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")
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