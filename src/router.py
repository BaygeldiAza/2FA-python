from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends, Request
from sqlalchemy.orm import Session
import bcrypt
import os
from pathlib import Path
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from .schemas import UserRegistration, UserLogin, OTPVerification, Token, GoogleAuthRequest, UserResponse
from .crud import create_user, get_user_by_email, generate_otp, create_oauth_user, get_user_by_oauth
from .utils import send_otp_email 
from .auth import create_access_token, verify_google_token, get_current_user
from .config import settings
from .db import get_db

router = APIRouter()

# Fix template directory path - make it more robust
BASE_DIR = Path(__file__).resolve().parent
templates_dir = BASE_DIR / "templates"

# Debug template directory
print(f"Router BASE_DIR: {BASE_DIR}")
print(f"Templates directory: {templates_dir}")
print(f"Templates directory exists: {templates_dir.exists()}")

if templates_dir.exists():
    templates = Jinja2Templates(directory=str(templates_dir))
else:
    # Try alternative path
    templates_dir = Path(os.path.dirname(os.path.abspath(__file__))) / "templates"
    print(f"Trying alternative path: {templates_dir}")
    templates = Jinja2Templates(directory=str(templates_dir))

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

@router.get("/", response_class=HTMLResponse)
async def root(request: Request):
    # Debug: Print what we're sending to template
    client_id = settings.GOOGLE_CLIENT_ID
    print(f"Rendering template with GOOGLE_CLIENT_ID: {client_id[:20] if client_id else 'NONE'}...")
    
    if not client_id:
        print("❌ ERROR: GOOGLE_CLIENT_ID is None or empty!")
    
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "google_client_id": client_id or ""  # Provide empty string as fallback
        }
    )

@router.get("/debug/check-config")
async def check_config():
    """Debug endpoint to check configuration"""
    return {
        "google_client_id_exists": bool(settings.GOOGLE_CLIENT_ID),
        "google_client_id_length": len(settings.GOOGLE_CLIENT_ID) if settings.GOOGLE_CLIENT_ID else 0,
        "google_client_id_preview": settings.GOOGLE_CLIENT_ID[:20] + "..." if settings.GOOGLE_CLIENT_ID else "EMPTY",
        "templates_dir": str(templates_dir),
        "templates_dir_exists": templates_dir.exists(),
        "template_files": list(templates_dir.glob("*.html")) if templates_dir.exists() else []
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