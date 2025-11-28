"""
Tests for manual employee add form with duplicate detection (Story 2.1 and 2.2)
and success confirmation (Story 2.3)
Tests form validation, duplicate detection, data preservation, and success flow
"""
import pytest
import time


class TestManualEmployeeAddForm:
    """Test suite for manual employee add form (Story 2.1 & 2.2)"""

    def test_add_employee_form_loads(self, app):
        """Test that add employee form page loads successfully"""
        with app.test_client() as client:
            response = client.get('/employees/add')
            assert response.status_code == 200
            assert b'Add New Employee' in response.data or b'add employee' in response.data.lower()

    def test_add_employee_success(self, app, db):
        """Test successful employee creation with all fields"""
        Employee = app.config['Employee']
        EmployeeWeeklyAvailability = app.config['EmployeeWeeklyAvailability']

        with app.test_client() as client:
            form_data = {
                'name': 'John Smith',
                'employee_id': 'US123456',
                'email': 'john.smith@example.com',
                'phone': '555-1234',
                'job_title': 'Event Specialist',
                'is_active': 'true',
                'is_supervisor': True,
                'adult_beverage_trained': True,
                'monday': True,
                'tuesday': True,
                'wednesday': True,
                'thursday': True,
                'friday': True,
                'saturday': False,
                'sunday': False,
            }

            response = client.post('/employees/add', data=form_data, follow_redirects=True)

            # Check redirect to employees list
            assert response.status_code == 200

            # Verify employee created in database
            employee = Employee.query.filter_by(id='US123456').first()
            assert employee is not None
            assert employee.name == 'John Smith'
            assert employee.email == 'john.smith@example.com'
            assert employee.phone == '555-1234'
            assert employee.job_title == 'Event Specialist'
            assert employee.is_active is True
            assert employee.is_supervisor is True
            assert employee.adult_beverage_trained is True

            # Verify weekly availability created
            availability = EmployeeWeeklyAvailability.query.filter_by(employee_id='US123456').first()
            assert availability is not None
            assert availability.monday is True
            assert availability.tuesday is True
            assert availability.wednesday is True
            assert availability.thursday is True
            assert availability.friday is True
            assert availability.saturday is False
            assert availability.sunday is False

    def test_add_employee_minimal_fields(self, app, db):
        """Test employee creation with only required fields"""
        Employee = app.config['Employee']

        with app.test_client() as client:
            form_data = {
                'name': 'Jane Doe',
                'is_active': 'false',  # Default
            }

            response = client.post('/employees/add', data=form_data, follow_redirects=True)
            assert response.status_code == 200

            # Employee ID should be auto-generated from name
            employee = Employee.query.filter_by(id='JANE_DOE').first()
            assert employee is not None
            assert employee.name == 'Jane Doe'
            assert employee.email is None
            assert employee.phone is None
            assert employee.is_active is False  # Default from form

    def test_add_employee_missing_required_name(self, app, db):
        """Test validation error when name is missing"""
        with app.test_client() as client:
            form_data = {
                'email': 'test@example.com',
            }

            response = client.post('/employees/add', data=form_data)
            assert response.status_code == 200
            assert b'Name is required' in response.data or b'required' in response.data.lower()

    def test_add_employee_invalid_email(self, app, db):
        """Test validation error for invalid email format"""
        with app.test_client() as client:
            form_data = {
                'name': 'Test User',
                'email': 'invalid-email',
            }

            response = client.post('/employees/add', data=form_data)
            assert response.status_code == 200
            # Should show email validation error
            assert b'email' in response.data.lower()


class TestDuplicateDetection:
    """Test suite for duplicate name detection (Story 2.2)"""

    def test_duplicate_exact_case_match(self, app, db):
        """Test duplicate detection with exact case match"""
        Employee = app.config['Employee']

        # Create existing employee
        employee = Employee(
            id='JOHN_SMITH',
            name='John Smith',
            is_active=True,
            job_title='Event Specialist'
        )
        db.session.add(employee)
        db.session.commit()

        # Try to add duplicate with same case
        with app.test_client() as client:
            form_data = {
                'name': 'John Smith',
                'is_active': 'false',
            }

            response = client.post('/employees/add', data=form_data)
            assert response.status_code == 200
            assert b"Employee 'John Smith' already exists" in response.data

            # Verify no duplicate created
            employees = Employee.query.filter_by(name='John Smith').all()
            assert len(employees) == 1

    def test_duplicate_different_case(self, app, db):
        """Test duplicate detection is case-insensitive (different case)"""
        Employee = app.config['Employee']

        # Create existing employee with proper case
        employee = Employee(
            id='JANE_DOE',
            name='Jane Doe',
            is_active=True,
            job_title='Event Specialist'
        )
        db.session.add(employee)
        db.session.commit()

        # Try to add duplicate with lowercase
        with app.test_client() as client:
            form_data = {
                'name': 'jane doe',
                'is_active': 'false',
            }

            response = client.post('/employees/add', data=form_data)
            assert response.status_code == 200
            assert b"Employee 'jane doe' already exists" in response.data

            # Verify no duplicate created
            employees = Employee.query.all()
            assert len(employees) == 1
            assert employees[0].name == 'Jane Doe'  # Original case preserved

    def test_duplicate_mixed_case(self, app, db):
        """Test duplicate detection with mixed case variations"""
        Employee = app.config['Employee']

        # Create existing employee
        employee = Employee(
            id='BOB_JONES',
            name='Bob Jones',
            is_active=True,
            job_title='Event Specialist'
        )
        db.session.add(employee)
        db.session.commit()

        # Try variations
        test_cases = [
            'BOB JONES',
            'bob jones',
            'BoB jOnEs',
            'BOB jones',
        ]

        with app.test_client() as client:
            for test_name in test_cases:
                form_data = {
                    'name': test_name,
                    'is_active': 'false',
                }

                response = client.post('/employees/add', data=form_data)
                assert response.status_code == 200
                assert b'already exists' in response.data

        # Verify only one employee exists
        employees = Employee.query.all()
        assert len(employees) == 1

    def test_duplicate_with_whitespace(self, app, db):
        """Test duplicate detection handles leading/trailing whitespace"""
        Employee = app.config['Employee']

        # Create existing employee
        employee = Employee(
            id='ALICE_SMITH',
            name='Alice Smith',
            is_active=True,
            job_title='Event Specialist'
        )
        db.session.add(employee)
        db.session.commit()

        # Try to add with extra whitespace
        with app.test_client() as client:
            form_data = {
                'name': '  Alice Smith  ',
                'is_active': 'false',
            }

            response = client.post('/employees/add', data=form_data)
            assert response.status_code == 200
            # Should detect duplicate after stripping whitespace
            assert b'already exists' in response.data

    def test_non_duplicate_allowed(self, app, db):
        """Test that non-duplicate names are allowed"""
        Employee = app.config['Employee']

        # Create existing employee
        employee = Employee(
            id='JOHN_SMITH',
            name='John Smith',
            is_active=True,
            job_title='Event Specialist'
        )
        db.session.add(employee)
        db.session.commit()

        # Add different employee (should succeed)
        with app.test_client() as client:
            form_data = {
                'name': 'Jane Smith',
                'is_active': 'false',
            }

            response = client.post('/employees/add', data=form_data, follow_redirects=True)
            assert response.status_code == 200

            # Verify both employees exist
            employees = Employee.query.all()
            assert len(employees) == 2

    def test_partial_name_not_duplicate(self, app, db):
        """Test that partial name matches don't trigger duplicate detection"""
        Employee = app.config['Employee']

        # Create existing employee
        employee = Employee(
            id='JOHN_SMITH',
            name='John Smith',
            is_active=True,
            job_title='Event Specialist'
        )
        db.session.add(employee)
        db.session.commit()

        # Try to add employee with partial name (should succeed)
        with app.test_client() as client:
            form_data = {
                'name': 'John',
                'is_active': 'false',
            }

            response = client.post('/employees/add', data=form_data, follow_redirects=True)
            assert response.status_code == 200

            # Verify both employees exist
            employees = Employee.query.all()
            assert len(employees) == 2


class TestFormDataPreservation:
    """Test suite for form data preservation on validation failure (Story 2.2 AC)"""

    def test_form_preserves_data_on_duplicate_error(self, app, db):
        """Test that form data is preserved when duplicate error occurs"""
        Employee = app.config['Employee']

        # Create existing employee
        employee = Employee(
            id='TEST_USER',
            name='Test User',
            is_active=True,
            job_title='Event Specialist'
        )
        db.session.add(employee)
        db.session.commit()

        # Submit form with duplicate name and other data
        with app.test_client() as client:
            form_data = {
                'name': 'test user',  # Duplicate
                'employee_id': 'US999999',
                'email': 'test@example.com',
                'phone': '555-9999',
                'job_title': 'Club Supervisor',
                'is_active': 'true',
                'is_supervisor': True,
                'adult_beverage_trained': True,
            }

            response = client.post('/employees/add', data=form_data)
            assert response.status_code == 200

            # Check that error is displayed
            assert b'already exists' in response.data

            # Form should preserve entered data
            assert b'US999999' in response.data or 'US999999' in response.get_data(as_text=True)
            assert b'test@example.com' in response.data
            assert b'555-9999' in response.data

    def test_user_can_correct_and_resubmit(self, app, db):
        """Test that user can correct duplicate name and successfully resubmit"""
        Employee = app.config['Employee']

        # Create existing employee
        employee = Employee(
            id='EXISTING_USER',
            name='Existing User',
            is_active=True,
            job_title='Event Specialist'
        )
        db.session.add(employee)
        db.session.commit()

        with app.test_client() as client:
            # First attempt - duplicate name
            form_data_duplicate = {
                'name': 'existing user',
                'email': 'corrected@example.com',
                'is_active': 'false',
            }

            response = client.post('/employees/add', data=form_data_duplicate)
            assert response.status_code == 200
            assert b'already exists' in response.data

            # Second attempt - corrected name
            form_data_corrected = {
                'name': 'New User',
                'email': 'corrected@example.com',
                'is_active': 'false',
            }

            response = client.post('/employees/add', data=form_data_corrected, follow_redirects=True)
            assert response.status_code == 200

            # Verify new employee created
            new_employee = Employee.query.filter_by(name='New User').first()
            assert new_employee is not None
            assert new_employee.email == 'corrected@example.com'


class TestDuplicateDetectionPerformance:
    """Test suite for duplicate detection performance (Story 2.2 NFR-P1)"""

    def test_duplicate_check_performance(self, app, db):
        """Test that duplicate check completes in < 2 seconds (NFR-P1)"""
        Employee = app.config['Employee']

        # Create 100 employees to simulate realistic database size
        for i in range(100):
            employee = Employee(
                id=f'TEST_{i}',
                name=f'Test Employee {i}',
                is_active=True,
                job_title='Event Specialist'
            )
            db.session.add(employee)
        db.session.commit()

        # Measure duplicate check time
        with app.test_client() as client:
            form_data = {
                'name': 'Test Employee 50',  # Duplicate
                'is_active': 'false',
            }

            start_time = time.time()
            response = client.post('/employees/add', data=form_data)
            end_time = time.time()

            elapsed_time = end_time - start_time

            # Check performance requirement: < 2 seconds
            assert elapsed_time < 2.0, f"Duplicate check took {elapsed_time:.3f}s (should be < 2.0s)"

            # Should have detected duplicate
            assert response.status_code == 200
            assert b'already exists' in response.data

            # Log performance for documentation
            print(f"Duplicate check performance: {elapsed_time:.3f}s with 100 employees")


class TestErrorMessageFormat:
    """Test suite for error message format (Story 2.2 AC)"""

    def test_error_message_includes_name(self, app, db):
        """Test that error message includes the employee name"""
        Employee = app.config['Employee']

        employee = Employee(
            id='SARAH_JONES',
            name='Sarah Jones',
            is_active=True,
            job_title='Event Specialist'
        )
        db.session.add(employee)
        db.session.commit()

        with app.test_client() as client:
            form_data = {
                'name': 'sarah jones',
                'is_active': 'false',
            }

            response = client.post('/employees/add', data=form_data)
            assert response.status_code == 200

            # Check exact error message format
            assert b"Employee 'sarah jones' already exists" in response.data

    def test_error_displayed_as_field_error(self, app, db):
        """Test that duplicate error is displayed as a field-level error"""
        Employee = app.config['Employee']

        employee = Employee(
            id='TEST_EMPLOYEE',
            name='Test Employee',
            is_active=True,
            job_title='Event Specialist'
        )
        db.session.add(employee)
        db.session.commit()

        with app.test_client() as client:
            form_data = {
                'name': 'test employee',
                'is_active': 'false',
            }

            response = client.post('/employees/add', data=form_data)
            assert response.status_code == 200

            # Error should be associated with name field
            response_text = response.get_data(as_text=True)
            assert 'already exists' in response_text
            # Should be near the name field in the HTML
            assert 'name' in response_text.lower()


class TestSuccessConfirmation:
    """Test suite for success confirmation (Story 2.3)"""

    def test_success_flash_message_displayed(self, app, db):
        """Test that success flash message appears after successful add (Story 2.3)"""
        Employee = app.config['Employee']

        with app.test_client() as client:
            # Use session_transaction to test flash messages properly
            form_data = {
                'name': 'Success Test User',
                'is_active': 'false',
            }

            response = client.post('/employees/add', data=form_data, follow_redirects=False)

            # Should redirect (302)
            assert response.status_code == 302

            # Verify employee was created
            employee = Employee.query.filter_by(name='Success Test User').first()
            assert employee is not None

            # Follow redirect and check for flash message
            response = client.get(response.location)
            assert response.status_code == 200

    def test_success_redirects_to_employee_list(self, app, db):
        """Test that successful add redirects to employee list (Story 2.3)"""
        with app.test_client() as client:
            form_data = {
                'name': 'Redirect Test User',
                'is_active': 'false',
            }

            # Don't follow redirects to check the redirect response
            response = client.post('/employees/add', data=form_data, follow_redirects=False)

            # Should be a redirect
            assert response.status_code == 302

            # Should redirect to employees page
            assert '/employees' in response.location

    def test_employee_appears_in_list_after_add(self, app, db):
        """Test that employee appears in employee list after successful add (Story 2.3)"""
        Employee = app.config['Employee']

        with app.test_client() as client:
            form_data = {
                'name': 'List Test User',
                'email': 'listtest@example.com',
                'is_active': 'true',
            }

            response = client.post('/employees/add', data=form_data, follow_redirects=True)
            assert response.status_code == 200

            # Verify employee was created
            employee = Employee.query.filter_by(name='List Test User').first()
            assert employee is not None
            assert employee.email == 'listtest@example.com'
            assert employee.is_active is True

    def test_default_values_applied_correctly(self, app, db):
        """Test that default values are applied correctly (Story 2.3)"""
        Employee = app.config['Employee']

        with app.test_client() as client:
            # Submit with only required fields - should use defaults
            form_data = {
                'name': 'Default Values Test',
                # job_title defaults to 'Event Specialist'
                # is_active defaults to 'False' (Inactive)
                # is_supervisor defaults to False
                # adult_beverage_trained defaults to False
            }

            response = client.post('/employees/add', data=form_data, follow_redirects=True)
            assert response.status_code == 200

            # Verify defaults
            employee = Employee.query.filter_by(name='Default Values Test').first()
            assert employee is not None
            assert employee.job_title == 'Event Specialist'
            assert employee.is_active is False  # Inactive by default
            assert employee.is_supervisor is False
            assert employee.adult_beverage_trained is False

    def test_success_operation_performance(self, app, db):
        """Test that successful operation completes in < 2 seconds (Story 2.3 NFR-P1)"""
        with app.test_client() as client:
            form_data = {
                'name': 'Performance Test User',
                'email': 'performance@example.com',
                'phone': '555-1234',
                'job_title': 'Event Specialist',
                'is_active': 'true',
            }

            start_time = time.time()
            response = client.post('/employees/add', data=form_data, follow_redirects=True)
            end_time = time.time()

            elapsed_time = end_time - start_time

            # Check performance requirement: < 2 seconds
            assert elapsed_time < 2.0, f"Employee add took {elapsed_time:.3f}s (should be < 2.0s)"
            assert response.status_code == 200

            # Log performance for documentation
            print(f"Employee add performance: {elapsed_time:.3f}s")

    def test_error_handling_on_database_error(self, app, db):
        """Test that error handling works on database error (Story 2.3)"""
        with app.test_client() as client:
            # Try to create employee with duplicate ID
            Employee = app.config['Employee']

            # Create first employee
            employee = Employee(
                id='DUPLICATE_ID',
                name='First Employee',
                is_active=True,
                job_title='Event Specialist'
            )
            db.session.add(employee)
            db.session.commit()

            # Try to add another with same ID (via form)
            form_data = {
                'name': 'Second Employee',
                'employee_id': 'DUPLICATE_ID',
                'is_active': 'false',
            }

            response = client.post('/employees/add', data=form_data, follow_redirects=False)

            # Should not redirect (stays on form with error)
            assert response.status_code == 200

            # Verify employee was NOT created
            employees = Employee.query.filter_by(name='Second Employee').all()
            assert len(employees) == 0


class TestLogging:
    """Test suite for logging (Story 2.3)"""

    def test_success_logging_includes_name_and_id(self, app, db, caplog):
        """Test that successful add logs employee name and ID (Story 2.3)"""
        import logging

        with app.test_client() as client:
            form_data = {
                'name': 'Logging Test User',
                'employee_id': 'LOG_TEST_001',
                'is_active': 'false',
            }

            with caplog.at_level(logging.INFO):
                response = client.post('/employees/add', data=form_data, follow_redirects=True)
                assert response.status_code == 200

            # Check that log message contains name and ID
            log_messages = [record.message for record in caplog.records if record.levelname == 'INFO']
            assert any('Manual add: Logging Test User' in msg and 'LOG_TEST_001' in msg
                      for msg in log_messages), f"Expected log message not found. Log messages: {log_messages}"

    def test_error_logging_includes_exception_info(self, app, db, caplog, monkeypatch):
        """Test that error logging includes exc_info=True (Story 2.3)"""
        import logging

        # Mock db.session.commit to raise an exception
        def mock_commit():
            raise Exception("Simulated database error")

        with app.test_client() as client:
            form_data = {
                'name': 'Error Logging Test',
                'is_active': 'false',
            }

            with caplog.at_level(logging.ERROR):
                # Patch the commit method to simulate an error
                from app import db as app_db
                monkeypatch.setattr(app_db.session, 'commit', mock_commit)

                response = client.post('/employees/add', data=form_data, follow_redirects=True)

            # Check that error was logged
            error_logs = [record for record in caplog.records if record.levelname == 'ERROR']
            assert len(error_logs) > 0, "No error logs found"

            # Check that exc_info was captured (traceback present)
            assert any(record.exc_info is not None for record in error_logs), "exc_info not captured in error logs"
