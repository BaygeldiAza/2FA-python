from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends
from sqlalchemy.orm import Session
import bcrypt
from contextlib import asynccontextmanager

from .schemas import UserRegistration, UserLogin, OTPVerification
from .crud import create_user, get_user_by_email, generate_otp
from .utils import send_otp_email, send_login_notification_email 
from .config import settings
from .db import SessionLocal, engine
from .models import Base

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("Database initialized")

    yield
    print("Closing database connections... ")
    engine.dispose()
    print("Shutdown complete")

app = FastAPI(
    title="User Authentication API",
    version="1.0.0",
    lifespan=lifespan
)

# Dependency to get the database session
def get_db():
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

@app.post("/register/")
async def register(user: UserRegistration, db: Session = Depends(get_db)):
    email = user.email.lower().strip()
    
    # Check if user already exists
    if get_user_by_email(db, email):
        raise HTTPException(status_code=409, detail="Email already registered")

    # Hash password and create user
    hashed_password = bcrypt.hashpw(user.password.encode("utf-8"), bcrypt.gensalt())
    create_user(db, user.username, email, hashed_password)

    return {"message": "User registered successfully"}

@app.post("/login/")
async def login(user: UserLogin, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    email = user.email.lower().strip()
    db_user = get_user_by_email(db, email)

    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    if not bcrypt.checkpw(user.password.encode("utf-8"), db_user.hashed_password.encode("utf-8")):
        raise HTTPException(status_code=400, detail="Invalid credentials")

    # Generate OTP and send it
    otp = generate_otp(db, email)
    background_tasks.add_task(send_otp_email, db_user.email, otp)

    return {"message": f"OTP sent to email (expires in {settings.OTP_TTL_SECONDS} seconds)"}


@app.post("/verify_otp/")
async def verify_otp(otp_data: OTPVerification, db: Session = Depends(get_db)):
    from datetime import datetime
    email = otp_data.email.lower().strip()
    db_user = get_user_by_email(db, email)
    
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if db_user.otp_expires_at < datetime.utcnow():
        db_user.otp = None
        db_user.otp_expires_at = None
        db.commit()
        raise HTTPException(status_code=400, detail="OTP expired! Login again.")
    
    if db_user.otp != otp_data.otp:
        raise HTTPException(status_code=400, detail="Invalid OTP")
    
    db_user.otp = None
    db_user.otp_expires_at = None
    db.commit()
    
    return {"message": "OTP verified successfully"}