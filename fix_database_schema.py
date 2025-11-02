"""
Fix database schema and migration version
"""
import sqlite3
import os

def fix_database():
    """Fix the database schema and migration tracking"""
    basedir = os.path.abspath(os.path.dirname(__file__))
    db_path = os.path.join(basedir, 'instance', 'scheduler.db')

    if not os.path.exists(db_path):
        print(f"Database not found at: {db_path}")
        return

    print(f"Fixing database at: {db_path}\n")

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Step 1: Add missing 'condition' column to events table
        print("Step 1: Adding 'condition' column to events table...")
        try:
            cursor.execute("""
                ALTER TABLE events
                ADD COLUMN condition VARCHAR(20) DEFAULT 'Unstaffed'
            """)
            conn.commit()
            print("[OK] Added 'condition' column")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e).lower():
                print("[OK] Column 'condition' already exists")
            else:
                raise

        # Step 1b: Add missing 'parent_event_ref_num' column to events table
        print("\nStep 1b: Adding 'parent_event_ref_num' column to events table...")
        try:
            cursor.execute("""
                ALTER TABLE events
                ADD COLUMN parent_event_ref_num INTEGER
            """)
            conn.commit()
            print("[OK] Added 'parent_event_ref_num' column")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e).lower():
                print("[OK] Column 'parent_event_ref_num' already exists")
            else:
                raise

        # Step 1c: Add foreign key constraint (note: SQLite doesn't support adding FK to existing table)
        # The FK constraint is defined in the model but can't be added after table creation in SQLite
        print("[INFO] Foreign key constraint for parent_event_ref_num defined in model (SQLite limitation)")

        # Step 2: Update alembic_version to point to a valid migration
        print("\nStep 2: Updating migration version...")
        cursor.execute("SELECT version_num FROM alembic_version")
        current_version = cursor.fetchone()

        if current_version:
            print(f"Current version: {current_version[0]}")

            # Update to the migration just before the newest one
            # The newest migration expects condition column to exist
            # So we point to 0be04acd9951 which is before 58becd6c9441
            cursor.execute("""
                UPDATE alembic_version
                SET version_num = '0be04acd9951'
            """)
            conn.commit()
            print("[OK] Updated migration version to: 0be04acd9951")
        else:
            print("No migration version found, inserting initial version...")
            cursor.execute("""
                INSERT INTO alembic_version (version_num)
                VALUES ('0be04acd9951')
            """)
            conn.commit()
            print("[OK] Set migration version to: 0be04acd9951")

        # Step 3: Verify the fix
        print("\nStep 3: Verifying fix...")
        cursor.execute("PRAGMA table_info(events)")
        columns = cursor.fetchall()
        has_condition = any(col[1] == 'condition' for col in columns)
        has_parent_event_ref_num = any(col[1] == 'parent_event_ref_num' for col in columns)

        if has_condition:
            print("[OK] Events table has 'condition' column")
        else:
            print("[ERROR] Events table still missing 'condition' column")

        if has_parent_event_ref_num:
            print("[OK] Events table has 'parent_event_ref_num' column")
        else:
            print("[ERROR] Events table still missing 'parent_event_ref_num' column")

        cursor.execute("SELECT version_num FROM alembic_version")
        version = cursor.fetchone()
        print(f"[OK] Migration version: {version[0]}")

        print("\n[SUCCESS] Database fix complete!")
        print("\nNext step: Run 'python run_migrations.py' to apply remaining migrations")

    except Exception as e:
        print(f"[ERROR] Error fixing database: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()

if __name__ == '__main__':
    fix_database()
