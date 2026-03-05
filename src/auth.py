from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from datetime import datetime, timedelta
from jose import JWTError, jwt  
from google.oauth2 import id_token
from google.auth.transport import requests
import hashlib
import secrets 
import logging
from .config import settings
from .db import get_db
from .crud import (
    get_user_by_email,
    create_refresh_token_record,
    get_refresh_token_by_hash,
    revoke_refresh_token_by_hash,
    revoke_all_user_refresh_tokens,
    delete_expired_refresh_tokens,
)


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login/")
logger = logging.getLogger(__name__)


def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else: 
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def hash_token(token: str)->str:
    return hashlib.sha256(token.encode()).hexdigest()

def create_refresh_token(db: Session, user_id: int, email: str)->str:
    token = secrets.token_urlsafe(32)
    token_hash = hash_token(token)
    expires_at = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    create_refresh_token_record(db, user_id, token_hash, expires_at)
    logger.info(f"Created refresh token for user {user_id}")

    return  token

def verify_refresh_token(db: Session, token: str):
    try:
        token_hash = hash_token(token)
        db_token = get_refresh_token_by_hash
        
        if not db_token:
            logger.warning("Refresh token not found or revoked")
            return None
        
        if db_token.expires_at < datetime.utcnow():
            logger.warning(f"Refresh token expired for user {db_token.user_id}")
            revoke_refresh_token_by_hash(db, token_hash)
            return None
        
        user =  db_token.user

        if not user:
            logger.error(f"User not found for token user_id {db_token.user_id}")
            return None
        
        return user
    except Exception as e:
        logger.error(f"Error verifying refresh token: {str(e)}")

def revoke_refresh_token(db: Session, token: str)->bool:
    try:
        token_hash = hash_token(token)
        success = revoke_refresh_token_by_hash(db, token_hash)
        
        if success:
            logger.info(f"Revoked refresh token")
    
        return success
    except Exception as e:
        logger.error(f"Error revoking token: {str(e)}")
        return False

def revoke_all_user_tokens(db: Session, user_id: int)->int:
    try:
        count = revoke_all_user_refresh_tokens(db, user_id)
        logger.info(f"Revoked {count} tokens for user {user_id}")
        return count
    
    except Exception as e:
        logger.error(f"Error revoking all tokens for user {user_id}: {str(e)}")
        raise

def cleanup_expired_tokens(db: Session)->int:
    try:
        deleted = delete_expired_refresh_tokens(db)
        logger.info(f"Cleaned up {deleted} expired/revoked tokens")
        return deleted
    except Exception as e:
        logger.error(f"Error cleaning up tokens: {str(e)}")
        raise


def verify_google_token(token: str):
    try:
        idinfo = id_token.verify_oauth2_token(
            token,
            requests.Request(),
            settings.GOOGLE_CLIENT_ID
        )

        if idinfo['iss'] not in ['accounts.google.com', 'https://accounts.google.com']:
            raise ValueError('wrong issuer.')
        
        return {
            'email': idinfo['email'],
            'name': idinfo.get('name', idinfo['email'].split('@')[0]),
            'picture': idinfo.get('picture'),
            'google_id': idinfo['sub'],
            'email_verified': idinfo.get('email_verified', False)
        }
    
    except ValueError as e:
        logger.error(f"Token verification failed: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error verifying token: {str(e)}")
        return None

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            
            email: str = payload.get("sub")
            if email is None:
                raise credentials_exception
    
        except JWTError:
            raise credentials_exception
        
        user = get_user_by_email(db, email)
        if user is None:
            raise credentials_exception
        
        return user


