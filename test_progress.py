#!/usr/bin/env python
"""Test script to verify individual model progress events are working"""

import requests
import json
import time
import threading

def monitor_progress(session_id):
    """Monitor progress events using long polling"""
    print(f"📡 Monitoring progress for session {session_id}")
    last_event_id = None
    
    while True:
        try:
            # Long poll for events
            params = {'timeout': 30}
            if last_event_id:
                params['since_id'] = last_event_id
            
            response = requests.get(
                f'http://localhost:5001/api/progress/{session_id}/events',
                params=params,
                timeout=35
            )
            
            if response.status_code == 200:
                data = response.json()
                events = data.get('events', [])
                
                for event in events:
                    last_event_id = event['id']
                    event_type = event['type']
                    event_data = event.get('data', {})
                    
                    # Display different event types
                    if event_type == 'model_started':
                        model_name = event_data.get('model_name', 'Unknown')
                        model_index = event_data.get('model_index', 0)
                        total_models = event_data.get('total_models', 0)
                        print(f"🚀 Model Started: {model_name} ({model_index + 1}/{total_models})")
                    
                    elif event_type == 'model_completed':
                        model_name = event_data.get('model_name', 'Unknown')
                        status = event_data.get('status', 'unknown')
                        error = event_data.get('error', '')
                        if status == 'completed':
                            print(f"✅ Model Completed: {model_name}")
                        else:
                            print(f"❌ Model Failed: {model_name} - {error}")
                    
                    elif event_type == 'model_progress':
                        progress = event_data.get('progress', 0)
                        message = event_data.get('message', '')
                        print(f"📊 Progress: {progress}% - {message}")
                    
                    elif event_type == 'analysis_completed':
                        successful = event_data.get('successful_models', 0)
                        total = event_data.get('total_models', 0)
                        print(f"🎉 Analysis Complete: {successful}/{total} models successful")
                        return  # Stop monitoring
                    
                    else:
                        print(f"📨 Event: {event_type} - {event_data.get('message', '')}")
            
            elif response.status_code == 404:
                print("❌ Session not found")
                break
                
        except requests.exceptions.Timeout:
            print("⏱️ Long poll timeout, retrying...")
        except Exception as e:
            print(f"❌ Error monitoring progress: {e}")
            time.sleep(2)

def start_analysis():
    """Start a new analysis and return the session ID"""
    
    # Start a new analysis
    case_text = """
    Patient: 45-year-old male
    Chief Complaint: Recurring fever and abdominal pain
    
    History: Episodes of fever (up to 39°C), severe abdominal pain lasting 2-3 days,
    occurring every 3-4 weeks for the past year. Pain is diffuse, worse in lower quadrants.
    Family history: Father had similar episodes. Patient is of Mediterranean descent.
    
    Physical Exam: During episode - fever 38.8°C, diffuse abdominal tenderness, 
    no rebound tenderness, no organomegaly.
    
    Labs: During attack - WBC 15,000, CRP 120 mg/L, ESR 80 mm/hr
    Between attacks - all labs normal
    """
    
    print("🚀 Starting new analysis...")
    response = requests.post('http://localhost:5001/api/analyze', json={
        'case_text': case_text,
        'case_title': 'Test Case - FMF',
        'use_free_models': True
    })
    
    if response.status_code == 200:
        data = response.json()
        session_id = data.get('progress_session_id')
        analysis_id = data.get('analysis_id')
        print(f"✅ Analysis started: {analysis_id}")
        print(f"📡 Progress session: {session_id}")
        return session_id
    else:
        print(f"❌ Failed to start analysis: {response.status_code}")
        print(response.text)
        return None

def main():
    """Main test function"""
    print("=" * 60)
    print("MEDLEY Progress Events Test")
    print("=" * 60)
    
    # Start analysis
    session_id = start_analysis()
    
    if session_id:
        # Monitor progress in a separate thread
        monitor_thread = threading.Thread(target=monitor_progress, args=(session_id,))
        monitor_thread.daemon = True
        monitor_thread.start()
        
        # Wait for completion
        monitor_thread.join(timeout=300)  # 5 minute timeout
        
        if monitor_thread.is_alive():
            print("⏱️ Test timed out after 5 minutes")
    
    print("=" * 60)
    print("Test Complete")
    print("=" * 60)

if __name__ == "__main__":
    main()