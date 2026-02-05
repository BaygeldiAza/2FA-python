from sqlalchemy.orm import Session
from .models import User
from datetime import datetime, timedelta
import secrets

def create_user(db: Session, username: str, email: str, hashed_password: str):
    db_user = User(
                    username=username,
                    email=email.strip(),
                    hashed_password=hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def get_user_by_email(db: Session, email: str):
    return db.query(User).filter(User.email == email).first()


def generate_otp(db: Session, email: str):
    otp = ''.join([str(secrets.randbelow(10)) for _ in range(6)])
    
    db_user = get_user_by_email(db, email)

    if db_user:
        db_user.otp = otp
        db_user.otp_expires_at = datetime.utcnow() + timedelta(seconds=120)
        db_user.otp_attempts = 0
        db.commit()
    return otp


