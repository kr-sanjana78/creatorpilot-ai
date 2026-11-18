from pydantic_settings import BaseSettings
from pathlib import Path
from pydantic_settings import SettingsConfigDict

class Settings(BaseSettings):
    MONGODB_URI: str
    MONGODB_DB_NAME: str = "creatorpilot_db"
    GEMINI_API_KEY: str
    GEMINI_MODEL: str
    JWT_SECRET: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    FRONTEND_ORIGIN: str = "http://localhost:5173"

    model_config = SettingsConfigDict(env_file=Path(__file__).resolve().parent / ".env")

settings = Settings()