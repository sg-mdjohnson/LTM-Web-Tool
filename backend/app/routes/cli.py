from flask import Blueprint, jsonify, request, current_app
from flask_login import login_required, current_user
from app import db
from app.models.cli import CommandTemplate, CommandHistory
from app.utils.f5_utils import F5Client
import time
import logging

bp = Blueprint('cli', __name__, url_prefix='/api/cli')
logger = logging.getLogger('cli')

# Pre-defined TMSH commands
SYSTEM_COMMANDS = [
    {
        'name': 'List Virtual Servers',
        'command': 'list ltm virtual',
        'category': 'virtual',
        'description': 'List all virtual servers'
    },
    {
        'name': 'List Rules',
        'command': 'list ltm rule',
        'category': 'rule',
        'description': 'List all iRules'
    },
    {
        'name': 'List Pools',
        'command': 'list ltm pool',
        'category': 'pool',
        'description': 'List all pools'
    },
    {
        'name': 'List TCP Monitors',
        'command': 'list ltm monitor tcp',
        'category': 'monitor',
        'description': 'List all TCP monitors'
    },
    {
        'name': 'List Cookie Persistence',
        'command': 'list ltm persistence cookie',
        'category': 'persistence',
        'description': 'List all cookie persistence profiles'
    },
    {
        'name': 'List SSL Profiles',
        'command': 'list ltm profile client-ssl',
        'category': 'ssl',
        'description': 'List all client SSL profiles'
    },
    {
        'name': 'List Nodes',
        'command': 'list ltm node',
        'category': 'node',
        'description': 'List all nodes'
    }
]

@bp.route('/commands', methods=['GET'])
@login_required
def get_commands():
    """Get all available commands (system + user templates)"""
    try:
        # Get user's command templates
        templates = CommandTemplate.query.filter(
            (CommandTemplate.created_by == current_user.id) |
            (CommandTemplate.is_system == True)
        ).all()
        
        return jsonify({
            'status': 'success',
            'commands': [
                {
                    'id': t.id,
                    'name': t.name,
                    'description': t.description,
                    'command': t.command,
                    'category': t.category,
                    'is_favorite': t.is_favorite,
                    'variables': t.get_variables()
                } for t in templates
            ]
        })
    except Exception as e:
        logger.error(f"Error fetching commands: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@bp.route('/execute', methods=['POST'])
@login_required
def execute_command():
    """Execute a command on F5 device"""
    data = request.json
    command = data.get('command')
    device_id = data.get('device_id')
    
    if not command or not device_id:
        return jsonify({
            'status': 'error',
            'message': 'Command and device_id are required'
        }), 400

    try:
        # Get device details and create F5 client
        device = Device.query.get(device_id)
        if not device:
            return jsonify({
                'status': 'error',
                'message': 'Device not found'
            }), 404

        # Create command history entry
        history = CommandHistory(
            user_id=current_user.id,
            device_id=device_id,
            command=command
        )
        db.session.add(history)
        
        # Execute command
        start_time = time.time()
        client = F5Client(
            host=device.host,
            username=device.username,
            password=device.password,
            timeout=current_user.config.get_timeout_settings().get('ssh', 60)
        )
        
        output = client.execute_command(command)
        execution_time = time.time() - start_time
        
        # Update history
        history.output = output
        history.status = 'success'
        history.execution_time = execution_time
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'output': output,
            'execution_time': execution_time
        })
        
    except Exception as e:
        logger.error(f"Command execution error: {str(e)}")
        if history:
            history.status = 'error'
            history.error_message = str(e)
            db.session.commit()
            
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@bp.route('/history', methods=['GET'])
@login_required
def get_history():
    """Get command execution history"""
    try:
        history = CommandHistory.query.filter_by(
            user_id=current_user.id
        ).order_by(
            CommandHistory.executed_at.desc()
        ).limit(100).all()
        
        return jsonify({
            'status': 'success',
            'history': [h.to_dict() for h in history]
        })
    except Exception as e:
        logger.error(f"Error fetching history: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500 