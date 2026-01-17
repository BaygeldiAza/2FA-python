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

user_db = {}

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
     