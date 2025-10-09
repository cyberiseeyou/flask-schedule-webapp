"""
Create a test session for EDR testing without external API authentication
"""
from datetime import datetime
import secrets
import requests

# Create session data
session_id = secrets.token_urlsafe(32)
session_data = {
    'user_id': 'test_user',
    'user_info': {
        'username': 'test_user',
        'userId': 'test_user',
        'authenticated': True
    },
    'created_at': datetime.utcnow().isoformat(),
    'crossmark_authenticated': False  # Mock session without real API auth
}

# Send session creation request to Flask app
# We'll do this by making a POST request to a custom endpoint
print(f"Session ID: {session_id}")
print(f"Session Data: {session_data}")
print("\nTo use this session, set a cookie in your browser:")
print(f"  Name: session_id")
print(f"  Value: {session_id}")
print(f"  Domain: 127.0.0.1")
print(f"  Path: /")
