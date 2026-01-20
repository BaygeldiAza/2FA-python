from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import bcrypt
import random
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import os
import ssl
from pathlib import Path 
from dotenv import load_dotenv

# Load environment variables from the .env file
load_dotenv(Path(__file__).resolve().parent / ".env")

# Initialize FastAPI app
app = FastAPI()

# In-memory user store (You can replace this with a database)
users_db = {}

# Load email credentials from environment variables
SENDER_EMAIL = os.getenv("SENDER_EMAIL")
SENDER_PASSWORD = os.getenv("SENDER_PASSWORD")

# Helper function to send OTP email
def send_otp_email(to_email, otp):
    try:
        # Create the email message
        msg = MIMEMultipart()
        msg['From'] = SENDER_EMAIL
        msg['To'] = to_email
        msg['Subject'] = 'Your OTP for Login'

        body = f'Your One-Time Passcode (OTP) is: {otp}'
        msg.attach(MIMEText(body, 'plain'))

        # Setup the SMTP server and send the email
        context = ssl.create_default_context()
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.ehlo()
            server.starttls(context=ssl.create_default_context())
            server.ehlo()
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.sendmail(SENDER_EMAIL, to_email, msg.as_string())
            server.quit()

    except Exception as e:
        print("SMTP ERROR:", repr(e))  # show in uvicorn terminal
        raise HTTPException(status_code=500, detail=f"Error sending email: {e}")


# Define Pydantic models for request validation
class UserRegistration(BaseModel):
    username: str
    password: str
    email: str

class UserLogin(BaseModel):
    email: str
    password: str

class OTPVerification(BaseModel):
    email: str
    otp: str

# Route to register a user
@app.post("/register/")
async def register(user: UserRegistration):
    # Hash password before storing (bcrypt)
    hashed_password = bcrypt.hashpw(user.password.encode('utf-8'), bcrypt.gensalt())
    
    # Simulate storing the user in an in-memory database
    users_db[user.username] = {
        'password': hashed_password,
        'email': user.email,
        'otp': None
    }
    return {"message": "User registered successfully"}

@app.post("/login/")
async def login(user: UserLogin):
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

    # Generate OTP and send it
    otp = random.randint(100000, 999999)
    users_db[found_username]["otp"] = otp
    send_otp_email(user.email, otp)

    return {"message": "OTP sent to email"}

@app.post("/verify_otp/")
async def verify_otp(otp_data: OTPVerification):
    # Find user by email
    found_username = None
    for username, data in users_db.items():
        if data["email"] == otp_data.email:
            found_username = username
            break

    if found_username is None:
        raise HTTPException(status_code=404, detail="User not found")

    # Verify OTP
    stored_otp = users_db[found_username]["otp"]
    if stored_otp is None or str(stored_otp) != otp_data.otp:
        raise HTTPException(status_code=400, detail="Invalid OTP")

    # Optional: clear OTP after use
    users_db[found_username]["otp"] = None

    return {"message": "Login successful"}
