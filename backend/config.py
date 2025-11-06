import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    APP_NAME: str = "Medical Kiosk API"
    APP_VERSION: str = "1.0.0"
    ALLOWED_ORIGINS = ["*"]
    
    # Database - Use postgresql:// not postgres://
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://postgres:root@localhost:5432/med_kiosk")
    
    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
    ALGORITHM: str = "HS256"
    
    # CORS
    ALLOWED_ORIGINS: list = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:8000").split(",")
    
    # Camera Settings
    CAMERA_RESOLUTION: tuple = (1280, 720)
    CAMERA_FPS: int = 30
    
    # rPPG Settings
    RPPG_WINDOW_SIZE: int = 150
    HEART_RATE_RANGE: tuple = (40, 180)  # BPM

settings = Settings()