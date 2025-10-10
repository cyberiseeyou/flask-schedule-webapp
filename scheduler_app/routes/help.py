"""
Help and documentation routes
Provides comprehensive guides for using the Product Connections Scheduler
"""
from flask import Blueprint, render_template
from routes.auth import require_authentication

# Create blueprint
help_bp = Blueprint('help', __name__, url_prefix='/help')


@help_bp.route('/')
@require_authentication()
def help_home():
    """Display help home page with navigation to all guides"""
    return render_template('help/index.html')


@help_bp.route('/getting-started')
@require_authentication()
def getting_started():
    """Display getting started guide"""
    return render_template('help/getting_started.html')


@help_bp.route('/walmart-credentials')
@require_authentication()
def walmart_credentials():
    """Display Walmart Retail Link credentials setup guide"""
    return render_template('help/walmart_credentials.html')


@help_bp.route('/employee-management')
@require_authentication()
def employee_management():
    """Display employee management guide"""
    return render_template('help/employee_management.html')


@help_bp.route('/auto-scheduler')
@require_authentication()
def auto_scheduler_guide():
    """Display auto scheduler explanation and guide"""
    return render_template('help/auto_scheduler.html')


@help_bp.route('/review-approve')
@require_authentication()
def review_approve():
    """Display review and approval workflow guide"""
    return render_template('help/review_approve.html')
