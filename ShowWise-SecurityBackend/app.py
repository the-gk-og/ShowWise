"""Security Backend Application"""
import os
from flask import Flask, jsonify, request
from flask_login import LoginManager
from werkzeug.security import generate_password_hash
from config import get_config
from extensions import db, login_manager
from models import SecurityDashboardUser


def create_app(config_name=None):
    """Application factory"""
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')
    
    app = Flask(__name__)
    app.config.from_object(get_config())
    
    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    
    @login_manager.user_loader
    def load_user(user_id):
        return SecurityDashboardUser.query.get(int(user_id))
    
    # Register error handlers
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({'error': 'Not found'}), 404
    
    @app.errorhandler(500)
    def server_error(error):
        return jsonify({'error': 'Internal server error'}), 500
    
    # Health check
    @app.route('/health', methods=['GET'])
    def health_check():
        return jsonify({'status': 'ok', 'service': 'security-backend'}), 200
    
    # Register blueprints
    from routes import register_blueprints
    register_blueprints(app)
    
    # Create database context
    with app.app_context():
        db.create_all()
    
    return app


if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, port=5001)
