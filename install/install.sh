#!/bin/bash

# Exit on error
set -e

# Configuration
APP_NAME="f5-ltm-app"
APP_USER="f5app"
APP_GROUP="f5app"
INSTALL_DIR="/opt/${APP_NAME}"
VENV_DIR="${INSTALL_DIR}/venv"
CONFIG_DIR="${INSTALL_DIR}/config"
LOGS_DIR="${INSTALL_DIR}/logs"
SERVICE_NAME="f5app"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Logging function
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}" >&2
}

warn() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING: $1${NC}"
}

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    error "Please run as root"
    exit 1
fi

# Check Python version
check_python() {
    log "Checking Python version..."
    if ! command -v python3 >/dev/null 2>&1; then
        error "Python 3 is not installed"
        exit 1
    fi
    
    PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
    if (( $(echo "$PYTHON_VERSION < 3.8" | bc -l) )); then
        error "Python 3.8 or higher is required"
        exit 1
    fi
}

# Create user and group
create_user() {
    log "Creating service user and group..."
    if ! getent group "$APP_GROUP" >/dev/null; then
        groupadd "$APP_GROUP"
    fi
    if ! getent passwd "$APP_USER" >/dev/null; then
        useradd -r -g "$APP_GROUP" -d "$INSTALL_DIR" -s /bin/false "$APP_USER"
    fi
}

# Install system dependencies
install_dependencies() {
    log "Installing system dependencies..."
    if command -v apt-get >/dev/null 2>&1; then
        apt-get update
        apt-get install -y python3-venv python3-pip nginx
    elif command -v zypper >/dev/null 2>&1; then
        zypper refresh
        zypper install -y python3-venv python3-pip nginx
    else
        error "Unsupported package manager"
        exit 1
    fi
}

# Create directory structure
create_directories() {
    log "Creating directory structure..."
    mkdir -p "$INSTALL_DIR"
    mkdir -p "$CONFIG_DIR"
    mkdir -p "$LOGS_DIR"
    
    # Copy application files
    cp -r ../backend/* "$INSTALL_DIR/"
    cp -r ../config/* "$CONFIG_DIR/"
    
    # Create virtual environment
    python3 -m venv "$VENV_DIR"
    
    # Set permissions
    chown -R "$APP_USER:$APP_GROUP" "$INSTALL_DIR"
    chmod -R 750 "$INSTALL_DIR"
}

# Install Python dependencies
install_python_deps() {
    log "Installing Python dependencies..."
    "$VENV_DIR/bin/pip" install -r "$INSTALL_DIR/requirements.txt"
    "$VENV_DIR/bin/pip" install gunicorn
}

# Initialize database
init_database() {
    log "Initializing database..."
    cd "$INSTALL_DIR"
    export FLASK_APP=app
    "$VENV_DIR/bin/flask" db upgrade
    
    # Create initial admin user if doesn't exist
    "$VENV_DIR/bin/python" -c "
from app import create_app, db
from app.models.user import User
from app.models.config import UserConfig

app = create_app()
with app.app_context():
    if not User.query.filter_by(username='admin').first():
        admin = User(username='admin', email='admin@local', role='admin')
        admin.set_password('admin')  # Change this in production!
        config = UserConfig(user=admin)
        db.session.add(admin)
        db.session.add(config)
        db.session.commit()
        print('Created initial admin user')
    "
}

# Install systemd service
install_service() {
    log "Installing systemd service..."
    cp f5app.service /etc/systemd/system/
    systemctl daemon-reload
    systemctl enable "$SERVICE_NAME"
    systemctl start "$SERVICE_NAME"
}

# Main installation process
main() {
    log "Starting installation of $APP_NAME..."
    
    check_python
    create_user
    install_dependencies
    create_directories
    install_python_deps
    init_database
    install_service
    
    log "Installation completed successfully!"
    log "Default admin credentials: admin/admin"
    warn "Please change the admin password immediately!"
    log "Service status: $(systemctl is-active $SERVICE_NAME)"
}

# Run installation
main 