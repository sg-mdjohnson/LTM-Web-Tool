from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
import logging
from logging.handlers import RotatingFileHandler
import os
from config import Config

# Initialize extensions
db = SQLAlchemy()
login_manager = LoginManager()
migrate = Migrate()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize Flask extensions
    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)

    # Ensure log directory exists
    if not os.path.exists('logs'):
        os.mkdir('logs')

    # Setup logging
    log_files = {
        'app': 'app.log',
        'audit': 'audit.log',
        'cli': 'cli.log',
        'api': 'api.log',
        'ssh': 'ssh.log',
        'performance': 'performance.log',
        'error': 'error.log'
    }

    for log_name, log_file in log_files.items():
        handler = RotatingFileHandler(
            f'logs/{log_file}', 
            maxBytes=10240000, 
            backupCount=10
        )
        handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s '
            '[in %(pathname)s:%(lineno)d]'
        ))
        handler.setLevel(logging.INFO)
        
        logger = logging.getLogger(log_name)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)

    # Register blueprints
    from app.routes import auth, device, cli, admin
    app.register_blueprint(auth.bp)
    app.register_blueprint(device.bp)
    app.register_blueprint(cli.bp)
    app.register_blueprint(admin.bp)

    return app 