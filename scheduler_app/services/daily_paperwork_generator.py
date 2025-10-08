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
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER
    from xhtml2pdf import pisa
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
                        <th style="width: 40%;">Event</th>
                        <th style="width: 10%;">Type</th>
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
                        <td>{event.event_type}</td>
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
                item_desc = str(item.get('itemDesc', ''))

                if item_nbr and item_nbr != 'N/A' and item_nbr not in seen_items:
                    items_list.append((item_nbr, item_desc))
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
            fontSize=18,
            spaceAfter=12,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        )
        story.append(Paragraph("Daily Item Numbers", title_style))
        story.append(Spacer(1, 12))

        # Date
        date_str = target_date.strftime('%A, %B %d, %Y')
        story.append(Paragraph(f"<b>{date_str}</b>", styles['Normal']))
        story.append(Spacer(1, 12))

        # Help text
        help_text = "Use this list for getting the next day's product and printing price signs."
        story.append(Paragraph(help_text, styles['Normal']))
        story.append(Spacer(1, 20))

        # Table
        if items_list:
            table_data = [['Item Number', 'Description']]
            # Maintain the order items appear in the events (no sorting)
            for item_num, desc in items_list:
                table_data.append([str(item_num), str(desc)])

            item_table = Table(table_data, colWidths=[1.5*inch, 5*inch])
            item_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('TOPPADDING', (0, 0), (-1, -1), 8),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ]))
            story.append(item_table)

            # Add summary
            story.append(Spacer(1, 20))
            summary_text = f"<b>Total Items: {len(items_list)}</b>"
            story.append(Paragraph(summary_text, styles['Normal']))
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

        # 2. Fetch all EDR data first (we'll use this for both item list and individual EDRs)
        print("📄 Fetching EDR data for all events...")
        edr_data_cache = {}  # Cache: event_number -> edr_data
        edr_data_list = []

        if self.edr_generator:
            from utils.event_helpers import extract_event_number
            for schedule, event, employee in schedules:
                if event.event_type == 'Core':
                    event_num = extract_event_number(event.project_name)
                    if event_num:
                        print(f"   Fetching EDR for event {event_num}...")
                        edr_data = self.edr_generator.get_edr_report(event_num)
                        if edr_data:
                            edr_data_cache[event_num] = edr_data
                            edr_data_list.append(edr_data)
                            print(f"   ✅ EDR data retrieved for event {event_num}")
                        else:
                            print(f"   ⚠️ No EDR data for event {event_num}")

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
