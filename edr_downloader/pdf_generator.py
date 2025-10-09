"""
EDR PDF Generation Module
Generates PDF files from EDR report data using ReportLab
"""
import logging
import os
import sys
from typing import Dict, Any
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.platypus.flowables import Flowable

# Import mapping files
mappings_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'mappings')
if mappings_path not in sys.path:
    sys.path.insert(0, mappings_path)

try:
    from demo_class_codes import DEMO_CLASS_CODES
    from event_status_codes import EVENT_STATUS_CODES
    from department_codes import DEPARTMENT_CODES
except ImportError as e:
    print(f"Warning: Could not import mapping files: {e}")
    DEMO_CLASS_CODES = []
    EVENT_STATUS_CODES = []
    DEPARTMENT_CODES = []


class PriceSignBox(Flowable):
    """Custom flowable to draw a box with text at the bottom"""

    def __init__(self, width, height, text="Place Price Signs Here"):
        Flowable.__init__(self)
        self.width = width
        self.height = height
        self.text = text

    def draw(self):
        """Draw the box with centered text at bottom"""
        # Draw the rectangle border
        self.canv.setStrokeColor(colors.black)
        self.canv.setLineWidth(2)
        self.canv.rect(0, 0, self.width, self.height)

        # Draw the text at the bottom center
        self.canv.setFont('Helvetica-Bold', 14)
        text_width = self.canv.stringWidth(self.text, 'Helvetica-Bold', 14)
        x_pos = (self.width - text_width) / 2
        y_pos = 15  # 15 points from bottom
        self.canv.drawString(x_pos, y_pos, self.text)


class EDRPDFGenerator:
    """Generates PDF files from EDR report data"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

        # Product Connections colors
        self.pc_blue = colors.HexColor('#2E4C73')
        self.pc_light_blue = colors.HexColor('#1B9BD8')

        # Build event type code mappings from demo_class_codes.py
        self.event_type_codes = {}
        if isinstance(DEMO_CLASS_CODES, tuple) and len(DEMO_CLASS_CODES) > 0:
            for item in DEMO_CLASS_CODES[0]:
                code = str(item.get('DEMO_CLASS_CODE', ''))
                desc = item.get('DEMO_CLASS_DESC', '').strip()
                if code and desc:
                    self.event_type_codes[code] = desc

        # Build event status code mappings from event_status_codes.py
        self.event_status_codes = {}
        for item in EVENT_STATUS_CODES:
            code = str(item.get('DEMO_STATUS_CODE', ''))
            desc = item.get('DEMO_STATUS_DESC', '').strip()
            if code and desc:
                self.event_status_codes[code] = desc

        # Build department code mappings from department_codes.py
        self.department_codes = {}
        for item in DEPARTMENT_CODES:
            dept_no = str(item.get('DEPT_NO', ''))
            desc = item.get('DESCRIPTION', '').strip()
            if dept_no and desc:
                self.department_codes[dept_no] = desc

    def get_event_type_description(self, code: str) -> str:
        """Convert event type code to human readable description"""
        if not code or code == 'N/A':
            return 'N/A'
        return self.event_type_codes.get(str(code), f"Type {code}")

    def get_event_status_description(self, code: str) -> str:
        """Convert event status code to human readable description"""
        if not code or code == 'N/A':
            return 'N/A'
        return self.event_status_codes.get(str(code), f"Status {code}")

    def get_department_description(self, dept_no: str) -> str:
        """Convert department number to description"""
        if not dept_no or dept_no == 'N/A' or dept_no == '':
            return 'N/A'
        return self.department_codes.get(str(dept_no), f"Dept {dept_no}")

    def format_date(self, date_str: str) -> str:
        """Format date from YYYY-MM-DD to MM-DD-YYYY"""
        if not date_str or date_str == 'N/A':
            return 'N/A'
        try:
            # Parse the date string (assuming YYYY-MM-DD format from Walmart)
            date_obj = datetime.strptime(date_str, '%Y-%m-%d')
            return date_obj.strftime('%m-%d-%Y')
        except:
            return date_str  # Return as-is if parsing fails

    def generate_pdf(self, edr_data: Dict[str, Any], filename: str, employee_name: str = 'N/A') -> bool:
        """Generate a PDF file from EDR data"""
        try:
            doc = SimpleDocTemplate(filename, pagesize=letter, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=72)
            story = []
            styles = getSampleStyleSheet()

            title_style = ParagraphStyle('CustomTitle', parent=styles['Heading1'], fontSize=18, spaceAfter=30, alignment=TA_CENTER, fontName='Helvetica-Bold')
            header_style = ParagraphStyle('CustomHeader', parent=styles['Heading2'], fontSize=14, spaceAfter=12, alignment=TA_CENTER, fontName='Helvetica-Bold')

            # Extract event data
            event_number = edr_data.get('demoId', 'N/A')
            event_type_code = edr_data.get('demoClassCode', 'N/A')
            event_status_code = edr_data.get('demoStatusCode', 'N/A')
            event_date_raw = edr_data.get('demoDate', 'N/A')
            event_name = edr_data.get('demoName', 'N/A')
            event_locked = edr_data.get('demoLockInd', 'N/A')

            # Format the data
            event_type = self.get_event_type_description(event_type_code)
            event_status = self.get_event_status_description(event_status_code)
            event_date = self.format_date(event_date_raw)
            locked_display = 'YES' if str(event_locked).upper() in ['Y', 'YES', 'TRUE', '1'] else 'NO'

            item_details = edr_data.get('itemDetails', [])

            # Calculate available width for tables (letter width - margins)
            page_width = letter[0] - 144  # 72 left + 72 right margins

            # Title
            story.append(Paragraph("EVENT DETAIL REPORT", title_style))
            story.append(Spacer(1, 12))

            # Row 1: Event Number and Event Name
            row1_data = [
                ['Event Number', 'Event Name'],
                [str(event_number), str(event_name)]
            ]
            row1_table = Table(row1_data, colWidths=[page_width * 0.25, page_width * 0.75])
            row1_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), self.pc_blue),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('TEXTCOLOR', (0, 1), (-1, 1), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTNAME', (0, 1), (-1, 1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 11),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('TOPPADDING', (0, 0), (-1, -1), 8),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ]))

            # Row 2: Event Date, Event Type, Status, Locked (4 equal columns)
            row2_data = [
                ['Event Date', 'Event Type', 'Status', 'Locked'],
                [event_date, event_type, event_status, locked_display]
            ]
            col_width = page_width / 4
            row2_table = Table(row2_data, colWidths=[col_width, col_width, col_width, col_width])
            row2_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), self.pc_light_blue),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('TEXTCOLOR', (0, 1), (-1, 1), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTNAME', (0, 1), (-1, 1), 'Helvetica'),
                ('FONTNAME', (3, 1), (3, 1), 'Helvetica-Bold'),  # Bold for Locked value
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('TOPPADDING', (0, 0), (-1, -1), 8),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ]))

            story.append(row1_table)
            story.append(Spacer(1, 3))
            story.append(row2_table)
            story.append(Spacer(1, 20))

            # Items table with department description
            if item_details:
                items_data = [['Item Number', 'Primary Item Number', 'Description', 'Vendor', 'Category']]
                for item in item_details:
                    dept_no = str(item.get('deptNbr', ''))
                    category = self.get_department_description(dept_no)
                    items_data.append([
                        str(item.get('itemNbr', '')),
                        str(item.get('gtin', '')),
                        str(item.get('itemDesc', '')),
                        str(item.get('vendorNbr', '')),
                        category
                    ])

                items_table = Table(items_data, colWidths=[0.9*inch, 1.1*inch, 2.2*inch, 0.7*inch, 1.6*inch])
                items_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), self.pc_blue),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                    ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('ALIGN', (0, 0), (0, -1), 'CENTER'),  # Center item numbers
                    ('ALIGN', (1, 0), (1, -1), 'CENTER'),  # Center primary item numbers
                    ('ALIGN', (3, 0), (3, -1), 'CENTER'),  # Center vendor numbers
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                    ('FONTSIZE', (0, 0), (-1, -1), 8),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                    ('TOPPADDING', (0, 0), (-1, -1), 6),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ]))
                story.append(items_table)
                story.append(Spacer(1, 20))

            # Signature section - required for employee and supervisor sign-off
            story.append(Paragraph("<b>MUST BE SIGNED AND DATED</b>", header_style))
            story.append(Spacer(1, 20))

            # Create signature table with employee name and blank lines for signatures
            signature_data = [
                ['Scheduled Employee:', employee_name],  # Pre-filled with assigned employee
                ['Employee Signature:', '________________________________'],  # Blank line for signature
                ['Date Performed:', '________________________________'],  # Blank line for date
                ['Supervisor Signature:', '________________________________']  # Blank line for supervisor
            ]

            # Create table with appropriate column widths for labels and values
            signature_table = Table(signature_data, colWidths=[2.5*inch, 3.5*inch])
            signature_table.setStyle(TableStyle([
                ('FONTSIZE', (0, 0), (-1, -1), 10),  # 10pt font for all cells
                ('ALIGN', (0, 0), (0, -1), 'LEFT'),  # Left-align labels
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),  # Vertically center all content
                ('FONTNAME', (0, 0), (0, 0), 'Helvetica-Bold'),  # Bold for "Scheduled Employee:" label
            ]))
            story.append(signature_table)

            # Add space before the price sign box
            story.append(Spacer(1, 30))

            # Add "Place Price Signs Here" box
            # Calculate box height to be about 1/3 of remaining page
            # Letter page is 11 inches, with 72pt top and 72pt bottom margin = 9 inches usable
            # We want a box that's about 2.5 inches tall
            box_height = 2.5 * inch
            story.append(PriceSignBox(page_width, box_height))

            # Build PDF document from all story elements
            # ReportLab processes the story list and creates the final PDF file
            doc.build(story)
            self.logger.info(f"PDF generated successfully: {filename}")
            return True

        except Exception as e:
            # Log any errors during PDF generation and return failure
            self.logger.error(f"Failed to generate PDF: {str(e)}")
            return False
