"""
Clean up temporary Alembic tables left from failed migrations
"""
import sqlite3
import os

def cleanup_temp_tables():
    """Remove temporary Alembic tables"""
    # Get project root (parent of scripts directory)
    basedir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    db_path = os.path.join(basedir, 'instance', 'scheduler.db')

    if not os.path.exists(db_path):
        print(f"[ERROR] Database not found at: {db_path}")
        return

    print(f"Cleaning up database at: {db_path}\n")

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Find all tables starting with '_alembic_tmp_'
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name LIKE '_alembic_tmp_%'
        """)

        temp_tables = cursor.fetchall()

        if not temp_tables:
            print("[OK] No temporary Alembic tables found")
        else:
            print(f"Found {len(temp_tables)} temporary table(s):")
            for table in temp_tables:
                table_name = table[0]
                print(f"  - {table_name}")
                cursor.execute(f"DROP TABLE IF EXISTS {table_name}")
                print(f"    [OK] Dropped {table_name}")

        conn.commit()
        print("\n[SUCCESS] Cleanup complete!")

    except Exception as e:
        print(f"[ERROR] Error cleaning up: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()

if __name__ == '__main__':
    cleanup_temp_tables()
