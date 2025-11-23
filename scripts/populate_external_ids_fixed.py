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
            print("All active employees already have external_id populated")
            return

        print(f"Found {len(employees_missing_id)} employees missing external_id")
        print("-" * 80)

        # Get available representatives from Crossmark
        print(f"Fetching representatives from Crossmark...")
        reps_data = external_api.get_available_representatives()

        if not reps_data:
            print("Failed to fetch representatives from Crossmark")
            return

        # Parse representatives - FIXED to handle reps object structure
        representatives = []
        if isinstance(reps_data, dict):
            # Check for 'reps' key which contains an object
            if 'reps' in reps_data:
                # Convert reps object to list of values
                reps_obj = reps_data['reps']
                representatives = list(reps_obj.values()) if isinstance(reps_obj, dict) else []
            elif 'representatives' in reps_data:
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

            # Try to find matching rep by employeeId field
            matched_rep = None

            for rep in representatives:
                if not isinstance(rep, dict):
                    continue

                # Get various ID fields
                rep_employee_id = rep.get('employeeId') or rep.get('RepID') or rep.get('repMvid')
                rep_name = (rep.get('title') or rep.get('name') or rep.get('Name') or
                           f"{rep.get('FirstName', '')} {rep.get('LastName', '')}").strip()

                # Match by employee ID (most reliable)
                if rep_employee_id and emp.id and str(rep_employee_id).upper() == str(emp.id).upper():
                    matched_rep = rep
                    break

                # Fallback: Match by name (case-insensitive)
                if rep_name.lower().strip() == emp.name.lower().strip():
                    matched_rep = rep
                    break

            if matched_rep:
                # Get the external_id (repId is the numeric scheduling ID)
                external_id = matched_rep.get('repId') or matched_rep.get('id') or matched_rep.get('RepID')

                if external_id:
                    emp.external_id = str(external_id)
                    print(f"  [OK] Found: external_id = {external_id}")
                    updated_count += 1
                else:
                    print(f"  [WARN] Matched but no repId field found")
                    not_found_count += 1
            else:
                print(f"  [NOT FOUND] Not found in Crossmark system")
                not_found_count += 1

        # Commit changes
        if updated_count > 0:
            try:
                db.session.commit()
                print("\n" + "=" * 80)
                print(f"SUCCESS: Updated {updated_count} employees")
                if not_found_count > 0:
                    print(f"WARNING: {not_found_count} employees not found in Crossmark")
                print("=" * 80)
            except Exception as e:
                db.session.rollback()
                print(f"\nERROR saving changes: {e}")
        else:
            print("\nNo employees were updated")

if __name__ == '__main__':
    populate_external_ids()
