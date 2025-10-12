"""
Test script to check if EDR methods return UPC numbers
"""
import sys
import io
# Set UTF-8 encoding for stdout to handle emojis
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from edr_report_generator import EDRReportGenerator
import json

def test_edr_methods():
    generator = EDRReportGenerator()

    print("=" * 80)
    print("EDR UPC NUMBER TEST")
    print("=" * 80)

    # Authenticate first
    print("\n🔐 Starting authentication...")
    print("Step 1: Submitting password...")
    if not generator.step1_submit_password():
        print("❌ Password submission failed!")
        return

    print("\nStep 2: Requesting MFA code...")
    if not generator.step2_request_mfa_code():
        print("❌ MFA request failed!")
        return

    # Now pause and ask for the MFA code
    print("\n" + "=" * 80)
    mfa_code = input("📱 Enter the MFA code you received: ").strip()
    print("=" * 80)

    print("\nStep 3: Validating MFA code...")
    if not generator.step3_validate_mfa_code(mfa_code):
        print("❌ MFA validation failed!")
        return

    print("\nStep 4-6: Completing authentication...")
    generator.step4_register_page_access()
    generator.step5_navigate_to_event_management()

    if not generator.step6_authenticate_event_management():
        print("❌ Event Management auth failed!")
        return

    print("✅ Authentication complete!")

    print("\n" + "=" * 80)
    print("TEST 1: get_event_detail_report_page()")
    print("=" * 80)

    # Test 1: Check the event detail report page
    page_html = generator.get_event_detail_report_page()

    if page_html:
        print(f"\n📄 Page HTML length: {len(page_html)} characters")

        # Check if 'upc' or 'gtin' appears in the HTML
        upc_count = page_html.lower().count('upc')
        gtin_count = page_html.lower().count('gtin')

        print(f"🔍 Found 'upc' mentions: {upc_count}")
        print(f"🔍 Found 'gtin' mentions: {gtin_count}")

        # Save to file for inspection
        with open('test_edr_page.html', 'w', encoding='utf-8') as f:
            f.write(page_html)
        print("💾 Saved HTML to: test_edr_page.html")
    else:
        print("❌ No HTML content returned")

    print("\n" + "=" * 80)
    print("TEST 2: get_edr_report(event_id)")
    print("=" * 80)

    # Test 2: Get a specific EDR report
    # Use a test event ID (you may need to change this to a valid one)
    test_event_id = input("\n📝 Enter an event ID to test (or press Enter for 606034): ").strip()
    if not test_event_id:
        test_event_id = "606034"

    print(f"\n📋 Testing with event ID: {test_event_id}")
    edr_data = generator.get_edr_report(test_event_id)

    if edr_data:
        # Pretty print the structure
        print("\n📊 EDR Data Structure:")
        print(json.dumps(edr_data, indent=2)[:1000] + "...\n")

        # Check for UPC/GTIN in the data
        edr_str = json.dumps(edr_data).lower()
        print(f"🔍 Found 'upc' in data: {'upc' in edr_str}")
        print(f"🔍 Found 'gtin' in data: {'gtin' in edr_str}")

        # Check item details specifically
        item_details = edr_data.get('itemDetails', [])
        if item_details:
            print(f"\n📦 Number of items: {len(item_details)}")
            print("\n🔍 First item structure:")
            if item_details:
                first_item = item_details[0]
                print(json.dumps(first_item, indent=2))

                # Check specifically for UPC fields
                if 'gtin' in first_item:
                    print(f"\n✅ GTIN field found: {first_item['gtin']}")
                if 'upc' in first_item or 'upcNbr' in first_item:
                    print(f"✅ UPC field found: {first_item.get('upc') or first_item.get('upcNbr')}")

                # List all keys in the first item
                print(f"\n📋 All fields in item: {list(first_item.keys())}")
        else:
            print("⚠️ No item details in response")

        # Save full response
        with open('test_edr_response.json', 'w', encoding='utf-8') as f:
            json.dump(edr_data, f, indent=2)
        print("\n💾 Saved full response to: test_edr_response.json")
    else:
        print("❌ No EDR data returned")

    print("\n" + "=" * 80)
    print("TEST COMPLETE")
    print("=" * 80)

if __name__ == "__main__":
    test_edr_methods()
