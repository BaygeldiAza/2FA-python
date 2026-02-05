from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(255), index=True, nullable=False)  
    email = Column(String(255), unique=True, index=True, nullable=False)  
    hashed_password = Column(String(255),nullable=False) 
    otp = Column(String(6), nullable=True)  
    otp_expires_at = Column(DateTime, nullable=True)
    otp_attempts = Column(Integer, default=0)

    def __repr__(self):
        return f"<User(id='{self.id}', username='{self.username}', email='{self.email}')>"

