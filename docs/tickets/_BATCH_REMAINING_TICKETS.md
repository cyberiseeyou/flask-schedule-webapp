# MEDIUM & LOW PRIORITY TICKETS - Quick Reference

## MED-01: Implement Repository Pattern
**Effort**: 20-24h | **Assigned**: Dev (James)

Extract database queries into repository classes for better testability and maintainability.

```python
# repositories/event_repository.py
class EventRepository:
    def get_unscheduled_events(self): ...
    def get_events_by_date_range(self, start, end): ...
```

## MED-02: Create UX/UI Agent and Conduct Full Review
**Effort**: 30-40h | **Assigned**: UX/UI Agent (Sarah - to be created)

Create new UX/UI agent and conduct comprehensive review of all 12 templates for accessibility, responsiveness, and usability.

**Key Areas**:
- Accessibility (WCAG 2.1 AA)
- Mobile responsiveness
- User workflows
- Design consistency

## MED-03: Add Database Indexes
**Effort**: 8-12h | **Assigned**: Dev (James)

Add missing indexes on frequently queried columns to improve performance.

```sql
CREATE INDEX idx_schedules_datetime ON schedules(schedule_datetime);
CREATE INDEX idx_schedules_employee ON schedules(employee_id);
CREATE INDEX idx_events_type ON events(event_type);
CREATE INDEX idx_events_scheduled ON events(is_scheduled);
```

## MED-04: Implement APM Monitoring
**Effort**: 16-20h | **Assigned**: Dev (James)

Implement Application Performance Monitoring using New Relic or similar.

**Features**:
- Request tracing
- Error tracking
- Performance metrics
- Database query monitoring

## LOW-01: Add OpenAPI/Swagger Documentation
**Effort**: 16-20h | **Assigned**: Dev (James)

Add interactive API documentation using Flask-RESTX or similar.

```python
from flask_restx import Api, Resource

api = Api(app, version='1.0', title='Scheduler API',
    description='Event scheduling and management API')
```

## LOW-02: Implement Redis Caching
**Effort**: 20-24h | **Assigned**: Dev (James)

Implement Redis for session management and caching frequently accessed data.

**Use Cases**:
- Session storage
- EDR report caching
- Employee rotation caching

## LOW-03: Containerize Application
**Effort**: 12-16h | **Assigned**: Dev (James)

Create Docker containerization for easy deployment.

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY scheduler_app/ ./scheduler_app/
CMD ["gunicorn", "app:app"]
```

## LOW-04: Setup CI/CD Pipeline
**Effort**: 16-20h | **Assigned**: Dev (James)

Implement automated testing, building, and deployment pipeline.

**Pipeline**:
1. Lint → Test → Build → Deploy to staging → Deploy to production

