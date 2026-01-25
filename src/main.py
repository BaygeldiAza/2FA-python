from fastapi import FastAPI, HTTPException, BackgroundTasks, Request
from pydantic import BaseModel
import bcrypt
import secrets
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import os
import time
import ssl
from pathlib import Path
from dotenv import load_dotenv
from datetime import datetime, timezone

# Load environment variables from the .env file
load_dotenv(Path(__file__).resolve().parent / ".env")

# Initialize FastAPI app
app = FastAPI()

# In-memory user store (You can replace this with a database)
users_db = {}

# Load email credentials from environment variables
SENDER_EMAIL = os.getenv("SENDER_EMAIL")
SENDER_PASSWORD = os.getenv("SENDER_PASSWORD")

OTP_TTL_SECONDS = 120


# Helper function to send OTP email
def send_otp_email(to_email: str, otp: str):
    try:
        msg = MIMEMultipart()
        msg["From"] = SENDER_EMAIL
        msg["To"] = to_email
        msg["Subject"] = "Your OTP for Login"

        body = f"Your One-Time Passcode (OTP) is: {otp}"
        msg.attach(MIMEText(body, "plain"))

        sslcreate = ssl.create_default_context()
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.ehlo()
            server.starttls(context=sslcreate)
            server.ehlo()
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.sendmail(SENDER_EMAIL, to_email, msg.as_string())

    except Exception as e:
        print("SMTP ERROR:", repr(e))  # show in uvicorn terminal
        raise HTTPException(status_code=500, detail=f"Error sending email: {e}")


# Login notification email
def send_login_notification_email(to_email: str, ip: str = "unknown", user_agent: str = "unknown"):
    try:
        msg = MIMEMultipart()
        msg["From"] = SENDER_EMAIL
        msg["To"] = to_email
        msg["Subject"] = "Login Notification"

        now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        body = (
            "New login detected.\n\n"
            f"Time: {now}\n"
            f"IP: {ip}\n"
            f"Device: {user_agent}\n\n"
            "If this wasn't you, please change your password."
        )
        msg.attach(MIMEText(body, "plain"))

        sslcreate = ssl.create_default_context()
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.ehlo()
            server.starttls(context=sslcreate)
            server.ehlo()
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.sendmail(SENDER_EMAIL, to_email, msg.as_string())

    except Exception as e:
        # Don't fail login if notification fails
        print("LOGIN NOTIFICATION SMTP ERROR:", repr(e))


# Define Pydantic models for request validation
class UserRegistration(BaseModel):
    username: str
    email: str
    password: str


class UserLogin(BaseModel):
    email: str
    password: str


class OTPVerification(BaseModel):
    email: str
    otp: str


# Route to register a user
@app.post("/register/")
async def register(user: UserRegistration):
    hashed_password = bcrypt.hashpw(user.password.encode("utf-8"), bcrypt.gensalt())

    users_db[user.username] = {
        "password": hashed_password,
        "email": user.email,
        "otp": None,
        "otp_expires_at": None,
    }
    return {"message": "User registered successfully"}


@app.post("/login/")
async def login(user: UserLogin, background_tasks: BackgroundTasks):
    # Find user by email
    found_username = None
    for username, data in users_db.items():
        if data["email"] == user.email:
            found_username = username
            break

    if found_username is None:
        raise HTTPException(status_code=404, detail="User not found")

    # Verify password
    stored_password = users_db[found_username]["password"]
    if not bcrypt.checkpw(user.password.encode("utf-8"), stored_password):
        raise HTTPException(status_code=400, detail="Invalid credentials")

    # Generate OTP (secure) and send it
    otp = f"{secrets.randbelow(1_000_000):06d}"
    users_db[found_username]["otp"] = otp
    users_db[found_username]["otp_expires_at"] = time.time() + OTP_TTL_SECONDS

    # Send OTP email in background (non-blocking)
    background_tasks.add_task(send_otp_email, user.email, otp)

    return {"message": "OTP sent to email (expires in 2 minutes)"}


@app.post("/verify_otp/")
async def verify_otp(otp_data: OTPVerification, background_tasks: BackgroundTasks, request: Request):
    # Find user by email
    found_username = None
    for username, data in users_db.items():
        if data["email"] == otp_data.email:
            found_username = username
            break

    if found_username is None:
        raise HTTPException(status_code=404, detail="User not found")

    stored_otp = users_db[found_username].get("otp")
    expires_at = users_db[found_username].get("otp_expires_at")

    if stored_otp is None or expires_at is None:
        raise HTTPException(status_code=400, detail="No OTP requested. Please login again.")

    if time.time() >= expires_at:
        users_db[found_username]["otp"] = None
        users_db[found_username]["otp_expires_at"] = None
        raise HTTPException(status_code=400, detail="OTP expired! Login again.")

    if stored_otp != otp_data.otp.strip():
        raise HTTPException(status_code=400, detail="Invalid OTP")

    # Clear after success
    users_db[found_username]["otp"] = None
    users_db[found_username]["otp_expires_at"] = None

    # Send login notification (non-blocking)
    ip = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "unknown")
    background_tasks.add_task(send_login_notification_email, otp_data.email, ip, user_agent)

    return {"message": "Login successful"}
