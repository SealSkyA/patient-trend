import os
from pydantic_settings import BaseSettings
from typing import Optional

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class Settings(BaseSettings):
    APP_NAME: str = "患者检查报告趋势分析系统"
    DEBUG: bool = True

    DATABASE_URL: str = "mysql+aiomysql://root:100Trust%21%40@127.0.0.1:3306/patient_trend?charset=utf8mb4"
    DATABASE_ECHO: bool = False

    SECRET_KEY: str = "patient-trend-secret-key-2026-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7

    UPLOAD_DIR: str = os.path.join(PROJECT_ROOT, "backend", "uploads")

    class Config:
        env_file = os.path.join(PROJECT_ROOT, ".env")


settings = Settings()

os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
