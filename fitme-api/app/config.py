from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    app_name: str = "FITME API"
    app_version: str = "1.0.0"
    app_env: str = "development"
    app_debug: bool = True

    # OpenAI
    openai_api_key: str = ""

    # AWS S3
    aws_access_key_id: str = ""
    aws_secret_access_key: str = ""
    aws_region: str = "us-east-1"
    s3_bucket_name: str = "fitme-photos"

    # CORS
    cors_origins: List[str] = ["http://localhost:3000", "http://localhost:8501"]

    # Database
    database_url: str = "postgresql+asyncpg://fitme:fitme_secret@localhost:5432/fitme"

    # Replicate (IDM-VTON)
    replicate_api_token: str = ""

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
