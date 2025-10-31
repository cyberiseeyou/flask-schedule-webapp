"""
Script to convert Activity Log PDFs to JPG images
"""
import fitz  # PyMuPDF
from PIL import Image

def pdf_to_jpg(pdf_path, jpg_path, dpi=300):
    """
    Convert PDF to high-quality JPG image

    Args:
        pdf_path: Path to input PDF file
        jpg_path: Path to output JPG file
        dpi: Resolution in dots per inch (default 300 for high quality)
    """
    # Open the PDF
    doc = fitz.open(pdf_path)

    # Get the first page
    page = doc[0]

    # Calculate zoom factor for desired DPI
    # Default is 72 DPI, so zoom = desired_dpi / 72
    zoom = dpi / 72
    mat = fitz.Matrix(zoom, zoom)

    # Render page to pixmap
    pix = page.get_pixmap(matrix=mat)

    # Save as JPG
    pix.save(jpg_path)

    doc.close()
    print(f"Converted: {pdf_path} -> {jpg_path}")
    print(f"  Resolution: {pix.width} x {pix.height} pixels")

def main():
    print("Converting Activity Log PDFs to JPG...\n")

    # Convert modified Activity Log with QR code
    pdf_to_jpg(
        'Daily Paperwork/Event Table Activity Log - QR.pdf',
        'Daily Paperwork/Event Table Activity Log - QR.jpg',
        dpi=300
    )

    print()

    # Convert original Activity Log
    pdf_to_jpg(
        'Daily Paperwork/Event Table Activity Log.pdf',
        'Daily Paperwork/Event Table Activity Log.jpg',
        dpi=300
    )

    print("\nSuccess! Both JPG images have been created.")

if __name__ == '__main__':
    main()
