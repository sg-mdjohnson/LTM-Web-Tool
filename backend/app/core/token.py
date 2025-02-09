from datetime import datetime, timedelta
from typing import Dict, Optional
import time
from app.core.config import settings

class TokenManager:
    def __init__(self):
        self._blacklist: Dict[str, float] = {}
        self._cleanup_interval = 3600  # Clean up every hour
        self._last_cleanup = time.time()

    def add_to_blacklist(self, token: str, expires_at: float) -> None:
        self._cleanup_expired()
        self._blacklist[token] = expires_at

    def is_blacklisted(self, token: str) -> bool:
        self._cleanup_expired()
        return token in self._blacklist

    def _cleanup_expired(self) -> None:
        now = time.time()
        if now - self._last_cleanup < self._cleanup_interval:
            return

        self._blacklist = {
            token: expires_at 
            for token, expires_at in self._blacklist.items() 
            if expires_at > now
        }
        self._last_cleanup = now 