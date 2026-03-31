"""ShowWise-home app.py with security integration"""
import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from services.security import init_security
from config import get_config

db = SQLAlchemy()

def create_app(config_name=None):
    """Create and configure Flask app"""
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')
    
    app = Flask(__name__)
    app.config.from_object(get_config())
    
    # Initialize database
    db.init_app(app)
    
    # Initialize security features
    init_security(app)
    
    # Register blueprints
    with app.app_context():
        db.create_all()
        
        # Import and register routes
        from routes.contact_secure import register_contact_routes
        register_contact_routes(app)
    
    return app


if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, port=5002)
