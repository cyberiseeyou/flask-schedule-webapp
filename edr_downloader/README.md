# EDR Downloader

A lightweight Flask web application for downloading Event Detail Reports (EDR) from Walmart's Retail Link Event Management System.

## Overview

The EDR Downloader automates the process of retrieving and generating PDF reports for CORE events scheduled on specific dates. It authenticates with Walmart's Retail Link using multi-factor authentication (MFA), fetches event data from their API, and generates professional PDF documents suitable for printing and employee signatures.

## Features

- **Multi-Factor Authentication**: Secure SMS-based MFA for Walmart Retail Link access
- **Date-Based Event Filtering**: Query CORE events by scheduled date
- **Automated PDF Generation**: Creates formatted EDR reports with:
  - Event details (number, type, date, status)
  - Item information (numbers, descriptions, vendors)
  - Employee signature sections
- **Batch Processing**: Downloads all EDR reports for a selected date in one operation
- **Error Handling**: Graceful handling of partial failures with detailed error reporting

## Architecture

```
edr_downloader/
├── app.py              # Main Flask application with API endpoints
├── config.py           # Configuration settings and credentials
├── models.py           # Database models (Event, Schedule, Employee)
├── edr_auth.py         # Walmart authentication and PDF generation
├── templates/          # HTML templates
│   └── index.html      # Main UI
├── static/             # Static assets
│   ├── css/
│   │   └── style.css   # Application styles
│   └── js/
│       └── main.js     # Frontend JavaScript
├── instance/
│   └── scheduler.db    # SQLite database
├── temp_edrs/          # Output directory for generated PDFs
└── README.md           # This file
```

### Components

1. **Flask Web Application** (`app.py`)
   - Serves web interface
   - Provides RESTful API endpoints
   - Coordinates authentication and report generation

2. **EDRAuthenticator** (`edr_auth.py`)
   - Handles Walmart Retail Link authentication
   - Manages MFA flow (SMS OTP)
   - Fetches EDR data from Event Management API

3. **EDRPDFGenerator** (`edr_auth.py`)
   - Converts EDR JSON data to PDF documents
   - Formats event and item details
   - Creates signature sections for employees

4. **Database Models** (`models.py`)
   - Read-only access to scheduler database
   - Query events, schedules, and employees

## Installation

### Prerequisites

- Python 3.8 or higher
- Access to the scheduler database (`instance/scheduler.db`)
- Walmart Retail Link credentials with MFA enabled

### Setup

1. **Navigate to EDR Downloader Directory**
   ```bash
   cd edr_downloader
   ```

2. **Create Virtual Environment (Recommended)**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Dependencies**
   ```bash
   pip install flask flask-sqlalchemy python-decouple reportlab requests
   ```

4. **Configure Environment Variables**

   Create a `.env` file in the `edr_downloader` directory:
   ```env
   SECRET_KEY=your-random-secret-key-here
   WALMART_EDR_USERNAME=your.email@company.com
   WALMART_EDR_PASSWORD=YourSecurePassword123!
   WALMART_EDR_MFA_CREDENTIAL_ID=your-mfa-credential-id
   ```

   **Important**:
   - Never commit credentials to version control
   - Use strong, unique passwords
   - Rotate credentials regularly

5. **Verify Database Access**

   Ensure the scheduler database exists:
   ```bash
   # Database should be at: edr_downloader/instance/scheduler.db
   ls -l instance/scheduler.db
   ```

## Usage

### Starting the Server

```bash
cd edr_downloader
python app.py
```

The application will start on `http://0.0.0.0:5001` (port 5001 to avoid conflict with the main scheduler).

### Web Interface Workflow

1. **Open the Application**
   - Navigate to `http://localhost:5001`

2. **Authenticate**
   - Click "Request MFA Code"
   - Wait for SMS code (30-60 seconds)
   - Enter the 6-digit code
   - Click "Authenticate"

3. **Download EDRs**
   - Select a date from the date picker
   - Click "Get Events" to preview events (optional)
   - Click "Download EDRs" to generate all PDFs
   - PDFs are saved to `temp_edrs/` folder

### API Endpoints

#### POST /api/request-mfa
Request MFA code to be sent via SMS.

**Request:** No body required

**Response:**
```json
{
  "success": true,
  "message": "MFA code sent to your phone"
}
```

#### POST /api/authenticate
Complete authentication with MFA code.

**Request:**
```json
{
  "mfa_code": "123456"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Authentication successful"
}
```

#### POST /api/get-events
Get CORE events for a specific date.

**Request:**
```json
{
  "date": "2024-01-15"
}
```

**Response:**
```json
{
  "success": true,
  "count": 3,
  "events": [
    {
      "id": 123,
      "project_name": "456789 - Food Demo at Store",
      "event_number": "456789",
      "store_name": "Walmart Supercenter #1234",
      "scheduled_datetime": "2024-01-15T10:00:00"
    }
  ]
}
```

#### POST /api/download-edrs
Download EDR PDFs for all CORE events on a date.

**Request:**
```json
{
  "date": "2024-01-15"
}
```

**Response:**
```json
{
  "success": true,
  "downloaded": 2,
  "failed": 1,
  "files": [
    {
      "project_name": "123456 - Food Demo",
      "event_number": "123456",
      "filename": "123456 - Food Demo.pdf"
    }
  ],
  "errors": [
    {
      "project_name": "789012 - Beverage Demo",
      "event_number": "789012",
      "error": "Failed to retrieve EDR data"
    }
  ]
}
```

## Configuration

### Environment Variables

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `SECRET_KEY` | Flask secret key for sessions | No | `edr-downloader-secret-key` |
| `WALMART_EDR_USERNAME` | Walmart Retail Link username | Yes | - |
| `WALMART_EDR_PASSWORD` | Walmart Retail Link password | Yes | - |
| `WALMART_EDR_MFA_CREDENTIAL_ID` | MFA credential identifier | Yes | - |

### Database Configuration

The application expects the scheduler database at:
```
edr_downloader/instance/scheduler.db
```

This is a read-only connection to the main scheduler database containing:
- Events (work assignments)
- Schedules (employee assignments)
- Employees (staff information)

### Output Directory

PDFs are saved to:
```
edr_downloader/temp_edrs/
```

This directory is automatically created on startup if it doesn't exist.

## Authentication Flow

The EDR Downloader uses a multi-step authentication process:

1. **Submit Credentials** - Username and password sent to Walmart login API
2. **Request MFA Code** - SMS OTP code requested
3. **Validate MFA Code** - User enters code from SMS
4. **Register Page Access** - Analytics tracking (optional)
5. **Navigate to Event Management** - Establish navigation flow
6. **Obtain Auth Token** - Extract Bearer token for API requests

### MFA Credential ID

The MFA Credential ID can be found in your Walmart Retail Link account settings:
1. Log in to Retail Link
2. Go to Account Settings → Security
3. Find the MFA/2FA section
4. Copy the Credential ID (typically a 10-12 digit number)

## PDF Report Format

Generated PDFs include:

### Event Details Section
- Event Number
- Event Type (translated from code)
- Event Locked Status
- Event Status (translated from code)
- Event Date
- Event Name

### Items Section
Table with columns:
- Item Number
- Primary Item Number (GTIN)
- Description
- Vendor Number
- Category (Department)

### Signature Section
- Scheduled Employee (pre-filled)
- Employee Signature (blank line)
- Date Performed (blank line)
- Supervisor Signature (blank line)

## Troubleshooting

### Authentication Issues

**Problem**: "Failed to submit password"
- **Solution**: Verify credentials in `.env` file
- Check for typos in username/password
- Ensure account is not locked

**Problem**: "Invalid MFA code"
- **Solution**:
  - Verify you entered the code correctly
  - Codes expire after 5-10 minutes - request a new one
  - Check for delays in SMS delivery

**Problem**: "Failed to authenticate with Event Management"
- **Solution**:
  - Your session may have expired - restart authentication
  - Check network connectivity
  - Verify account has access to Event Management

### Database Issues

**Problem**: "Database not found"
- **Solution**:
  - Verify database path: `edr_downloader/instance/scheduler.db`
  - Check database file permissions
  - Ensure you're running from the correct directory

**Problem**: "No CORE events found for this date"
- **Solution**:
  - Verify the date has scheduled CORE events
  - Check the `event_type` field in the database
  - Ensure schedules exist for the selected date

### PDF Generation Issues

**Problem**: "Failed to generate PDF"
- **Solution**:
  - Check disk space in `temp_edrs/` directory
  - Verify write permissions on output directory
  - Review logs for specific error messages

**Problem**: "Could not extract event number"
- **Solution**:
  - Event names must contain a 6-digit number
  - Check `project_name` format in database
  - Manually verify event name follows pattern: "123456 - Description"

## Security Considerations

### Credential Management

- **Never commit credentials** to version control
- Use `.env` files (add to `.gitignore`)
- Rotate passwords regularly
- Use strong, unique passwords
- Enable MFA on all accounts

### Network Security

- Application binds to `0.0.0.0` for development
- For production:
  - Use a reverse proxy (nginx, Apache)
  - Enable HTTPS/TLS
  - Implement rate limiting
  - Add authentication to web interface

### Session Management

- Auth tokens persist in memory during server runtime
- Restart server to clear authentication state
- Implement token expiration for production use

## Development

### Running in Debug Mode

The application runs in debug mode by default:
```python
app.run(debug=True, host='0.0.0.0', port=5001)
```

For production, set `debug=False` and use a production WSGI server:
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5001 app:app
```

### Logging

Logs are output to console with INFO level:
```python
logging.basicConfig(level=logging.INFO)
```

For production, configure file-based logging:
```python
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('edr_downloader.log'),
        logging.StreamHandler()
    ]
)
```

### Code Documentation

All Python files include comprehensive docstrings and inline comments:
- **config.py**: Configuration settings and environment variables
- **models.py**: Database models with field descriptions
- **app.py**: API endpoints with request/response formats
- **edr_auth.py**: Authentication flow and PDF generation

### Testing

Test individual components:

```python
# Test authentication
from edr_auth import EDRAuthenticator
auth = EDRAuthenticator(username, password, mfa_cred_id)
auth.step1_submit_password()
auth.step2_request_mfa_code()
# Enter MFA code
auth.step3_validate_mfa_code("123456")
# ... complete remaining steps

# Test PDF generation
from edr_auth import EDRPDFGenerator
gen = EDRPDFGenerator()
edr_data = {...}  # Sample EDR data
gen.generate_pdf(edr_data, "test.pdf", "John Doe")
```

## Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| Flask | >= 2.0 | Web framework |
| Flask-SQLAlchemy | >= 2.5 | Database ORM |
| python-decouple | >= 3.6 | Environment variable management |
| reportlab | >= 3.6 | PDF generation |
| requests | >= 2.27 | HTTP requests to Walmart API |

## License

Internal use only - Product Connections proprietary software.

## Support

For issues or questions:
1. Check the Troubleshooting section
2. Review application logs
3. Contact the development team

## Version History

### Version 1.0 (Current)
- Initial release
- MFA authentication with Walmart Retail Link
- Date-based event filtering
- Batch PDF generation
- Error handling and reporting
- Comprehensive code documentation

## Future Enhancements

Potential improvements for future versions:
- Web-based PDF viewer
- Email delivery of generated PDFs
- Scheduled automated downloads
- Support for additional event types
- Integration with main scheduler UI
- User authentication and access control
- Audit logging of downloads
- PDF archiving and retrieval

## How It Works

### Workflow

1. **Date Selection**: User selects a date from the date picker
2. **Database Query**: Application queries for CORE events scheduled on that date
3. **Event Number Extraction**: Extracts 6-digit event numbers from project names
4. **MFA Authentication**: User authenticates with Walmart Retail Link
5. **EDR Download**: For each event:
   - Fetches EDR data from Walmart API
   - Looks up assigned employee
   - Generates PDF with all details
6. **Results**: Summary of successful and failed downloads

### Data Flow

```
User Browser
    ↓ (Select Date)
Flask API
    ↓ (Query Database)
SQLite Database
    ↓ (Return Events)
Flask API
    ↓ (Authenticate)
Walmart Retail Link
    ↓ (Return Auth Token)
Flask API
    ↓ (Fetch EDR Data)
Walmart Event Management API
    ↓ (Return EDR JSON)
PDF Generator
    ↓ (Generate PDF)
temp_edrs/ folder
```

## Technology Stack

- **Backend**: Flask (Python web framework)
- **Database**: SQLite with SQLAlchemy ORM
- **PDF Generation**: ReportLab
- **HTTP Client**: Requests library
- **Frontend**: HTML5, CSS3, Vanilla JavaScript
- **Authentication**: Walmart Retail Link MFA (SMS-based)
- **Configuration**: python-decouple for environment variables
