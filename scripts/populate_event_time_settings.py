#!/usr/bin/env python3
"""
Database migration script to populate default event time settings
"""
import sys
import os

# Add parent directory to path to import app
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from app.models.registry import get_models

app = create_app()


def populate_event_time_settings():
    """Populate default event time settings in SystemSettings table"""
    with app.app_context():
        try:
            models = get_models()
            SystemSetting = models['SystemSetting']

            print("Populating event time settings...")

            # Freeosk times
            SystemSetting.set_setting(
                'freeosk_start_time',
                '09:00',
                setting_type='string',
                user='system',
                description='Freeosk event start time'
            )
            SystemSetting.set_setting(
                'freeosk_end_time',
                '09:15',
                setting_type='string',
                user='system',
                description='Freeosk event end time'
            )
            print("[OK] Freeosk times configured")

            # Digital Setup 1-4 (4 time slots)
            digital_setup_slots = [
                {'slot': 1, 'start': '09:15', 'end': '09:30'},
                {'slot': 2, 'start': '09:30', 'end': '09:45'},
                {'slot': 3, 'start': '09:45', 'end': '10:00'},
                {'slot': 4, 'start': '10:00', 'end': '10:15'},
            ]

            for slot_config in digital_setup_slots:
                slot = slot_config['slot']
                SystemSetting.set_setting(
                    f'digital_setup_{slot}_start_time',
                    slot_config['start'],
                    setting_type='string',
                    user='system',
                    description=f'Digital Setup slot {slot} start time'
                )
                SystemSetting.set_setting(
                    f'digital_setup_{slot}_end_time',
                    slot_config['end'],
                    setting_type='string',
                    user='system',
                    description=f'Digital Setup slot {slot} end time'
                )
            print("[OK] Digital Setup times configured (4 slots)")

            # Core 1-4 (4 time slots with lunch breaks)
            core_slots = [
                {'slot': 1, 'start': '09:45', 'lunch_begin': '13:00', 'lunch_end': '13:30', 'end': '16:15'},
                {'slot': 2, 'start': '10:30', 'lunch_begin': '13:45', 'lunch_end': '14:15', 'end': '17:00'},
                {'slot': 3, 'start': '11:00', 'lunch_begin': '14:15', 'lunch_end': '14:45', 'end': '17:30'},
                {'slot': 4, 'start': '11:30', 'lunch_begin': '14:45', 'lunch_end': '15:15', 'end': '18:00'},
            ]

            for slot_config in core_slots:
                slot = slot_config['slot']
                SystemSetting.set_setting(
                    f'core_{slot}_start_time',
                    slot_config['start'],
                    setting_type='string',
                    user='system',
                    description=f'Core slot {slot} start time'
                )
                SystemSetting.set_setting(
                    f'core_{slot}_lunch_begin_time',
                    slot_config['lunch_begin'],
                    setting_type='string',
                    user='system',
                    description=f'Core slot {slot} lunch begin time'
                )
                SystemSetting.set_setting(
                    f'core_{slot}_lunch_end_time',
                    slot_config['lunch_end'],
                    setting_type='string',
                    user='system',
                    description=f'Core slot {slot} lunch end time'
                )
                SystemSetting.set_setting(
                    f'core_{slot}_end_time',
                    slot_config['end'],
                    setting_type='string',
                    user='system',
                    description=f'Core slot {slot} end time'
                )
            print("[OK] Core times configured (4 slots)")

            # Supervisor times
            SystemSetting.set_setting(
                'supervisor_start_time',
                '12:00',
                setting_type='string',
                user='system',
                description='Supervisor event start time'
            )
            SystemSetting.set_setting(
                'supervisor_end_time',
                '12:05',
                setting_type='string',
                user='system',
                description='Supervisor event end time'
            )
            print("[OK] Supervisor times configured")

            # Digital Teardown 1-4 (4 time slots)
            digital_teardown_slots = [
                {'slot': 1, 'start': '17:00', 'end': '17:15'},
                {'slot': 2, 'start': '17:15', 'end': '17:30'},
                {'slot': 3, 'start': '17:30', 'end': '17:45'},
                {'slot': 4, 'start': '17:45', 'end': '18:00'},
            ]

            for slot_config in digital_teardown_slots:
                slot = slot_config['slot']
                SystemSetting.set_setting(
                    f'digital_teardown_{slot}_start_time',
                    slot_config['start'],
                    setting_type='string',
                    user='system',
                    description=f'Digital Teardown slot {slot} start time'
                )
                SystemSetting.set_setting(
                    f'digital_teardown_{slot}_end_time',
                    slot_config['end'],
                    setting_type='string',
                    user='system',
                    description=f'Digital Teardown slot {slot} end time'
                )
            print("[OK] Digital Teardown times configured (4 slots)")

            # Other event type times
            SystemSetting.set_setting(
                'other_start_time',
                '10:00',
                setting_type='string',
                user='system',
                description='Other event type start time'
            )
            SystemSetting.set_setting(
                'other_end_time',
                '10:15',
                setting_type='string',
                user='system',
                description='Other event type end time'
            )
            print("[OK] Other event times configured")

            print("\n[SUCCESS] Event time settings migration completed successfully!")
            print("\nConfigured settings:")
            print("  - Freeosk: 1 time slot")
            print("  - Digital Setup: 4 time slots")
            print("  - Core: 4 time slots (with lunch breaks)")
            print("  - Supervisor: 1 time slot")
            print("  - Digital Teardown: 4 time slots")
            print("  - Other: 1 time slot")

        except Exception as e:
            print(f"[ERROR] Error during migration: {e}")
            raise


if __name__ == '__main__':
    populate_event_time_settings()
