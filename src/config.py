import os
from dotenv import load_dotenv
from pathlib import Path

# Specify the path to your .env file explicitly if it's not in the same directory
env_path = Path('.') / '.env'  # or specify the full path like 'C:/path/to/.env'
load_dotenv(dotenv_path=env_path)

class Settings: 
    DATABASE_URL: str = os.getenv("DATABASE_URL", "mysql+mysqlconnector://USERNAME:PASSWORD@localhost/mydatabase")
    SENDER_EMAIL: str = os.getenv("SENDER_EMAIL")
    RESEND_API_KEY: str = os.getenv("RESEND_API_KEY")
    OTP_TTL_SECONDS: int = 120
    OTP_LEN: int = 6

settings = Settings()
