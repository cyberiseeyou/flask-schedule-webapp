"""
Unit Tests for EDR PDF Generator
=================================

Tests for the EDRPDFGenerator class to verify:
- Correct PDF layout and structure
- Proper field mapping from EDR data
- Color scheme consistency
- Bold formatting for Locked field
"""

import unittest
import os
import tempfile
from datetime import datetime

# Import the PDF generator from scheduler_app
import sys
scheduler_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'scheduler_app')
if scheduler_path not in sys.path:
    sys.path.insert(0, scheduler_path)

from scheduler_app.edr.pdf_generator import EDRPDFGenerator


class TestEDRPDFGenerator(unittest.TestCase):
    """Test cases for EDRPDFGenerator"""

    def setUp(self):
        """Set up test fixtures"""
        self.generator = EDRPDFGenerator()

        # Sample EDR data matching Walmart API response structure
        self.sample_edr_data = {
            'demoId': '606034',
            'demoName': 'Hot Dog Demo - Test Event',
            'demoDate': '2025-10-05',
            'demoClassCode': '3',  # STANDARD
            'demoStatusCode': '2',  # APPROVED
            'demoLockInd': 'Y',  # Yes
            'demoInstructions': {
                'demoPrepnTxt': 'Prepare grill and condiments',
                'demoPortnTxt': '1 hot dog per sample'
            },
            'itemDetails': [
                {
                    'itemNbr': '123456',
                    'gtin': '00012345678901',
                    'itemDesc': 'Premium Hot Dogs 8pk',
                    'vendorNbr': '1234',
                    'deptNbr': '54'
                },
                {
                    'itemNbr': '789012',
                    'gtin': '00098765432101',
                    'itemDesc': 'Hot Dog Buns 8ct',
                    'vendorNbr': '5678',
                    'deptNbr': '48'
                }
            ]
        }

    def tearDown(self):
        """Clean up after tests"""
        pass

    def test_mapping_event_type_code(self):
        """Test event type code mapping"""
        # Test STANDARD event type (code 3)
        result = self.generator.get_event_type_description('3')
        self.assertIn('STANDARD', result.upper())

        # Test invalid code
        result = self.generator.get_event_type_description('999')
        self.assertIn('999', result)

        # Test N/A
        result = self.generator.get_event_type_description('N/A')
        self.assertEqual(result, 'N/A')

    def test_mapping_event_status_code(self):
        """Test event status code mapping"""
        # Test APPROVED status (code 2)
        result = self.generator.get_event_status_description('2')
        self.assertIn('APPROVED', result.upper())

        # Test invalid code
        result = self.generator.get_event_status_description('999')
        self.assertIn('999', result)

        # Test N/A
        result = self.generator.get_event_status_description('N/A')
        self.assertEqual(result, 'N/A')

    def test_mapping_department_code(self):
        """Test department code mapping"""
        # Test department 1 (CANDY - SNACKS - BUSINESS)
        result = self.generator.get_department_description('1')
        self.assertIn('CANDY', result.upper())

        # Test department 54 (MEAT)
        result = self.generator.get_department_description('54')
        self.assertTrue(len(result) > 0)

        # Test invalid code
        result = self.generator.get_department_description('9999')
        self.assertIn('9999', result)

    def test_date_formatting(self):
        """Test date format conversion"""
        # Test YYYY-MM-DD to MM-DD-YYYY
        result = self.generator.format_date('2025-10-05')
        self.assertEqual(result, '10-05-2025')

        # Test N/A handling
        result = self.generator.format_date('N/A')
        self.assertEqual(result, 'N/A')

        # Test empty string
        result = self.generator.format_date('')
        self.assertEqual(result, 'N/A')

    def test_pdf_generation_success(self):
        """Test successful PDF generation"""
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp:
            output_path = tmp.name

        try:
            # Generate PDF
            success = self.generator.generate_pdf(
                self.sample_edr_data,
                output_path,
                'John Doe'
            )

            # Verify PDF was created
            self.assertTrue(success)
            self.assertTrue(os.path.exists(output_path))

            # Verify file size is reasonable (at least 2KB)
            file_size = os.path.getsize(output_path)
            self.assertGreater(file_size, 2000)

        finally:
            # Clean up
            if os.path.exists(output_path):
                os.remove(output_path)

    def test_pdf_with_empty_items(self):
        """Test PDF generation with no item details"""
        empty_data = self.sample_edr_data.copy()
        empty_data['itemDetails'] = []

        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp:
            output_path = tmp.name

        try:
            success = self.generator.generate_pdf(empty_data, output_path, 'Jane Smith')
            self.assertTrue(success)
            self.assertTrue(os.path.exists(output_path))

        finally:
            if os.path.exists(output_path):
                os.remove(output_path)

    def test_pdf_with_missing_fields(self):
        """Test PDF generation with missing optional fields"""
        minimal_data = {
            'demoId': '999999',
            'demoName': 'Test Event',
            'demoDate': '2025-12-25',
            'demoClassCode': 'N/A',
            'demoStatusCode': 'N/A',
            'demoLockInd': 'N',
            'itemDetails': []
        }

        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp:
            output_path = tmp.name

        try:
            success = self.generator.generate_pdf(minimal_data, output_path)
            self.assertTrue(success)

        finally:
            if os.path.exists(output_path):
                os.remove(output_path)

    def test_locked_indicator_yes(self):
        """Test locked indicator displays YES correctly"""
        # Test with 'Y'
        data = self.sample_edr_data.copy()
        data['demoLockInd'] = 'Y'

        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp:
            output_path = tmp.name

        try:
            success = self.generator.generate_pdf(data, output_path)
            self.assertTrue(success)
            # Note: Would need PDF parsing library to verify "YES" appears in bold
            # This is a basic smoke test

        finally:
            if os.path.exists(output_path):
                os.remove(output_path)

    def test_locked_indicator_no(self):
        """Test locked indicator displays NO correctly"""
        # Test with 'N'
        data = self.sample_edr_data.copy()
        data['demoLockInd'] = 'N'

        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp:
            output_path = tmp.name

        try:
            success = self.generator.generate_pdf(data, output_path)
            self.assertTrue(success)

        finally:
            if os.path.exists(output_path):
                os.remove(output_path)

    def test_color_scheme(self):
        """Test color scheme is correctly configured"""
        # Verify Product Connections colors are set
        self.assertEqual(self.generator.pc_blue.hexval().upper().replace('0X', '#'), '#2E4C73')
        self.assertEqual(self.generator.pc_light_blue.hexval().upper().replace('0X', '#'), '#1B9BD8')

    def test_employee_name_in_signature_section(self):
        """Test employee name is pre-filled in signature section"""
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp:
            output_path = tmp.name

        try:
            employee_name = 'Alice Johnson'
            success = self.generator.generate_pdf(
                self.sample_edr_data,
                output_path,
                employee_name
            )

            self.assertTrue(success)
            # Note: Would need PDF parsing to verify employee name appears in PDF

        finally:
            if os.path.exists(output_path):
                os.remove(output_path)

    def test_error_handling_invalid_path(self):
        """Test error handling for invalid file path"""
        invalid_path = '/nonexistent/directory/file.pdf'

        success = self.generator.generate_pdf(
            self.sample_edr_data,
            invalid_path,
            'Test Employee'
        )

        # Should return False on error
        self.assertFalse(success)

    def test_multiple_items_rendering(self):
        """Test PDF generation with multiple items"""
        # Create data with 10 items
        multi_item_data = self.sample_edr_data.copy()
        multi_item_data['itemDetails'] = [
            {
                'itemNbr': f'00000{i}',
                'gtin': f'000000000000{i:02d}',
                'itemDesc': f'Test Item {i}',
                'vendorNbr': f'{1000+i}',
                'deptNbr': str((i % 100) + 1)
            }
            for i in range(1, 11)
        ]

        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp:
            output_path = tmp.name

        try:
            success = self.generator.generate_pdf(multi_item_data, output_path)
            self.assertTrue(success)

            # Verify PDF is larger with more items (at least 2.5KB)
            file_size = os.path.getsize(output_path)
            self.assertGreater(file_size, 2500)

        finally:
            if os.path.exists(output_path):
                os.remove(output_path)


class TestPDFLayoutSpecifics(unittest.TestCase):
    """Test specific layout requirements from architecture"""

    def setUp(self):
        """Set up test fixtures"""
        self.generator = EDRPDFGenerator()

    def test_row1_structure(self):
        """Test Row 1 contains Event Number and Event Name"""
        # This would require PDF parsing to verify
        # For now, ensure method exists and works
        sample_data = {
            'demoId': '123456',
            'demoName': 'Test Event Name',
            'demoDate': '2025-01-01',
            'demoClassCode': '3',
            'demoStatusCode': '2',
            'demoLockInd': 'N',
            'itemDetails': []
        }

        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp:
            output_path = tmp.name

        try:
            success = self.generator.generate_pdf(sample_data, output_path)
            self.assertTrue(success)

        finally:
            if os.path.exists(output_path):
                os.remove(output_path)

    def test_row2_structure(self):
        """Test Row 2 contains Date, Event Type, Status, Locked"""
        # This would require PDF parsing to verify correct fields
        # For now, ensure generation succeeds
        sample_data = {
            'demoId': '123456',
            'demoName': 'Test',
            'demoDate': '2025-01-01',
            'demoClassCode': '3',  # Should map to STANDARD
            'demoStatusCode': '2',  # Should map to APPROVED
            'demoLockInd': 'Y',  # Should show YES in bold
            'itemDetails': []
        }

        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp:
            output_path = tmp.name

        try:
            success = self.generator.generate_pdf(sample_data, output_path)
            self.assertTrue(success)

        finally:
            if os.path.exists(output_path):
                os.remove(output_path)


if __name__ == '__main__':
    unittest.main()
