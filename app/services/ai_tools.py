"""
AI Tools Module

Defines all available tools/functions that the AI assistant can call.
Each tool maps to existing application functionality.
"""
from typing import Dict, List, Any
from datetime import datetime, date, timedelta
import logging
from difflib import SequenceMatcher

logger = logging.getLogger(__name__)


class AITools:
    """Registry and executor for AI assistant tools"""

    def __init__(self, db_session, models):
        """
        Initialize tools registry

        Args:
            db_session: SQLAlchemy database session
            models: Dictionary of database models
        """
        self.db = db_session
        self.models = models

    def get_tool_schemas(self) -> List[Dict[str, Any]]:
        """Get OpenAI/Anthropic compatible tool schemas"""
        return [
            # READ TOOLS
            {
                "type": "function",
                "function": {
                    "name": "verify_schedule",
                    "description": "Verify a schedule for a specific date to identify potential issues like missing staff, imbalanced shifts, or scheduling conflicts. Returns verification status and list of issues if any.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "date": {
                                "type": "string",
                                "description": "Date to verify in YYYY-MM-DD format or relative dates like 'tomorrow', 'next Monday', 'this Friday'"
                            }
                        },
                        "required": ["date"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "count_employees",
                    "description": "Count how many employees are scheduled to work on a specific date",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "date": {
                                "type": "string",
                                "description": "Date in YYYY-MM-DD format or relative dates like 'tomorrow', 'Wednesday', etc."
                            }
                        },
                        "required": ["date"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_schedule",
                    "description": "Get detailed schedule information for a specific date, including all events and employee assignments",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "date": {
                                "type": "string",
                                "description": "Date in YYYY-MM-DD format"
                            }
                        },
                        "required": ["date"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "check_time_off",
                    "description": "Check time-off requests for a specific date or employee",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "employee_name": {
                                "type": "string",
                                "description": "Employee name (optional, fuzzy matched if provided)"
                            },
                            "date": {
                                "type": "string",
                                "description": "Date to check (optional)"
                            }
                        }
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_unscheduled_events",
                    "description": "List all events that need to be scheduled",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "date_range": {
                                "type": "string",
                                "description": "Optional date range like 'this week', 'next week', 'today'"
                            }
                        }
                    }
                }
            },

            # WRITE TOOLS
            {
                "type": "function",
                "function": {
                    "name": "print_paperwork",
                    "description": "Generate and prepare daily paperwork PDF for a specific date",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "date": {
                                "type": "string",
                                "description": "Date for paperwork in YYYY-MM-DD format"
                            }
                        },
                        "required": ["date"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "request_time_off",
                    "description": "Create a time-off request for an employee",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "employee_name": {
                                "type": "string",
                                "description": "Name of the employee (will be fuzzy matched)"
                            },
                            "start_date": {
                                "type": "string",
                                "description": "Start date of time off in YYYY-MM-DD format"
                            },
                            "end_date": {
                                "type": "string",
                                "description": "End date of time off (same as start for single day)"
                            },
                            "reason": {
                                "type": "string",
                                "description": "Reason for time off (e.g., 'Doctor appointment', 'Vacation')"
                            }
                        },
                        "required": ["employee_name", "start_date", "end_date"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_employee_info",
                    "description": "Get detailed information about an employee including their schedule, availability, and job title",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "employee_name": {
                                "type": "string",
                                "description": "Employee name (fuzzy matched)"
                            }
                        },
                        "required": ["employee_name"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "list_employees",
                    "description": "List all active employees, optionally filtered by job title or availability",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "job_title": {
                                "type": "string",
                                "description": "Filter by job title (e.g., 'Lead Event Specialist', 'Club Supervisor')"
                            },
                            "available_on": {
                                "type": "string",
                                "description": "Filter by availability on a specific date"
                            }
                        }
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_schedule_summary",
                    "description": "Get a summary of schedules for a date range (e.g., this week, next week)",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "date_range": {
                                "type": "string",
                                "description": "Date range like 'this week', 'next week', 'this month'"
                            }
                        },
                        "required": ["date_range"]
                    }
                }
            }
        ]

    def execute_tool(self, tool_name: str, tool_args: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a tool by name

        Args:
            tool_name: Name of the tool to execute
            tool_args: Arguments for the tool

        Returns:
            Dictionary with execution results
        """
        # Map tool names to methods
        tool_map = {
            'verify_schedule': self._tool_verify_schedule,
            'count_employees': self._tool_count_employees,
            'get_schedule': self._tool_get_schedule,
            'check_time_off': self._tool_check_time_off,
            'get_unscheduled_events': self._tool_get_unscheduled_events,
            'print_paperwork': self._tool_print_paperwork,
            'request_time_off': self._tool_request_time_off,
            'get_employee_info': self._tool_get_employee_info,
            'list_employees': self._tool_list_employees,
            'get_schedule_summary': self._tool_get_schedule_summary,
        }

        if tool_name not in tool_map:
            return {
                'success': False,
                'message': f"Unknown tool: {tool_name}",
                'data': None
            }

        try:
            return tool_map[tool_name](tool_args)
        except Exception as e:
            logger.error(f"Error executing tool {tool_name}: {str(e)}", exc_info=True)
            return {
                'success': False,
                'message': f"Error executing {tool_name}: {str(e)}",
                'data': {'error': str(e)}
            }

    # ===== READ TOOLS =====

    def _tool_verify_schedule(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Verify schedule for a specific date"""
        date_str = args.get('date')
        parsed_date = self._parse_date(date_str)

        if not parsed_date:
            return {
                'success': False,
                'message': f"Could not parse date: {date_str}",
                'data': None
            }

        # Call schedule verification service
        from app.services.schedule_verification import ScheduleVerificationService
        service = ScheduleVerificationService(self.db, self.models)
        result = service.verify_schedule(parsed_date)

        # Format response
        status_messages = {
            'pass': '✅ All clear!',
            'warning': '⚠️ Warnings found',
            'fail': '❌ Critical issues found'
        }

        status_emoji = status_messages.get(result.status, '')

        message = f"{status_emoji} Verified schedule for {parsed_date.strftime('%A, %B %d, %Y')}. "
        message += f"Status: {result.status.title()}. "
        message += f"{result.summary['total_events']} events, {result.summary['total_employees']} employees. "

        if result.summary['critical_issues'] > 0:
            message += f"{result.summary['critical_issues']} critical issue(s) found."
        elif result.summary['warnings'] > 0:
            message += f"{result.summary['warnings']} warning(s) found."
        else:
            message += "No issues found."

        return {
            'success': True,
            'message': message,
            'data': {
                'verification_result': result.to_dict(),
                'date': parsed_date.isoformat()
            },
            'suggested_actions': [
                {'label': 'View Full Report', 'action': f'/schedule-verification?date={parsed_date.isoformat()}'}
            ] if result.issues else None
        }

    def _tool_count_employees(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Count employees scheduled for a date"""
        date_str = args.get('date')
        parsed_date = self._parse_date(date_str)

        if not parsed_date:
            return {
                'success': False,
                'message': f"Could not parse date: {date_str}",
                'data': None
            }

        Schedule = self.models['Schedule']

        # Count distinct employees
        count = self.db.query(Schedule.employee_id).filter(
            self.db.func.date(Schedule.schedule_datetime) == parsed_date
        ).distinct().count()

        day_name = parsed_date.strftime('%A, %B %d')
        message = f"📊 {count} employee{'s' if count != 1 else ''} scheduled for {day_name}."

        return {
            'success': True,
            'message': message,
            'data': {
                'count': count,
                'date': parsed_date.isoformat()
            }
        }

    def _tool_get_schedule(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Get detailed schedule for a date"""
        date_str = args.get('date')
        parsed_date = self._parse_date(date_str)

        if not parsed_date:
            return {
                'success': False,
                'message': f"Could not parse date: {date_str}",
                'data': None
            }

        Schedule = self.models['Schedule']
        Event = self.models['Event']
        Employee = self.models['Employee']

        # Get all schedules for the date
        schedules = self.db.query(Schedule, Event, Employee).join(
            Event, Schedule.event_ref_num == Event.project_ref_num
        ).join(
            Employee, Schedule.employee_id == Employee.id
        ).filter(
            self.db.func.date(Schedule.schedule_datetime) == parsed_date
        ).order_by(Schedule.schedule_datetime).all()

        if not schedules:
            return {
                'success': True,
                'message': f"No events scheduled for {parsed_date.strftime('%A, %B %d')}.",
                'data': {'schedules': [], 'date': parsed_date.isoformat()}
            }

        # Format schedule data
        schedule_list = []
        for sched, event, emp in schedules:
            schedule_list.append({
                'time': sched.schedule_datetime.strftime('%I:%M %p'),
                'employee': emp.name,
                'job_title': emp.job_title,
                'event': event.project_name,
                'event_type': event.event_type
            })

        message = f"📅 Schedule for {parsed_date.strftime('%A, %B %d')}:\n"
        message += f"Total: {len(schedules)} event(s)\n"

        # Group by time
        from collections import defaultdict
        by_time = defaultdict(list)
        for item in schedule_list:
            by_time[item['time']].append(f"{item['employee']} - {item['event_type']}")

        for time, events in sorted(by_time.items())[:5]:  # Show first 5 time slots
            message += f"{time}: {', '.join(events)}\n"

        return {
            'success': True,
            'message': message.strip(),
            'data': {
                'schedules': schedule_list,
                'date': parsed_date.isoformat(),
                'total': len(schedules)
            },
            'suggested_actions': [
                {'label': 'View Full Schedule', 'action': f'/daily-view/{parsed_date.isoformat()}'}
            ]
        }

    def _tool_check_time_off(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Check time-off requests"""
        employee_name = args.get('employee_name')
        date_str = args.get('date')

        EmployeeTimeOff = self.models['EmployeeTimeOff']
        Employee = self.models['Employee']

        query = self.db.query(EmployeeTimeOff, Employee).join(
            Employee, EmployeeTimeOff.employee_id == Employee.id
        )

        # Filter by employee if provided
        if employee_name:
            matched_employee = self._find_employee_by_name(employee_name)
            if matched_employee:
                query = query.filter(Employee.id == matched_employee.id)
            else:
                return {
                    'success': False,
                    'message': f"Could not find employee: {employee_name}",
                    'data': None
                }

        # Filter by date if provided
        if date_str:
            parsed_date = self._parse_date(date_str)
            if parsed_date:
                query = query.filter(
                    EmployeeTimeOff.start_date <= parsed_date,
                    EmployeeTimeOff.end_date >= parsed_date
                )

        time_off_records = query.all()

        if not time_off_records:
            message = "No time-off requests found"
            if employee_name:
                message += f" for {employee_name}"
            if date_str:
                message += f" on {date_str}"
            message += "."

            return {
                'success': True,
                'message': message,
                'data': {'time_off': []}
            }

        # Format results
        time_off_list = []
        for time_off, emp in time_off_records:
            time_off_list.append({
                'employee': emp.name,
                'start_date': time_off.start_date.isoformat(),
                'end_date': time_off.end_date.isoformat(),
                'reason': time_off.reason or 'Not specified'
            })

        message = f"📋 Found {len(time_off_list)} time-off request(s):\n"
        for i, to in enumerate(time_off_list[:3], 1):  # Show first 3
            message += f"{i}. {to['employee']}: {to['start_date']} to {to['end_date']} ({to['reason']})\n"

        if len(time_off_list) > 3:
            message += f"... and {len(time_off_list) - 3} more"

        return {
            'success': True,
            'message': message.strip(),
            'data': {'time_off': time_off_list}
        }

    def _tool_get_unscheduled_events(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Get unscheduled events"""
        date_range = args.get('date_range', 'all')

        Event = self.models['Event']

        query = self.db.query(Event).filter(Event.is_scheduled == False)

        # Apply date range filter if specified
        if date_range and date_range != 'all':
            start_date, end_date = self._parse_date_range(date_range)
            if start_date and end_date:
                query = query.filter(
                    Event.start_datetime >= start_date,
                    Event.due_datetime <= end_date
                )

        unscheduled = query.all()

        if not unscheduled:
            return {
                'success': True,
                'message': "✅ No unscheduled events found.",
                'data': {'unscheduled': []}
            }

        # Format results
        event_list = []
        for event in unscheduled:
            event_list.append({
                'id': event.id,
                'name': event.project_name,
                'type': event.event_type,
                'start_date': event.start_datetime.date().isoformat(),
                'due_date': event.due_datetime.date().isoformat()
            })

        message = f"📌 Found {len(event_list)} unscheduled event(s)"
        if date_range and date_range != 'all':
            message += f" for {date_range}"
        message += "."

        return {
            'success': True,
            'message': message,
            'data': {'unscheduled': event_list, 'count': len(event_list)},
            'suggested_actions': [
                {'label': 'View Unscheduled Events', 'action': '/unscheduled'}
            ]
        }

    # ===== WRITE TOOLS =====

    def _tool_print_paperwork(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Generate daily paperwork"""
        date_str = args.get('date')
        parsed_date = self._parse_date(date_str)
        confirmed = args.get('_confirmed', False)

        if not parsed_date:
            return {
                'success': False,
                'message': f"Could not parse date: {date_str}",
                'data': None
            }

        if not confirmed:
            # Require confirmation
            return {
                'success': True,
                'message': f"⚠️ Confirm: Generate paperwork PDF for {parsed_date.strftime('%A, %B %d, %Y')}?",
                'requires_confirmation': True,
                'confirmation_data': {
                    'tool_name': 'print_paperwork',
                    'tool_args': {'date': parsed_date.isoformat()},
                    'action': f"Generate paperwork for {parsed_date.strftime('%A, %B %d')}"
                }
            }

        # Generate paperwork (this would call the actual paperwork generation service)
        message = f"🖨️ Paperwork for {parsed_date.strftime('%A, %B %d')} is being generated. You can download it when ready."

        return {
            'success': True,
            'message': message,
            'data': {'date': parsed_date.isoformat(), 'status': 'generating'},
            'suggested_actions': [
                {'label': 'Download PDF', 'action': f'/admin/generate-paperwork?date={parsed_date.isoformat()}'}
            ]
        }

    def _tool_request_time_off(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Create time-off request"""
        employee_name = args.get('employee_name')
        start_date_str = args.get('start_date')
        end_date_str = args.get('end_date')
        reason = args.get('reason', '')
        confirmed = args.get('_confirmed', False)

        # Find employee
        employee = self._find_employee_by_name(employee_name)
        if not employee:
            return {
                'success': False,
                'message': f"Could not find employee: {employee_name}",
                'data': None
            }

        # Parse dates
        start_date = self._parse_date(start_date_str)
        end_date = self._parse_date(end_date_str)

        if not start_date or not end_date:
            return {
                'success': False,
                'message': "Invalid date format",
                'data': None
            }

        if not confirmed:
            # Require confirmation
            return {
                'success': True,
                'message': f"⚠️ Confirm: Add time-off for {employee.name} from {start_date.strftime('%A, %B %d')} to {end_date.strftime('%A, %B %d')}?\nReason: {reason or 'Not specified'}",
                'requires_confirmation': True,
                'confirmation_data': {
                    'tool_name': 'request_time_off',
                    'tool_args': {
                        'employee_name': employee.name,
                        'start_date': start_date.isoformat(),
                        'end_date': end_date.isoformat(),
                        'reason': reason
                    },
                    'action': f"Create time-off request for {employee.name}"
                }
            }

        # Create time-off request
        EmployeeTimeOff = self.models['EmployeeTimeOff']
        time_off = EmployeeTimeOff(
            employee_id=employee.id,
            start_date=start_date,
            end_date=end_date,
            reason=reason
        )
        self.db.add(time_off)
        self.db.commit()

        message = f"✅ Time-off request created for {employee.name} from {start_date.strftime('%b %d')} to {end_date.strftime('%b %d')}."
        if reason:
            message += f" Reason: {reason}"

        return {
            'success': True,
            'message': message,
            'data': {
                'employee': employee.name,
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
                'reason': reason
            }
        }

    def _tool_get_employee_info(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Get employee information"""
        employee_name = args.get('employee_name')

        employee = self._find_employee_by_name(employee_name)
        if not employee:
            return {
                'success': False,
                'message': f"Could not find employee: {employee_name}",
                'data': None
            }

        message = f"👤 {employee.name}\n"
        message += f"Job Title: {employee.job_title}\n"
        message += f"Status: {'Active' if employee.is_active else 'Inactive'}\n"
        if employee.email:
            message += f"Email: {employee.email}\n"
        if employee.phone:
            message += f"Phone: {employee.phone}"

        return {
            'success': True,
            'message': message.strip(),
            'data': {
                'id': employee.id,
                'name': employee.name,
                'job_title': employee.job_title,
                'email': employee.email,
                'phone': employee.phone,
                'is_active': employee.is_active
            }
        }

    def _tool_list_employees(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """List employees"""
        job_title = args.get('job_title')
        available_on = args.get('available_on')

        Employee = self.models['Employee']

        query = self.db.query(Employee).filter(Employee.is_active == True)

        # Filter by job title
        if job_title:
            query = query.filter(Employee.job_title.ilike(f'%{job_title}%'))

        # Filter by availability
        if available_on:
            parsed_date = self._parse_date(available_on)
            if parsed_date:
                # TODO: Add availability filtering logic
                pass

        employees = query.all()

        if not employees:
            return {
                'success': True,
                'message': "No employees found matching criteria.",
                'data': {'employees': []}
            }

        # Format results
        emp_list = []
        for emp in employees:
            emp_list.append({
                'id': emp.id,
                'name': emp.name,
                'job_title': emp.job_title
            })

        message = f"👥 Found {len(emp_list)} employee(s)"
        if job_title:
            message += f" with job title '{job_title}'"
        message += ":\n"

        for i, emp in enumerate(emp_list[:10], 1):
            message += f"{i}. {emp['name']} ({emp['job_title']})\n"

        if len(emp_list) > 10:
            message += f"... and {len(emp_list) - 10} more"

        return {
            'success': True,
            'message': message.strip(),
            'data': {'employees': emp_list, 'count': len(emp_list)}
        }

    def _tool_get_schedule_summary(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Get schedule summary for a date range"""
        date_range = args.get('date_range', 'this week')
        start_date, end_date = self._parse_date_range(date_range)

        if not start_date or not end_date:
            return {
                'success': False,
                'message': f"Could not parse date range: {date_range}",
                'data': None
            }

        Schedule = self.models['Schedule']
        Event = self.models['Event']

        # Count schedules per day
        from sqlalchemy import func
        daily_counts = self.db.query(
            func.date(Schedule.schedule_datetime).label('date'),
            func.count(Schedule.id).label('count')
        ).filter(
            Schedule.schedule_datetime >= start_date,
            Schedule.schedule_datetime <= end_date
        ).group_by(func.date(Schedule.schedule_datetime)).all()

        if not daily_counts:
            return {
                'success': True,
                'message': f"No schedules found for {date_range}.",
                'data': {'summary': []}
            }

        # Format results
        summary = []
        for day_date, count in daily_counts:
            summary.append({
                'date': day_date.isoformat(),
                'day_name': day_date.strftime('%A'),
                'event_count': count
            })

        message = f"📊 Schedule summary for {date_range}:\n"
        for item in summary:
            message += f"{item['day_name']}: {item['event_count']} events\n"

        total = sum(item['event_count'] for item in summary)
        message += f"\nTotal: {total} events across {len(summary)} days"

        return {
            'success': True,
            'message': message.strip(),
            'data': {'summary': summary, 'total': total}
        }

    # ===== UTILITY METHODS =====

    def _parse_date(self, date_str: str) -> Optional[date]:
        """Parse date string including relative dates"""
        if not date_str:
            return None

        date_str = date_str.lower().strip()
        today = date.today()

        # Handle relative dates
        if date_str == 'today':
            return today
        elif date_str == 'tomorrow':
            return today + timedelta(days=1)
        elif date_str == 'yesterday':
            return today - timedelta(days=1)
        elif 'next' in date_str:
            # Handle "next Monday", "next Friday", etc.
            for i, day in enumerate(['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']):
                if day in date_str:
                    days_ahead = i - today.weekday()
                    if days_ahead <= 0:
                        days_ahead += 7
                    return today + timedelta(days=days_ahead)
        elif 'this' in date_str:
            # Handle "this Wednesday", "this Friday", etc.
            for i, day in enumerate(['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']):
                if day in date_str:
                    days_ahead = i - today.weekday()
                    if days_ahead < 0:
                        days_ahead += 7
                    return today + timedelta(days=days_ahead)
        elif date_str in ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']:
            # Assume next occurrence
            day_index = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday'].index(date_str)
            days_ahead = day_index - today.weekday()
            if days_ahead <= 0:
                days_ahead += 7
            return today + timedelta(days=days_ahead)

        # Try parsing as YYYY-MM-DD
        try:
            return datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            pass

        # Try other common formats
        for fmt in ['%m/%d/%Y', '%m-%d-%Y', '%Y/%m/%d']:
            try:
                return datetime.strptime(date_str, fmt).date()
            except ValueError:
                continue

        return None

    def _parse_date_range(self, range_str: str) -> tuple:
        """Parse date range string"""
        range_str = range_str.lower().strip()
        today = date.today()

        if range_str == 'this week':
            start = today - timedelta(days=today.weekday())
            end = start + timedelta(days=6)
            return start, end
        elif range_str == 'next week':
            start = today - timedelta(days=today.weekday()) + timedelta(days=7)
            end = start + timedelta(days=6)
            return start, end
        elif range_str == 'this month':
            start = today.replace(day=1)
            next_month = start.replace(day=28) + timedelta(days=4)
            end = next_month - timedelta(days=next_month.day)
            return start, end

        return None, None

    def _find_employee_by_name(self, name: str):
        """Find employee by fuzzy matching name"""
        Employee = self.models['Employee']

        # First try exact match
        employee = self.db.query(Employee).filter(
            Employee.name.ilike(name)
        ).first()

        if employee:
            return employee

        # Fuzzy match
        all_employees = self.db.query(Employee).filter(Employee.is_active == True).all()

        best_match = None
        best_ratio = 0

        for emp in all_employees:
            ratio = SequenceMatcher(None, name.lower(), emp.name.lower()).ratio()
            if ratio > best_ratio:
                best_ratio = ratio
                best_match = emp

        # Return if similarity is above 60%
        if best_ratio > 0.6:
            return best_match

        return None
