"""
Generate proper barcodes with numbers positioned below and correct check digits
"""
import barcode
from barcode.writer import ImageWriter
from PIL import Image, ImageDraw, ImageFont
import os

# Product data with their UPC codes
products = [
    {"code": "333832507", "name": "RED SEEDLESS GRAPES"},
    {"code": "81355201026", "name": "ORGANIC GREEN GRAPES"},
    {"code": "85013800224", "name": "ORGANIC RED GRAPES"},
    {"code": "3383250791", "name": "GREEN GRAPES"},
    {"code": "25540600000", "name": "ORANGE JUICE"},
    {"code": "25540500000", "name": "LEMONADE"}
]

def generate_barcode_with_text(code, product_name, output_path):
    """
    Generate a barcode image with the code number properly positioned below
    The library will automatically add the check digit

    Args:
        code: The numeric code for the barcode
        product_name: Name of the product
        output_path: Where to save the barcode image
    """
    print(f"Generating barcode for: {product_name}")
    print(f"  Input code: {code}")

    # Determine barcode format based on length
    code_length = len(code)

    # Use Code128 which handles variable lengths and adds check digits
    barcode_class = barcode.get_barcode_class('code128')

    # Configure writer options to show text below barcode
    writer = ImageWriter()
    writer.set_options({
        'module_width': 0.3,        # Width of the bars
        'module_height': 15.0,      # Height of bars in mm
        'quiet_zone': 6.5,          # Margin around barcode
        'font_size': 12,            # Size of text below
        'text_distance': 5.0,       # Distance between barcode and text
        'write_text': True,         # IMPORTANT: Show the numbers below barcode
        'background': 'white',
        'foreground': 'black',
    })

    # Generate barcode
    barcode_instance = barcode_class(code, writer=writer)

    # Save with proper filename (remove .png as library adds it)
    filename = output_path.replace('.png', '')
    full_path = barcode_instance.save(filename)

    print(f"  Output code: {code} (displayed below barcode)")
    print(f"  Saved to: {full_path}\n")

    return full_path

def create_barcode_sheet():
    """Create individual barcode files for each product"""
    output_dir = "Daily Paperwork/Barcodes"
    os.makedirs(output_dir, exist_ok=True)

    print("="*70)
    print("BARCODE GENERATOR - With numbers positioned below barcodes")
    print("="*70)
    print()

    generated_files = []
    for product in products:
        output_path = f"{output_dir}/{product['code']}_{product['name'].replace(' ', '_')}.png"
        barcode_file = generate_barcode_with_text(
            product['code'],
            product['name'],
            output_path
        )
        generated_files.append({
            'file': barcode_file,
            'code': product['code'],
            'name': product['name']
        })

    print("="*70)
    print(f"SUCCESS! All {len(generated_files)} barcodes generated in:")
    print(f"  {output_dir}/")
    print("="*70)
    print("\nGenerated files:")
    for item in generated_files:
        print(f"  - {os.path.basename(item['file'])}")

    return generated_files

def main():
    create_barcode_sheet()

if __name__ == '__main__':
    main()
