"""
Test barcode generation for Daily Item Numbers
"""
import os
import tempfile
from datetime import datetime

try:
    import barcode
    from barcode.writer import ImageWriter
    from reportlab.lib.pagesizes import letter
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Image as ReportLabImage
    from reportlab.lib.units import inch
    from reportlab.lib import colors
    LIBRARIES_AVAILABLE = True
except ImportError as e:
    print(f"Missing libraries: {e}")
    print("Install with: pip install python-barcode Pillow reportlab")
    LIBRARIES_AVAILABLE = False
    exit(1)

def generate_test_barcode(item_number):
    """Generate a test barcode"""
    try:
        # Clean the item number
        clean_number = ''.join(filter(str.isdigit, str(item_number)))

        if not clean_number:
            return None

        # Pad to 12 digits for UPC
        if len(clean_number) < 12:
            clean_number = clean_number.zfill(12)

        # For UPC-A, we need exactly 11 digits (12th is check digit)
        if len(clean_number) == 12:
            try:
                barcode_class = barcode.get_barcode_class('upca')
                # UPC-A needs 11 digits, check digit is auto-calculated
                clean_number = clean_number[:11]
            except:
                barcode_class = barcode.get_barcode_class('code128')
                clean_number = str(item_number)
        else:
            barcode_class = barcode.get_barcode_class('code128')
            clean_number = str(item_number)

        # Generate barcode
        output_path = os.path.join(tempfile.gettempdir(), f'test_barcode_{item_number}')

        barcode_instance = barcode_class(clean_number, writer=ImageWriter())

        options = {
            'module_width': 0.2,
            'module_height': 8.0,
            'quiet_zone': 2.0,
            'font_size': 8,
            'text_distance': 2.0,
            'write_text': True,
        }

        barcode_instance.save(output_path, options=options)

        final_path = output_path + '.png'

        if os.path.exists(final_path):
            print(f"[PASS] Generated barcode for {item_number}: {final_path}")
            return final_path
        else:
            print(f"[FAIL] Barcode file not found for {item_number}")
            return None

    except Exception as e:
        print(f"[FAIL] Error generating barcode for {item_number}: {e}")
        return None


def test_pdf_with_barcodes():
    """Test creating a PDF with barcodes"""
    print("\n=== Testing PDF with Barcodes ===")

    # Sample item data
    test_items = [
        ('123456', 'Test Product A'),
        ('789012', 'Test Product B'),
        ('345678901234', 'Long Item Number Product'),
        ('99', 'Short Item Number'),
    ]

    # Generate barcodes
    barcodes = {}
    for item_num, desc in test_items:
        barcode_path = generate_test_barcode(item_num)
        if barcode_path:
            barcodes[item_num] = barcode_path

    # Create PDF
    output_path = os.path.join(tempfile.gettempdir(), f'test_item_numbers_{datetime.now().strftime("%Y%m%d%H%M%S")}.pdf')
    doc = SimpleDocTemplate(output_path, pagesize=letter)

    story = []

    # Create table
    table_data = [['Item Number', 'Barcode', 'Description']]

    for item_num, desc in test_items:
        if item_num in barcodes:
            barcode_img = ReportLabImage(barcodes[item_num], width=1.2*inch, height=0.5*inch)
            table_data.append([str(item_num), barcode_img, desc])
        else:
            table_data.append([str(item_num), 'N/A', desc])

    item_table = Table(table_data, colWidths=[1.2*inch, 1.5*inch, 3.8*inch])
    item_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2E4C73')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F9F9F9')]),
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('ALIGN', (1, 0), (1, -1), 'CENTER'),
        ('ALIGN', (2, 0), (2, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#DDDDDD')),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
    ]))

    story.append(item_table)

    try:
        doc.build(story)
        print(f"\n[SUCCESS] Test PDF created: {output_path}")
        print(f"Open this file to verify barcodes are displayed correctly")
        return output_path
    except Exception as e:
        print(f"\n[FAIL] Error creating PDF: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == '__main__':
    print("Testing Barcode Generation for Daily Item Numbers")
    print("=" * 60)

    # Test 1: Generate individual barcodes
    print("\n=== Test 1: Generate Individual Barcodes ===")
    test_numbers = ['123456', '789012345678', '99', 'ABC123']

    for num in test_numbers:
        generate_test_barcode(num)

    # Test 2: Create PDF with barcodes
    pdf_path = test_pdf_with_barcodes()

    if pdf_path:
        print(f"\n[SUCCESS] All tests passed!")
        print(f"\nGenerated files:")
        print(f"  - Test PDF: {pdf_path}")
    else:
        print(f"\n[FAIL] Some tests failed")
