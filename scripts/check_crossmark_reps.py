"""
Debug script to check what Crossmark API returns for representatives
"""
import sys
import os
import json

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from app.integrations.external_api.session_api_service import session_api as external_api
from datetime import datetime, timedelta

def check_reps():
    """Check what the Crossmark API returns"""
    app = create_app()

    with app.app_context():
        print("Testing different date ranges to see what Crossmark returns...")
        print("-" * 80)

        # Try different date ranges
        test_ranges = [
            ("1 week", 7),
            ("30 days", 30),
            ("90 days", 90),
            ("1 year", 365),
        ]

        for label, days in test_ranges:
            start_date = datetime.now()
            end_date = start_date + timedelta(days=days)

            print(f"\n{label} ({start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}):")
            reps_data = external_api.get_available_representatives(start_date, end_date)

            if reps_data:
                print(f"  Response type: {type(reps_data)}")
                if isinstance(reps_data, dict):
                    print(f"  Keys: {list(reps_data.keys())}")

                # Try to extract representatives
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

                print(f"  Count: {len(representatives)}")

                # Show first rep if available
                if representatives and len(representatives) > 0:
                    print(f"  Sample rep data:")
                    print(f"    {json.dumps(representatives[0], indent=6)}")
            else:
                print("  No data returned")

        print("\n" + "=" * 80)
        print("FULL RESPONSE STRUCTURE:")
        print("-" * 80)

        # Get one more time and dump full structure
        reps_data = external_api.get_available_representatives()
        if reps_data:
            print(json.dumps(reps_data, indent=2))
        else:
            print("No data")

if __name__ == '__main__':
    check_reps()
