"""
EDR PDF Generation Module
Generates PDF files from EDR report data using ReportLab
"""
import logging
from typing import Dict, Any
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER


class EDRPDFGenerator:
    """Generates PDF files from EDR report data"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

        # Event type code mappings
        self.event_type_codes = {
            '44': 'Event Type 44',
            '45': 'Food Demo/Sampling',
            '46': 'Beverage Demo',
            '47': 'Product Demonstration',
            '48': 'Special Event',
            '49': 'Promotional Event',
            '50': 'Tasting Event',
        }

        # Event status code mappings
        self.event_status_codes = {
            '1': 'Pending',
            '2': 'Active/Scheduled',
            '3': 'In Progress',
            '4': 'Completed',
            '5': 'Cancelled',
        }

    def get_event_type_description(self, code: str) -> str:
        """Convert event type code to human readable description"""
        if not code or code == 'N/A':
            return 'N/A'
        return self.event_type_codes.get(str(code), f"Event Type {code}")

    def get_event_status_description(self, code: str) -> str:
        """Convert event status code to human readable description"""
        if not code or code == 'N/A':
            return 'N/A'
        return self.event_status_codes.get(str(code), f"Status {code}")

    def generate_pdf(self, edr_data: Dict[str, Any], filename: str, employee_name: str = 'N/A') -> bool:
        """Generate a PDF file from EDR data"""
        try:
            doc = SimpleDocTemplate(filename, pagesize=letter, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=18)
            story = []
            styles = getSampleStyleSheet()

            title_style = ParagraphStyle('CustomTitle', parent=styles['Heading1'], fontSize=18, spaceAfter=30, alignment=TA_CENTER, fontName='Helvetica-Bold')
            header_style = ParagraphStyle('CustomHeader', parent=styles['Heading2'], fontSize=14, spaceAfter=12, alignment=TA_CENTER, fontName='Helvetica-Bold')

            # Extract event data
            event_number = edr_data.get('demoId', 'N/A')
            event_type_code = edr_data.get('demoClassCode', 'N/A')
            event_status_code = edr_data.get('demoStatusCode', 'N/A')
            event_date = edr_data.get('demoDate', 'N/A')
            event_name = edr_data.get('demoName', 'N/A')
            event_locked = edr_data.get('demoLockInd', 'N/A')

            event_type = self.get_event_type_description(event_type_code)
            event_status = self.get_event_status_description(event_status_code)

            item_details = edr_data.get('itemDetails', [])

            # Title
            story.append(Paragraph("EVENT DETAIL REPORT", title_style))
            story.append(Spacer(1, 12))

            # Event details table 1
            event_details_row1 = [
                ['Event Number', 'Event Type', 'Event Locked'],
                [str(event_number), str(event_type), str(event_locked)]
            ]

            # Event details table 2
            event_details_row2 = [
                ['Event Status', 'Event Date', 'Event Name'],
                [str(event_status), str(event_date), str(event_name)]
            ]

            table1 = Table(event_details_row1, colWidths=[1.3*inch, 2*inch, 2.7*inch])
            table1.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ]))

            table2 = Table(event_details_row2, colWidths=[1.3*inch, 1.5*inch, 3.2*inch])
            table2.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ]))

            story.append(table1)
            story.append(Spacer(1, 3))
            story.append(table2)
            story.append(Spacer(1, 20))

            # Items table
            if item_details:
                items_data = [['Item Number', 'Primary Item Number', 'Description', 'Vendor', 'Category']]
                for item in item_details:
                    items_data.append([
                        str(item.get('itemNbr', '')),
                        str(item.get('gtin', '')),
                        str(item.get('itemDesc', '')),
                        str(item.get('vendorNbr', '')),
                        str(item.get('deptNbr', ''))
                    ])

                items_table = Table(items_data, colWidths=[1.2*inch, 1.2*inch, 2*inch, 1*inch, 1*inch])
                items_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                    ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, -1), 9),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
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

            # Build PDF document from all story elements
            # ReportLab processes the story list and creates the final PDF file
            doc.build(story)
            self.logger.info(f"PDF generated successfully: {filename}")
            return True

        except Exception as e:
            # Log any errors during PDF generation and return failure
            self.logger.error(f"Failed to generate PDF: {str(e)}")
            return False
