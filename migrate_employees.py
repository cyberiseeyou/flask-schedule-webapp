#!/usr/bin/env python3
"""
Migration script to add job_title and adult_beverage_trained columns to employees table.
"""

import os
import sys
import sqlite3

# Add the scheduler_app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'scheduler_app'))

from app import app, db, Employee

def migrate_employee_table():
    """Add job_title and adult_beverage_trained columns to employees table"""
    
    # Get database path
    basedir = os.path.dirname(__file__)
    db_path = os.path.join(basedir, 'scheduler_app', 'instance', 'scheduler.db')
    
    if not os.path.exists(db_path):
        print("Database file not found. Creating new database...")
        with app.app_context():
            db.create_all()
        return True
    
    print(f"Migrating employee table at: {db_path}")
    
    try:
        # Connect directly to SQLite
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check existing columns
        cursor.execute("PRAGMA table_info(employees)")
        columns = [column[1] for column in cursor.fetchall()]
        
        # Add job_title column if it doesn't exist
        if 'job_title' not in columns:
            print("Adding job_title column...")
            cursor.execute("ALTER TABLE employees ADD COLUMN job_title VARCHAR(50) DEFAULT 'Event Specialist'")
            conn.commit()
            print("job_title column added successfully.")
        else:
            print("job_title column already exists.")
        
        # Add adult_beverage_trained column if it doesn't exist
        if 'adult_beverage_trained' not in columns:
            print("Adding adult_beverage_trained column...")
            cursor.execute("ALTER TABLE employees ADD COLUMN adult_beverage_trained BOOLEAN DEFAULT 0")
            conn.commit()
            print("adult_beverage_trained column added successfully.")
        else:
            print("adult_beverage_trained column already exists.")
        
        # Now update existing employees with job titles based on is_supervisor flag
        with app.app_context():
            print("Updating existing employees with job titles...")
            employees = Employee.query.all()
            updated_count = 0
            
            for employee in employees:
                # Set job title based on existing is_supervisor flag
                if employee.is_supervisor and (not employee.job_title or employee.job_title == 'Event Specialist'):
                    employee.job_title = 'Club Supervisor'
                    updated_count += 1
                    print(f"Updated '{employee.name}' to Club Supervisor")
                elif not employee.job_title or employee.job_title == 'Event Specialist':
                    # Keep default Event Specialist for non-supervisors
                    employee.job_title = 'Event Specialist'
            
            db.session.commit()
            print(f"Updated {updated_count} employees with job titles.")
            
            # Show summary
            print("\nJob title summary:")
            title_counts = db.session.query(Employee.job_title, db.func.count(Employee.id)).group_by(Employee.job_title).all()
            for job_title, count in title_counts:
                print(f"  {job_title}: {count} employees")
            
            # Show adult beverage training summary
            ab_trained_count = Employee.query.filter_by(adult_beverage_trained=True).count()
            total_employees = Employee.query.count()
            print(f"\nAdult Beverage Training: {ab_trained_count}/{total_employees} employees trained")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"Error during migration: {e}")
        return False

if __name__ == '__main__':
    print("Starting employee table migration...")
    success = migrate_employee_table()
    if success:
        print("Employee table migration completed successfully!")
    else:
        print("Employee table migration failed!")
        sys.exit(1)