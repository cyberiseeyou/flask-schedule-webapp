"""
Club 8135 Scheduling Rulebook Generator
Creates a comprehensive PDF with all scheduling rules and requirements
"""

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle,
    ListFlowable, ListItem, KeepTogether
)
from reportlab.pdfgen import canvas
from datetime import datetime

class NumberedCanvas(canvas.Canvas):
    """Custom canvas to add page numbers"""
    def __init__(self, *args, **kwargs):
        canvas.Canvas.__init__(self, *args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_number(num_pages)
            canvas.Canvas.showPage(self)
        canvas.Canvas.save(self)

    def draw_page_number(self, page_count):
        page = "Page %s of %s" % (self._pageNumber, page_count)
        self.setFont("Helvetica", 9)
        self.drawRightString(7.5*inch, 0.5*inch, page)


def create_rulebook():
    """Create the Club 8135 Scheduling Rulebook PDF"""

    # Create PDF
    filename = "Club_8135_Scheduling_Rulebook.pdf"
    doc = SimpleDocTemplate(
        filename,
        pagesize=letter,
        rightMargin=0.75*inch,
        leftMargin=0.75*inch,
        topMargin=0.75*inch,
        bottomMargin=1*inch
    )

    # Styles
    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Title'],
        fontSize=28,
        textColor=colors.HexColor('#1a365d'),
        spaceAfter=30,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )

    subtitle_style = ParagraphStyle(
        'Subtitle',
        parent=styles['Normal'],
        fontSize=14,
        textColor=colors.HexColor('#2d3748'),
        spaceAfter=12,
        alignment=TA_CENTER
    )

    heading1_style = ParagraphStyle(
        'CustomHeading1',
        parent=styles['Heading1'],
        fontSize=18,
        textColor=colors.HexColor('#1a365d'),
        spaceAfter=12,
        spaceBefore=12,
        fontName='Helvetica-Bold'
    )

    heading2_style = ParagraphStyle(
        'CustomHeading2',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor('#2c5282'),
        spaceAfter=10,
        spaceBefore=10,
        fontName='Helvetica-Bold'
    )

    heading3_style = ParagraphStyle(
        'CustomHeading3',
        parent=styles['Heading3'],
        fontSize=12,
        textColor=colors.HexColor('#2c5282'),
        spaceAfter=8,
        spaceBefore=8,
        fontName='Helvetica-Bold'
    )

    body_style = ParagraphStyle(
        'CustomBody',
        parent=styles['Normal'],
        fontSize=10,
        spaceAfter=6,
        alignment=TA_JUSTIFY
    )

    # Build content
    story = []

    # ===== COVER PAGE =====
    story.append(Spacer(1, 2*inch))
    story.append(Paragraph("CLUB 8135", title_style))
    story.append(Paragraph("Scheduling Rulebook", title_style))
    story.append(Spacer(1, 0.5*inch))
    story.append(Paragraph("Comprehensive Guide to Scheduling Requirements,", subtitle_style))
    story.append(Paragraph("Employee Availability, and Business Rules", subtitle_style))
    story.append(Spacer(1, 1*inch))
    story.append(Paragraph(f"Version 1.0 | {datetime.now().strftime('%B %Y')}", subtitle_style))
    story.append(PageBreak())

    # ===== TABLE OF CONTENTS =====
    story.append(Paragraph("Table of Contents", heading1_style))
    story.append(Spacer(1, 0.2*inch))

    toc_items = [
        "1. Introduction",
        "2. Auto-Scheduler Configuration",
        "3. Event Priority System",
        "4. Wave-Based Scheduling",
        "5. Employee Availability",
        "6. Days Off Management",
        "7. Position-Based Rules",
        "8. Event Duration Standards",
        "9. Daily Event Limits",
        "10. Time Slot Constraints",
        "11. Business Rules",
        "12. Conflict Resolution",
        "13. Validation Rules",
        "14. Rotation Management",
        "15. Time-Based Constraints",
        "16. Special Business Logic",
        "17. Configuration Constants",
        "18. Audit and Validation",
    ]

    for item in toc_items:
        story.append(Paragraph(item, body_style))

    story.append(PageBreak())

    # ===== SECTION 1: INTRODUCTION =====
    story.append(Paragraph("1. Introduction", heading1_style))
    story.append(Paragraph(
        "This rulebook documents all scheduling requirements, employee availability rules, "
        "and business constraints for Club 8135's automated scheduling system. The system "
        "implements a sophisticated constraint-based scheduling engine with multi-level "
        "priority handling, rotation management, and comprehensive validation.",
        body_style
    ))
    story.append(Spacer(1, 0.2*inch))

    story.append(Paragraph("System Overview", heading2_style))
    overview_data = [
        ['Component', 'Description'],
        ['Constraint Types', '11 different types (hard and soft)'],
        ['Scheduling Waves', '5-wave priority system with cascading'],
        ['Availability Tiers', '3-tier system (weekly, date-specific, overrides)'],
        ['Job Title Levels', '4 levels with role-based restrictions'],
        ['Rotation Types', '2 types (Juicer, Primary Lead)'],
    ]

    overview_table = Table(overview_data, colWidths=[2*inch, 4*inch])
    overview_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c5282')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('TOPPADDING', (0, 1), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
    ]))
    story.append(overview_table)
    story.append(PageBreak())

    # ===== SECTION 2: AUTO-SCHEDULER CONFIGURATION =====
    story.append(Paragraph("2. Auto-Scheduler Configuration", heading1_style))

    story.append(Paragraph("2.1 Scheduling Window", heading2_style))
    story.append(Paragraph(
        "<b>3-Day Buffer Rule:</b> The auto-scheduler does not schedule events within 3 days "
        "from today. This buffer allows for manual adjustments and prevents last-minute automatic changes.",
        body_style
    ))
    story.append(Paragraph(
        "<b>Formula:</b> Earliest Schedule Date = MAX(Event Start Date, Today + 3 Days)",
        body_style
    ))
    story.append(Spacer(1, 0.1*inch))

    story.append(Paragraph("2.2 File References", heading2_style))
    story.append(Paragraph(
        "Configuration: <i>services/scheduling_engine.py</i> (Lines 30-31, 266)<br/>"
        "Constant: <i>SCHEDULING_WINDOW_DAYS = 3</i>",
        body_style
    ))
    story.append(PageBreak())

    # ===== SECTION 3: EVENT PRIORITY SYSTEM =====
    story.append(Paragraph("3. Event Priority System", heading1_style))
    story.append(Paragraph(
        "Events are processed in strict priority order based on urgency and business importance. "
        "Higher priority events (lower numbers) are scheduled first and can bump lower priority events.",
        body_style
    ))
    story.append(Spacer(1, 0.2*inch))

    priority_data = [
        ['Priority', 'Event Type', 'Notes'],
        ['1', 'Juicer', 'Highest priority - 9-hour shifts'],
        ['2', 'Digital Setup', 'Must be completed before refresh'],
        ['3', 'Digital Refresh', 'Mid-priority digital maintenance'],
        ['4', 'Freeosk', 'Product sampling events'],
        ['5', 'Digital Teardown', 'Scheduled after 5:00 PM'],
        ['6', 'Core', 'Primary 6.5-hour shifts'],
        ['7', 'Supervisor', 'Paired with Core events'],
        ['8', 'Digitals', 'General digital maintenance'],
        ['9', 'Other', 'Lowest priority events'],
    ]

    priority_table = Table(priority_data, colWidths=[0.8*inch, 1.5*inch, 3.7*inch])
    priority_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c5282')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (0, -1), 'CENTER'),
        ('ALIGN', (1, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('TOPPADDING', (0, 1), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
    ]))
    story.append(priority_table)
    story.append(Spacer(1, 0.1*inch))
    story.append(Paragraph(
        "Reference: <i>services/scheduling_engine.py</i> (Lines 33-44)",
        body_style
    ))
    story.append(PageBreak())

    # ===== SECTION 4: WAVE-BASED SCHEDULING =====
    story.append(Paragraph("4. Wave-Based Scheduling System", heading1_style))
    story.append(Paragraph(
        "The scheduler processes events in 5 distinct waves. Each wave has specific employee "
        "assignment priorities and time slot allocations.",
        body_style
    ))
    story.append(Spacer(1, 0.2*inch))

    story.append(Paragraph("Wave 1: Juicer Events (Highest Priority)", heading2_style))
    story.append(Paragraph("• Rotation-based assignment to Juicer Baristas", body_style))
    story.append(Paragraph("• <b>CAN BUMP Core events</b> if Juicer has conflicts", body_style))
    story.append(Paragraph("• Default time: 9:00 AM (or 5:00 PM for surveys)", body_style))
    story.append(Paragraph("• Duration: 9 hours (540 minutes)", body_style))
    story.append(Spacer(1, 0.1*inch))

    story.append(Paragraph("Wave 2: Core Events (3 Sub-waves)", heading2_style))
    story.append(Paragraph("<b>Wave 2.1:</b> Lead Event Specialists (fill available days first)", body_style))
    story.append(Paragraph("<b>Wave 2.2:</b> Juicer Baristas (when not doing Juicer events that day)", body_style))
    story.append(Paragraph("<b>Wave 2.3:</b> Event Specialists", body_style))
    story.append(Paragraph("• Default time: 9:45 AM for Primary Leads", body_style))
    story.append(Paragraph("• Time slots rotate: 9:45, 10:30, 11:00, 11:30", body_style))
    story.append(Paragraph("• Supervisor events scheduled INLINE at 12:00 PM", body_style))
    story.append(Paragraph("• Duration: 6.5 hours (390 minutes)", body_style))
    story.append(Spacer(1, 0.1*inch))

    story.append(Paragraph("Wave 3: Freeosk Events", heading2_style))
    story.append(Paragraph("• Time: 9:00 AM", body_style))
    story.append(Paragraph("• Priority: Primary Lead → Other Leads → Club Supervisor", body_style))
    story.append(Paragraph("• Duration: 15 minutes", body_style))
    story.append(Spacer(1, 0.1*inch))

    story.append(Paragraph("Wave 4: Digital Events", heading2_style))
    story.append(Paragraph("<b>Setup/Refresh:</b> Times 9:15, 9:30, 9:45, 10:00 (only 4 slots, rotating)", body_style))
    story.append(Paragraph("<b>Teardown:</b> 5:00 PM+ in 15-minute intervals", body_style))
    story.append(Paragraph("• Priority: Primary/Secondary Lead → Club Supervisor", body_style))
    story.append(Paragraph("• Duration: 15 minutes", body_style))
    story.append(Spacer(1, 0.1*inch))

    story.append(Paragraph("Wave 5: Other Events", heading2_style))
    story.append(Paragraph("• Time: 10:00 AM or noon", body_style))
    story.append(Paragraph("• Priority: Club Supervisor → ANY Lead Event Specialist", body_style))
    story.append(Paragraph("• Duration: 15 minutes", body_style))
    story.append(Spacer(1, 0.1*inch))

    story.append(Paragraph(
        "Reference: <i>services/scheduling_engine.py</i> (Lines 122-187)",
        body_style
    ))
    story.append(PageBreak())

    # ===== SECTION 5: EMPLOYEE AVAILABILITY =====
    story.append(Paragraph("5. Employee Availability", heading1_style))
    story.append(Paragraph(
        "The system implements a 3-tier availability structure that allows flexible scheduling "
        "while respecting employee work patterns.",
        body_style
    ))
    story.append(Spacer(1, 0.2*inch))

    story.append(Paragraph("5.1 Weekly Availability Pattern (Base Level)", heading2_style))
    story.append(Paragraph(
        "Defines which days of the week an employee typically works. Boolean fields for each day "
        "(Monday through Sunday). Default: All days = True.",
        body_style
    ))
    story.append(Paragraph("• One pattern per employee (unique constraint)", body_style))
    story.append(Paragraph("• Applies week-to-week unless overridden", body_style))
    story.append(Paragraph("• Reference: <i>models/availability.py</i> (Lines 11-33)", body_style))
    story.append(Spacer(1, 0.1*inch))

    story.append(Paragraph("5.2 Date-Specific Availability (Override Level 1)", heading2_style))
    story.append(Paragraph(
        "Overrides weekly pattern for specific dates. Used for one-time availability changes.",
        body_style
    ))
    story.append(Paragraph("• Fields: employee_id, date, is_available, reason", body_style))
    story.append(Paragraph("• One record per employee per date (unique constraint)", body_style))
    story.append(Paragraph("• Reference: <i>models/availability.py</i> (Lines 35-54)", body_style))
    story.append(Spacer(1, 0.1*inch))

    story.append(Paragraph("5.3 Temporary Availability Overrides (Override Level 2)", heading2_style))
    story.append(Paragraph(
        "Temporary changes to weekly availability for date ranges. Example: 'Normally works Mon-Fri, "
        "but for 3 weeks can only work Tue/Thu'.",
        body_style
    ))
    story.append(Paragraph("• Date range-based: start_date to end_date", body_style))
    story.append(Paragraph("• Per-day boolean overrides (NULL = no override for that day)", body_style))
    story.append(Paragraph("• Auto-expires after end_date", body_style))
    story.append(Paragraph("• <b>Highest Priority:</b> Checked FIRST before weekly pattern", body_style))
    story.append(Paragraph("• Reference: <i>models/availability.py</i> (Lines 77-147)", body_style))
    story.append(Spacer(1, 0.2*inch))

    story.append(Paragraph("5.4 Availability Resolution Order", heading2_style))
    availability_order = [
        "1. Check Temporary Availability Overrides (if date falls in range)",
        "2. Check Date-Specific Availability (if exists for date)",
        "3. Fall back to Weekly Availability Pattern",
    ]
    for item in availability_order:
        story.append(Paragraph(item, body_style))

    story.append(PageBreak())

    # ===== SECTION 6: DAYS OFF MANAGEMENT =====
    story.append(Paragraph("6. Days Off Management", heading1_style))

    story.append(Paragraph("6.1 Time Off Requests", heading2_style))
    story.append(Paragraph(
        "Date range-based absences that create <b>HARD CONSTRAINTS</b>. Employees cannot be "
        "scheduled during approved time-off periods under any circumstances.",
        body_style
    ))
    story.append(Spacer(1, 0.1*inch))

    timeoff_data = [
        ['Field', 'Description'],
        ['employee_id', 'Employee taking time off'],
        ['start_date', 'First day of absence'],
        ['end_date', 'Last day of absence (inclusive)'],
        ['reason', 'Optional explanation'],
        ['created_at', 'Request timestamp'],
    ]

    timeoff_table = Table(timeoff_data, colWidths=[1.5*inch, 4.5*inch])
    timeoff_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c5282')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('TOPPADDING', (0, 1), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
    ]))
    story.append(timeoff_table)
    story.append(Spacer(1, 0.1*inch))
    story.append(Paragraph("• Reference: <i>models/availability.py</i> (Lines 56-75)", body_style))
    story.append(Spacer(1, 0.2*inch))

    story.append(Paragraph("6.2 Time Off Validation", heading2_style))
    story.append(Paragraph(
        "The system validates that no schedule falls within a time-off range. If a conflict is "
        "detected, scheduling is blocked with error details including time-off dates and ID.",
        body_style
    ))
    story.append(Paragraph("• Severity: <b>HARD</b> (cannot be overridden)", body_style))
    story.append(Paragraph("• Query: Checks if schedule date falls within [start_date, end_date]", body_style))
    story.append(Paragraph("• Reference: <i>services/constraint_validator.py</i> (Lines 93-110)", body_style))
    story.append(PageBreak())

    # ===== SECTION 7: POSITION-BASED RULES =====
    story.append(Paragraph("7. Position-Based Scheduling Rules", heading1_style))

    story.append(Paragraph("7.1 Job Title Hierarchy", heading2_style))
    hierarchy_data = [
        ['Level', 'Job Title', 'Can Work Events'],
        ['1', 'Club Supervisor', 'All event types'],
        ['2', 'Lead Event Specialist', 'Core, Supervisor, Freeosk, Digitals, Other'],
        ['3', 'Juicer Barista', 'Juicer, Core, Other'],
        ['4', 'Event Specialist', 'Core, Other only'],
    ]

    hierarchy_table = Table(hierarchy_data, colWidths=[0.7*inch, 2*inch, 3.3*inch])
    hierarchy_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c5282')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (0, -1), 'CENTER'),
        ('ALIGN', (1, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('TOPPADDING', (0, 1), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
    ]))
    story.append(hierarchy_table)
    story.append(Spacer(1, 0.1*inch))
    story.append(Paragraph("• Reference: <i>models/employee.py</i> (Lines 11-73)", body_style))
    story.append(Spacer(1, 0.2*inch))

    story.append(Paragraph("7.2 Role-Based Event Restrictions", heading2_style))
    story.append(Paragraph("<b>Juicer Events:</b>", heading3_style))
    story.append(Paragraph("• <b>HARD requirement:</b> Must be Juicer Barista or Club Supervisor", body_style))
    story.append(Paragraph("• Restricted from: Event Specialist, Lead Event Specialist", body_style))
    story.append(Spacer(1, 0.1*inch))

    story.append(Paragraph("<b>Lead-Only Events (Supervisor, Freeosk, Digitals):</b>", heading3_style))
    story.append(Paragraph("• <b>HARD requirement:</b> Must be Lead Event Specialist or Club Supervisor", body_style))
    story.append(Paragraph("• Restricted from: Event Specialist, Juicer Barista", body_style))
    story.append(Spacer(1, 0.1*inch))

    story.append(Paragraph("<b>Core and Other Events:</b>", heading3_style))
    story.append(Paragraph("• All employees can work these", body_style))
    story.append(Paragraph("• No restrictions", body_style))
    story.append(Spacer(1, 0.1*inch))

    story.append(Paragraph("<b>Club Supervisor Special Rule:</b>", heading3_style))
    story.append(Paragraph("• <b>SOFT warning:</b> Should not work regular Core events", body_style))
    story.append(Paragraph("• Allowed but warned if assigned to Core", body_style))
    story.append(Paragraph("• Exception: Can work Supervisor, Digitals, Freeosk without warning", body_style))
    story.append(Spacer(1, 0.1*inch))

    story.append(Paragraph(
        "References: <i>models/employee.py</i> (Lines 46-68), "
        "<i>services/constraint_validator.py</i> (Lines 139-169)",
        body_style
    ))
    story.append(PageBreak())

    # ===== SECTION 8: EVENT DURATION STANDARDS =====
    story.append(Paragraph("8. Event Duration Standards", heading1_style))
    story.append(Paragraph(
        "Each event type has a default duration used for scheduling and overlap detection. "
        "These durations can be overridden per-event if needed.",
        body_style
    ))
    story.append(Spacer(1, 0.2*inch))

    duration_data = [
        ['Event Type', 'Duration (Minutes)', 'Duration (Hours)', 'Notes'],
        ['Core', '390', '6.5', 'Primary shift type'],
        ['Juicer', '540', '9.0', 'Longest shift'],
        ['Supervisor', '5', '0.08', 'Paired with Core'],
        ['Digitals', '15', '0.25', 'Quick maintenance'],
        ['Freeosk', '15', '0.25', 'Product sampling'],
        ['Other', '15', '0.25', 'Miscellaneous tasks'],
    ]

    duration_table = Table(duration_data, colWidths=[1.2*inch, 1.2*inch, 1.2*inch, 2.4*inch])
    duration_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c5282')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('ALIGN', (1, 1), (2, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('TOPPADDING', (0, 1), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
    ]))
    story.append(duration_table)
    story.append(Spacer(1, 0.1*inch))
    story.append(Paragraph("• Reference: <i>models/event.py</i> (Lines 21-29)", body_style))
    story.append(PageBreak())

    # ===== SECTION 9: DAILY EVENT LIMITS =====
    story.append(Paragraph("9. Daily Event Limits", heading1_style))

    story.append(Paragraph("9.1 Core Events Limit", heading2_style))
    story.append(Paragraph(
        "<b>MAX_CORE_EVENTS_PER_DAY = 1</b>",
        body_style
    ))
    story.append(Paragraph(
        "Each employee can only work ONE Core event per day. This is a <b>HARD CONSTRAINT</b> "
        "that prevents employee burnout and ensures proper workload distribution.",
        body_style
    ))
    story.append(Spacer(1, 0.1*inch))

    story.append(Paragraph("9.2 Exception: Juicer Priority", heading2_style))
    story.append(Paragraph(
        "Juicer events can bump Core events in Wave 1 if a Juicer Barista has conflicts. "
        "This is the ONLY exception to the one-Core-per-day rule.",
        body_style
    ))
    story.append(Spacer(1, 0.1*inch))

    story.append(Paragraph("9.3 Validation Scope", heading2_style))
    story.append(Paragraph("• Checks both existing schedules AND pending schedules", body_style))
    story.append(Paragraph("• Validates in real-time during scheduling", body_style))
    story.append(Paragraph("• Blocks attempt with error message if violated", body_style))
    story.append(Spacer(1, 0.1*inch))

    story.append(Paragraph(
        "Reference: <i>services/constraint_validator.py</i> (Lines 34, 171-209)",
        body_style
    ))
    story.append(PageBreak())

    # ===== SECTION 10: TIME SLOT CONSTRAINTS =====
    story.append(Paragraph("10. Time Slot Constraints", heading1_style))
    story.append(Paragraph(
        "Different event types are assigned specific time windows and slots to optimize "
        "scheduling efficiency and prevent conflicts.",
        body_style
    ))
    story.append(Spacer(1, 0.2*inch))

    story.append(Paragraph("10.1 Core Event Time Slots", heading2_style))
    timeslot_data = [
        ['Slot', 'Time', 'Priority Assignment'],
        ['1', '9:45 AM', 'Primary Lead (default)'],
        ['2', '10:30 AM', 'Rotation'],
        ['3', '11:00 AM', 'Rotation'],
        ['4', '11:30 AM', 'Rotation'],
    ]

    timeslot_table = Table(timeslot_data, colWidths=[0.8*inch, 1.5*inch, 3.7*inch])
    timeslot_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c5282')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (1, -1), 'CENTER'),
        ('ALIGN', (2, 0), (2, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('TOPPADDING', (0, 1), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
    ]))
    story.append(timeslot_table)
    story.append(Paragraph("• Reference: <i>services/scheduling_engine.py</i> (Lines 60-66)", body_style))
    story.append(Spacer(1, 0.2*inch))

    story.append(Paragraph("10.2 Digital Event Time Slots", heading2_style))
    story.append(Paragraph("<b>Setup/Refresh:</b> Only 4 time slots available", body_style))
    story.append(Paragraph("  • 9:15 AM, 9:30 AM, 9:45 AM, 10:00 AM", body_style))
    story.append(Paragraph("  • Slots rotate per day", body_style))
    story.append(Paragraph("  • Reference: Lines 68-74", body_style))
    story.append(Spacer(1, 0.1*inch))

    story.append(Paragraph("<b>Teardown:</b> Evening slots", body_style))
    story.append(Paragraph("  • Start: 5:00 PM (17:00)", body_style))
    story.append(Paragraph("  • 15-minute intervals through 6:45 PM", body_style))
    story.append(Paragraph("  • Reference: Lines 76-86", body_style))
    story.append(Spacer(1, 0.2*inch))

    story.append(Paragraph("10.3 Other Event Default Times", heading2_style))
    story.append(Paragraph("• <b>Juicer:</b> 9:00 AM (or 5:00 PM for surveys)", body_style))
    story.append(Paragraph("• <b>Freeosk:</b> 9:00 AM", body_style))
    story.append(Paragraph("• <b>Supervisor:</b> 12:00 PM (paired with Core)", body_style))
    story.append(Paragraph("• <b>Other:</b> 10:00 AM or noon", body_style))
    story.append(PageBreak())

    # ===== SECTION 11: BUSINESS RULES =====
    story.append(Paragraph("11. Business Rules for Scheduling", heading1_style))

    story.append(Paragraph("11.1 Event Date Range Rules", heading2_style))
    story.append(Paragraph("<b>STRICT REQUIREMENTS:</b>", body_style))
    story.append(Paragraph("• Schedule date must be ≥ Start Date (on or after)", body_style))
    story.append(Paragraph("• Schedule date must be < Due Date (strictly before, NOT on)", body_style))
    story.append(Paragraph("• Both conditions must be true for valid scheduling", body_style))
    story.append(Spacer(1, 0.1*inch))
    story.append(Paragraph(
        "Reference: <i>services/scheduling_engine.py</i> (Lines 275-293)",
        body_style
    ))
    story.append(Spacer(1, 0.2*inch))

    story.append(Paragraph("11.2 Weekend Handling", heading2_style))
    story.append(Paragraph(
        "Weekends (Saturday=5, Sunday=6) are skipped when finding alternative scheduling slots. "
        "The system automatically advances to the next weekday.",
        body_style
    ))
    story.append(Paragraph(
        "Reference: <i>services/conflict_resolver.py</i> (Lines 200-203)",
        body_style
    ))
    story.append(Spacer(1, 0.2*inch))

    story.append(Paragraph("11.3 Short Notice Scheduling", heading2_style))
    story.append(Paragraph("<b>Days 1-3 from now (SHORT NOTICE):</b>", body_style))
    story.append(Paragraph("  • BUMP ONLY strategy", body_style))
    story.append(Paragraph("  • Don't try to fill empty slots", body_style))
    story.append(Paragraph("  • More aggressive bumping to handle urgency", body_style))
    story.append(Spacer(1, 0.1*inch))

    story.append(Paragraph("<b>Day 4+ (NORMAL):</b>", body_style))
    story.append(Paragraph("  • Try empty slots first", body_style))
    story.append(Paragraph("  • Bump only if necessary", body_style))
    story.append(Spacer(1, 0.1*inch))

    story.append(Paragraph(
        "Reference: <i>services/scheduling_engine.py</i> (Lines 1206-1224)",
        body_style
    ))
    story.append(PageBreak())

    # ===== SECTION 12: CONFLICT RESOLUTION =====
    story.append(Paragraph("12. Conflict Resolution Rules", heading1_style))

    story.append(Paragraph("12.1 Bumping Strategy", heading2_style))
    story.append(Paragraph(
        "When scheduling conflicts occur, lower priority events can be 'bumped' (rescheduled) "
        "to make room for higher priority events.",
        body_style
    ))
    story.append(Spacer(1, 0.1*inch))

    story.append(Paragraph("<b>Bumping Rules:</b>", body_style))
    story.append(Paragraph("• Priority based on due date urgency", body_style))
    story.append(Paragraph("• <b>MIN_DAYS_TO_DUE_DATE = 2</b>", body_style))
    story.append(Paragraph("• Never bump events within 2 days of due date", body_style))
    story.append(Paragraph("• Lower priority events can be bumped for higher priority", body_style))
    story.append(Paragraph("• Maximum 3 bumps per event (MAX_BUMPS_PER_EVENT = 3)", body_style))
    story.append(Spacer(1, 0.1*inch))

    story.append(Paragraph(
        "Reference: <i>services/conflict_resolver.py</i> (Lines 13-25)",
        body_style
    ))
    story.append(Spacer(1, 0.2*inch))

    story.append(Paragraph("12.2 Cascading Bump Logic", heading2_style))
    story.append(Paragraph("When an event is bumped, the system follows this sequence:", body_style))
    story.append(Spacer(1, 0.1*inch))

    cascade_steps = [
        "1. Try to move bumped event to earlier date ('forward move')",
        "2. If forward move fails, unschedule and reschedule",
        "3. Bumped event may cascade and bump another event",
        "4. Maximum 3 bumps per event to prevent infinite loops",
    ]
    for step in cascade_steps:
        story.append(Paragraph(step, body_style))

    story.append(Spacer(1, 0.1*inch))
    story.append(Paragraph(
        "Reference: <i>services/scheduling_engine.py</i> (Lines 656-862)",
        body_style
    ))
    story.append(Spacer(1, 0.2*inch))

    story.append(Paragraph("12.3 Time Proximity Rules", heading2_style))
    story.append(Paragraph("<b>TIME_PROXIMITY_HOURS = 2</b>", body_style))
    story.append(Paragraph(
        "The system checks for overlapping events within a 2-hour window. If events are too "
        "close together, a soft warning is issued to prevent scheduling conflicts and account "
        "for travel time between locations.",
        body_style
    ))
    story.append(Paragraph("• Severity: SOFT (warning only, can proceed)", body_style))
    story.append(Paragraph(
        "• Reference: <i>services/conflict_validation.py</i> (Lines 46-47, 348-416)",
        body_style
    ))
    story.append(PageBreak())

    # ===== SECTION 13: VALIDATION RULES =====
    story.append(Paragraph("13. Validation Rules and Constraints", heading1_style))

    story.append(Paragraph("13.1 Constraint Types", heading2_style))
    constraint_types_data = [
        ['Type', 'Severity', 'Description'],
        ['AVAILABILITY', 'SOFT', 'Weekly/date-specific availability'],
        ['TIME_OFF', 'HARD', 'Employee time-off requests'],
        ['ROLE', 'HARD', 'Job title/qualification requirements'],
        ['DAILY_LIMIT', 'HARD', 'Max events per day limits'],
        ['ALREADY_SCHEDULED', 'HARD', 'Overlap/conflict detection'],
        ['EVENT_TYPE', 'HARD', 'Event type compatibility'],
        ['DUE_DATE', 'HARD', 'Event date range validation'],
        ['ROTATION', 'HARD', 'Rotation assignment validation'],
    ]

    constraint_table = Table(constraint_types_data, colWidths=[1.8*inch, 1*inch, 3.2*inch])
    constraint_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c5282')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('ALIGN', (1, 1), (1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('TOPPADDING', (0, 1), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
    ]))
    story.append(constraint_table)
    story.append(Spacer(1, 0.1*inch))
    story.append(Paragraph(
        "Reference: <i>services/validation_types.py</i> (Lines 9-18)",
        body_style
    ))
    story.append(Spacer(1, 0.2*inch))

    story.append(Paragraph("13.2 Constraint Severity Levels", heading2_style))
    story.append(Paragraph("<b>HARD Constraints:</b> Cannot be violated (blocks scheduling)", body_style))
    story.append(Paragraph("  • Time off", body_style))
    story.append(Paragraph("  • Already scheduled (overlap)", body_style))
    story.append(Paragraph("  • Role restrictions", body_style))
    story.append(Paragraph("  • Daily limits", body_style))
    story.append(Paragraph("  • Date out of range", body_style))
    story.append(Spacer(1, 0.1*inch))

    story.append(Paragraph("<b>SOFT Constraints:</b> Warnings only (can proceed with caution)", body_style))
    story.append(Paragraph("  • Weekly availability mismatch", body_style))
    story.append(Paragraph("  • Time proximity warnings", body_style))
    story.append(Paragraph("  • Club Supervisor on regular events", body_style))
    story.append(Spacer(1, 0.1*inch))

    story.append(Paragraph(
        "Reference: <i>services/validation_types.py</i> (Lines 21-24)",
        body_style
    ))
    story.append(Spacer(1, 0.2*inch))

    story.append(Paragraph("13.3 Real-Time Validation Checks", heading2_style))
    story.append(Paragraph("7 validation checks performed during scheduling:", body_style))
    validation_checks = [
        "1. Core event duplicate (one per day rule)",
        "2. Employee marked unavailable",
        "3. Time-off conflict",
        "4. Weekly availability pattern",
        "5. Role/qualification restrictions",
        "6. Time proximity (2-hour window)",
        "7. Event date range validation",
    ]
    for check in validation_checks:
        story.append(Paragraph(check, body_style))

    story.append(Spacer(1, 0.1*inch))
    story.append(Paragraph(
        "Reference: <i>services/conflict_validation.py</i> (Lines 113-121)",
        body_style
    ))
    story.append(PageBreak())

    # ===== SECTION 14: ROTATION MANAGEMENT =====
    story.append(Paragraph("14. Rotation Management", heading1_style))

    story.append(Paragraph("14.1 Rotation Assignments", heading2_style))
    story.append(Paragraph(
        "The system maintains weekly rotations for Juicer Baristas and Primary Leads. Each day "
        "of the week is assigned to a specific employee for each rotation type.",
        body_style
    ))
    story.append(Spacer(1, 0.1*inch))

    rotation_fields_data = [
        ['Field', 'Description'],
        ['day_of_week', '0=Monday through 6=Sunday'],
        ['rotation_type', "'juicer' or 'primary_lead'"],
        ['employee_id', 'Assigned employee for that day'],
    ]

    rotation_table = Table(rotation_fields_data, colWidths=[1.8*inch, 4.2*inch])
    rotation_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c5282')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('TOPPADDING', (0, 1), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
    ]))
    story.append(rotation_table)
    story.append(Spacer(1, 0.1*inch))

    story.append(Paragraph("<b>Key Properties:</b>", body_style))
    story.append(Paragraph("• Unique constraint: One assignment per day per rotation type", body_style))
    story.append(Paragraph("• Persistent week-to-week unless manually changed", body_style))
    story.append(Paragraph(
        "• Reference: <i>models/auto_scheduler.py</i> (Lines 59-88)",
        body_style
    ))
    story.append(Spacer(1, 0.2*inch))

    story.append(Paragraph("14.2 Rotation Exceptions", heading2_style))
    story.append(Paragraph(
        "One-time overrides for specific dates. Used when the regular rotation employee cannot "
        "work on a particular day. The standing rotation remains unchanged.",
        body_style
    ))
    story.append(Spacer(1, 0.1*inch))

    exception_fields = [
        "• exception_date: Specific date to override",
        "• rotation_type: 'juicer' or 'primary_lead'",
        "• employee_id: Substitute employee for that date",
        "• reason: Optional explanation for the exception",
    ]
    for field in exception_fields:
        story.append(Paragraph(field, body_style))

    story.append(Spacer(1, 0.1*inch))
    story.append(Paragraph(
        "Reference: <i>models/auto_scheduler.py</i> (Lines 219-250)",
        body_style
    ))
    story.append(Spacer(1, 0.2*inch))

    story.append(Paragraph("14.3 Rotation Resolution Priority", heading2_style))
    story.append(Paragraph("When determining rotation assignment:", body_style))
    resolution_order = [
        "1. Check for one-time exception FIRST",
        "2. If no exception, fall back to weekly rotation",
        "3. Method: get_rotation_employee(target_date, rotation_type)",
    ]
    for item in resolution_order:
        story.append(Paragraph(item, body_style))

    story.append(Spacer(1, 0.1*inch))
    story.append(Paragraph(
        "Reference: <i>services/rotation_manager.py</i> (Lines 33-63)",
        body_style
    ))
    story.append(PageBreak())

    # ===== SECTION 15: TIME-BASED CONSTRAINTS =====
    story.append(Paragraph("15. Time-Based Constraints", heading1_style))

    story.append(Paragraph("15.1 Overlap Detection Algorithm", heading2_style))
    story.append(Paragraph(
        "The system calculates event end times and detects overlaps using a precise algorithm:",
        body_style
    ))
    story.append(Spacer(1, 0.1*inch))

    story.append(Paragraph(
        "<b>Overlap Formula:</b><br/>"
        "(proposed_start &lt; existing_end) AND (proposed_end &gt; existing_start)",
        body_style
    ))
    story.append(Spacer(1, 0.1*inch))

    story.append(Paragraph("<b>Process:</b>", body_style))
    overlap_process = [
        "1. Calculate end time using event duration",
        "2. Check both committed schedules AND pending schedules",
        "3. HARD constraint violation if overlap detected",
        "4. Block scheduling attempt with detailed error message",
    ]
    for step in overlap_process:
        story.append(Paragraph(step, body_style))

    story.append(Spacer(1, 0.1*inch))
    story.append(Paragraph(
        "Reference: <i>services/constraint_validator.py</i> (Lines 211-280)",
        body_style
    ))
    story.append(Spacer(1, 0.2*inch))

    story.append(Paragraph("15.2 Event Duration Calculation", heading2_style))
    story.append(Paragraph(
        "Method: <b>calculate_end_datetime(start_datetime)</b>",
        body_style
    ))
    story.append(Paragraph(
        "Uses estimated_time field OR default duration for event type. "
        "Returns: start_datetime + timedelta(minutes=duration)",
        body_style
    ))
    story.append(Spacer(1, 0.1*inch))
    story.append(Paragraph(
        "Reference: <i>models/event.py</i> (Lines 115-127)",
        body_style
    ))
    story.append(PageBreak())

    # ===== SECTION 16: SPECIAL BUSINESS LOGIC =====
    story.append(Paragraph("16. Special Business Logic", heading1_style))

    story.append(Paragraph("16.1 Core-Supervisor Pairing", heading2_style))
    story.append(Paragraph(
        "Each Core event has a matching Supervisor event that must be scheduled together.",
        body_style
    ))
    story.append(Spacer(1, 0.1*inch))

    story.append(Paragraph("<b>Pairing Rules:</b>", body_style))
    pairing_rules = [
        "• Format: 606001-CORE-... pairs with 606001-SUPERVISOR-...",
        "• Supervisor event scheduled at 12:00 PM on same date as Core",
        "• When Core moves, Supervisor moves with it",
        "• Event numbers must match for validation",
        "• Both events managed as a unit",
    ]
    for rule in pairing_rules:
        story.append(Paragraph(rule, body_style))

    story.append(Spacer(1, 0.1*inch))
    story.append(Paragraph(
        "Reference: <i>utils/event_helpers.py</i> (Lines 235-456)",
        body_style
    ))
    story.append(Spacer(1, 0.2*inch))

    story.append(Paragraph("16.2 Juicer Priority Override", heading2_style))
    story.append(Paragraph(
        "<b>Wave 1 Special Logic:</b> Juicer rotation employees MUST do Juicer events. "
        "This requirement overrides certain other constraints.",
        body_style
    ))
    story.append(Spacer(1, 0.1*inch))

    story.append(Paragraph("<b>Bumpable Constraints (for Juicer priority):</b>", body_style))
    story.append(Paragraph("  • DAILY_LIMIT (can exceed one Core per day)", body_style))
    story.append(Paragraph("  • ALREADY_SCHEDULED (can bump existing Core events)", body_style))
    story.append(Spacer(1, 0.1*inch))

    story.append(Paragraph("<b>Blocking Constraints (still enforced):</b>", body_style))
    story.append(Paragraph("  • TIME_OFF (cannot override time off)", body_style))
    story.append(Paragraph("  • AVAILABILITY (must be available)", body_style))
    story.append(Paragraph("  • ROLE (must be Juicer Barista)", body_style))
    story.append(Paragraph("  • DUE_DATE (must be within event date range)", body_style))
    story.append(Spacer(1, 0.1*inch))

    story.append(Paragraph(
        "Reference: <i>services/scheduling_engine.py</i> (Lines 442-517)",
        body_style
    ))
    story.append(Spacer(1, 0.2*inch))

    story.append(Paragraph("16.3 Employee Termination Rules", heading2_style))
    story.append(Paragraph(
        "Terminated employees are tracked but not scheduled for future events:",
        body_style
    ))
    story.append(Paragraph("• Field: termination_date (nullable)", body_style))
    story.append(Paragraph("• Prevents scheduling after termination", body_style))
    story.append(Paragraph("• Allows historical data retention", body_style))
    story.append(Paragraph("• Reference: <i>models/employee.py</i> (Line 39)", body_style))
    story.append(Spacer(1, 0.2*inch))

    story.append(Paragraph("16.4 Event Scheduling Overrides", heading2_style))
    story.append(Paragraph(
        "Per-event control over auto-scheduler behavior. Some events require manual assignment:",
        body_style
    ))
    story.append(Spacer(1, 0.1*inch))

    story.append(Paragraph("<b>Field:</b> allow_auto_schedule (Boolean)", body_style))
    story.append(Paragraph("<b>Use Cases:</b>", body_style))
    override_cases = [
        "  • VIP events requiring manual assignment",
        "  • Complex events with special requirements",
        "  • Events needing human review before scheduling",
    ]
    for case in override_cases:
        story.append(Paragraph(case, body_style))

    story.append(Spacer(1, 0.1*inch))
    story.append(Paragraph(
        "Reference: <i>models/auto_scheduler.py</i> (Lines 252-283)",
        body_style
    ))
    story.append(PageBreak())

    # ===== SECTION 17: CONFIGURATION CONSTANTS =====
    story.append(Paragraph("17. Configuration Constants", heading1_style))

    story.append(Paragraph("17.1 Key System Constants", heading2_style))
    constants_data = [
        ['Constant', 'Value', 'Purpose'],
        ['SCHEDULING_WINDOW_DAYS', '3', '3-day buffer before auto-scheduling'],
        ['MAX_CORE_EVENTS_PER_DAY', '1', 'One Core event per employee per day'],
        ['MAX_BUMPS_PER_EVENT', '3', 'Prevent infinite bump loops'],
        ['MIN_DAYS_TO_DUE_DATE', '2', 'Never bump within 2 days of due date'],
        ['TIME_PROXIMITY_HOURS', '2', 'Check conflicts within 2-hour window'],
    ]

    constants_table = Table(constants_data, colWidths=[2.2*inch, 1*inch, 2.8*inch])
    constants_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c5282')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('ALIGN', (1, 1), (1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('TOPPADDING', (0, 1), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
    ]))
    story.append(constants_table)
    story.append(Spacer(1, 0.2*inch))

    story.append(Paragraph("17.2 Database Constraints", heading2_style))
    db_constraints = [
        "• Unique constraint on employee weekly availability",
        "• Unique constraint on employee-date availability",
        "• Check constraint: end_date ≥ start_date for overrides",
        "• Check constraint: day_of_week between 0-6",
        "• Check constraint: Valid rotation types",
        "• Check constraint: Valid run statuses",
    ]
    for constraint in db_constraints:
        story.append(Paragraph(constraint, body_style))

    story.append(Spacer(1, 0.2*inch))

    story.append(Paragraph("17.3 API Configuration", heading2_style))
    api_config = [
        "• Rate Limit: 100 requests per hour (default)",
        "• External API Max Retries: 3",
        "• CSRF Time Limit: 3600 seconds (1 hour)",
    ]
    for config in api_config:
        story.append(Paragraph(config, body_style))

    story.append(Spacer(1, 0.1*inch))
    story.append(Paragraph("Reference: <i>config.py</i>", body_style))
    story.append(PageBreak())

    # ===== SECTION 18: AUDIT AND VALIDATION =====
    story.append(Paragraph("18. Daily Audit and Validation Checks", heading1_style))
    story.append(Paragraph(
        "The system performs comprehensive daily validation to identify potential issues "
        "before they become problems.",
        body_style
    ))
    story.append(Spacer(1, 0.2*inch))

    story.append(Paragraph("18.1 Automated Daily Checks", heading2_style))
    audit_checks = [
        ['Check', 'Purpose'],
        ['Unscheduled Events', 'Identify events approaching due date without assignments'],
        ['Rotation Gaps', 'Detect days missing Juicer or Primary Lead assignments'],
        ['Overbooked Employees', 'Find employees with too many events in one day'],
        ['Conflicting Schedules', 'Detect overlapping events for same employee'],
        ['Availability Violations', 'Find schedules on unavailable days'],
        ['3-Day Window Events', 'Highlight urgent events needing attention'],
        ['Rotation Time-Off Conflicts', 'Detect when rotation employee has time off'],
        ['Supervisor Event Pairing', 'Validate Core-Supervisor event matching'],
    ]

    audit_table = Table(audit_checks, colWidths=[2.2*inch, 3.8*inch])
    audit_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c5282')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('TOPPADDING', (0, 1), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
    ]))
    story.append(audit_table)
    story.append(Spacer(1, 0.1*inch))
    story.append(Paragraph(
        "Reference: <i>services/daily_audit_checker.py</i>",
        body_style
    ))
    story.append(PageBreak())

    # ===== APPENDIX: QUICK REFERENCE =====
    story.append(Paragraph("Appendix: Quick Reference Guide", heading1_style))

    story.append(Paragraph("Event Type Summary", heading2_style))
    quick_ref_data = [
        ['Event', 'Duration', 'Who Can Work', 'Default Time'],
        ['Juicer', '9 hrs', 'Juicer Barista, Supervisor', '9:00 AM'],
        ['Core', '6.5 hrs', 'All employees', '9:45 AM (Lead)'],
        ['Supervisor', '5 min', 'Lead, Supervisor', '12:00 PM'],
        ['Freeosk', '15 min', 'Lead, Supervisor', '9:00 AM'],
        ['Digital Setup', '15 min', 'Lead, Supervisor', '9:15-10:00'],
        ['Digital Refresh', '15 min', 'Lead, Supervisor', '9:15-10:00'],
        ['Digital Teardown', '15 min', 'Lead, Supervisor', '5:00 PM+'],
        ['Other', '15 min', 'All employees', '10:00 AM'],
    ]

    quick_table = Table(quick_ref_data, colWidths=[1.5*inch, 1*inch, 2*inch, 1.5*inch])
    quick_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c5282')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('TOPPADDING', (0, 1), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
    ]))
    story.append(quick_table)
    story.append(Spacer(1, 0.3*inch))

    story.append(Paragraph("Critical Rules to Remember", heading2_style))
    critical_rules = [
        "• 3-day buffer: Auto-scheduler doesn't schedule within 3 days",
        "• One Core per day: Each employee can only work ONE Core event per day",
        "• Time off is HARD: Cannot override approved time-off periods",
        "• Juicer priority: Can bump Core events in Wave 1 if needed",
        "• Never bump within 2 days of due date",
        "• Max 3 bumps per event to prevent cascading loops",
        "• 2-hour proximity check for overlapping events",
        "• Core-Supervisor events must be paired and move together",
        "• Rotation exceptions override weekly rotation assignments",
    ]
    for rule in critical_rules:
        story.append(Paragraph(rule, body_style))

    story.append(Spacer(1, 0.3*inch))
    story.append(Paragraph(
        "For detailed information on any topic, refer to the corresponding section in this rulebook.",
        body_style
    ))

    # Build PDF with numbered pages
    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"SUCCESS: Rulebook created: {filename}")
    return filename


if __name__ == "__main__":
    create_rulebook()
