# Barcode Generation for Daily Item Numbers

## Overview
The Daily Item Numbers page now includes **UPC barcodes** next to each item number, making it easy to scan items for inventory management, price sign printing, and product verification.

## Features

### Barcode Types
The system intelligently selects the appropriate barcode format:

- **UPC-A**: Used for standard 12-digit item numbers (most common retail format)
- **Code128**: Used for shorter or longer item numbers (more flexible format)

### Automatic Padding
- Item numbers shorter than 12 digits are automatically zero-padded on the left
- Example: Item `123` becomes `000000000123` for UPC-A generation

### Barcode Specifications
- **Width**: 1.2 inches in PDF
- **Height**: 0.5 inches in PDF
- **Format**: PNG images embedded in PDF
- **Text**: Item number displayed below barcode for manual verification
- **Quality**: High-resolution images optimized for printing and scanning

## Table Layout

### New Column Structure
```
| Item Number | Barcode              | Description           |
|-------------|----------------------|----------------------|
| 123456      | [BARCODE IMAGE]      | Super Pretzel King   |
| 789012      | [BARCODE IMAGE]      | Organic Juice Blend  |
```

### Column Widths
- **Item Number**: 1.2 inches (left-aligned)
- **Barcode**: 1.5 inches (center-aligned)
- **Description**: 3.8 inches (left-aligned)

## Implementation Details

### Barcode Generation Function
**Location**: `services/daily_paperwork_generator.py::generate_barcode_image()`

**Process**:
1. Cleans item number (removes non-digit characters)
2. Determines appropriate barcode format (UPC-A or Code128)
3. Generates barcode image with custom options
4. Returns path to temporary PNG file
5. File is automatically cleaned up after PDF generation

**Barcode Options**:
```python
{
    'module_width': 0.2,      # Width of individual bars
    'module_height': 8.0,     # Height of bars in mm
    'quiet_zone': 2.0,        # White space around barcode
    'font_size': 8,           # Size of text below barcode
    'text_distance': 2.0,     # Space between bars and text
    'write_text': True,       # Show number below barcode
}
```

### PDF Integration

#### Complete Paperwork Package
**Location**: `services/daily_paperwork_generator.py::generate_item_numbers_pdf()`

**Changes**:
1. Added barcode generation for each item
2. Updated table to include barcode column
3. Adjusted column widths to accommodate barcodes
4. Centered barcode images in their column
5. Maintained theme consistency with navy blue headers

#### Standalone Daily Items List
**Location**: `edr/pdf_generator.py::DailyItemsListPDFGenerator`

**Changes**:
1. Added barcode imports and availability check
2. Implemented `generate_barcode_image()` method
3. Updated table to include barcode column
4. Adjusted column widths: Item Number (1.0"), Barcode (1.5"), Description (2.3"), Category (1.7")
5. Updated alignment for 4-column layout

## Dependencies

### Required Libraries
```txt
python-barcode>=0.15.1
Pillow>=10.0.0
```

### Installation
```bash
pip install python-barcode Pillow
```

## Usage

### Method 1: Complete Daily Paperwork Package
1. Navigate to **Printing** section
2. Select **Complete Daily Paperwork**
3. Choose date with scheduled events
4. Generate paperwork
5. Barcodes automatically appear in Daily Item Numbers page

### Method 2: Standalone Daily Items List
1. Navigate to **Printing** section
2. Select **Daily Item Numbers** (standalone)
3. Choose date with scheduled events
4. Authenticate with EDR system if needed
5. Generate item list
6. Barcodes automatically appear in the PDF

### Scanning Barcodes
The generated barcodes are:
- **Scannable** with standard retail barcode scanners
- **Print-ready** at standard PDF resolution
- **Readable** by Walmart's inventory systems
- **Compatible** with most POS systems

## Error Handling

### Fallback Behavior
If barcode generation fails for any item:
- Item still appears in table
- Barcode column shows "N/A"
- Description and item number remain intact
- PDF generation continues normally

### Common Issues
1. **Invalid item numbers**: Non-numeric characters are removed
2. **Very long numbers**: Automatically switches to Code128 format
3. **Missing library**: Gracefully degrades to text-only display

## Testing

### Test Script
**Location**: `test_barcode_generation.py`

**Runs**:
```bash
python test_barcode_generation.py
```

**Tests**:
1. ✓ Generates barcodes for various item number formats
2. ✓ Creates PDF with embedded barcode images
3. ✓ Verifies table layout and styling
4. ✓ Validates barcode image creation

### Sample Output
```
[PASS] Generated barcode for 123456
[PASS] Generated barcode for 789012345678
[PASS] Generated barcode for 99
[SUCCESS] Test PDF created: /tmp/test_item_numbers_[timestamp].pdf
```

## Visual Example

### Before (Text Only)
```
+--------------+---------------------------+
| Item Number  | Description               |
+--------------+---------------------------+
| 123456       | Super Pretzel King Size   |
| 789012       | Organic Juice Blend       |
+--------------+---------------------------+
```

### After (With Barcodes)
```
+--------------+------------------+---------------------------+
| Item Number  | Barcode          | Description               |
+--------------+------------------+---------------------------+
| 123456       | ||||||||||||     | Super Pretzel King Size   |
|              | 000000123456     |                           |
+--------------+------------------+---------------------------+
| 789012       | ||||||||||||     | Organic Juice Blend       |
|              | 000000789012     |                           |
+--------------+------------------+---------------------------+
```

## Benefits

### For Store Teams
- **Quick Scanning**: Scan items directly from printed sheets
- **Accurate Identification**: Eliminates manual number entry errors
- **Time Savings**: Faster product lookup and verification
- **Price Signs**: Easy printing of shelf tags

### For Inventory Management
- **Product Verification**: Quickly confirm correct items received
- **Stock Checking**: Scan to check inventory levels in Walmart systems
- **Order Preparation**: Verify items before events

### For Quality Control
- **Visual Verification**: Both barcode and text for double-checking
- **Audit Trail**: Printed proof of scheduled products
- **Error Prevention**: Catch mismatches before events start

## Technical Notes

### Barcode Standards
- **UPC-A**: 12 digits with check digit (11 data + 1 check)
- **Code128**: Variable length, high data density
- **Check Digit**: Automatically calculated per UPC standard

### Image Format
- **Type**: PNG (Portable Network Graphics)
- **Resolution**: Optimized for 300 DPI printing
- **Color**: Black bars on white background
- **Compression**: Lossless PNG compression

### Temporary Files
- Barcode images stored in system temp directory
- Automatically deleted after PDF generation
- No manual cleanup required
- Tracked in `self.temp_files` list

## Future Enhancements

Potential improvements:
- QR codes with additional item metadata
- Batch barcode printing for inventory sheets
- Customizable barcode sizes
- Export barcodes as separate image files
- Integration with mobile scanning apps
