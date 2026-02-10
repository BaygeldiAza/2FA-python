from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from typing import Optional


class UserRegistration(BaseModel):
    username: str = Field(..., min_length=3, max_length=25)
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)

    class Config:
        from_attributes=True

class UserLogin(BaseModel):
    email: EmailStr
    password: str 

    class Config:
        from_attributes=True

class OTPVerification(BaseModel):
    email: EmailStr
    otp: str = Field(...,min_length=6,max_length=6)

    class Config:
        from_attributes=True

class Token(BaseModel):
    access_token: str
    token_type: str
    user: dict

class GoogleAuthRequest(BaseModel):
    token: str

class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    oauth_provider: Optional[str] = None
    profile_picture: Optional[str] = None
    is_verified: bool = False
    
    class Config:
        from_attributes = True