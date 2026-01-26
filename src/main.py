from fastapi import FastAPI, HTTPException, BackgroundTasks, Request
from pydantic import BaseModel, EmailStr, Field
import bcrypt
import secrets
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import os
import ssl
import time
from pathlib import Path
from dotenv import load_dotenv
from datetime import datetime, timezone

# Load environment variables
load_dotenv(Path(__file__).resolve().parent / ".env")

app = FastAPI()

SENDER_EMAIL = os.getenv("SENDER_EMAIL")
SENDER_PASSWORD = os.getenv("SENDER_PASSWORD")

OTP_TTL_SECONDS = 120
OTP_LEN = 6

# Store users by EMAIL for fast lookup
# users_db[email] = {"username": ..., "password": ..., "otp": ..., "otp_expires_at": ...}
users_db: dict[str, dict] = {}


def require_email_config():
    if not SENDER_EMAIL or not SENDER_PASSWORD:
        raise RuntimeError(
            "Missing SENDER_EMAIL or SENDER_PASSWORD in .env. "
            "For Gmail, use an App Password (not your normal password)."
        )


def send_email(to_email: str, subject: str, body: str) -> None:
    """
    Send email via Gmail SMTP. This runs in background task.
    IMPORTANT: Do NOT raise HTTPException here (client won't see it).
    """
    try:
        require_email_config()

        msg = MIMEMultipart()
        msg["From"] = SENDER_EMAIL
        msg["To"] = to_email
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))

        context = ssl.create_default_context()
        with smtplib.SMTP("smtp.gmail.com", 587, timeout=60) as server:
            server.ehlo()
            server.starttls(context=context)
            server.ehlo()
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.sendmail(SENDER_EMAIL, to_email, msg.as_string())

    except Exception as e:
        # Background tasks should not crash the request
        print(f"EMAIL ERROR to={to_email} subject={subject} err={repr(e)}")


def send_otp_email(to_email: str, otp: str) -> None:
    send_email(
        to_email=to_email,
        subject="Your OTP for Login",
        body=f"Your One-Time Passcode (OTP) is: {otp}\n\nIt expires in {OTP_TTL_SECONDS} seconds."
    )


def send_login_notification_email(to_email: str, ip: str, user_agent: str) -> None:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    send_email(
        to_email=to_email,
        subject="Login Notification",
        body=(
            "New login detected.\n\n"
            f"Time: {now}\n"
            f"IP: {ip}\n"
            f"Device: {user_agent}\n\n"
            "If this wasn't you, please change your password."
        )
    )


class UserRegistration(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class OTPVerification(BaseModel):
    email: EmailStr
    otp: str = Field(min_length=OTP_LEN, max_length=OTP_LEN)


@app.get("/")
async def root():
    return {"status": "success", "message": "API is running"}


@app.post("/register/")
async def register(user: UserRegistration):
    email = user.email.lower().strip()

    if email in users_db:
        raise HTTPException(status_code=409, detail="Email already registered")

    hashed_password = bcrypt.hashpw(user.password.encode("utf-8"), bcrypt.gensalt())

    users_db[email] = {
        "username": user.username,
        "password": hashed_password,
        "otp": None,
        "otp_expires_at": None,
        "otp_attempts": 0,   # optional: basic brute-force protection
    }
    return {"message": "User registered successfully"}


@app.post("/login/")
async def login(user: UserLogin, background_tasks: BackgroundTasks):
    email = user.email.lower().strip()
    db_user = users_db.get(email)

    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    if not bcrypt.checkpw(user.password.encode("utf-8"), db_user["password"]):
        raise HTTPException(status_code=400, detail="Invalid credentials")

    # Generate OTP
    otp = f"{secrets.randbelow(1_000_000):06d}"
    db_user["otp"] = otp
    db_user["otp_expires_at"] = time.time() + OTP_TTL_SECONDS
    db_user["otp_attempts"] = 0

    # Send OTP email in background
    background_tasks.add_task(send_otp_email, email, otp)

    return {"message": f"OTP sent to email (expires in {OTP_TTL_SECONDS} seconds)"}


@app.post("/verify_otp/")
async def verify_otp(
    otp_data: OTPVerification,
    background_tasks: BackgroundTasks,
    request: Request
):
    email = otp_data.email.lower().strip()
    db_user = users_db.get(email)

    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    stored_otp = db_user.get("otp")
    expires_at = db_user.get("otp_expires_at")

    if not stored_otp or not expires_at:
        raise HTTPException(status_code=400, detail="No OTP requested. Please login again.")

    if time.time() >= expires_at:
        db_user["otp"] = None
        db_user["otp_expires_at"] = None
        raise HTTPException(status_code=400, detail="OTP expired! Login again.")

    # Optional brute-force protection
    db_user["otp_attempts"] += 1
    if db_user["otp_attempts"] > 5:
        db_user["otp"] = None
        db_user["otp_expires_at"] = None
        raise HTTPException(status_code=429, detail="Too many OTP attempts. Login again.")

    # Constant-time compare
    if not secrets.compare_digest(stored_otp, otp_data.otp.strip()):
        raise HTTPException(status_code=400, detail="Invalid OTP")

    # Success: clear OTP
    db_user["otp"] = None
    db_user["otp_expires_at"] = None
    db_user["otp_attempts"] = 0

    ip = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "unknown")
    background_tasks.add_task(send_login_notification_email, email, ip, user_agent)

    return {"message": "Login successful"}
