# **Flask Schedule Webapp Brownfield Architecture Document**

## **Introduction**

This document captures the CURRENT STATE of the Flask Schedule Webapp codebase, including technical debt, workarounds, and real-world patterns. It serves as a reference for AI agents working on enhancements.

### **Document Scope**

Comprehensive documentation of the entire system.

### **Change Log**

|

| Date | Version | Description | Author |  
| 2025-10-02 | 1.0 | Initial brownfield analysis | Mary (Business Analyst) |

## **Quick Reference \- Key Files and Entry Points**

### **Critical Files for Understanding the System**

* **Main Entry**: app.py  
* **Configuration**: config.py, .flaskenv  
* **Core Business Logic**: app/routes.py (Note: Logic is tightly coupled with view functions)  
* **API Definitions**: N/A (The application is a traditional server-rendered web app, not API-centric)  
* **Database Models**: app/models.py  
* **Application Factory**: app/\_\_init\_\_.py

## **High Level Architecture**

### **Technical Summary**

The project is a monolithic web application built using the Flask framework in Python. It uses a server-side rendering approach with Jinja2 templates. Data persistence is handled by SQLAlchemy with a SQLite database for development, and database migrations are managed by Flask-Migrate. The architecture follows a standard simple Flask application pattern where business logic is often located directly within the route handlers.

### **Actual Tech Stack (from requirements.txt)**

| Category | Technology | Version | Notes |  
| Language | Python | 3.x (assumed) | Not specified |  
| Framework | Flask | 2.0.1 | Core web framework |  
| Database ORM | Flask-SQLAlchemy | 2.5.1 | Interacts with the database |  
| Database | SQLite | (default) | Default for development |  
| Migrations | Flask-Migrate | 3.1.0 | Handles database schema changes |  
| Forms | Flask-WTF | 1.0.0 | Form creation and validation |  
| Auth | Flask-Login | 0.5.0 | Manages user sessions |  
| Web Server | gunicorn | 20.1.0 | Production WSGI server |  
| Templating | Jinja2 | 3.0.1 | Server-side HTML templating |  
| Environment | python-dotenv | 0.19.0 | Manages environment variables |

### **Repository Structure Reality Check**

* **Type**: Monolithic Application  
* **Package Manager**: pip  
* **Notable**: Uses a standard Flask application factory pattern (create\_app) inside a package (app/).

## **Source Tree and Module Organization**

### **Project Structure (Actual)**

flask-schedule-webapp/  
├── app/                  \# Main application package  
│   ├── static/           \# Static files (CSS, JS, images)  
│   ├── templates/        \# Jinja2 HTML templates  
│   ├── \_\_init\_\_.py       \# Application factory  
│   ├── forms.py          \# WTForms form definitions  
│   ├── models.py         \# SQLAlchemy database models  
│   └── routes.py         \# Application routes and view logic  
├── migrations/           \# Flask-Migrate migration scripts  
├── .flaskenv             \# Environment variables for 'flask' command  
├── app.py                \# Main application entry point  
├── config.py             \# Configuration settings  
└── requirements.txt      \# Python dependencies

### **Key Modules and Their Purpose**

* **app package**: The core application module.  
* **app/routes.py**: Handles all HTTP request routing and contains the business logic for creating, viewing, and managing users and events.  
* **app/models.py**: Defines the User and Event data structures for the database using SQLAlchemy. Includes password hashing logic.  
* **app/forms.py**: Defines the structure and validation rules for web forms like login, registration, and event creation.  
* **app/\_\_init\_\_.py**: Contains the create\_app factory function, which initializes the Flask app and its extensions. This allows for creating multiple instances of the app for testing or different configurations.

## **Data Models and APIs**

### **Data Models**

The data models are defined declaratively using SQLAlchemy.

* **User Model**: See app/models.py. Contains fields for id, username, email, and password\_hash. Includes methods for setting and checking passwords.  
* **Event Model**: See app/models.py. Contains fields for id, title, start\_time, end\_time, and a user\_id foreign key to link events to users.

### **API Specifications**

* This is not an API-driven application. It is a traditional server-rendered web application where routes in app/routes.py render HTML templates directly.

## **Technical Debt and Known Issues**

### **Critical Technical Debt**

1. **Hardcoded Secret Key**: The SECRET\_KEY in config.py is hardcoded to 'you-will-never-guess'. This is a significant security vulnerability and should be loaded from an environment variable.  
2. **No Automated Tests**: The project lacks a tests/ directory or any form of automated unit or integration testing. This makes refactoring or adding new features risky and prone to regressions.  
3. **Logic Coupled to Routes**: Most of the application's business logic is located inside the view functions in app/routes.py. This makes the logic difficult to test in isolation and reuse. For a larger application, this should be refactored into a separate service or business logic layer.

### **Workarounds and Gotchas**

* The application relies on a .flaskenv file to set FLASK\_APP and FLASK\_ENV. The application will not run correctly with the flask command without it.  
* The default database is SQLite, which is file-based and not suitable for most production environments that require concurrent access.

## **Integration Points and External Dependencies**

### **External Services**

* The application does not integrate with any external APIs or services.

### **Internal Integration Points**

* The application is self-contained. The primary integration is between the Flask application logic and the SQLite database via the SQLAlchemy ORM.

## **Development and Deployment**

### **Local Development Setup**

1. Create a virtual environment and install dependencies from requirements.txt.  
2. Set up the .flaskenv file (already present in the repo).  
3. Run flask db upgrade to apply database migrations and create the app.db file.  
4. Run flask run to start the local development server.

### **Build and Deployment Process**

* **Build Command**: N/A (Python is an interpreted language).  
* **Deployment**: The presence of gunicorn in requirements.txt suggests the intended production deployment command is gunicorn "app:create\_app()".  
* **Environments**: The config.py file uses os.environ.get() to pull in DATABASE\_URL, implying it can be configured for different environments (e.g., development, production).

## **Testing Reality**

### **Current Test Coverage**

* Unit Tests: None.  
* Integration Tests: None.  
* E2E Tests: None.  
* Manual Testing is the only method for QA.

### **Running Tests**

* No test runner or framework is configured.

## **Appendix \- Useful Commands and Scripts**

### **Frequently Used Commands**

\# Install dependencies  
pip install \-r requirements.txt

\# Apply database migrations  
flask db upgrade

\# Start development server  
flask run

