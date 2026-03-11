from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends, Request, status
from sqlalchemy.orm import Session
import bcrypt
import os
from pathlib import Path
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from .schemas import (
    UserRegistration, 
    UserLogin, 
    OTPVerification, 
    Token, 
    GoogleAuthRequest, 
    UserResponse,
    RefreshTokenRequest 
)
from .crud import create_user, get_user_by_email, generate_otp, create_oauth_user, get_user_by_oauth, save_otp
from .utils import send_otp_email 
from .auth import (
    create_access_token, 
    create_refresh_token, 
    verify_google_token, 
    get_current_user,
    verify_refresh_token, 
    revoke_refresh_token, 
    revoke_all_user_tokens,
    cleanup_expired_tokens 
)
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
    
    if get_user_by_email(db, email):
        raise HTTPException(status_code=409, detail="Email already registered")

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

    otp = generate_otp(db, email)

    save_otp(db, db_user, otp, settings.OTP_TTL_SECONDS)
    background_tasks.add_task(send_otp_email, db_user.email, otp)

    return {"message": f"OTP sent to email (expires in {settings.OTP_TTL_SECONDS} seconds)"}


@router.post("/verify_otp/", response_model=Token)
async def verify_otp(otp_data: OTPVerification, db: Session = Depends(get_db)):
    from datetime import datetime  
    email = otp_data.email.lower().strip()
    db_user = get_user_by_email(db, email)
    
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    now = datetime.utcnow()  
    if not db_user.otp_expires_at or db_user.otp_expires_at < now:
        db_user.otp = None
        db_user.otp_expires_at = None
        db.commit()
        raise HTTPException(status_code=400, detail="OTP expired! Login again.")
    
    if str(db_user.otp) != str(otp_data.otp):
        raise HTTPException(status_code=400, detail="Invalid OTP")
    
    # Clear OTP
    db_user.otp = None
    db_user.otp_expires_at = None
    db.commit()
    
    # Create tokens
    access_token = create_access_token(data={"sub": db_user.email, "user_id": db_user.id})
    refresh_token = create_refresh_token(db=db, user_id=db_user.id, email=db_user.email)
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": {
            "id": db_user.id,
            "username": db_user.username,
            "email": db_user.email,
            "profile_picture": db_user.profile_picture,
            "is_verified": db_user.is_verified
        }
    }

@router.post("/auth/refresh", response_model=Token)
async def refresh_access_token(refresh_data: RefreshTokenRequest, db: Session = Depends(get_db)):
    
    
    user = verify_refresh_token(db, refresh_data.refresh_token)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token"
        )
    
    # Revoke the old refresh token (one-time use)
    revoke_refresh_token(db, refresh_data.refresh_token)
    
    # Create new tokens
    access_token = create_access_token(data={"sub": user.email, "user_id": user.id})
    new_refresh_token = create_refresh_token(db=db, user_id=user.id, email=user.email)
    
    return {
        "access_token": access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "profile_picture": user.profile_picture,
            "is_verified": user.is_verified
        }
    }


@router.post("/auth/logout")
async def logout(refresh_data: RefreshTokenRequest, current_user = Depends(get_current_user), db: Session = Depends(get_db)):
    
    revoke_refresh_token(db, refresh_data.refresh_token)
    return {"message": "Logged out successfully"}


@router.post("/auth/logout-all")
async def logout_all_devices(current_user = Depends(get_current_user), db: Session = Depends(get_db)):
    revoke_all_user_tokens(db, current_user.id)
    return {"message": "Logged out from all devices"}


@router.get("/", response_class=HTMLResponse)
async def root(request: Request):

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
    
    # Create and store refresh token
    refresh_token = create_refresh_token(db=db, user_id=db_user.id, email=db_user.email)
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
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


@router.post("/admin/cleanup-tokens")
async def cleanup_tokens(current_user = Depends(get_current_user),db: Session = Depends(get_db)):
    deleted = cleanup_expired_tokens(db)
    return {"message": f"Cleaned up {deleted} tokens"}