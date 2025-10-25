"""
Generate UPC barcodes from the upc_barcodes.html file
"""
import barcode
from barcode.writer import ImageWriter
from PIL import Image, ImageDraw, ImageFont
import os

# UPC codes to generate
upc_codes = [
    "229233130748",
    "22869372198"
]

def generate_barcode(upc_code, copies=3):
    """Generate barcode images for a given UPC code"""
    print(f"Generating barcodes for UPC: {upc_code}")

    # Create output directory if it doesn't exist
    output_dir = "barcode_output"
    os.makedirs(output_dir, exist_ok=True)

    # Generate barcodes for each copy
    for i in range(1, copies + 1):
        # Generate the barcode
        upc = barcode.get('upca', upc_code, writer=ImageWriter())

        # Save with options
        filename = f"{output_dir}/upc_{upc_code}_copy_{i}"
        options = {
            'module_width': 0.4,  # Width of bars
            'module_height': 15.0,  # Height of bars in mm
            'quiet_zone': 6.5,  # Margin
            'font_size': 14,
            'text_distance': 5,
            'background': 'white',
            'foreground': 'black',
        }

        barcode_path = upc.save(filename, options)
        print(f"  [OK] Created: {barcode_path}")

    print()

def main():
    print("=" * 60)
    print("UPC Barcode Generator")
    print("=" * 60)
    print()

    for upc_code in upc_codes:
        generate_barcode(upc_code, copies=3)

    print("=" * 60)
    print(f"All barcodes generated in 'barcode_output' directory")
    print("=" * 60)

if __name__ == "__main__":
    main()
