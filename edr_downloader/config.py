"""
Configuration Module for EDR Downloader Application.

This module contains all configuration settings for the EDR Downloader Flask application,
including Flask settings, database configuration, Walmart Retail Link credentials, and
file storage paths.

Configuration values are loaded from environment variables using python-decouple, with
sensible defaults provided for development environments.

Environment Variables:
    SECRET_KEY: Flask secret key for session management and CSRF protection
    WALMART_EDR_USERNAME: Walmart Retail Link account username/email
    WALMART_EDR_PASSWORD: Walmart Retail Link account password
    WALMART_EDR_MFA_CREDENTIAL_ID: MFA credential ID from Retail Link settings

Usage:
    from config import Config
    app.config.from_object(Config)

Author: Schedule Management System
Version: 1.0
"""
import os
from decouple import config


class Config:
    """
    Application configuration class for EDR Downloader.

    This class centralizes all configuration settings for the Flask application.
    Settings are loaded from environment variables with secure defaults.

    Attributes:
        SECRET_KEY (str): Secret key for Flask session encryption and CSRF tokens
        basedir (str): Absolute path to the application's base directory
        SQLALCHEMY_DATABASE_URI (str): Database connection string for SQLAlchemy
        SQLALCHEMY_TRACK_MODIFICATIONS (bool): Disable SQLAlchemy modification tracking
        WALMART_EDR_USERNAME (str): Walmart Retail Link authentication username
        WALMART_EDR_PASSWORD (str): Walmart Retail Link authentication password
        WALMART_EDR_MFA_CREDENTIAL_ID (str): MFA credential identifier for SMS OTP
        TEMP_EDR_FOLDER (str): Directory path for storing downloaded EDR PDF files

    Security Notes:
        - In production, all sensitive values should be set via environment variables
        - Never commit credentials to version control
        - Use a .env file for local development (excluded from git)
        - Rotate credentials regularly and use strong passwords

    Example:
        # In your .env file:
        SECRET_KEY=your-random-secret-key-here
        WALMART_EDR_USERNAME=your.email@company.com
        WALMART_EDR_PASSWORD=YourSecurePassword123!
        WALMART_EDR_MFA_CREDENTIAL_ID=your-mfa-credential-id
    """

    # Flask settings
    # SECRET_KEY is used for session encryption, CSRF protection, and other security features
    # In production, this MUST be set to a secure random value via environment variable
    SECRET_KEY = config('SECRET_KEY', default='edr-downloader-secret-key')

    # Database settings
    # Determine the base directory of the application
    basedir = os.path.abspath(os.path.dirname(__file__))

    # SQLite database URI - points to scheduler.db in the instance folder
    # The instance folder should be located one level up from edr_downloader directory
    SQLALCHEMY_DATABASE_URI = f'sqlite:///{os.path.join(basedir, "instance", "scheduler.db")}'

    # Disable modification tracking to save memory and improve performance
    # This feature is not needed for most applications
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Walmart Retail Link EDR settings
    # These credentials are required for authenticating with Walmart's Event Management System
    # NOTE: In production, these should ALWAYS come from environment variables, never defaults
    WALMART_EDR_USERNAME = config('WALMART_EDR_USERNAME', default='mat.conder@productconnections.com')
    WALMART_EDR_PASSWORD = config('WALMART_EDR_PASSWORD', default='Demos812Th$')
    WALMART_EDR_MFA_CREDENTIAL_ID = config('WALMART_EDR_MFA_CREDENTIAL_ID', default='18122365202')

    # EDR download settings
    # Temporary folder for storing downloaded EDR PDF files
    # Files are stored here before being sent to the user or processed
    TEMP_EDR_FOLDER = os.path.join(basedir, 'temp_edrs')

    # Ensure the temporary EDR folder exists at application startup
    # exist_ok=True prevents errors if the folder already exists
    os.makedirs(TEMP_EDR_FOLDER, exist_ok=True)
