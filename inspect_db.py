"""
Inspect database schema and migration version
"""
import sqlite3
import os

def inspect_database():
    """Inspect the database schema"""
    basedir = os.path.abspath(os.path.dirname(__file__))
    db_path = os.path.join(basedir, 'instance', 'scheduler.db')

    if not os.path.exists(db_path):
        print(f"Database not found at: {db_path}")
        return

    print(f"Database found at: {db_path}\n")

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Check if alembic_version table exists
    cursor.execute("""
        SELECT name FROM sqlite_master
        WHERE type='table' AND name='alembic_version'
    """)
    if cursor.fetchone():
        print("Migration tracking table (alembic_version) exists")
        cursor.execute("SELECT version_num FROM alembic_version")
        current_version = cursor.fetchone()
        if current_version:
            print(f"Current migration version: {current_version[0]}\n")
        else:
            print("No migration version recorded\n")
    else:
        print("No migration tracking table found\n")

    # Get events table schema
    cursor.execute("PRAGMA table_info(events)")
    columns = cursor.fetchall()

    print("Events table columns:")
    for col in columns:
        print(f"  - {col[1]} ({col[2]})")

    # Check if 'condition' column exists
    has_condition = any(col[1] == 'condition' for col in columns)
    print(f"\n'condition' column exists: {has_condition}")

    conn.close()

if __name__ == '__main__':
    inspect_database()
