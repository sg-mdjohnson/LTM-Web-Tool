from typing import Dict, Any, Optional, List
from pydantic import BaseSettings, validator, PostgresDsn, RedisDsn
from pathlib import Path
from functools import lru_cache
import os
import json

class Settings(BaseSettings):
    """Application settings with validation"""
    
    # Application
    APP_NAME: str = "LTM Web Tool"
    VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = False
    API_PREFIX: str = "/api"
    
    # Security
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    ALLOWED_HOSTS: List[str] = ["*"]
    CORS_ORIGINS: List[str] = ["*"]
    
    # Database
    POSTGRES_HOST: str
    POSTGRES_PORT: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    DB_POOL_SIZE: int = 5
    DB_MAX_OVERFLOW: int = 10
    DB_ECHO: bool = False

    # Redis
    REDIS_HOST: str
    REDIS_PORT: int
    REDIS_PASSWORD: Optional[str] = None
    REDIS_DB: int = 0
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FILE: Optional[str] = "logs/app.log"
    LOG_JSON_FORMAT: bool = True
    
    # Rate Limiting
    RATE_LIMIT_PER_SECOND: int = 10
    RATE_LIMIT_BURST: int = 20
    
    # Cache
    CACHE_TTL: int = 300  # 5 minutes
    
    # F5 LTM Settings
    F5_VERIFY_SSL: bool = True
    F5_TIMEOUT: int = 30

    @validator("SQLALCHEMY_DATABASE_URI", pre=True)
    def assemble_db_uri(cls, v: Optional[str], values: Dict[str, Any]) -> str:
        """Construct database URI from components"""
        if v:
            return v
            
        return PostgresDsn.build(
            scheme="postgresql+asyncpg",
            user=values["POSTGRES_USER"],
            password=values["POSTGRES_PASSWORD"],
            host=values["POSTGRES_HOST"],
            port=values["POSTGRES_PORT"],
            path=f"/{values['POSTGRES_DB']}"
        )

    @validator("REDIS_URI", pre=True)
    def assemble_redis_uri(cls, v: Optional[str], values: Dict[str, Any]) -> str:
        """Construct Redis URI from components"""
        if v:
            return v
            
        password_part = f":{values['REDIS_PASSWORD']}@" if values.get('REDIS_PASSWORD') else "@"
        return RedisDsn.build(
            scheme="redis",
            user=None,
            password=values.get("REDIS_PASSWORD"),
            host=values["REDIS_HOST"],
            port=str(values["REDIS_PORT"]),
            path=f"/{values['REDIS_DB']}"
        )

    def load_secrets_from_file(self, file_path: str) -> None:
        """Load sensitive settings from a JSON file"""
        try:
            with open(file_path) as f:
                secrets = json.load(f)
                for key, value in secrets.items():
                    if hasattr(self, key):
                        setattr(self, key, value)
        except Exception as e:
            raise ValueError(f"Error loading secrets file: {str(e)}")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True

@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance"""
    settings = Settings()
    
    # Load secrets if file exists
    secrets_file = os.getenv("SECRETS_FILE")
    if secrets_file and Path(secrets_file).exists():
        settings.load_secrets_from_file(secrets_file)
        
    return settings

# Global settings instance
settings = get_settings() 