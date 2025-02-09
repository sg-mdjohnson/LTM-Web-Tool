from typing import Dict, List, Any, Optional
from pydantic import BaseModel, validator, Field
import yaml
import json
from pathlib import Path
from app.core.logging import logger

class DatabaseConfig(BaseModel):
    url: str
    pool_size: int = Field(ge=1, le=20)
    max_overflow: int = Field(ge=0, le=10)
    pool_timeout: int = Field(ge=1, le=60)
    pool_recycle: int = Field(ge=1, le=3600)

class SecurityConfig(BaseModel):
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = Field(ge=1, le=1440)
    verify_ssl: bool = True
    allowed_hosts: List[str]

class LoggingConfig(BaseModel):
    level: str = Field(regex="^(DEBUG|INFO|WARNING|ERROR|CRITICAL)$")
    format: str
    file_path: Path
    max_size_mb: int = Field(ge=1, le=1000)
    backup_count: int = Field(ge=0, le=100)

class AppConfig(BaseModel):
    database: DatabaseConfig
    security: SecurityConfig
    logging: LoggingConfig

    @validator('database')
    def validate_database_url(cls, v):
        if not v.url.startswith(('sqlite:///', 'postgresql://', 'mysql://')):
            raise ValueError("Invalid database URL")
        return v

class ConfigValidator:
    def __init__(self, config_path: Path):
        self.config_path = config_path
        self.config: Optional[AppConfig] = None

    def load_and_validate(self) -> AppConfig:
        try:
            if self.config_path.suffix == '.yaml':
                with open(self.config_path) as f:
                    config_data = yaml.safe_load(f)
            else:
                with open(self.config_path) as f:
                    config_data = json.load(f)

            self.config = AppConfig(**config_data)
            return self.config
        except Exception as e:
            logger.error(f"Configuration validation failed: {str(e)}")
            raise 