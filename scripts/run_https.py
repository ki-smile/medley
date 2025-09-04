#!/usr/bin/env python
"""
Run MEDLEY with HTTPS support
Creates self-signed certificate for local development
"""

import os
import ssl
from pathlib import Path

# Import the Flask app
from web_app import app, socketio

def create_self_signed_cert():
    """Create a self-signed certificate for HTTPS"""
    cert_dir = Path("certs")
    cert_dir.mkdir(exist_ok=True)
    
    cert_file = cert_dir / "cert.pem"
    key_file = cert_dir / "key.pem"
    
    if not cert_file.exists() or not key_file.exists():
        print("Creating self-signed certificate...")
        import subprocess
        
        # Generate self-signed certificate
        subprocess.run([
            "openssl", "req", "-x509", "-newkey", "rsa:4096",
            "-keyout", str(key_file),
            "-out", str(cert_file),
            "-days", "365",
            "-nodes",
            "-subj", "/C=SE/ST=Stockholm/L=Stockholm/O=MEDLEY/CN=localhost"
        ])
        
        print(f"Certificate created: {cert_file}")
        print(f"Key created: {key_file}")
    
    return str(cert_file), str(key_file)

if __name__ == '__main__':
    # Create SSL context
    cert_file, key_file = create_self_signed_cert()
    
    # Configure SSL context
    ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    ssl_context.load_cert_chain(cert_file, key_file)
    
    print("\n" + "="*60)
    print("🔒 MEDLEY HTTPS Server Starting")
    print("="*60)
    print(f"📍 URL: https://localhost:5001/")
    print(f"📍 Alternative: https://127.0.0.1:5001/")
    print("\n⚠️  Note: Browser will show security warning (self-signed cert)")
    print("   Click 'Advanced' → 'Proceed to localhost' to continue")
    print("="*60 + "\n")
    
    # Run with SSL
    socketio.run(
        app,
        host='0.0.0.0',
        port=5001,
        debug=False,
        ssl_context=ssl_context,
        allow_unsafe_werkzeug=True
    )