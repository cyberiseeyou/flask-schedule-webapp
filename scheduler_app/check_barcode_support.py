"""
Check if barcode libraries are available in the current Python environment
"""
import sys

print(f"Python executable: {sys.executable}")
print(f"Python version: {sys.version}")
print("\nChecking barcode library support...")
print("=" * 60)

# Check python-barcode
try:
    import barcode
    print("[OK] python-barcode is installed")
    print(f"     Version: {barcode.__version__ if hasattr(barcode, '__version__') else 'unknown'}")
    print(f"     Location: {barcode.__file__}")
except ImportError as e:
    print(f"[FAIL] python-barcode is NOT installed: {e}")
    print("       Install with: pip install python-barcode")

# Check barcode.writer
try:
    from barcode.writer import ImageWriter
    print("[OK] barcode.writer.ImageWriter is available")
except ImportError as e:
    print(f"[FAIL] barcode.writer.ImageWriter is NOT available: {e}")

# Check Pillow
try:
    from PIL import Image
    import PIL
    print(f"[OK] Pillow is installed")
    print(f"     Version: {PIL.__version__}")
    print(f"     Location: {PIL.__file__}")
except ImportError as e:
    print(f"[FAIL] Pillow is NOT installed: {e}")
    print("       Install with: pip install Pillow")

# Try to generate a test barcode
print("\nTesting barcode generation...")
print("=" * 60)
try:
    import barcode
    from barcode.writer import ImageWriter
    import tempfile
    import os

    barcode_class = barcode.get_barcode_class('upca')
    test_barcode = barcode_class('12345678901', writer=ImageWriter())

    output_path = os.path.join(tempfile.gettempdir(), 'test_barcode')
    options = {
        'module_width': 0.2,
        'module_height': 8.0,
        'quiet_zone': 2.0,
        'font_size': 8,
        'text_distance': 2.0,
        'write_text': True,
    }

    test_barcode.save(output_path, options=options)
    final_path = output_path + '.png'

    if os.path.exists(final_path):
        file_size = os.path.getsize(final_path)
        print(f"[OK] Test barcode generated successfully")
        print(f"     Path: {final_path}")
        print(f"     Size: {file_size} bytes")

        # Clean up
        os.remove(final_path)
        print("[OK] Test file cleaned up")
    else:
        print(f"[FAIL] Barcode file was not created at {final_path}")

except Exception as e:
    print(f"[FAIL] Barcode generation test failed: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
print("Barcode support check complete!")
