import os
from dotenv import load_dotenv
from pathlib import Path

# Get the directory where this file is located
BASE_DIR = Path(__file__).resolve().parent.parent

# Try multiple locations for .env file
env_locations = [
    Path('.') / '.env',  # Current working directory
    BASE_DIR / '.env',   # Project root
    Path(__file__).parent / '.env',  # Same directory as config.py
]

env_loaded = False
for env_path in env_locations:
    if env_path.exists():
        print(f"Loading .env from: {env_path.resolve()}")
        load_dotenv(dotenv_path=env_path)
        env_loaded = True
        break

if not env_loaded:
    print("WARNING: .env file not found in any of the expected locations!")
    print("Searched locations:")
    for loc in env_locations:
        print(f"  - {loc.resolve()}")

class Settings: 
    DATABASE_URL: str = os.getenv("DATABASE_URL", "mysql+mysqlconnector://USERNAME:PASSWORD@localhost/mydatabase")
    SENDER_EMAIL: str = os.getenv("SENDER_EMAIL")
    SENDER_PASSWORD: str = os.getenv("SENDER_PASSWORD")
    SMTP_HOST: str = os.getenv("SMTP_HOST")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", 587))
    OTP_TTL_SECONDS: int = 120
    OTP_LEN: int = 6
    
    # Google OAuth 2.0 Settings
    GOOGLE_CLIENT_ID: str = os.getenv("GOOGLE_CLIENT_ID")
    GOOGLE_CLIENT_SECRET: str = os.getenv("GOOGLE_CLIENT_SECRET")
    GOOGLE_REDIRECT_URI: str = os.getenv("GOOGLE_REDIRECT_URI")

    SECRET_KEY: str = os.getenv("SECRET_KEY")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

settings = Settings()