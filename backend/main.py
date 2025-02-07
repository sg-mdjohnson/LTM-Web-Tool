from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import uvicorn

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Models
class Device(BaseModel):
    name: str
    host: str
    username: str
    password: str
    description: Optional[str] = None

class DeviceResponse(BaseModel):
    id: int
    name: str
    host: str
    username: str
    description: Optional[str] = None
    status: str = "inactive"
    last_used: Optional[str] = None

# Temporary storage (replace with database later)
devices = []
device_id_counter = 1

@app.get("/api/devices", response_model=List[DeviceResponse])
async def get_devices():
    return devices

@app.post("/api/devices")
async def add_device(device: Device):
    global device_id_counter
    new_device = DeviceResponse(
        id=device_id_counter,
        name=device.name,
        host=device.host,
        username=device.username,
        description=device.description,
    )
    devices.append(new_device)
    device_id_counter += 1
    return {"status": "success", "message": "Device added successfully"}

@app.delete("/api/devices/{device_id}")
async def delete_device(device_id: int):
    device = next((d for d in devices if d.id == device_id), None)
    if device is None:
        raise HTTPException(status_code=404, detail="Device not found")
    devices.remove(device)
    return {"status": "success", "message": "Device deleted successfully"}

@app.post("/api/devices/{device_id}/test")
async def test_device(device_id: int):
    device = next((d for d in devices if d.id == device_id), None)
    if device is None:
        raise HTTPException(status_code=404, detail="Device not found")
    # Simulate device testing
    return {"status": "success", "message": "Device test successful"}

@app.get("/api/admin/metrics")
async def get_metrics():
    return {
        "status": "success",
        "metrics": {
            "cpu_usage": 45,
            "memory_usage": 60,
            "disk_usage": 35,
            "uptime": "5d 12h 30m",
            "active_users": 3,
            "active_sessions": 5,
            "last_backup": "2024-03-10 15:30:00",
            "database_size": "256 MB"
        }
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000) 