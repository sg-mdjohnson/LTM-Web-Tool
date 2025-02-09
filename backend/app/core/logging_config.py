import logging
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict
from app.core.config import settings

class JSONFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        log_data: Dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        if hasattr(record, "request_id"):
            log_data["request_id"] = record.request_id
            
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
            
        return json.dumps(log_data)

def setup_logging() -> None:
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    handlers = {
        "app": logging.FileHandler("logs/app.log"),
        "error": logging.FileHandler("logs/error.log"),
        "access": logging.FileHandler("logs/access.log"),
        "audit": logging.FileHandler("logs/audit.log"),
    }
    
    for name, handler in handlers.items():
        handler.setFormatter(JSONFormatter())
        logger = logging.getLogger(name)
        logger.addHandler(handler)
        logger.setLevel(settings.LOG_LEVEL) 