#!/usr/bin/env python3
"""
Migration script to update employee IDs from name-based IDs to actual Employee IDs from CSV
"""
import sys
import os
sys.path.append('./scheduler_app')
from app import app, db, Employee, Schedule, EmployeeAvailability, EmployeeWeeklyAvailability

# Employee ID mapping from CSV analysis
EMPLOYEE_ID_MAPPING = {
    'CAROLYN_MANN': 'US814117',
    'DIANE_CARR': 'US815021', 
    'MICHELLE_MONTAGUE': 'US857761',
    'ROBI_DUNFEE': 'US899165',
    'LANIE_SULLIVAN': 'US913438',
    'NANCY_DINKINS': 'US914335',
    'MAXX_SPALLONE': 'US924342'
}

# Additional employees from CSV that might not be in database yet
NEW_EMPLOYEES = {
    'US863735': 'THOMAS RARICK',
    'US919042': 'KAREN MCCULLOUGH COLLIER', 
    'US920644': 'Mat Conder',
    'US929037': 'ARIANA FAULKNER',
    'US929156': 'BRANDY CREASEY'
}

def migrate_employee_ids():
    """Migrate employee IDs from name-based to actual Employee IDs"""
    with app.app_context():
        try:
            print("Starting employee ID migration...")
            
            # First, update existing employees with correct IDs
            for old_id, new_id in EMPLOYEE_ID_MAPPING.items():
                employee = Employee.query.filter_by(id=old_id).first()
                if employee:
                    print(f"Updating employee {old_id} -> {new_id} ({employee.name})")
                    
                    # Update related records first
                    Schedule.query.filter_by(employee_id=old_id).update({'employee_id': new_id})
                    EmployeeAvailability.query.filter_by(employee_id=old_id).update({'employee_id': new_id})
                    EmployeeWeeklyAvailability.query.filter_by(employee_id=old_id).update({'employee_id': new_id})
                    
                    # Update the employee ID
                    employee.id = new_id
                    db.session.add(employee)
                else:
                    print(f"Employee with old ID {old_id} not found")
            
            # Add new employees that are in CSV but not in database
            for emp_id, emp_name in NEW_EMPLOYEES.items():
                existing = Employee.query.filter_by(id=emp_id).first()
                if not existing:
                    print(f"Adding new employee: {emp_id} -> {emp_name}")
                    new_employee = Employee(
                        id=emp_id,
                        name=emp_name,
                        is_active=True,
                        is_supervisor=False
                    )
                    db.session.add(new_employee)
                else:
                    print(f"Employee {emp_id} ({emp_name}) already exists")
            
            # Commit all changes
            db.session.commit()
            print("Migration completed successfully!")
            
            # Verify the results
            print("\nFinal employee list:")
            employees = Employee.query.all()
            for emp in employees:
                print(f"ID: {emp.id}, Name: {emp.name}")
                
        except Exception as e:
            print(f"Error during migration: {str(e)}")
            db.session.rollback()
            raise

if __name__ == '__main__':
    migrate_employee_ids()