#!/usr/bin/env python3
"""
Generate Load Test Data for Calendar Performance Testing
Generates 1000+ events across October 2025 with realistic distribution

Usage:
    python test_data/generate_load_test_data.py --count=1000 --month=2025-10
    python test_data/generate_load_test_data.py --count=10000 --month=2025-10 --output=test_data/load_test_10k.sql
"""

import argparse
import random
from datetime import datetime, timedelta

def generate_company_name():
    """Generate fake company/product names"""
    products = [
        'Super Pretzel', 'Nature Valley', 'Cheetos', 'Doritos', 'Lay\'s Chips',
        'Pepsi', 'Mountain Dew', 'Gatorade', 'Quaker Oats', 'Tropicana',
        'Lipton Tea', 'Aquafina', 'Starbucks', 'Frappuccino', 'Rockstar',
        'Muscle Milk', 'Naked Juice', 'SoBe', 'Sierra Mist', 'Mug Root Beer'
    ]
    return random.choice(products)

def generate_store_name():
    """Generate fake store names"""
    stores = [
        'Costco', 'Sam\'s Club', 'Walmart', 'Target', 'Kroger',
        'Safeway', 'Albertsons', 'Publix', 'HEB', 'Wegmans',
        'BJ\'s Wholesale', 'WinCo', 'Fred Meyer', 'Giant Eagle'
    ]
    store_chain = random.choice(stores)
    store_number = random.randint(100, 999)
    return f'{store_chain} #{store_number}'

def generate_load_test_data(month_start, event_count, output_file):
    """
    Generate SQL INSERT statements for load testing

    Args:
        month_start: Start date as string 'YYYY-MM-DD'
        event_count: Number of events to generate
        output_file: Path to output SQL file
    """

    month_start = datetime.strptime(month_start, '%Y-%m-%d')
    month_end = month_start + timedelta(days=30)

    # Event type distribution (realistic percentages)
    event_types = [
        ('CORE', 0.40),                 # 40% CORE events
        ('Juicer Production', 0.20),    # 20% Juicer
        ('Supervisor', 0.20),           # 20% Supervisor (should match CORE count)
        ('Freeosk', 0.10),              # 10% Freeosk
        ('Digitals', 0.10)              # 10% Digitals
    ]

    events = []
    schedules = []

    event_id_start = 5000
    schedule_id_start = 10000

    event_id = event_id_start
    schedule_id = schedule_id_start

    # Track CORE event numbers to create matching Supervisors
    core_event_numbers = []

    print(f"Generating {event_count} events for {month_start.strftime('%Y-%m')}...")

    for i in range(event_count):
        # Pick event type based on distribution
        event_type = random.choices(
            [t[0] for t in event_types],
            weights=[t[1] for t in event_types]
        )[0]

        # Random date within month
        days_offset = random.randint(0, 29)
        event_date = month_start + timedelta(days=days_offset)

        # Random time (8 AM to 5 PM)
        hour = random.randint(8, 17)
        minute = random.choice([0, 15, 30, 45])
        event_datetime = event_date.replace(hour=hour, minute=minute)

        # Generate project name based on event type
        if event_type == 'CORE':
            # Create unique 6-digit event number
            event_number = 600000 + len(core_event_numbers)
            core_event_numbers.append(event_number)
            product = generate_company_name()
            project_name = f'{event_number}-CORE-{product}'
            estimated_hours = round(random.uniform(4.0, 8.0), 1)

        elif event_type == 'Supervisor':
            # Match with a CORE event
            if core_event_numbers:
                event_number = random.choice(core_event_numbers)
                product = generate_company_name()
                project_name = f'{event_number}-Supervisor-{product}'
            else:
                # Fallback if no CORE events yet
                event_number = 600000 + i
                project_name = f'{event_number}-Supervisor-Fallback'
            estimated_hours = 0.08  # 5 minutes

        elif event_type == 'Juicer Production':
            store = generate_store_name()
            project_name = f'Juicer Production - {store}'
            estimated_hours = round(random.uniform(6.0, 8.0), 1)

        elif event_type == 'Freeosk':
            store = generate_store_name()
            project_name = f'Freeosk Setup - {store}'
            estimated_hours = round(random.uniform(3.0, 5.0), 1)

        elif event_type == 'Digitals':
            store = generate_store_name()
            project_name = f'Digital Display - {store}'
            estimated_hours = round(random.uniform(2.0, 4.0), 1)

        else:
            project_name = f'Other Event - {i}'
            estimated_hours = round(random.uniform(2.0, 6.0), 1)

        # 90% scheduled, 10% unscheduled (realistic ratio)
        is_scheduled = random.random() < 0.9
        condition = 'Scheduled' if is_scheduled else 'Unstaffed'

        # Escape single quotes in project names
        project_name_escaped = project_name.replace("'", "''")

        # Create event INSERT statement
        event_insert = (
            f"({event_id}, '{project_name_escaped}', '{event_type}', '{condition}', "
            f"{is_scheduled}, {estimated_hours}, "
            f"'{event_datetime.strftime('%Y-%m-%d %H:%M:%S')}', "
            f"'{event_date.strftime('%Y-%m-%d')}', NOW())"
        )
        events.append(event_insert)

        # Create schedule INSERT if event is scheduled
        if is_scheduled:
            # Random employee (assuming employee_ids 101-120 exist)
            employee_id = random.randint(101, 120)

            schedule_insert = (
                f"({schedule_id}, {event_id}, {employee_id}, "
                f"'{event_datetime.strftime('%Y-%m-%d %H:%M:%S')}', NOW())"
            )
            schedules.append(schedule_insert)
            schedule_id += 1

        event_id += 1

        # Progress indicator
        if (i + 1) % 100 == 0:
            print(f"  Generated {i + 1}/{event_count} events...")

    print(f"✅ Generated {len(events)} events and {len(schedules)} schedules")
    print(f"📝 Writing to {output_file}...")

    # Write to SQL file
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(f"-- Load Test Data: {event_count} events\n")
        f.write(f"-- Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"-- Month: {month_start.strftime('%Y-%m')}\n")
        f.write(f"--\n")
        f.write(f"-- Event ID range: {event_id_start} - {event_id - 1}\n")
        f.write(f"-- Schedule ID range: {schedule_id_start} - {schedule_id - 1}\n\n")

        # Events INSERT
        f.write("-- ============================================================\n")
        f.write("-- EVENTS\n")
        f.write("-- ============================================================\n\n")
        f.write("INSERT INTO events (event_id, project_name, event_type, condition, is_scheduled, estimated_hours, start_datetime, due_datetime, created_at)\n")
        f.write("VALUES\n")

        # Write in batches of 100 for better readability
        batch_size = 100
        for i in range(0, len(events), batch_size):
            batch = events[i:i + batch_size]
            f.write(',\n'.join(batch))
            if i + batch_size < len(events):
                f.write(',\n')
            else:
                f.write(';\n\n')

        # Schedules INSERT
        f.write("-- ============================================================\n")
        f.write("-- SCHEDULES\n")
        f.write("-- ============================================================\n\n")
        f.write("INSERT INTO schedule (schedule_id, event_id, employee_id, start_datetime, created_at)\n")
        f.write("VALUES\n")

        for i in range(0, len(schedules), batch_size):
            batch = schedules[i:i + batch_size]
            f.write(',\n'.join(batch))
            if i + batch_size < len(schedules):
                f.write(',\n')
            else:
                f.write(';\n\n')

        # Verification queries
        f.write("-- ============================================================\n")
        f.write("-- VERIFICATION QUERIES\n")
        f.write("-- ============================================================\n\n")

        f.write("-- 1. Count events by type:\n")
        f.write("-- SELECT event_type, COUNT(*) as count\n")
        f.write("-- FROM events\n")
        f.write(f"-- WHERE event_id BETWEEN {event_id_start} AND {event_id - 1}\n")
        f.write("-- GROUP BY event_type\n")
        f.write("-- ORDER BY event_type;\n\n")

        f.write("-- 2. Count scheduled vs unscheduled:\n")
        f.write("-- SELECT condition, COUNT(*) as count\n")
        f.write("-- FROM events\n")
        f.write(f"-- WHERE event_id BETWEEN {event_id_start} AND {event_id - 1}\n")
        f.write("-- GROUP BY condition;\n\n")

        f.write("-- 3. Events per day:\n")
        f.write("-- SELECT DATE(start_datetime) as event_date, COUNT(*) as count\n")
        f.write("-- FROM events\n")
        f.write(f"-- WHERE event_id BETWEEN {event_id_start} AND {event_id - 1}\n")
        f.write("-- GROUP BY DATE(start_datetime)\n")
        f.write("-- ORDER BY event_date;\n\n")

        # Cleanup script
        f.write("-- ============================================================\n")
        f.write("-- CLEANUP SCRIPT (Run after testing)\n")
        f.write("-- ============================================================\n\n")
        f.write(f"-- DELETE FROM schedule WHERE schedule_id BETWEEN {schedule_id_start} AND {schedule_id - 1};\n")
        f.write(f"-- DELETE FROM events WHERE event_id BETWEEN {event_id_start} AND {event_id - 1};\n\n")

    print(f"✅ SQL file written successfully!")
    print(f"\n📊 Statistics:")
    print(f"   Total events: {len(events)}")
    print(f"   Scheduled events: {len(schedules)}")
    print(f"   Unscheduled events: {len(events) - len(schedules)}")
    print(f"   CORE events: {sum(1 for e in events if 'CORE' in e and 'Supervisor' not in e)}")
    print(f"   Supervisor events: {sum(1 for e in events if 'Supervisor' in e)}")
    print(f"\n💡 To load data:")
    print(f"   psql -U your_user -d your_database -f {output_file}")
    print(f"   OR: mysql -u your_user -p your_database < {output_file}")


def main():
    parser = argparse.ArgumentParser(description='Generate load test data for calendar')
    parser.add_argument('--count', type=int, default=1000, help='Number of events to generate (default: 1000)')
    parser.add_argument('--month', type=str, default='2025-10-01', help='Month start date YYYY-MM-DD (default: 2025-10-01)')
    parser.add_argument('--output', type=str, default='test_data/load_test_data.sql', help='Output SQL file (default: test_data/load_test_data.sql)')

    args = parser.parse_args()

    # Validate month format
    try:
        datetime.strptime(args.month, '%Y-%m-%d')
    except ValueError:
        print(f"❌ Invalid month format: {args.month}")
        print("   Use format: YYYY-MM-DD (e.g., 2025-10-01)")
        return

    generate_load_test_data(args.month, args.count, args.output)


if __name__ == '__main__':
    main()
