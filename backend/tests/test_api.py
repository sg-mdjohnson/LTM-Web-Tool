import requests
import json

BASE_URL = "http://localhost:8000"

def test_auth_flow():
    # 1. Try accessing protected route without token
    resp = requests.get(f"{BASE_URL}/api/devices")
    assert resp.status_code == 401, "Should be unauthorized"

    # 2. Login with admin credentials
    login_data = {
        "username": "admin",
        "password": "admin"
    }
    resp = requests.post(f"{BASE_URL}/api/auth/login", data=login_data)
    assert resp.status_code == 200, "Login failed"
    token = resp.json()["access_token"]
    
    # 3. Use token to access protected route
    headers = {"Authorization": f"Bearer {token}"}
    resp = requests.get(f"{BASE_URL}/api/devices", headers=headers)
    assert resp.status_code == 200, "Protected route access failed"

    # 4. Test device operations
    device_data = {
        "name": "Test F5",
        "host": "192.168.1.10",
        "username": "admin",
        "password": "password123",
        "description": "Test device"
    }
    
    # Add device
    resp = requests.post(
        f"{BASE_URL}/api/devices", 
        headers=headers,
        json=device_data
    )
    assert resp.status_code == 200, "Device creation failed"

    # Get devices
    resp = requests.get(f"{BASE_URL}/api/devices", headers=headers)
    assert resp.status_code == 200, "Get devices failed"
    devices = resp.json()
    assert len(devices) > 0, "No devices found"

    # Test connection
    device_id = devices[0]["id"]
    resp = requests.post(
        f"{BASE_URL}/api/devices/{device_id}/test", 
        headers=headers
    )
    assert resp.status_code == 200, "Device test failed"

    # Delete device
    resp = requests.delete(
        f"{BASE_URL}/api/devices/{device_id}", 
        headers=headers
    )
    assert resp.status_code == 200, "Device deletion failed"

    print("All tests passed!")

if __name__ == "__main__":
    test_auth_flow() 