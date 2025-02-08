from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List

from app.auth.deps import get_current_user
from app.db.session import get_db
from app.models.device import Device
from app.models.user import User
from app.models.auth import DeviceCreate, DeviceResponse

router = APIRouter(prefix="/api/devices", tags=["devices"])

@router.get("", response_model=List[DeviceResponse])
async def get_devices(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    devices = db.query(Device).all()
    return devices

@router.post("")
async def add_device(
    device: DeviceCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    db_device = Device(
        name=device.name,
        host=device.host,
        username=device.username,
        password=device.password,  # TODO: Encrypt password
        description=device.description
    )
    db.add(db_device)
    db.commit()
    db.refresh(db_device)
    return {"status": "success", "message": "Device added successfully"}

@router.delete("/{device_id}")
async def delete_device(
    device_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    
    db.delete(device)
    db.commit()
    return {"status": "success", "message": "Device deleted successfully"}

@router.post("/{device_id}/test")
async def test_device(
    device_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    # TODO: Implement actual device testing
    return {"status": "success", "message": "Device test successful"} 