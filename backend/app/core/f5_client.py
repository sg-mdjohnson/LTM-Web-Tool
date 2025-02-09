from typing import Dict, Any, Optional
import requests
from requests.adapters import HTTPAdapter, Retry
from urllib3.util.retry import Retry
from app.core.errors import F5Error
from app.core.logging import logger

class F5Client:
    def __init__(
        self, 
        host: str, 
        username: str, 
        password: str,
        verify_ssl: bool = True,
        timeout: int = 30
    ):
        self.host = host
        self.username = username
        self.password = password
        self.verify_ssl = verify_ssl
        self.timeout = timeout
        self.session = self._create_session()
        self.token: Optional[str] = None

    def _create_session(self) -> requests.Session:
        session = requests.Session()
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[500, 502, 503, 504]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("https://", adapter)
        session.mount("http://", adapter)
        return session

    def authenticate(self) -> None:
        try:
            response = self.session.post(
                f"https://{self.host}/mgmt/shared/authn/login",
                json={
                    "username": self.username,
                    "password": self.password,
                    "loginProviderName": "tmos"
                },
                verify=self.verify_ssl,
                timeout=self.timeout
            )
            response.raise_for_status()
            self.token = response.json()["token"]["token"]
            self.session.headers.update({
                "X-F5-Auth-Token": self.token
            })
        except Exception as e:
            logger.error(f"F5 authentication failed: {str(e)}")
            raise F5Error(f"Authentication failed: {str(e)}")

    def _ensure_authenticated(self) -> None:
        if not self.token:
            self.authenticate() 