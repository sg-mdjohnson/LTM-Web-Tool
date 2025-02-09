from typing import Any, Dict, Optional
import os
import json
import yaml
from pathlib import Path
from pydantic import BaseSettings, validator
from app.core.logging import logger

class ConfigManager:
    def __init__(self, config_path: Optional[Path] = None):
        self._config_path = config_path or Path("config.yaml")
        self._config: Dict[str, Any] = {}
        self._load_config()

    def _load_config(self) -> None:
        try:
            if not self._config_path.exists():
                logger.warning(f"Config file not found: {self._config_path}")
                return

            with open(self._config_path) as f:
                if self._config_path.suffix == '.yaml':
                    self._config = yaml.safe_load(f)
                else:
                    self._config = json.load(f)

            # Override with environment variables
            self._override_from_env()
            
            logger.info("Configuration loaded successfully")
        except Exception as e:
            logger.error(f"Error loading config: {str(e)}")
            raise

    def _override_from_env(self) -> None:
        for key, value in os.environ.items():
            if key.startswith('APP_'):
                config_key = key[4:].lower()
                self._set_nested_value(self._config, config_key.split('_'), value)

    def _set_nested_value(
        self,
        config: Dict[str, Any],
        keys: list,
        value: Any
    ) -> None:
        for key in keys[:-1]:
            config = config.setdefault(key, {})
        config[keys[-1]] = value

    def get(self, key: str, default: Any = None) -> Any:
        try:
            value = self._config
            for k in key.split('.'):
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default

    def set(self, key: str, value: Any) -> None:
        try:
            keys = key.split('.')
            self._set_nested_value(self._config, keys, value)
            logger.info(f"Config value set: {key}={value}")
        except Exception as e:
            logger.error(f"Error setting config value: {str(e)}")
            raise

    def save(self) -> None:
        try:
            with open(self._config_path, 'w') as f:
                if self._config_path.suffix == '.yaml':
                    yaml.safe_dump(self._config, f)
                else:
                    json.dump(self._config, f, indent=2)
            logger.info("Configuration saved successfully")
        except Exception as e:
            logger.error(f"Error saving config: {str(e)}")
            raise 