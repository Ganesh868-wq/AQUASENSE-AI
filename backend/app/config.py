import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file from project root
BASE_DIR = Path(__file__).resolve().parent.parent.parent
load_dotenv(BASE_DIR / ".env")

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "aquasense_secure_default_key_2026_jwt")
    JWT_ALGORITHM = "HS256"
    JWT_EXPIRATION_HOURS = 72

    # Database: Supabase/PostgreSQL with automatic SQLite fallback
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///aquasense.db")
    # Handle postgres:// vs postgresql:// scheme if provided by Supabase or older platforms
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

    # Weather
    OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY", "")
    
    # Simulation & Demo
    ENABLE_IOT_SIMULATOR = os.getenv("ENABLE_IOT_SIMULATOR", "true").lower() in ("true", "1", "yes")
    DEMO_MODE = os.getenv("DEMO_MODE", "true").lower() in ("true", "1", "yes")

    # Static / Frontend path
    FRONTEND_DIR = BASE_DIR / "frontend"
