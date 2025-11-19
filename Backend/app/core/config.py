# config.py
from pydantic_settings import BaseSettings
import os
from dotenv import load_dotenv

load_dotenv()  # Carga variables del archivo .env


class Settings(BaseSettings):
    SECRET_KEY: str = os.getenv("SECRET_KEY")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    # Validar que exista la SECRET_KEY
    if not SECRET_KEY:
        raise ValueError("SECRET_KEY no configurada en variables de entorno")


settings = Settings()
