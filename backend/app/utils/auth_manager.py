from flask_login import LoginManager
from app.models.user import User
import logging

logger = logging.getLogger('app')

def init_login_manager(app):
    """Initialize and configure the login manager"""
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    
    @login_manager.user_loader
    def load_user(user_id):
        try:
            return User.query.get(int(user_id))
        except Exception as e:
            logger.error(f"Error loading user {user_id}: {str(e)}")
            return None

    @login_manager.unauthorized_handler
    def unauthorized():
        return {
            'status': 'error',
            'message': 'Authentication required'
        }, 401

    return login_manager 