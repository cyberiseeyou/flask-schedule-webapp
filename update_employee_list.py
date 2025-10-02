#!/usr/bin/env python3
"""
Update employee database to match the provided employee list
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'scheduler_app'))
from app import app, db, Employee, Schedule, EmployeeAvailability, EmployeeWeeklyAvailability

# Final employee list with correct IDs and names
FINAL_EMPLOYEES = {
    'US857761': 'MICHELLE MONTAGUE',
    'US863735': 'THOMAS RARICK', 
    'US928953': 'CODY WEAVER',  # New employee
    'US899165': 'ROBI DUNFEE',
    'US814117': 'CAROLYN MANN',
    'US815021': 'DIANE CARR',
    'US929037': 'ARIANA FAULKNER',
    'US914335': 'NANCY DINKINS',
    'US919042': 'KAREN MCCULLOUGH COLLIER',  # Keep database name in all caps
    'US929156': 'BRANDY CREASEY',
    'US924342': 'MAXX SPALLONE',  # Keep database name in all caps
    'US913438': 'LANIE SULLIVAN',  # Keep database name in all caps
    'US920644': 'Mat Conder'  # Keep mixed case, correct ID
}

def update_employee_database():
    """Update employee database to match the final list"""
    with app.app_context():
        try:
            print("Starting employee database update...")
            
            # Get current employees
            current_employees = Employee.query.all()
            current_ids = {emp.id: emp.name for emp in current_employees}
            
            print(f"Current employees: {len(current_employees)}")
            print(f"Target employees: {len(FINAL_EMPLOYEES)}")
            
            # Remove employees not in the final list
            for emp in current_employees:
                if emp.id not in FINAL_EMPLOYEES:
                    print(f"Removing employee: {emp.id} -> {emp.name}")
                    
                    # Check for scheduled events
                    scheduled_count = Schedule.query.filter_by(employee_id=emp.id).count()
                    if scheduled_count > 0:
                        print(f"  WARNING: Employee has {scheduled_count} scheduled events. Deactivating instead of deleting.")
                        emp.is_active = False
                    else:
                        # Delete related records
                        EmployeeWeeklyAvailability.query.filter_by(employee_id=emp.id).delete()
                        EmployeeAvailability.query.filter_by(employee_id=emp.id).delete()
                        db.session.delete(emp)
            
            # Add or update employees in the final list
            for emp_id, emp_name in FINAL_EMPLOYEES.items():
                existing = Employee.query.filter_by(id=emp_id).first()
                
                if existing:
                    print(f"Updating employee: {emp_id} -> {emp_name}")
                    existing.name = emp_name
                    existing.is_active = True  # Ensure they are active
                else:
                    print(f"Adding new employee: {emp_id} -> {emp_name}")
                    new_employee = Employee(
                        id=emp_id,
                        name=emp_name,
                        is_active=True,
                        is_supervisor=False
                    )
                    db.session.add(new_employee)
                    
                    # Create default weekly availability (available all days)
                    weekly_availability = EmployeeWeeklyAvailability(
                        employee_id=emp_id,
                        monday=True,
                        tuesday=True,
                        wednesday=True,
                        thursday=True,
                        friday=True,
                        saturday=True,
                        sunday=True
                    )
                    db.session.add(weekly_availability)
            
            # Handle Mat Conder's ID change if needed (from US276044 back to US920644)
            old_mat_conder = Employee.query.filter_by(id='US276044').first()
            if old_mat_conder:
                print("Found Mat Conder with old ID US276044, updating to US920644")
                # Update related records
                Schedule.query.filter_by(employee_id='US276044').update({'employee_id': 'US920644'})
                EmployeeAvailability.query.filter_by(employee_id='US276044').update({'employee_id': 'US920644'})
                EmployeeWeeklyAvailability.query.filter_by(employee_id='US276044').update({'employee_id': 'US920644'})
                
                # Delete old record
                db.session.delete(old_mat_conder)
                
                # Create new record with correct ID
                new_mat_conder = Employee(
                    id='US920644',
                    name='Mat Conder',
                    is_active=True,
                    is_supervisor=old_mat_conder.is_supervisor,
                    email=old_mat_conder.email,
                    phone=old_mat_conder.phone
                )
                db.session.add(new_mat_conder)
            
            # Commit all changes
            db.session.commit()
            print("Employee database update completed successfully!")
            
            # Verify the results
            print("\nFinal employee list:")
            final_employees = Employee.query.filter_by(is_active=True).order_by(Employee.name).all()
            for emp in final_employees:
                print(f"  {emp.id}: {emp.name}")
            
            print(f"\nTotal active employees: {len(final_employees)}")
                
        except Exception as e:
            print(f"Error during update: {str(e)}")
            db.session.rollback()
            raise

if __name__ == '__main__':
    update_employee_database()