"""
Celery worker configuration
Run this to start the Celery worker for background task processing
"""
from services.sync_service import celery_app
from app import app

# Import Flask app context for Celery tasks
celery_app.conf.update(app.config)

if __name__ == '__main__':
    celery_app.start()
