from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import bcrypt
import random 
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import os
from dotenv import load_dotenv


load_dotenv()

app = FastAPI

users_db = {}

SENDER_EMAIL = os.getenv("SENDER_EMAIL")
SENDER_PASSWORD = os.getenv("SENDER_PASSWORD")

def send_otp_email(to_email, otp):
    try:
        msg = MIMEMultipart()
        msg['From'] = SENDER_EMAIL
        msg['To'] = to_email
        msg['Subject'] = 'Your OTP for Login'

        body = f'Your One-Time Passcode (OTP) is: {otp}'
        msg.attach(MIMEText(body, 'plain'))

        server = smtplib.STMP('smtp.gmail.com', 587)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.sendmail(SENDER_EMAIL, to_email, msg.as_string())
        server.quit()

    except Exception as e:
        raise HTTPException(status_code=500, detail="Error sending email.")


class UserRegistration(BaseModel):
    username: str
    password: str
    email: str

class UserLogin(BaseModel):
    username: str
    password: str

class OTPVerification(BaseModel):
    username: str
    otp: str

@app.post("/register")
async def register(user: UserRegistration):
    hashed_password = bcrypt.hashpw(user.password.encode('utf-8'), bcrypt.gensalt())

    users_db[user.username] = {
        'password': hashed_password,
        'email': user.email,
        'otp': None
    }
    return {"message": "User registered successfully"}

@app.post("/login/")
async def login(user: UserLogin):
    if user.username not in users_db:
        raise HTTPException(status_code=404, detail="User not found")
    
    stored_password = users_db[user.username] ['password']
    if not bcrypt.checkpw(user.password.encode('utf-8'), stored_password):
        raise HTTPException(status_code=400, detail="Invalid credentials")
    
    otp = random.randint(100000, 999999)
    users_db[user.username]['otp'] = otp
    send_otp_email(users_db[user.username]['email'], otp)

    return {"message": "OTP sent to email"}

@app.post("/verify_otp/")
async def verify_otp(otp_data: OTPVerification):
    if otp_data.username not in users_db:
        raise HTTPException(status_code=404, detail="User not found")
    
    stored_otp = users_db[otp_data.username]['otp']
    if str(stored_otp) != otp_data.otp:
        raise HTTPException(status_code=400, detail="Invalid OTP")
    
    return {"message": "Login successful"}
