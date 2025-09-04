#!/usr/bin/env python
"""
Start MEDLEY Web Application with HTTPS
"""

import os
import sys
import ssl
from pathlib import Path

# Add current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

# Set Flask environment variables
os.environ['FLASK_APP'] = 'web_app.py'
os.environ['FLASK_DEBUG'] = '1'

# Import and run the app
from web_app import app, socketio

if __name__ == '__main__':
    print("=" * 60)
    print("Starting MEDLEY Web Application with HTTPS")
    print("=" * 60)
    print("\n📌 Access the application at:")
    print("   https://localhost:5001")
    print("   https://127.0.0.1:5001")
    print("\n⚠️  Chrome Users:")
    print("   1. You'll see a security warning (self-signed certificate)")
    print("   2. Click 'Advanced' then 'Proceed to localhost (unsafe)'")
    print("\n🔧 Alternative for Chrome:")
    print("   Type in address bar: chrome://flags/#allow-insecure-localhost")
    print("   Enable 'Allow invalid certificates for localhost'")
    print("\nPress Ctrl+C to stop the server")
    print("=" * 60)
    
    # Create SSL context
    context = ssl.SSLContext(ssl.PROTOCOL_TLS)
    context.load_cert_chain('cert.pem', 'key.pem')
    
    try:
        # Run with HTTPS
        socketio.run(
            app, 
            debug=False, 
            host='0.0.0.0',  # Allow all interfaces
            port=5001, 
            use_reloader=False, 
            allow_unsafe_werkzeug=True,
            ssl_context=context
        )
    except KeyboardInterrupt:
        print("\nShutting down server...")
    except Exception as e:
        print(f"Error starting server: {e}")
        sys.exit(1)