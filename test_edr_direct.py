"""Direct test of EDR functionality with specific event IDs"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from edr_printer.edr_report_generator import EDRReportGenerator

# Event IDs to test (provided by user)
event_ids = ["606878", "604207"]

print("="*60)
print("EDR Report Generator Test")
print("="*60)

# Initialize EDR generator with credentials
edr_gen = EDRReportGenerator(
    username="mat.conder@productconnections.com",
    password="Demos812Th$",
    mfa_credential_id="18122365202"
)

# Step 1 & 2: Request MFA code
print("\n[*] Requesting MFA code...")
if edr_gen.request_mfa_code():
    print("[+] MFA code sent to your phone")

    # Get MFA code from user
    mfa_code = input("\n[?] Enter the MFA code you received: ").strip()

    # Complete authentication
    print(f"\n[*] Authenticating with MFA code: {mfa_code}")
    if edr_gen.complete_authentication_with_mfa_code(mfa_code):
        print("[+] Authentication successful!")
        print(f"[+] Auth token: {edr_gen.auth_token[:50] if edr_gen.auth_token else 'None'}...")

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
                print(f"    Demo Type: {edr_data.get('demoClassCode', 'N/A')}")

                item_details = edr_data.get('itemDetails', [])
                print(f"    Item Count: {len(item_details)}")

                if item_details:
                    print(f"\n    Sample Items:")
                    for i, item in enumerate(item_details[:3], 1):
                        print(f"      {i}. {item.get('itemDesc', 'N/A')} (#{item.get('itemNbr', 'N/A')})")

                # Generate HTML report
                print(f"\n[*] Generating HTML report...")
                html_report = edr_gen.generate_html_report(edr_data)

                # Save report
                filename = f"edr_report_{event_id}_test.html"
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(html_report)
                print(f"[+] Report saved to: {filename}")

                # Get absolute path
                abs_path = os.path.abspath(filename)
                print(f"[+] Full path: {abs_path}")
            else:
                print(f"[-] No data returned for event {event_id}")

        print(f"\n{'='*60}")
        print("Test complete!")
        print(f"{'='*60}")
    else:
        print("[-] Authentication failed")
else:
    print("[-] Failed to request MFA code")
