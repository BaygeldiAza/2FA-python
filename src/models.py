from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

BaseModel = declarative_base()

class User(BaseModel):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(255), index=True, nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=True)

    refresh_tokens = relationship(
        "RefreshToken",
        back_populates="user",
        cascade="all, delete-orphan"
    )

    oauth_provider = Column(String(255), nullable=True)
    oauth_id = Column(String(255), nullable=True)
    profile_picture = Column(String(500), nullable=True)
    is_verified = Column(Boolean, default=False)

    otp = Column(String(6), nullable=True)
    otp_expires_at = Column(DateTime, nullable=False)
    otp_attempts = Column(Integer, default=0)
    user_created_time = Column(DateTime, default=datetime.utcnow, server_default=func.now(), nullable=False)

    def __repr__(self):
        return f"<User(id='{self.id}', username='{self.username}', email='{self.email}')>"

class RefreshToken(BaseModel):
    __tablename__ = "refresh_tokens"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    token_hash = Column(String(255), nullable=False, unique=True, index=True)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, server_default=func.now(), nullable=False)
    revoked = Column(Boolean, default=False)

    user = relationship(
        "User",
        back_populates="refresh_tokens"
    )

    def __repr__(self):
        return f"<RefreshToken(id='{self.id}', user_id='{self.user_id}', revoked='{self.revoked}')>"