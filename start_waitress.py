"""
Start the Flask Schedule Webapp using Waitress (Windows-compatible production server)

Usage:
    python start_waitress.py
"""
from waitress import serve
from wsgi import app

if __name__ == '__main__':
    print("=" * 60)
    print("Flask Schedule Webapp - Starting with Waitress")
    print("=" * 60)
    print()
    print("Server starting on http://localhost:8000")
    print("Press Ctrl+C to stop the server")
    print()

    # Serve the application
    serve(app, host='0.0.0.0', port=8000, threads=4)
