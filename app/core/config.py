from pydantic_settings import BaseSettings
from typing import Optional
from functools import lru_cache
import os


class Settings(BaseSettings):
    PROJECT_NAME: str = "NeoFi Event Management System"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api"
    
    # Security
    SECRET_KEY: str = os.environ["SECRET_KEY"]
    ALGORITHM: str = os.environ["ALGORITHM"]
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.environ["ACCESS_TOKEN_EXPIRE_MINUTES"])
    
    # Database
    DATABASE_URL: str = os.environ["DATABASE_URL"]
    
    # Redis
    REDIS_URL: Optional[str] = None
    
    # CORS
    BACKEND_CORS_ORIGINS: list[str] = ["*"]
    
    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings() 