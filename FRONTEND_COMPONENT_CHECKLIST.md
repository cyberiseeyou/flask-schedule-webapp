# Front-End Component Checklist
## Calendar Redesign Implementation

**Project:** Flask Schedule WebApp - Calendar Enhancement
**Version:** 1.0
**Date:** 2025-10-12
**Reference:** UX_MOCKUP_SPECIFICATION.md

---

## 📋 Implementation Overview

This checklist provides a step-by-step guide for developers to implement the calendar redesign. Each component is broken down into actionable tasks with acceptance criteria.

**Estimated Timeline:**
- **Sprint 1 (2 weeks):** Phase 1 (Calendar View) + Phase 3 (Pairing Logic)
- **Sprint 2 (2 weeks):** Phase 2 (Daily View)

---

## Phase 1: Calendar Month View

### 1.1 Full-Screen Layout Structure

**Files to Modify:**
- `scheduler_app/static/css/style.css`
- `scheduler_app/static/css/responsive.css`
- `scheduler_app/templates/calendar.html`

**Tasks:**

- [ ] **Update container max-width to 100%**
  ```css
  .calendar-container {
    max-width: 100%;
    width: 100%;
    padding: 0 2rem;
  }
  ```
  - File: `style.css` (line ~315)
  - Acceptance: Calendar spans full viewport width on desktop

- [ ] **Remove 1200px constraint from calendar grid**
  ```css
  .calendar-grid {
    display: grid;
    grid-template-columns: repeat(7, 1fr);
    gap: 1px;
    background: #dee2e6;
  }
  ```
  - File: `style.css` or new `calendar.css`
  - Acceptance: Calendar cells divide equally across viewport

- [ ] **Add responsive padding adjustments**
  - Desktop (≥1024px): `padding: 0 2rem`
  - Tablet (768-1023px): `padding: 0 1.5rem`
  - Mobile (≤767px): `padding: 0 1rem`
  - File: `responsive.css`
  - Acceptance: Appropriate spacing on all devices

---

### 1.2 Calendar Cell Redesign

**Files to Create/Modify:**
- `scheduler_app/templates/calendar.html` (cell structure)
- `scheduler_app/static/css/calendar.css` (new file)
- `scheduler_app/static/js/calendar.js` (modify)

**Tasks:**

- [ ] **Create calendar cell HTML structure**
  ```html
  <div class="calendar-cell" data-date="2025-10-15" role="button" tabindex="0">
    <div class="cell-header">
      <span class="day-number">15</span>
      <span class="warning-icon" title="2 unscheduled events">⚠️</span>
    </div>
    <div class="event-badges">
      <span class="event-badge badge-core">C: 4</span>
      <span class="event-badge badge-juicer">J: 2</span>
      <span class="event-badge badge-supervisor">S: 4</span>
      <span class="event-badge badge-freeosk">F: 1</span>
      <span class="event-badge badge-digitals">D: 3</span>
      <span class="event-badge badge-other zero-count">O: 0</span>
    </div>
  </div>
  ```
  - File: `calendar.html` (Jinja loop for days)
  - Acceptance: Matches mockup structure exactly

- [ ] **Style calendar cell container**
  ```css
  .calendar-cell {
    background: #ffffff;
    border: 1px solid #dee2e6;
    min-height: 180px;
    padding: 0.75rem;
    position: relative;
    cursor: pointer;
    transition: all 0.2s ease;
  }
  ```
  - File: `calendar.css`
  - Acceptance: Clean white cells with proper spacing

- [ ] **Add hover/focus states**
  ```css
  .calendar-cell:hover,
  .calendar-cell:focus {
    background: #f8f9fa;
    border: 2px solid #007bff;
    outline: none;
    box-shadow: 0 2px 8px rgba(0,123,255,0.2);
  }
  ```
  - File: `calendar.css`
  - Acceptance: Blue border + subtle shadow on hover

- [ ] **Position day number (top-left)**
  ```css
  .cell-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: 0.5rem;
  }

  .day-number {
    font-size: 1.5rem;
    font-weight: 600;
    color: #212529;
  }
  ```
  - File: `calendar.css`
  - Acceptance: Day number clearly visible, proper spacing

- [ ] **Position warning icon (top-right)**
  ```css
  .warning-icon {
    font-size: 20px;
    color: #FFC107;
    filter: drop-shadow(0 2px 4px rgba(255, 193, 7, 0.4));
    cursor: help;
  }

  .warning-icon:hover {
    animation: pulse 1.5s ease-in-out infinite;
  }

  @keyframes pulse {
    0%, 100% { transform: scale(1); }
    50% { transform: scale(1.1); }
  }
  ```
  - File: `calendar.css`
  - Acceptance: Icon visible only when unscheduled events exist, animated on hover

---

### 1.3 Event Type Badges

**Tasks:**

- [ ] **Create badge grid layout**
  ```css
  .event-badges {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 0.5rem;
  }
  ```
  - File: `calendar.css`
  - Acceptance: 2×3 grid (CORE/Juicer/Supervisor on top, Freeosk/Digitals/Other on bottom)

- [ ] **Style base badge component**
  ```css
  .event-badge {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    padding: 6px 8px;
    border-radius: 4px;
    font-size: 0.875rem;
    font-weight: 600;
    min-width: 50px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    white-space: nowrap;
  }
  ```
  - File: `calendar.css`
  - Acceptance: Compact, readable badges

- [ ] **Add event type color variants**
  ```css
  .badge-core       { background: #dc3545; color: #fff; }
  .badge-juicer     { background: #1e7e34; color: #fff; } /* WCAG AA compliant */
  .badge-supervisor { background: #6610f2; color: #fff; }
  .badge-freeosk    { background: #fd7e14; color: #fff; }
  .badge-digitals   { background: #007bff; color: #fff; }
  .badge-other      { background: #6c757d; color: #fff; }
  ```
  - File: `calendar.css`
  - Acceptance: All colors meet WCAG AA contrast standards (4.5:1 minimum)

- [ ] **Style zero-count badges**
  ```css
  .event-badge.zero-count {
    background: #f8f9fa;
    color: #adb5bd;
    border: 1px dashed #dee2e6;
    box-shadow: none;
  }
  ```
  - File: `calendar.css`
  - Acceptance: Visually de-emphasized when count is 0

- [ ] **Add responsive badge adjustments**
  - Desktop: Font-size 0.875rem (14px)
  - Tablet: Font-size 0.75rem (12px)
  - Mobile: Font-size 0.7rem (11.2px) OR icon-only mode
  - File: `responsive.css`
  - Acceptance: Readable on all screen sizes

---

### 1.4 Backend Data Fetching

**Files to Modify:**
- `scheduler_app/routes/main.py` (calendar_view function)

**Tasks:**

- [ ] **Create optimized aggregation query**
  ```python
  from sqlalchemy import func, case

  def get_calendar_event_counts(year, month):
      start_date = datetime(year, month, 1)
      end_date = datetime(year, month + 1, 1) if month < 12 else datetime(year + 1, 1, 1)

      counts = db.session.query(
          func.date(Event.start_datetime).label('date'),
          func.sum(case((Event.project_name.like('%-CORE-%'), 1), else_=0)).label('core_count'),
          func.sum(case((Event.event_type == 'Juicer Production', 1), else_=0)).label('juicer_count'),
          func.sum(case((Event.project_name.like('%-Supervisor-%'), 1), else_=0)).label('supervisor_count'),
          func.sum(case((Event.event_type.like('%Freeosk%'), 1), else_=0)).label('freeosk_count'),
          func.sum(case((Event.event_type.like('%Digital%'), 1), else_=0)).label('digitals_count'),
          func.sum(case((Event.condition == 'Unstaffed', 1), else_=0)).label('unscheduled_count')
      ).filter(
          func.date(Event.start_datetime).between(start_date, end_date)
      ).group_by(
          func.date(Event.start_datetime)
      ).all()

      return {str(row.date): row._asdict() for row in counts}
  ```
  - File: `main.py` (add new function)
  - Acceptance: Single query returns all counts, no N+1 queries

- [ ] **Update calendar_view route**
  ```python
  @main.route('/calendar')
  def calendar_view():
      year = request.args.get('year', datetime.now().year, type=int)
      month = request.args.get('month', datetime.now().month, type=int)

      event_counts = get_calendar_event_counts(year, month)

      return render_template('calendar.html',
                           year=year,
                           month=month,
                           event_counts=event_counts)
  ```
  - File: `main.py`
  - Acceptance: Template receives aggregated event counts

- [ ] **Update Jinja template to use event counts**
  ```jinja
  {% for day in days_in_month %}
    <div class="calendar-cell" data-date="{{ day.date }}">
      <div class="cell-header">
        <span class="day-number">{{ day.day }}</span>
        {% if event_counts[day.date].unscheduled_count > 0 %}
          <span class="warning-icon" title="{{ event_counts[day.date].unscheduled_count }} unscheduled events">⚠️</span>
        {% endif %}
      </div>
      <div class="event-badges">
        <span class="event-badge badge-core {% if event_counts[day.date].core_count == 0 %}zero-count{% endif %}">C: {{ event_counts[day.date].core_count }}</span>
        <!-- Repeat for other event types -->
      </div>
    </div>
  {% endfor %}
  ```
  - File: `calendar.html`
  - Acceptance: Correct counts displayed, warning icon shows conditionally

---

### 1.5 Click Navigation

**Files to Modify:**
- `scheduler_app/static/js/calendar.js`

**Tasks:**

- [ ] **Add click handler for calendar cells**
  ```javascript
  document.querySelectorAll('.calendar-cell').forEach(cell => {
    cell.addEventListener('click', function() {
      const date = this.dataset.date;
      window.location.href = `/calendar/daily/${date}`;
    });
  });
  ```
  - File: `calendar.js`
  - Acceptance: Clicking cell navigates to daily view

- [ ] **Add keyboard navigation**
  ```javascript
  cell.addEventListener('keydown', function(e) {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      const date = this.dataset.date;
      window.location.href = `/calendar/daily/${date}`;
    }
  });
  ```
  - File: `calendar.js`
  - Acceptance: Enter/Space keys navigate (accessibility)

- [ ] **Add loading state**
  ```javascript
  cell.addEventListener('click', function() {
    this.classList.add('loading');
    // Navigate after adding class for visual feedback
    setTimeout(() => {
      window.location.href = `/calendar/daily/${date}`;
    }, 100);
  });
  ```
  - File: `calendar.js`
  - CSS: `.calendar-cell.loading { opacity: 0.6; cursor: wait; }`
  - Acceptance: Visual feedback on click

---

### 1.6 Accessibility

**Tasks:**

- [ ] **Add ARIA labels to calendar cells**
  ```html
  <div class="calendar-cell"
       role="button"
       tabindex="0"
       aria-label="October 15, 2025. 4 CORE events, 2 Juicer events, 4 Supervisor events, 1 Freeosk event, 3 Digital events. Warning: 2 unscheduled events due.">
  ```
  - File: `calendar.html`
  - Acceptance: Screen readers announce full information

- [ ] **Add tooltip to warning icon**
  ```html
  <span class="warning-icon"
        role="img"
        aria-label="Warning: 2 unscheduled events due"
        title="2 unscheduled events due this day">⚠️</span>
  ```
  - File: `calendar.html`
  - Acceptance: Accessible tooltip on hover/focus

- [ ] **Test keyboard navigation**
  - Tab through calendar cells
  - Arrow keys move between cells (optional enhancement)
  - Enter/Space activate cell
  - File: Manual testing checklist
  - Acceptance: Fully keyboard accessible

---

## Phase 2: Daily View Page

### 2.1 Route & View Setup

**Files to Create/Modify:**
- `scheduler_app/routes/main.py`
- `scheduler_app/templates/calendar_daily.html` (new)

**Tasks:**

- [ ] **Create daily view route**
  ```python
  @main.route('/calendar/daily/<date>')
  def calendar_daily_view(date):
      # Parse date
      try:
          date_obj = datetime.strptime(date, '%Y-%m-%d')
      except ValueError:
          flash('Invalid date format', 'error')
          return redirect(url_for('main.calendar_view'))

      # Fetch data
      daily_data = get_daily_view_data(date_obj)

      return render_template('calendar_daily.html',
                           date=date_obj,
                           data=daily_data)
  ```
  - File: `main.py`
  - Acceptance: Route accessible at `/calendar/daily/2025-10-15`

- [ ] **Create data fetching function**
  ```python
  def get_daily_view_data(date):
      # Get all events for the day
      events = Event.query.filter(
          func.date(Event.start_datetime) == date.date()
      ).all()

      # Categorize events
      categorized = {
          'juicer': [],
          'freeosk': [],
          'digitals': [],
          'core': [],
          'supervisor': []
      }

      for event in events:
          if event.event_type == 'Juicer Production':
              categorized['juicer'].append(event)
          elif 'Freeosk' in event.event_type:
              categorized['freeosk'].append(event)
          elif 'Digital' in event.event_type:
              categorized['digitals'].append(event)
          elif '-CORE-' in event.project_name:
              # Add supervisor status
              event.supervisor_status = get_supervisor_status(event)
              categorized['core'].append(event)
          elif '-Supervisor-' in event.project_name:
              categorized['supervisor'].append(event)

      # Get Juicer and Lead
      juicers = [e.schedule.employee.name for e in categorized['juicer']
                 if e.schedule and e.schedule.employee]
      primary_lead = categorized['core'][0].schedule.employee.name \
                     if categorized['core'] and categorized['core'][0].schedule \
                     else None

      # Supervisor summary
      supervisor_scheduled = sum(1 for e in categorized['supervisor']
                                 if e.condition == 'Scheduled')
      supervisor_unscheduled = sum(1 for e in categorized['supervisor']
                                   if e.condition == 'Unstaffed')

      # Unscheduled events
      unscheduled_count = sum(1 for e in events if e.condition == 'Unstaffed')

      return {
          'events': categorized,
          'juicers': juicers,
          'primary_lead': primary_lead,
          'supervisor_summary': {
              'scheduled': supervisor_scheduled,
              'unscheduled': supervisor_unscheduled
          },
          'unscheduled_count': unscheduled_count
      }
  ```
  - File: `main.py`
  - Acceptance: Returns complete daily data structure

---

### 2.2 Header Section

**File:** `scheduler_app/templates/calendar_daily.html`

**Tasks:**

- [ ] **Create header HTML**
  ```html
  <div class="daily-view-header">
    <a href="{{ url_for('main.calendar_view') }}" class="back-link">
      <span aria-hidden="true">←</span> Back to Calendar
    </a>
    <h1 class="daily-date">{{ date.strftime('%A, %B %d, %Y') }}</h1>
  </div>
  ```
  - Acceptance: Back link functional, date formatted correctly

- [ ] **Style header**
  ```css
  .daily-view-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 2rem;
    padding-bottom: 1rem;
    border-bottom: 2px solid #dee2e6;
  }

  .back-link {
    color: #007bff;
    text-decoration: none;
    font-size: 1.125rem;
    font-weight: 500;
  }

  .back-link:hover {
    text-decoration: underline;
  }

  .daily-date {
    font-size: 2.5rem;
    font-weight: 700;
    color: #212529;
    margin: 0;
  }
  ```
  - File: `calendar_daily.css` (new)
  - Acceptance: Matches mockup design

---

### 2.3 Summary Banner

**Tasks:**

- [ ] **Create summary banner HTML**
  ```html
  <div class="summary-banner">
    <div class="summary-row">
      <div class="summary-item">
        <span class="summary-icon">🧃</span>
        <span class="summary-label">Juicer:</span>
        {% if data.juicers %}
          <span class="summary-value">{{ data.juicers|join(', ') }}</span>
        {% else %}
          <span class="summary-value warning">None scheduled</span>
        {% endif %}
      </div>

      <div class="summary-item">
        <span class="summary-icon">👔</span>
        <span class="summary-label">Primary Lead:</span>
        {% if data.primary_lead %}
          <span class="summary-value">{{ data.primary_lead }}</span>
        {% else %}
          <span class="summary-value warning">None scheduled</span>
        {% endif %}
      </div>
    </div>

    <div class="summary-row">
      <div class="summary-item">
        {% if data.supervisor_summary.scheduled > 0 %}
          <span class="summary-icon success">✅</span>
          <span class="summary-value">{{ data.supervisor_summary.scheduled }} Supervisor Events Scheduled</span>
        {% endif %}
      </div>

      <div class="summary-item">
        {% if data.unscheduled_count > 0 %}
          <span class="summary-icon warning">⚠️</span>
          <span class="summary-value warning">{{ data.unscheduled_count }} Unscheduled Events Due Today</span>
        {% endif %}
      </div>
    </div>
  </div>
  ```
  - File: `calendar_daily.html`
  - Acceptance: Shows all summary information

- [ ] **Style summary banner**
  ```css
  .summary-banner {
    background: #e7f3ff;
    border: 1px solid #b3d9ff;
    border-radius: 8px;
    padding: 1.5rem;
    margin-bottom: 2rem;
  }

  .summary-row {
    display: flex;
    gap: 2rem;
    margin-bottom: 0.75rem;
  }

  .summary-row:last-child {
    margin-bottom: 0;
  }

  .summary-item {
    font-size: 1.125rem;
    display: flex;
    align-items: center;
    gap: 0.5rem;
  }

  .summary-value.warning {
    color: #dc3545;
    font-weight: 600;
  }

  .summary-icon.success {
    color: #28a745;
  }

  .summary-icon.warning {
    color: #ffc107;
  }
  ```
  - File: `calendar_daily.css`
  - Acceptance: Matches mockup colors and layout

---

### 2.4 Event Group Sections

**Tasks:**

- [ ] **Create collapsible group component**
  ```html
  <div class="event-group" id="juicer-events" data-expanded="true">
    <h3 class="group-header" role="button" aria-expanded="true" aria-controls="juicer-events-content">
      <span class="group-title">
        <span class="group-icon">🧃</span>
        JUICER EVENTS ({{ data.events.juicer|length }})
      </span>
      <span class="toggle-icon">▼</span>
    </h3>

    <div class="group-content" id="juicer-events-content" role="region">
      {% if data.events.juicer %}
        {% for event in data.events.juicer %}
          {% include 'components/event_card.html' %}
        {% endfor %}
      {% else %}
        <p class="empty-state">No Juicer events scheduled for this day</p>
      {% endif %}
    </div>
  </div>
  ```
  - File: `calendar_daily.html`
  - Acceptance: Proper semantic HTML with ARIA

- [ ] **Style event group**
  ```css
  .event-group {
    margin-bottom: 2rem;
  }

  .group-header {
    background: #f8f9fa;
    padding: 1rem 1.5rem;
    border-radius: 8px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    cursor: pointer;
    transition: background 0.2s ease;
  }

  .group-header:hover {
    background: #e9ecef;
  }

  .group-title {
    font-size: 1.5rem;
    font-weight: 700;
    color: #212529;
    display: flex;
    align-items: center;
    gap: 0.75rem;
  }

  .toggle-icon {
    font-size: 1.25rem;
    transition: transform 0.3s ease;
  }

  .event-group[data-expanded="false"] .toggle-icon {
    transform: rotate(-90deg);
  }

  .group-content {
    overflow: hidden;
    transition: max-height 0.3s ease-out;
    padding-top: 1rem;
  }

  .event-group[data-expanded="false"] .group-content {
    max-height: 0;
    padding-top: 0;
  }
  ```
  - File: `calendar_daily.css`
  - Acceptance: Smooth collapse/expand animation

- [ ] **Add collapse/expand JavaScript**
  ```javascript
  document.querySelectorAll('.group-header').forEach(header => {
    header.addEventListener('click', function() {
      const group = this.closest('.event-group');
      const content = group.querySelector('.group-content');
      const isExpanded = group.dataset.expanded === 'true';

      if (isExpanded) {
        // Collapse
        content.style.maxHeight = '0';
        group.dataset.expanded = 'false';
        this.setAttribute('aria-expanded', 'false');
      } else {
        // Expand
        content.style.maxHeight = content.scrollHeight + 'px';
        group.dataset.expanded = 'true';
        this.setAttribute('aria-expanded', 'true');
      }

      // Save state
      localStorage.setItem(`event-group-${group.id}`, group.dataset.expanded);
    });

    // Restore state from localStorage
    const group = header.closest('.event-group');
    const savedState = localStorage.getItem(`event-group-${group.id}`);
    if (savedState !== null) {
      group.dataset.expanded = savedState;
      const content = group.querySelector('.group-content');
      if (savedState === 'true') {
        content.style.maxHeight = content.scrollHeight + 'px';
      }
    }
  });
  ```
  - File: `calendar_daily.js` (new)
  - Acceptance: State persists across page loads

- [ ] **Create empty state component**
  ```css
  .empty-state {
    color: #6c757d;
    font-style: italic;
    text-align: center;
    padding: 2rem;
    font-size: 1.125rem;
  }
  ```
  - File: `calendar_daily.css`
  - Acceptance: Shows when no events in category

---

### 2.5 Event Card Component

**Files to Create:**
- `scheduler_app/templates/components/event_card.html`

**Tasks:**

- [ ] **Create standard event card template**
  ```html
  <div class="event-card" data-event-type="{{ event.event_type }}">
    <div class="card-header">
      <span class="event-icon">📍</span>
      <span class="event-time">{{ event.start_datetime.strftime('%I:%M %p') }}</span>
      <span class="event-separator">-</span>
      <span class="event-name">{{ event.project_name }}</span>
    </div>

    <div class="card-details">
      <div class="detail-row">
        <span class="detail-item">
          <span class="detail-icon">👤</span>
          <span class="detail-label">Employee:</span>
          <span class="detail-value">{{ event.schedule.employee.name if event.schedule else 'Unassigned' }}</span>
        </span>

        <span class="detail-item">
          <span class="detail-icon">⏱️</span>
          <span class="detail-label">Duration:</span>
          <span class="detail-value">{{ event.estimated_hours }} hours</span>
        </span>
      </div>

      <div class="detail-row">
        <span class="detail-item">
          <span class="detail-icon">📅</span>
          <span class="detail-label">Due:</span>
          <span class="detail-value">{{ event.due_datetime.strftime('%b %d, %Y') }}</span>
        </span>

        <span class="detail-item">
          <span class="detail-icon">✅</span>
          <span class="detail-label">Status:</span>
          <span class="detail-value status-{{ event.condition|lower }}">{{ event.condition }}</span>
        </span>
      </div>
    </div>

    {% if '-CORE-' in event.project_name %}
      {% include 'components/supervisor_status.html' %}
    {% endif %}

    <div class="card-actions">
      <button class="btn btn-primary" data-action="reschedule" data-event-id="{{ event.event_id }}">
        Reschedule
      </button>
      <button class="btn btn-danger" data-action="unschedule" data-event-id="{{ event.event_id }}">
        Unschedule
      </button>
      {% if '-CORE-' in event.project_name %}
        <button class="btn btn-trade" data-action="trade" data-event-id="{{ event.event_id }}">
          Trade
        </button>
      {% endif %}
      <button class="btn btn-secondary" data-action="change-employee" data-event-id="{{ event.event_id }}">
        Change Employee
      </button>
    </div>
  </div>
  ```
  - File: `components/event_card.html`
  - Acceptance: Reusable for all event types

- [ ] **Style event card**
  ```css
  .event-card {
    background: #ffffff;
    border: 2px solid #dee2e6;
    border-radius: 8px;
    padding: 1.25rem;
    margin-bottom: 1rem;
    box-shadow: 0 2px 4px rgba(0,0,0,0.08);
    transition: all 0.2s ease;
  }

  .event-card:hover {
    box-shadow: 0 4px 12px rgba(0,0,0,0.12);
    transform: translateY(-2px);
  }

  /* Border color based on event type */
  .event-card[data-event-type*="Juicer"] {
    border-left: 6px solid #1e7e34;
  }

  .event-card[data-event-type*="Freeosk"] {
    border-left: 6px solid #fd7e14;
  }

  .event-card[data-event-type*="Digital"] {
    border-left: 6px solid #007bff;
  }

  .event-card .event-name:contains("CORE") {
    border-left-color: #dc3545;
  }

  .card-header {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    margin-bottom: 1rem;
    font-size: 1.25rem;
    font-weight: 600;
    color: #212529;
  }

  .card-details {
    margin-bottom: 1rem;
  }

  .detail-row {
    display: flex;
    gap: 2rem;
    margin-bottom: 0.5rem;
  }

  .detail-item {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    font-size: 1rem;
  }

  .detail-label {
    font-weight: 500;
    color: #6c757d;
  }

  .detail-value {
    color: #212529;
  }
  ```
  - File: `calendar_daily.css`
  - Acceptance: Clean card design with proper hierarchy

- [ ] **Style action buttons**
  ```css
  .card-actions {
    display: flex;
    gap: 0.75rem;
    flex-wrap: wrap;
  }

  .btn {
    padding: 0.75rem 1.5rem;
    border-radius: 6px;
    font-size: 1rem;
    font-weight: 600;
    border: none;
    cursor: pointer;
    transition: all 0.2s ease;
  }

  .btn:hover {
    box-shadow: 0 4px 8px rgba(0,0,0,0.2);
  }

  .btn:active {
    transform: scale(0.98);
  }

  .btn-primary {
    background: #007bff;
    color: #fff;
  }

  .btn-primary:hover {
    background: #0056b3;
  }

  .btn-danger {
    background: #dc3545;
    color: #fff;
  }

  .btn-danger:hover {
    background: #c82333;
  }

  .btn-secondary {
    background: #6c757d;
    color: #fff;
  }

  .btn-secondary:hover {
    background: #545b62;
  }

  .btn-trade {
    background: #ffc107;
    color: #212529;
  }

  .btn-trade:hover {
    background: #e0a800;
  }
  ```
  - File: `calendar_daily.css`
  - Acceptance: All button states working

---

### 2.6 Supervisor Status Component

**Files to Create:**
- `scheduler_app/templates/components/supervisor_status.html`

**Tasks:**

- [ ] **Create supervisor status banner**
  ```html
  <div class="supervisor-status status-{{ event.supervisor_status.status }}">
    {% if event.supervisor_status.status == 'scheduled' %}
      <span class="status-icon">✅</span>
      <span class="status-text">
        Supervisor Event Scheduled
        ({{ event.supervisor_status.employee }} @ {{ event.supervisor_status.time }})
      </span>
    {% elif event.supervisor_status.status == 'unscheduled' %}
      <span class="status-icon">⚠️</span>
      <span class="status-text">Supervisor Event NOT Scheduled</span>
    {% else %}
      <span class="status-icon">ℹ️</span>
      <span class="status-text">No Supervisor event configured for this CORE event</span>
    {% endif %}
  </div>

  {% if event.supervisor_status.status in ['scheduled', 'unscheduled'] %}
    <button class="btn btn-supervisor" data-action="view-supervisor" data-event-id="{{ event.supervisor_status.event_id }}">
      📋 View/Edit Supervisor Event
    </button>
  {% endif %}
  ```
  - File: `components/supervisor_status.html`
  - Acceptance: Shows correct status with icon

- [ ] **Style supervisor status**
  ```css
  .supervisor-status {
    padding: 0.75rem 1rem;
    border-radius: 6px;
    margin: 1rem 0;
    display: flex;
    align-items: center;
    gap: 0.5rem;
    font-size: 1rem;
  }

  .supervisor-status.status-scheduled {
    background: #d4edda;
    border: 1px solid #c3e6cb;
    color: #155724;
  }

  .supervisor-status.status-unscheduled {
    background: #fff3cd;
    border: 1px solid #ffeaa7;
    color: #856404;
  }

  .supervisor-status.status-not_found {
    background: #d1ecf1;
    border: 1px solid #bee5eb;
    color: #0c5460;
  }

  .status-icon {
    font-size: 1.25rem;
  }

  .btn-supervisor {
    background: #6610f2;
    color: #fff;
    width: 100%;
    margin-top: 0.5rem;
  }

  .btn-supervisor:hover {
    background: #520dc2;
  }
  ```
  - File: `calendar_daily.css`
  - Acceptance: Matches mockup colors

---

### 2.7 Supervisor Event Modal

**Files to Create:**
- `scheduler_app/templates/modals/supervisor_modal.html`
- `scheduler_app/static/js/supervisor_modal.js`

**Tasks:**

- [ ] **Create modal HTML**
  ```html
  <div id="supervisor-modal" class="modal" role="dialog" aria-labelledby="modal-title" aria-hidden="true">
    <div class="modal-overlay" aria-hidden="true"></div>
    <div class="modal-content">
      <div class="modal-header">
        <h2 id="modal-title">Supervisor Event Details</h2>
        <button class="modal-close" aria-label="Close modal">&times;</button>
      </div>

      <div class="modal-body">
        <div class="event-info">
          <p><strong>Event:</strong> <span id="supervisor-event-name"></span></p>
          <p><strong>Paired with:</strong> <span id="core-event-name"></span></p>
        </div>

        <div class="assignment-section">
          <h3>Current Assignment</h3>
          <div class="assignment-details">
            <p>👤 <strong>Supervisor:</strong> <span id="current-supervisor"></span></p>
            <p>⏰ <strong>Scheduled Time:</strong> <span id="current-time"></span></p>
            <p>📅 <strong>Date:</strong> <span id="current-date"></span></p>
            <p>⏱️ <strong>Duration:</strong> <span id="duration"></span></p>
          </div>
        </div>

        <div class="change-employee-section">
          <h3>Change Employee</h3>
          <select id="supervisor-employee-select" class="form-control">
            <option value="">Select Supervisor...</option>
          </select>
          <button class="btn btn-primary" id="change-supervisor-btn">Update Employee</button>
        </div>

        <div class="reschedule-section">
          <h3>Reschedule Time</h3>
          <div class="time-inputs">
            <input type="date" id="supervisor-date" class="form-control">
            <input type="time" id="supervisor-time" class="form-control">
            <button class="btn btn-primary" id="reschedule-supervisor-btn">Update</button>
          </div>
        </div>
      </div>

      <div class="modal-footer">
        <button class="btn btn-danger" id="unschedule-supervisor-btn">Unschedule Supervisor Event</button>
        <div class="modal-actions">
          <button class="btn btn-primary" id="save-supervisor-btn">Save</button>
          <button class="btn btn-secondary" id="cancel-supervisor-btn">Cancel</button>
        </div>
      </div>
    </div>
  </div>
  ```
  - File: `modals/supervisor_modal.html`
  - Acceptance: Complete modal structure

- [ ] **Style modal**
  ```css
  .modal {
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    z-index: 1000;
    display: none;
  }

  .modal.active {
    display: flex;
    align-items: center;
    justify-content: center;
  }

  .modal-overlay {
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: rgba(0, 0, 0, 0.6);
    animation: fadeIn 0.2s ease-out;
  }

  .modal-content {
    position: relative;
    background: #fff;
    width: 90%;
    max-width: 600px;
    max-height: 80vh;
    overflow-y: auto;
    border-radius: 12px;
    box-shadow: 0 10px 40px rgba(0,0,0,0.3);
    animation: slideUp 0.3s ease-out;
    z-index: 1001;
  }

  @keyframes fadeIn {
    from { opacity: 0; }
    to { opacity: 1; }
  }

  @keyframes slideUp {
    from {
      opacity: 0;
      transform: translateY(40px) scale(0.95);
    }
    to {
      opacity: 1;
      transform: translateY(0) scale(1);
    }
  }

  .modal-header {
    padding: 1.5rem;
    border-bottom: 1px solid #dee2e6;
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  .modal-close {
    font-size: 2rem;
    background: none;
    border: none;
    cursor: pointer;
    color: #6c757d;
  }

  .modal-close:hover {
    color: #212529;
  }

  .modal-body {
    padding: 1.5rem;
  }

  .modal-footer {
    padding: 1.5rem;
    border-top: 1px solid #dee2e6;
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  .modal-actions {
    display: flex;
    gap: 0.75rem;
  }
  ```
  - File: `calendar_daily.css`
  - Acceptance: Professional modal appearance

- [ ] **Implement modal JavaScript**
  ```javascript
  // Open modal
  document.querySelectorAll('[data-action="view-supervisor"]').forEach(btn => {
    btn.addEventListener('click', async function() {
      const eventId = this.dataset.eventId;
      await loadSupervisorModal(eventId);
    });
  });

  async function loadSupervisorModal(supervisorEventId) {
    const modal = document.getElementById('supervisor-modal');

    // Fetch supervisor event data
    const response = await fetch(`/api/supervisor-event/${supervisorEventId}`);
    const data = await response.json();

    // Populate modal
    document.getElementById('supervisor-event-name').textContent = data.event_name;
    document.getElementById('core-event-name').textContent = data.core_event_name;
    document.getElementById('current-supervisor').textContent = data.employee_name || 'Unassigned';
    document.getElementById('current-time').textContent = data.time || 'N/A';
    document.getElementById('current-date').textContent = data.date || 'N/A';
    document.getElementById('duration').textContent = data.duration || 'N/A';

    // Load available supervisors
    const supervisorSelect = document.getElementById('supervisor-employee-select');
    supervisorSelect.innerHTML = '<option value="">Select Supervisor...</option>';
    data.available_supervisors.forEach(sup => {
      const option = document.createElement('option');
      option.value = sup.id;
      option.textContent = `${sup.name} (${sup.role})`;
      supervisorSelect.appendChild(option);
    });

    // Show modal
    modal.classList.add('active');
    modal.setAttribute('aria-hidden', 'false');

    // Focus first element
    supervisorSelect.focus();

    // Trap focus
    trapFocus(modal);
  }

  // Close modal
  function closeModal() {
    const modal = document.getElementById('supervisor-modal');
    modal.classList.remove('active');
    modal.setAttribute('aria-hidden', 'true');
  }

  document.getElementById('modal-close').addEventListener('click', closeModal);
  document.getElementById('cancel-supervisor-btn').addEventListener('click', closeModal);
  document.querySelector('.modal-overlay').addEventListener('click', closeModal);

  // ESC key
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
      const modal = document.getElementById('supervisor-modal');
      if (modal.classList.contains('active')) {
        closeModal();
      }
    }
  });

  // Focus trap implementation
  function trapFocus(modal) {
    const focusableElements = modal.querySelectorAll(
      'button, input, select, [tabindex]:not([tabindex="-1"])'
    );
    const firstElement = focusableElements[0];
    const lastElement = focusableElements[focusableElements.length - 1];

    modal.addEventListener('keydown', (e) => {
      if (e.key === 'Tab') {
        if (e.shiftKey && document.activeElement === firstElement) {
          e.preventDefault();
          lastElement.focus();
        } else if (!e.shiftKey && document.activeElement === lastElement) {
          e.preventDefault();
          firstElement.focus();
        }
      }
    });
  }
  ```
  - File: `supervisor_modal.js`
  - Acceptance: Modal opens, closes, traps focus correctly

---

## Phase 3: CORE-Supervisor Pairing Logic

### 3.1 Helper Functions

**File:** `scheduler_app/utils/supervisor_helpers.py` (new)

**Tasks:**

- [ ] **Create supervisor matching function**
  ```python
  import re
  from scheduler_app.models import Event

  def get_supervisor_event(core_event):
      """
      Find the Supervisor event paired with a CORE event.

      Args:
          core_event: Event object with '-CORE-' in project_name

      Returns:
          Event object or None
      """
      # Extract 6-digit event number
      match = re.search(r'(\d{6})-CORE-', core_event.project_name)
      if not match:
          return None

      event_number = match.group(1)

      # Find matching Supervisor event
      supervisor_event = Event.query.filter(
          Event.project_name.like(f'{event_number}-Supervisor-%')
      ).first()

      return supervisor_event
  ```
  - Acceptance: Correctly matches CORE and Supervisor events

- [ ] **Create supervisor status function**
  ```python
  from scheduler_app.models import Schedule

  def get_supervisor_status(core_event):
      """
      Get the status of a CORE event's paired Supervisor event.

      Returns:
          dict with keys: status, employee, time, event_id, message
      """
      supervisor_event = get_supervisor_event(core_event)

      if not supervisor_event:
          return {
              'status': 'not_found',
              'message': 'No Supervisor event configured'
          }

      if supervisor_event.condition == 'Scheduled':
          schedule = Schedule.query.filter_by(
              event_id=supervisor_event.event_id
          ).first()

          if schedule:
              return {
                  'status': 'scheduled',
                  'employee': schedule.employee.name,
                  'time': schedule.start_datetime.strftime('%I:%M %p'),
                  'event_id': supervisor_event.event_id,
                  'message': f'Supervisor Event Scheduled ({schedule.employee.name} @ {schedule.start_datetime.strftime("%I:%M %p")})'
              }

      return {
          'status': 'unscheduled',
          'message': 'Supervisor Event NOT Scheduled',
          'event_id': supervisor_event.event_id
      }
  ```
  - Acceptance: Returns correct status information

---

### 3.2 Reschedule Pairing

**File:** `scheduler_app/routes/api.py`

**Tasks:**

- [ ] **Update reschedule endpoint**
  ```python
  from scheduler_app.utils.supervisor_helpers import get_supervisor_event
  from datetime import datetime, timedelta

  @api.route('/api/reschedule_event', methods=['POST'])
  def reschedule_event():
      try:
          data = request.json
          schedule_id = data['schedule_id']
          new_date = datetime.fromisoformat(data['new_date'])
          new_employee_id = data.get('new_employee_id')

          # Get schedule and event
          schedule = Schedule.query.get(schedule_id)
          if not schedule:
              return jsonify({'error': 'Schedule not found'}), 404

          event = Event.query.get(schedule.event_id)

          # Update CORE event schedule
          old_date = schedule.start_datetime
          schedule.start_datetime = new_date

          if new_employee_id:
              schedule.employee_id = new_employee_id

          # If this is a CORE event, also reschedule Supervisor
          if '-CORE-' in event.project_name:
              supervisor_event = get_supervisor_event(event)

              if supervisor_event:
                  supervisor_schedule = Schedule.query.filter_by(
                      event_id=supervisor_event.event_id
                  ).first()

                  if supervisor_schedule:
                      # Reschedule to same date at 12:00 PM
                      supervisor_date = datetime.combine(
                          new_date.date(),
                          datetime.strptime('12:00', '%H:%M').time()
                      )
                      supervisor_schedule.start_datetime = supervisor_date

                      # Log the pairing action
                      print(f"Auto-rescheduled Supervisor event {supervisor_event.event_id} to {supervisor_date}")

          db.session.commit()

          return jsonify({
              'success': True,
              'message': 'Event rescheduled successfully',
              'supervisor_rescheduled': supervisor_event is not None
          })

      except Exception as e:
          db.session.rollback()
          return jsonify({'error': str(e)}), 500
  ```
  - Acceptance: Rescheduling CORE event also reschedules Supervisor

- [ ] **Add transaction rollback on failure**
  ```python
  # Wrap in try-except with rollback (already shown above)
  ```
  - Acceptance: Database remains consistent on errors

---

### 3.3 Unschedule Pairing

**Tasks:**

- [ ] **Update unschedule endpoint**
  ```python
  @api.route('/api/unschedule/<int:schedule_id>', methods=['DELETE'])
  def unschedule(schedule_id):
      try:
          # Get schedule and event
          schedule = Schedule.query.get(schedule_id)
          if not schedule:
              return jsonify({'error': 'Schedule not found'}), 404

          event = Event.query.get(schedule.event_id)

          # Unschedule CORE event
          event.condition = 'Unstaffed'
          event.is_scheduled = False
          db.session.delete(schedule)

          # If this is a CORE event, also unschedule Supervisor
          supervisor_unscheduled = False
          if '-CORE-' in event.project_name:
              supervisor_event = get_supervisor_event(event)

              if supervisor_event:
                  supervisor_schedule = Schedule.query.filter_by(
                      event_id=supervisor_event.event_id
                  ).first()

                  if supervisor_schedule:
                      supervisor_event.condition = 'Unstaffed'
                      supervisor_event.is_scheduled = False
                      db.session.delete(supervisor_schedule)
                      supervisor_unscheduled = True

                      # Log the pairing action
                      print(f"Auto-unscheduled Supervisor event {supervisor_event.event_id}")

          db.session.commit()

          return jsonify({
              'success': True,
              'message': 'Event unscheduled successfully',
              'supervisor_unscheduled': supervisor_unscheduled
          })

      except Exception as e:
          db.session.rollback()
          return jsonify({'error': str(e)}), 500
  ```
  - Acceptance: Unscheduling CORE event also unschedules Supervisor

---

### 3.4 Manual Scheduling Verification

**File:** `scheduler_app/routes/scheduling.py`

**Tasks:**

- [ ] **Verify auto_schedule_supervisor_event integration**
  ```python
  # Check that save_schedule() calls auto_schedule_supervisor_event()
  # after scheduling a CORE event

  def save_schedule(event_id, employee_id, date):
      # ... existing code ...

      # Add CORE event check
      event = Event.query.get(event_id)
      if '-CORE-' in event.project_name:
          # Call supervisor auto-scheduling
          from scheduler_app.routes.scheduling import auto_schedule_supervisor_event
          auto_schedule_supervisor_event(event, employee_id, date)

      # ... rest of function ...
  ```
  - File: `scheduling.py`
  - Acceptance: Manual scheduling triggers supervisor pairing

- [ ] **Test with existing auto_schedule_supervisor_event**
  - Create unit test
  - Manually test in UI
  - Acceptance: Supervisor event automatically scheduled

---

## Phase 4: Testing & QA

### 4.1 Unit Tests

**File:** `tests/test_supervisor_pairing.py` (new)

**Tasks:**

- [ ] **Test get_supervisor_event()**
  ```python
  def test_get_supervisor_event_match():
      core_event = create_test_event('606001-CORE-Test')
      supervisor_event = create_test_event('606001-Supervisor-Test')

      result = get_supervisor_event(core_event)
      assert result.event_id == supervisor_event.event_id

  def test_get_supervisor_event_no_match():
      core_event = create_test_event('606001-CORE-Test')

      result = get_supervisor_event(core_event)
      assert result is None
  ```
  - Acceptance: Tests pass

- [ ] **Test reschedule pairing**
  ```python
  def test_reschedule_core_reschedules_supervisor():
      core_event = create_scheduled_event('606001-CORE-Test', date='2025-10-15')
      supervisor_event = create_scheduled_event('606001-Supervisor-Test', date='2025-10-15')

      # Reschedule CORE to 10-20
      reschedule_event(core_event.schedule.id, new_date='2025-10-20')

      # Supervisor should also be rescheduled
      db.session.refresh(supervisor_event)
      assert supervisor_event.schedule.start_datetime.date() == date(2025, 10, 20)
  ```
  - Acceptance: Tests pass

- [ ] **Test unschedule pairing**
  ```python
  def test_unschedule_core_unschedules_supervisor():
      core_event = create_scheduled_event('606001-CORE-Test')
      supervisor_event = create_scheduled_event('606001-Supervisor-Test')

      # Unschedule CORE
      unschedule(core_event.schedule.id)

      # Supervisor should also be unscheduled
      db.session.refresh(supervisor_event)
      assert supervisor_event.condition == 'Unstaffed'
      assert supervisor_event.is_scheduled == False
  ```
  - Acceptance: Tests pass

---

### 4.2 Integration Tests

**Tasks:**

- [ ] **Test calendar month view loading**
  - Navigate to `/calendar`
  - Verify event counts display
  - Verify warning icons show for unscheduled events
  - Acceptance: Page loads < 2 seconds

- [ ] **Test calendar cell navigation**
  - Click on calendar cell
  - Verify navigation to `/calendar/daily/{date}`
  - Acceptance: Smooth transition

- [ ] **Test daily view loading**
  - Navigate to `/calendar/daily/2025-10-15`
  - Verify all event groups display
  - Verify Juicer/Lead detection
  - Verify supervisor summary
  - Acceptance: Complete data displayed

- [ ] **Test collapsible sections**
  - Click to collapse/expand each event group
  - Verify smooth animation
  - Verify state persists on page reload
  - Acceptance: Works on all groups

- [ ] **Test supervisor modal**
  - Click "View/Edit Supervisor Event"
  - Verify modal opens with correct data
  - Test change employee
  - Test reschedule
  - Test unschedule
  - Verify modal closes (X, Cancel, ESC, overlay click)
  - Acceptance: All interactions work

---

### 4.3 Accessibility Tests

**Tasks:**

- [ ] **Keyboard navigation**
  - Tab through all interactive elements
  - Verify visual focus indicators
  - Test Enter/Space on calendar cells
  - Test arrow keys (optional)
  - Acceptance: Fully keyboard accessible

- [ ] **Screen reader testing**
  - Test with NVDA/JAWS (Windows) or VoiceOver (Mac)
  - Verify ARIA labels read correctly
  - Verify modal focus trap
  - Acceptance: Logical reading order

- [ ] **Color contrast testing**
  - Use browser DevTools or online checker
  - Verify all text meets WCAG AA (4.5:1)
  - Verify badges meet contrast standards
  - Acceptance: All elements pass AA

- [ ] **Touch target sizing**
  - Verify buttons ≥ 44×44px on mobile
  - Verify calendar cells tappable
  - Acceptance: No accidental taps

---

### 4.4 Responsive Testing

**Tasks:**

- [ ] **Desktop testing (≥1024px)**
  - Test at 1920×1080
  - Test at 1366×768
  - Verify full-screen layout
  - Acceptance: Proper spacing, no horizontal scroll

- [ ] **Tablet testing (768-1023px)**
  - Test at 1024×768 (iPad landscape)
  - Test at 768×1024 (iPad portrait)
  - Verify badge scaling
  - Verify daily view layout
  - Acceptance: Readable, usable

- [ ] **Mobile testing (≤767px)**
  - Test at 375×667 (iPhone SE)
  - Test at 390×844 (iPhone 12)
  - Verify calendar cell layout
  - Verify stacked buttons
  - Verify modal becomes full-screen
  - Acceptance: Touch-friendly, no overlaps

---

## Phase 5: Deployment

### 5.1 Pre-Deployment

**Tasks:**

- [ ] **Database backup**
  ```bash
  # Create full backup before deployment
  python manage.py db_backup --output backup_$(date +%Y%m%d).sql
  ```
  - Acceptance: Backup file created

- [ ] **Run all tests**
  ```bash
  pytest tests/ -v
  ```
  - Acceptance: All tests pass

- [ ] **Check migrations**
  ```bash
  flask db check
  flask db migrate -m "Calendar redesign"
  flask db upgrade
  ```
  - Acceptance: No migration issues

---

### 5.2 Deployment Steps

**Tasks:**

- [ ] **Deploy to staging**
  - Push to staging branch
  - Run migrations
  - Test manually
  - Acceptance: Staging works correctly

- [ ] **Deploy to production**
  - Push to main branch
  - Run migrations
  - Monitor logs for errors
  - Acceptance: Production stable

- [ ] **Monitor first 24 hours**
  - Check error logs
  - Monitor performance
  - Verify CORE-Supervisor pairing working
  - Acceptance: No critical errors

---

### 5.3 Post-Deployment

**Tasks:**

- [ ] **User documentation**
  - Update user guide with new calendar features
  - Create quick-start tutorial
  - Acceptance: Documentation complete

- [ ] **Training (if needed)**
  - Train staff on new daily view
  - Explain supervisor pairing
  - Acceptance: Team comfortable with changes

- [ ] **Gather feedback**
  - Monitor support tickets
  - Collect user feedback
  - Plan iteration if needed
  - Acceptance: Feedback documented

---

## Summary Checklist

### Phase 1: Calendar Month View
- [ ] Full-screen layout (100% width)
- [ ] Calendar cell redesign with badges
- [ ] Event type color-coded badges (6 types)
- [ ] Warning icon for unscheduled events
- [ ] Optimized backend query
- [ ] Click navigation to daily view
- [ ] Accessibility (keyboard, ARIA, contrast)

### Phase 2: Daily View Page
- [ ] Route `/calendar/daily/<date>`
- [ ] Header with back button & date
- [ ] Summary banner (Juicer, Lead, Supervisor, Unscheduled)
- [ ] Collapsible event groups (5 types)
- [ ] Event card component
- [ ] Supervisor status banner on CORE cards
- [ ] Supervisor event modal
- [ ] Action buttons (Reschedule, Unschedule, Trade, Change Employee)

### Phase 3: CORE-Supervisor Pairing
- [ ] Helper functions (get_supervisor_event, get_supervisor_status)
- [ ] Reschedule pairing logic
- [ ] Unschedule pairing logic
- [ ] Manual scheduling verification
- [ ] Transaction rollback on errors

### Phase 4: Testing
- [ ] Unit tests for pairing logic
- [ ] Integration tests (calendar, daily view, modal)
- [ ] Accessibility tests (keyboard, screen reader, contrast)
- [ ] Responsive tests (desktop, tablet, mobile)

### Phase 5: Deployment
- [ ] Database backup
- [ ] Staging deployment
- [ ] Production deployment
- [ ] Monitoring
- [ ] Documentation & training

---

## Estimated Timeline

**Sprint 1 (2 weeks):**
- Week 1: Phase 1 (Calendar Month View)
- Week 2: Phase 3 (CORE-Supervisor Pairing) + Testing

**Sprint 2 (2 weeks):**
- Week 3: Phase 2 (Daily View Page)
- Week 4: Testing + Deployment

**Total: 4 weeks**

---

## Developer Notes

### Key Files to Create:
- `scheduler_app/static/css/calendar.css`
- `scheduler_app/static/css/calendar_daily.css`
- `scheduler_app/static/js/calendar.js`
- `scheduler_app/static/js/calendar_daily.js`
- `scheduler_app/static/js/supervisor_modal.js`
- `scheduler_app/templates/calendar_daily.html`
- `scheduler_app/templates/components/event_card.html`
- `scheduler_app/templates/components/supervisor_status.html`
- `scheduler_app/templates/modals/supervisor_modal.html`
- `scheduler_app/utils/supervisor_helpers.py`
- `tests/test_supervisor_pairing.py`

### Key Files to Modify:
- `scheduler_app/routes/main.py`
- `scheduler_app/routes/api.py`
- `scheduler_app/routes/scheduling.py`
- `scheduler_app/templates/calendar.html`
- `scheduler_app/static/css/style.css`
- `scheduler_app/static/css/responsive.css`

### Dependencies:
- No new Python packages required
- Existing SQLAlchemy, Flask, Jinja2 sufficient

---

**Document Status:** ✅ Ready for Development
**Last Updated:** 2025-10-12
**Created By:** Sally (UX Expert)
