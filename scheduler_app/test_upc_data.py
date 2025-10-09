"""
Test script to check what UPC data is available in item_details
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from walmart_api.retail_link_api import RetailLinkAPI
from datetime import datetime, timedelta
import json

def check_upc_data():
    """Check what UPC fields are available in the actual EDR data"""
    print("Fetching EDR data to check UPC fields...")
    print("=" * 80)

    try:
        api = RetailLinkAPI()

        # Get tomorrow's date
        tomorrow = datetime.now().date() + timedelta(days=1)

        # Fetch EDR data
        edr_data_list = api.get_edr_data(tomorrow)

        if not edr_data_list:
            print("No EDR data found for tomorrow")
            return

        print(f"Found {len(edr_data_list)} events for {tomorrow}")
        print("=" * 80)

        # Check first event's item details
        for idx, edr_data in enumerate(edr_data_list[:3], 1):  # Check first 3 events
            event_name = edr_data.get('demoName', 'N/A')
            item_details = edr_data.get('itemDetails', [])

            print(f"\nEvent {idx}: {event_name}")
            print(f"Number of items: {len(item_details) if item_details else 0}")

            if item_details and len(item_details) > 0:
                # Check first item
                first_item = item_details[0]
                print(f"\nFirst item fields:")
                print(f"  itemNbr: {first_item.get('itemNbr', 'NOT FOUND')}")
                print(f"  upcNbr: {first_item.get('upcNbr', 'NOT FOUND')}")
                print(f"  gtin: {first_item.get('gtin', 'NOT FOUND')}")
                print(f"  itemDesc: {first_item.get('itemDesc', 'NOT FOUND')}")

                # Show all available fields
                print(f"\n  All available fields in this item:")
                for key in sorted(first_item.keys()):
                    value = first_item[key]
                    if len(str(value)) > 50:
                        value = str(value)[:50] + "..."
                    print(f"    {key}: {value}")

                # Check a few more items
                if len(item_details) > 1:
                    print(f"\n  Checking UPC fields for all items in this event:")
                    for i, item in enumerate(item_details[:5], 1):  # First 5 items
                        item_nbr = item.get('itemNbr', 'N/A')
                        upc_nbr = item.get('upcNbr', 'NOT FOUND')
                        gtin = item.get('gtin', 'NOT FOUND')
                        print(f"    Item {i}: itemNbr={item_nbr}, upcNbr={upc_nbr}, gtin={gtin}")

            print("-" * 80)

    except Exception as e:
        print(f"Error fetching EDR data: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    check_upc_data()
