import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

# Dynamically resolve the absolute path to backend/.env
BACKEND_DIR = Path(__file__).resolve().parent.parent
ENV_FILE_PATH = os.path.join(BACKEND_DIR, ".env")

class Settings(BaseSettings):
    # Database connection string (defaults to a mock local SQLite DB if Neon URL isn't set yet)
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/orca_marine"

    # Gemini API Credentials
    GEMINI_API_KEY: Optional[str] = None

    # Console-only grounded narrative provider.  It is intentionally separate
    # from shared planning and is read from backend/.env by Settings.
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_NARRATIVE_MODEL: str = "gpt-4o-mini"

    # OpenAlex Academic Research API (Optional)
    OPENALEX_API_KEY: Optional[str] = None

    # Bhashini Translation Credentials (if using custom endpoint keys)
    BHASHINI_API_KEY: Optional[str] = None
    BHASHINI_USER_ID: Optional[str] = None

    # Twilio SMS Config (for offline query gateway)
    TWILIO_ACCOUNT_SID: Optional[str] = None
    TWILIO_AUTH_TOKEN: Optional[str] = None
    TWILIO_PHONE_NUMBER: Optional[str] = None

    # Load configurations from a local .env file if it exists
    model_config = SettingsConfigDict(
        env_file=ENV_FILE_PATH, env_file_encoding="utf-8", extra="ignore"
    )


settings = Settings()
