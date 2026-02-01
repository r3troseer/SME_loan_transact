from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    # App settings
    APP_NAME: str = "GFA Loan Sandbox API"
    DEBUG: bool = True

    # Database
    DATABASE_URL: str = "sqlite:///./data/gfa.db"

    # CORS
    CORS_ORIGINS: list[str] = ["http://localhost:3000", "http://localhost:5173"]

    # AI
    GEMINI_API_KEY: Optional[str] = None

    # Credits
    INITIAL_CREDITS: int = 100

    # Anonymization
    ANONYMIZE: bool = True

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
