import sys
import io
import json

# Set console encoding to UTF-8 to handle emojis
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

from edr.report_generator import EDRReportGenerator


RG = EDRReportGenerator()

RG.username = "mat.conder@productconnections.com"
RG.password = "Demos812Th$"
RG.mfa_credential_id = "18122365202"

if RG.authenticate():
    print("\n" + "="*80)
    print("AUTHENTICATION SUCCESSFUL!")
    print("="*80 + "\n")

    # Browse events
    events = RG.browse_events()

    print("\n" + "="*80)
    print(f"FOUND {len(events)} EVENTS")
    print("="*80 + "\n")

    # Pretty print the events data
    print(json.dumps(events, indent=2))

    # Save to file for later analysis
    with open('events_data.json', 'w') as f:
        json.dump(events, f, indent=2)
    print("\n" + "="*80)
    print("Events data saved to: events_data.json")
    print("="*80)
else:
    print("\n" + "="*80)
    print("AUTHENTICATION FAILED!")
    print("="*80)
# eventId = event[0]
# eventType = event[1]
# eventStatus = event[4]
# lockDate = event[5]
# itemNbr = event[6]
# itemDesc = event[7]
# upcNbr = event[8]
# deptDesc = event[10]
# eventName = event[18]

# print(f"Event ID: {eventId}")
# print(f"Event Name: {eventName}")
# print(f"Event Type: {eventType}")
# print(f"Event Status: {eventStatus}")
# print(f"Lock Date: {lockDate}")
# print(f"Item Number: {itemNbr}")
# print(f"Item Description: {itemDesc}")
# print(f"UPC Number: {upcNbr}")
# print(f"Department Description: {deptDesc}")
