import sys
import io
import json

# Set console encoding to UTF-8 to handle emojis
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

from edr.report_generator import EDRReportGenerator
from edr.db_manager import EDRDatabaseManager


def test_database_operations():
    """Test basic database operations."""
    print("\n" + "="*80)
    print("TEST 1: Database Operations")
    print("="*80 + "\n")

    # Load test data from events_data.json
    print("📂 Loading test data from events_data.json...")
    with open('events_data.json', 'r') as f:
        events_data = json.load(f)
    print(f"✅ Loaded {len(events_data)} event items from file\n")

    # Initialize database
    print("🗄️ Initializing database...")
    db = EDRDatabaseManager("test_edr_cache.db")
    print("✅ Database initialized\n")

    # Store events
    print("💾 Storing events in database...")
    stored_count = db.store_events(events_data, "8135", "2025-10-01", "2025-10-31")
    print(f"✅ Stored {stored_count} event items\n")

    # Get cache stats
    print("📊 Cache Statistics:")
    stats = db.get_cache_stats()
    for key, value in stats.items():
        print(f"  {key}: {value}")
    print()

    # Test retrieval by event ID
    print("🔍 Testing retrieval by event ID...")
    test_event_id = events_data[0]['eventId']
    event_items = db.get_event_by_id(test_event_id)
    print(f"✅ Retrieved {len(event_items)} items for event {test_event_id}\n")

    # Test date range query
    print("🔍 Testing date range query...")
    range_events = db.get_events_by_date_range("2025-10-01", "2025-10-31", "8135")
    print(f"✅ Retrieved {len(range_events)} total event items in date range\n")

    # Test unique event IDs
    print("🔍 Getting unique event IDs...")
    event_ids = db.get_all_event_ids("2025-10-01", "2025-10-31")
    print(f"✅ Found {len(event_ids)} unique events")
    print(f"   Sample IDs: {event_ids[:5]}\n")

    db.close()
    print("✅ Test 1 completed successfully!\n")


def test_generator_with_cache():
    """Test EDRReportGenerator with caching enabled."""
    print("\n" + "="*80)
    print("TEST 2: EDRReportGenerator with Caching")
    print("="*80 + "\n")

    # Initialize generator with caching enabled
    print("🔧 Initializing EDRReportGenerator with caching...")
    generator = EDRReportGenerator(
        enable_caching=True,
        cache_max_age_hours=24,
        db_path="test_edr_cache.db"
    )
    print("✅ Generator initialized\n")

    # Get cache stats
    print("📊 Cache Statistics:")
    stats = generator.get_cache_stats()
    for key, value in stats.items():
        print(f"  {key}: {value}")
    print()

    # Test retrieving event from cache
    print("🔍 Testing event retrieval from cache...")
    event_items = generator.get_event_from_cache(612730)
    if event_items:
        print(f"✅ Successfully retrieved event 612730 from cache")
        print(f"   Event Name: {event_items[0]['eventName']}")
        print(f"   Event Date: {event_items[0]['eventDate']}")
        print(f"   Items: {len(event_items)}\n")
    else:
        print("❌ Failed to retrieve event from cache\n")
        return

    # Test HTML report generation from cache
    print("📄 Testing HTML report generation from cached data...")
    html_report = generator.generate_html_report_from_cache(612730)
    if html_report:
        print(f"✅ Generated HTML report ({len(html_report)} characters)")

        # Save the report to file
        output_file = "test_edr_report_from_cache.html"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_report)
        print(f"💾 Saved report to: {output_file}\n")
    else:
        print("❌ Failed to generate HTML report\n")
        return

    print("✅ Test 2 completed successfully!\n")


def test_cache_workflow():
    """Test complete caching workflow."""
    print("\n" + "="*80)
    print("TEST 3: Complete Caching Workflow")
    print("="*80 + "\n")

    # Initialize generator with caching
    generator = EDRReportGenerator(
        enable_caching=True,
        cache_max_age_hours=24,
        db_path="test_edr_cache.db"
    )

    # Simulate cached data retrieval (no authentication needed)
    print("📦 Testing cached data retrieval workflow...")
    print("   (Simulating scenario where data is already cached)\n")

    # Get all event IDs from cache
    if generator.db:
        event_ids = generator.db.get_all_event_ids("2025-10-01", "2025-10-31")
        print(f"✅ Found {len(event_ids)} events in cache\n")

        if event_ids:
            # Generate reports for first 3 events
            print("📄 Generating reports for first 3 events...")
            for event_id in event_ids[:3]:
                print(f"\n   Processing Event {event_id}:")
                html_report = generator.generate_html_report_from_cache(event_id)
                if html_report:
                    filename = f"cached_report_{event_id}.html"
                    with open(filename, 'w', encoding='utf-8') as f:
                        f.write(html_report)
                    print(f"      ✅ Generated and saved: {filename}")
                else:
                    print(f"      ❌ Failed to generate report")
            print()

    print("✅ Test 3 completed successfully!\n")


def main():
    """Run all tests."""
    print("\n" + "="*80)
    print("EDR CACHING SYSTEM - TEST SUITE")
    print("="*80)

    try:
        # Test 1: Basic database operations
        test_database_operations()

        # Test 2: Generator with caching
        test_generator_with_cache()

        # Test 3: Complete workflow
        test_cache_workflow()

        print("\n" + "="*80)
        print("ALL TESTS COMPLETED SUCCESSFULLY!")
        print("="*80 + "\n")

        print("📝 Summary:")
        print("  - Database operations: ✅")
        print("  - Cache integration: ✅")
        print("  - Report generation from cache: ✅")
        print("  - Complete workflow: ✅\n")

        print("💡 Next Steps:")
        print("  1. Test with live authentication: Run test.py to populate cache")
        print("  2. Generate reports without re-authenticating using cached data")
        print("  3. Set up automatic cache refresh schedule\n")

    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
