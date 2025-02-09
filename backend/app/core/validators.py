from typing import Tuple, Optional
import re
from ipaddress import ip_address, IPv4Address, IPv6Address
from datetime import datetime
from pydantic import BaseModel, validator
from app.core.errors import ValidationError

class RequestValidator:
    @staticmethod
    def validate_ip(ip: str) -> Tuple[bool, Optional[str]]:
        try:
            ip_obj = ip_address(ip)
            return True, 'ipv4' if isinstance(ip_obj, IPv4Address) else 'ipv6'
        except ValueError:
            return False, None

    @staticmethod
    def validate_domain(domain: str) -> bool:
        pattern = r'^(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}$'
        return bool(re.match(pattern, domain))

    @staticmethod
    def validate_port(port: int) -> bool:
        return 1 <= port <= 65535

    @staticmethod
    def validate_timestamp(timestamp: str) -> bool:
        try:
            datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            return True
        except ValueError:
            return False

    @staticmethod
    def sanitize_input(value: str, max_length: int = 255) -> str:
        # Remove any control characters
        value = ''.join(char for char in value if ord(char) >= 32)
        # Truncate to max length
        return value[:max_length]

def validate_password(password: str) -> tuple[bool, str]:
    if len(password) < 8:
        return False, "Password must be at least 8 characters"
    if not any(c.isupper() for c in password):
        return False, "Password must contain uppercase letter"
    if not any(c.islower() for c in password):
        return False, "Password must contain lowercase letter"
    if not any(c.isdigit() for c in password):
        return False, "Password must contain number"
    if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
        return False, "Password must contain special character"
    return True, "Password is valid" 