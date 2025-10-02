# **Interactive Scheduling Assistant Fullstack Architecture Document (v2.0 FINAL)**

| Date | Version | Description | Author |
| :---- | :---- | :---- | :---- |
| 2025-09-23 | 1.0 | Initial architecture draft. | Winston (Architect) |
| 2025-09-23 | 2.0 | Revised with CSV data models and import/export functionality. | Winston (Architect) |

## **Introduction**

This document outlines the complete fullstack architecture for the Interactive Scheduling Assistant, including the backend system, frontend implementation, and their integration. It serves as the single source of truth for AI-driven development, ensuring consistency across the entire technology stack.

### **Starter Template or Existing Project**

N/A \- This is a greenfield project. Given the requirements for a lightweight, local application using Python/Flask and plain JavaScript, we will proceed with a custom setup from scratch. This approach avoids unnecessary complexity from starter templates and is perfectly suited for the project's scope.

## **High Level Architecture**

### **Technical Summary**

The application will be a lightweight, monolithic web application running on the user's local machine. It follows a classic client-server model, with a **Python Flask server** handling business logic and data persistence, and a browser-based frontend built with standard **HTML, CSS, and JavaScript**. Data will be stored in a local **SQLite** database, accessed via the **SQLAlchemy ORM**. The core functionality relies on an asynchronous JavaScript call to a backend API to fetch available employees, creating an interactive and efficient user experience. **It will now also support bulk import of unscheduled events from a CSV file and export of the completed schedule to a CSV file.**

### **Repository Structure**

* **Structure**: **Monorepo**. A single repository is the most efficient structure for a simple, tightly-coupled local application, containing both the backend and frontend code.

### **High Level Architecture Diagram**

graph TD  
    subgraph User's Local Machine  
        subgraph Web Browser  
            A\[Dashboard UI\] \--\> B\[Scheduling Form UI\];  
            A \-- Click \--\> Z1\[Import Events Button\];  
            A \-- Click \--\> Z2\[Export Schedule Button\];  
            Z1 \-- Opens File Dialog \--\> Z3\[Uploads WorkBankVisits.csv\];  
            Z3 \-- POST /api/import/events \--\> E;  
            Z2 \-- GET /api/export/schedule \--\> E;

            B \-- 1\. Selects Date \--\> C\[JavaScript\];  
            C \-- 2\. AJAX GET Request \--\> D\[Flask API: /api/available\_employees\];  
            D \-- 3\. Returns JSON \--\> C;  
            C \-- 4\. Populates Dropdown \--\> B;  
            B \-- 5\. POST Form Data \--\> E\[Flask Route: /save\_schedule\];  
        end

        subgraph Backend Server  
            D \--\> F\[SQLAlchemy ORM\];  
            E \--\> F;  
            F \--\> G\[SQLite Database File\];  
        end  
    end

### **Architectural and Design Patterns**

* **Monolith**: The entire application (backend and frontend logic) is managed within a single codebase and runs as a single process. This is ideal for its simplicity and ease of local deployment.  
* **Client-Server**: A standard model where the client (web browser) makes requests to the server (Flask application) for data and to perform actions.  
* **ORM (Object-Relational Mapping)**: SQLAlchemy will be used to abstract database interactions, allowing us to work with Python objects instead of raw SQL, which improves code readability and maintainability.

## **Tech Stack**

| Category | Technology | Version | Purpose |
| :---- | :---- | :---- | :---- |
| Backend Language | Python | 3.11+ | Core application logic. |
| Web Framework | Flask | 2.3+ | Lightweight web server for routing and handling requests. |
| Database ORM | SQLAlchemy | 2.0+ | Interfacing with the database using Python objects. |
| Database | SQLite | 3.3+ | Serverless, file-based database requiring no setup. |
| Frontend | HTML5 / CSS3 | latest | Structure and styling of the user interface. |
| Frontend Scripting | JavaScript (ES6+) | latest | Handling user interactions and API calls. |
| Testing | Pytest | 7.4+ | Unit and integration testing for the Flask backend. |

## **Data Models**

**The data models have been updated to precisely match the columns in your provided CSV files.**

### **1\. Events**

* **Purpose**: Represents an unscheduled task imported from WorkBankVisits.csv.  
* **Key Attributes**:  
  * id: Integer, Primary Key  
  * project\_name: String (from Project Name)  
  * project\_ref\_num: Integer, Unique (from Project Reference Number)  
  * location\_mvid: String (from Location MVID)  
  * store\_number: Integer (from Store Number)  
  * store\_name: String (from Store Name)  
  * start\_datetime: DateTime (from Start Date/Time)  
  * due\_datetime: DateTime (from Due Date/Time)  
  * estimated\_time: Integer (from Estimated Time)  
  * is\_scheduled: Boolean (default: False)

### **2\. Employees**

* **Purpose**: Represents a staff member who can be scheduled. The initial list of employees will be extracted from the provided CalendarSchedule.csv.  
* **Key Attributes**:  
  * id: String, Primary Key (from Employee ID)  
  * name: String (from Rep Name)

### **3\. Schedules**

* **Purpose**: Links an event to an employee, representing a scheduled item for the export.  
* **Key Attributes**:  
  * id: Integer, Primary Key  
  * event\_ref\_num: Integer, Foreign Key (Events.project\_ref\_num)  
  * employee\_id: String, Foreign Key (Employees.id)  
  * schedule\_datetime: DateTime (from Schedule Date/Time)

## **API Specification (OpenAPI 3.0)**

openapi: 3.0.0  
info:  
  title: Interactive Scheduler API  
  version: 1.1.0  
paths:  
  /:  
    get:  
      summary: Get Dashboard  
      description: Renders the main dashboard with a list of unscheduled events.  
  /schedule/{event\_id}:  
    get:  
      summary: Get Scheduling Page  
      parameters:  
        \- in: path  
          name: event\_id  
          required: true  
          schema:  
            type: integer  
      description: Renders the interactive scheduling form for a single event.  
  /api/available\_employees/{date}:  
    get:  
      summary: Get Available Employees  
      parameters:  
        \- in: path  
          name: date  
          required: true  
          schema:  
            type: string  
            format: date  
      description: Returns a JSON list of employees available on a given date.  
      responses:  
        '200':  
          description: A list of employees.  
          content:  
            application/json:  
              schema:  
                type: array  
                items:  
                  type: object  
                  properties:  
                    id:  
                      type: integer  
                    name:  
                      type: string  
  /save\_schedule:  
    post:  
      summary: Save a new schedule  
      description: Creates a new schedule record in the database.  
      requestBody:  
        content:  
          application/x-www-form-urlencoded:  
            schema:  
              type: object  
              properties:  
                event\_id:  
                  type: integer  
                employee\_id:  
                  type: integer  
                scheduled\_date:  
                  type: string  
                  format: date  
                start\_time:  
                  type: string  
      responses:  
        '302':  
          description: Redirects back to the dashboard on success.  
  /api/import/events:  
    post:  
      summary: Import unscheduled events from CSV  
      requestBody:  
        content:  
          multipart/form-data:  
            schema:  
              type: object  
              properties:  
                file:  
                  type: string  
                  format: binary  
      responses:  
        '200':  
          description: Import successful, returns count of imported events.  
        '400':  
          description: Bad request (e.g., wrong file type, bad data).  
  /api/export/schedule:  
    get:  
      summary: Export scheduled events to CSV  
      responses:  
        '200':  
          description: A CSV file of the current schedule.  
          content:  
            text/csv:  
              schema:  
                type: string

## **Database Schema (SQL DDL)**

**The database schema is updated to reflect the final data models.**

CREATE TABLE employees (  
    id VARCHAR(50) PRIMARY KEY,  
    name VARCHAR(100) NOT NULL  
);

CREATE TABLE events (  
    id INTEGER PRIMARY KEY AUTOINCREMENT,  
    project\_name TEXT NOT NULL,  
    project\_ref\_num INTEGER NOT NULL UNIQUE,  
    location\_mvid TEXT,  
    store\_number INTEGER,  
    store\_name TEXT,  
    start\_datetime DATETIME NOT NULL,  
    due\_datetime DATETIME NOT NULL,  
    estimated\_time INTEGER,  
    is\_scheduled BOOLEAN NOT NULL DEFAULT 0  
);

CREATE TABLE schedules (  
    id INTEGER PRIMARY KEY AUTOINCREMENT,  
    event\_ref\_num INTEGER NOT NULL,  
    employee\_id VARCHAR(50) NOT NULL,  
    schedule\_datetime DATETIME NOT NULL,  
    FOREIGN KEY (event\_ref\_num) REFERENCES events (project\_ref\_num),  
    FOREIGN KEY (employee\_id) REFERENCES employees (id)  
);

\-- Index for performance on the availability query  
CREATE INDEX idx\_schedules\_date ON schedules (schedule\_datetime);

## **Backend Logic**

### **CSV Import (/api/import/events)**

1. The endpoint receives a WorkBankVisits.csv file upload.  
2. The backend will first populate the Employees table using the unique Rep Name and Employee ID combinations from the provided CalendarSchedule.csv data. This is a one-time setup step.  
3. It will then parse the uploaded WorkBankVisits.csv, mapping columns to the Events data model.  
4. It will create new records in the Events table, using the Project Reference Number to avoid importing duplicates.

### **CSV Export (/api/export/schedule)**

1. The endpoint queries the database, performing a JOIN across the schedules, events, and employees tables.  
2. The query will select all data required to build the CalendarSchedule.csv format.  
3. The backend will construct a CSV file in memory with the exact headers from your example (Project Name, Project Reference Number, etc.).  
4. It will return this data as a downloadable file named CalendarSchedule.csv.

## **Unified Project Structure**

/scheduler\_app  
├── app.py                  \# Main Flask application file  
├── requirements.txt        \# Python dependencies  
├── instance/  
│   └── scheduler.db        \# SQLite database file will be created here  
├── static/  
│   ├── css/  
│   │   └── style.css       \# Main stylesheet  
│   └── js/  
│       └── main.js         \# Main JavaScript for interactivity  
└── templates/  
    ├── index.html          \# Dashboard page  
    └── schedule.html       \# Scheduling page

## **Security and Performance**

* **Security**: Backend validation will be implemented on the /save\_schedule route to prevent invalid data submission. SQLAlchemy automatically uses parameterized queries, which prevents SQL injection vulnerabilities.  
* **Performance**: For a local, single-user application, performance is not a primary concern. However, an index will be added to the schedule\_datetime column in the Schedules table to ensure the employee availability API remains fast as the data grows.