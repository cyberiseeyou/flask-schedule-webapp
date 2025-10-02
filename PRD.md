# **Interactive Scheduling Assistant Product Requirements Document (PRD)**

| Date | Version | Description | Author |
| :---- | :---- | :---- | :---- |
| 2025-09-23 | 1.0 | Initial PRD draft based on project brief. | John (PM) |

## **Goals and Background Context**

### **Goals**

* **Automate Availability Checks**: Eliminate the manual, time-consuming process of cross-referencing employee schedules.  
* **Reduce Errors**: Dramatically increase scheduling accuracy by enforcing date ranges and preventing double-bookings.  
* **Centralize Planning**: Provide a single, clear, and prioritized view of all unscheduled work to improve efficiency.  
* **Build a Scalable Foundation**: Create a robust application that can be easily expanded with more complex features in the future.

### **Background Context**

The current scheduling process is manual and error-prone, leading to inefficiencies like double-bookings and scheduling events outside their required timeframes. It relies on cross-referencing multiple lists, which is not scalable. This project aims to solve this by creating a local web application that serves as a smart, centralized planning tool, automating availability checks and enforcing scheduling rules.

## **Requirements**

### **Functional**

1. **FR1**: The system shall display a list of all unscheduled events on the main dashboard, sorted first by start\_date and then by due\_date.  
2. **FR2**: The system shall provide a dedicated, interactive scheduling form for each event.  
3. **FR3**: The date picker on the scheduling form must only allow the selection of dates between the event's specified start\_date and due\_date.  
4. **FR4**: Upon selecting a date, the system shall dynamically fetch and display a list of employees who are not already scheduled for another event on that day.  
5. **FR5**: The system shall validate and save a new schedule to the database, containing the event ID, employee ID, chosen date, and start time.  
6. **FR6**: Upon successfully saving a new schedule, the system shall update the corresponding event's status to is\_scheduled \= True.

### **Non Functional**

1. **NFR1**: The application must run locally on a single machine via a Python script.  
2. **NFR2**: The backend shall be built using the Python Flask web framework.  
3. **NFR3**: The database shall be a local SQLite file, managed via the SQLAlchemy ORM.  
4. **NFR4**: The frontend shall be rendered with standard HTML, CSS, and JavaScript, without a heavy frontend framework.  
5. **NFR5**: The architecture must be designed to be extensible for future enhancements, such as API integration and role-based scheduling.

## **User Interface Design Goals**

* **Overall UX Vision**: The user experience should be clean, efficient, and task-oriented. The primary goal is to make the scheduling process as fast and error-free as possible. The interface should require minimal training.  
* **Key Interaction Paradigms**: The core of the application is a dynamic form. The key interaction is the date selection immediately triggering a filtered list of available employees. This cause-and-effect relationship should be instant and obvious to the user.  
* **Core Screens and Views**:  
  * **Dashboard**: A simple list or table view of unscheduled events.  
  * **Scheduling Page**: A focused form for a single event, containing a date picker, employee dropdown, and time input.  
* **Accessibility**: WCAG AA  
* **Target Device and Platforms**: Web Responsive (Desktop-first, as it's a local tool, but should be usable on smaller screens).

## **Technical Assumptions**

* **Repository Structure**: Monorepo. Since the frontend and backend are tightly coupled for this simple local application, a single repository is the most efficient structure.  
* **Service Architecture**: Monolith. The application is a single Flask service.  
* **Testing Requirements**: Unit \+ Integration. A testing pyramid approach will be followed, with unit tests for business logic (e.g., date validation) and integration tests for database interactions and API endpoints.

## **Epic List**

1. **Epic 1: Core Scheduling Engine & UI**: Establish the foundational Flask application, database models, and implement the complete end-to-end user workflow for scheduling an event.  
2. **Epic 2: Administration & Future-Proofing**: Implement the planned future enhancements, including an admin interface for managing data and API integration capabilities.

## **Epic 1: Core Scheduling Engine & UI**

**Epic Goal**: To deliver a fully functional, local web application that allows a user to view a prioritized list of unscheduled events and schedule them for available employees within the correct date constraints.

### **Story 1.1: Project Setup and Dashboard View**

As a scheduler,  
I want to run the application and see a prioritized list of all unscheduled events,  
so that I have a clear and organized view of the work that needs to be done.

#### **Acceptance Criteria**

1. A Flask application structure is created with required folders and files.  
2. SQLAlchemy is configured and can connect to a local SQLite database file.  
3. The Events, Employees, and Schedules database tables are created based on the data models.  
4. When I navigate to the main dashboard (/), I see a list of all events where is\_scheduled is False.  
5. The list of events is correctly sorted first by start\_date (ascending) and then by due\_date (ascending).

### **Story 1.2: Interactive Scheduling Form**

As a scheduler,  
I want to click on an event from the dashboard and be taken to a dedicated scheduling page,  
so that I can focus on scheduling that single event.

#### **Acceptance Criteria**

1. Each event on the dashboard has a "Schedule" button or link.  
2. Clicking the "Schedule" link navigates to /schedule/\<event\_id\>.  
3. The scheduling page displays the name of the selected event.  
4. The page contains a date picker input field.  
5. Using JavaScript, the date picker is constrained to only allow dates between the event's start\_date and due\_date.

### **Story 1.3: Develop Employee Availability API**

As a frontend developer,  
I want an API endpoint that returns available employees for a specific date,  
so that I can dynamically populate the employee dropdown menu.

#### **Acceptance Criteria**

1. A GET endpoint is created at /api/available\_employees/\<date\>.  
2. When the endpoint is called with a valid date (e.g., 2025-10-30), it returns a JSON response.  
3. The JSON response is a list of all employees who do not have an entry in the Schedules table for that specific date.  
4. Each employee in the JSON list includes their id and name.

### **Story 1.4: Implement Schedule Saving Logic**

As a scheduler,  
I want to select a date, an available employee, and a time, then save the schedule,  
so that the event is successfully scheduled and removed from my to-do list.

#### **Acceptance Criteria**

1. On the scheduling page, selecting a date triggers a JavaScript call to the availability API and populates the "Employee" dropdown.  
2. The form can be submitted via a POST request to /save\_schedule.  
3. The backend validates that the submitted scheduled\_date is within the event's start\_date and due\_date.  
4. If valid, a new record is created in the Schedules table with the correct event\_id, employee\_id, scheduled\_date, and start\_time.  
5. The corresponding record in the Events table has its is\_scheduled flag set to True.  
6. After a successful save, the user is redirected back to the dashboard, which no longer shows the event that was just scheduled.