"""
Script to replace handwashing graphic with QR code on Activity Log PDF
"""
from PIL import Image
import io
import fitz  # PyMuPDF for PDF manipulation and image extraction

def extract_qr_code_from_pdf(pdf_path):
    """Extract the first QR code image from the PDF"""
    doc = fitz.open(pdf_path)
    page = doc[0]

    # Get all images from the page
    images = page.get_images()

    if not images:
        print("No images found in PDF")
        return None

    # Extract the first image (assuming it's a QR code)
    for img_index, img in enumerate(images):
        xref = img[0]
        base_image = doc.extract_image(xref)
        image_bytes = base_image["image"]

        # Convert to PIL Image
        image = Image.open(io.BytesIO(image_bytes))

        # Save as temp file for inspection
        print(f"Found image {img_index}: {image.size} - {image.format}")

        # Return the first suitable image (likely QR code)
        if min(image.size) > 50:  # Filter out very small images
            return image

    return None

def modify_pdf_with_qr(base_pdf_path, qr_image, output_path):
    """Directly modify the PDF using PyMuPDF to cover handwashing graphic with QR code"""
    # Open the PDF
    doc = fitz.open(base_pdf_path)
    page = doc[0]

    # Get page dimensions
    page_rect = page.rect
    page_width = page_rect.width
    page_height = page_rect.height

    print(f"Page dimensions: {page_width} x {page_height}")

    # Define the area to cover (handwashing graphic in top-right)
    # In fitz coordinates: (0,0) is top-left corner
    # The handwashing character starts around x=400
    # Cover entire right corner area to ensure complete coverage
    cover_rect = fitz.Rect(400, 0, page_width, 125)  # x0, y0, x1, y1

    # Draw white rectangle to cover the handwashing graphic
    page.draw_rect(cover_rect, color=None, fill=(1, 1, 1), width=0)

    # Convert PIL Image to bytes
    img_buffer = io.BytesIO()
    qr_image.save(img_buffer, format='PNG')
    img_bytes = img_buffer.getvalue()

    # Position for QR code (centered in the covered area)
    qr_size = 75
    qr_rect = fitz.Rect(
        page_width - qr_size - 20,  # x0: 20 points from right edge
        10,  # y0: 10 points from top
        page_width - 20,  # x1
        10 + qr_size  # y1
    )

    # Insert QR code image
    page.insert_image(qr_rect, stream=img_bytes)

    # Save the modified PDF
    doc.save(output_path)
    doc.close()

def main():
    print("Step 1: Extracting QR code from Pre-Demo-Checklist-QR.pdf...")
    qr_image = extract_qr_code_from_pdf('Daily Paperwork/Pre-Demo-Checklist-QR.pdf')

    if qr_image is None:
        print("Failed to extract QR code")
        return

    print(f"QR code extracted: {qr_image.size}")

    print("\nStep 2: Modifying Activity Log with QR code...")
    output_path = 'Daily Paperwork/Event Table Activity Log - QR.pdf'
    modify_pdf_with_qr('Daily Paperwork/Event Table Activity Log.pdf', qr_image, output_path)

    print(f"\nSuccess! Modified Activity Log saved to: {output_path}")

if __name__ == '__main__':
    main()
