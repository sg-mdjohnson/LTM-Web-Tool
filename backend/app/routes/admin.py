from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from app import db
from app.models.user import User
from app.models.config import UserConfig
import logging
from datetime import datetime, timedelta

bp = Blueprint('admin', __name__, url_prefix='/api/admin')
logger = logging.getLogger('audit')

def admin_required(f):
    """Decorator to check if user is admin"""
    @login_required
    def decorated_function(*args, **kwargs):
        if not current_user.is_admin():
            logger.warning(f"Unauthorized admin access attempt by {current_user.username}")
            return jsonify({
                'status': 'error',
                'message': 'Admin privileges required'
            }), 403
        return f(*args, **kwargs)
    return decorated_function

@bp.route('/users', methods=['GET'])
@admin_required
def list_users():
    """Get list of all users"""
    try:
        users = User.query.all()
        return jsonify({
            'status': 'success',
            'users': [{
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'role': user.role,
                'is_active': user.is_active
            } for user in users]
        })
    except Exception as e:
        logger.error(f"Error listing users: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@bp.route('/users/<int:user_id>', methods=['PUT'])
@admin_required
def update_user(user_id):
    """Update user details (admin only)"""
    try:
        user = User.query.get(user_id)
        if not user:
            return jsonify({
                'status': 'error',
                'message': 'User not found'
            }), 404

        data = request.json
        
        # Update role if provided
        if 'role' in data:
            old_role = user.role
            user.role = data['role']
            logger.info(f"User {user.username} role changed from {old_role} to {data['role']}")

        # Update active status if provided
        if 'is_active' in data:
            user.is_active = data['is_active']
            status = 'activated' if user.is_active else 'deactivated'
            logger.info(f"User {user.username} {status}")

        # Update email if provided
        if 'email' in data:
            user.email = data['email']

        # Update password if provided
        if 'password' in data:
            user.set_password(data['password'])
            logger.info(f"Password updated for user {user.username}")

        db.session.commit()

        return jsonify({
            'status': 'success',
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'role': user.role,
                'is_active': user.is_active
            }
        })

    except Exception as e:
        logger.error(f"Error updating user {user_id}: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@bp.route('/users/<int:user_id>', methods=['DELETE'])
@admin_required
def delete_user(user_id):
    """Delete user (admin only)"""
    try:
        user = User.query.get(user_id)
        if not user:
            return jsonify({
                'status': 'error',
                'message': 'User not found'
            }), 404

        # Prevent deleting self
        if user.id == current_user.id:
            return jsonify({
                'status': 'error',
                'message': 'Cannot delete own account'
            }), 400

        username = user.username
        db.session.delete(user)
        db.session.commit()

        logger.info(f"User deleted: {username}")
        return jsonify({
            'status': 'success',
            'message': f'User {username} deleted successfully'
        })

    except Exception as e:
        logger.error(f"Error deleting user {user_id}: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@bp.route('/logs', methods=['GET'])
@admin_required
def get_logs():
    """Get application logs"""
    try:
        log_type = request.args.get('type', 'audit')  # audit, app, error, etc.
        days = int(request.args.get('days', 7))  # Default to 7 days
        
        # Read appropriate log file based on type
        log_file = f'logs/{log_type}.log'
        
        try:
            with open(log_file, 'r') as f:
                logs = f.readlines()
                
            # Filter logs by date if needed
            if days:
                cutoff = datetime.now() - timedelta(days=days)
                logs = [
                    log for log in logs 
                    if _parse_log_date(log) >= cutoff
                ]
            
            return jsonify({
                'status': 'success',
                'logs': logs
            })
            
        except FileNotFoundError:
            return jsonify({
                'status': 'error',
                'message': f'Log file {log_type}.log not found'
            }), 404

    except Exception as e:
        logger.error(f"Error fetching logs: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

def _parse_log_date(log_line):
    """Parse date from log line"""
    try:
        # Assuming log format: "2024-02-06 19:46:28,454 ..."
        date_str = log_line.split(',')[0]
        return datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')
    except:
        return datetime.min 