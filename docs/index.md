# Flask Schedule Webapp - Documentation Index

**Project Type:** Web Application (Monolith)
**Primary Language:** Python 3.11+
**Framework:** Flask 3.0.3
**Architecture Pattern:** MVC/Layered with Application Factory
**Generated:** 2025-11-20

## Quick Reference

- **Tech Stack:** Flask + PostgreSQL/SQLite + Redis + Celery + Gunicorn
- **Entry Point:** `wsgi.py` (WSGI application)
- **Application Factory:** `app/__init__.py::create_app()`
- **Architecture:** MVC with Blueprint modularity and Service layer
- **External Integrations:** Crossmark API (crossmark.mvretail.com), Walmart Retail Link
- **Database:** 16 models with Alembic migrations
- **API Endpoints:** 50+ REST endpoints across 23 blueprints
- **Deployment:** Docker (recommended) or manual with Gunicorn

## Core Features

1. **Event Management** - Crossmark API sync, scheduling, validation
2. **Employee Management** - Roster, availability, time-off, terminations
3. **Auto-Scheduler** - Intelligent algorithm-based assignment with constraints
4. **Attendance Tracking** - QR code + manual check-in/out
5. **Reporting** - PDF paperwork with EDR data, CSV exports, analytics
6. **AI Assistant** - Natural language interface (Google Gemini/OpenAI/Anthropic)
7. **Schedule Validation** - Real-time conflict detection, coverage analysis
8. **External Sync** - Bidirectional sync with Crossmark and Walmart systems

## Generated Documentation

### Core Documentation
- [Project Overview](./project-overview.md) - Executive summary, tech stack, features
- [Source Tree Analysis](./source-tree-analysis.md) - Complete directory structure with annotations
- [API Contracts](./api-contracts.md) - All REST API endpoints with examples
- [Data Models](./data-models.md) - Database schema, relationships, 16 models

### Architecture Documentation
- [Architectural Optimizations](./architecture/ARCHITECTURAL_OPTIMIZATIONS.md) - System optimizations
- [Optimizations Completed](./architecture/OPTIMIZATIONS_COMPLETED.md) - Optimization tracking
- [Project Root Refactor](./architecture/PROJECT_ROOT_REFACTOR.md) - Restructuring notes

### Deployment Documentation
- [Docker Deployment Guide](./deployment/DOCKER.md) - Docker setup and configuration
- [Deployment Guide](./deployment/DEPLOYMENT.md) - General deployment procedures
- [Production Checklist](./deployment/PRODUCTION_CHECKLIST.md) - Pre-deployment validation

### Operations Documentation
- [Restart Procedures](./operations/RESTART_APP.md) - Application restart guide

### Testing Documentation
- [Test Report](./testing/TEST_REPORT.md) - Test coverage and results

### Integration Documentation
- [Walmart API Integration](../app/integrations/walmart_api/README.md) - Walmart Retail Link docs
- [Walmart API Status](../app/integrations/walmart_api/CURRENT_STATUS.md) - Implementation status
- [EDR Caching Strategy](../app/integrations/edr/CACHING_README.md) - EDR caching docs

### Other Documentation
- [AI Assistant Setup](./AI_ASSISTANT_SETUP.md) - AI configuration guide
- [Import Updates Report](./IMPORT_UPDATES_REPORT.md) - Import functionality changes
- [Project README](../README.md) - Main project documentation

## Project Context Files

These files provide high-level project tracking and status:

- [Project Structure](../.context/project_structure.md) - Structure overview
- [Overall Project Status](../.context/overall_project_status.md) - Current status
- [Feature Checklist](../.context/feature_checklist.md) - Feature tracking
- [Identified Issues](../.context/identified_issues.md) - Known issues
- [Recommendations](../.context/recommendations.md) - Improvement recommendations

## Getting Started

### For New Developers

1. **Read First:**
   - [Project Overview](./project-overview.md) - Understand what the system does
   - [Source Tree Analysis](./source-tree-analysis.md) - Navigate the codebase

2. **Understand the Data:**
   - [Data Models](./data-models.md) - Database schema and relationships

3. **Explore the API:**
   - [API Contracts](./api-contracts.md) - Available endpoints and usage

4. **Deploy Locally:**
   - [Docker Deployment Guide](./deployment/DOCKER.md) - Fastest way to get running
   - Or see [README](../README.md) for manual setup

### For AI-Assisted Development

When planning new features or modifications, reference:

1. **For Backend Changes:**
   - [Data Models](./data-models.md) - Database schema
   - [API Contracts](./api-contracts.md) - Existing endpoints
   - [Source Tree Analysis](./source-tree-analysis.md) - Code organization

2. **For Frontend Changes:**
   - [Source Tree Analysis](./source-tree-analysis.md) - Template and static file locations
   - See `app/templates/` and `app/static/` directories

3. **For Integration Work:**
   - Integration docs in `app/integrations/*/README.md`
   - [API Contracts](./api-contracts.md) - Internal API structure

4. **For Deployment:**
   - [Docker Deployment Guide](./deployment/DOCKER.md)
   - [Production Checklist](./deployment/PRODUCTION_CHECKLIST.md)

## Quick Start Commands

```bash
# Docker setup (recommended)
./setup.sh              # Linux/Mac
setup.bat               # Windows

# Manual setup
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
.venv\Scripts\activate      # Windows
pip install -r requirements.txt
flask db upgrade
python wsgi.py

# Testing
pytest
pytest --cov=app tests/

# Database migrations
flask db migrate -m "Description"
flask db upgrade

# Access
http://localhost:8000  # Production (Docker)
http://localhost:5000  # Development
```

## Default Credentials

- **Username:** mat.conder8135
- **Password:** Password123!

## Key Technologies

### Backend
- **Flask 3.0.3** - Web framework
- **SQLAlchemy 3.1.1** - ORM
- **Alembic** - Database migrations
- **Celery 5.3.6** - Async task queue
- **Redis 5.0.3** - Cache and broker
- **Gunicorn 21.2.0** - WSGI server
- **Gevent 24.2.1** - Async workers

### Database
- **PostgreSQL** - Production database
- **SQLite** - Development/testing database

### Frontend
- **Jinja2** - Template engine
- **Vanilla JavaScript** - Client-side logic (ES6+)
- **Custom CSS** - Responsive design

### External Integrations
- **Crossmark API** - Event synchronization (crossmark.mvretail.com)
- **Walmart Retail Link** - EDR sales data
- **Google Gemini / OpenAI / Anthropic** - AI assistant (optional)

### Deployment
- **Docker** - Containerization
- **Nginx** - Reverse proxy
- **Docker Compose** - Multi-container orchestration

## Architecture Highlights

**Application Factory Pattern:**
- `create_app(config_name)` enables multiple configurations
- Supports development, testing, and production environments

**Blueprint Modularity:**
- 23 blueprints organize routes by domain
- `/api` - REST API endpoints
- `/` - Main views
- `/employees` - Employee management
- `/auto-scheduler` - Automated scheduling
- And 19 more...

**Service Layer:**
- Business logic in `app/services/` (16 service modules)
- Routes delegate to services for complex operations
- Services manipulate models, enforce business rules

**Model Registry:**
- Dynamic model access via `get_models()`
- Factory pattern for testability
- Centralized model management

**External Integration Layer:**
- `app/integrations/` - Isolated external system code
- Session management for API authentication
- Sync engine for bidirectional data flow

## Development Workflow

1. **Feature Development:**
   - Review existing [Data Models](./data-models.md) and [API Contracts](./api-contracts.md)
   - Implement in service layer first
   - Add routes/views
   - Update templates/frontend as needed
   - Write tests

2. **Database Changes:**
   - Modify models in `app/models/`
   - Create migration: `flask db migrate -m "Description"`
   - Review migration script in `migrations/versions/`
   - Apply: `flask db upgrade`

3. **API Changes:**
   - Add/modify routes in appropriate blueprint
   - Update [API Contracts](./api-contracts.md) documentation
   - Add integration tests

4. **Testing:**
   - Unit tests for services and utilities
   - Integration tests for routes
   - Run: `pytest --cov=app tests/`

## Troubleshooting

- **Database Issues:** Check `instance/scheduler.db` exists (dev) or `DATABASE_URL` is set (prod)
- **Import Errors:** Ensure virtual environment is activated
- **API Integration Failures:** Verify credentials in `.env` file
- **Docker Issues:** Check `docker-compose logs -f web`
- **Performance:** Review query patterns in [Data Models](./data-models.md)

## Support Resources

- **Main README:** [../README.md](../README.md)
- **Deployment Guide:** [deployment/DOCKER.md](./deployment/DOCKER.md)
- **Architecture Docs:** `docs/architecture/`
- **Integration Guides:** `app/integrations/*/README.md`

## BMad Method Workflow

**Status Tracking:** [bmm-workflow-status.yaml](./bmm-workflow-status.yaml)

This project uses BMad Method for feature planning:
- **Phase 1 - Planning:** PRD creation
- **Phase 2 - Solutioning:** Architecture and epic breakdown
- **Phase 3 - Implementation:** Sprint planning and development

Current workflow phase and next steps are tracked in the status file.

## Notes

- Timezone: America/Indiana/Indianapolis (configurable)
- Date format: YYYY-MM-DD
- Time format: HH:MM:SS (24-hour)
- All datetime fields are timezone-aware
- CSRF protection enabled on state-changing operations
- Rate limiting: 100 requests/hour (production)

---

**Documentation Generated:** 2025-11-20
**Application Version:** 1.2
**Python Version:** 3.11+
**Status:** Production-Ready
