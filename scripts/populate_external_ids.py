"""
Script to populate external_id (Crossmark RepID) for all employees
by looking them up in the Crossmark MVRetail system
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app, db
from app.integrations.external_api.session_api_service import session_api as external_api

def populate_external_ids():
    """Lookup and populate external_id for all employees missing it"""
    app = create_app()

    with app.app_context():
        Employee = app.config['Employee']

        # Get all active employees without external_id
        employees_missing_id = Employee.query.filter(
            Employee.is_active == True,
            Employee.external_id == None
        ).all()

        if not employees_missing_id:
            print("✅ All active employees already have external_id populated")
            return

        print(f"Found {len(employees_missing_id)} employees missing external_id")
        print("-" * 80)

        # Get available representatives from Crossmark (expand date range)
        from datetime import datetime, timedelta

        # Use a wider date range to get more reps
        start_date = datetime.now()
        end_date = start_date + timedelta(days=90)  # 90 days instead of 7

        print(f"Fetching representatives from Crossmark...")
        reps_data = external_api.get_available_representatives(start_date, end_date)

        if not reps_data:
            print("❌ Failed to fetch representatives from Crossmark")
            return

        # Parse representatives
        representatives = []
        if isinstance(reps_data, dict):
            if 'representatives' in reps_data:
                representatives = reps_data['representatives']
            elif 'data' in reps_data:
                representatives = reps_data['data']
            elif 'records' in reps_data:
                representatives = reps_data['records']
        elif isinstance(reps_data, list):
            representatives = reps_data

        print(f"Found {len(representatives)} representatives in Crossmark")
        print("-" * 80)

        # Track results
        updated_count = 0
        not_found_count = 0

        # Match each employee
        for emp in employees_missing_id:
            print(f"\nLooking up: {emp.name} ({emp.id})")

            # Try to find matching rep by name or employee ID
            matched_rep = None

            for rep in representatives:
                if not isinstance(rep, dict):
                    continue

                rep_name = rep.get('name') or rep.get('Name') or f"{rep.get('FirstName', '')} {rep.get('LastName', '')}".strip()
                rep_employee_id = rep.get('RepID') or rep.get('EmployeeID') or rep.get('employeeId')

                # Match by name (case-insensitive) or employee ID
                name_match = rep_name.lower().strip() == emp.name.lower().strip()
                id_match = emp.id and str(rep_employee_id) == str(emp.id)

                if name_match or id_match:
                    matched_rep = rep
                    break

            if matched_rep:
                # Get the external_id (repId, id, or RepID)
                external_id = matched_rep.get('repId') or matched_rep.get('id') or matched_rep.get('RepID')

                if external_id:
                    emp.external_id = str(external_id)
                    print(f"  ✅ Found: external_id = {external_id}")
                    updated_count += 1
                else:
                    print(f"  ⚠️  Matched but no ID field found in rep data")
                    not_found_count += 1
            else:
                print(f"  ❌ Not found in Crossmark system")
                not_found_count += 1

        # Commit changes
        if updated_count > 0:
            try:
                db.session.commit()
                print("\n" + "=" * 80)
                print(f"✅ Successfully updated {updated_count} employees")
                if not_found_count > 0:
                    print(f"⚠️  {not_found_count} employees not found in Crossmark")
                print("=" * 80)
            except Exception as e:
                db.session.rollback()
                print(f"\n❌ Error saving changes: {e}")
        else:
            print("\n⚠️  No employees were updated")

if __name__ == '__main__':
    populate_external_ids()
