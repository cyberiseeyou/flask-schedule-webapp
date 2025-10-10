"""
Authentication routes blueprint
Handles user login, logout, and session management
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app
from functools import wraps
from datetime import datetime, timedelta
import secrets

# Create blueprint
auth_bp = Blueprint('auth', __name__)

# Session store - will be shared with app
session_store = {}


def is_authenticated():
    """Check if user is authenticated"""
    session_id = request.cookies.get('session_id')
    if not session_id:
        return False

    session_data = session_store.get(session_id)
    if not session_data:
        return False

    # Check if session has expired (24 hours)
    if datetime.utcnow() - session_data['created_at'] > timedelta(hours=24):
        del session_store[session_id]
        return False

    return True


def get_current_user():
    """Get current authenticated user info"""
    session_id = request.cookies.get('session_id')
    if session_id and session_id in session_store:
        return session_store[session_id].get('user_info')
    return None


def require_authentication():
    """Decorator to require authentication for routes"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not is_authenticated():
                return redirect(url_for('auth.login_page'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator


@auth_bp.route('/login')
def login_page():
    """Display login page"""
    # Redirect to dashboard if already authenticated
    if is_authenticated():
        return redirect(url_for('main.dashboard'))

    return render_template('login.html')


@auth_bp.route('/login', methods=['POST'])
# Note: CSRF exemption applied in app.py - cannot have token before authentication session exists
def login():
    """Handle login form submission and authenticate with Crossmark API"""
    from session_api_service import session_api as external_api

    try:
        # Debug logging
        current_app.logger.info(f"Login attempt - Content-Type: {request.content_type}")
        current_app.logger.info(f"Login attempt - Form data: {request.form}")
        current_app.logger.info(f"Login attempt - Raw data: {request.get_data(as_text=True)[:200]}")

        # Get credentials from form
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        remember_me = request.form.get('remember') == 'on'

        # Validate input
        if not username or not password:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({
                    'success': False,
                    'error': 'Username and password are required'
                }), 400
            else:
                flash('Username and password are required', 'error')
                return redirect(url_for('auth.login_page'))

        # Temporarily configure external API with user credentials
        original_username = external_api.username
        original_password = external_api.password
        auth_success = False  # Initialize auth_success outside try block

        external_api.username = username
        external_api.password = password

        try:
            # Attempt authentication with Crossmark API
            current_app.logger.info(f"Attempting authentication for user: {username}")

            # Development mode bypass - allow login with any credentials
            is_dev_mode = (
                current_app.config.get('DEBUG', False) or
                current_app.config.get('ENV') == 'development' or
                current_app.config.get('FLASK_ENV') == 'development' or
                current_app.config.get('TESTING', False)
            )

            if is_dev_mode:
                current_app.logger.info("Development mode: bypassing external API authentication")
                auth_success = True
            else:
                auth_success = external_api.login()

            if auth_success:
                # Get user information
                user_info = external_api._get_user_info()
                if not user_info:
                    user_info = {
                        'username': username,
                        'userId': username,
                        'authenticated': True
                    }

                # Create session
                session_id = secrets.token_urlsafe(32)
                session_data = {
                    'user_id': username,
                    'user_info': user_info,
                    'created_at': datetime.utcnow(),
                    'crossmark_authenticated': True,
                    'phpsessid': external_api.phpsessid
                }
                session_store[session_id] = session_data

                current_app.logger.info(f"Successful authentication for user: {username}")

                # Create response
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    response = jsonify({
                        'success': True,
                        'redirect': url_for('main.dashboard'),
                        'user': user_info,
                        'refresh_database': True  # Trigger post-login database refresh
                    })
                else:
                    response = redirect(url_for('main.dashboard'))

                # Set session cookie
                response.set_cookie(
                    'session_id',
                    session_id,
                    max_age=86400 if remember_me else None,  # 24 hours if remember me
                    httponly=True,
                    secure=request.is_secure,
                    samesite='Lax'
                )

                return response

            else:
                current_app.logger.warning(f"Authentication failed for user: {username}")
                error_message = 'Invalid username or password. Please check your Crossmark credentials.'

                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return jsonify({
                        'success': False,
                        'error': error_message
                    }), 401
                else:
                    flash(error_message, 'error')
                    return redirect(url_for('auth.login_page'))

        finally:
            # Only restore original credentials if authentication failed
            # If auth was successful, keep the new credentials for API calls
            if not auth_success:
                external_api.username = original_username
                external_api.password = original_password

    except Exception as e:
        current_app.logger.error(f"Login error for user {username}: {str(e)}")
        error_message = 'An error occurred during login. Please try again.'

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({
                'success': False,
                'error': error_message
            }), 500
        else:
            flash(error_message, 'error')
            return redirect(url_for('auth.login_page'))


@auth_bp.route('/logout')
def logout():
    """Handle user logout"""
    from session_api_service import session_api as external_api

    session_id = request.cookies.get('session_id')

    if session_id and session_id in session_store:
        # Clear session
        del session_store[session_id]
        current_app.logger.info("User logged out successfully")

    # Clear external API session if authenticated
    if external_api.authenticated:
        external_api.logout()

    response = redirect(url_for('auth.login_page'))
    response.set_cookie('session_id', '', expires=0)
    flash('You have been logged out successfully', 'info')

    return response


@auth_bp.route('/api/auth/status')
def auth_status():
    """Check authentication status"""
    if is_authenticated():
        user_info = get_current_user()
        return jsonify({
            'authenticated': True,
            'user': user_info
        })
    else:
        return jsonify({
            'authenticated': False
        }), 401
