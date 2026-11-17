from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    MONGODB_URI: str
    MONGODB_DB_NAME: str = "creatorpilot_db"
    GEMINI_API_KEY: str
    GEMINI_MODEL: str
    JWT_SECRET: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    FRONTEND_ORIGIN: str = "http://localhost:5173"

    class Config:
        env_file = ".env"

settings = Settings()
from dotenv import load_dotenv
load_dotenv()  # Loads variables from .env

import os
from google import genai

# Example client initialization:
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))