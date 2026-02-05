from pydantic import BaseModel, EmailStr, Field
from datetime import datetime

class UserRegistration(BaseModel):
    username: str = Field(..., min_length=3, max_length=25)
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)

    class Config:
        from_attributes=True

class UserLogin(BaseModel):
    email: EmailStr
    password: str
    user_created_time: datetime 

    class Config:
        from_attributes=True

class OTPVerification(BaseModel):
    email: EmailStr
    otp: str = Field(...,min_length=6,max_length=6)

    class Config:
        from_attributes=True

