from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from .config import settings

engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(255), index=True, nullable=False)  # Added length here
    email = Column(String(255), unique=True, index=True, nullable=False)  # Specify length here too
    hashed_password = Column(String(128))  # Specify length if needed
    otp = Column(String(6), nullable=True)  # Adjusted length of OTP if necessary
    otp_expires_at = Column(DateTime, nullable=True)

Base.metadata.create_all(bind=engine)
