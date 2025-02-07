from flask import Blueprint, jsonify, request, current_app
from flask_login import login_required, current_user
from app import db
from app.models.device import Device
from app.utils.f5_utils import F5Client, F5Error
from app.utils.encryption import CredentialEncryption
import logging

bp = Blueprint('device', __name__, url_prefix='/api/device')
logger = logging.getLogger('app')
encryption = CredentialEncryption()

@bp.route('/add', methods=['POST'])
@login_required
def add_device():
    """Add a new F5 device"""
    try:
        data = request.json
        required = ['name', 'host', 'username', 'password']
        if not all(k in data for k in required):
            return jsonify({
                'status': 'error',
                'message': 'Missing required fields'
            }), 400

        # Check if device already exists
        existing = Device.query.filter_by(host=data['host']).first()
        if existing:
            return jsonify({
                'status': 'error',
                'message': 'Device already exists'
            }), 400

        # Encrypt sensitive data
        encrypted_password = encryption.encrypt(data['password'])

        # Create device
        device = Device(
            name=data['name'],
            host=data['host'],
            username=data['username'],
            password=encrypted_password,
            description=data.get('description', '')
        )

        # Test connection
        client = F5Client(
            host=device.host,
            username=device.username,
            password=data['password']  # Use original password for test
        )

        if not client.check_connection():
            return jsonify({
                'status': 'error',
                'message': 'Failed to connect to device'
            }), 400

        # Save device
        db.session.add(device)
        db.session.commit()

        logger.info(f"Added new device: {device.name} ({device.host})")
        return jsonify({
            'status': 'success',
            'device': device.to_dict()
        })

    except Exception as e:
        logger.error(f"Error adding device: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@bp.route('/list', methods=['GET'])
@login_required
def list_devices():
    """Get list of all devices"""
    try:
        devices = Device.query.all()
        return jsonify({
            'status': 'success',
            'devices': [d.to_dict() for d in devices]
        })
    except Exception as e:
        logger.error(f"Error listing devices: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@bp.route('/<int:device_id>', methods=['GET'])
@login_required
def get_device(device_id):
    """Get device details"""
    try:
        device = Device.query.get(device_id)
        if not device:
            return jsonify({
                'status': 'error',
                'message': 'Device not found'
            }), 404

        return jsonify({
            'status': 'success',
            'device': device.to_dict()
        })
    except Exception as e:
        logger.error(f"Error getting device {device_id}: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@bp.route('/<int:device_id>/test', methods=['POST'])
@login_required
def test_connection(device_id):
    """Test connection to device"""
    try:
        device = Device.query.get(device_id)
        if not device:
            return jsonify({
                'status': 'error',
                'message': 'Device not found'
            }), 404

        client = F5Client(
            host=device.host,
            username=device.username,
            password=device.password
        )

        if client.check_connection():
            return jsonify({
                'status': 'success',
                'message': 'Connection successful'
            })
        else:
            return jsonify({
                'status': 'error',
                'message': 'Connection failed'
            }), 400

    except Exception as e:
        logger.error(f"Error testing device {device_id}: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500 