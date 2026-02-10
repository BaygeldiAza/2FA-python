from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean
from sqlalchemy.sql import func
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(255), index=True, nullable=False)  
    email = Column(String(255), unique=True, index=True, nullable=False)  
    hashed_password = Column(String(255),nullable=False) 

    #OAuth fields
    oauth_provider = Column(String(50), nullable=True)
    oauth_id = Column(String(255), nullable=True)
    profile_picture = Column(String(500), nullable=True)
    is_verified = Column(Boolean, default=False)

    #OTP fields
    otp = Column(String(6), nullable=True)  
    otp_expires_at = Column(DateTime, nullable=True)
    otp_attempts = Column(Integer, default=0)
    user_created_time = Column(DateTime, default=datetime.utcnow, server_default=func.now(), nullable=False)

    def __repr__(self):
        return f"<User(id='{self.id}', username='{self.username}', email='{self.email}')>"

