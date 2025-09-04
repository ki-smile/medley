#!/usr/bin/env python
"""
Start MEDLEY Web Application
"""

import os
import sys
from pathlib import Path

# Add current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

# Set Flask environment variables
os.environ['FLASK_APP'] = 'web_app.py'
os.environ['FLASK_ENV'] = 'development'

# Import and run the app
from web_app import app, socketio

if __name__ == '__main__':
    print("Starting MEDLEY Web Application...")
    print("Server will be available at: http://127.0.0.1:5000")
    print("Press Ctrl+C to stop the server")
    
    try:
        socketio.run(app, debug=False, host='127.0.0.1', port=5000, use_reloader=False, allow_unsafe_werkzeug=True)
    except KeyboardInterrupt:
        print("\nShutting down server...")
    except Exception as e:
        print(f"Error starting server: {e}")
        sys.exit(1)