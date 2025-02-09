from typing import Optional, Dict, Any
from datetime import datetime
from app.core.errors import AppError
from app.core.f5 import F5Client

class DeviceError(AppError):
    pass

class DeviceManager:
    def __init__(self):
        self.clients: Dict[str, F5Client] = {}
        self.status_cache: Dict[str, Dict[str, Any]] = {}
        self.last_check: Dict[str, datetime] = {}

    def get_client(self, device_id: str) -> F5Client:
        if device_id not in self.clients:
            raise DeviceError(f"Device {device_id} not found")
        return self.clients[device_id]

    def check_device_status(self, device_id: str) -> Dict[str, Any]:
        client = self.get_client(device_id)
        now = datetime.utcnow()
        
        # Cache status for 1 minute
        if (device_id in self.last_check and 
            (now - self.last_check[device_id]).total_seconds() < 60):
            return self.status_cache[device_id]

        try:
            status = client.execute_command("show sys status")
            self.status_cache[device_id] = status
            self.last_check[device_id] = now
            return status
        except Exception as e:
            raise DeviceError(f"Failed to check device status: {str(e)}") 