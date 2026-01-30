from pydantic import BaseModel, EmailStr, Field

class UserRegistration(BaseModel):
    username: str = Field(..., min_length=3, max_length=25)
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)

    class Config:
        orm_mode = True

class UserLogin(BaseModel):
    email: EmailStr
    password: str

    class Config:
        orm_code = True

class OTPVerification(BaseModel):
    email: EmailStr
    otp: str = Field(...,min_length=6,max_length=6)

    class Config:
        orm_mode=True

        