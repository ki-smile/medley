#!/usr/bin/env python
"""
Test script for MEDLEY Web Application Integration
Tests the custom case analysis pipeline with free models
"""

import os
import sys
import json
import time
import requests
from pathlib import Path

# Configuration
BASE_URL = "http://localhost:5000"
API_BASE = f"{BASE_URL}/api"

def test_health_check():
    """Test the health check endpoint"""
    print("Testing health check...")
    response = requests.get(f"{API_BASE}/health")
    if response.status_code == 200:
        data = response.json()
        print(f"✓ Health check passed: {data['status']}")
        print(f"  - Version: {data.get('version', 'N/A')}")
        print(f"  - Cases available: {data.get('statistics', {}).get('total_cases_available', 0)}")
        return True
    else:
        print(f"✗ Health check failed: {response.status_code}")
        return False

def test_get_cases():
    """Test getting list of cases"""
    print("\nTesting get cases...")
    response = requests.get(f"{API_BASE}/cases")
    if response.status_code == 200:
        cases = response.json()
        print(f"✓ Retrieved {len(cases)} cases")
        if cases:
            print(f"  - First case: {cases[0].get('title', 'N/A')}")
        return True
    else:
        print(f"✗ Get cases failed: {response.status_code}")
        return False

def test_analyze_custom_case():
    """Test analyzing a custom case with free models"""
    print("\nTesting custom case analysis (free models only)...")
    
    # Sample medical case
    case_data = {
        "case_text": """
        A 28-year-old male presents to the emergency department with severe chest pain that 
        started suddenly 2 hours ago. The pain is sharp, radiates to his back, and worsens 
        with deep breathing. He reports no fever, cough, or shortness of breath. 
        
        Past medical history is unremarkable. He is tall and thin (6'4", 160 lbs). 
        He mentions his father died suddenly at age 45 from "heart problems."
        
        On examination: BP 140/60 mmHg (right arm), 120/70 mmHg (left arm), HR 95 bpm, 
        RR 20/min, SpO2 98% on room air. Cardiac exam reveals a diastolic murmur. 
        Chest X-ray shows widened mediastinum.
        """,
        "case_title": "Young Male with Acute Chest Pain",
        "use_free_models": True  # Use only free models
    }
    
    # Start analysis
    print("  Sending analysis request...")
    response = requests.post(f"{API_BASE}/analyze", json=case_data)
    
    if response.status_code == 200:
        result = response.json()
        analysis_id = result.get('analysis_id')
        print(f"✓ Analysis started: {analysis_id}")
        print(f"  - Estimated time: {result.get('estimated_time', 'N/A')} seconds")
        print(f"  - WebSocket channel: {result.get('websocket_channel', 'N/A')}")
        
        # Poll for status (in real usage, would use WebSocket)
        print("\n  Polling for status...")
        for i in range(30):  # Poll for up to 30 seconds
            time.sleep(2)
            status_response = requests.get(f"{API_BASE}/analyze/{analysis_id}/status")
            if status_response.status_code == 200:
                status = status_response.json()
                progress = status.get('progress', 0)
                print(f"    Progress: {progress}% - {status.get('status', 'unknown')}")
                
                if status.get('status') == 'completed':
                    print(f"\n✓ Analysis completed successfully!")
                    print(f"  - Models responded: {status.get('results', {}).get('models_responded', 0)}")
                    print(f"  - Primary diagnosis: {status.get('results', {}).get('primary_diagnosis', {}).get('name', 'N/A')}")
                    return True
                elif status.get('status') == 'failed':
                    print(f"\n✗ Analysis failed: {status.get('error', 'Unknown error')}")
                    return False
        
        print("\n⚠ Analysis timed out (still running)")
        return False
    else:
        print(f"✗ Analysis request failed: {response.status_code}")
        if response.text:
            print(f"  Error: {response.text}")
        return False

def test_api_endpoints():
    """Test the REST API endpoints"""
    print("\n" + "="*60)
    print("MEDLEY Web Integration Test Suite")
    print("="*60)
    
    all_passed = True
    
    # Run tests
    if not test_health_check():
        all_passed = False
    
    if not test_get_cases():
        all_passed = False
    
    # Only test analysis if API key is available
    api_key = os.getenv('OPENROUTER_API_KEY')
    if api_key:
        if not test_analyze_custom_case():
            all_passed = False
    else:
        print("\n⚠ Skipping analysis test (no OPENROUTER_API_KEY in environment)")
        print("  To test analysis, set your API key:")
        print("  export OPENROUTER_API_KEY='your-key-here'")
    
    # Summary
    print("\n" + "="*60)
    if all_passed:
        print("✓ All tests passed!")
    else:
        print("✗ Some tests failed. Check the output above.")
    print("="*60)
    
    return all_passed

def main():
    """Main test runner"""
    # Check if server is running
    try:
        response = requests.get(BASE_URL, timeout=2)
        print(f"Server is running at {BASE_URL}")
    except requests.exceptions.RequestException:
        print(f"ERROR: Server is not running at {BASE_URL}")
        print("\nTo start the server, run:")
        print("  python web_app.py")
        sys.exit(1)
    
    # Run tests
    success = test_api_endpoints()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()