import sys
import io
import json
import os
from decouple import config

# Set console encoding to UTF-8 to handle emojis
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

from edr.report_generator import EDRReportGenerator


RG = EDRReportGenerator()

# SECURITY: Use environment variables instead of hardcoded credentials
# Set these in your .env file:
#   WALMART_EDR_USERNAME=your_username
#   WALMART_EDR_PASSWORD=your_password
#   WALMART_EDR_MFA_CREDENTIAL_ID=your_mfa_id
RG.username = config('WALMART_EDR_USERNAME', default='')
RG.password = config('WALMART_EDR_PASSWORD', default='')
RG.mfa_credential_id = config('WALMART_EDR_MFA_CREDENTIAL_ID', default='')

# Validate credentials are set
if not all([RG.username, RG.password, RG.mfa_credential_id]):
    print("\n" + "="*80)
    print("ERROR: Missing Walmart EDR credentials!")
    print("="*80)
    print("\nPlease set the following in your .env file:")
    print("  WALMART_EDR_USERNAME=your_username")
    print("  WALMART_EDR_PASSWORD=your_password")
    print("  WALMART_EDR_MFA_CREDENTIAL_ID=your_mfa_id")
    print("="*80 + "\n")
    sys.exit(1)

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
