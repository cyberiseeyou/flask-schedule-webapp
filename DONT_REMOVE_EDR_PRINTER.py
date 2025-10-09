"""
Standalone EDR Printer - All-in-One
===================================

Complete EDR (Event Detail Report) printer with authentication, report generation,
and PDF consolidation in a single file.

Features:
- Multi-factor authentication with Walmart Retail Link
- Event browsing and filtering
- HTML report generation
- Consolidated PDF generation using ReportLab
- Automated printing capabilities
- No external dependencies except standard library + requests + reportlab

Usage:
    python standalone_edr_printer.py [event_id1] [event_id2] ...

Configuration:
    Edit the credentials at the top of the EDRReportGenerator class
"""

import requests
import json
import datetime
import sys
import os
import tempfile
import subprocess
import platform
import urllib.parse
from typing import Dict, List, Optional, Tuple, Any, Union

# Try to import PDF generation libraries
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
    print("⚠️ ReportLab not available - PDF generation will be disabled")
    print("💡 Install with: pip install reportlab")

try:
    from weasyprint import HTML, CSS
    WEASYPRINT_AVAILABLE = True
except (ImportError, OSError) as e:
    WEASYPRINT_AVAILABLE = False
    # Silently handle WeasyPrint import errors (common on Windows)


# ============================================================================
# EDR REPORT GENERATOR CLASS
# ============================================================================

class EDRReportGenerator:
    """
    Event Detail Report Generator for Walmart Retail Link Event Management System.

    Handles:
    1. Multi-factor authentication with Retail Link
    2. Event browsing and filtering
    3. EDR report data retrieval
    4. HTML report generation with print styling
    """

    def __init__(self):
        self.session = requests.Session()
        self.base_url = "https://retaillink2.wal-mart.com/EventManagement"
        self.auth_token = None
        self.user_data = None

        # Store credentials (in production, use environment variables)
        self.username = "mat.conder@productconnections.com"
        self.password = "Demos812Th$"
        self.mfa_credential_id = "18122365202"

        # Event report table headers
        self.report_headers = [
            "Item Number", "Primary Item Number", "Description", "Vendor", "Category"
        ]

        # Default store number for filtering
        self.default_store_number = "8135"

    def _get_initial_cookies(self) -> Dict[str, str]:
        """Return initial cookies required for authentication."""
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
            'TS0111a950': '0164c7ecbba28bf006381fcf7bc3c3fbc81a9b73705f5cedd649131a664e0cc5179472f6c66a7cee46d5fc6556faef1eb07fb3b8db',
            'TS01b1e5a6': '0164c7ecbba28bf006381fcf7bc3c3fbc81a9b73705f5cedd649131a664e0cc5179472f6c66a7cee46d5fc6556faef1eb07fb3b8db',
            'mp_c586ded18141faef3e556292ef2810bc_mixpanel': '%7B%22distinct_id%22%3A%20%22d2fr4w2%20%20%20%20%20%22%2C%22%24device_id%22%3A%20%221981deb804c5f0-08ebcf61e7361f-26011151-e12d0-1981deb804d22c4%22%2C%22%24initial_referrer%22%3A%20%22https%3A%2F%2Fretaillink.login.wal-mart.com%2F%22%2C%22%24initial_referring_domain%22%3A%20%22retaillink.login.wal-mart.com%22%2C%22%24user_id%22%3A%20%22d2fr4w2%20%20%20%20%20%22%7D',
            'TS04fe286f027': '08a6069d6cab2000cf0b847458906d222e70afa03939fa0de76da5c00884f260a79443300cc5407408d2c3bf9e113000b642cbc898d0534c0c86a20a3d11bab7101afcd84708efbc3e17c493bcf63e44a30e69658f98e8ce282590fbc1283275',
            '_px3': '85d2f0646ea75d99a2faac1898a7785dc1c8c7807e2612e865c5b74b4059d5fb:UHj6hAC9RHoxLnDq2rdjE+HkchqIMD2wKeYTOfHkRyo03uaqeN4xA4DX8dbN5RrJrX+uLLB/HTtX12k0ymeoSg==:1000:9TQQXsEtZxJ8rnnXulfuBg/dxB30NwnoogsLoiaQFk/xQECXPbbFYCno02+QFD40nnBos0iUVfyD2CpgeCV+cIFLDpCggGG0LVI2Q5S4hDYjVHb0fhh7UQ2cqGLr55bijg0Ix75CQdsdWi+gc34m88u66pDWGpB13rAKmim6yJo7/mxA32DYqKWBKbTwG/HvVDaGQCGDa+Iog+lfBNePx/WdAInb6LQ00IZGqYrdrE0='
        }

    def _get_standard_headers(self, content_type: Optional[str] = None, referer: Optional[str] = None) -> Dict[str, str]:
        """Return standard headers for API requests."""
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
        """Step 1: Submit username and password."""
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

        for name, value in self._get_initial_cookies().items():
            self.session.cookies.set(name, value)

        payload = {"username": self.username, "password": self.password, "language": "en"}

        print("Submitting username and password...")
        try:
            response = self.session.post(login_url, headers=headers, json=payload)
            response.raise_for_status()
            print("Password accepted. Proceediung to MFA.")
            return True
        except requests.exceptions.RequestException as e:
            print(f"❌ Username or Password error {e}")
            return False

    def step2_request_mfa_code(self) -> bool:
        """Step 2: Request MFA code to be sent to user's device."""
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

        print("➡️ Step 2: Requesting MFA code...")
        try:
            response = self.session.post(send_code_url, headers=headers, json=payload)
            response.raise_for_status()
            print("MFA code sent successfully. Check your device.")
            return True
        except requests.exceptions.RequestException as e:
            print(f"Step 2 failed: {e}")
            return False

    def step3_validate_mfa_code(self, code: str) -> bool:
        """Step 3: Validate the MFA code entered by user."""
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

        print("➡️ Step 3: Validating MFA code...")
        try:
            response = self.session.post(validate_url, headers=headers, json=payload)
            response.raise_for_status()
            print("MFA authentication complete!")
            return True
        except requests.exceptions.RequestException as e:
            print(f"Step 3 failed. The code may have been incorrect.")
            return False

    def step4_register_page_access(self) -> bool:
        """Step 4: Register page access to Event Management System."""
        url = "https://retaillink2.wal-mart.com/rl_portal_services/api/Site/InsertRlPageDetails"
        params = {
            'pageId': '6',
            'pageSubId': 'w6040',
            'pageSubDesc': 'Event Management System'
        }
       
        headers = self._get_standard_headers(referer='https://retaillink2.wal-mart.com/rl_portal/')
        headers['priority'] = 'u=1, i'        

        print("Step 4: Registering page access...")
        try:
            response = self.session.get(url, headers=headers, params=params)
            if response.status_code == 200:
                print("Page access registered")
                return True
            else:
                print(f"Page registration status: {response.status_code}")
                return False
        except requests.exceptions.RequestException as e:
            print(f"Page registration failed: {e}")
            return False

    def step5_navigate_to_event_management(self) -> bool:
        """Step 5: Navigate to Event Management system."""
        # Navigate to portal first
        portal_url = "https://retaillink2.wal-mart.com/rl_portal/"
        headers = {
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'accept-language': 'en-US,en;q=0.9',
            'sec-ch-ua': '"Not)A;Brand";v="8", "Chromium";v="138", "Google Chrome";v="138"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'document',
            'sec-fetch-mode': 'navigate',
            'sec-fetch-site': 'same-site',
            'upgrade-insecure-requests': '1',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36',
        }

        print("Step 5: Navigating to Event Management...")
        try:
            response = self.session.get(portal_url, headers=headers)
            if response.status_code != 200:
                print(f"Portal access failed: {response.status_code}")
                return False

            event_mgmt_url = f"{self.base_url}/"
            response = self.session.get(event_mgmt_url, headers=headers)
            if response.status_code == 200:
                print("Event Management navigation successful")
                return True
            else:
                print(f"Event Management access failed: {response.status_code}")
                return False
        except requests.exceptions.RequestException as e:
            print(f"Navigation failed: {e}")
            return False


    def step6_authenticate_event_management(self) -> bool:
        """Step 6: Authenticate with Event Management API and extract auth token."""
        auth_url = f"{self.base_url}/api/authenticate"
        headers = self._get_standard_headers(referer=f"{self.base_url}/")
        
        print("➡️ Step 6: Authenticating with Event Management API...")
        try:
            response = self.session.get(auth_url, headers=headers)
            if response.status_code == 200:
                try:
                    auth_data = response.json()
                    print("✅ Event Management authentication successful!")
                    
                    # Extract auth token from cookies (based on cURL command)
                    for cookie in self.session.cookies:
                        if cookie.name == 'auth-token' and cookie.value:
                            # Parse the URL-encoded cookie value
                            cookie_data = urllib.parse.unquote(cookie.value)
                            try:
                                token_data = json.loads(cookie_data)
                                self.auth_token = token_data.get('token')
                                print(f"🔑 Auth token extracted: {self.auth_token[:50]}...")
                                return True
                            except json.JSONDecodeError:
                                print("⚠️ Could not parse auth-token cookie")
                    
                    print("⚠️ auth-token cookie not found")
                    return False
                    
                except json.JSONDecodeError:
                    print("⚠️ Authentication response not JSON but status OK")
                    return True
            else:
                print(f"❌ Authentication failed: {response.status_code}")
                return False
        except requests.exceptions.RequestException as e:
            print(f"❌ Authentication API call failed: {e}")
            return False


    def authenticate(self) -> bool:
        """Complete authentication flow."""
        print("🔐 Starting Retail Link authentication...")

        if not self.step1_submit_password():
            return False

        if not self.step2_request_mfa_code():
            return False

        mfa_code = input("📱 Please enter the MFA code you received: ").strip()
        if not self.step3_validate_mfa_code(mfa_code):
            return False

        if not self.step4_register_page_access():
            print("⚠️ Page registration failed, continuing...")

        if not self.step5_navigate_to_event_management():
            print("⚠️ Navigation failed, continuing...")

        if not self.step6_authenticate_event_management():
            print("❌ Could not obtain auth token")
            return False

        print("✅ Full authentication completed successfully!")
        return True

    def get_edr_report(self, event_id: str) -> Dict[str, Any]:
        """Get EDR report data for a specific event ID."""
        if not self.auth_token:
            raise ValueError("Must authenticate first before getting EDR report")

        url = f"{self.base_url}/api/edrReport?id={event_id}"
        headers = self._get_standard_headers(referer=f"{self.base_url}/browse-event")

        print(f"📄 Retrieving EDR report for event {event_id}...")
        try:
            response = self.session.get(url, headers=headers)
            response.raise_for_status()

            report_data = response.json()
            print(f"✅ EDR report retrieved successfully")
            return report_data
        except requests.exceptions.RequestException as e:
            print(f"❌ EDR report retrieval failed: {e}")
            return {}

    def generate_html_report(self, edr_data: Dict[str, Any]) -> str:
        """Generate HTML report from EDR data."""
        now = datetime.datetime.now()
        report_date = now.strftime("%Y-%m-%d")
        report_time = now.strftime("%H:%M:%S")

        event_number = edr_data.get('demoId', 'N/A') if edr_data else 'N/A'
        event_type = edr_data.get('demoClassCode', 'N/A') if edr_data else 'N/A'
        event_status = edr_data.get('demoStatusCode', 'N/A') if edr_data else 'N/A'
        event_date = edr_data.get('demoDate', 'N/A') if edr_data else 'N/A'
        event_name = edr_data.get('demoName', 'N/A') if edr_data else 'N/A'
        event_locked = edr_data.get('demoLockInd', 'N/A') if edr_data else 'N/A'

        instructions = edr_data.get('demoInstructions', {}) if edr_data else {}
        event_prep = instructions.get('demoPrepnTxt', 'N/A') if instructions else 'N/A'
        event_portion = instructions.get('demoPortnTxt', 'N/A') if instructions else 'N/A'

        item_details = edr_data.get('itemDetails', []) if edr_data else []

        item_rows = ""
        for item in item_details:
            item_rows += f"""
                <tr class="edr-wrapper">
                    <td class="report-table-content">{item.get('itemNbr', '')}</td>
                    <td class="report-table-content">{item.get('gtin', '')}</td>
                    <td class="report-table-content">{item.get('itemDesc', '')}</td>
                    <td class="report-table-content">{item.get('vendorNbr', '')}</td>
                    <td class="report-table-content">{item.get('deptNbr', '')}</td>
                </tr>
            """

        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Event Management System - EDR Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; padding: 20px; margin: 0; }}
        .detail-header {{ display: flex; justify-content: center; align-items: center; font-weight: 700; font-size: 24px; margin-bottom: 20px; }}
        .font-weight-bold {{ font-size: 18px; margin-top: 10px; margin-bottom: 10px; font-weight: bold; }}
        .help-text {{ font-size: 14px; line-height: 1.2; }}
        .demo-text {{ margin-left: 12px; font-weight: 700; }}
        .row {{ display: flex; padding: 5px; width: 100%; }}
        .col {{ flex: 1; display: block; padding: 5px; width: 100%; }}
        .col-25 {{ flex: 0 0 25%; max-width: 25%; }}
        .col-40 {{ flex: 0 0 40%; max-width: 40%; }}
        .input-label {{ font-weight: normal; }}
        td {{ padding: 8px; border-top: solid 1px #ccc; font-family: arial; font-size: 12px; text-align: left; font-weight: 400; color: grey; }}
        table {{ width: 100%; border-collapse: collapse; text-align: center; font-size: 94%; outline: #ccc solid 1px; margin-bottom: 10px; }}
        th {{ padding: 5px; background: #e2e1e1; font-size: 14px; font-weight: 400; color: grey; }}
        hr {{ border: 1px solid #ccc; margin: 10px 0; }}
        @media print {{ .print-button {{ display: none; }} }}
    </style>
</head>
<body>
    <div class="detail-header">EVENT DETAIL REPORT</div>
    <div class="font-weight-bold"><span>RUN ON </span><span>{report_date}</span><span> AT </span><span>{report_time}</span></div>
    <hr>
    <div class="help-text">
        <div><b>IMPORTANT!!!</b> This report should be printed each morning prior to completing each event.</div>
    </div>
    <hr>
    <div>
        <div class="row">
            <div class="col col-25"><span class="input-label">Event Number <span class="demo-text">{event_number}</span></span></div>
            <div class="col col-25"><span class="input-label">Event Type <span class="demo-text">{event_type}</span></span></div>
            <div class="col col-40"><span class="input-label">Event Locked <span class="demo-text">{event_locked}</span></span></div>
        </div>
        <div class="row">
            <div class="col col-25"><span class="input-label">Event Status <span class="demo-text">{event_status}</span></span></div>
            <div class="col col-25"><span class="input-label">Event Date <span class="demo-text">{event_date}</span></span></div>
            <div class="col col-40"><span class="input-label">Event Name <span class="demo-text">{event_name}</span></span></div>
        </div>
    </div>
    <table>
        <thead>
            <tr><th>Item Number</th><th>Primary Item Number</th><th>Description</th><th>Vendor</th><th>Category</th></tr>
        </thead>
        <tbody>{item_rows}</tbody>
    </table>
    <div class="print-button" style="margin-top: 20px; text-align: right;">
        <button onclick="window.print()" style="padding: 10px 20px; background: #1976d2; color: white; border: none; border-radius: 4px; cursor: pointer;">🖨️ Print Report</button>
    </div>
</body>
</html>
        """
        return html_content.strip()

    def save_html_report(self, html_content: str, filename: Optional[str] = None) -> str:
        """Save HTML report to file."""
        if not filename:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"edr_report_{timestamp}.html"

        with open(filename, 'w', encoding='utf-8') as f:
            f.write(html_content)

        print(f"💾 Report saved to: {filename}")
        return filename


# ============================================================================
# AUTOMATED EDR PRINTER CLASS
# ============================================================================

class AutomatedEDRPrinter:
    """Fully automated EDR report printer with no user interaction."""

    def __init__(self):
        self.generator = EDRReportGenerator()
        self.DEFAULT_EVENT_IDS = ["606034"]  # Default event IDs

    def authenticate_once(self) -> bool:
        """Perform authentication once for the entire session."""
        print("🔐 Performing one-time authentication...")
        success = self.generator.authenticate()
        if success:
            print("✅ Authentication successful - token will be reused for all reports")
            return True
        else:
            print("❌ Authentication failed")
            return False


# ============================================================================
# ENHANCED EDR PRINTER CLASS (WITH PDF SUPPORT)
# ============================================================================

class EnhancedEDRPrinter(AutomatedEDRPrinter):
    """Enhanced EDR printer that creates consolidated PDF files from multiple reports."""

    def __init__(self):
        super().__init__()
        self.pdf_reports = []

        # Event type code mappings
        self.event_type_codes = {
            '1': 'Sampling', '2': 'Demo/Sampling', '3': 'Cooking Demo',
            '4': 'Product Demo', '5': 'Educational', '6': 'Seasonal',
            '7': 'Holiday', '8': 'Back to School', '9': 'Health & Wellness',
            '10': 'New Product Launch', '45': 'Food Demo/Sampling',
            '46': 'Beverage Demo', '47': 'Product Demonstration',
        }

        # Event status code mappings
        self.event_status_codes = {
            '1': 'Pending', '2': 'Active/Scheduled', '3': 'In Progress',
            '4': 'Completed', '5': 'Cancelled', '6': 'On Hold',
            '7': 'Under Review', '8': 'Approved', '9': 'Rejected',
        }

    def get_event_type_description(self, code: str) -> str:
        """Convert event type code to human readable description."""
        if not code or code == 'N/A':
            return 'N/A'
        code_str = str(code).upper()
        return self.event_type_codes.get(code_str, f"Event Type {code}")

    def get_event_status_description(self, code: str) -> str:
        """Convert event status code to human readable description."""
        if not code or code == 'N/A':
            return 'N/A'
        code_str = str(code).upper()
        return self.event_status_codes.get(code_str, f"Status {code}")

    def generate_consolidated_pdf_reportlab(self, event_data_list: List[Dict[str, Any]], filename: Optional[str] = None) -> str:
        """Generate a consolidated PDF using ReportLab from multiple EDR data sets."""
        if not REPORTLAB_AVAILABLE:
            raise ImportError("ReportLab is required for PDF generation. Install with: pip install reportlab")

        if not filename:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"consolidated_edr_reports_{timestamp}.pdf"

        doc = SimpleDocTemplate(filename, pagesize=letter, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=18)
        story = []
        styles = getSampleStyleSheet()

        title_style = ParagraphStyle('CustomTitle', parent=styles['Heading1'], fontSize=18, spaceAfter=30, alignment=TA_CENTER, fontName='Helvetica-Bold')
        header_style = ParagraphStyle('CustomHeader', parent=styles['Heading2'], fontSize=14, spaceAfter=12, alignment=TA_CENTER, fontName='Helvetica-Bold')
        normal_style = styles['Normal']
        normal_style.fontSize = 10

        now = datetime.datetime.now()
        report_date = now.strftime("%Y-%m-%d")
        report_time = now.strftime("%H:%M:%S")

        print(f"📄 Generating consolidated PDF with {len(event_data_list)} reports...")

        # Cover page
        cover_title_style = ParagraphStyle('CoverTitle', parent=styles['Heading1'], fontSize=24, spaceAfter=50, alignment=TA_CENTER, fontName='Helvetica-Bold')
        story.append(Paragraph("CONSOLIDATED EVENT DETAILS REPORT", cover_title_style))
        story.append(Spacer(1, 50))
        story.append(Paragraph(f"Generated on {report_date} at {report_time}", header_style))
        story.append(Spacer(1, 30))
        story.append(Paragraph(f"Total Events: {len(event_data_list)}", header_style))
        story.append(Spacer(1, 30))

        # Summary table
        if event_data_list:
            summary_data = [['Event ID', 'Event Name', 'Event Type', 'Status']]
            for event_data in event_data_list:
                event_number = event_data.get('demoId', 'N/A') if event_data else 'N/A'
                event_name = event_data.get('demoName', 'N/A') if event_data else 'N/A'
                event_type_code = event_data.get('demoClassCode', 'N/A') if event_data else 'N/A'
                event_status_code = event_data.get('demoStatusCode', 'N/A') if event_data else 'N/A'

                event_type_desc = self.get_event_type_description(event_type_code)
                event_status_desc = self.get_event_status_description(event_status_code)

                event_name_short = str(event_name)[:30] + '...' if len(str(event_name)) > 30 else str(event_name)

                summary_data.append([str(event_number), event_name_short, event_type_desc, event_status_desc])

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

        story.append(PageBreak())

        # Individual reports
        for i, event_data in enumerate(event_data_list):
            if i > 0:
                story.append(PageBreak())

            event_number = event_data.get('demoId', 'N/A') if event_data else 'N/A'
            event_type_code = event_data.get('demoClassCode', 'N/A') if event_data else 'N/A'
            event_status_code = event_data.get('demoStatusCode', 'N/A') if event_data else 'N/A'
            event_date = event_data.get('demoDate', 'N/A') if event_data else 'N/A'
            event_name = event_data.get('demoName', 'N/A') if event_data else 'N/A'
            event_locked = event_data.get('demoLockInd', 'N/A') if event_data else 'N/A'

            event_type = self.get_event_type_description(event_type_code)
            event_status = self.get_event_status_description(event_status_code)

            item_details = event_data.get('itemDetails', []) if event_data else []

            story.append(Paragraph("EVENT DETAIL REPORT", title_style))
            story.append(Spacer(1, 12))

            # Event details tables
            event_details_row1 = [
                ['Event Number', 'Event Type', 'Event Locked'],
                [str(event_number), str(event_type), str(event_locked)]
            ]

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

            # Signature section
            story.append(Paragraph("<b>MUST BE SIGNED AND DATED</b>", header_style))
            story.append(Spacer(1, 20))

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
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ]))
            story.append(signature_table)

        doc.build(story)
        print(f"✅ Consolidated PDF generated: {filename}")
        return filename

    def open_pdf_file(self, pdf_path: str) -> bool:
        """Open a PDF file with the default system viewer."""
        abs_path = os.path.abspath(pdf_path)
        system = platform.system().lower()

        try:
            if system == "windows":
                os.startfile(abs_path)
            elif system == "darwin":
                subprocess.run(["open", abs_path])
            elif system == "linux":
                subprocess.run(["xdg-open", abs_path])

            print(f"📂 Opened PDF file: {abs_path}")
            return True
        except Exception as e:
            print(f"❌ Failed to open PDF: {e}")
            return False

    def run_enhanced_batch(self, event_ids: Optional[List[str]] = None, authenticate: bool = True, create_pdf: bool = True, open_pdf: bool = True) -> bool:
        """Run enhanced batch processing with PDF consolidation."""
        print("🚀 ENHANCED EDR PRINTER WITH PDF CONSOLIDATION")
        print("=" * 50)
        print(f"⏰ Started at: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        if event_ids is None:
            event_ids = self.DEFAULT_EVENT_IDS

        if authenticate and not self.generator.auth_token:
            if not self.authenticate_once():
                print("❌ Authentication failed - cannot proceed")
                return False

        print(f"📊 Collecting data for {len(event_ids)} events...")
        event_data_list = []

        for i, event_id in enumerate(event_ids, 1):
            print(f"📋 Processing event {i}/{len(event_ids)}: {event_id}")

            try:
                edr_data = self.generator.get_edr_report(event_id)
                if edr_data:
                    event_data_list.append(edr_data)
                    print(f"✅ Event {event_id} processed successfully")
                else:
                    print(f"❌ Event {event_id} failed: Could not retrieve data")
            except Exception as e:
                print(f"❌ Event {event_id} failed: {e}")

        if not event_data_list:
            print("❌ No event data collected - cannot create PDF")
            return False

        pdf_path = None
        if create_pdf:
            print(f"📄 Creating consolidated PDF from {len(event_data_list)} reports...")

            try:
                if REPORTLAB_AVAILABLE:
                    pdf_path = self.generate_consolidated_pdf_reportlab(event_data_list)
                else:
                    print("❌ No PDF generation library available")
                    print("💡 Install with: pip install reportlab")
                    return False
            except Exception as e:
                print(f"❌ PDF generation failed: {e}")
                return False

        if open_pdf and pdf_path:
            self.open_pdf_file(pdf_path)

        print("\n" + "=" * 50)
        print("📊 ENHANCED PROCESSING SUMMARY")
        print("=" * 50)
        print(f"📋 Events Processed: {len(event_data_list)}/{len(event_ids)}")
        if pdf_path:
            print(f"📄 Consolidated PDF: {pdf_path}")
        print(f"⏰ Completed at: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        return len(event_data_list) > 0


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

def main():
    """Main entry point for standalone EDR printing."""
    printer = EnhancedEDRPrinter()

    event_ids = None
    if len(sys.argv) > 1:
        event_ids = sys.argv[1:]
        print(f"Using event IDs from command line: {event_ids}")
    else:
        print(f"Using default event IDs: {printer.DEFAULT_EVENT_IDS}")

    print(f"\n[AUTH] Authentication Required")
    print("You will be prompted for MFA code once, then all reports will be processed automatically.")
    print("A consolidated PDF will be created and opened for easy printing.")
    print()

    success = printer.run_enhanced_batch(event_ids=event_ids, authenticate=True, create_pdf=True, open_pdf=True)

    return success


if __name__ == "__main__":
    exit_code = 0 if main() else 1
    sys.exit()
