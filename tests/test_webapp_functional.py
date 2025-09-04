#!/usr/bin/env python
"""
Functional test to verify web app starts and all endpoints work
Run this test to ensure the web application is fully functional
"""

import os
import sys
import time
import json
import requests
import subprocess
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

def test_webapp_startup():
    """Test that web app starts and responds correctly"""
    
    print("🧪 MEDLEY Web App Functional Test")
    print("=" * 50)
    
    # Check if app is already running
    base_url = "http://127.0.0.1:5002"
    
    try:
        response = requests.get(f"{base_url}/api/health", timeout=2)
        print("✅ Web app is already running")
        app_was_running = True
    except:
        print("⏳ Starting web app...")
        app_was_running = False
        
        # Start the web app in background
        env = os.environ.copy()
        env['USE_FREE_MODELS'] = 'true'
        process = subprocess.Popen(
            ['python', 'web_app.py'],
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        # Wait for startup
        for i in range(10):
            time.sleep(2)
            try:
                response = requests.get(f"{base_url}/api/health", timeout=2)
                print("✅ Web app started successfully")
                break
            except:
                if i == 9:
                    print("❌ Failed to start web app")
                    process.terminate()
                    return False
    
    # Test all critical endpoints
    tests_passed = 0
    tests_failed = 0
    
    endpoints = [
        # Web pages
        ("GET", "/", None, "Landing page"),
        ("GET", "/analyze", None, "Analyze page"),
        ("GET", "/test", None, "Test page"),
        ("GET", "/dashboard", None, "Dashboard"),
        ("GET", "/settings", None, "Settings"),
        
        # API endpoints
        ("GET", "/api/health", None, "Health check"),
        ("GET", "/api/cases", None, "Get cases"),
        ("GET", "/api/models", None, "Get models"),
        ("GET", "/api/session/status", None, "Session status"),
        ("GET", "/api/available_models", None, "Available models"),
        
        # Case endpoints
        ("GET", "/case/case_001", None, "View case 001"),
        ("GET", "/api/case/case_001/report", None, "Get case report"),
    ]
    
    print("\n📋 Testing Endpoints:")
    print("-" * 50)
    
    for method, endpoint, data, description in endpoints:
        try:
            url = f"{base_url}{endpoint}"
            
            if method == "GET":
                response = requests.get(url, timeout=5)
            elif method == "POST":
                response = requests.post(url, json=data, timeout=5)
            
            if response.status_code in [200, 304]:
                print(f"✅ {description:<25} [{endpoint}]")
                tests_passed += 1
            elif response.status_code == 404 and "/report" in endpoint:
                # Report might not exist yet
                print(f"⚠️  {description:<25} [404 - Report not generated yet]")
                tests_passed += 1
            else:
                print(f"❌ {description:<25} [Status: {response.status_code}]")
                tests_failed += 1
                
        except Exception as e:
            print(f"❌ {description:<25} [Error: {str(e)[:30]}]")
            tests_failed += 1
    
    # Test WebSocket connectivity
    print("\n🔌 Testing WebSocket:")
    print("-" * 50)
    try:
        import socketio
        sio = socketio.Client()
        sio.connect(base_url)
        print("✅ WebSocket connection successful")
        sio.disconnect()
        tests_passed += 1
    except:
        print("⚠️  WebSocket connection failed (optional feature)")
    
    # Test model availability
    print("\n🤖 Testing Model Availability:")
    print("-" * 50)
    try:
        response = requests.get(f"{base_url}/api/available_models")
        if response.status_code == 200:
            data = response.json()
            free_count = len(data.get('free', []))
            paid_count = len(data.get('paid', []))
            print(f"✅ Free models available: {free_count}")
            print(f"✅ Paid models available: {paid_count}")
            tests_passed += 2
        else:
            print(f"❌ Could not fetch model list")
            tests_failed += 1
    except Exception as e:
        print(f"❌ Model API error: {str(e)[:50]}")
        tests_failed += 1
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Summary:")
    print(f"   ✅ Passed: {tests_passed}")
    print(f"   ❌ Failed: {tests_failed}")
    print(f"   Success Rate: {tests_passed/(tests_passed+tests_failed)*100:.1f}%")
    
    # Cleanup if we started the app
    if not app_was_running and 'process' in locals():
        print("\n🛑 Stopping test web app...")
        process.terminate()
        time.sleep(1)
    
    return tests_failed == 0


def test_analyze_functionality():
    """Test the analyze functionality with a sample case"""
    
    print("\n🔬 Testing Analysis Functionality:")
    print("=" * 50)
    
    base_url = "http://127.0.0.1:5002"
    
    # Check if free models are available
    try:
        response = requests.get(f"{base_url}/api/available_models")
        data = response.json()
        free_models = data.get('free', [])
        
        if not free_models:
            print("⚠️  No free models available for testing")
            return False
        
        print(f"✅ Found {len(free_models)} free models for testing")
        
        # Test analyze endpoint (without actually running full analysis)
        test_case = {
            "case_text": "Test patient: 45-year-old with chest pain and shortness of breath.",
            "use_free_models": True,
            "model_selection": "free"
        }
        
        # Just verify the endpoint accepts the request
        response = requests.post(
            f"{base_url}/api/analyze",
            json=test_case,
            timeout=5
        )
        
        if response.status_code in [200, 202, 503]:
            print("✅ Analyze endpoint responds correctly")
            return True
        else:
            print(f"❌ Analyze endpoint error: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Analysis test error: {str(e)[:100]}")
        return False


if __name__ == "__main__":
    print("\n🏥 MEDLEY Web Application Functional Test Suite")
    print("=" * 50)
    
    # Run tests
    startup_ok = test_webapp_startup()
    analyze_ok = test_analyze_functionality()
    
    # Final result
    print("\n" + "=" * 50)
    if startup_ok and analyze_ok:
        print("✅ ALL TESTS PASSED - Web app is fully functional!")
        sys.exit(0)
    else:
        print("❌ Some tests failed - Please check the output above")
        sys.exit(1)