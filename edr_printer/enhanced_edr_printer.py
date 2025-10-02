"""
Enhanced EDR Printer with PDF Consolidation
==========================================

This module creates a consolidated PDF from multiple EDR reports and provides
better printing options since direct HTML printing has been unreliable.
"""

from .edr_report_generator import EDRReportGenerator
from .automated_edr_printer import AutomatedEDRPrinter
import sys
import datetime
import os
import tempfile
import subprocess
import platform
from typing import List, Optional, Dict, Any

try:
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER, TA_LEFT
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

try:
    from weasyprint import HTML, CSS
    WEASYPRINT_AVAILABLE = True
except ImportError:
    WEASYPRINT_AVAILABLE = False


class EnhancedEDRPrinter(AutomatedEDRPrinter):
    """
    Enhanced EDR printer that creates consolidated PDF files from multiple reports.
    """
    
    def __init__(self):
        super().__init__()
        self.pdf_reports = []  # Store generated reports for PDF consolidation
        
        # Event type code mappings (numeric codes from API)
        self.event_type_codes = {
            '1': 'Sampling',
            '2': 'Demo/Sampling', 
            '3': 'Cooking Demo',
            '4': 'Product Demo',
            '5': 'Educational',
            '6': 'Seasonal',
            '7': 'Holiday',
            '8': 'Back to School',
            '9': 'Health & Wellness',
            '10': 'New Product Launch',
            '45': 'Food Demo/Sampling',  # Common code we see in data
            '46': 'Beverage Demo',
            '47': 'Product Demonstration',
            '48': 'Special Event',
            '49': 'Promotional Event',
            '50': 'Tasting Event',
            # Add more as discovered
            'DEMO': 'Demonstration',
            'SAMP': 'Sampling',
            'COOK': 'Cooking Demo',
            'SPEC': 'Special Event',
            'PROM': 'Promotion',
            'DISP': 'Display',
            'TAST': 'Tasting',
            'EDUC': 'Educational',
            'SEAS': 'Seasonal',
            'NEW': 'New Product',
            'HOLI': 'Holiday',
            'BACK': 'Back to School',
            'GRIL': 'Grilling',
            'HEAL': 'Health & Wellness'
        }
        
        # Event status code mappings (numeric codes from API)
        self.event_status_codes = {
            '1': 'Pending',
            '2': 'Active/Scheduled',  # Common code we see in data
            '3': 'In Progress', 
            '4': 'Completed',
            '5': 'Cancelled',
            '6': 'On Hold',
            '7': 'Under Review',
            '8': 'Approved',
            '9': 'Rejected',
            '10': 'Suspended',
            # Add more as discovered
            'ACTV': 'Active',
            'COMP': 'Completed',
            'CANC': 'Cancelled',
            'PEND': 'Pending',
            'HOLD': 'On Hold',
            'PREP': 'In Preparation',
            'SCHED': 'Scheduled',
            'INPR': 'In Progress',
            'SUSP': 'Suspended',
            'CLOS': 'Closed',
            'APPR': 'Approved',
            'REJE': 'Rejected',
            'SUBM': 'Submitted',
            'REVI': 'Under Review'
        }
    
    def get_event_type_description(self, code: str) -> str:
        """Convert event type code to human readable description."""
        if not code or code == 'N/A':
            return 'N/A'
        code_str = str(code).upper()
        description = self.event_type_codes.get(code_str, None)
        if description:
            return description
        # If no mapping found, return a descriptive fallback
        return f"Event Type {code}"
    
    def get_event_status_description(self, code: str) -> str:
        """Convert event status code to human readable description.""" 
        if not code or code == 'N/A':
            return 'N/A'
        code_str = str(code).upper()
        description = self.event_status_codes.get(code_str, None)
        if description:
            return description
        # If no mapping found, return a descriptive fallback
        return f"Status {code}"
        
    def generate_consolidated_pdf_reportlab(self, event_data_list: List[Dict[str, Any]], filename: Optional[str] = None) -> str:
        """
        Generate a consolidated PDF using ReportLab from multiple EDR data sets.
        
        Args:
            event_data_list: List of dictionaries containing event data
            filename: Optional PDF filename
            
        Returns:
            Path to generated PDF file
        """
        if not REPORTLAB_AVAILABLE:
            raise ImportError("ReportLab is required for PDF generation. Install with: pip install reportlab")
        
        if not filename:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"consolidated_edr_reports_{timestamp}.pdf"
        
        # Create PDF document
        doc = SimpleDocTemplate(filename, pagesize=letter, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=18)
        story = []
        styles = getSampleStyleSheet()
        
        # Custom styles
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=18,
            spaceAfter=30,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        )
        
        header_style = ParagraphStyle(
            'CustomHeader',
            parent=styles['Heading2'],
            fontSize=14,
            spaceAfter=12,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        )
        
        normal_style = styles['Normal']
        normal_style.fontSize = 10
        
        # Generate timestamp
        now = datetime.datetime.now()
        report_date = now.strftime("%Y-%m-%d")
        report_time = now.strftime("%H:%M:%S")
        
        print(f"📄 Generating consolidated PDF with {len(event_data_list)} reports...")
        
        # Create cover page
        cover_title_style = ParagraphStyle(
            'CoverTitle',
            parent=styles['Heading1'],
            fontSize=24,
            spaceAfter=50,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        )
        
        # Cover page content
        story.append(Paragraph("CONSOLIDATED EVENT DETAILS REPORT", cover_title_style))
        story.append(Spacer(1, 50))
        story.append(Paragraph(f"Generated on {report_date} at {report_time}", header_style))
        story.append(Spacer(1, 30))
        story.append(Paragraph(f"Total Events: {len(event_data_list)}", header_style))
        story.append(Spacer(1, 30))
        
        # Event summary table on cover page
        if event_data_list:
            summary_data = [['Event ID', 'Event Name', 'Event Type', 'Status']]
            for event_data in event_data_list:
                event_number = event_data.get('demoId', 'N/A') if event_data else 'N/A'
                event_name = event_data.get('demoName', 'N/A') if event_data else 'N/A'
                event_type_code = event_data.get('demoClassCode', 'N/A') if event_data else 'N/A'
                event_status_code = event_data.get('demoStatusCode', 'N/A') if event_data else 'N/A'
                
                # Convert codes to descriptions
                event_type_desc = self.get_event_type_description(event_type_code)
                event_status_desc = self.get_event_status_description(event_status_code)
                
                # Truncate long names for table
                event_name_short = str(event_name)[:30] + '...' if len(str(event_name)) > 30 else str(event_name)
                
                summary_data.append([
                    str(event_number),
                    event_name_short,
                    event_type_desc,
                    event_status_desc
                ])
            
            summary_table = Table(summary_data, colWidths=[1.2*inch, 2.3*inch, 1.5*inch, 1.5*inch])
            summary_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ]))
            story.append(summary_table)
        
        # Add page break after cover page
        story.append(PageBreak())
        
        for i, event_data in enumerate(event_data_list):
            if i > 0:
                story.append(PageBreak())  # New page for each report after the cover page
            
            # Extract event information
            event_number = event_data.get('demoId', 'N/A') if event_data else 'N/A'
            event_type_code = event_data.get('demoClassCode', 'N/A') if event_data else 'N/A'
            event_status_code = event_data.get('demoStatusCode', 'N/A') if event_data else 'N/A'
            event_date = event_data.get('demoDate', 'N/A') if event_data else 'N/A'
            event_name = event_data.get('demoName', 'N/A') if event_data else 'N/A'
            event_locked = event_data.get('demoLockInd', 'N/A') if event_data else 'N/A'
            
            # Convert codes to readable descriptions
            event_type = self.get_event_type_description(event_type_code)
            event_status = self.get_event_status_description(event_status_code)
            
            # Instructions
            instructions = event_data.get('demoInstructions', {}) if event_data else {}
            event_prep = instructions.get('demoPrepnTxt', 'N/A') if instructions else 'N/A'
            event_portion = instructions.get('demoPortnTxt', 'N/A') if instructions else 'N/A'
            
            # Item details
            item_details = event_data.get('itemDetails', []) if event_data else []
            
            # Title - exactly like HTML
            story.append(Paragraph("EVENT DETAIL REPORT", title_style))
            story.append(Spacer(1, 12))
            
            # Important notice - exactly like HTML
            important_text = """
            <b>IMPORTANT!!!</b> This report should be printed each morning prior to completing each event.<br/>
            1. The Event Details Report should be kept in the event prep area for each demonstrator to review instructions and item status.<br/>
            2. The Event Co-ordinator should use this sheet when visiting the event area. Comments should be written to enter into the system at a later time.<br/>
            3. Remember to scan items for product charge using the Club Use function on the handheld device.<br/>
            Retention: This report should be kept in a monthly folder with the most recent being put in the front. The previous 6 months need to be kept accessible in the event prep area. Reports older than 6 months should be boxed and stored. Discard any report over 18 months old.
            """
            story.append(Paragraph(important_text, normal_style))
            story.append(Spacer(1, 20))
            
            # Event details section - replicate HTML structure exactly
            # First row: Event Number, Event Type, Event Locked
            event_details_row1 = [
                ['Event Number', 'Event Type', 'Event Locked'],
                [str(event_number), str(event_type), str(event_locked)]
            ]
            
            # Second row: Event Status, Event Date, Event Name  
            event_details_row2 = [
                ['Event Status', 'Event Date', 'Event Name'],
                [str(event_status), str(event_date), str(event_name)]
            ]
            
            # Create tables to match HTML structure with adjusted column widths
            table1 = Table(event_details_row1, colWidths=[1.3*inch, 2*inch, 2.7*inch])
            table1.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('TOPPADDING', (0, 0), (-1, -1), 5),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
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
                ('TOPPADDING', (0, 0), (-1, -1), 5),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
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
            
            
            # MUST BE SIGNED AND DATED - centered, bold, all caps
            story.append(Paragraph("<b>MUST BE SIGNED AND DATED</b>", header_style))
            story.append(Spacer(1, 20))
            
            # Signature lines with updated field names
            signature_data = [
                ['Event Specialist Printed Name:', '________________________________'],
                ['Event Specialist Signature:', '________________________________'],
                ['Date Performed:', '________________________________'],
                ['Supervisor Signature:', '________________________________']
            ]
            
            signature_table = Table(signature_data, colWidths=[2.5*inch, 3.5*inch])
            signature_table.setStyle(TableStyle([
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('ALIGN', (0, 0), (0, -1), 'LEFT'),
                ('ALIGN', (1, 0), (1, -1), 'LEFT'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('TOPPADDING', (0, 0), (-1, -1), 8),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ]))
            story.append(signature_table)
        
        # Build the PDF
        doc.build(story)
        print(f"✅ Consolidated PDF generated: {filename}")
        return filename
    
    def generate_consolidated_pdf_weasyprint(self, html_reports: List[str], filename: Optional[str] = None) -> str:
        """
        Generate a consolidated PDF using WeasyPrint from HTML reports.
        
        Args:
            html_reports: List of HTML report strings
            filename: Optional PDF filename
            
        Returns:
            Path to generated PDF file
        """
        if not WEASYPRINT_AVAILABLE:
            raise ImportError("WeasyPrint is required for PDF generation. Install with: pip install weasyprint")
        
        if not filename:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"consolidated_edr_reports_{timestamp}.pdf"
        
        # Combine all HTML reports into one document
        combined_html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Consolidated EDR Reports</title>
            <style>
                body { 
                    font-family: Arial, sans-serif; 
                    margin: 0; 
                    padding: 20px;
                }
                .page-break { 
                    page-break-before: always; 
                }
                @page {
                    size: letter;
                    margin: 0.5in;
                }
                @media print {
                    .print-button { display: none; }
                }
            </style>
        </head>
        <body>
        """
        
        for i, html_report in enumerate(html_reports):
            if i > 0:
                combined_html += '<div class="page-break"></div>'
            
            # Extract body content from each report
            start_idx = html_report.find('<body>') + 6
            end_idx = html_report.find('</body>')
            if start_idx > 5 and end_idx > start_idx:
                body_content = html_report[start_idx:end_idx]
                # Remove the print button div
                body_content = body_content.replace('<div class="print-button"', '<div class="print-button" style="display:none;"')
                combined_html += body_content
        
        combined_html += """
        </body>
        </html>
        """
        
        # Generate PDF
        HTML(string=combined_html).write_pdf(filename)
        print(f"✅ Consolidated PDF generated: {filename}")
        return filename
    
    def print_pdf_file(self, pdf_path: str) -> bool:
        """
        Attempt to print a PDF file using system commands.
        
        Args:
            pdf_path: Path to the PDF file to print
            
        Returns:
            True if print command was executed successfully
        """
        abs_path = os.path.abspath(pdf_path)
        system = platform.system().lower()
        
        print(f"🖨️ Attempting to print PDF: {abs_path}")
        
        try:
            if system == "windows":
                # Method 1: Use Adobe Reader or default PDF viewer
                result = subprocess.run([
                    "cmd", "/c", "start", "/wait", "/min", "", "/print", abs_path
                ], capture_output=True, text=True, timeout=30)
                
                if result.returncode == 0:
                    print("✅ PDF sent to printer successfully")
                    return True
                else:
                    print(f"⚠️ Print command returned code: {result.returncode}")
                    
                # Method 2: Try PowerShell approach
                ps_cmd = f'Start-Process -FilePath "{abs_path}" -Verb Print -WindowStyle Hidden -Wait'
                result = subprocess.run([
                    "powershell.exe", "-WindowStyle", "Hidden", "-Command", ps_cmd
                ], capture_output=True, text=True, timeout=30)
                
                if result.returncode == 0:
                    print("✅ PDF sent to printer via PowerShell")
                    return True
                else:
                    print(f"⚠️ PowerShell print failed with code: {result.returncode}")
                    
            elif system == "darwin":  # macOS
                result = subprocess.run(["lp", abs_path], capture_output=True, text=True, timeout=30)
                if result.returncode == 0:
                    print("✅ PDF sent to printer on macOS")
                    return True
                    
            elif system == "linux":
                result = subprocess.run(["lp", abs_path], capture_output=True, text=True, timeout=30)
                if result.returncode == 0:
                    print("✅ PDF sent to printer on Linux")
                    return True
            
            print("❌ All PDF printing methods failed")
            print(f"💡 You can manually print this file: {abs_path}")
            return False
            
        except subprocess.TimeoutExpired:
            print("⚠️ Print command timed out")
            return False
        except Exception as e:
            print(f"❌ Print operation failed: {e}")
            return False
    
    def open_pdf_file(self, pdf_path: str) -> bool:
        """
        Open a PDF file with the default system viewer.
        
        Args:
            pdf_path: Path to the PDF file to open
            
        Returns:
            True if file was opened successfully
        """
        abs_path = os.path.abspath(pdf_path)
        system = platform.system().lower()
        
        try:
            if system == "windows":
                os.startfile(abs_path)
            elif system == "darwin":  # macOS
                subprocess.run(["open", abs_path])
            elif system == "linux":
                subprocess.run(["xdg-open", abs_path])
            
            print(f"📂 Opened PDF file: {abs_path}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to open PDF: {e}")
            return False
    
    def run_enhanced_batch(self, event_ids: Optional[List[str]] = None, 
                          authenticate: bool = True,
                          create_pdf: bool = True,
                          auto_print: bool = True,
                          open_pdf: bool = True) -> bool:
        """
        Run enhanced batch processing with PDF consolidation.
        
        Args:
            event_ids: List of event IDs to process
            authenticate: Whether to perform authentication
            create_pdf: Whether to create consolidated PDF
            auto_print: Whether to attempt automatic printing
            open_pdf: Whether to open the PDF file
            
        Returns:
            True if processing was successful
        """
        print("🚀 ENHANCED EDR PRINTER WITH PDF CONSOLIDATION")
        print("=" * 50)
        print(f"⏰ Started at: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        if event_ids is None:
            event_ids = self.DEFAULT_EVENT_IDS
        
        # Authenticate once if needed
        if authenticate and not self.generator.auth_token:
            if not self.authenticate_once():
                print("❌ Authentication failed - cannot proceed")
                return False
        
        # Collect EDR data for all events
        print(f"📊 Collecting data for {len(event_ids)} events...")
        event_data_list = []
        html_reports = []
        
        for i, event_id in enumerate(event_ids, 1):
            print(f"📋 Processing event {i}/{len(event_ids)}: {event_id}")
            
            try:
                # Get EDR data
                edr_data = self.generator.get_edr_report(event_id)
                if edr_data:
                    event_data_list.append(edr_data)
                    
                    # Generate HTML report
                    html_report = self.generator.generate_html_report(edr_data)
                    html_reports.append(html_report)
                    
                    # Save individual copy
                    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                    individual_file = self.generator.save_html_report(
                        html_report, 
                        f"edr_report_{event_id}_{timestamp}.html"
                    )
                    
                    print(f"✅ Event {event_id} processed successfully")
                else:
                    print(f"❌ Event {event_id} failed: Could not retrieve data")
                    
            except Exception as e:
                print(f"❌ Event {event_id} failed: {e}")
        
        if not event_data_list:
            print("❌ No event data collected - cannot create PDF")
            return False
        
        # Create consolidated PDF
        pdf_path = None
        if create_pdf:
            print(f"📄 Creating consolidated PDF from {len(event_data_list)} reports...")
            
            try:
                if REPORTLAB_AVAILABLE:
                    pdf_path = self.generate_consolidated_pdf_reportlab(event_data_list)
                elif WEASYPRINT_AVAILABLE:
                    pdf_path = self.generate_consolidated_pdf_weasyprint(html_reports)
                else:
                    print("❌ No PDF generation library available")
                    print("💡 Install with: pip install reportlab")
                    return False
                    
            except Exception as e:
                print(f"❌ PDF generation failed: {e}")
                return False
        
        # Print PDF if requested
        if auto_print and pdf_path:
            print("🖨️ Attempting to print consolidated PDF...")
            print_success = self.print_pdf_file(pdf_path)
            if not print_success:
                print("💡 Please print the PDF file manually")
        
        # Open PDF if requested
        if open_pdf and pdf_path:
            self.open_pdf_file(pdf_path)
        
        # Final summary
        print("\n" + "=" * 50)
        print("📊 ENHANCED PROCESSING SUMMARY")
        print("=" * 50)
        print(f"📋 Events Processed: {len(event_data_list)}/{len(event_ids)}")
        print(f"📄 Individual HTML Reports: {len(html_reports)}")
        if pdf_path:
            print(f"📄 Consolidated PDF: {pdf_path}")
        print(f"⏰ Completed at: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        return len(event_data_list) > 0


def main():
    """Main entry point for enhanced EDR printing."""
    printer = EnhancedEDRPrinter()
    
    # Check command line arguments for event IDs
    event_ids = None
    if len(sys.argv) > 1:
        event_ids = sys.argv[1:]
        print(f"📋 Using event IDs from command line: {event_ids}")
    else:
        print(f"📋 Using default event IDs: {printer.DEFAULT_EVENT_IDS}")
    
    print(f"\n🔐 Authentication Required")
    print("You will be prompted for MFA code once, then all reports will be processed automatically.")
    print("📄 A consolidated PDF will be created and opened for easy printing.")
    print()
    
    # Run the enhanced batch processing
    success = printer.run_enhanced_batch(
        event_ids=event_ids,
        authenticate=True,
        create_pdf=True,
        auto_print=True,
        open_pdf=True
    )
    
    return success


if __name__ == "__main__":
    exit_code = 0 if main() else 1
    sys.exit(exit_code)
