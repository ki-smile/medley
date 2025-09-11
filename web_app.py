#!/usr/bin/env python
"""
MEDLEY Web Application
Material 3 Expressive Design Interface for Medical AI Ensemble System
"""

import os
import json
import hashlib
import csv
import io
import requests
import fcntl
import atexit
import signal
import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from flask import Flask, render_template, request, jsonify, send_file, session, Response
# Socket.IO removed - using long polling instead
from flask_cors import CORS
from flask_session import Session
from src.medley.utils.validators import ResponseValidator
from flask_compress import Compress
from flask_caching import Cache
from dotenv import load_dotenv
from model_metadata_2025 import get_comprehensive_model_metadata

# Import progress manager for long polling
from utils.progress_manager import progress_manager

# Import the web orchestrator
try:
    from web_orchestrator import WebOrchestrator
    web_orchestrator_available = True
except ImportError:
    web_orchestrator_available = False
    WebOrchestrator = None

orchestrator = None

# Load environment variables
load_dotenv()

# Process lock to prevent multiple instances
LOCK_FILE = '/tmp/medley_web_app.lock'
lock_file = None

def is_process_running(pid):
    """Check if a process with given PID is still running"""
    try:
        # Send signal 0 to check if process exists (doesn't kill the process)
        os.kill(int(pid), 0)
        return True
    except (OSError, ValueError):
        return False

def acquire_lock():
    """Acquire an exclusive lock to prevent multiple instances with PID validation"""
    global lock_file
    
    # Check if lock file exists and validate the PID
    if os.path.exists(LOCK_FILE):
        try:
            with open(LOCK_FILE, 'r') as f:
                existing_pid = f.read().strip()
            
            if existing_pid and is_process_running(existing_pid):
                print(f"❌ Another MEDLEY instance is already running (PID: {existing_pid})")
                return False
            else:
                print(f"🧹 Removing stale lock file (PID {existing_pid} no longer running)")
                os.unlink(LOCK_FILE)
        except (IOError, ValueError) as e:
            print(f"⚠️ Error reading lock file, removing it: {e}")
            try:
                os.unlink(LOCK_FILE)
            except OSError:
                pass
    
    # Create new lock file
    try:
        lock_file = open(LOCK_FILE, 'w')
        fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        lock_file.write(str(os.getpid()))
        lock_file.flush()
        print(f"🔒 Acquired process lock (PID: {os.getpid()})")
        return True
    except (IOError, OSError) as e:
        print(f"❌ Failed to acquire lock: {e}")
        if lock_file:
            lock_file.close()
        return False

def release_lock():
    """Release the process lock"""
    global lock_file
    if lock_file:
        try:
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)
            lock_file.close()
            os.unlink(LOCK_FILE)
            print(f"🔓 Released process lock")
        except (IOError, OSError):
            pass
    lock_file = None

def signal_handler(signum, frame):
    """Handle termination signals gracefully"""
    print(f"\n⚠️ Received signal {signum}, cleaning up...")
    release_lock()
    sys.exit(0)

def setup_error_handling():
    """Set up comprehensive error handling and cleanup"""
    # Register cleanup on normal exit
    atexit.register(release_lock)
    
    # Register signal handlers for graceful shutdown
    signal.signal(signal.SIGTERM, signal_handler)  # Termination signal
    signal.signal(signal.SIGINT, signal_handler)   # Ctrl+C
    
    # Handle SIGUSR1 and SIGUSR2 if available (Unix systems)
    if hasattr(signal, 'SIGUSR1'):
        signal.signal(signal.SIGUSR1, signal_handler)
    if hasattr(signal, 'SIGUSR2'):
        signal.signal(signal.SIGUSR2, signal_handler)

# Acquire lock or exit
if not acquire_lock():
    print("⚠️ Exiting to prevent conflicts with running instance")
    exit(1)

# Set up comprehensive error handling and cleanup
setup_error_handling()

# Import security utilities
from utils.security import InputValidator, RateLimiter, SecurityHeaders, SessionSecurity

# Import database management
try:
    from src.database.models import init_database
    db_available = True
except ImportError:
    db_available = False
    init_database = None

# Initialize Flask app
app = Flask(__name__, 
    static_folder='static',
    template_folder='templates'
)

# Configuration
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'medley-demo-key-2025')
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_PERMANENT'] = False
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=2)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['TEMPLATES_AUTO_RELOAD'] = True  # Force template reload
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0  # Disable caching

# Performance configuration
app.config['COMPRESS_MIMETYPES'] = [
    'text/html', 'text/css', 'text/xml', 'application/json',
    'application/javascript', 'text/javascript', 'image/svg+xml'
]
app.config['COMPRESS_LEVEL'] = 6  # Balanced compression
app.config['COMPRESS_MIN_SIZE'] = 500  # Only compress files > 500 bytes

# Cache configuration  
app.config['CACHE_TYPE'] = 'simple'
app.config['CACHE_DEFAULT_TIMEOUT'] = 300  # 5 minutes

# Initialize extensions
Session(app)
compress = Compress(app)
cache = Cache(app)
CORS(app)

# Environment detection
IS_PRODUCTION = os.path.exists('/.dockerenv') or os.getenv('FLASK_ENV') == 'production'

# SocketIO Configuration: Dummy implementation for long polling mode
# SocketIO removed - using long polling instead via progress_manager
class DummySocketIO:
    """Dummy SocketIO class for compatibility with existing code - integrates with progress_manager"""
    def __init__(self, app, **kwargs):
        self.app = app
        self._current_session_id = None
        
    def emit(self, event, data=None, room=None, namespace=None, **kwargs):
        """Emit method that forwards to progress_manager for long polling"""
        # Map SocketIO events to progress manager events
        if self._current_session_id and event in ['progress_update', 'model_started', 'model_completed', 'analysis_completed', 'analysis_error']:
            # Extract relevant data from the SocketIO event
            if isinstance(data, dict):
                progress_manager.add_event(self._current_session_id, event, data)
            else:
                progress_manager.add_event(self._current_session_id, event, {'message': str(data) if data else ''})
        
    def set_session_id(self, session_id):
        """Set the current session ID for progress events"""
        self._current_session_id = session_id
        
    def on(self, event):
        """Dummy decorator - returns the function unchanged"""
        def decorator(f):
            return f
        return decorator
        
    def run(self, app, **kwargs):
        """Run the Flask app normally without SocketIO"""
        # Filter out SocketIO-specific parameters
        flask_kwargs = {k: v for k, v in kwargs.items() 
                       if k not in ['allow_unsafe_werkzeug']}
        app.run(**flask_kwargs)

if IS_PRODUCTION:
    print("🐳 Production/Docker environment detected")
    print("📡 Using long polling instead of SocketIO for production")
    socketio = DummySocketIO(app)
else:
    print("💻 Local development environment detected")  
    print("📡 Using long polling instead of SocketIO for development")
    socketio = DummySocketIO(app)

# Global variables for SocketIO management
connected_clients = set()
global_socketio = socketio  # Global reference for pipeline access

# Enhanced helper function for thread-safe WebSocket emission
def safe_socketio_emit(event, data, room=None):
    """Simplified SocketIO emission for production vs development."""
    if not connected_clients:
        print(f"⚠️ No clients connected - skipping {event} emission")
        return False
        
    try:
        if IS_PRODUCTION:
            # Production: Use gevent spawn for non-blocking emission
            try:
                import gevent
                gevent.spawn(lambda: socketio.emit(event, data, room=room))
            except ImportError:
                socketio.emit(event, data, room=room)
        else:
            # Development: Direct emission with threading
            socketio.emit(event, data, room=room)
            
        print(f"✅ Emitted {event} to {len(connected_clients)} clients")
        return True
    except (BrokenPipeError, ConnectionResetError, OSError) as socket_error:
        print(f"⚠️ WebSocket connection lost during {event} emission: {socket_error}")
        return False
    except Exception as emit_error:
        print(f"❌ Error emitting {event}: {emit_error}")
        return False

# Helper function to validate model response success
def is_model_response_valid(response_dict):
    """Check if a model response is valid and successful using enhanced validation"""
    # Check for basic presence of response and absence of error
    if not response_dict.get('response') or response_dict.get('error'):
        return False
    
    # Use enhanced medical response validation
    response_text = response_dict.get('response', '')
    return ResponseValidator.validate_medical_response(response_text)

# Add security headers to all responses
@app.after_request
def add_security_headers(response):
    return SecurityHeaders.add_security_headers(response)

# Initialize database
db_manager = None
if db_available:
    db_manager = init_database()

# Constants - Environment-aware paths
import os
# Smart path detection: use /app if we're in Docker, otherwise current directory
APP_BASE_DIR = os.getenv('APP_BASE_DIR')
if APP_BASE_DIR:
    BASE_DIR = Path(APP_BASE_DIR)
elif Path('/app').exists() and Path('/app/web_app.py').exists():
    # We're likely in Docker container
    BASE_DIR = Path('/app')
else:
    # Local development
    BASE_DIR = Path('.')
    
print(f"🗂️  BASE_DIR set to: {BASE_DIR.absolute()}", flush=True)
CACHE_DIR = BASE_DIR / "cache" / "responses"
REPORTS_DIR = BASE_DIR / "reports"
USECASES_DIR = BASE_DIR / "usecases"

# Ensure critical directories exist
try:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True) 
    USECASES_DIR.mkdir(parents=True, exist_ok=True)
    print(f"✅ Directory structure verified: cache={CACHE_DIR.exists()}, reports={REPORTS_DIR.exists()}, usecases={USECASES_DIR.exists()}", flush=True)
except Exception as e:
    print(f"⚠️  Could not create directories: {e}", flush=True)

# Initialize the web orchestrator if available
if web_orchestrator_available:
    orchestrator = WebOrchestrator(
        socketio=socketio,
        cache_dir=CACHE_DIR,
        reports_dir=REPORTS_DIR,
        usecases_dir=USECASES_DIR,
        db_manager=db_manager
    )

# Pre-defined cases mapping
PREDEFINED_CASES = {
    "case_001": {
        "id": "Case_1",
        "title": "Familial Mediterranean Fever",
        "file": "case_001_fmf.txt",
        "specialty": "Rheumatology",
        "complexity": "High",
        "description": "Young adult with recurrent fever and abdominal pain"
    },
    "case_002": {
        "id": "Case_2", 
        "title": "Elderly Complex Multi-morbidity",
        "file": "case_002_elderly_complex.txt",
        "specialty": "Geriatrics",
        "complexity": "Very High",
        "description": "82-year-old with fatigue and multiple conditions"
    },
    "case_003": {
        "id": "Case_3",
        "title": "Socioeconomic Health Disparities",
        "file": "case_003_homeless_tb.txt",
        "specialty": "Social Medicine",
        "complexity": "High",
        "description": "Homeless individual with chronic cough"
    },
    "case_004": {
        "id": "Case_4",
        "title": "Marfan Syndrome",
        "file": "case_004_marfan.txt",
        "specialty": "Medical Genetics",
        "complexity": "High",
        "description": "Tall adolescent with cardiovascular symptoms"
    },
    "case_005": {
        "id": "Case_5",
        "title": "Lead Poisoning",
        "file": "case_005_lead_poisoning.txt",
        "specialty": "Environmental Medicine",
        "complexity": "Medium",
        "description": "Child with developmental delays in old housing"
    },
    "case_006": {
        "id": "Case_6",
        "title": "Thrombotic Thrombocytopenic Purpura",
        "file": "case_006_ttp.txt",
        "specialty": "Hematology",
        "complexity": "Very High",
        "description": "Young woman with fever, confusion, and low platelets"
    },
    "case_007": {
        "id": "Case_7",
        "title": "Melioidosis",
        "file": "case_007_melioidosis.txt",
        "specialty": "Tropical Medicine",
        "complexity": "High",
        "description": "Farmer with pneumonia after monsoon flooding"
    },
    "case_008": {
        "id": "Case_8",
        "title": "Porphyria",
        "file": "case_008_porphyria.txt",
        "specialty": "Metabolic Medicine",
        "complexity": "High",
        "description": "Recurrent abdominal pain and neurological symptoms"
    },
    "case_009": {
        "id": "Case_9",
        "title": "Thyroid Storm",
        "file": "case_009_thyroid_storm.txt",
        "specialty": "Endocrinology",
        "complexity": "Critical",
        "description": "Acute hyperthyroidism with cardiac compromise"
    },
    "case_010": {
        "id": "Case_10",
        "title": "Long COVID Syndrome",
        "file": "case_010_long_covid.txt",
        "specialty": "Post-Infectious",
        "complexity": "Medium",
        "description": "Persistent symptoms after COVID-19 infection"
    },
    "case_011": {
        "id": "Case_11",
        "title": "Kawasaki Disease",
        "file": "case_011_kawasaki.txt",
        "specialty": "Pediatric Rheumatology",
        "complexity": "High",
        "description": "Child with prolonged fever and rash"
    },
    "case_012": {
        "id": "Case_12",
        "title": "Familial Mediterranean Fever - Male",
        "file": "case_012_fmf_male.txt",
        "specialty": "Rheumatology",
        "complexity": "High",
        "description": "26-year-old male with recurrent fever and abdominal pain"
    },
    "case_013": {
        "id": "Case_13",
        "title": "Complex Glomerulonephritis",
        "file": "case_013_complex_urology.txt",
        "specialty": "Nephrology/Rheumatology",
        "complexity": "High",
        "description": "24-year-old male with recurrent hematuria and renal dysfunction"
    }
}

# Model performance tracking (in-memory for demo)
model_performance = {}

@app.route('/')
def index():
    """Landing page with system explanation"""
    # Use updated template with all changes
    return render_template('index.html', cases=PREDEFINED_CASES)

@app.route('/test')
def test():
    """Test page to verify server is working"""
    return render_template('test.html')

@app.route('/testcase/<case_key>')
def test_case(case_key):
    """Test case route to debug routing issues"""
    print(f"TEST CASE ROUTE: case_key = {case_key}")
    return f"Test case route works! Case key: {case_key}"

@app.route('/case/<case_key>')
def view_case(case_key):
    """View individual case report"""
    app.logger.info(f"🔍 view_case called with case_key: {case_key}")
    print(f"🔍 view_case called with case_key: {case_key}", flush=True)
    
    # Check predefined cases first (to avoid conflicts with case_ prefix)
    if case_key in PREDEFINED_CASES:
        print(f"DEBUG: Found predefined case: {case_key}")
        return render_template('case_viewer.html', case_id=case_key)
    
    # Check if it's a custom case (starts with custom_, Case_, or case_)
    if case_key.startswith('custom_') or case_key.startswith('Case_') or case_key.startswith('case_'):
        app.logger.info(f"🎯 Custom case detected: {case_key}")
        print(f"🎯 Custom case detected: {case_key}", flush=True)
        
        # Check if custom case exists in active analyses or reports
        if orchestrator:
            app.logger.info(f"🤖 Orchestrator exists, checking analysis status")
            print(f"🤖 Orchestrator exists, checking analysis status", flush=True)
            try:
                analysis_status = orchestrator.get_analysis_status(case_key)
                app.logger.info(f"📊 Analysis status: {analysis_status}")
                print(f"📊 Analysis status: {analysis_status}", flush=True)
                if 'error' not in analysis_status:
                    # Custom case exists
                    app.logger.info(f"✅ Returning orchestrator-based case viewer")
                    print(f"✅ Returning orchestrator-based case viewer", flush=True)
                    return render_template('case_viewer.html', 
                        case_id=case_key, 
                        is_custom=True,
                        analysis_status=analysis_status)
            except Exception as e:
                app.logger.error(f"❌ Orchestrator error: {e}")
                print(f"❌ Orchestrator error: {e}", flush=True)
        else:
            app.logger.info(f"📁 No orchestrator, falling back to JSON files")
            print(f"📁 No orchestrator, falling back to JSON files", flush=True)
        
        # Check if report exists - look for exact match or with _ensemble_data suffix
        app.logger.info(f"🔍 Looking for JSON files with pattern: {case_key}_ensemble_data.json")
        print(f"🔍 Looking for JSON files with pattern: {case_key}_ensemble_data.json", flush=True)
        json_files = list(REPORTS_DIR.glob(f"{case_key}_ensemble_data.json"))
        app.logger.info(f"📂 Found JSON files: {json_files}")
        print(f"📂 Found JSON files: {json_files}", flush=True)
        
        if not json_files:
            # Also check for older format
            app.logger.info(f"🔍 Checking older format: {case_key}_ensemble_data_*.json")
            print(f"🔍 Checking older format: {case_key}_ensemble_data_*.json", flush=True)
            json_files = list(REPORTS_DIR.glob(f"{case_key}_ensemble_data_*.json"))
            app.logger.info(f"📂 Found older format files: {json_files}")
            print(f"📂 Found older format files: {json_files}", flush=True)
        
        if json_files:
            app.logger.info(f"📄 Loading JSON data from {len(json_files)} files")
            print(f"📄 Loading JSON data from {len(json_files)} files", flush=True)
            try:
                # Load the JSON data to pass to template
                latest_json = max(json_files, key=lambda p: p.stat().st_mtime) if len(json_files) > 1 else json_files[0]
                print(f"DEBUG: Loading JSON from: {latest_json}")
                
                with open(latest_json, 'r') as f:
                    ensemble_data = json.load(f)
                print(f"DEBUG: JSON loaded successfully, keys: {list(ensemble_data.keys()) if isinstance(ensemble_data, dict) else 'Not a dict'}")
                
                # Check for PDF
                pdf_files = list(REPORTS_DIR.glob(f"FINAL_{case_key}_*.pdf"))
                has_pdf = len(pdf_files) > 0
                print(f"DEBUG: PDF files found: {has_pdf}")
                
                print(f"DEBUG: Returning JSON-based case viewer")
                return render_template('case_viewer.html', 
                    case_id=case_key, 
                    is_custom=True,
                    has_report=True,
                    ensemble_data=ensemble_data,
                    has_pdf=has_pdf)
            except Exception as e:
                print(f"DEBUG: Error loading JSON: {e}")
                return render_template('error.html',
                    title="Case Data Error",
                    message=f"Error loading case data: {str(e)}",
                    subtitle="The case data file appears to be corrupted or inaccessible."
                ), 500
        
        print(f"DEBUG: No JSON files found, showing custom case not found error")
        return render_template('error.html',
            title="Custom Case Not Found",
            message=f"The custom case '{case_key}' could not be found.",
            subtitle="This case may have been automatically cleaned up after 2 days, or the analysis may not have completed successfully."
        ), 404
    
    # Case not found
    print(f"DEBUG: Case not found: {case_key}")
    return render_template('error.html',
        title="Case Not Found", 
        message=f"The case '{case_key}' does not exist.",
        subtitle="Please check the case name and try again."
    ), 404

@app.route('/share/<share_id>')
def view_shared_analysis(share_id):
    """View analysis via shareable link"""
    if not db_manager:
        return "Database not available", 503
    
    try:
        analysis_data = db_manager.get_shareable_analysis(share_id)
        
        if not analysis_data:
            return render_template('error.html', 
                title='Shared Link Expired',
                message='This shared analysis link has expired or is no longer available.',
                subtitle='Shared links expire after 24 hours or after 100 views.')
        
        # Render the shared analysis view
        return render_template('shared_analysis.html', 
            analysis_id=analysis_data['id'],
            analysis=analysis_data,
            is_shared=True)
    
    except Exception as e:
        return render_template('error.html',
            title='Error Loading Shared Analysis',
            message=f'An error occurred: {str(e)}')

@app.route('/api/cases')
@cache.cached(timeout=600)  # Cache for 10 minutes
def get_cases():
    """Get list of pre-defined cases (excluding custom cases)"""
    cases = []
    for case_key, case_info in PREDEFINED_CASES.items():
        # Skip custom cases - they shouldn't appear in the main list
        if case_info.get('custom', False) or case_key.startswith('custom_'):
            continue
            
        # Check if we have cached results
        case_id = case_info['id']
        report_pattern = f"FINAL_{case_id}_*.pdf"
        existing_reports = list(REPORTS_DIR.glob(report_pattern))
        
        case_data = {
            **case_info,
            "key": case_key,
            "has_report": len(existing_reports) > 0,
            "report_date": None
        }
        
        if existing_reports:
            latest_report = max(existing_reports, key=lambda p: p.stat().st_mtime)
            case_data["report_date"] = datetime.fromtimestamp(
                latest_report.stat().st_mtime
            ).strftime("%Y-%m-%d %H:%M")
        
        cases.append(case_data)
    
    return jsonify(cases)

@app.route('/api/case/<case_key>/report')
def get_case_report(case_key):
    """Get HTML version of case report"""
    
    # Check predefined cases first 
    if case_key in PREDEFINED_CASES:
        # Predefined case
        case_info = PREDEFINED_CASES[case_key].copy()  # Make a copy to preserve all fields including title
        case_id = case_info['id']
    elif case_key.startswith('custom_') or case_key.startswith('Case_') or case_key.startswith('case_'):
        # Custom case handling
        case_info = {
            'id': case_key,
            'title': 'Custom Analysis',
            'specialty': 'Custom',
            'complexity': 'Variable',
            'description': 'User-submitted case analysis'
        }
        case_id = case_key
    else:
        return jsonify({"error": "Case not found"}), 404
    
    # Find the latest ensemble data
    json_files = []
    
    # First, try to find in reports directory (legacy location)
    json_pattern = f"{case_id}_ensemble_data.json"
    json_files = list(REPORTS_DIR.glob(json_pattern))
    
    # If not found, try with wildcard in reports directory
    if not json_files:
        json_pattern = f"{case_id}_ensemble_data_*.json"
        json_files = list(REPORTS_DIR.glob(json_pattern))
    
    # Fallback: If glob with wildcard fails, manually search for the file
    if not json_files:
        # List all files and filter manually (workaround for glob issues)
        all_files = list(REPORTS_DIR.glob("*.json"))
        json_files = [f for f in all_files if f.name.startswith(f"{case_id}_ensemble_data")]
    
    # If still not found, try orchestrator cache directory
    if not json_files:
        orchestrator_cache_dir = BASE_DIR / "cache" / "orchestrator" / case_id
        if orchestrator_cache_dir.exists():
            json_files = list(orchestrator_cache_dir.glob("orchestrator_analysis_*.json"))
    
    if not json_files:
        return jsonify({"error": "No report available for this case"}), 404
    
    latest_json = max(json_files, key=lambda p: p.stat().st_mtime)
    
    with open(latest_json, 'r') as f:
        ensemble_data = json.load(f)
    
    # Process model responses to extract which models support each diagnosis
    ensemble_data = enrich_diagnosis_with_models(ensemble_data)
    
    # Transform data for HTML display
    report_data = {
        "case_info": case_info,
        "ensemble_data": ensemble_data,
        "generated_at": datetime.fromtimestamp(
            latest_json.stat().st_mtime
        ).strftime("%Y-%m-%d %H:%M:%S")
    }
    
    # Create response with cache-busting headers
    response = jsonify(report_data)
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

def normalize_diagnosis_name(diagnosis):
    """Normalize diagnosis names to handle variations"""
    if not diagnosis:
        return diagnosis
        
    # Convert to string and strip whitespace
    diag = str(diagnosis).strip()
    
    # Common normalizations
    normalizations = {
        "Crohn's Disease": "Crohn Disease",
        "Crohn disease": "Crohn Disease", 
        "Inflammatory bowel disease": "Inflammatory Bowel Disease",
        "IBD": "Inflammatory Bowel Disease",
        "Familial Mediterranean fever": "Familial Mediterranean Fever",
        "FMF": "Familial Mediterranean Fever",
        "Systemic Lupus Erythematosus": "Systemic Lupus Erythematosus",
        "SLE": "Systemic Lupus Erythematosus",
        "Adult-Onset Still's Disease": "Adult-Onset Still's Disease",
        "AOSD": "Adult-Onset Still's Disease",
        "Behçet's Disease": "Behçet's Disease",
        "Behcet's Disease": "Behçet's Disease",
        "Behcet Disease": "Behçet's Disease",
    }
    
    # Check if diagnosis matches any normalization
    for variant, normalized in normalizations.items():
        if diag.lower() == variant.lower():
            return normalized
    
    # Handle IBD with Crohn's specifically
    if "crohn" in diag.lower():
        return "Crohn Disease"
    elif "inflammatory bowel" in diag.lower() or "ibd" in diag.lower():
        return "Inflammatory Bowel Disease"
    
    return diag

def generate_analysis_html_report(ensemble_data, analysis_id):
    """Generate HTML report matching the case detail format"""
    
    # Extract data from ensemble results
    diagnostic_landscape = ensemble_data.get('diagnostic_landscape', {})
    primary = diagnostic_landscape.get('primary_diagnosis', {})
    alternatives = diagnostic_landscape.get('strong_alternatives', [])
    all_alternatives = diagnostic_landscape.get('all_alternative_diagnoses', [])
    
    model_responses = ensemble_data.get('model_responses', [])
    consensus = ensemble_data.get('consensus_analysis', {})
    
    # Calculate statistics - use same criteria as comprehensive report
    total_models = len(model_responses)
    successful_models = sum(1 for r in model_responses if is_model_response_valid(r))
    failed_models = total_models - successful_models
    success_rate = (successful_models / total_models * 100) if total_models > 0 else 0
    
    # Check if free models or orchestrator were used and generate disclaimers
    free_models_disclaimer = ""
    free_models_used = ensemble_data.get('free_models_used', False)
    free_orchestrator_used = ensemble_data.get('orchestrator_used_free_models', False)
    
    if free_models_used or free_orchestrator_used:
        disclaimer_parts = []
        if free_models_used:
            disclaimer_parts.append("free AI models")
        if free_orchestrator_used:
            disclaimer_parts.append("a free orchestrator")
        
        disclaimer_text = " and ".join(disclaimer_parts)
        free_models_disclaimer = f'''
                <div style="background: #fff3cd; border: 1px solid #ffeaa7; border-radius: 6px; padding: 15px; margin: 15px 0; font-size: 0.85em;">
                    <p style="margin: 0; color: #856404;"><strong>⚠️ Free Model Disclaimer:</strong> 
                    This analysis was generated using {disclaimer_text}, which may provide suboptimal results. 
                    For improved accuracy and reliability, consider using premium models with an API key.</p>
                </div>'''
    
    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>MEDLEY Analysis Report - {analysis_id}</title>
        <style>
            body {{ 
                font-family: system-ui, -apple-system, sans-serif; 
                margin: 0; 
                padding: 40px; 
                background: #f5f5f5;
                color: #333; 
            }}
            .container {{ 
                max-width: 1200px; 
                margin: 0 auto; 
                background: white;
                border-radius: 12px;
                padding: 40px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }}
            .header {{ 
                background: linear-gradient(135deg, #2E7D32, #43A047); 
                color: white; 
                padding: 30px; 
                border-radius: 12px; 
                margin-bottom: 30px; 
                text-align: center;
            }}
            .header h1 {{ margin: 0 0 10px 0; font-size: 2.5em; }}
            .header p {{ margin: 5px 0; opacity: 0.9; }}
            
            .section {{ 
                margin: 30px 0; 
                padding: 25px; 
                background: #f9f9f9; 
                border-radius: 8px; 
                border-left: 4px solid #2E7D32;
            }}
            .section h2 {{ 
                color: #2E7D32; 
                margin-top: 0; 
                font-size: 1.8em;
                display: flex;
                align-items: center;
                gap: 10px;
            }}
            
            .diagnosis-card {{
                background: white;
                padding: 20px;
                border-radius: 8px;
                margin: 15px 0;
                box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            }}
            .diagnosis-primary {{ border-left: 4px solid #2E7D32; }}
            .diagnosis-alternative {{ border-left: 4px solid #FFA726; }}
            .diagnosis-minority {{ border-left: 4px solid #9E9E9E; }}
            
            .diagnosis-name {{ 
                font-weight: 600; 
                font-size: 1.2em; 
                color: #1a472a;
                margin-bottom: 10px;
            }}
            .confidence-badge {{ 
                display: inline-block; 
                padding: 4px 12px; 
                border-radius: 20px; 
                background: #2E7D32; 
                color: white;
                font-weight: 500;
                margin-left: 10px;
            }}
            .supporting-models {{
                margin-top: 10px;
                color: #666;
                font-size: 0.9em;
            }}
            
            .stats-grid {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 20px;
                margin: 20px 0;
            }}
            .stat-card {{
                background: white;
                padding: 20px;
                border-radius: 8px;
                text-align: center;
                box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            }}
            .stat-value {{
                font-size: 2em;
                font-weight: bold;
                color: #2E7D32;
            }}
            .stat-label {{
                color: #666;
                margin-top: 5px;
                font-size: 0.9em;
            }}
            
            .model-response {{
                background: white;
                padding: 15px;
                margin: 10px 0;
                border-radius: 6px;
                border: 1px solid #e0e0e0;
            }}
            .model-name {{
                font-weight: 600;
                color: #333;
                margin-bottom: 5px;
            }}
            .model-diagnosis {{
                color: #666;
                font-size: 0.95em;
            }}
            
            .footer {{
                margin-top: 40px;
                padding-top: 20px;
                border-top: 1px solid #e0e0e0;
                text-align: center;
                color: #666;
                font-size: 0.9em;
            }}
            
            @media print {{
                body {{ padding: 20px; background: white; }}
                .container {{ box-shadow: none; padding: 20px; }}
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>MEDLEY Analysis Report</h1>
                <p>Medical AI Ensemble Diagnostic Analysis</p>
                <p>Analysis ID: {analysis_id}</p>
                <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            </div>
            
            {free_models_disclaimer}
            
            <div class="section">
                <h2>📊 Analysis Overview</h2>
                <div class="stats-grid">
                    <div class="stat-card">
                        <div class="stat-value">{total_models}</div>
                        <div class="stat-label">Total Models</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value">{successful_models}</div>
                        <div class="stat-label">Successful</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value">{failed_models}</div>
                        <div class="stat-label">Failed</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value">{success_rate:.1f}%</div>
                        <div class="stat-label">Success Rate</div>
                    </div>
                </div>
            </div>
            
            <div class="section">
                <h2>🎯 Primary Diagnosis</h2>
                <div class="diagnosis-card diagnosis-primary">
                    <div class="diagnosis-name">
                        {primary.get('name', 'Pending Analysis')}
                        <span class="confidence-badge">{primary.get('agreement_percentage', 0):.1f}% Agreement</span>
                    </div>
                    <div class="supporting-models">
                        <strong>Supporting Models:</strong> {', '.join(primary.get('supporting_models', [])) or 'Processing...'}
                    </div>
                    <div style="margin-top: 10px;">
                        <strong>Key Evidence:</strong>
                        <ul>
                            {''.join(f"<li>{e}</li>" for e in primary.get('key_evidence', [])[:3]) or '<li>Analyzing evidence...</li>'}
                        </ul>
                    </div>
                </div>
            </div>
            
            <div class="section">
                <h2>🔄 Alternative Diagnoses</h2>
                {"".join(f'''
                <div class="diagnosis-card diagnosis-alternative">
                    <div class="diagnosis-name">
                        {alt.get('name', 'Unknown')}
                        <span class="confidence-badge" style="background: #FFA726;">{alt.get('agreement_percentage', 0):.1f}% Agreement</span>
                    </div>
                    <div class="supporting-models">
                        <strong>Supporting Models:</strong> {', '.join(alt.get('supporting_models', [])) or 'N/A'}
                    </div>
                </div>
                ''' for alt in alternatives[:3]) or '<p>No strong alternative diagnoses identified.</p>'}
            </div>
            
            <div class="section">
                <h2>💡 All Differential Diagnoses</h2>
                <div style="display: flex; flex-wrap: wrap; gap: 10px;">
                    {"".join(f'''
                    <span style="padding: 6px 16px; background: #e0e0e0; border-radius: 20px; font-size: 0.9em;">
                        {alt.get('name', 'Unknown')} ({alt.get('model_count', 0)} models)
                    </span>
                    ''' for alt in all_alternatives) or '<p>Processing differential diagnoses...</p>'}
                </div>
            </div>
            
            <div class="section">
                <h2>🤖 Individual Model Responses</h2>
                <div style="max-height: 400px; overflow-y: auto;">
                    {"".join(f'''
                    <div class="model-response">
                        <div class="model-name">{resp.get('model', 'Unknown Model')}</div>
                        <div class="model-diagnosis">
                            <strong>Diagnosis:</strong> {resp.get('primary_diagnosis', 'N/A')} | 
                            <strong>Status:</strong> {'✅ Success' if resp.get('success', False) else '❌ Failed'}
                        </div>
                    </div>
                    ''' for resp in model_responses[:10]) or '<p>Loading model responses...</p>'}
                </div>
            </div>
            
            <div class="footer">
                <p><strong>MEDLEY - Medical AI Ensemble</strong></p>
                <p>Stockholm Medical Artificial Intelligence and Learning Environments (SMAILE)</p>
                <p>Karolinska Institutet</p>
                <p style="margin-top: 10px; font-size: 0.8em;">
                    This report is generated by an AI ensemble system for research purposes only.
                    Always consult qualified healthcare professionals for medical decisions.
                </p>
            </div>
        </div>
    </body>
    </html>
    """
    
    return html_content

def extract_primary_diagnoses(results):
    """Extract primary diagnoses from ensemble results"""
    diagnostic_landscape = results.get('diagnostic_landscape', {})
    primary = diagnostic_landscape.get('primary_diagnosis', {})
    
    if primary:
        return [{
            'diagnosis': primary.get('name', 'Unknown'),
            'confidence': primary.get('agreement_percentage', 0)
        }]
    return []

def extract_alternative_diagnoses(results):
    """Extract alternative diagnoses from ensemble results"""
    diagnostic_landscape = results.get('diagnostic_landscape', {})
    alternatives = diagnostic_landscape.get('strong_alternatives', [])
    
    return [
        {
            'diagnosis': alt.get('name', 'Unknown'),
            'confidence': alt.get('agreement_percentage', 0)
        }
        for alt in alternatives[:4]
    ]

def extract_minority_opinions(results):
    """Extract minority opinions from ensemble results"""
    diagnostic_landscape = results.get('diagnostic_landscape', {})
    minority = diagnostic_landscape.get('minority_opinions', [])
    
    return [
        {
            'diagnosis': m.get('name', 'Unknown'),
            'confidence': m.get('model_count', 0) * 10  # Approximate confidence
        }
        for m in minority[:2]
    ]

def enrich_diagnosis_with_models(ensemble_data):
    """Extract which models support each diagnosis from model responses"""
    
    # Check if we already have comprehensive diagnosis data from the pipeline
    if 'consensus_analysis' in ensemble_data and 'model_diagnoses' in ensemble_data['consensus_analysis']:
        # Use the comprehensive extraction from the pipeline
        model_diagnoses_raw = ensemble_data['consensus_analysis']['model_diagnoses']
        
        # Convert to the format expected by the web interface (model names as sets)
        model_diagnoses = {}
        for diagnosis, model_data in model_diagnoses_raw.items():
            all_models = set()
            if 'primary' in model_data:
                # Clean model names (remove /free suffix)
                cleaned_primary = [model.split('/')[-1] for model in model_data['primary']]
                all_models.update(cleaned_primary)
            if 'differential' in model_data:
                # Clean model names (remove /free suffix)
                cleaned_differential = [model.split('/')[-1] for model in model_data['differential']]
                all_models.update(cleaned_differential)
            
            if all_models:
                model_diagnoses[diagnosis] = all_models
        
        print(f"Using comprehensive extraction: {len(model_diagnoses)} diagnoses with model support")
        
        # Debug: Log what we found with cleaned counts
        print(f"Model diagnoses mapping: {len(model_diagnoses)} unique diagnoses found")
        for diag, models in model_diagnoses.items():
            print(f"  {diag}: {len(models)} models")
            
        # Skip the individual model response processing since we have comprehensive data
        # Update diagnostic landscape directly and return
        diagnostic_landscape = ensemble_data.get('diagnostic_landscape', {})
        
        # Update primary diagnosis
        if 'primary_diagnosis' in diagnostic_landscape:
            primary_name = diagnostic_landscape['primary_diagnosis'].get('name', '')
            normalized_primary = normalize_diagnosis_name(primary_name)
            
            # Try both normalized and original name
            if normalized_primary in model_diagnoses:
                diagnostic_landscape['primary_diagnosis']['supporting_models'] = list(model_diagnoses[normalized_primary])
                diagnostic_landscape['primary_diagnosis']['model_count'] = len(model_diagnoses[normalized_primary])
                # Update agreement percentage based on actual model count (successful models only)
                primary_model_count = len(model_diagnoses[normalized_primary])
                successful_models_count = sum(1 for r in ensemble_data.get('model_responses', []) if is_model_response_valid(r))
                if successful_models_count > 0:
                    diagnostic_landscape['primary_diagnosis']['agreement_percentage'] = (primary_model_count / successful_models_count) * 100
            elif primary_name in model_diagnoses:
                diagnostic_landscape['primary_diagnosis']['supporting_models'] = list(model_diagnoses[primary_name])
                diagnostic_landscape['primary_diagnosis']['model_count'] = len(model_diagnoses[primary_name])
                # Update agreement percentage based on actual model count (successful models only)
                primary_model_count = len(model_diagnoses[primary_name])
                successful_models_count = sum(1 for r in ensemble_data.get('model_responses', []) if is_model_response_valid(r))
                if successful_models_count > 0:
                    diagnostic_landscape['primary_diagnosis']['agreement_percentage'] = (primary_model_count / successful_models_count) * 100
        
        # Update alternatives
        for alt in diagnostic_landscape.get('strong_alternatives', []):
            alt_name = alt.get('name', '')
            normalized_alt = normalize_diagnosis_name(alt_name)
            
            if normalized_alt in model_diagnoses:
                alt['supporting_models'] = list(model_diagnoses[normalized_alt])
                alt['model_count'] = len(model_diagnoses[normalized_alt])
            elif alt_name in model_diagnoses:
                alt['supporting_models'] = list(model_diagnoses[alt_name])
                alt['model_count'] = len(model_diagnoses[alt_name])
        
        # Update all alternatives
        for alt in diagnostic_landscape.get('all_alternative_diagnoses', []):
            alt_name = alt.get('name', '')
            normalized_alt = normalize_diagnosis_name(alt_name)
            
            if normalized_alt in model_diagnoses:
                alt['supporting_models'] = list(model_diagnoses[normalized_alt])
                alt['model_count'] = len(model_diagnoses[normalized_alt])
            elif alt_name in model_diagnoses:
                alt['supporting_models'] = list(model_diagnoses[alt_name])
                alt['model_count'] = len(model_diagnoses[alt_name])
        
        # Re-categorize alternatives based on new thresholds BEFORE returning
        all_alternatives = diagnostic_landscape.get('all_alternative_diagnoses', [])
        strong_alternatives = []
        regular_alternatives = []
        minority_opinions = []
        
        # Get successful models count for percentage calculation
        successful_models_count = sum(1 for r in ensemble_data.get('model_responses', []) if is_model_response_valid(r))
        
        for alt in all_alternatives:
            model_count = len(alt.get('supporting_models', []))
            
            # Calculate agreement percentage (based on successful models only)
            if successful_models_count > 0:
                agreement_percentage = (model_count / successful_models_count) * 100
                alt['agreement_percentage'] = agreement_percentage
                
                # Apply updated categorization thresholds (10% instead of 20%)
                if agreement_percentage >= 30.0:  # Strong alternatives
                    strong_alternatives.append(alt)
                elif agreement_percentage >= 10.0:  # Regular alternatives (was 20%)
                    regular_alternatives.append(alt)
                else:  # Minority opinions (< 10%, was < 20%)
                    minority_opinions.append(alt)
            else:
                alt['agreement_percentage'] = 0
                minority_opinions.append(alt)
        
        # Update the categorized lists
        diagnostic_landscape['strong_alternatives'] = strong_alternatives
        diagnostic_landscape['alternatives'] = regular_alternatives
        diagnostic_landscape['minority_opinions'] = minority_opinions
        
        print(f"✅ Re-categorized: {len(strong_alternatives)} strong, {len(regular_alternatives)} regular, {len(minority_opinions)} minority")
        
        ensemble_data['diagnostic_landscape'] = diagnostic_landscape
        return ensemble_data
    
    # Fallback to the old extraction method only if comprehensive data is not available
    model_diagnoses = {}
    
    # Process each model response to extract diagnoses
    for response in ensemble_data.get('model_responses', []):
        if not response.get('response') or response.get('error'):
            continue
            
        model_name = response.get('model_name', 'Unknown').split('/')[-1]  # Clean model name
        
        # Try to parse JSON response
        response_text = response.get('response', '')
        diagnoses_found = set()
        
        try:
            # Try to parse as JSON first
            import json
            if isinstance(response_text, str):
                # Clean up the response text - remove markdown code blocks if present
                if '```json' in response_text:
                    response_text = response_text.split('```json')[1].split('```')[0]
                elif '```' in response_text:
                    response_text = response_text.split('```')[1].split('```')[0]
                
                # Parse the JSON
                parsed_response = json.loads(response_text)
                
                # Extract primary diagnosis
                if 'primary_diagnosis' in parsed_response:
                    primary = parsed_response['primary_diagnosis']
                    if isinstance(primary, dict) and 'name' in primary:
                        diag_name = primary['name']
                    elif isinstance(primary, str):
                        diag_name = primary
                    else:
                        diag_name = None
                    
                    if diag_name:
                        # Handle variations like "Crohn disease (Inflammatory bowel disease)"
                        # but don't add both as separate diagnoses
                        if '(' in diag_name:
                            main_part = diag_name.split('(')[0].strip()
                            diagnoses_found.add(main_part)
                        else:
                            diagnoses_found.add(diag_name)
                
                # Extract differential diagnoses
                if 'differential_diagnoses' in parsed_response:
                    for diff in parsed_response['differential_diagnoses']:
                        diag_name = None
                        if isinstance(diff, dict) and 'name' in diff:
                            diag_name = diff['name']
                        elif isinstance(diff, str):
                            diag_name = diff
                        
                        if diag_name:
                            # Handle variations
                            if '(' in diag_name:
                                main_part = diag_name.split('(')[0].strip()
                                diagnoses_found.add(main_part)
                            else:
                                diagnoses_found.add(diag_name)
        except:
            # Fallback to text parsing if JSON parsing fails
            response_lower = str(response_text).lower()
            
            # Extended diagnosis mapping - be more specific to avoid false positives
            diagnosis_patterns = {
                'Familial Mediterranean Fever': ['familial mediterranean fever', 'fmf', '"e85.0"', '"m04.1"'],
                'Systemic Lupus Erythematosus': ['systemic lupus', 'sle', 'lupus erythematosus', '"m32.9"'],
                'Adult-Onset Still\'s Disease': ['still\'s disease', 'aosd', 'adult-onset still'],
                'Behçet\'s Disease': ['behcet', 'behçet\'s', '"m35.2"'],
                'Periodic Fever Syndrome': ['periodic fever syndrome', 'pfapa', 'traps'],
                'Reactive Arthritis': ['reactive arthritis', '"m45.9"', '"m45.0"', '"m40.0"'],
                'Inflammatory Bowel Disease': ['inflammatory bowel disease', '"ibd"', '"k50"'],
                'Crohn\'s Disease': ['crohn\'s disease', 'crohn disease', '"k50.9"'],
                'Acute Intermittent Porphyria': ['porphyria', 'acute intermittent porphyria', '"e80.21"'],
                'Tuberculosis': ['tuberculosis', '"tb"', '"a15.9"', '"a18.3"'],
                'Septic Arthritis': ['septic arthritis', '"m00"', '"m10.9"'],
                'Gouty Arthritis': ['gout', 'gouty arthritis', '"m10"'],
                'Acute Appendicitis': ['appendicitis', '"k35.80"', '"k35"'],
                'Ulcerative Colitis': ['ulcerative colitis', '"k50.8"'],
                'Peritonitis': ['peritonitis', '"r11"'],
                'Hyper IgD Syndrome': ['hyper igd', 'mevalonate kinase', '"d80.1"'],
                'Autoinflammatory Disease': ['autoinflammatory disease', '"m04.9"', '"m04.2"'],
                'Infectious Arthritis': ['infectious arthritis', '"m00.9"'],
                'Psoriatic Arthritis': ['psoriatic arthritis', '"m05.x"', '"m86.0"'],
                'Ankylosing Spondylitis': ['ankylosing spondylitis', '"m45.0"'],
                'Heart Failure': ['heart failure', 'chf', 'congestive heart failure'],
                'Marfan Syndrome': ['marfan syndrome'],
                'Lead Poisoning': ['lead poisoning', 'lead toxicity'],
                'Thrombotic Thrombocytopenic Purpura': ['ttp', 'thrombotic thrombocytopenic purpura'],
                'Melioidosis': ['melioidosis'],
                'Thyroid Storm': ['thyroid storm', 'thyrotoxicosis'],
                'Long COVID': ['long covid', 'post-covid'],
                'Kawasaki Disease': ['kawasaki disease'],
                'Irritable Bowel Syndrome': ['irritable bowel syndrome', '"ibs"', '"k58.9"']
            }
            
            for diagnosis, patterns in diagnosis_patterns.items():
                for pattern in patterns:
                    if pattern in response_lower:
                        diagnoses_found.add(diagnosis)
                        break
        
        # Normalize and add found diagnoses to the model_diagnoses mapping
        for diagnosis in diagnoses_found:
            # Normalize the diagnosis name for consistent mapping
            normalized_diagnosis = normalize_diagnosis_name(diagnosis)
            
            if normalized_diagnosis not in model_diagnoses:
                model_diagnoses[normalized_diagnosis] = set()  # Use set to avoid duplicates
            model_diagnoses[normalized_diagnosis].add(model_name)
    
    # Debug: Log what we found
    print(f"Model diagnoses mapping: {len(model_diagnoses)} unique diagnoses found")
    for diag, models in model_diagnoses.items():
        print(f"  {diag}: {len(models)} models")
    
    # Update diagnostic landscape with supporting models
    diagnostic_landscape = ensemble_data.get('diagnostic_landscape', {})
    
    # Update primary diagnosis
    if 'primary_diagnosis' in diagnostic_landscape:
        primary_name = diagnostic_landscape['primary_diagnosis'].get('name', '')
        normalized_primary = normalize_diagnosis_name(primary_name)
        
        # Try both normalized and original name
        if normalized_primary in model_diagnoses:
            diagnostic_landscape['primary_diagnosis']['supporting_models'] = list(model_diagnoses[normalized_primary])
            diagnostic_landscape['primary_diagnosis']['model_count'] = len(model_diagnoses[normalized_primary])
        elif primary_name in model_diagnoses:
            diagnostic_landscape['primary_diagnosis']['supporting_models'] = list(model_diagnoses[primary_name])
            diagnostic_landscape['primary_diagnosis']['model_count'] = len(model_diagnoses[primary_name])
    
    # Update alternatives
    for alt in diagnostic_landscape.get('strong_alternatives', []):
        alt_name = alt.get('name', '')
        normalized_alt = normalize_diagnosis_name(alt_name)
        
        if normalized_alt in model_diagnoses:
            alt['supporting_models'] = list(model_diagnoses[normalized_alt])
            alt['model_count'] = len(model_diagnoses[normalized_alt])
        elif alt_name in model_diagnoses:
            alt['supporting_models'] = list(model_diagnoses[alt_name])
            alt['model_count'] = len(model_diagnoses[alt_name])
    
    # Update all alternatives  
    for alt in diagnostic_landscape.get('all_alternative_diagnoses', []):
        alt_name = alt.get('name', '')
        normalized_alt = normalize_diagnosis_name(alt_name)
        
        if normalized_alt in model_diagnoses:
            alt['supporting_models'] = list(model_diagnoses[normalized_alt])
            alt['model_count'] = len(model_diagnoses[normalized_alt])
        elif alt_name in model_diagnoses:
            alt['supporting_models'] = list(model_diagnoses[alt_name])
            alt['model_count'] = len(model_diagnoses[alt_name])
    
    ensemble_data['diagnostic_landscape'] = diagnostic_landscape
    return ensemble_data

@app.route('/api/case/<case_key>/pdf')
def download_case_pdf(case_key):
    """Download PDF report for a case"""
    
    # Check if it's a custom case
    if case_key.startswith('custom_') or case_key.startswith('Case_'):
        case_info = {
            'id': case_key,
            'title': 'Custom Analysis'
        }
        case_id = case_key
    elif case_key in PREDEFINED_CASES:
        case_info = PREDEFINED_CASES[case_key]
        case_id = case_info['id']
    else:
        return jsonify({"error": "Case not found"}), 404
    
    # Find the latest PDF report
    # For custom cases, handle the naming mismatch between Case_timestamp format and tmp_id format
    if case_key.startswith('Case_20'):
        # Extract timestamp from Case_20250905_083643 format
        timestamp_part = case_key.replace('Case_', '')
        # Look for both formats: FINAL_Case_timestamp and FINAL_tmp*_comprehensive_timestamp
        pdf_patterns = [
            f"FINAL_{case_id}_*.pdf",
            f"FINAL_tmp*_comprehensive_{timestamp_part}.pdf",
            f"FINAL_*_{timestamp_part}.pdf"
        ]
        pdf_files = []
        for pattern in pdf_patterns:
            pdf_files.extend(list(REPORTS_DIR.glob(pattern)))
    else:
        pdf_pattern = f"FINAL_{case_id}_*.pdf"
        pdf_files = list(REPORTS_DIR.glob(pdf_pattern))
    
    if not pdf_files:
        return jsonify({"error": "No PDF report available"}), 404
    
    latest_pdf = max(pdf_files, key=lambda p: p.stat().st_mtime)
    
    # Create response with cache-busting headers
    response = send_file(
        latest_pdf,
        as_attachment=True,
        download_name=f"MEDLEY_{case_info['title'].replace(' ', '_')}_Report.pdf",
        mimetype='application/pdf'
    )
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

@app.route('/api/case/<case_key>/models')
def get_model_responses(case_key):
    """Get individual model responses for a case"""
    
    # Check predefined cases first (to avoid conflicts with case_ prefix)
    if case_key in PREDEFINED_CASES:
        case_info = PREDEFINED_CASES[case_key]
        case_id = case_info['id']
    elif case_key.startswith('custom_') or case_key.startswith('Case_') or case_key.startswith('case_'):
        case_id = case_key
    else:
        return jsonify({"error": "Case not found"}), 404
    
    # Find the latest ensemble data
    json_files = []
    
    # First, try to find in reports directory (legacy location)
    json_pattern = f"{case_id}_ensemble_data.json"
    json_files = list(REPORTS_DIR.glob(json_pattern))
    
    # If not found, try with wildcard in reports directory
    if not json_files:
        json_pattern = f"{case_id}_ensemble_data_*.json"
        json_files = list(REPORTS_DIR.glob(json_pattern))
    
    # Fallback: If glob with wildcard fails, manually search for the file
    if not json_files:
        # List all files and filter manually (workaround for glob issues)
        all_files = list(REPORTS_DIR.glob("*.json"))
        json_files = [f for f in all_files if f.name.startswith(f"{case_id}_ensemble_data")]
    
    # If still not found, try orchestrator cache directory
    if not json_files:
        orchestrator_cache_dir = BASE_DIR / "cache" / "orchestrator" / case_id
        if orchestrator_cache_dir.exists():
            json_files = list(orchestrator_cache_dir.glob("orchestrator_analysis_*.json"))
    
    if not json_files:
        return jsonify({"error": "No data available"}), 404
    
    latest_json = max(json_files, key=lambda p: p.stat().st_mtime)
    
    with open(latest_json, 'r') as f:
        ensemble_data = json.load(f)
    
    # Extract model responses
    model_responses = ensemble_data.get('model_responses', [])
    
    # Format for display - include all models, even those with errors or empty responses
    formatted_responses = []
    for response in model_responses:
        # Include all responses, not just successful ones
        # Note: model_id field doesn't exist in the data, use model_name for both
        model_name = response.get('model_name', 'Unknown')
        formatted_responses.append({
            "model_name": model_name,
            "model_id": model_name,  # Use model_name as ID since model_id doesn't exist
            "response": response.get('response', ''),  # May be empty string
            "tokens_used": response.get('tokens_used', 0),
            "input_tokens": response.get('input_tokens', 0),
            "output_tokens": response.get('output_tokens', 0),
            "response_time": response.get('response_time', 0),
            "error": response.get('error', None)
        })
    
    # Create response with cache-busting headers
    response = jsonify(formatted_responses)
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

@app.route('/api/performance')
@cache.cached(timeout=300)  # Cache for 5 minutes  
def get_model_performance():
    """Get model performance statistics"""
    # Calculate performance from all available reports
    performance_data = calculate_model_performance()
    return jsonify(performance_data)

@app.route('/api/analyses/recent')
def get_recent_analyses():
    """Get recent analyses for dashboard"""
    # Get limit from query params
    limit = request.args.get('limit', 10, type=int)
    
    # For now, return mock data for demonstration
    # In production, this would query the database
    recent_analyses = [
        {
            'id': 'Case_20250811_1',
            'created_at': (datetime.now() - timedelta(hours=2)).isoformat(),
            'model_count': 6,
            'duration': '45s',
            'status': 'completed'
        },
        {
            'id': 'demo_20250811_2', 
            'created_at': (datetime.now() - timedelta(hours=5)).isoformat(),
            'model_count': 8,
            'duration': '62s',
            'status': 'completed'
        },
        {
            'id': 'Case_20250810_3',
            'created_at': (datetime.now() - timedelta(days=1)).isoformat(),
            'model_count': 17,
            'duration': '3m 15s',
            'status': 'completed'
        }
    ]
    
    return jsonify(recent_analyses[:limit])

@app.route('/api/metrics/export')
def export_metrics():
    """Export metrics data"""
    export_format = request.args.get('format', 'json')
    
    if export_format == 'csv':
        return export_csv('performance')
    else:
        return export_json('performance')

@app.route('/api/cache/clear', methods=['POST'])
def clear_cache():
    """Clear all cached responses"""
    try:
        # Clear the cache directory
        cache_dir = Path(__file__).parent / 'cache'
        
        if cache_dir.exists():
            import shutil
            # Remove all subdirectories in cache
            for item in cache_dir.iterdir():
                if item.is_dir():
                    shutil.rmtree(item)
                elif item.is_file() and item.name != '.gitkeep':
                    item.unlink()
            
            # Recreate the responses directory
            responses_dir = cache_dir / 'responses'
            responses_dir.mkdir(parents=True, exist_ok=True)
            
            # Clear Flask cache if using it
            if hasattr(cache, 'clear'):
                cache.clear()
            
            return jsonify({
                'success': True,
                'message': 'Cache cleared successfully'
            })
        else:
            return jsonify({
                'success': True,
                'message': 'No cache to clear'
            })
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/cache/stats', methods=['GET'])
def get_cache_stats():
    """Get cache statistics"""
    try:
        cache_dir = Path(__file__).parent / 'cache'
        
        if not cache_dir.exists():
            return jsonify({
                'total_size': 0,
                'file_count': 0,
                'formatted_size': '0 B'
            })
        
        total_size = 0
        file_count = 0
        
        # Calculate cache size
        for item in cache_dir.rglob('*'):
            if item.is_file():
                total_size += item.stat().st_size
                file_count += 1
        
        # Format size
        def format_bytes(size):
            for unit in ['B', 'KB', 'MB', 'GB']:
                if size < 1024.0:
                    return f"{size:.1f} {unit}"
                size /= 1024.0
            return f"{size:.1f} TB"
        
        return jsonify({
            'total_size': total_size,
            'file_count': file_count,
            'formatted_size': format_bytes(total_size)
        })
        
    except Exception as e:
        return jsonify({
            'error': str(e)
        }), 500

@app.route('/api/rate', methods=['POST'])
def rate_diagnosis():
    """Rate a diagnosis (stored in session)"""
    data = request.json
    model_name = data.get('model_name')
    case_id = data.get('case_id')
    rating = data.get('rating')
    diagnosis_type = data.get('type', 'primary')  # primary or alternative
    
    if not all([model_name, case_id, rating]):
        return jsonify({"error": "Missing required fields"}), 400
    
    # Store in session (demo purposes)
    if 'ratings' not in session:
        session['ratings'] = {}
    
    rating_key = f"{case_id}_{model_name}_{diagnosis_type}"
    session['ratings'][rating_key] = {
        'rating': rating,
        'timestamp': datetime.now().isoformat()
    }
    
    return jsonify({"success": True, "message": "Rating saved"})

@app.route('/api/session/info')
def get_session_info():
    """Get current session information"""
    return jsonify({
        "session_id": session.get('_id', 'none'),
        "api_key_set": bool(session.get('openrouter_api_key')),
        "analyses_count": len(session.get('analyses', [])),
        "ratings_count": len(session.get('ratings', {}))
    })

@app.route('/api/session/clear', methods=['POST'])
def clear_session():
    """Clear session data"""
    session.clear()
    return jsonify({"success": True, "message": "Session cleared"})

@app.route('/api/session/set-key', methods=['POST'])
def set_api_key():
    """Set API key in session"""
    data = request.json
    api_key = data.get('api_key')
    if api_key:
        session['api_key'] = api_key  # Use consistent key name
        session['openrouter_api_key'] = api_key  # Also store with old name for compatibility
        return jsonify({"success": True, "message": "API key saved successfully"})
    return jsonify({"error": "No API key provided"}), 400

@app.route('/api/test-connection', methods=['POST'])
def test_connection():
    """Test OpenRouter API connection"""
    import requests
    
    data = request.json
    api_key = data.get('api_key') or session.get('api_key') or session.get('openrouter_api_key') or os.getenv('OPENROUTER_API_KEY')
    
    if not api_key:
        return jsonify({"success": False, "error": "No API key provided"}), 400
    
    # Test the API key with a simple request to OpenRouter
    try:
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        # Test with a minimal request to check if the key is valid
        test_data = {
            "model": "openai/gpt-3.5-turbo",
            "messages": [{"role": "user", "content": "test"}],
            "max_tokens": 1
        }
        
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=test_data,
            timeout=30
        )
        
        if response.status_code == 200:
            return jsonify({"success": True, "message": "Connection successful"})
        elif response.status_code == 401:
            return jsonify({"success": False, "error": "Invalid API key"}), 401
        else:
            return jsonify({"success": False, "error": f"Connection failed: {response.status_code}"}), 400
            
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/health')
@app.route('/api/health')
def health_check():
    """Health check endpoint for monitoring"""
    import sys
    from pathlib import Path
    
    health_status = {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "2.0.0",
        "checks": {
            "cache_directory": CACHE_DIR.exists(),
            "reports_directory": REPORTS_DIR.exists(),
            "usecases_directory": USECASES_DIR.exists(),
            "predefined_cases": len(PREDEFINED_CASES),
            "cached_reports": len(list(REPORTS_DIR.glob("*_ensemble_data_*.json"))),
            "python_version": sys.version.split()[0],
            "flask_running": True,
            "socketio_enabled": True,
            "session_enabled": 'openrouter_api_key' in session or True
        },
        "statistics": {
            "total_cases_available": len(PREDEFINED_CASES),
            "models_supported": 31,
            "countries_represented": 6,
            "medical_specialties": len(set(case.get('specialty', '') for case in PREDEFINED_CASES.values()))
        }
    }
    
    # Check if all critical directories exist
    if not all([CACHE_DIR.exists(), REPORTS_DIR.exists(), USECASES_DIR.exists()]):
        health_status["status"] = "degraded"
        
    return jsonify(health_status)

@app.route('/api/available_models')
def get_available_models():
    """Get list of available AI models from model_metadata_2025.py"""
    metadata = get_comprehensive_model_metadata()
    free_models = []
    paid_models = []
    
    for model_id, info in metadata.items():
        # Determine if model is free based on cost_tier
        is_free = info.get('cost_tier') == 'Free'
        
        # Extract display name from model_id
        provider, model_name = model_id.split('/', 1) if '/' in model_id else ('Unknown', model_id)
        
        # Create display name
        display_name = model_name.replace('-', ' ').replace('_', ' ').title()
        # Clean up common suffixes
        display_name = display_name.replace(' 20240229', '').replace(' 20240307', '')
        
        model_info = {
            "id": model_id + (':free' if is_free else ''),  # Add :free suffix for compatibility
            "name": display_name,
            "provider": info.get('provider', provider.title()),
            "origin": info.get('origin_country', 'Unknown')
        }
        
        if is_free:
            free_models.append(model_info)
        else:
            paid_models.append(model_info)
    
    # Sort by provider and then by name
    free_models.sort(key=lambda x: (x['provider'], x['name']))
    paid_models.sort(key=lambda x: (x['provider'], x['name']))
    
    return jsonify({
        'free': free_models,
        'paid': paid_models
    })

@app.route('/analyze')
def analyze():
    """Custom case analysis page"""
    from flask import make_response
    
    # Check for API key in session or environment
    if not session.get('api_key') and os.getenv('OPENROUTER_API_KEY'):
        session['api_key'] = os.getenv('OPENROUTER_API_KEY')
        session['openrouter_api_key'] = os.getenv('OPENROUTER_API_KEY')
    
    # Get API key for template
    api_key = session.get('api_key', '') or session.get('openrouter_api_key', '')
    
    # Use the v3 template with better styling and progress section
    # Add cache buster to force template refresh
    import time
    cache_buster = str(int(time.time()))
    print(f"🚀 DEBUG: Serving analyze_v4.html template with api_key='{api_key[:10] if api_key else 'None'}...'")
    
    # Create response with no-cache headers to ensure fresh JavaScript
    response = make_response(render_template('analyze_v4.html', api_key=api_key, cache_buster=cache_buster))
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    
    return response

@app.route('/settings')
def settings():
    """Settings and API management page"""
    # Check for API key in session or environment
    if not session.get('api_key') and os.getenv('OPENROUTER_API_KEY'):
        session['api_key'] = os.getenv('OPENROUTER_API_KEY')
        session['openrouter_api_key'] = os.getenv('OPENROUTER_API_KEY')
    
    api_stats = {
        'total_requests': 0,
        'tokens_used': 0,
        'total_cost': '0.00'
    }
    return render_template('settings_material3.html', api_stats=api_stats)

@app.route('/dashboard')
@cache.cached(timeout=300)  # Cache for 5 minutes
def dashboard():
    """Model performance dashboard"""
    return render_template('dashboard_material3.html')

@app.route('/compare')
@cache.cached(timeout=300)  # Cache for 5 minutes
def compare():
    """Side-by-side model comparison tool"""
    return render_template('compare_material3.html')

@app.route('/visualizations')
@cache.cached(timeout=300)  # Cache for 5 minutes
def visualizations():
    """Analytics and visualizations dashboard"""
    return render_template('visualizations_material3.html')

@app.route('/api/docs')
@app.route('/docs')
@cache.cached(timeout=600)  # Cache docs for 10 minutes
def api_docs():
    """API documentation page"""
    return render_template('api_docs_material3.html')

@app.route('/api/export/csv/<export_type>')
def export_csv(export_type):
    """Export data as CSV"""
    
    if export_type == 'performance':
        # Export model performance data
        performance_data = calculate_model_performance()
        
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=[
            'model_name', 'consensus_participation_rate', 
            'total_cases_analyzed', 'unique_diagnoses_count', 'average_rating'
        ])
        
        writer.writeheader()
        writer.writerows(performance_data)
        
        response = Response(output.getvalue(), mimetype='text/csv')
        response.headers['Content-Disposition'] = 'attachment; filename=model_performance.csv'
        return response
    
    elif export_type == 'cases':
        # Export cases summary
        cases = []
        for case_key, case_info in PREDEFINED_CASES.items():
            cases.append({
                'case_id': case_info['id'],
                'title': case_info['title'],
                'specialty': case_info['specialty'],
                'complexity': case_info['complexity'],
                'description': case_info['description']
            })
        
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=[
            'case_id', 'title', 'specialty', 'complexity', 'description'
        ])
        
        writer.writeheader()
        writer.writerows(cases)
        
        response = Response(output.getvalue(), mimetype='text/csv')
        response.headers['Content-Disposition'] = 'attachment; filename=medical_cases.csv'
        return response
    
    elif export_type == 'diagnoses':
        # Export all diagnoses across cases
        all_diagnoses = []
        
        for case_key in PREDEFINED_CASES:
            case_info = PREDEFINED_CASES[case_key]
            case_id = case_info['id']
            
            # Find ensemble data
            json_pattern = f"{case_id}_ensemble_data_*.json"
            json_files = list(REPORTS_DIR.glob(json_pattern))
            
            if json_files:
                latest_json = max(json_files, key=lambda p: p.stat().st_mtime)
                with open(latest_json, 'r') as f:
                    ensemble_data = json.load(f)
                
                landscape = ensemble_data.get('diagnostic_landscape', {})
                
                # Add primary diagnosis
                if 'primary_diagnosis' in landscape:
                    primary = landscape['primary_diagnosis']
                    all_diagnoses.append({
                        'case_id': case_id,
                        'case_title': case_info['title'],
                        'diagnosis_type': 'Primary',
                        'diagnosis_name': primary.get('name', ''),
                        'agreement_percentage': primary.get('agreement_percentage', 0),
                        'model_count': primary.get('model_count', 0)
                    })
                
                # Add alternatives
                for alt in landscape.get('strong_alternatives', []):
                    all_diagnoses.append({
                        'case_id': case_id,
                        'case_title': case_info['title'],
                        'diagnosis_type': 'Strong Alternative',
                        'diagnosis_name': alt.get('name', ''),
                        'agreement_percentage': alt.get('agreement_percentage', 0),
                        'model_count': alt.get('model_count', 0)
                    })
        
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=[
            'case_id', 'case_title', 'diagnosis_type', 
            'diagnosis_name', 'agreement_percentage', 'model_count'
        ])
        
        writer.writeheader()
        writer.writerows(all_diagnoses)
        
        response = Response(output.getvalue(), mimetype='text/csv')
        response.headers['Content-Disposition'] = 'attachment; filename=all_diagnoses.csv'
        return response
    
    else:
        return jsonify({"error": "Invalid export type"}), 400

@app.route('/api/export/json/<export_type>')
def export_json(export_type):
    """Export data as JSON"""
    
    if export_type == 'performance':
        data = calculate_model_performance()
    elif export_type == 'cases':
        data = list(PREDEFINED_CASES.values())
    elif export_type == 'all':
        # Export comprehensive data
        data = {
            'cases': list(PREDEFINED_CASES.values()),
            'performance': calculate_model_performance(),
            'exported_at': datetime.now().isoformat(),
            'version': '2.0.0'
        }
    else:
        return jsonify({"error": "Invalid export type"}), 400
    
    response = Response(
        json.dumps(data, indent=2),
        mimetype='application/json',
        headers={
            'Content-Disposition': f'attachment; filename=medley_{export_type}.json'
        }
    )
    return response

def calculate_model_performance():
    """Calculate model performance metrics from available data"""
    metrics = {}
    
    # Process all ensemble data files
    json_files = list(REPORTS_DIR.glob("*_ensemble_data_*.json"))
    
    for json_file in json_files:
        try:
            with open(json_file, 'r') as f:
                ensemble_data = json.load(f)
            
            # Process model responses
            for response in ensemble_data.get('model_responses', []):
                model_name = response.get('model_name', 'Unknown').split('/')[-1]  # Clean model name
                
                if model_name not in metrics:
                    metrics[model_name] = {
                        'name': model_name,
                        'provider': response.get('model_name', '').split('/')[0] if '/' in response.get('model_name', '') else 'Unknown',
                        'calls': 0,
                        'successful_calls': 0,
                        'total_response_time': 0,
                        'total_cost': 0.0,
                        'unique_diagnoses': set()
                    }
                
                # Update metrics
                metrics[model_name]['calls'] += 1
                
                if response.get('success', True) and not response.get('error'):
                    metrics[model_name]['successful_calls'] += 1
                
                if 'response_time' in response:
                    metrics[model_name]['total_response_time'] += response['response_time']
                
                # Estimate cost (placeholder values)
                tokens_used = response.get('tokens_used', response.get('input_tokens', 0) + response.get('output_tokens', 0))
                estimated_cost = (tokens_used / 1000) * 0.002  # $0.002 per 1k tokens estimate
                metrics[model_name]['total_cost'] += estimated_cost
                
        except Exception as e:
            print(f"Error processing {json_file}: {e}")
            continue
    
    # Format for dashboard
    formatted_metrics = []
    for model_name, data in metrics.items():
        avg_time = (data['total_response_time'] / data['calls']) if data['calls'] > 0 else 0
        success_rate = (data['successful_calls'] / data['calls'] * 100) if data['calls'] > 0 else 0
        
        formatted_metrics.append({
            'name': data['name'],
            'provider': data['provider'].title(),
            'calls': data['calls'],
            'avg_time': f"{avg_time:.1f}s" if avg_time > 0 else 'N/A',
            'success_rate': f"{success_rate:.1f}%",
            'cost': f"{data['total_cost']:.4f}"
        })
    
    # Sort by number of calls
    formatted_metrics.sort(key=lambda x: x['calls'], reverse=True)
    
    return {'models': formatted_metrics}

# ============== REST API ENDPOINTS ==============

@app.route('/api/analyze', methods=['POST'])
@RateLimiter.analysis_rate_limit()  # Apply rate limiting
def api_analyze_case():
    """Start analysis of a custom case via REST API"""
    if not orchestrator:
        return jsonify({'error': 'Orchestrator not available'}), 503
    
    data = request.json
    case_text = data.get('case_text')
    
    if not case_text:
        return jsonify({'error': 'Missing case_text'}), 400
    
    # Validate and sanitize input
    is_valid, error_msg = InputValidator.validate_case_text(case_text)
    if not is_valid:
        return jsonify({'error': error_msg}), 400
    
    case_text = InputValidator.sanitize_text(case_text)
    case_title = InputValidator.sanitize_text(data.get('case_title', 'Custom Case'), max_length=200)
    
    use_free_models = data.get('use_free_models', False)
    selected_models = data.get('selected_models')
    enable_pdf = data.get('enable_pdf', True)  # Extract PDF generation setting from frontend
    
    # Validate model selection
    if selected_models:
        is_valid, error_msg = InputValidator.validate_model_selection(selected_models)
        if not is_valid:
            return jsonify({'error': error_msg}), 400
    
    api_key = data.get('api_key') or session.get('openrouter_api_key') or os.getenv('OPENROUTER_API_KEY')
    
    # Validate API key format if provided
    if api_key and not InputValidator.validate_api_key(api_key):
        return jsonify({'error': 'Invalid API key format'}), 400
    
    # Create progress session for long polling
    progress_session_id = progress_manager.create_session()
    
    # Start analysis with progress session
    result = orchestrator.analyze_custom_case(
        case_text=case_text,
        case_title=case_title,
        use_free_models=use_free_models,
        selected_models=selected_models,
        session_id=session.get('session_id'),
        api_key=api_key,
        progress_session_id=progress_session_id,  # Add progress session
        enable_pdf=enable_pdf  # Pass PDF generation setting to orchestrator
    )
    
    # Add progress session ID to result
    if isinstance(result, dict):
        result['progress_session_id'] = progress_session_id
    
    return jsonify(result)

@app.route('/api/analyze/<analysis_id>/status', methods=['GET'])
def api_get_analysis_status(analysis_id):
    """Get current status of an analysis"""
    # First check session storage for current user's analyses
    if 'analyses' in session and analysis_id in session['analyses']:
        analysis_data = session['analyses'][analysis_id]
        
        # Calculate elapsed time
        start_time = analysis_data.get('started_at', time.time())
        elapsed_seconds = int(time.time() - start_time)
        
        status = {
            'analysis_id': analysis_id,
            'status': analysis_data.get('status', 'unknown'),
            'elapsed_time': elapsed_seconds,
            'title': analysis_data.get('title', 'Custom Analysis')
        }
        
        if analysis_data.get('status') == 'completed':
            status.update({
                'report_file': analysis_data.get('report_file'),
                'data_file': analysis_data.get('data_file'),
                'report_available': bool(analysis_data.get('report_file'))
            })
        elif analysis_data.get('status') == 'failed':
            status['error'] = analysis_data.get('error', 'Unknown error')
            
        return jsonify(status)
    
    # Fallback to orchestrator if available
    if orchestrator:
        status = orchestrator.get_analysis_status(analysis_id)
        return jsonify(status)
    
    return jsonify({'error': 'Analysis not found', 'analysis_id': analysis_id}), 404

@app.route('/api/user/analyses', methods=['GET'])
def api_get_user_analyses():
    """Get all analyses for the current user session"""
    if 'analyses' not in session:
        return jsonify({'analyses': []})
    
    analyses = []
    for analysis_id, analysis_data in session['analyses'].items():
        # Calculate elapsed/completion time
        start_time = analysis_data.get('started_at', time.time())
        if analysis_data.get('status') == 'completed':
            elapsed_seconds = int(analysis_data.get('completed_at', time.time()) - start_time)
        else:
            elapsed_seconds = int(time.time() - start_time)
        
        analysis_info = {
            'id': analysis_id,
            'title': analysis_data.get('title', 'Custom Analysis'),
            'status': analysis_data.get('status', 'unknown'),
            'elapsed_time': elapsed_seconds,
            'started_at': analysis_data.get('started_at'),
            'case_preview': analysis_data.get('case_text', ''),
            'use_free_models': analysis_data.get('use_free_models', True)
        }
        
        if analysis_data.get('status') == 'completed':
            analysis_info['report_available'] = bool(analysis_data.get('report_file'))
        elif analysis_data.get('status') == 'failed':
            analysis_info['error'] = analysis_data.get('error', 'Unknown error')
        
        analyses.append(analysis_info)
    
    # Sort by start time, most recent first
    analyses.sort(key=lambda x: x.get('started_at', 0), reverse=True)
    
    return jsonify({'analyses': analyses})

@app.route('/api/analyze/<analysis_id>', methods=['DELETE'])
def api_cancel_analysis(analysis_id):
    """Cancel an ongoing analysis"""
    if not orchestrator:
        return jsonify({'error': 'Orchestrator not available'}), 503
    
    result = orchestrator.cancel_analysis(analysis_id)
    return jsonify(result)

@app.route('/api/analyze/<analysis_id>/retry', methods=['POST'])
def api_retry_failed_models(analysis_id):
    """Retry failed models in an analysis"""
    if not orchestrator:
        return jsonify({'error': 'Orchestrator not available'}), 503
    
    result = orchestrator.retry_failed_models(analysis_id)
    return jsonify(result)

@app.route('/api/analyze/<analysis_id>/rate', methods=['POST'])
def api_rate_diagnosis(analysis_id):
    """Rate a diagnosis from analysis"""
    try:
        data = request.json or {}
        diagnosis = data.get('diagnosis', '')
        rating = data.get('rating', 0)
        is_correct = data.get('is_correct')
        feedback = data.get('feedback')
        
        if not diagnosis or not (1 <= rating <= 5):
            return jsonify({'error': 'Invalid rating data'}), 400
        
        # Save rating to database
        if db_manager:
            db_manager.save_rating(
                analysis_id=analysis_id,
                diagnosis=diagnosis,
                rating=rating,
                is_correct=is_correct,
                feedback=feedback,
                session_id=session.get('session_id')
            )
        
        return jsonify({'success': True, 'message': 'Rating saved successfully'})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/analyze/<analysis_id>/share', methods=['POST'])
def api_create_share_link(analysis_id):
    """Create a shareable link for analysis results"""
    try:
        data = request.json or {}
        expiry_hours = data.get('expiry_hours', 24)
        
        if not (1 <= expiry_hours <= 168):  # 1 hour to 1 week max
            expiry_hours = 24
        
        # Create shareable link
        if db_manager:
            share_id = db_manager.create_shareable_link(
                analysis_id=analysis_id,
                hours=expiry_hours,
                session_id=session.get('session_id')
            )
            
            # Generate full URL
            share_url = url_for('view_shared_analysis', share_id=share_id, _external=True)
            
            return jsonify({
                'success': True,
                'share_url': share_url,
                'share_id': share_id,
                'expires_in_hours': expiry_hours
            })
        
        return jsonify({'error': 'Database not available'}), 503
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/analyze/<analysis_id>/download')
def api_download_analysis(analysis_id):
    """Download analysis report as HTML or PDF matching case detail format"""
    try:
        from datetime import datetime
        from flask import make_response, request
        import json
        
        report_format = request.args.get('format', 'html')  # html or pdf
        
        # Check if we have real analysis data
        ensemble_data_file = REPORTS_DIR / f"{analysis_id}_ensemble_data.json"
        
        if ensemble_data_file.exists():
            # Load actual analysis data
            with open(ensemble_data_file, 'r') as f:
                ensemble_data = json.load(f)
            
            # Use the comprehensive report generator
            from src.medley.reporters.comprehensive_report import ComprehensiveReportGenerator
            
            generator = ComprehensiveReportGenerator()
            
            if report_format == 'pdf':
                # Generate PDF report
                output_file = REPORTS_DIR / f"{analysis_id}_report.pdf"
                generator.generate_report(
                    ensemble_results=ensemble_data,
                    output_format='pdf',
                    output_file=str(output_file)
                )
                
                # Return PDF file
                with open(output_file, 'rb') as f:
                    pdf_content = f.read()
                
                response = make_response(pdf_content)
                response.headers['Content-Type'] = 'application/pdf'
                response.headers['Content-Disposition'] = f'attachment; filename=medley_report_{analysis_id}.pdf'
                return response
            else:
                # Generate HTML report matching case detail format
                html_content = generate_analysis_html_report(ensemble_data, analysis_id)
                response = make_response(html_content)
                response.headers['Content-Type'] = 'text/html'
                response.headers['Content-Disposition'] = f'attachment; filename=medley_report_{analysis_id}.html'
                return response
                
        # For demo analyses, generate a report on the fly
        elif analysis_id.startswith('demo_'):
            # Create HTML report
            html_content = f"""
            <!DOCTYPE html>
            <html lang="en">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>MEDLEY Analysis Report - {analysis_id}</title>
                <style>
                    body {{ font-family: system-ui, -apple-system, sans-serif; margin: 40px; color: #333; }}
                    .header {{ background: linear-gradient(135deg, #2E7D32, #43A047); color: white; padding: 30px; border-radius: 12px; margin-bottom: 30px; }}
                    .section {{ margin: 30px 0; padding: 20px; background: #f5f5f5; border-radius: 8px; }}
                    .diagnosis {{ display: inline-block; padding: 8px 16px; margin: 5px; border-radius: 20px; background: white; }}
                    .primary {{ background: #2E7D32; color: white; }}
                    .alternative {{ background: #FFA726; color: white; }}
                    .minority {{ background: #9E9E9E; color: white; }}
                    .timestamp {{ text-align: right; color: #666; font-size: 0.9em; }}
                </style>
            </head>
            <body>
                <div class="header">
                    <h1>MEDLEY Analysis Report</h1>
                    <p>Medical AI Ensemble Diagnostic Analysis</p>
                    <p>Analysis ID: {analysis_id}</p>
                </div>
                
                <div class="section">
                    <h2>Primary Diagnoses</h2>
                    <div>
                        <span class="diagnosis primary">Acute Myocardial Infarction (STEMI) - 85%</span>
                        <span class="diagnosis primary">Unstable Angina - 72%</span>
                    </div>
                </div>
                
                <div class="section">
                    <h2>Alternative Diagnoses</h2>
                    <div>
                        <span class="diagnosis alternative">Pulmonary Embolism - 45%</span>
                        <span class="diagnosis alternative">Aortic Dissection - 38%</span>
                    </div>
                </div>
                
                <div class="section">
                    <h2>Minority Opinions</h2>
                    <div>
                        <span class="diagnosis minority">Costochondritis - 15%</span>
                        <span class="diagnosis minority">Panic Attack - 10%</span>
                    </div>
                </div>
                
                <div class="section">
                    <h2>Model Performance</h2>
                    <p>✅ 7 of 8 models completed successfully</p>
                    <p>❌ 1 model failed (Zephyr 7B Beta - timeout)</p>
                    <p>Success Rate: 87.5%</p>
                </div>
                
                <div class="timestamp">
                    <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                    <p>MEDLEY - Stockholm Medical Artificial Intelligence and Learning Environments</p>
                </div>
            </body>
            </html>
            """
            
            # Create response with proper headers for download
            response = make_response(html_content)
            response.headers['Content-Type'] = 'text/html'
            response.headers['Content-Disposition'] = f'attachment; filename=medley_report_{analysis_id}.html'
            return response
            
        else:
            # For real analyses, fetch from database
            if db_manager:
                analysis = db_manager.get_analysis(analysis_id)
                if analysis:
                    # Generate report from actual data
                    # TODO: Implement full report generation
                    pass
            
            return jsonify({'error': 'Analysis not found'}), 404
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ============== LONG POLLING API ENDPOINTS ==============

@app.route('/api/progress/session', methods=['POST'])
def api_create_progress_session():
    """Create a new progress session for long polling"""
    try:
        session_id = progress_manager.create_session()
        return jsonify({
            'success': True,
            'session_id': session_id
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/progress/<session_id>/events', methods=['GET'])
def api_get_progress_events(session_id):
    """Get progress events for a session (long polling endpoint)"""
    try:
        # Get query parameters
        since_id = request.args.get('since_id')
        timeout = float(request.args.get('timeout', 30.0))
        timeout = min(timeout, 60.0)  # Cap at 60 seconds
        
        # Get events with long polling
        events = progress_manager.get_events(session_id, since_id, timeout)
        
        # Auto-cleanup old sessions periodically
        progress_manager.cleanup_old_sessions()
        
        return jsonify({
            'success': True,
            'events': events,
            'session_id': session_id
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/progress/<session_id>/status', methods=['GET'])
def api_get_progress_status(session_id):
    """Get current status of a progress session"""
    try:
        status = progress_manager.get_session_status(session_id)
        
        if status:
            return jsonify({
                'success': True,
                'status': status,
                'session_id': session_id
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Session not found',
                'session_id': session_id
            }), 404
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/progress/stats', methods=['GET'])
def api_get_progress_stats():
    """Get progress manager statistics"""
    try:
        return jsonify({
            'success': True,
            'stats': {
                'active_sessions': progress_manager.get_session_count(),
                'server_time': datetime.utcnow().isoformat()
            }
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ============== WEBSOCKET EVENT HANDLERS ==============

@socketio.on('cancel_analysis')
def handle_cancel_analysis(data):
    """Handle analysis cancellation request"""
    analysis_id = data.get('analysis_id')
    print(f"🚫 Cancel analysis requested for: {analysis_id}")
    
    # Emit cancellation confirmation
    emit('analysis_cancelled', {
        'analysis_id': analysis_id,
        'message': 'Analysis cancellation requested'
    })
    
    # Note: For CLI processes, we would need to track and kill the subprocess
    # For now, this provides UI feedback
    
    return True

@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    from flask import request
    client_id = request.sid
    connected_clients.add(client_id)
    print(f"🟢 Client connected: {client_id} (Total: {len(connected_clients)})")
    emit('connected', {'message': 'Connected to MEDLEY server'})

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    from flask import request
    client_id = request.sid
    connected_clients.discard(client_id)
    print(f"🔴 Client disconnected: {client_id} (Total: {len(connected_clients)})")

@socketio.on('join_analysis')
def handle_join_analysis(data):
    """Join analysis room for updates"""
    analysis_id = data.get('analysis_id')
    if analysis_id:
        join_room(f'analysis_{analysis_id}')
        emit('joined_room', {'room': f'analysis_{analysis_id}'})

@socketio.on('leave_analysis')
def handle_leave_analysis(data):
    """Leave analysis room"""
    analysis_id = data.get('analysis_id')
    if analysis_id:
        leave_room(f'analysis_{analysis_id}')
        emit('left_room', {'room': f'analysis_{analysis_id}'})

@socketio.on('analyze_case')
def handle_analyze_case(data):
    """Handle real-time case analysis via WebSocket"""
    import threading
    import time
    
    case_text = data.get('case_text') or data.get('content', '')
    
    # Check if we should use simulation or real analysis
    # Force real analysis - always set to False
    use_simulation = False  # Always use real CLI analysis
    print(f"🔄 FORCED use_simulation = {use_simulation} (ignoring frontend request)")
    
    if use_simulation:
        # Use simulation mode
        analysis_id = 'demo_' + datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Get model names for display
        selected_models_list = data.get('selected_models', [])
        model_mapping = {
            'google/gemini-2.0-flash-exp:free': 'Gemini 2.0 Flash',
            'meta-llama/llama-3.2-3b-instruct:free': 'Llama 3.2 3B',
            'microsoft/phi-3-medium-128k-instruct:free': 'Phi-3 Medium',
            'mistralai/mistral-7b-instruct:free': 'Mistral 7B',
            'anthropic/claude-3.5-sonnet': 'Claude 3.5 Sonnet',
            'openai/gpt-4o': 'GPT-4o',
            'x-ai/grok-beta': 'Grok Beta',
        }
        display_models = [model_mapping.get(model_id, model_id) for model_id in selected_models_list] if selected_models_list else ['Gemini 2.0 Flash', 'Llama 3.2 3B', 'Phi-3 Medium', 'Mistral 7B', 'Qwen 2.5', 'DeepSeek Chat']
        
        # Emit start event
        emit('analysis_started', {
            'analysis_id': analysis_id,
            'message': 'Starting simulated analysis',
            'models': display_models
        })
        
        def run_simulation():
            """Run a quick simulation with progress updates"""
            try:
                with app.app_context():
                    # Use selected models or default models
                    selected_models = data.get('selected_models', [])
                    if selected_models:
                        # Map model IDs to display names
                        model_mapping = {
                            'google/gemini-2.0-flash-exp:free': 'Gemini 2.0 Flash',
                            'meta-llama/llama-3.2-3b-instruct:free': 'Llama 3.2 3B',
                            'microsoft/phi-3-medium-128k-instruct:free': 'Phi-3 Medium',
                            'mistralai/mistral-7b-instruct:free': 'Mistral 7B',
                            'anthropic/claude-3.5-sonnet': 'Claude 3.5 Sonnet',
                            'openai/gpt-4o': 'GPT-4o',
                            'x-ai/grok-beta': 'Grok Beta',
                        }
                        models = [model_mapping.get(model_id, model_id) for model_id in selected_models]
                    else:
                        models = ['Gemini 2.0 Flash', 'Llama 3.2 3B', 'Phi-3 Medium', 'Mistral 7B', 'Qwen 2.5', 'DeepSeek Chat']
                    
                    for i, model in enumerate(models):
                        time.sleep(1.5)  # Quick simulation
                        progress = ((i + 1) / len(models)) * 100
                        
                        socketio.emit('model_progress', {
                            'analysis_id': analysis_id,
                            'model': model,
                            'status': f'✅ {model} completed',
                            'progress': progress
                        })
                    
                    # Generate case-specific results based on case text
                    case_text = data.get('case_text', '').lower()
                    
                    # Default results
                    results = {
                        'primary_diagnoses': [
                            {'diagnosis': 'Community-Acquired Pneumonia', 'confidence': 85},
                            {'diagnosis': 'Congestive Heart Failure', 'confidence': 75}
                        ],
                        'alternative_diagnoses': [
                            {'diagnosis': 'Pulmonary Embolism', 'confidence': 45},
                            {'diagnosis': 'Acute Bronchitis', 'confidence': 40},
                            {'diagnosis': 'COVID-19 Pneumonia', 'confidence': 35}
                        ],
                        'minority_opinions': [
                            {'diagnosis': 'Tuberculosis', 'confidence': 15},
                            {'diagnosis': 'Lung Cancer', 'confidence': 10}
                        ],
                        'consensus': 'Community-acquired pneumonia with possible heart failure exacerbation. Consider ruling out pulmonary embolism given the presentation.'
                    }
                    
                    # Customize based on keywords in case
                    if 'maria' in case_text or 'heart failure' in case_text or 'decompensated' in case_text:
                        results = {
                            'primary_diagnoses': [
                                {'diagnosis': 'Acute Decompensated Heart Failure', 'confidence': 92},
                                {'diagnosis': 'Atrial Fibrillation with RVR', 'confidence': 88}
                            ],
                            'alternative_diagnoses': [
                                {'diagnosis': 'Pneumonia (CAP)', 'confidence': 55},
                                {'diagnosis': 'Acute Kidney Injury', 'confidence': 50},
                                {'diagnosis': 'Hypertensive Emergency', 'confidence': 45}
                            ],
                            'minority_opinions': [
                                {'diagnosis': 'Pulmonary Embolism', 'confidence': 20},
                                {'diagnosis': 'COPD Exacerbation', 'confidence': 15}
                            ],
                            'consensus': 'Acute decompensated heart failure with new-onset atrial fibrillation. Volume overload secondary to medication non-compliance and dietary indiscretion. Consider diuresis and rate control.'
                        }
                    elif 'fever' in case_text and 'mediterranean' in case_text:
                        results = {
                            'primary_diagnoses': [
                                {'diagnosis': 'Familial Mediterranean Fever', 'confidence': 90},
                                {'diagnosis': 'Periodic Fever Syndrome', 'confidence': 80}
                            ],
                            'alternative_diagnoses': [
                                {'diagnosis': 'Adult-Onset Still Disease', 'confidence': 45},
                                {'diagnosis': 'Systemic Lupus Erythematosus', 'confidence': 40},
                                {'diagnosis': 'Inflammatory Bowel Disease', 'confidence': 35}
                            ],
                            'minority_opinions': [
                                {'diagnosis': 'Lymphoma', 'confidence': 18},
                                {'diagnosis': 'Tuberculosis', 'confidence': 12}
                            ],
                            'consensus': 'Clinical presentation highly suggestive of Familial Mediterranean Fever given ethnicity, family history, and periodic fever pattern. Recommend genetic testing for MEFV mutation and trial of colchicine.'
                        }
                    elif 'abdominal' in case_text or 'pain' in case_text:
                        results = {
                            'primary_diagnoses': [
                                {'diagnosis': 'Acute Appendicitis', 'confidence': 78},
                                {'diagnosis': 'Cholecystitis', 'confidence': 72}
                            ],
                            'alternative_diagnoses': [
                                {'diagnosis': 'Gastroenteritis', 'confidence': 50},
                                {'diagnosis': 'Kidney Stone', 'confidence': 45},
                                {'diagnosis': 'Pancreatitis', 'confidence': 40}
                            ],
                            'minority_opinions': [
                                {'diagnosis': 'Ovarian Cyst', 'confidence': 25},
                                {'diagnosis': 'Diverticulitis', 'confidence': 20}
                            ],
                            'consensus': 'Acute abdominal pain with inflammatory signs. Recommend CT abdomen/pelvis for definitive diagnosis. Consider surgical consultation.'
                        }
                    
                    # Send completion with case-specific results
                    socketio.emit('analysis_complete', {
                        'analysis_id': analysis_id,
                        'message': 'Simulation complete',
                        'results': results
                    })
            except Exception as e:
                socketio.emit('analysis_error', {
                    'analysis_id': analysis_id,
                    'error': f'Simulation failed: {str(e)}'
                })
        
        # Start simulation thread
        thread = threading.Thread(target=run_simulation)
        thread.daemon = True
        thread.start()
        return
    
    elif False and orchestrator and case_text and not use_simulation:
        # Use orchestrator for custom cases (disabled - using CLI instead)
        case_title = data.get('case_title', 'Custom Case')
        use_free_models = data.get('use_free_models') or data.get('free_only', False)
        selected_models = data.get('selected_models')
        api_key = data.get('api_key') or session.get('openrouter_api_key') or os.getenv('OPENROUTER_API_KEY')
        
        if not api_key:
            emit('error', {'message': 'No API key available'})
            return
        
        result = orchestrator.analyze_custom_case(
            case_text=case_text,
            case_title=case_title,
            use_free_models=use_free_models,
            selected_models=selected_models,
            session_id=session.get('session_id'),
            api_key=api_key
        )
        
        emit('analysis_started', result)
    else:
        # Use CLI wrapper to generate report like cases 1-12
        import tempfile
        import subprocess
        import re
        
        # Use frontend's analysis_id if provided, otherwise generate one
        analysis_id = data.get('analysis_id') or ('Case_' + datetime.now().strftime('%Y%m%d_%H%M%S'))
        print(f"DEBUG: Using analysis_id: {analysis_id} (from frontend: {data.get('analysis_id')})")
        
        # Store analysis metadata in session for persistence
        if 'analyses' not in session:
            session['analyses'] = {}
        
        session['analyses'][analysis_id] = {
            'id': analysis_id,
            'title': data.get('case_title', 'Custom Analysis'),
            'status': 'running',
            'started_at': time.time(),
            'case_text': case_text[:200] + '...' if len(case_text) > 200 else case_text,  # Store preview
            'use_free_models': data.get('use_free_models', True)
        }
        
        # Get selected models from the request data FIRST
        selected_models = data.get('selected_models', [])
        if not selected_models:
            # Default free models if none selected
            selected_models = [
                'deepseek/deepseek-chat-v3.1:free',
                'deepseek/deepseek-r1:free',
                'google/gemma-2-9b-it:free',
                'google/gemma-3-12b-it:free',
                'meta-llama/llama-3.2-3b-instruct:free',
                'mistralai/mistral-7b-instruct:free',
                'shisa-ai/shisa-v2-llama3.3-70b:free'
            ]
        
        # Define model display names mapping
        model_display_names_map = {
            # Free models
            'google/gemini-2.0-flash-exp:free': 'Gemini 2.0 Flash',
            'google/gemini-flash-1.5-8b:free': 'Gemini Flash 1.5 8B',
            'google/gemma-2-9b-it:free': 'Gemma 2 9B',
            'google/gemma-3-12b-it:free': 'Gemma 3 12B',
            'meta-llama/llama-3.2-3b-instruct:free': 'Llama 3.2 3B',
            'openai/gpt-oss-20b:free': 'GPT OSS 20B',
            'meta-llama/llama-3.2-1b-instruct:free': 'Llama 3.2 1B',
            'meta-llama/llama-3.1-8b-instruct:free': 'Llama 3.1 8B',
            'microsoft/phi-3-medium-128k-instruct:free': 'Phi-3 Medium',
            'microsoft/phi-3-mini-128k-instruct:free': 'Phi-3 Mini',
            'mistralai/mistral-7b-instruct:free': 'Mistral 7B',
            'qwen/qwen-2.5-coder-32b-instruct': 'Qwen 2.5 Coder',
            'deepseek/deepseek-chat-v3-0324:free': 'DeepSeek Chat',
            'deepseek/deepseek-chat-v3.1:free': 'DeepSeek Chat v3.1',
            'huggingfaceh4/zephyr-7b-beta:free': 'Zephyr 7B',
            'openchat/openchat-7b:free': 'OpenChat 7B',
            'undi95/toppy-m-7b:free': 'Toppy M 7B',
            'gryphe/mythomist-7b:free': 'Mythomist 7B',
            'nousresearch/nous-capybara-7b:free': 'Nous Capybara 7B',
            'koboldai/psyfighter-13b-2:free': 'Psyfighter 13B v2',
            'jebcarter/psyfighter-13b:free': 'Psyfighter 13B',
        }
        
        # Convert selected model IDs to display names for the UI
        display_model_names = []
        for model_id in selected_models:
            if model_id in model_display_names_map:
                display_model_names.append(model_display_names_map[model_id])
            else:
                # Extract name from model ID if not in mapping
                if '/' in model_id:
                    parts = model_id.split('/')
                    name = parts[1].replace('-', ' ').replace(':', ' ').title()
                    name = name.replace(' Free', '').strip()
                    display_model_names.append(name)
                else:
                    display_model_names.append(model_id)
        
        # Emit start event with ALL selected models
        emit('analysis_started', {
            'analysis_id': analysis_id,
            'message': f'Starting ensemble analysis with {len(selected_models)} models',
            'models': display_model_names  # Send all selected model names
        })
        
        # Get session data before entering thread (to avoid request context issues)
        try:
            session_api_key = session.get('api_key')
            session_openrouter_key = session.get('openrouter_api_key')
        except:
            session_api_key = None
            session_openrouter_key = None
        
        def run_cli_ensemble():
            """Run the medley CLI ensemble command with progress monitoring"""
            print(f"DEBUG: Starting run_cli_ensemble function")
            
            # Access outer scope variables
            nonlocal selected_models, analysis_id, case_text
            
            try:
                with app.app_context():
                    print(f"DEBUG: In app context, creating temp file")
                    # Create a temporary case file
                    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
                        f.write(case_text)
                        case_file_path = f.name
                    print(f"DEBUG: Created temp file: {case_file_path}")
                    
                    # Get case ID for cache monitoring
                    case_name = Path(case_file_path).stem
                    
                    # Get API key from web app session (prioritize over env var)
                    # Use pre-captured session data to avoid request context issues
                    api_key = data.get('api_key') or session_api_key or session_openrouter_key
                    
                    # Only use env variable if no web app API key is available
                    if not api_key:
                        api_key = os.getenv('OPENROUTER_API_KEY')
                    
                    # Prepare environment with API key
                    env = os.environ.copy()
                    if api_key:
                        # Clear any existing env API key and use the web app one
                        env.pop('OPENROUTER_API_KEY', None)  # Remove env var if it exists
                        env['OPENROUTER_API_KEY'] = api_key  # Set the web app API key
                        print(f"✅ Using API key from web app session for CLI")
                    else:
                        print("⚠️  No API key available from web app or environment")
                    
                    # Get other parameters from UI (selected_models already retrieved above)
                    use_free_models = data.get('use_free_models', False)
                    model_limit = data.get('model_limit', 'all')
                    orchestrator_model = data.get('orchestrator_model', 'auto')
                    
                    # Apply model limit if specified
                    if model_limit != 'all' and model_limit.isdigit():
                        selected_models = selected_models[:int(model_limit)]
                    
                    print(f"Using {len(selected_models)} selected models: {selected_models}")
                    print(f"Using orchestrator model: {orchestrator_model}")
                    
                    # Real progress will be emitted by the GeneralMedicalPipeline via SocketIO
                    
                    # Use GeneralMedicalPipeline directly instead of CLI
                    # This ensures we get the new report format with all sections
                    from general_medical_pipeline import GeneralMedicalPipeline
                    
                    # Get user's API key from captured session variables
                    user_api_key = session_api_key or session_openrouter_key
                    if user_api_key:
                        print("✅ Using API key from user session")
                    else:
                        # Fallback to environment variable for backward compatibility
                        user_api_key = os.getenv('OPENROUTER_API_KEY')
                        if user_api_key:
                            print("✅ Using API key from environment")
                        else:
                            print("⚠️  No API key found in session or environment")
                    
                    # Set environment for model selection
                    if use_free_models or all(':free' in model for model in selected_models):
                        os.environ['USE_FREE_MODELS'] = 'true'
                        print("Using free models only")
                    else:
                        os.environ.pop('USE_FREE_MODELS', None)
                    
                    # Initialize pipeline with user's API key, selected models, and socketio for real-time progress
                    # Use case_name for caching but analysis_id for SocketIO progress events
                    pipeline = GeneralMedicalPipeline(case_name, api_key=user_api_key, selected_models=selected_models, socketio=socketio, display_case_id=analysis_id)
                    
                    # Set the orchestrator model selection from GUI
                    pipeline.orchestrator_model = orchestrator_model
                    
                    # Read case content
                    with open(case_file_path, 'r') as f:
                        case_content = f.read()
                    
                    print(f"Running GeneralMedicalPipeline for {case_name}")
                    print(f"Case file: {case_file_path}")
                    print(f"Using {len(selected_models)} models")
                    
                    # Create case directory name (will be created by CLI)
                    case_id = Path(case_file_path).stem
                    cache_base = Path("cache/responses")
                    cache_dir = cache_base / case_id
                    
                    completed_models = set()
                    total_models = len(selected_models)
                    model_display_names = {
                        # Free models - Updated to match actual working models
                        'deepseek/deepseek-r1:free': 'DeepSeek R1',
                        'deepseek/deepseek-chat:free': 'DeepSeek Chat',
                        'meta-llama/llama-3.1-70b-instruct:free': 'Llama 3.1 70B',
                        'google/gemma-3-27b-it:free': 'Gemma 3 27B',
                        'qwen/qwen-2.5-72b-instruct:free': 'Qwen 2.5 72B',
                        'nvidia/llama-3.1-nemotron-70b-instruct:free': 'Nemotron 70B',
                        'mistralai/mistral-7b-instruct:free': 'Mistral 7B',
                        'openai/gpt-oss-20b:free': 'GPT OSS 20B',
                        'google/gemma-3-4b-it:free': 'Gemma 3 4B',
                        'meta-llama/llama-3.2-3b-instruct:free': 'Llama 3.2 3B',
                        # Premium models
                        'anthropic/claude-3.5-sonnet': 'Claude 3.5 Sonnet',
                        'anthropic/claude-opus-4.1': 'Claude Opus 4.1',
                        'openai/gpt-4o': 'GPT-4o',
                        'openai/gpt-4-turbo': 'GPT-4 Turbo',
                        'x-ai/grok-4': 'Grok 4',
                        'x-ai/grok-beta': 'Grok Beta',
                        'google/gemini-pro-1.5': 'Gemini Pro 1.5',
                        'google/gemini-pro-vision': 'Gemini Pro Vision',
                        'mistralai/mistral-large': 'Mistral Large',
                        'mistralai/mistral-medium': 'Mistral Medium',
                        'cohere/command-r-plus': 'Command R+',
                        'deepseek/deepseek-chat': 'DeepSeek V3',
                        'meta-llama/llama-3.1-405b-instruct': 'Llama 3.1 405B'
                    }
                    
                    # Let the GeneralMedicalPipeline handle all progress updates via SocketIO
                    
                    # Run the pipeline analysis
                    try:
                        # TODO: Add progress callback support to GeneralMedicalPipeline
                        # For now, the simulated progress will continue
                        results = pipeline.run_complete_analysis(
                            case_description=case_content,
                            case_title='Custom Case Analysis'
                        )
                        
                        print(f"Pipeline completed successfully")
                        print(f"Results keys: {list(results.keys())}")
                        
                        # The pipeline returns paths to the generated files
                        ensemble_file_path = results.get('data_file')
                        pdf_file_path = results.get('report_file')
                        
                    except Exception as e:
                        print(f"Pipeline failed: {str(e)}")
                        raise Exception(f"Analysis failed: {str(e)}")
                    
                    # Find the generated files
                    import glob
                    
                    # Look for all JSON files first
                    all_json_files = glob.glob(str(REPORTS_DIR / f"*.json"))
                    print(f"Found {len(all_json_files)} JSON files in reports dir")
                    if all_json_files:
                        print(f"Recent JSON files: {[os.path.basename(f) for f in sorted(all_json_files, key=os.path.getctime)[-5:]]}")
                    
                    ensemble_files = glob.glob(str(REPORTS_DIR / f"*ensemble*.json"))
                    pdf_files = glob.glob(str(REPORTS_DIR / f"*.pdf"))
                    
                    print(f"Found {len(ensemble_files)} ensemble files and {len(pdf_files)} PDF files")
                    
                    # Get the most recent files
                    results = None
                    new_pdf_path = None
                    
                    if ensemble_files:
                        latest_ensemble = max(ensemble_files, key=os.path.getctime)
                        print(f"Latest ensemble file: {os.path.basename(latest_ensemble)}")
                        
                        # Rename to match our analysis ID
                        new_ensemble_path = REPORTS_DIR / f"{analysis_id}_ensemble_data.json"
                        os.rename(latest_ensemble, new_ensemble_path)
                        
                        # Load the results
                        with open(new_ensemble_path, 'r') as f:
                            results = json.load(f)
                        print(f"Loaded results with keys: {list(results.keys())}")
                    else:
                        print("WARNING: No ensemble files found after CLI completion")
                    
                    # Files already renamed above, get the new paths
                    if ensemble_files:
                        new_ensemble_path = REPORTS_DIR / f"{analysis_id}_ensemble_data.json"
                        print(f"✅ Using renamed JSON: {new_ensemble_path}")
                    
                    if pdf_files:
                        new_pdf_path = REPORTS_DIR / f"FINAL_{analysis_id}_comprehensive.pdf"  
                        print(f"✅ Using renamed PDF: {new_pdf_path}")
                    
                    # Clean up temp file
                    Path(case_file_path).unlink(missing_ok=True)
                    
                    # Check if we have results
                    if not results:
                        print("ERROR: No results found after CLI completion")
                        socketio.emit('error', {
                            'analysis_id': analysis_id,
                            'message': 'Analysis completed but no results were generated. Please try again.'
                        })
                        return
                    
                    # Extract diagnoses from results
                    # Check if we have diagnostic_landscape (new format) or consensus_analysis (old format)
                    diagnostic_landscape = results.get('diagnostic_landscape', {})
                    
                    # If no diagnostic_landscape, convert from consensus_analysis
                    if not diagnostic_landscape and 'consensus_analysis' in results:
                        consensus = results['consensus_analysis']
                        diagnostic_landscape = {
                            'primary_diagnosis': {},
                            'strong_alternatives': [],
                            'minority_opinions': [],
                            'synthesis': ''
                        }
                        
                        # Extract primary diagnosis from consensus
                        # Handle two formats: old (diagnoses dict) and new (direct fields)
                        if consensus.get('primary_diagnosis'):
                            # New format with direct primary_diagnosis field
                            diagnostic_landscape['primary_diagnosis'] = {
                                'name': consensus['primary_diagnosis'],
                                'agreement_percentage': consensus.get('primary_confidence', 0) * 100,
                                'model_count': consensus.get('responding_models', 0),
                                'supporting_models': []
                            }
                            
                            # Extract alternatives
                            for alt in consensus.get('alternative_diagnoses', []):
                                if isinstance(alt, dict):
                                    diagnostic_landscape['strong_alternatives'].append({
                                        'name': alt.get('diagnosis', ''),
                                        'agreement_percentage': alt.get('confidence', 0) * 100,
                                        'model_count': alt.get('model_count', 0),
                                        'supporting_models': alt.get('supporting_models', [])
                                    })
                            
                            # Extract minority opinions
                            for minority in consensus.get('minority_opinions', []):
                                if isinstance(minority, dict):
                                    diagnostic_landscape['minority_opinions'].append({
                                        'name': minority.get('diagnosis', ''),
                                        'model_count': minority.get('model_count', 0),
                                        'supporting_models': minority.get('supporting_models', [])
                                    })
                        elif 'diagnoses' in consensus:
                            # Old format with diagnoses dict
                            diagnoses = consensus['diagnoses']
                            if diagnoses:
                                # Sort by confidence/count
                                sorted_diags = sorted(diagnoses.items(), 
                                                    key=lambda x: x[1].get('count', 0), 
                                                    reverse=True)
                                
                                # Primary is the most common
                                if sorted_diags:
                                    primary_name, primary_data = sorted_diags[0]
                                    total_models = sum(d.get('count', 0) for _, d in diagnoses.items())
                                    diagnostic_landscape['primary_diagnosis'] = {
                                        'name': primary_name,
                                        'agreement_percentage': (primary_data.get('count', 0) / total_models * 100) if total_models > 0 else 0,
                                        'model_count': primary_data.get('count', 0),
                                        'supporting_models': primary_data.get('models', [])
                                    }
                                
                                # Alternatives are the next diagnoses
                                for diag_name, diag_data in sorted_diags[1:4]:
                                    diagnostic_landscape['strong_alternatives'].append({
                                        'name': diag_name,
                                        'agreement_percentage': (diag_data.get('count', 0) / total_models * 100) if total_models > 0 else 0,
                                        'model_count': diag_data.get('count', 0),
                                        'supporting_models': diag_data.get('models', [])
                                    })
                                
                                # Minority opinions (single model diagnoses)
                                for diag_name, diag_data in sorted_diags:
                                    if diag_data.get('count', 0) == 1:
                                        diagnostic_landscape['minority_opinions'].append({
                                            'name': diag_name,
                                            'model_count': 1,
                                            'supporting_models': diag_data.get('models', [])
                                        })
                        
                        # Get synthesis from consensus summary
                        if 'summary' in consensus:
                            diagnostic_landscape['synthesis'] = consensus['summary']
                    
                    # Add diagnostic_landscape to results if it was created
                    if diagnostic_landscape and not results.get('diagnostic_landscape'):
                        results['diagnostic_landscape'] = diagnostic_landscape
                        # Save the enhanced results back to renamed JSON file
                        if new_ensemble_path and new_ensemble_path.exists():
                            with open(new_ensemble_path, 'w') as f:
                                json.dump(results, f, indent=2)
                            print(f"Enhanced JSON with diagnostic_landscape saved to {new_ensemble_path}")
                    
                    primary = diagnostic_landscape.get('primary_diagnosis', {})
                    alternatives = diagnostic_landscape.get('strong_alternatives', [])
                    minority = diagnostic_landscape.get('minority_opinions', [])
                    
                    # Format results properly
                    formatted_results = {
                        'primary_diagnoses': [],
                        'alternative_diagnoses': [],
                        'minority_opinions': [],
                        'consensus': diagnostic_landscape.get('synthesis', '')
                    }
                    
                    # Add primary diagnosis
                    if primary and primary.get('name'):
                        formatted_results['primary_diagnoses'].append({
                            'diagnosis': primary.get('name'),
                            'confidence': primary.get('agreement_percentage', 0)
                        })
                    
                    # Add alternatives
                    for alt in alternatives[:5]:
                        if alt.get('name'):
                            formatted_results['alternative_diagnoses'].append({
                                'diagnosis': alt.get('name'),
                                'confidence': alt.get('agreement_percentage', 0)
                            })
                    
                    # Add minority opinions
                    for m in minority[:3]:
                        if m.get('name'):
                            formatted_results['minority_opinions'].append({
                                'diagnosis': m.get('name'),
                                'confidence': m.get('model_count', 0) * 10
                            })
                    
                    # Generate HTML report URL
                    html_file = new_pdf_path.with_suffix('.html') if 'new_pdf_path' in locals() else None
                    
                    # Save the complete results for the case viewer
                    if 'new_ensemble_path' in locals():
                        # The JSON file already exists with full results
                        pass
                    
                    # Create HTML report if PDF exists but HTML doesn't
                    html_report_path = None
                    if new_pdf_path and new_pdf_path.exists():
                        # Generate HTML version from the results
                        html_report_path = new_pdf_path.with_suffix('.html')
                        # We'll use the case viewer instead of generating HTML here
                    
                    # Send completion with actual results
                    socketio.emit('analysis_complete', {
                        'analysis_id': analysis_id,
                        'message': 'Analysis complete',
                        'results': formatted_results,
                        'report_url': f'/case/{analysis_id}',  # Use case viewer format
                        'pdf_url': f'/api/case/{analysis_id}/pdf' if new_pdf_path else None,
                        'html_report': f'/case/{analysis_id}'  # Direct to case viewer
                    })
                    
            except Exception as e:
                import traceback
                error_msg = f"Analysis failed: {str(e)}"
                print(f"Error in CLI ensemble: {traceback.format_exc()}")
                socketio.emit('analysis_error', {
                    'analysis_id': analysis_id,
                    'error': error_msg
                })
        
        # If we want to use real CLI 
        print(f"DEBUG: use_simulation = {use_simulation}")
        if not use_simulation:  # Use CLI when simulation is disabled
            print("DEBUG: Starting CLI ensemble thread")
            # Start analysis in background thread
            thread = threading.Thread(target=run_cli_ensemble)
            thread.daemon = True
            thread.start()
            print("DEBUG: Thread started")
            
            return  # Exit early, thread will handle the rest
        
        # Use simulation mode for better UX
        analysis_id = 'demo_' + str(int(time.time()))
        
        # List of free models to simulate
        models = [
            'Gemini 2.0 Flash', 'Llama 3.2 3B', 'Phi-3 Medium', 'Mistral 7B',
            'Qwen 2.5', 'Zephyr 7B Beta', 'Hermes 3', 'DeepSeek Chat'
        ]
        
        emit('analysis_started', {
            'analysis_id': analysis_id,
            'message': 'Analysis started (simulation mode)',
            'models': models
        })
        
        # Execute real pipeline analysis
        def run_real_analysis():
            with app.app_context():
                try:
                    # Run the complete pipeline analysis
                    print(f"🚀 Starting real analysis with {len(selected_models)} models")
                    results = pipeline.run_complete_analysis(case_content, case_title=case_name)
                    
                    # Send completion notification with error handling
                    success = safe_socketio_emit('analysis_complete', {
                        'analysis_id': analysis_id,
                        'message': 'Analysis complete!',
                        'results': {
                            'report_file': results.get('report_file'),
                            'data_file': results.get('data_file'),
                            'total_models': results.get('total_models', len(selected_models))
                        }
                    })
                    
                    # Update session status to completed
                    if 'analyses' in session and analysis_id in session['analyses']:
                        session['analyses'][analysis_id].update({
                            'status': 'completed',
                            'completed_at': time.time(),
                            'report_file': results.get('report_file'),
                            'data_file': results.get('data_file')
                        })
                        session.modified = True
                    
                    if success:
                        print(f"✅ Analysis complete - report: {results.get('report_file')}")
                    else:
                        print(f"✅ Analysis completed (WebSocket disconnected) - report: {results.get('report_file')}")
                    
                except Exception as e:
                    print(f"❌ Pipeline analysis failed: {str(e)}")
                    
                    # Update session status to failed
                    if 'analyses' in session and analysis_id in session['analyses']:
                        session['analyses'][analysis_id].update({
                            'status': 'failed',
                            'error': str(e),
                            'completed_at': time.time()
                        })
                        session.modified = True
                    
                    safe_socketio_emit('analysis_error', {
                        'analysis_id': analysis_id,
                        'error': f'Analysis failed: {str(e)}'
                    })
        
        thread = threading.Thread(target=run_real_analysis)
        thread.daemon = True
        thread.start()

def check_ssl_certificates():
    """Check for SSL certificates and return SSL context if available"""
    ssl_cert = os.getenv('SSL_CERT_PATH', '/etc/letsencrypt/live/medley.smile.ki.se/fullchain.pem')
    ssl_key = os.getenv('SSL_KEY_PATH', '/etc/letsencrypt/live/medley.smile.ki.se/privkey.pem')
    
    if os.path.exists(ssl_cert) and os.path.exists(ssl_key):
        print(f"🔒 SSL certificates found - enabling HTTPS")
        print(f"   Certificate: {ssl_cert}")
        print(f"   Private Key: {ssl_key}")
        return (ssl_cert, ssl_key)
    else:
        print(f"🔓 SSL certificates not found - running HTTP only")
        print(f"   Looked for cert: {ssl_cert}")
        print(f"   Looked for key: {ssl_key}")
        return None

if __name__ == '__main__':
    port = int(os.environ.get('FLASK_PORT', 5003))
    
    # Environment detection
    is_docker = os.path.exists('/.dockerenv') or os.getenv('FLASK_ENV') == 'production'
    is_debug = not is_docker and os.getenv('FLASK_DEBUG', '0') == '1'
    
    # SSL configuration
    ssl_context = check_ssl_certificates()
    
    # Choose appropriate server based on SSL availability and Socket.IO compatibility
    if 'socketio' in globals() and socketio:
        # Use Socket.IO server (current implementation)
        if is_docker:
            print(f"🐳 Starting MEDLEY with Socket.IO in Docker/Production mode on port {port}")
            if ssl_context:
                print("⚠️  Note: SSL with Socket.IO - consider using nginx reverse proxy for production")
            socketio.run(app, debug=False, host='0.0.0.0', port=port, ssl_context=ssl_context)
        else:
            print(f"💻 Starting MEDLEY with Socket.IO in Local Development mode on port {port}")
            socketio.run(app, debug=is_debug, host='0.0.0.0', port=port, ssl_context=ssl_context, allow_unsafe_werkzeug=True)
    else:
        # Fallback to regular Flask server (for long polling only)
        if is_docker:
            print(f"🐳 Starting MEDLEY with Flask server in Docker/Production mode on port {port}")
            app.run(debug=False, host='0.0.0.0', port=port, ssl_context=ssl_context)
        else:
            print(f"💻 Starting MEDLEY with Flask server in Local Development mode on port {port}")
            app.run(debug=is_debug, host='0.0.0.0', port=port, ssl_context=ssl_context)