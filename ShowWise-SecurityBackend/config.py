"""Security Backend Configuration"""
import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()


class BaseConfig:
    """Base configuration"""
    SECRET_KEY = os.environ.get('SECRET_KEY', os.urandom(32).hex())
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'SECURITY_DATABASE_URL',
        'sqlite:///security.db'
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # API Integration
    API_INTEGRATION_SECRET = os.environ.get('API_INTEGRATION_SECRET', '')
    API_INTEGRATION_KEY = os.environ.get('API_INTEGRATION_KEY', '')
    
    # Security Settings
    IP_BLOCK_THRESHOLD = int(os.environ.get('IP_BLOCK_THRESHOLD', 100))  # Failed attempts
    RATE_LIMIT_WINDOW = int(os.environ.get('RATE_LIMIT_WINDOW', 3600))  # seconds
    RATE_LIMIT_MAX_REQUESTS = int(os.environ.get('RATE_LIMIT_MAX_REQUESTS', 1000))
    
    # Appeal Settings
    APPEAL_EXPIRY_DAYS = int(os.environ.get('APPEAL_EXPIRY_DAYS', 30))
    APPEAL_AUTO_REVIEW_DAYS = int(os.environ.get('APPEAL_AUTO_REVIEW_DAYS', 7))
    
    # Quarantine Settings
    QUARANTINE_AUTO_RELEASE_DAYS = int(os.environ.get('QUARANTINE_AUTO_RELEASE_DAYS', 90))
    
    # Admin Settings
    ADMIN_API_KEY = os.environ.get('ADMIN_API_KEY', '')
    
    # Cloudflare
    CLOUDFLARE_API_TOKEN = os.environ.get('CLOUDFLARE_API_TOKEN', '')
    CLOUDFLARE_ZONE_ID = os.environ.get('CLOUDFLARE_ZONE_ID', '')


class DevelopmentConfig(BaseConfig):
    """Development configuration"""
    DEBUG = True
    TESTING = False


class ProductionConfig(BaseConfig):
    """Production configuration"""
    DEBUG = False
    TESTING = False
    PREFERRED_URL_SCHEME = 'https'


class TestingConfig(BaseConfig):
    """Testing configuration"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False


def get_config():
    """Get appropriate config based on environment"""
    env = os.environ.get('FLASK_ENV', 'development')
    if env == 'production':
        return ProductionConfig
    elif env == 'testing':
        return TestingConfig
    return DevelopmentConfig
