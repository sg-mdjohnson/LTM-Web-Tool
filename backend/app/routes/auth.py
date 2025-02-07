from flask import Blueprint, jsonify, request, session
from flask_login import login_user, logout_user, login_required, current_user
from app import db
from app.models.user import User
from app.models.config import UserConfig
import logging
from datetime import datetime

bp = Blueprint('auth', __name__, url_prefix='/api/auth')
logger = logging.getLogger('audit')

@bp.route('/login', methods=['POST'])
def login():
    """Handle user login"""
    try:
        data = request.json
        user = User.query.filter_by(username=data.get('username')).first()

        if user and user.check_password(data.get('password')):
            if not user.is_active:
                logger.warning(f"Login attempt for inactive user: {user.username}")
                return jsonify({
                    'status': 'error',
                    'message': 'Account is inactive'
                }), 401

            login_user(user)
            session.permanent = True  # Use permanent session with timeout
            
            # Log successful login
            logger.info(f"Successful login: {user.username}")
            
            return jsonify({
                'status': 'success',
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'role': user.role,
                    'config': user.config.get_theme_customization() if user.config else {}
                }
            })
        else:
            # Log failed attempt
            logger.warning(f"Failed login attempt for user: {data.get('username')}")
            return jsonify({
                'status': 'error',
                'message': 'Invalid credentials'
            }), 401

    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'Login failed'
        }), 500

@bp.route('/logout', methods=['POST'])
@login_required
def logout():
    """Handle user logout"""
    try:
        username = current_user.username
        logout_user()
        logger.info(f"User logged out: {username}")
        return jsonify({'status': 'success'})
    except Exception as e:
        logger.error(f"Logout error: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'Logout failed'
        }), 500

@bp.route('/register', methods=['POST'])
@login_required
def register():
    """Register new user (admin only)"""
    try:
        if not current_user.is_admin():
            return jsonify({
                'status': 'error',
                'message': 'Unauthorized'
            }), 403

        data = request.json
        required = ['username', 'email', 'password', 'role']
        if not all(k in data for k in required):
            return jsonify({
                'status': 'error',
                'message': 'Missing required fields'
            }), 400

        # Check if user exists
        if User.query.filter_by(username=data['username']).first():
            return jsonify({
                'status': 'error',
                'message': 'Username already exists'
            }), 400

        if User.query.filter_by(email=data['email']).first():
            return jsonify({
                'status': 'error',
                'message': 'Email already exists'
            }), 400

        # Create user
        user = User(
            username=data['username'],
            email=data['email'],
            role=data['role']
        )
        user.set_password(data['password'])

        # Create default user config
        config = UserConfig(user=user)
        
        db.session.add(user)
        db.session.add(config)
        db.session.commit()

        logger.info(f"New user registered: {user.username}")
        return jsonify({
            'status': 'success',
            'user': {
                'id': user.id,
                'username': user.username,
                'role': user.role
            }
        })

    except Exception as e:
        logger.error(f"Registration error: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@bp.route('/profile', methods=['GET'])
@login_required
def get_profile():
    """Get current user profile"""
    try:
        return jsonify({
            'status': 'success',
            'user': {
                'id': current_user.id,
                'username': current_user.username,
                'email': current_user.email,
                'role': current_user.role,
                'config': current_user.config.get_theme_customization() if current_user.config else {}
            }
        })
    except Exception as e:
        logger.error(f"Error fetching profile: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@bp.route('/profile', methods=['PUT'])
@login_required
def update_profile():
    """Update user profile"""
    try:
        data = request.json
        user = current_user

        # Update basic info
        if 'email' in data:
            user.email = data['email']

        # Update password if provided
        if 'password' in data:
            user.set_password(data['password'])

        # Update theme preferences
        if 'theme' in data and user.config:
            user.config.theme = data['theme']
            if 'theme_customization' in data:
                user.config.theme_customization = data['theme_customization']

        db.session.commit()
        logger.info(f"Profile updated: {user.username}")

        return jsonify({
            'status': 'success',
            'message': 'Profile updated successfully'
        })

    except Exception as e:
        logger.error(f"Profile update error: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500 