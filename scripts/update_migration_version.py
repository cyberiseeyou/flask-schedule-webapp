"""
Update migration version directly to skip problematic migration
"""
import sqlite3
import os

def update_migration_version():
    """Update migration version to latest"""
    # Get project root (parent of scripts directory)
    basedir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    db_path = os.path.join(basedir, 'instance', 'scheduler.db')

    if not os.path.exists(db_path):
        print(f"[ERROR] Database not found at: {db_path}")
        return

    print(f"Updating migration version in: {db_path}\n")

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Check current version
        cursor.execute("SELECT version_num FROM alembic_version")
        current_version = cursor.fetchone()

        if current_version:
            print(f"Current migration version: {current_version[0]}")

            # Update to latest migration version
            # This skips the problematic migration since we've manually added the columns
            latest_version = '58becd6c9441'
            cursor.execute("""
                UPDATE alembic_version
                SET version_num = ?
            """, (latest_version,))
            conn.commit()
            print(f"[OK] Updated migration version to: {latest_version}")
        else:
            print("[ERROR] No migration version found in database")

        print("\n[SUCCESS] Migration version updated successfully!")

    except Exception as e:
        print(f"[ERROR] Error updating migration version: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()

if __name__ == '__main__':
    update_migration_version()
