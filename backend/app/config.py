from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Database connection string (defaults to a mock local SQLite DB if Neon URL isn't set yet)
    DATABASE_URL: str = "postgresql://neondb_owner:npg_joGJhxuU0O7c@ep-rough-union-az8ee9rv-pooler.c-3.ap-southeast-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require"

    # Gemini API Credentials
    GEMINI_API_KEY: str | None = None

    # Bhashini Translation Credentials (if using custom endpoint keys)
    BHASHINI_API_KEY: str | None = None
    BHASHINI_USER_ID: str | None = None

    # Twilio SMS Config (for offline query gateway)
    TWILIO_ACCOUNT_SID: str | None = None
    TWILIO_AUTH_TOKEN: str | None = None
    TWILIO_PHONE_NUMBER: str | None = None

    # Load configurations from a local .env file if it exists
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )


settings = Settings()
