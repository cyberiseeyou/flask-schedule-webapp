#!/usr/bin/env python3
"""
Migration script to add employee_time_off table for tracking requested days off.
"""

import os
import sys
import sqlite3

# Add the scheduler_app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'scheduler_app'))

from app import app, db, EmployeeTimeOff

def migrate_time_off_table():
    """Add employee_time_off table for tracking time off requests"""
    
    # Get database path
    basedir = os.path.dirname(__file__)
    db_path = os.path.join(basedir, 'scheduler_app', 'instance', 'scheduler.db')
    
    if not os.path.exists(db_path):
        print("Database file not found. Creating new database...")
        with app.app_context():
            db.create_all()
        return True
    
    print(f"Migrating database at: {db_path}")
    
    try:
        # Connect directly to SQLite
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if employee_time_off table already exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='employee_time_off'")
        table_exists = cursor.fetchone()
        
        if table_exists:
            print("employee_time_off table already exists.")
        else:
            print("Creating employee_time_off table...")
            # Create the table
            cursor.execute("""
                CREATE TABLE employee_time_off (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    employee_id VARCHAR(50) NOT NULL,
                    start_date DATE NOT NULL,
                    end_date DATE NOT NULL,
                    reason VARCHAR(200),
                    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(employee_id) REFERENCES employees (id)
                )
            """)
            
            # Create index for performance
            cursor.execute("""
                CREATE INDEX idx_employee_time_off_dates 
                ON employee_time_off (employee_id, start_date, end_date)
            """)
            
            conn.commit()
            print("employee_time_off table created successfully.")
        
        # Test the table by creating and deleting a sample record
        with app.app_context():
            # Make sure table is accessible from SQLAlchemy
            test_count = EmployeeTimeOff.query.count()
            print(f"Time off table accessible. Current records: {test_count}")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"Error during migration: {e}")
        return False

if __name__ == '__main__':
    print("Starting employee time off table migration...")
    success = migrate_time_off_table()
    if success:
        print("Employee time off table migration completed successfully!")
    else:
        print("Employee time off table migration failed!")
        sys.exit(1)