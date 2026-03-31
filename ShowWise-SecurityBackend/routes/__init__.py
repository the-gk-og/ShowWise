"""Route initialization"""


def register_blueprints(app):
    """Register all blueprints"""
    from routes.ip_management import ip_bp
    from routes.security_events import events_bp
    from routes.appeals import appeals_bp
    from routes.admin import admin_bp
    from routes.dashboard import dashboard_bp
    from routes.integration import integration_bp
    
    app.register_blueprint(ip_bp, url_prefix='/api/ip')
    app.register_blueprint(events_bp, url_prefix='/api/events')
    app.register_blueprint(appeals_bp, url_prefix='/api/appeals')
    app.register_blueprint(admin_bp, url_prefix='/api/admin')
    app.register_blueprint(dashboard_bp, url_prefix='/api/dashboard')
    app.register_blueprint(integration_bp, url_prefix='/api/integration')
