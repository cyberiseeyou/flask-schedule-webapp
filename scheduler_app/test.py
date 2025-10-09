from edr.report_generator import EDRReportGenerator


RG = EDRReportGenerator()

RG.username = "mat.conder@productconnections.com"
RG.password = "Demos812Th$"
RG.mfa_credential_id = "18122365202"

RG.authenticate()
events = RG.browse_events()
print(events)
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
