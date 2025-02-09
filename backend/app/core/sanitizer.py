from typing import Any, Dict, List, Optional, Union
import re
import html
from fastapi import Request
from app.core.logging import logger

class RequestSanitizer:
    # Common XSS patterns to sanitize
    XSS_PATTERNS = [
        r'<script[^>]*?>.*?</script>',
        r'javascript:',
        r'onerror=',
        r'onload=',
        r'onclick=',
        r'onmouseover=',
        r'eval\(',
        r'document\.',
        r'window\.'
    ]

    # SQL injection patterns
    SQL_PATTERNS = [
        r'(\s*([\0\b\'\"\n\r\t\%\_\\]*\s*(((select\s*.+\s*from\s*.+)|(insert\s*.+\s*into\s*.+)|(update\s*.+\s*set\s*.+)|(delete\s*.+\s*from\s*.+)|(drop\s*.+)|(truncate\s*.+)|(alter\s*.+)|(exec\s*.+)|(\s*(all|any|not|and|between|in|like|or|some|contains|containsall|containskey)\s*.+[\=\>\<=\!\~]+.+)|(let\s+.+[\=]\s*.+)|(begin\s*.*\s*end)|(\s*[\/\*]+\s*.*\s*[\*\/]+)|(\s*(\-\-)\s*.*\s+)|(\s*(contains|containsall|containskey)\s+.*))))',
        r'(\%27)|(\')|(\-\-)|(\%23)|(#)',
        r'((\%3D)|(=))[^\n]*((\%27)|(\')|(\-\-)|(\%3B)|(;))',
        r'\w*((\%27)|(\'))((\%6F)|o|(\%4F))((\%72)|r|(\%52))',
        r'((\%27)|(\'))union'
    ]

    @staticmethod
    def sanitize_string(value: str) -> str:
        # HTML escape
        value = html.escape(value)
        
        # Remove XSS patterns
        for pattern in RequestSanitizer.XSS_PATTERNS:
            value = re.sub(pattern, '', value, flags=re.IGNORECASE)
            
        # Remove SQL injection patterns
        for pattern in RequestSanitizer.SQL_PATTERNS:
            value = re.sub(pattern, '', value, flags=re.IGNORECASE)
            
        return value.strip()

    @staticmethod
    def sanitize_dict(data: Dict[str, Any]) -> Dict[str, Any]:
        sanitized = {}
        for key, value in data.items():
            if isinstance(value, str):
                sanitized[key] = RequestSanitizer.sanitize_string(value)
            elif isinstance(value, dict):
                sanitized[key] = RequestSanitizer.sanitize_dict(value)
            elif isinstance(value, list):
                sanitized[key] = RequestSanitizer.sanitize_list(value)
            else:
                sanitized[key] = value
        return sanitized

    @staticmethod
    def sanitize_list(data: List[Any]) -> List[Any]:
        sanitized = []
        for item in data:
            if isinstance(item, str):
                sanitized.append(RequestSanitizer.sanitize_string(item))
            elif isinstance(item, dict):
                sanitized.append(RequestSanitizer.sanitize_dict(item))
            elif isinstance(item, list):
                sanitized.append(RequestSanitizer.sanitize_list(item))
            else:
                sanitized.append(item)
        return sanitized

class RequestSanitizerMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)

        async def wrapped_receive():
            message = await receive()
            
            if message["type"] == "http.request":
                try:
                    # Sanitize query parameters
                    if scope.get("query_string"):
                        from urllib.parse import parse_qs, urlencode
                        query_params = parse_qs(scope["query_string"].decode())
                        sanitized_params = RequestSanitizer.sanitize_dict(query_params)
                        scope["query_string"] = urlencode(sanitized_params, doseq=True).encode()

                    # Sanitize request body
                    body = message.get("body", b"")
                    if body:
                        import json
                        try:
                            data = json.loads(body)
                            sanitized_data = RequestSanitizer.sanitize_dict(data)
                            message["body"] = json.dumps(sanitized_data).encode()
                        except json.JSONDecodeError:
                            # If not JSON, sanitize as string
                            message["body"] = RequestSanitizer.sanitize_string(
                                body.decode()
                            ).encode()

                except Exception as e:
                    logger.error(f"Error sanitizing request: {str(e)}")
                    # Continue with original data if sanitization fails
                    pass

            return message

        await self.app(scope, wrapped_receive, send) 