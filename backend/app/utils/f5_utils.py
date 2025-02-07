import paramiko
import requests
import logging
from typing import Optional, Dict, Any, Union, List
import json
from requests.exceptions import RequestException
from paramiko.ssh_exception import SSHException
import time
from app.utils.encryption import CredentialEncryption  # Add encryption support

logger = logging.getLogger('api')
ssh_logger = logging.getLogger('ssh')

class F5Error(Exception):
    """Base exception for F5 related errors"""
    pass

class F5ConnectionError(F5Error):
    """Raised when connection to F5 device fails"""
    pass

class F5CommandError(F5Error):
    """Raised when command execution fails"""
    pass

class F5TimeoutError(F5Error):
    """Raised when operation times out"""
    pass

class F5Client:
    def __init__(
        self,
        host: str,
        username: str,
        password: str,
        verify_ssl: bool = False,
        api_timeout: int = 30,
        ssh_timeout: int = 60,
        max_retries: int = 3
    ):
        self.host = host
        self.username = username
        self.password = self._decrypt_password(password)
        self.verify_ssl = verify_ssl
        self.api_timeout = api_timeout
        self.ssh_timeout = ssh_timeout
        self.max_retries = max_retries
        
        # Initialize connections as None
        self.ssh_client = None
        self.api_session = None
        
        # Setup logging and encryption
        self.logger = logging.getLogger('f5')
        self.encryption = CredentialEncryption()

    def _decrypt_password(self, password: str) -> str:
        """Decrypt password if encrypted"""
        try:
            return self.encryption.decrypt(password)
        except:
            return password  # Return as-is if not encrypted

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def close(self):
        """Close all connections"""
        if self.ssh_client:
            try:
                self.ssh_client.close()
            except Exception as e:
                self.logger.warning(f"Error closing SSH connection: {str(e)}")
        
        if self.api_session:
            try:
                self.api_session.close()
            except Exception as e:
                self.logger.warning(f"Error closing API session: {str(e)}")

    def _init_ssh(self) -> None:
        """Initialize SSH connection"""
        try:
            if not self.ssh_client:
                self.ssh_client = paramiko.SSHClient()
                self.ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                self.ssh_client.connect(
                    self.host,
                    username=self.username,
                    password=self.password,
                    timeout=self.ssh_timeout
                )
                ssh_logger.info(f"SSH connection established to {self.host}")
        except Exception as e:
            ssh_logger.error(f"SSH connection failed: {str(e)}")
            raise F5ConnectionError(f"Failed to establish SSH connection: {str(e)}")

    def _init_api(self) -> None:
        """Initialize API session"""
        try:
            if not self.api_session:
                self.api_session = requests.Session()
                self.api_session.verify = self.verify_ssl
                self.api_session.auth = (self.username, self.password)
                # Test connection
                response = self.api_session.get(
                    f"https://{self.host}/mgmt/tm/sys",
                    timeout=self.api_timeout
                )
                response.raise_for_status()
                logger.info(f"API connection established to {self.host}")
        except Exception as e:
            logger.error(f"API connection failed: {str(e)}")
            raise F5ConnectionError(f"Failed to establish API connection: {str(e)}")

    def execute_command(self, command: str, timeout: Optional[int] = None) -> str:
        """Execute command via SSH"""
        if not timeout:
            timeout = self.ssh_timeout
            
        try:
            self._init_ssh()
            start_time = time.time()
            
            # Execute command
            stdin, stdout, stderr = self.ssh_client.exec_command(
                f"tmsh -c '{command}'",
                timeout=timeout
            )
            
            # Get output
            output = stdout.read().decode('utf-8')
            error = stderr.read().decode('utf-8')
            
            execution_time = time.time() - start_time
            ssh_logger.info(
                f"Command executed successfully in {execution_time:.2f}s: {command}"
            )
            
            if error:
                ssh_logger.warning(f"Command produced errors: {error}")
                raise F5CommandError(f"Command error: {error}")
                
            return output.strip()
            
        except SSHException as e:
            ssh_logger.error(f"SSH command failed: {str(e)}")
            raise F5CommandError(f"SSH command failed: {str(e)}")
        except Exception as e:
            ssh_logger.error(f"Unexpected error during command execution: {str(e)}")
            raise F5Error(f"Command execution failed: {str(e)}")

    def api_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        timeout: Optional[int] = None
    ) -> Dict[str, Any]:
        """Make API request to F5 device"""
        if not timeout:
            timeout = self.api_timeout
            
        try:
            self._init_api()
            start_time = time.time()
            
            url = f"https://{self.host}/mgmt/tm/{endpoint}"
            response = self.api_session.request(
                method=method,
                url=url,
                json=data if data else None,
                timeout=timeout
            )
            
            execution_time = time.time() - start_time
            logger.info(
                f"API request completed in {execution_time:.2f}s: {method} {endpoint}"
            )
            
            response.raise_for_status()
            return response.json()
            
        except RequestException as e:
            logger.error(f"API request failed: {str(e)}")
            raise F5ConnectionError(f"API request failed: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error during API request: {str(e)}")
            raise F5Error(f"API request failed: {str(e)}")

    def get_virtual_servers(self) -> Dict[str, Any]:
        """Get list of virtual servers via API"""
        return self.api_request('GET', 'ltm/virtual')

    def get_pools(self) -> Dict[str, Any]:
        """Get list of pools via API"""
        return self.api_request('GET', 'ltm/pool')

    def get_nodes(self) -> Dict[str, Any]:
        """Get list of nodes via API"""
        return self.api_request('GET', 'ltm/node')

    def get_device_info(self) -> Dict[str, Any]:
        """Get device information"""
        return self.api_request('GET', 'sys/hardware')

    def check_connection(self) -> bool:
        """Test both SSH and API connectivity"""
        try:
            # Test SSH
            self.execute_command('show sys version')
            # Test API
            self.get_device_info()
            return True
        except Exception as e:
            logger.error(f"Connection check failed: {str(e)}")
            return False 

    def execute_command_with_retry(self, command: str, max_retries: Optional[int] = None) -> str:
        """Execute command with retry logic"""
        retries = max_retries or self.max_retries
        last_error = None
        
        for attempt in range(retries):
            try:
                return self.execute_command(command)
            except (F5ConnectionError, F5TimeoutError) as e:
                last_error = e
                self.logger.warning(f"Attempt {attempt + 1}/{retries} failed: {str(e)}")
                if attempt < retries - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
                continue
            except F5CommandError:
                raise  # Don't retry if command itself is invalid
        
        raise last_error or F5Error("All retry attempts failed")

    # Additional F5 LTM specific methods
    def get_irules(self) -> Dict[str, Any]:
        """Get list of iRules"""
        return self.api_request('GET', 'ltm/rule')

    def get_profiles(self, profile_type: str = 'all') -> Dict[str, Any]:
        """Get list of profiles"""
        if profile_type == 'all':
            return self.api_request('GET', 'ltm/profile')
        return self.api_request('GET', f'ltm/profile/{profile_type}')

    def get_monitors(self, monitor_type: Optional[str] = None) -> Dict[str, Any]:
        """Get list of monitors"""
        if monitor_type:
            return self.api_request('GET', f'ltm/monitor/{monitor_type}')
        return self.api_request('GET', 'ltm/monitor')

    def get_persistence(self, persistence_type: Optional[str] = None) -> Dict[str, Any]:
        """Get persistence profiles"""
        if persistence_type:
            return self.api_request('GET', f'ltm/persistence/{persistence_type}')
        return self.api_request('GET', 'ltm/persistence')

    def get_pool_members(self, pool_name: str) -> List[Dict[str, Any]]:
        """Get members of a specific pool"""
        try:
            response = self.api_request('GET', f'ltm/pool/{pool_name}/members')
            return response.get('items', [])
        except F5Error:
            return []

    def get_virtual_server_details(self, vs_name: str) -> Dict[str, Any]:
        """Get detailed information about a virtual server"""
        return self.api_request('GET', f'ltm/virtual/{vs_name}')

    def backup_config(self, filename: Optional[str] = None) -> str:
        """Create a backup of the device configuration"""
        if not filename:
            timestamp = time.strftime('%Y%m%d-%H%M%S')
            filename = f'backup_{timestamp}.ucs'
        
        try:
            # Create backup via TMSH
            cmd = f'save sys ucs {filename}'
            self.execute_command(cmd)
            return f"Backup created successfully: {filename}"
        except Exception as e:
            raise F5Error(f"Backup failed: {str(e)}")

    def verify_config(self) -> bool:
        """Verify the current configuration"""
        try:
            result = self.execute_command('load sys config verify')
            return 'Error' not in result
        except Exception:
            return False 