from sqlalchemy.orm import Session
from .models import User, RefreshToken
from datetime import datetime, timedelta, timezone
import secrets
from .config import settings

def create_user(db: Session, username: str, email: str, hashed_password: str):
    db_user = User(
        username=username,
        email=email.strip(),
        hashed_password=hashed_password
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def create_oauth_user(db: Session, email: str, username: str, oauth_provider: str, oauth_id: str, profile_picture: str = None):
    db_user = User(
        username = username,
        email=email.strip(),
        oauth_provider=oauth_provider,
        oauth_id=oauth_id,
        profile_picture=profile_picture,
        is_verified=True
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def get_user_by_email(db: Session, email: str):
    return db.query(User).filter(User.email == email).first()

def get_user_by_oauth(db: Session, oauth_provider: str, oauth_id: str):
    return db.query(User).filter(User.oauth_provider==oauth_provider, User.oauth_id==oauth_id).first()

def generate_otp(db: Session, email: str):
    return ''.join([str(secrets.randbelow(10)) for _ in range(6)])

def save_otp(db: Session, user: User, otp: str, ttl_seconds: int = 300):
    user.otp = otp
    user.otp_expires_at = datetime.now(timezone.utc) + timedelta(seconds=ttl_seconds)  # ✅ Timezone-aware
    user.otp_attempts = 0
    db.commit()
    db.refresh(user)
    return user

def verify_otp(db: Session, user: User, provided_otp: int) -> bool:
    if not user or not user.otp:
        return False
    
    now = datetime.now(timezone.utc)
    
    if not user.otp_expires_at or user.otp_expires_at < now:
        user.otp = None
        user.otp_expires_at = None 
        db.commit()
        return False
    
    if user.otp_attempts >= settings.OTP_ATTEMPTS:
        user.otp = None
        user.otp_expires_at = None
        db.commit()
        return False

    if str(user.otp)!=str(provided_otp):
        user.otp_attempts += 1
        db.commit()
        return False
    
    user.otp = None
    user.otp_expires_at = None
    user.otp_attempts = 0
    db.commit()
    return True
    
'''Refresh Token crud functions'''

def create_refresh_token_record(db:Session, user_id: int, token_hash: str, expires_at: datetime)->RefreshToken:
    db_token = RefreshToken(
        user_id = user_id,
        token_hash = token_hash,
        expires_at = expires_at
    )
    db.add(db_token)
    db.commit()
    db.refresh(db_token)
    return db_token

def get_refresh_token_by_hash(db: Session, token_hash: str)->RefreshToken:
    return db.query(RefreshToken).filter(
        RefreshToken.token_hash==token_hash,
        RefreshToken.revoked==False
        ).first()

def revoke_refresh_token_by_hash(db: Session, token_hash: str)->bool:
    db_token = db.query(RefreshToken).filter(RefreshToken.token_hash == token_hash).first()

    if db_token:
        db.token.revoked = True
        db.commit()
        return True
    return False

def revoke_all_user_refresh_tokens(db: Session, user_id: int)->int:
    count=db.query(RefreshToken).filter(
        RefreshToken.user_id == user_id,
        RefreshToken.revoked == False
    ).update({"revoked": True})
    db.commit()
    return count

def delete_expired_refresh_tokens(db: Session)->int:
    count = db.query(RefreshToken).filter(
        (RefreshToken.expires_at < datetime.utcnow()),
        (RefreshToken.revoked==True)
    ).delete()
    db.commit()
    return count

def get_user_active_sessions(db: Session, user_id: int)->list:
    return db.query(
        RefreshToken.user_id == user_id,
        RefreshToken.revoked == False,
        RefreshToken.expires_at > datetime.utcnow()
        ).all()

def get_refresh_token_count_by_user(db: Session, user_id: int)->int:
    return db.query(
        RefreshToken.user_id == user_id,
        RefreshToken.revoked == False,
        RefreshToken.expires_at > datetime.utcnow()
        ).count()

