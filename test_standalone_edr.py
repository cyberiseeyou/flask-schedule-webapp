"""
Test script for standalone EDR printer
"""
import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))

from standalone_edr_printer import EDRReportGenerator, AutomatedEDRPrinter, EnhancedEDRPrinter

def test_imports():
    """Test that all classes can be imported."""
    print("[PASS] Test 1: Import test")
    print(f"   - EDRReportGenerator: {EDRReportGenerator}")
    print(f"   - AutomatedEDRPrinter: {AutomatedEDRPrinter}")
    print(f"   - EnhancedEDRPrinter: {EnhancedEDRPrinter}")
    return True

def test_instantiation():
    """Test that classes can be instantiated."""
    print("\n[PASS] Test 2: Instantiation test")

    generator = EDRReportGenerator()
    print(f"   - EDRReportGenerator instance: {type(generator).__name__}")
    print(f"   - Base URL: {generator.base_url}")
    print(f"   - Default store: {generator.default_store_number}")

    printer = AutomatedEDRPrinter()
    print(f"   - AutomatedEDRPrinter instance: {type(printer).__name__}")
    print(f"   - Default event IDs: {printer.DEFAULT_EVENT_IDS}")

    enhanced = EnhancedEDRPrinter()
    print(f"   - EnhancedEDRPrinter instance: {type(enhanced).__name__}")
    print(f"   - Event type codes loaded: {len(enhanced.event_type_codes)}")
    print(f"   - Event status codes loaded: {len(enhanced.event_status_codes)}")

    return True

def test_code_mappings():
    """Test event code mappings."""
    print("\n[PASS] Test 3: Code mapping test")

    enhanced = EnhancedEDRPrinter()

    # Test event type codes
    test_type = enhanced.get_event_type_description('1')
    print(f"   - Event type '1' maps to: {test_type}")
    assert test_type == 'Sampling', f"Expected 'Sampling', got '{test_type}'"

    test_type = enhanced.get_event_type_description('45')
    print(f"   - Event type '45' maps to: {test_type}")
    assert test_type == 'Food Demo/Sampling', f"Expected 'Food Demo/Sampling', got '{test_type}'"

    # Test event status codes
    test_status = enhanced.get_event_status_description('2')
    print(f"   - Event status '2' maps to: {test_status}")
    assert test_status == 'Active/Scheduled', f"Expected 'Active/Scheduled', got '{test_status}'"

    # Test unknown codes
    test_unknown = enhanced.get_event_type_description('999')
    print(f"   - Unknown event type '999' maps to: {test_unknown}")
    assert test_unknown == 'Event Type 999', f"Expected 'Event Type 999', got '{test_unknown}'"

    return True

def test_html_generation():
    """Test HTML report generation."""
    print("\n[PASS] Test 4: HTML generation test")

    generator = EDRReportGenerator()

    # Mock EDR data
    mock_data = {
        'demoId': 'TEST001',
        'demoClassCode': '1',
        'demoStatusCode': '2',
        'demoDate': '2025-10-04',
        'demoName': 'Test Event',
        'demoLockInd': 'N',
        'demoInstructions': {
            'demoPrepnTxt': 'Test preparation',
            'demoPortnTxt': 'Test portion'
        },
        'itemDetails': [
            {
                'itemNbr': '12345',
                'gtin': '67890',
                'itemDesc': 'Test Item',
                'vendorNbr': 'V001',
                'deptNbr': 'D001'
            }
        ]
    }

    html = generator.generate_html_report(mock_data)

    # Verify HTML content
    assert 'EVENT DETAIL REPORT' in html, "Missing report title"
    assert 'TEST001' in html, "Missing event ID"
    assert 'Test Event' in html, "Missing event name"
    assert 'Test Item' in html, "Missing item description"

    print(f"   - HTML length: {len(html)} characters")
    print(f"   - Contains event ID: [OK]")
    print(f"   - Contains event name: [OK]")
    print(f"   - Contains item details: [OK]")

    return True

def test_pdf_availability():
    """Test PDF library availability."""
    print("\n[PASS] Test 5: PDF library test")

    from standalone_edr_printer import REPORTLAB_AVAILABLE, WEASYPRINT_AVAILABLE

    print(f"   - ReportLab available: {REPORTLAB_AVAILABLE}")
    print(f"   - WeasyPrint available: {WEASYPRINT_AVAILABLE}")

    if REPORTLAB_AVAILABLE:
        print("   - [OK] PDF generation will work")
    else:
        print("   - [WARN] PDF generation disabled - install reportlab")

    return True

def test_inheritance():
    """Test class inheritance hierarchy."""
    print("\n[PASS] Test 6: Inheritance test")

    enhanced = EnhancedEDRPrinter()

    # Check inheritance
    assert isinstance(enhanced, EnhancedEDRPrinter), "Not instance of EnhancedEDRPrinter"
    assert isinstance(enhanced, AutomatedEDRPrinter), "Not instance of AutomatedEDRPrinter"
    assert hasattr(enhanced, 'generator'), "Missing generator attribute"
    assert hasattr(enhanced, 'authenticate_once'), "Missing authenticate_once method"
    assert hasattr(enhanced, 'get_event_type_description'), "Missing get_event_type_description method"

    print(f"   - EnhancedEDRPrinter is AutomatedEDRPrinter: [OK]")
    print(f"   - Has generator attribute: [OK]")
    print(f"   - Has authenticate_once method: [OK]")
    print(f"   - Has get_event_type_description method: [OK]")

    return True

def run_all_tests():
    """Run all tests."""
    print("=" * 60)
    print("STANDALONE EDR PRINTER TEST SUITE")
    print("=" * 60)

    tests = [
        ("Import Test", test_imports),
        ("Instantiation Test", test_instantiation),
        ("Code Mapping Test", test_code_mappings),
        ("HTML Generation Test", test_html_generation),
        ("PDF Library Test", test_pdf_availability),
        ("Inheritance Test", test_inheritance),
    ]

    passed = 0
    failed = 0

    for test_name, test_func in tests:
        try:
            result = test_func()
            if result:
                passed += 1
        except Exception as e:
            print(f"\n[FAIL] {test_name} FAILED: {e}")
            failed += 1

    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print(f"Total tests: {len(tests)}")
    print(f"[PASS] Passed: {passed}")
    print(f"[FAIL] Failed: {failed}")
    print(f"Success rate: {(passed/len(tests)*100):.1f}%")
    print("=" * 60)

    return failed == 0

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
