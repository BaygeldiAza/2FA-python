from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from sqlalchemy.orm import Session
import bcrypt

from .schemas import UserRegistration, UserLogin, OTPVerification, Token, GoogleAuthRequest, UserResponse
from .crud import create_user, get_user_by_email, generate_otp, create_oauth_user, get_user_by_oauth
from .utils import send_otp_email 
from .auth import create_access_token, verify_google_token, get_current_user
from .config import settings
from .db import get_db

router = APIRouter()


@router.post("/register/")
async def register(user: UserRegistration, db: Session = Depends(get_db)):
    email = user.email.lower().strip()
    
    # Check if user already exists
    if get_user_by_email(db, email):
        raise HTTPException(status_code=409, detail="Email already registered")

    # Hash password and create user
    hashed_password = bcrypt.hashpw(user.password.encode("utf-8"), bcrypt.gensalt())
    create_user(db, user.username, email, hashed_password.decode('utf-8'))

    return {"message": "User registered successfully"}

@router.post("/login/")
async def login(user: UserLogin, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    email = user.email.lower().strip()
    db_user = get_user_by_email(db, email)

    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    if not db_user.hashed_password:
        raise HTTPException(status_code=400, detail="Please use Google Sign-In for this account")

    if not bcrypt.checkpw(user.password.encode("utf-8"), db_user.hashed_password.encode("utf-8")):
        raise HTTPException(status_code=400, detail="Invalid credentials")

    # Generate OTP and send it
    otp = generate_otp(db, email)
    background_tasks.add_task(send_otp_email, db_user.email, otp)

    return {"message": f"OTP sent to email (expires in {settings.OTP_TTL_SECONDS} seconds)"}

@router.post("/verify_otp/", response_model=Token)
async def verify_otp(otp_data: OTPVerification, db: Session = Depends(get_db)):
    from datetime import datetime
    email = otp_data.email.lower().strip()
    db_user = get_user_by_email(db, email)
    
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if not db_user.otp_expires_at or db_user.otp_expires_at < datetime.utcnow():
        db_user.otp = None
        db_user.otp_expires_at = None
        db.commit()
        raise HTTPException(status_code=400, detail="OTP expired! Login again.")
    
    if db_user.otp != otp_data.otp:
        raise HTTPException(status_code=400, detail="Invalid OTP")
    
    # Clear OTP
    db_user.otp = None
    db_user.otp_expires_at = None
    db.commit()
    
    # Create access token
    access_token = create_access_token(data={"sub": db_user.email, "user_id": db_user.id})
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": db_user.id,
            "username": db_user.username,
            "email": db_user.email,
            "profile_picture": db_user.profile_picture,
            "is_verified": db_user.is_verified
        }
    }

@router.post("/auth/google", response_model=Token)
async def google_auth(auth_data: GoogleAuthRequest, db: Session = Depends(get_db)):
    """Handle Google OAuth authentication"""
    # Verify the Google token
    google_user = verify_google_token(auth_data.token)
    
    if not google_user:
        raise HTTPException(status_code=400, detail="Invalid Google token")
    
    email = google_user['email'].lower()
    
    # Check if user exists
    db_user = get_user_by_email(db, email)
    
    if not db_user:
        # Check if OAuth user exists
        db_user = get_user_by_oauth(db, 'google', google_user['google_id'])
    
    if not db_user:
        # Create new user
        db_user = create_oauth_user(
            db=db,
            email=email,
            username=google_user['name'],
            oauth_provider='google',
            oauth_id=google_user['google_id'],
            profile_picture=google_user.get('picture')
        )
    else:
        # Update existing user with OAuth info if not set
        if not db_user.oauth_provider:
            db_user.oauth_provider = 'google'
            db_user.oauth_id = google_user['google_id']
            db_user.profile_picture = google_user.get('picture')
            db_user.is_verified = True
            db.commit()
            db.refresh(db_user)
    
    # Create access token
    access_token = create_access_token(data={"sub": db_user.email, "user_id": db_user.id})
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": db_user.id,
            "username": db_user.username,
            "email": db_user.email,
            "oauth_provider": db_user.oauth_provider,
            "profile_picture": db_user.profile_picture,
            "is_verified": db_user.is_verified
        }
    }

@router.get("/auth/me", response_model=UserResponse)
async def read_current_user(current_user = Depends(get_current_user)):
    return current_user
    