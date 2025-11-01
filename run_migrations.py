"""
Direct migration runner script
Runs database migrations without Flask CLI
"""
from app import create_app
from app.extensions import db
from flask_migrate import upgrade, current, init, migrate as flask_migrate_migrate
import os

def run_migrations():
    """Run database migrations"""
    app = create_app()

    with app.app_context():
        migrations_dir = os.path.join(os.path.dirname(__file__), 'migrations')

        if not os.path.exists(migrations_dir):
            print("[ERROR] Migrations directory not found!")
            return

        try:
            # Get current migration version
            print("Checking current migration version...")
            current_version = current()
            print(f"Current version: {current_version}")
        except Exception as e:
            print(f"Could not get current version: {e}")

        try:
            # Apply all pending migrations
            print("\nApplying pending migrations...")
            upgrade(directory=migrations_dir)
            print("[SUCCESS] All migrations applied successfully")
        except Exception as e:
            print(f"[ERROR] Error applying migrations: {e}")
            import traceback
            traceback.print_exc()
            raise

if __name__ == '__main__':
    run_migrations()
