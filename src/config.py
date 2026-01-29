import os
from dotenv import load_dotenv

load_dotenv()

class Settings: 
    DATABASE_URL: str = os.getenv("DATABASE_URL", "mysql+mysqlconnector://USERNAME:PASSWORD@localhost/mydatabase")
    SENDER_EMAIL: str = os.getenv("SENDER_EMAIL")
    SENDER_PASSWORD: str = os.getenv("SENDER_PASSWORD")
    OTP_TTL_SECONDS: int = 120
    OTP_LEN: int = 6

settings = Settings()
