import os
from datetime import timedelta

class Config:
    # Basic Flask configuration
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key-here'
    
    # Database
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///app.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Session configuration
    PERMANENT_SESSION_LIFETIME = timedelta(minutes=30)  # Configurable up to 60
    
    # F5 Device defaults
    F5_TIMEOUT_API = int(os.environ.get('TIMEOUT_API', 30))
    F5_TIMEOUT_SSH = int(os.environ.get('TIMEOUT_SSH', 60))
    
    # Logging configuration
    LOG_ROTATION_SIZE = 10240000  # 10MB
    LOG_BACKUP_COUNT = 10

    # Theme configuration
    DEFAULT_THEME = 'dark'
    
    # Monitoring
    ENABLE_PROMETHEUS = os.environ.get('ENABLE_PROMETHEUS', 'false').lower() == 'true' 