"""
Configuration management for Flask Schedule Webapp
Handles environment-based settings and external API configuration
"""
import os
from decouple import config


class Config:
    """Base configuration class"""
    # Flask settings
    SECRET_KEY = config('SECRET_KEY', default='dev-secret-key-change-in-production')
    SQLALCHEMY_DATABASE_URI = config('DATABASE_URL', default='sqlite:///instance/scheduler.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # External API settings (Crossmark Session-based authentication)
    EXTERNAL_API_BASE_URL = config('EXTERNAL_API_BASE_URL', default='https://crossmark.mvretail.com')
    EXTERNAL_API_USERNAME = config('EXTERNAL_API_USERNAME', default='')
    EXTERNAL_API_PASSWORD = config('EXTERNAL_API_PASSWORD', default='')
    EXTERNAL_API_TIMEZONE = config('EXTERNAL_API_TIMEZONE', default='America/Indiana/Indianapolis')
    EXTERNAL_API_TIMEOUT = config('EXTERNAL_API_TIMEOUT', default=30, cast=int)
    EXTERNAL_API_MAX_RETRIES = config('EXTERNAL_API_MAX_RETRIES', default=3, cast=int)
    EXTERNAL_API_RETRY_DELAY = config('EXTERNAL_API_RETRY_DELAY', default=1, cast=int)
    SESSION_REFRESH_INTERVAL = config('SESSION_REFRESH_INTERVAL', default=3600, cast=int)  # 1 hour

    # Sync settings
    SYNC_ENABLED = config('SYNC_ENABLED', default=False, cast=bool)
    SYNC_INTERVAL_MINUTES = config('SYNC_INTERVAL_MINUTES', default=15, cast=int)
    SYNC_BATCH_SIZE = config('SYNC_BATCH_SIZE', default=50, cast=int)

    # Logging settings
    LOG_LEVEL = config('LOG_LEVEL', default='INFO')
    LOG_FILE = config('LOG_FILE', default='scheduler.log')

    # Walmart Retail Link EDR settings
    WALMART_EDR_USERNAME = config('WALMART_EDR_USERNAME', default='mat.conder@productconnections.com')
    WALMART_EDR_PASSWORD = config('WALMART_EDR_PASSWORD', default='Demos812Th$')
    WALMART_EDR_MFA_CREDENTIAL_ID = config('WALMART_EDR_MFA_CREDENTIAL_ID', default='18122365202')

    # Settings encryption key (should be set in environment for production)
    SETTINGS_ENCRYPTION_KEY = config('SETTINGS_ENCRYPTION_KEY', default=None)


class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    TESTING = False


class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    SYNC_ENABLED = False


class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    TESTING = False
    # Production should always use environment variables for sensitive data
    # Using default values to prevent import errors, will be validated at runtime
    SECRET_KEY = config('SECRET_KEY', default='prod-secret-key-must-be-set')
    EXTERNAL_API_USERNAME = config('EXTERNAL_API_USERNAME', default='')
    EXTERNAL_API_PASSWORD = config('EXTERNAL_API_PASSWORD', default='')


# Configuration mapping
config_mapping = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}


def get_config(config_name=None):
    """Get configuration class based on environment"""
    if config_name is None:
        config_name = config('FLASK_ENV', default='development')
    return config_mapping.get(config_name, DevelopmentConfig)