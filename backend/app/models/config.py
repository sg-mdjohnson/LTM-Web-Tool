from app import db
import json

class UserConfig(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), unique=True)
    
    # Theme preferences
    theme = db.Column(db.String(50), default='dark')
    theme_customization = db.Column(db.Text)  # JSON string of custom theme
    
    # CLI preferences
    cli_preferences = db.Column(db.Text)  # JSON string
    
    # Timeout settings
    timeout_settings = db.Column(db.Text)  # JSON string
    
    def get_theme_customization(self):
        if self.theme_customization:
            return json.loads(self.theme_customization)
        return {}
    
    def get_cli_preferences(self):
        if self.cli_preferences:
            return json.loads(self.cli_preferences)
        return {}
    
    def get_timeout_settings(self):
        if self.timeout_settings:
            return json.loads(self.timeout_settings)
        return {
            'api': 30,
            'ssh': 60
        } 