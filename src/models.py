from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(255), index=True, nullable=False)  
    email = Column(String(255), unique=True, index=True, nullable=False)  
    hashed_password = Column(String(255)) 
    otp = Column(String(6), nullable=False)  
    otp_expires_at = Column(DateTime, nullable=False)

    def __repr__(self):
        return f"<User(id='{self.id}', username='{self.username}', email='{self.email}')>"

