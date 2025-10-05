"""
EDR Authentication and Report Generation
Handles Walmart Retail Link authentication and EDR report downloading with PDF conversion
"""
import requests
import json
import urllib.parse
import logging
from typing import Dict, Optional, Any
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER


class EDRAuthenticator:
    """Handles authentication with Walmart Retail Link Event Management System"""

    def __init__(self, username: str, password: str, mfa_credential_id: str):
        self.session = requests.Session()
        self.base_url = "https://retaillink2.wal-mart.com/EventManagement"
        self.auth_token = None
        self.username = username
        self.password = password
        self.mfa_credential_id = mfa_credential_id
        self.logger = logging.getLogger(__name__)

    def _get_initial_cookies(self) -> Dict[str, str]:
        """Return initial cookies required for authentication"""
        return {
            'vtc': 'Q0JqQVX0STHy6sao9qdhNw',
            '_pxvid': '3c803a96-548a-11f0-84bf-e045250e632c',
            '_ga': 'GA1.2.103605184.1751648140',
            'QuantumMetricUserID': '23bc666aa80d92de6f4ffa5b79ff9fdc',
            'pxcts': 'd0d1b4d9-65f2-11f0-a59e-62912b00fffc',
            'rl_access_attempt': '0',
            'rlLoginInfo': '',
            'bstc': 'ZpNiPcM5OgU516Fy1nOhHw',
            'rl_show_login_form': 'N',
        }

    def _get_standard_headers(self, content_type: Optional[str] = None, referer: Optional[str] = None) -> Dict[str, str]:
        """Return standard headers for API requests"""
        headers = {
            'accept': 'application/json, text/plain, */*',
            'accept-language': 'en-US,en;q=0.9',
            'sec-ch-ua': '"Not)A;Brand";v="8", "Chromium";v="138", "Google Chrome";v="138"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-origin',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36'
        }

        if content_type:
            headers['content-type'] = content_type

        if referer:
            headers['referer'] = referer

        if self.auth_token:
            headers['authorization'] = f'Bearer {self.auth_token}'

        return headers

    def step1_submit_password(self) -> bool:
        """Submit username and password"""
        login_url = "https://retaillink.login.wal-mart.com/api/login"
        headers = {
            'accept': '*/*',
            'accept-language': 'en-US,en;q=0.9',
            'content-type': 'application/json',
            'origin': 'https://retaillink.login.wal-mart.com',
            'priority': 'u=1, i',
            'referer': 'https://retaillink.login.wal-mart.com/login',
            'sec-ch-ua': '"Not)A;Brand";v="8", "Chromium";v="138", "Google Chrome";v="138"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-origin',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36',
        }

        # Clear all existing cookies and set initial cookies
        self.session.cookies.clear()
        for name, value in self._get_initial_cookies().items():
            self.session.cookies.set(name, value)

        payload = {"username": self.username, "password": self.password, "language": "en"}

        try:
            response = self.session.post(login_url, headers=headers, json=payload)
            response.raise_for_status()
            self.logger.info("Password accepted")
            return True
        except Exception as e:
            self.logger.error(f"Password submission failed: {str(e)}")
            return False

    def step2_request_mfa_code(self) -> bool:
        """Request MFA code"""
        send_code_url = "https://retaillink.login.wal-mart.com/api/mfa/sendCode"
        headers = {
            'accept': '*/*',
            'accept-language': 'en-US,en;q=0.9',
            'content-type': 'application/json',
            'origin': 'https://retaillink.login.wal-mart.com',
            'referer': 'https://retaillink.login.wal-mart.com/login',
            'sec-ch-ua': '"Not)A;Brand";v="8", "Chromium";v="138", "Google Chrome";v="138"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-origin',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36',
        }
        payload = {"type": "SMS_OTP", "credid": self.mfa_credential_id}

        try:
            response = self.session.post(send_code_url, headers=headers, json=payload)
            response.raise_for_status()
            self.logger.info("MFA code sent successfully")
            return True
        except Exception as e:
            self.logger.error(f"MFA code request failed: {str(e)}")
            return False

    def step3_validate_mfa_code(self, code: str) -> bool:
        """Validate MFA code"""
        validate_url = "https://retaillink.login.wal-mart.com/api/mfa/validateCode"
        headers = {
            'accept': '*/*',
            'accept-language': 'en-US,en;q=0.9',
            'content-type': 'application/json',
            'origin': 'https://retaillink.login.wal-mart.com',
            'referer': 'https://retaillink.login.wal-mart.com/login',
            'sec-ch-ua': '"Not)A;Brand";v="8", "Chromium";v="138", "Google Chrome";v="138"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-origin',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36',
        }
        payload = {
            "type": "SMS_OTP",
            "credid": self.mfa_credential_id,
            "code": code,
            "failureCount": 0
        }

        try:
            response = self.session.post(validate_url, headers=headers, json=payload)
            response.raise_for_status()
            self.logger.info("MFA code validated successfully")
            return True
        except Exception as e:
            self.logger.error(f"MFA validation failed: {str(e)}")
            return False

    def step4_register_page_access(self):
        """Register page access"""
        url = "https://retaillink2.wal-mart.com/rl_portal_services/api/Site/InsertRlPageDetails"
        params = {'pageId': '6', 'pageSubId': 'w6040', 'pageSubDesc': 'Event Management System'}
        try:
            self.session.get(url, params=params, timeout=10)
        except:
            pass

    def step5_navigate_to_event_management(self):
        """Navigate to Event Management"""
        try:
            self.session.get("https://retaillink2.wal-mart.com/rl_portal/", timeout=10)
            self.session.get(f"{self.base_url}/", timeout=10)
        except:
            pass

    def step6_authenticate_event_management(self) -> bool:
        """Get auth token from Event Management API"""
        auth_url = f"{self.base_url}/api/authenticate"

        try:
            response = self.session.get(auth_url, timeout=10)
            if response.status_code == 200:
                # Extract auth token from cookies
                for cookie in self.session.cookies:
                    if cookie.name == 'auth-token' and cookie.value:
                        cookie_data = urllib.parse.unquote(cookie.value)
                        try:
                            token_data = json.loads(cookie_data)
                            self.auth_token = token_data.get('token')
                            if self.auth_token:
                                self.logger.info("Authentication successful")
                                return True
                        except:
                            pass
            return False
        except Exception as e:
            self.logger.error(f"Event Management auth failed: {str(e)}")
            return False

    def authenticate(self, mfa_code: str) -> bool:
        """Complete authentication flow with MFA code"""
        try:
            if not self.step1_submit_password():
                return False

            if not self.step2_request_mfa_code():
                return False

            if not self.step3_validate_mfa_code(mfa_code):
                return False

            self.step4_register_page_access()
            self.step5_navigate_to_event_management()

            if not self.step6_authenticate_event_management():
                return False

            return True
        except Exception as e:
            self.logger.error(f"Authentication failed: {str(e)}")
            return False

    def get_edr_report(self, event_id: str) -> Optional[Dict[str, Any]]:
        """Get EDR report data for a specific event ID"""
        if not self.auth_token:
            self.logger.error("Not authenticated - cannot get EDR report")
            return None

        url = f"{self.base_url}/api/edrReport?id={event_id}"
        headers = self._get_standard_headers(referer=f"{self.base_url}/browse-event")

        self.logger.info(f"Retrieving EDR report for event {event_id}...")
        try:
            response = self.session.get(url, headers=headers, timeout=30)
            response.raise_for_status()

            report_data = response.json()
            self.logger.info(f"EDR report retrieved successfully for event {event_id}")
            return report_data
        except Exception as e:
            self.logger.error(f"Failed to get EDR report for event {event_id}: {str(e)}")
            return None


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
