"""
Employees routes blueprint
Handles employee management, availability, and time off operations
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app
from scheduler_app.routes.auth import require_authentication
from datetime import datetime, timedelta

# Create blueprint
employees_bp = Blueprint('employees', __name__)


@employees_bp.route('/employees')
def employees():
    """Display employee management page"""
    Employee = current_app.config['Employee']
    employees = Employee.query.order_by(Employee.name).all()
    return render_template('employees.html', employees=employees)


@employees_bp.route('/api/employees', methods=['GET', 'POST'])
@employees_bp.route('/api/employees/<employee_id>', methods=['DELETE'])
def manage_employees(employee_id=None):
    db = current_app.extensions['sqlalchemy']
    Employee = current_app.config['Employee']
    Schedule = current_app.config['Schedule']
    EmployeeAvailability = current_app.config['EmployeeAvailability']
    EmployeeWeeklyAvailability = current_app.config['EmployeeWeeklyAvailability']

    if request.method == 'GET':
        # Get all employees with their weekly availability
        employees_data = []
        employees = Employee.query.order_by(Employee.name).all()

        for emp in employees:
            weekly_availability = EmployeeWeeklyAvailability.query.filter_by(employee_id=emp.id).first()
            employee_data = {
                'id': emp.id,
                'name': emp.name,
                'email': emp.email,
                'phone': emp.phone,
                'is_active': emp.is_active,
                'is_supervisor': emp.is_supervisor,
                'job_title': emp.job_title,
                'adult_beverage_trained': emp.adult_beverage_trained,
                'weekly_availability': {
                    'monday': weekly_availability.monday if weekly_availability else True,
                    'tuesday': weekly_availability.tuesday if weekly_availability else True,
                    'wednesday': weekly_availability.wednesday if weekly_availability else True,
                    'thursday': weekly_availability.thursday if weekly_availability else True,
                    'friday': weekly_availability.friday if weekly_availability else True,
                    'saturday': weekly_availability.saturday if weekly_availability else True,
                    'sunday': weekly_availability.sunday if weekly_availability else True,
                } if weekly_availability else {
                    'monday': True, 'tuesday': True, 'wednesday': True, 'thursday': True,
                    'friday': True, 'saturday': True, 'sunday': True
                }
            }
            employees_data.append(employee_data)

        return jsonify(employees_data)

    elif request.method == 'POST':
        # Add or update employee
        data = request.get_json()

        if not data.get('name'):
            return jsonify({'error': 'Employee name is required'}), 400

        # Use provided ID or generate from name if not provided
        employee_id = data.get('id') or data['name'].upper().replace(' ', '_')

        try:
            # Check if we're editing an existing employee (based on the editing flag)
            editing_employee_id = data.get('editing_employee_id')  # This will be set by frontend for edits

            if editing_employee_id and editing_employee_id != employee_id:
                # This is an ID change - need to handle it specially
                old_employee = Employee.query.filter_by(id=editing_employee_id).first()
                if old_employee:
                    # Check if new ID already exists
                    if Employee.query.filter_by(id=employee_id).first():
                        return jsonify({'error': f'Employee ID {employee_id} already exists'}), 400

                    # Update related records first
                    Schedule.query.filter_by(employee_id=editing_employee_id).update({'employee_id': employee_id})
                    EmployeeAvailability.query.filter_by(employee_id=editing_employee_id).update({'employee_id': employee_id})
                    EmployeeWeeklyAvailability.query.filter_by(employee_id=editing_employee_id).update({'employee_id': employee_id})

                    # Delete old employee record
                    db.session.delete(old_employee)

                    # Create new employee with new ID
                    employee = Employee(
                        id=employee_id,
                        name=data['name'],
                        email=data.get('email'),
                        phone=data.get('phone'),
                        is_active=data.get('is_active', True),
                        is_supervisor=data.get('is_supervisor', False),
                        job_title=data.get('job_title', 'Event Specialist'),
                        adult_beverage_trained=data.get('adult_beverage_trained', False)
                    )
                    db.session.add(employee)
                else:
                    return jsonify({'error': 'Original employee not found'}), 404
            else:
                # Check if employee exists
                employee = Employee.query.filter_by(id=employee_id).first()

                if employee:
                    # Update existing employee
                    employee.name = data['name']
                    employee.email = data.get('email')
                    employee.phone = data.get('phone')
                    employee.is_active = data.get('is_active', True)
                    employee.is_supervisor = data.get('is_supervisor', False)
                    employee.job_title = data.get('job_title', 'Event Specialist')
                    employee.adult_beverage_trained = data.get('adult_beverage_trained', False)
                else:
                    # Create new employee
                    employee = Employee(
                        id=employee_id,
                        name=data['name'],
                        email=data.get('email'),
                        phone=data.get('phone'),
                        is_active=data.get('is_active', True),
                        is_supervisor=data.get('is_supervisor', False),
                        job_title=data.get('job_title', 'Event Specialist'),
                        adult_beverage_trained=data.get('adult_beverage_trained', False)
                    )
                    db.session.add(employee)

            # Handle weekly availability
            if 'weekly_availability' in data:
                availability_data = data['weekly_availability']
                weekly_availability = EmployeeWeeklyAvailability.query.filter_by(employee_id=employee_id).first()

                if weekly_availability:
                    # Update existing availability
                    weekly_availability.monday = availability_data.get('monday', True)
                    weekly_availability.tuesday = availability_data.get('tuesday', True)
                    weekly_availability.wednesday = availability_data.get('wednesday', True)
                    weekly_availability.thursday = availability_data.get('thursday', True)
                    weekly_availability.friday = availability_data.get('friday', True)
                    weekly_availability.saturday = availability_data.get('saturday', True)
                    weekly_availability.sunday = availability_data.get('sunday', True)
                else:
                    # Create new weekly availability
                    weekly_availability = EmployeeWeeklyAvailability(
                        employee_id=employee_id,
                        monday=availability_data.get('monday', True),
                        tuesday=availability_data.get('tuesday', True),
                        wednesday=availability_data.get('wednesday', True),
                        thursday=availability_data.get('thursday', True),
                        friday=availability_data.get('friday', True),
                        saturday=availability_data.get('saturday', True),
                        sunday=availability_data.get('sunday', True)
                    )
                    db.session.add(weekly_availability)

            db.session.commit()
            return jsonify({'message': 'Employee saved successfully', 'employee_id': employee_id})

        except Exception as e:
            db.session.rollback()
            return jsonify({'error': f'Database error: {str(e)}'}), 500

    elif request.method == 'DELETE':
        # Delete employee
        if not employee_id:
            return jsonify({'error': 'Employee ID is required'}), 400

        try:
            # Find the employee
            employee = Employee.query.filter_by(id=employee_id).first()
            if not employee:
                return jsonify({'error': 'Employee not found'}), 404

            # Check if employee has any scheduled events
            scheduled_events = Schedule.query.filter_by(employee_id=employee_id).count()
            if scheduled_events > 0:
                return jsonify({'error': f'Cannot delete employee with {scheduled_events} scheduled events. Deactivate instead.'}), 400

            # Delete related records first
            EmployeeWeeklyAvailability.query.filter_by(employee_id=employee_id).delete()
            EmployeeAvailability.query.filter_by(employee_id=employee_id).delete()

            # Delete the employee
            db.session.delete(employee)
            db.session.commit()

            return jsonify({'message': f'Employee {employee.name} deleted successfully'})

        except Exception as e:
            db.session.rollback()
            return jsonify({'error': f'Database error: {str(e)}'}), 500


@employees_bp.route('/api/employees/<employee_id>/availability', methods=['GET', 'POST'])
def employee_availability(employee_id):
    """Manage specific date availability for an employee"""
    db = current_app.extensions['sqlalchemy']
    Employee = current_app.config['Employee']
    EmployeeAvailability = current_app.config['EmployeeAvailability']

    employee = Employee.query.filter_by(id=employee_id).first()
    if not employee:
        return jsonify({'error': 'Employee not found'}), 404

    if request.method == 'GET':
        # Get specific date availabilities for the employee
        availabilities = EmployeeAvailability.query.filter_by(employee_id=employee_id).all()
        availability_data = []
        for avail in availabilities:
            availability_data.append({
                'date': avail.date.isoformat(),
                'is_available': avail.is_available,
                'reason': avail.reason
            })
        return jsonify(availability_data)

    elif request.method == 'POST':
        # Set specific date availability
        data = request.get_json()
        date_str = data.get('date')
        is_available = data.get('is_available', True)
        reason = data.get('reason', '')

        if not date_str:
            return jsonify({'error': 'Date is required'}), 400

        try:
            parsed_date = datetime.strptime(date_str, '%Y-%m-%d').date()

            # Check if availability record exists for this date
            availability = EmployeeAvailability.query.filter_by(
                employee_id=employee_id,
                date=parsed_date
            ).first()

            if availability:
                # Update existing record
                availability.is_available = is_available
                availability.reason = reason
            else:
                # Create new record
                availability = EmployeeAvailability(
                    employee_id=employee_id,
                    date=parsed_date,
                    is_available=is_available,
                    reason=reason
                )
                db.session.add(availability)

            db.session.commit()
            return jsonify({'message': 'Availability updated successfully'})

        except ValueError:
            return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD.'}), 400
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': f'Database error: {str(e)}'}), 500


@employees_bp.route('/api/populate_employees', methods=['POST'])
def populate_employees():
    """Populate employees from the provided JSON data"""
    db = current_app.extensions['sqlalchemy']
    Employee = current_app.config['Employee']
    EmployeeWeeklyAvailability = current_app.config['EmployeeWeeklyAvailability']

    try:
        employees_data = request.get_json()

        if not isinstance(employees_data, list):
            return jsonify({'error': 'Expected a list of employees'}), 400

        added_count = 0
        updated_count = 0

        for emp_data in employees_data:
            if not emp_data.get('name'):
                continue

            # Generate employee ID from name
            employee_id = emp_data['name'].upper().replace(' ', '_')

            # Check if employee exists
            employee = Employee.query.filter_by(id=employee_id).first()

            if employee:
                # Update existing employee
                employee.is_supervisor = emp_data.get('is_supervisor', False)
                updated_count += 1
            else:
                # Create new employee
                employee = Employee(
                    id=employee_id,
                    name=emp_data['name'],
                    is_supervisor=emp_data.get('is_supervisor', False),
                    is_active=True
                )
                db.session.add(employee)
                added_count += 1

            # Handle weekly availability
            if 'availability' in emp_data:
                availability_data = emp_data['availability']
                weekly_availability = EmployeeWeeklyAvailability.query.filter_by(employee_id=employee_id).first()

                # Map day names to lowercase
                day_mapping = {
                    'Monday': 'monday', 'Tuesday': 'tuesday', 'Wednesday': 'wednesday',
                    'Thursday': 'thursday', 'Friday': 'friday', 'Saturday': 'saturday', 'Sunday': 'sunday'
                }

                if weekly_availability:
                    # Update existing availability
                    for day_name, available in availability_data.items():
                        if day_name in day_mapping:
                            setattr(weekly_availability, day_mapping[day_name], available)
                else:
                    # Create new weekly availability
                    availability_kwargs = {'employee_id': employee_id}
                    for day_name, available in availability_data.items():
                        if day_name in day_mapping:
                            availability_kwargs[day_mapping[day_name]] = available

                    weekly_availability = EmployeeWeeklyAvailability(**availability_kwargs)
                    db.session.add(weekly_availability)

        db.session.commit()
        return jsonify({
            'message': f'Successfully processed {len(employees_data)} employees',
            'added': added_count,
            'updated': updated_count
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Error processing employees: {str(e)}'}), 500


@employees_bp.route('/api/employees/<employee_id>/time_off', methods=['GET', 'POST'])
def manage_employee_time_off(employee_id):
    """Manage time off requests for a specific employee"""
    db = current_app.extensions['sqlalchemy']
    Employee = current_app.config['Employee']
    EmployeeTimeOff = current_app.config['EmployeeTimeOff']

    employee = Employee.query.filter_by(id=employee_id).first()
    if not employee:
        return jsonify({'error': 'Employee not found'}), 404

    if request.method == 'GET':
        # Get all time off requests for the employee
        time_off_requests = EmployeeTimeOff.query.filter_by(employee_id=employee_id).order_by(EmployeeTimeOff.start_date.desc()).all()

        requests_data = []
        for req in time_off_requests:
            requests_data.append({
                'id': req.id,
                'start_date': req.start_date.isoformat(),
                'end_date': req.end_date.isoformat(),
                'reason': req.reason,
                'created_at': req.created_at.isoformat()
            })

        return jsonify(requests_data)

    elif request.method == 'POST':
        # Add new time off request
        data = request.get_json()

        start_date_str = data.get('start_date')
        end_date_str = data.get('end_date')
        reason = data.get('reason', '')

        if not start_date_str or not end_date_str:
            return jsonify({'error': 'Start date and end date are required'}), 400

        try:
            from datetime import datetime, date
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()

            if start_date > end_date:
                return jsonify({'error': 'Start date cannot be after end date'}), 400

            # Check for overlapping time off requests
            overlapping = EmployeeTimeOff.query.filter(
                EmployeeTimeOff.employee_id == employee_id,
                EmployeeTimeOff.start_date <= end_date,
                EmployeeTimeOff.end_date >= start_date
            ).first()

            if overlapping:
                return jsonify({'error': f'Time off request overlaps with existing request from {overlapping.start_date} to {overlapping.end_date}'}), 400

            # Create new time off request
            time_off_request = EmployeeTimeOff(
                employee_id=employee_id,
                start_date=start_date,
                end_date=end_date,
                reason=reason
            )

            db.session.add(time_off_request)
            db.session.commit()

            return jsonify({
                'message': f'Time off request added for {employee.name} from {start_date} to {end_date}',
                'id': time_off_request.id
            })

        except ValueError:
            return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD.'}), 400
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': f'Database error: {str(e)}'}), 500


@employees_bp.route('/api/time_off/<int:time_off_id>', methods=['DELETE'])
def delete_time_off(time_off_id):
    """Delete a time off request"""
    db = current_app.extensions['sqlalchemy']
    Employee = current_app.config['Employee']
    EmployeeTimeOff = current_app.config['EmployeeTimeOff']

    time_off_request = EmployeeTimeOff.query.get(time_off_id)

    if not time_off_request:
        return jsonify({'error': 'Time off request not found'}), 404

    try:
        employee_name = Employee.query.get(time_off_request.employee_id).name
        db.session.delete(time_off_request)
        db.session.commit()

        return jsonify({
            'message': f'Time off request deleted for {employee_name} ({time_off_request.start_date} to {time_off_request.end_date})'
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Database error: {str(e)}'}), 500
