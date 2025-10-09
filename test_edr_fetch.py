"""Test script to fetch EDR data for specific event IDs"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from edr_printer.edr_report_generator import EDRReportGenerator
import pickle

# Event IDs to test
event_ids = ["606878", "604207"]

# Initialize EDR generator
edr_gen = EDRReportGenerator()

# Load cached session
cache_file = r"C:\Users\mathe\AppData\Local\Temp\edr_session_default.pkl"
if os.path.exists(cache_file):
    print(f"[*] Loading cached session from {cache_file}")
    with open(cache_file, 'rb') as f:
        cached_data = pickle.load(f)

        # Restore cookies
        for cookie in cached_data['cookies']:
            edr_gen.session.cookies.set_cookie(cookie)

        # Restore auth token
        edr_gen.auth_token = cached_data.get('auth_token')

    print(f"[+] Loaded {len(cached_data['cookies'])} cookies")
    print(f"[+] Auth token: {edr_gen.auth_token[:50] if edr_gen.auth_token else 'None'}...")
else:
    print("[-] No cached session found!")
    sys.exit(1)

# Test each event ID
for event_id in event_ids:
    print(f"\n{'='*60}")
    print(f"Testing Event ID: {event_id}")
    print(f"{'='*60}")

    # Fetch EDR data
    edr_data = edr_gen.get_edr_report(event_id)

    if edr_data:
        print(f"[+] Successfully retrieved EDR data!")
        print(f"    Demo ID: {edr_data.get('demoId', 'N/A')}")
        print(f"    Demo Name: {edr_data.get('demoName', 'N/A')}")
        print(f"    Demo Date: {edr_data.get('demoDate', 'N/A')}")
        print(f"    Demo Status: {edr_data.get('demoStatusCode', 'N/A')}")
        print(f"    Item Count: {len(edr_data.get('itemDetails', []))}")

        # Generate HTML report
        html_report = edr_gen.generate_html_report(edr_data)

        # Save report
        filename = f"edr_report_{event_id}_test.html"
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(html_report)
        print(f"[+] Report saved to: {filename}")
    else:
        print(f"[-] No data returned for event {event_id}")

print(f"\n{'='*60}")
print("Test complete!")
print(f"{'='*60}")
