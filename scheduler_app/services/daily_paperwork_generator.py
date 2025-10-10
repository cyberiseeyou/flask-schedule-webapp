"""
Daily Paperwork Generator Service
===================================

This service generates comprehensive daily paperwork packages including:
- Daily Schedule (Core and Juicer events)
- Daily Item Numbers table
- Per-event documentation (EDR, SalesTool, Activity Log, Checklist)
"""

import os
import tempfile
import requests
from datetime import datetime, timedelta
from io import BytesIO
from typing import List, Dict, Optional, Any

# Import EDR components
from edr import EDRReportGenerator

try:
    from PyPDF2 import PdfMerger, PdfReader, PdfWriter
    from reportlab.lib.pagesizes import letter
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image as ReportLabImage
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER
    from xhtml2pdf import pisa
    import barcode
    from barcode.writer import ImageWriter
    from PIL import Image as PILImage
    PDF_LIBRARIES_AVAILABLE = True
except ImportError:
    PDF_LIBRARIES_AVAILABLE = False


class DailyPaperworkGenerator:
    """Generates consolidated daily paperwork packages"""

    def __init__(self, db_session, models_dict, session_api_service=None, edr_generator=None):
        """
        Initialize the generator

        Args:
            db_session: SQLAlchemy database session
            models_dict: Dictionary containing model classes (Event, Schedule, Employee)
            session_api_service: Optional SessionAPIService for authenticated downloads
            edr_generator: Optional authenticated EDRReportGenerator instance (from Flask session)
        """
        self.db = db_session
        self.models = models_dict
        self.session_api_service = session_api_service
        self.edr_generator = edr_generator  # Injected authenticated instance
        self.temp_files = []  # Track temp files for cleanup

    def initialize_edr_generator(self):
        """
        Initialize the EDR generator for authentication

        DEPRECATED: EDR generator should be passed via constructor from Flask session.
        This method is kept for backward compatibility only.
        """
        if not self.edr_generator:
            self.edr_generator = EDRReportGenerator()
        return self.edr_generator

    def request_mfa_code(self) -> bool:
        """
        Request MFA code for authentication

        DEPRECATED: Use the admin route /api/admin/edr/request-code instead.
        Authentication should be managed at the Flask session level.
        """
        if not self.edr_generator:
            self.initialize_edr_generator()
        return self.edr_generator.request_mfa_code()

    def complete_authentication(self, mfa_code: str) -> bool:
        """
        Complete authentication with MFA code

        DEPRECATED: Use the admin route /api/admin/edr/authenticate instead.
        Authentication should be managed at the Flask session level.
        """
        if not self.edr_generator:
            return False
        return self.edr_generator.complete_authentication_with_mfa_code(mfa_code)

    def generate_barcode_image(self, item_number: str) -> Optional[str]:
        """
        Generate a barcode image for an item number

        Args:
            item_number: Item number to generate barcode for

        Returns:
            Path to generated barcode image or None if failed
        """
        try:
            # Clean the item number (remove any non-digits)
            clean_number = ''.join(filter(str.isdigit, str(item_number)))

            if not clean_number:
                return None

            # Pad to 12 digits for UPC-A if needed (standard retail UPC)
            if len(clean_number) < 12:
                clean_number = clean_number.zfill(12)
            elif len(clean_number) > 12:
                # For numbers longer than 12 digits, use Code128 which is more flexible
                barcode_class = barcode.get_barcode_class('code128')
            else:
                # Use UPC-A for 12-digit numbers
                try:
                    barcode_class = barcode.get_barcode_class('upca')
                except:
                    # Fallback to Code128 if UPC-A fails
                    barcode_class = barcode.get_barcode_class('code128')

            # For UPC-A, we need exactly 11 digits (12th is check digit)
            if len(clean_number) == 12:
                try:
                    barcode_class = barcode.get_barcode_class('upca')
                    # UPC-A needs 11 digits, check digit is auto-calculated
                    clean_number = clean_number[:11]
                except:
                    barcode_class = barcode.get_barcode_class('code128')
                    clean_number = item_number  # Use original for Code128
            else:
                barcode_class = barcode.get_barcode_class('code128')
                clean_number = str(item_number)

            # Generate barcode image
            output_path = os.path.join(tempfile.gettempdir(), f'barcode_{item_number}_{datetime.now().strftime("%Y%m%d%H%M%S%f")}.png')

            # Create barcode with custom options for smaller size
            barcode_instance = barcode_class(clean_number, writer=ImageWriter())

            # Save with custom options for better PDF integration
            options = {
                'module_width': 0.2,  # Width of bars
                'module_height': 8.0,  # Height of bars in mm
                'quiet_zone': 2.0,    # Quiet zone in mm
                'font_size': 8,       # Font size for text
                'text_distance': 2.0, # Distance between bars and text
                'write_text': True,   # Show the number below barcode
            }

            barcode_instance.save(output_path.replace('.png', ''), options=options)

            # The library adds .png automatically
            final_path = output_path.replace('.png', '') + '.png'

            if os.path.exists(final_path):
                self.temp_files.append(final_path)
                return final_path

            return None

        except Exception as e:
            print(f"⚠️ Failed to generate barcode for {item_number}: {e}")
            return None

    def get_events_for_date(self, target_date: datetime.date) -> List[Any]:
        """Get all scheduled Core events for a specific date"""
        Event = self.models['Event']
        Schedule = self.models['Schedule']
        Employee = self.models['Employee']

        # Query scheduled Core events for the date
        schedules = self.db.query(
            Schedule, Event, Employee
        ).join(
            Event, Schedule.event_ref_num == Event.project_ref_num
        ).join(
            Employee, Schedule.employee_id == Employee.id
        ).filter(
            Schedule.schedule_datetime >= target_date,
            Schedule.schedule_datetime < target_date + timedelta(days=1),
            Event.event_type == 'Core'  # Only Core events
        ).order_by(
            Schedule.schedule_datetime
        ).all()

        return schedules

    def generate_daily_schedule_pdf(self, target_date: datetime.date, schedules: List) -> str:
        """
        Generate the daily schedule PDF (same format as Print Today's Schedule)

        Returns:
            Path to generated PDF file
        """
        if not PDF_LIBRARIES_AVAILABLE:
            raise ImportError("PDF libraries required. Install: pip install reportlab xhtml2pdf PyPDF2")

        # Filter for Core and Juicer Production events
        filtered_schedules = []
        for schedule, event, employee in schedules:
            if event.event_type == 'Core' or \
               (event.event_type == 'Juicer' and 'Production' in event.project_name and
                'survey' not in event.project_name.lower()):
                filtered_schedules.append((schedule, event, employee))

        # Sort by time
        filtered_schedules.sort(key=lambda x: x[0].schedule_datetime)

        # Generate HTML
        date_str = target_date.strftime('%A, %B %d, %Y')

        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Core Events Schedule - {date_str}</title>
            <style>
                @page {{ size: letter; margin: 0.5in; }}
                body {{
                    font-family: Arial, sans-serif;
                    margin: 0;
                    background: white;
                }}
                .header {{
                    text-align: center;
                    margin-bottom: 30px;
                    border-bottom: 3px solid #2E4C73;
                    padding-bottom: 20px;
                }}
                .date-title {{
                    font-size: 24px;
                    font-weight: bold;
                    color: #2E4C73;
                    margin: 0;
                }}
                .subtitle {{
                    font-size: 16px;
                    color: #666;
                    margin: 5px 0 0 0;
                }}
                .schedule-table {{
                    width: 100%;
                    border-collapse: collapse;
                    margin-top: 20px;
                }}
                .schedule-table th {{
                    background: #2E4C73;
                    color: white;
                    padding: 12px;
                    text-align: left;
                    font-weight: bold;
                    font-size: 14px;
                    border: 1px solid #ddd;
                }}
                .schedule-table td {{
                    padding: 10px 12px;
                    border: 1px solid #ddd;
                    font-size: 13px;
                }}
                .schedule-table tr:nth-child(even) {{
                    background-color: #f9f9f9;
                }}
                .employee-name {{
                    font-weight: bold;
                    color: #2E4C73;
                }}
            </style>
        </head>
        <body>
            <div class="header">
                <p class="date-title">{date_str}</p>
                <p class="subtitle">CORE Events Schedule</p>
            </div>
            <table class="schedule-table">
                <thead>
                    <tr>
                        <th style="width: 15%;">Time</th>
                        <th style="width: 35%;">Employee</th>
                        <th style="width: 50%;">Event</th>
                    </tr>
                </thead>
                <tbody>
        """

        for schedule, event, employee in filtered_schedules:
            time_str = schedule.schedule_datetime.strftime('%I:%M %p')
            html += f"""
                    <tr>
                        <td>{time_str}</td>
                        <td class="employee-name">{employee.name}</td>
                        <td>{event.project_name}</td>
                    </tr>
            """

        html += """
                </tbody>
            </table>
        </body>
        </html>
        """

        # Generate PDF
        output_path = os.path.join(tempfile.gettempdir(), f'daily_schedule_{target_date.strftime("%Y%m%d")}.pdf')
        with open(output_path, 'wb') as pdf_file:
            pisa_status = pisa.CreatePDF(BytesIO(html.encode('utf-8')), dest=pdf_file)

        if pisa_status.err:
            raise Exception("Failed to generate daily schedule PDF")

        self.temp_files.append(output_path)
        return output_path

    def generate_item_numbers_pdf(self, edr_data_list: List, target_date: datetime.date) -> str:
        """
        Generate Daily Item Numbers table PDF from EDR data

        Args:
            edr_data_list: List of EDR data dictionaries
            target_date: Date for display

        Returns:
            Path to generated PDF file
        """
        if not PDF_LIBRARIES_AVAILABLE:
            raise ImportError("PDF libraries required")

        # Collect all unique items from EDR data (maintain order, no sorting)
        items_list = []  # Use list to maintain order
        seen_items = set()  # Track duplicates

        for edr_data in edr_data_list:
            if not edr_data:
                continue

            item_details = edr_data.get('itemDetails', [])
            if item_details is None:
                continue

            for item in item_details:
                item_nbr = str(item.get('itemNbr', ''))
                upc_nbr = str(item.get('gtin', ''))  # UPC number (gtin field) for barcode generation
                item_desc = str(item.get('itemDesc', ''))

                if item_nbr and item_nbr != 'N/A' and item_nbr not in seen_items:
                    # Use gtin (UPC) if available, otherwise fall back to itemNbr
                    barcode_number = upc_nbr if upc_nbr and upc_nbr not in ['', 'N/A', 'None'] else item_nbr

                    # Debug logging for first few items
                    if len(items_list) < 3:
                        print(f"DEBUG: Item {item_nbr}: upcNbr='{upc_nbr}', using '{barcode_number}' for barcode")

                    items_list.append((item_nbr, barcode_number, item_desc))
                    seen_items.add(item_nbr)

        # Create PDF
        output_path = os.path.join(tempfile.gettempdir(), f'daily_item_numbers_{datetime.now().strftime("%Y%m%d%H%M%S")}.pdf')
        doc = SimpleDocTemplate(output_path, pagesize=letter, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=72)

        styles = getSampleStyleSheet()
        story = []

        # Title
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            spaceAfter=12,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold',
            textColor=colors.HexColor('#2E4C73')
        )
        story.append(Paragraph("Daily Item Numbers", title_style))
        story.append(Spacer(1, 12))

        # Date
        date_str = target_date.strftime('%A, %B %d, %Y')
        date_style = ParagraphStyle(
            'DateStyle',
            parent=styles['Normal'],
            fontSize=14,
            alignment=TA_CENTER,
            textColor=colors.HexColor('#666666')
        )
        story.append(Paragraph(date_str, date_style))
        story.append(Spacer(1, 12))

        # Help text
        help_text = "Use this list for getting the next day's product and printing price signs."
        help_style = ParagraphStyle(
            'HelpStyle',
            parent=styles['Normal'],
            fontSize=11,
            alignment=TA_CENTER,
            textColor=colors.HexColor('#666666')
        )
        story.append(Paragraph(help_text, help_style))
        story.append(Spacer(1, 20))

        # Table
        if items_list:
            # Generate barcodes for each item
            table_data = [['UPC Number', 'Barcode', 'Description']]

            # Maintain the order items appear in the events (no sorting)
            for item_num, barcode_num, desc in items_list:
                # Generate barcode image based on the UPC number
                barcode_path = self.generate_barcode_image(barcode_num)

                if barcode_path:
                    # Create ReportLab Image object for the barcode
                    # Scale to fit nicely in the table (1.2 inches wide, 0.5 inches tall)
                    barcode_img = ReportLabImage(barcode_path, width=1.2*inch, height=0.5*inch)
                    # Display UPC number in first column, barcode in second column
                    table_data.append([str(barcode_num), barcode_img, str(desc)])
                else:
                    # If barcode generation fails, just show the UPC number
                    table_data.append([str(barcode_num), 'N/A', str(desc)])

            item_table = Table(table_data, colWidths=[1.2*inch, 1.5*inch, 3.8*inch])
            item_table.setStyle(TableStyle([
                # Header row - match the daily schedule theme
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2E4C73')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                # Data rows
                ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 10),
                # Alternating row colors
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F9F9F9')]),
                # Borders and alignment
                ('ALIGN', (0, 0), (0, -1), 'LEFT'),    # Item Number column - left align
                ('ALIGN', (1, 0), (1, -1), 'CENTER'),  # Barcode column - center align
                ('ALIGN', (2, 0), (2, -1), 'LEFT'),    # Description column - left align
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#DDDDDD')),
                # Padding - extra for barcode rows
                ('TOPPADDING', (0, 0), (-1, 0), 10),    # Header
                ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
                ('TOPPADDING', (0, 1), (-1, -1), 8),    # Data rows - tighter for barcodes
                ('BOTTOMPADDING', (0, 1), (-1, -1), 8),
                ('LEFTPADDING', (0, 0), (-1, -1), 8),
                ('RIGHTPADDING', (0, 0), (-1, -1), 8),
            ]))
            story.append(item_table)

            # Add summary
            story.append(Spacer(1, 20))
            summary_style = ParagraphStyle(
                'SummaryStyle',
                parent=styles['Normal'],
                fontSize=12,
                textColor=colors.HexColor('#2E4C73'),
                fontName='Helvetica-Bold'
            )
            summary_text = f"Total Items: {len(items_list)}"
            story.append(Paragraph(summary_text, summary_style))
        else:
            story.append(Paragraph("No items found for today's events.", styles['Normal']))

        doc.build(story)
        self.temp_files.append(output_path)
        return output_path

    def get_event_edr_pdf(self, event_mplan_id: str, employee_name: str) -> Optional[str]:
        """
        Get EDR PDF for an event (fetches EDR data first)

        Returns:
            Path to EDR PDF file or None if failed
        """
        if not self.edr_generator or not self.edr_generator.auth_token:
            print("❌ Not authenticated for EDR retrieval")
            return None

        try:
            # Import EDRPDFGenerator
            from edr import EDRPDFGenerator

            # Get EDR data
            edr_data = self.edr_generator.get_edr_report(event_mplan_id)
            if not edr_data:
                print(f"⚠️ No EDR data for event {event_mplan_id}")
                return None

            # Use EDRPDFGenerator instead of xhtml2pdf (which has CSS compatibility issues)
            output_path = os.path.join(tempfile.gettempdir(), f'edr_{event_mplan_id}_{datetime.now().strftime("%Y%m%d%H%M%S")}.pdf')

            pdf_generator = EDRPDFGenerator()
            if pdf_generator.generate_pdf(edr_data, output_path, employee_name):
                self.temp_files.append(output_path)
                print(f"   ✅ EDR PDF generated for event {event_mplan_id}")
                return output_path
            else:
                print(f"❌ Failed to generate EDR PDF for {event_mplan_id}")
                return None

        except Exception as e:
            print(f"❌ Error getting EDR for {event_mplan_id}: {e}")
            import traceback
            traceback.print_exc()
            return None

    def get_event_edr_pdf_from_data(self, edr_data: Dict, event_mplan_id: str, employee_name: str) -> Optional[str]:
        """
        Generate EDR PDF from already-fetched EDR data (for efficiency in batch operations)

        Args:
            edr_data: Pre-fetched EDR data dictionary
            event_mplan_id: Event mPlan ID for filename
            employee_name: Employee name to include in PDF

        Returns:
            Path to EDR PDF file or None if failed
        """
        try:
            # Import EDRPDFGenerator
            from edr import EDRPDFGenerator

            if not edr_data:
                print(f"⚠️ No EDR data provided for event {event_mplan_id}")
                return None

            # Use EDRPDFGenerator to create PDF
            output_path = os.path.join(tempfile.gettempdir(), f'edr_{event_mplan_id}_{datetime.now().strftime("%Y%m%d%H%M%S")}.pdf')

            pdf_generator = EDRPDFGenerator()
            if pdf_generator.generate_pdf(edr_data, output_path, employee_name):
                self.temp_files.append(output_path)
                return output_path
            else:
                print(f"❌ Failed to generate EDR PDF for {event_mplan_id}")
                return None

        except Exception as e:
            print(f"❌ Error generating EDR PDF for {event_mplan_id}: {e}")
            import traceback
            traceback.print_exc()
            return None

    def get_salestool_pdf(self, salestool_url: str, event_ref: str) -> Optional[str]:
        """
        Download SalesTool PDF from URL using authenticated session if available

        Returns:
            Path to downloaded PDF or None if failed
        """
        if not salestool_url:
            return None

        try:
            # Use authenticated session if available (for Crossmark URLs)
            if self.session_api_service and hasattr(self.session_api_service, 'session'):
                print(f"📥 Downloading SalesTool with authenticated session: {salestool_url}")
                response = self.session_api_service.session.get(salestool_url, timeout=30)
            else:
                print(f"📥 Downloading SalesTool (no auth): {salestool_url}")
                response = requests.get(salestool_url, timeout=30)

            response.raise_for_status()

            # Check if response is actually a PDF
            content_type = response.headers.get('Content-Type', '')
            if 'pdf' not in content_type.lower() and 'application/octet-stream' not in content_type.lower():
                print(f"⚠️ URL {salestool_url} did not return PDF (Content-Type: {content_type})")
                print(f"   Response size: {len(response.content)} bytes")
                if len(response.content) < 10000:  # Likely an error page
                    print(f"   Response preview: {response.text[:500]}")
                return None

            # Verify content is actually PDF by checking magic bytes
            if len(response.content) > 4:
                pdf_magic = response.content[:4]
                if pdf_magic != b'%PDF':
                    print(f"⚠️ Response does not start with PDF magic bytes: {pdf_magic}")
                    return None

            output_path = os.path.join(tempfile.gettempdir(), f'salestool_{event_ref}_{datetime.now().strftime("%Y%m%d%H%M%S")}.pdf')
            with open(output_path, 'wb') as f:
                f.write(response.content)

            file_size = len(response.content)
            print(f"✅ Downloaded SalesTool PDF ({file_size:,} bytes)")

            self.temp_files.append(output_path)
            return output_path

        except Exception as e:
            print(f"⚠️ Failed to download SalesTool from {salestool_url}: {e}")
            import traceback
            traceback.print_exc()
            return None

    def merge_pdfs(self, pdf_paths: List[str], output_path: str) -> bool:
        """
        Merge multiple PDFs into one

        Returns:
            True if successful
        """
        if not PDF_LIBRARIES_AVAILABLE:
            return False

        try:
            merger = PdfMerger()

            for pdf_path in pdf_paths:
                if pdf_path and os.path.exists(pdf_path):
                    merger.append(pdf_path)

            merger.write(output_path)
            merger.close()
            return True

        except Exception as e:
            print(f"❌ Failed to merge PDFs: {e}")
            return False

    def generate_complete_daily_paperwork(self, target_date: datetime.date) -> Optional[str]:
        """
        Generate complete daily paperwork package

        Returns:
            Path to final consolidated PDF
        """
        print(f"📋 Generating daily paperwork for {target_date.strftime('%Y-%m-%d')}...")

        # Get events for the date
        schedules = self.get_events_for_date(target_date)
        if not schedules:
            print("⚠️ No events found for this date")
            return None

        print(f"📊 Found {len(schedules)} scheduled events")

        # List to hold all PDF paths in order
        all_pdfs = []

        # 1. Generate Daily Schedule
        print("📄 Generating daily schedule...")
        schedule_pdf = self.generate_daily_schedule_pdf(target_date, schedules)
        all_pdfs.append(schedule_pdf)

        # 2. Fetch all EDR data - cache first, auto-sync if needed
        print("📄 Fetching EDR data (cache-first with auto-sync)...")
        edr_data_cache = {}  # Cache: event_number -> edr_data
        edr_data_list = []
        needs_sync = False

        if self.edr_generator:
            from utils.event_helpers import extract_event_number

            # First pass: Check which events are missing from cache
            missing_events = []
            for schedule, event, employee in schedules:
                if event.event_type == 'Core':
                    event_num = extract_event_number(event.project_name)
                    if event_num:
                        print(f"   Checking cache for event {event_num}...")
                        cached_items = self.edr_generator.get_event_from_cache(int(event_num))
                        if cached_items:
                            # Convert to EDR format for compatibility
                            edr_data = self.edr_generator.convert_cached_items_to_edr_format(cached_items)
                            edr_data_cache[event_num] = edr_data
                            edr_data_list.append(edr_data)
                            print(f"   ✅ Event {event_num} found in cache")
                        else:
                            missing_events.append(event_num)
                            print(f"   ⚠️ Event {event_num} not in cache")
                            needs_sync = True

            # Second pass: If any events are missing, sync the cache
            if needs_sync:
                print(f"⚠️ {len(missing_events)} events not in cache - triggering sync...")

                # Check if we need to authenticate
                if not self.edr_generator.auth_token:
                    print("❌ Not authenticated - cannot sync cache")
                    print("💡 Please authenticate via the printing interface first")
                else:
                    # Sync cache by calling browse_events (stores to database automatically)
                    print("📥 Syncing cache from Walmart API...")
                    events_data = self.edr_generator.browse_events()

                    if events_data:
                        print(f"✅ Cache sync complete - fetched {len(events_data)} event items")

                        # Now retry fetching the missing events from cache
                        for event_num in missing_events:
                            cached_items = self.edr_generator.get_event_from_cache(int(event_num))
                            if cached_items:
                                edr_data = self.edr_generator.convert_cached_items_to_edr_format(cached_items)
                                edr_data_cache[event_num] = edr_data
                                edr_data_list.append(edr_data)
                                print(f"   ✅ Event {event_num} now available after sync")
                            else:
                                print(f"   ⚠️ Event {event_num} still not in cache (may be outside date range)")
                    else:
                        print("❌ Cache sync failed - no data returned from API")

        # 3. Generate Daily Item Numbers from EDR data
        print("📄 Generating daily item numbers...")
        items_pdf = self.generate_item_numbers_pdf(edr_data_list, target_date)
        all_pdfs.append(items_pdf)

        # 4. For each event, generate EDR, SalesTool, Activity Log, Checklist
        docs_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'docs')
        activity_log_path = os.path.join(docs_dir, 'Event Table Activity Log.pdf')
        checklist_path = os.path.join(docs_dir, 'Daily Task Checkoff Sheet.pdf')

        for schedule, event, employee in schedules:
            print(f"📋 Processing event {event.project_ref_num} for {employee.name}...")

            # Only process documents for Core events
            if event.event_type == 'Core':
                from utils.event_helpers import extract_event_number
                event_num = extract_event_number(event.project_name)

                # Get EDR PDF if we have cached data
                if event_num and event_num in edr_data_cache:
                    print(f"   Generating EDR PDF for event {event_num}...")
                    edr_pdf = self.get_event_edr_pdf_from_data(edr_data_cache[event_num], event_num, employee.name)
                    if edr_pdf:
                        all_pdfs.append(edr_pdf)
                        print(f"   ✅ EDR PDF added for event {event_num}")

                # Get SalesTool if URL available
                if hasattr(event, 'sales_tools_url') and event.sales_tools_url:
                    print(f"   Downloading SalesTool for Core event...")
                    salestool_pdf = self.get_salestool_pdf(event.sales_tools_url, event.project_ref_num)
                    if salestool_pdf:
                        all_pdfs.append(salestool_pdf)
                        print(f"   ✅ SalesTool added")

                # Add Activity Log for Core events
                if os.path.exists(activity_log_path):
                    all_pdfs.append(activity_log_path)

                # Add Checklist for Core events
                if os.path.exists(checklist_path):
                    all_pdfs.append(checklist_path)
            else:
                print(f"   ℹ️ Skipping documents - event type is '{event.event_type}' (Core events only)")

        # Merge all PDFs
        output_filename = f'Paperwork_{target_date.strftime("%Y%m%d")}.pdf'
        output_path = os.path.join(tempfile.gettempdir(), output_filename)

        print(f"📄 Merging {len(all_pdfs)} PDFs into final document...")
        if self.merge_pdfs(all_pdfs, output_path):
            print(f"✅ Daily paperwork generated: {output_path}")
            return output_path
        else:
            print("❌ Failed to merge PDFs")
            return None

    def cleanup(self):
        """Clean up temporary files"""
        for temp_file in self.temp_files:
            try:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
            except:
                pass
        self.temp_files = []
