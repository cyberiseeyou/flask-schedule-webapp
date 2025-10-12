# Cache-First Implementation Plan

## Current Situation

### Data Structure Mismatch
There are TWO different data sources with different structures:

1. **browse_events() API** (currently cached):
```python
{
    'eventId': 612730,
    'eventType': 'Club Choice Company',
    'eventDate': '2025-10-01',
    'billType': '6 Hour',
    'eventStatus': 'APPROVED',
    'itemNbr': 980055288,
    'itemDesc': 'ORANGE JUICE',
    'upcNbr': 25540600000,
    'deptNbr': 56,
    'deptDesc': 'Produce and Floral',
    'vendorNbr': 456104,
    'vendorBilledDesc': 'SAMS PRODUCE DCS',
    'featuredItemInd': 'Y',
    # NO INSTRUCTIONS
}
```

2. **get_edr_report() API** (NOT cached):
```python
{
    'demoId': 612730,
    'demoClassCode': 'Club Choice Company',
    'demoStatusCode': 'APPROVED',
    'demoDate': '2025-10-01',
    'demoName': '10.01-LKD-CF-Orange/Lemonade/Limeade',
    'demoInstructions': {
        'demoPrepnTxt': 'Prepare juice samples...',
        'demoPortnTxt': '2 oz portions...'
    },
    'itemDetails': [
        {
            'itemNbr': 980055288,
            'itemDesc': 'ORANGE JUICE',
            'gtin': 25540600000,
            'vendorNbr': 456104,
            'deptNbr': 56
        }
    ]
}
```

### Current Routes That Need Updates

1. **`/printing/edr/daily-items-list`** (line 964)
   - Currently calls: `edr_authenticator.get_edr_report(event_number)`
   - Passes data to: `DailyItemsListPDFGenerator.generate_daily_items_pdf(edr_data_list)`
   - **Can use cache**: Only needs item information (itemNbr, itemDesc, upcNbr)

2. **`/printing/edr/batch-download`** (line 783)
   - Currently calls: `edr_authenticator.get_edr_report(event_number)`
   - Passes data to: `EDRPDFGenerator.generate_pdf(edr_data, temp_path, employee_name)`
   - **Needs full data**: Requires instructions from get_edr_report()

3. **`/printing/complete-paperwork`** (line 577)
   - Uses: `DailyPaperworkGenerator` which calls `get_edr_report()`
   - **Complex**: Generates multiple documents

## Implementation Options

### Option 1: Hybrid Approach (Recommended)
- Use cache for **item information** only
- Still call get_edr_report() for **full EDRs with instructions**
- Update PDF generators to accept both formats

**Pros**:
- Maintains full functionality (instructions still available)
- Cache reduces API calls for item lists
- Simpler to implement

**Cons**:
- Still requires authentication for full EDR reports
- Not 100% cache-first

### Option 2: Cache Everything
- Cache data from BOTH browse_events() AND get_edr_report()
- Store two types of records in database
- Use appropriate data for each operation

**Pros**:
- True cache-first for everything
- Minimal authentication needed

**Cons**:
- More complex database schema
- Need to fetch/cache full EDRs individually (slower initial sync)
- More storage required

### Option 3: Accept Limitations
- Use cache for item information (no instructions)
- Generate EDRs from cache without instructions (already works with `generate_html_report_from_cache()`)
- Note on reports: "Instructions not available - check Event Management System"

**Pros**:
- Simple implementation
- Already partially implemented
- Fast

**Cons**:
- EDRs missing instructions
- Users may need to check system separately

## Recommended Implementation Steps

### Phase 1: Items List (Simple)
1. Update `DailyItemsListPDFGenerator` to accept cached data format
2. Modify `/printing/edr/daily-items-list` to use `get_event_data_smart()`
3. Falls back to API if cache is empty

### Phase 2: EDR PDFs (Complex)
Decision needed: Accept EDRs without instructions, or keep calling API for full data?

### Phase 3: Daily Paperwork (Complex)
Update `DailyPaperworkGenerator` to use cache-first approach

## Questions for User

1. **Are instructions required** on EDR PDFs, or is it acceptable to show "N/A - Check Event Management System"?

2. **Authentication strategy**: Should system automatically authenticate if cache is empty, or prompt user to "Please sync first"?

3. **Sync frequency**: How often will users manually sync? Once per day? Multiple times?

4. **Priority**: Which route is most important to convert first?
   - Daily Items List (simplest)
   - EDR Batch Download (most complex)
   - Complete Paperwork (most comprehensive)
