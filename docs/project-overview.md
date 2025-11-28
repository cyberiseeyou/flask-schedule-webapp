# Project Overview

**Project Name:** Flask Schedule Webapp
**Type:** Web Application (Monolith)
**Status:** Production-Ready
**Generated:** 2025-11-20

## Executive Summary

Flask Schedule Webapp is a comprehensive employee scheduling and event management system built with Flask. The application provides intelligent automated scheduling, real-time availability tracking, external API synchronization with Crossmark and Walmart systems, and advanced analytics for workforce management. It features an AI-powered assistant for natural language interactions and supports complex scheduling constraints including job requirements, time-off management, and workload balancing.

## Purpose

The system automates and streamlines the complex process of assigning employees to work events while respecting availability constraints, skill requirements, and business rules. It integrates with external systems (Crossmark API for event data and Walmart Retail Link for sales reporting) to provide a complete end-to-end scheduling and reporting solution.

## Tech Stack Summary

| Category | Technology | Version | Purpose |
|----------|------------|---------|---------|
| **Runtime** | Python | 3.11+ | Application runtime |
| **Framework** | Flask | 3.0.3 | Web framework |
| **Database** | PostgreSQL / SQLite | Latest / Built-in | Data storage |
| **ORM** | SQLAlchemy | 3.1.1 | Database abstraction |
| **Migrations** | Alembic (Flask-Migrate) | 4.0.5 | Schema versioning |
| **Task Queue** | Celery | 5.3.6 | Async background jobs |
| **Cache/Broker** | Redis | 5.0.3 | Task queue backend |
| **WSGI Server** | Gunicorn | 21.2.0 | Production server |
| **Worker Type** | Gevent | 24.2.1 | Async I/O workers |
| **PDF Generation** | ReportLab + xhtml2pdf | 4.2.5 / 0.2.16 | Document creation |
| **Security** | Flask-WTF + Cryptography | 1.2.1 / 42.0.5 | CSRF + encryption |
| **Rate Limiting** | Flask-Limiter | 4.0.0 | API throttling |
| **HTTP Client** | Requests | 2.32.3 | External API calls |
| **Scheduling** | APScheduler | 3.11.0 | Periodic tasks |
| **Testing** | Pytest | 8.1.1 | Test framework |
| **Deployment** | Docker + Nginx | Latest | Containerization + proxy |
| **Frontend** | Vanilla JavaScript + CSS | ES6+ | Client-side logic |
| **Templates** | Jinja2 | Built-in | Server-side rendering |
| **AI (Optional)** | Google Gemini / OpenAI / Anthropic | Latest | Natural language assistant |

## Architecture Type

**Pattern:** MVC/Layered Architecture with Application Factory

```
┌─────────────────────────────────────────────────┐
│              Flask Application                   │
│                 (app/__init__.py)                │
└─────────────────────────────────────────────────┘
                      │
        ┌─────────────┼─────────────┐
        │             │             │
┌───────▼──────┐ ┌───▼──────┐ ┌───▼─────────┐
│   Routes     │ │ Services  │ │   Models     │
│ (Controllers)│ │(Business) │ │   (Data)     │
│ 23 Blueprints│ │16 Services│ │ 16 Models    │
└──────────────┘ └───────────┘ └──────────────┘
        │             │              │
        └─────────────┼──────────────┘
                      │
        ┌─────────────┼─────────────┐
        │             │             │
┌───────▼──────┐ ┌───▼──────┐ ┌───▼─────────┐
│  Templates   │ │  Static   │ │ Extensions   │
│   (Jinja2)   │ │(CSS/JS)   │ │(db,csrf,etc) │
└──────────────┘ └───────────┘ └──────────────┘
```

## Repository Structure

**Type:** Monolith
**Organization:** Single cohesive codebase with modular components
**Size:** ~80 Python modules, 20+ templates, extensive JavaScript/CSS

## Core Features

### 1. Event Management & Scheduling
- Import events from Crossmark API (crossmark.mvretail.com)
- Manual and automated event assignment
- Real-time conflict detection and resolution
- Schedule validation with business rule enforcement
- Rescheduling and reissue workflows

### 2. Employee Management
- Employee roster with skills and certifications
- Time-off request tracking and approval
- Weekly availability patterns
- Date-specific availability overrides
- Employee termination handling with final date tracking

### 3. Intelligent Auto-Scheduler
- Algorithm-based automatic event assignment
- Skill-matching and workload balancing
- Rotation management (daily Juicer and Primary Lead assignments)
- Confidence scoring for assignments
- Review and approval workflow for auto-assignments

### 4. Availability & Constraints
- Weekly recurring availability patterns
- Time-off calendars
- Event-specific scheduling overrides
- Job requirement enforcement
- Core timeslot coverage requirements

### 5. External API Integrations
- **Crossmark Integration:** Event synchronization from crossmark.mvretail.com
- **Walmart Retail Link:** EDR sales data retrieval with OAuth + MFA
- Session management and token refresh
- Configurable sync intervals and batch processing

### 6. Attendance Tracking
- QR code-based check-in/check-out
- Manual attendance recording
- Unreported event detection
- Attendance reports and analytics

### 7. Reporting & Analytics
- Daily schedule summaries
- Employee workload analytics
- Performance metrics and KPIs
- PDF paperwork generation with EDR data
- CSV export for external systems

### 8. Schedule Validation
- Real-time validation dashboard
- Coverage analysis for core timeslots
- Conflict detection (double-booking, unavailability)
- Business rule violation warnings
- Floating verification widget on all pages

### 9. AI Assistant
- Natural language query interface
- Context-aware responses
- Schedule analysis and suggestions
- Support for multiple LLM providers (Google Gemini, OpenAI, Anthropic)

### 10. System Administration
- Database-driven configuration (SystemSetting model)
- Encrypted credential storage
- Audit logging for all operations
- Health check endpoints
- Session management

## Key Differentiators

1. **Bi-directional External Sync:** Both pull events from Crossmark AND push results back
2. **Intelligent Auto-Scheduling:** Algorithm considers skills, availability, workload, and rotations
3. **Real-Time Validation:** Continuous monitoring with floating widget on all pages
4. **Flexible Availability:** Supports both recurring patterns and specific overrides
5. **Multi-Provider AI:** Choice of Google Gemini, OpenAI, or Anthropic for assistant
6. **EDR Integration:** Automatic sales data integration for event paperwork

## Development Patterns

**Application Factory:**
- `create_app(config_name)` pattern for testability
- Environment-specific configurations (dev/test/prod)

**Blueprint Modularity:**
- 23 blueprints organize routes by domain
- Each blueprint is independently testable

**Service Layer:**
- Business logic isolated from routes
- Services manipulate models, routes orchestrate services

**Model Registry:**
- Dynamic model access via `get_models()`
- Factory pattern for model creation

## Security Features

- CSRF protection on all state-changing operations
- Session-based authentication with secure cookies
- Rate limiting on API endpoints
- Encrypted storage for sensitive credentials (AES-256)
- Security headers in production (HSTS, X-Frame-Options, CSP)
- SQL injection protection via ORM
- Input validation on all user inputs

## Deployment Options

**Docker (Recommended):**
- Multi-container setup with web, database, redis, nginx
- Automated setup scripts for Windows and Linux/Mac
- Production and development configurations
- Health checks and auto-restart

**Manual:**
- Gunicorn with Gevent workers
- PostgreSQL or SQLite database
- Redis for task queue
- Nginx reverse proxy (optional)

## Performance Characteristics

- **Concurrent Workers:** Auto-scaled (2 * CPU cores + 1)
- **Worker Type:** Gevent for async I/O
- **Database Connection Pool:** 10 connections, 20 overflow
- **Rate Limiting:** 100 requests/hour default
- **Caching:** Redis-backed for session and task state
- **Query Optimization:** Indexed date ranges, batch operations

## Documentation

- **API Contracts:** Complete REST API documentation
- **Data Models:** Full database schema with relationships
- **Source Tree:** Annotated directory structure
- **Architecture:** System design and patterns
- **Deployment Guides:** Docker and manual setup
- **Operations:** Restart procedures, maintenance
- **Testing:** Test reports and coverage

## Getting Started

**Quick Start (Docker):**
```bash
# Linux/Mac
./setup.sh

# Windows
setup.bat
```

**Access:**
- Production: http://localhost:8000
- Development: http://localhost:5000

**Default Credentials:**
- Username: mat.conder8135
- Password: Password123!

## Quality Metrics

- **Test Coverage:** Unit and integration tests with pytest
- **Code Quality:** PEP 8 compliant with relaxed line length (120 chars)
- **Documentation:** Comprehensive inline comments and separate docs
- **Error Handling:** Structured error handlers with detailed logging
- **Audit Trail:** Complete audit log for all operations

## Future Roadmap

- Real-time updates via WebSockets
- Mobile app for employee self-service
- Advanced analytics dashboards
- Multi-location support
- Integration with additional external systems
- Enhanced AI capabilities with proactive suggestions

## Support & Maintenance

- Automated backup scripts
- Health monitoring endpoints
- Structured logging (JSON in production)
- Database migration system (Alembic)
- Rollback capabilities

## License & Usage

Internal project - see organization policies for usage guidelines.

---

**Last Updated:** 2025-11-20
**Documentation Version:** 1.0
**Application Version:** 1.2
