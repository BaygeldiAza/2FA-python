import os
from dotenv import load_dotenv
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
# Specify the path to your .env file explicitly if it's not in the same directory
env_path = Path('.') / '.env'  # or specify the full path like 'C:/path/to/.env'
load_dotenv(dotenv_path=env_path)

class Settings: 
    DATABASE_URL: str = os.getenv("DATABASE_URL", "mysql+mysqlconnector://USERNAME:PASSWORD@localhost/mydatabase")
    SENDER_EMAIL: str = os.getenv("SENDER_EMAIL")
    SENDER_PASSWORD: str = os.getenv("SENDER_PASSWORD")
    SMTP_HOST: str = os.getenv("SMTP_HOST")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT",587))
    OTP_TTL_SECONDS: int = 120
    OTP_LEN: int = 6
    # google OAuth 2.0 Settings
    GOOGLE_CLIENT_ID: str = os.getenv("GOOGLE_CLIENT_ID")
    GOOGLE_CLIENT_SECRET: str = os.getenv("GOOGLE_CLIENT_SECRET")
    GOOGLE_REDIRECT_URI: str = os.getenv("GOOGLE_REDIRECT_URI")

    SECRET_KEY: str = os.getenv("SECRET_KEY")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES:int = 30

settings = Settings()
