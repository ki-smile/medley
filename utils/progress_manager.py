"""
Progress Manager for Long Polling
Handles analysis progress events without WebSocket dependencies
"""

import time
import json
import threading
from collections import defaultdict, deque
from typing import Dict, List, Optional, Any
import uuid

class ProgressManager:
    """Thread-safe progress manager for analysis sessions"""
    
    def __init__(self):
        self._events: Dict[str, deque] = defaultdict(lambda: deque(maxlen=100))
        self._session_status: Dict[str, Dict] = {}
        self._lock = threading.Lock()
        self._cleanup_interval = 3600  # Clean up sessions older than 1 hour
        self._last_cleanup = time.time()
    
    def create_session(self) -> str:
        """Create a new analysis session and return session ID"""
        session_id = str(uuid.uuid4())
        with self._lock:
            self._session_status[session_id] = {
                'created_at': time.time(),
                'status': 'created',
                'last_activity': time.time()
            }
        return session_id
    
    def add_event(self, session_id: str, event_type: str, data: Any = None):
        """Add an event for a session"""
        event = {
            'id': str(uuid.uuid4())[:8],
            'timestamp': time.time(),
            'type': event_type,
            'data': data or {}
        }
        
        with self._lock:
            if session_id in self._session_status:
                self._events[session_id].append(event)
                self._session_status[session_id]['last_activity'] = time.time()
    
    def get_events(self, session_id: str, since_id: Optional[str] = None, timeout: float = 30.0) -> List[Dict]:
        """Get events for a session since a specific event ID (long polling)"""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            with self._lock:
                if session_id not in self._events:
                    return []
                
                events = list(self._events[session_id])
                
                # Find events since the specified event ID
                if since_id:
                    start_idx = 0
                    for i, event in enumerate(events):
                        if event['id'] == since_id:
                            start_idx = i + 1
                            break
                    events = events[start_idx:]
                
                if events:
                    return events
            
            # Wait a bit before checking again
            time.sleep(0.5)
        
        # Timeout reached, return empty list
        return []
    
    def get_session_status(self, session_id: str) -> Optional[Dict]:
        """Get current status of a session"""
        with self._lock:
            return self._session_status.get(session_id, None)
    
    def update_session_status(self, session_id: str, status: str, data: Dict = None):
        """Update session status"""
        with self._lock:
            if session_id in self._session_status:
                self._session_status[session_id]['status'] = status
                self._session_status[session_id]['last_activity'] = time.time()
                if data:
                    self._session_status[session_id].update(data)
    
    def cleanup_old_sessions(self):
        """Remove old inactive sessions"""
        current_time = time.time()
        if current_time - self._last_cleanup < 300:  # Only cleanup every 5 minutes
            return
        
        with self._lock:
            expired_sessions = []
            for session_id, status in self._session_status.items():
                if current_time - status['last_activity'] > self._cleanup_interval:
                    expired_sessions.append(session_id)
            
            for session_id in expired_sessions:
                del self._session_status[session_id]
                if session_id in self._events:
                    del self._events[session_id]
            
            self._last_cleanup = current_time
            
            if expired_sessions:
                print(f"🧹 Cleaned up {len(expired_sessions)} expired analysis sessions")

    def get_session_count(self) -> int:
        """Get number of active sessions"""
        with self._lock:
            return len(self._session_status)

# Global progress manager instance
progress_manager = ProgressManager()

# Progress event helper functions
def emit_progress(session_id: str, event_type: str, data: Any = None):
    """Emit a progress event (replaces socketio.emit)"""
    progress_manager.add_event(session_id, event_type, data)

def emit_model_started(session_id: str, model_name: str, model_index: int, total_models: int):
    """Emit model started event"""
    emit_progress(session_id, 'model_started', {
        'model_name': model_name,
        'model_index': model_index,
        'total_models': total_models,
        'message': f'🤖 Starting analysis with {model_name} ({model_index + 1}/{total_models})'
    })

def emit_model_completed(session_id: str, model_name: str, model_index: int, total_models: int, success: bool = True, error: str = None):
    """Emit model completed event"""
    status = 'completed' if success else 'failed'
    message = f'✅ {model_name} analysis completed' if success else f'❌ {model_name} failed: {error}'
    
    emit_progress(session_id, 'model_completed', {
        'model_name': model_name,
        'model_index': model_index,
        'total_models': total_models,
        'status': status,
        'message': message,
        'error': error
    })

def emit_analysis_completed(session_id: str, total_models: int, successful_models: int, report_url: str = None):
    """Emit analysis completed event"""
    emit_progress(session_id, 'analysis_completed', {
        'total_models': total_models,
        'successful_models': successful_models,
        'message': f'🎉 Analysis completed! {successful_models}/{total_models} models successful',
        'report_url': report_url
    })

def emit_progress_update(session_id: str, current_step: int, total_steps: int, message: str):
    """Emit general progress update"""
    emit_progress(session_id, 'progress_update', {
        'current_step': current_step,
        'total_steps': total_steps,
        'progress_percent': int((current_step / total_steps) * 100),
        'message': message
    })