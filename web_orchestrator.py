#!/usr/bin/env python
"""
Web Orchestrator Integration for MEDLEY
Connects the web UI to the actual ensemble analysis engine
"""

import os
import json
import hashlib
import threading
import traceback
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Callable
from queue import Queue

from flask import current_app
from flask_socketio import SocketIO, emit

# Import the actual orchestrator
import sys
sys.path.append(str(Path(__file__).parent))
from src.medley.models.ensemble import EnsembleOrchestrator
from src.database.models import DatabaseManager, Analysis, ModelResponse
from general_medical_pipeline import GeneralMedicalPipeline

class WebOrchestrator:
    """
    Bridge between web UI and the actual ensemble orchestrator
    Handles real-time progress updates via WebSocket
    """
    
    def __init__(self, socketio: SocketIO, cache_dir: Path, reports_dir: Path, usecases_dir: Path, db_manager: DatabaseManager = None):
        self.socketio = socketio
        self.cache_dir = cache_dir
        self.reports_dir = reports_dir
        self.usecases_dir = usecases_dir
        self.custom_cases_dir = usecases_dir / "custom"  # Separate folder for custom cases
        self.db_manager = db_manager
        self.active_analyses = {}
        self.analysis_queue = Queue()
        
        # Ensure directories exist
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.reports_dir.mkdir(parents=True, exist_ok=True)
        self.usecases_dir.mkdir(parents=True, exist_ok=True)
        self.custom_cases_dir.mkdir(parents=True, exist_ok=True)  # Create custom subfolder
        
    def analyze_custom_case(
        self,
        case_text: str,
        case_title: str = None,
        use_free_models: bool = True,  # Default to free models per user instruction
        selected_models: List[str] = None,
        session_id: str = None,
        api_key: str = None
    ) -> Dict:
        """
        Start analysis of a custom case
        
        Returns:
            Dict with analysis_id and status
        """
        # Generate unique analysis ID
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        case_id = f"custom_{timestamp}"
        
        # Save case to custom subfolder
        case_file = self.custom_cases_dir / f"{case_id}.txt"
        case_file.write_text(case_text)
        
        # Create analysis record
        analysis_info = {
            'id': case_id,
            'title': case_title or f"Custom Case {timestamp}",
            'status': 'queued',
            'progress': 0,
            'total_models': len(selected_models) if selected_models else 31,
            'completed_models': 0,
            'failed_models': 0,
            'start_time': datetime.now().isoformat(),
            'session_id': session_id,
            'case_file': str(case_file),
            'use_free_models': use_free_models,
            'selected_models': selected_models,
            'case_hash': hashlib.md5(case_text.encode()).hexdigest()
        }
        
        self.active_analyses[case_id] = analysis_info
        
        # Save initial analysis to database
        if self.db_manager:
            try:
                db_analysis = Analysis(
                    id=case_id,
                    title=analysis_info['title'],
                    case_text=case_text,
                    case_hash=analysis_info['case_hash'],
                    use_free_models=use_free_models,
                    selected_models=selected_models,
                    model_count=analysis_info['total_models'],
                    status='queued',
                    session_id=session_id,
                    started_at=datetime.now(),
                    estimated_cost=0.0 if use_free_models else analysis_info['total_models'] * 0.002  # Rough estimate
                )
                
                session = self.db_manager.get_session()
                session.add(db_analysis)
                session.commit()
                session.close()
            except Exception as e:
                print(f"⚠️ Database save failed: {e}")
                # Continue without database - don't block analysis
        
        # Start analysis in background thread
        thread = threading.Thread(
            target=self._run_analysis_thread,
            args=(case_id, api_key),
            daemon=True
        )
        thread.start()
        
        # Calculate estimated time based on model count
        total_models = len(selected_models) if selected_models else (
            len(self._get_free_models()) if use_free_models else 31
        )
        # Estimate 3-5 seconds per model for free, 5-8 for paid
        time_per_model = 4 if use_free_models else 6
        estimated_time = total_models * time_per_model
        
        return {
            'analysis_id': case_id,
            'status': 'started',
            'websocket_channel': f'analysis_{case_id}',
            'estimated_time': estimated_time,  # seconds
            'model_count': total_models
        }
    
    def _run_analysis_thread(self, case_id: str, api_key: str):
        """
        Run analysis in background thread
        """
        analysis_info = self.active_analyses[case_id]
        
        try:
            # Set API key in environment
            if api_key:
                os.environ['OPENROUTER_API_KEY'] = api_key
            
            # Emit start event
            self._emit_progress(case_id, 'analysis_started', {
                'message': 'Initializing ensemble analysis...',
                'progress': 0
            })
            
            # Initialize the improved pipeline with case_id
            pipeline = GeneralMedicalPipeline(case_id=case_id)
            
            # Configure models based on selection  
            if analysis_info['use_free_models'] or not api_key:
                # Set environment variable for free models
                os.environ['USE_FREE_MODELS'] = 'true'
                models = self._get_free_models()
                analysis_info['total_models'] = len(models)  # Update total count
                self._emit_progress(case_id, 'model_selection', {
                    'message': f'Using {len(models)} free models for analysis',
                    'model_count': len(models),
                    'progress': 8
                })
            elif analysis_info['selected_models']:
                # Use selected models
                models = self._get_selected_models(analysis_info['selected_models'])
                analysis_info['total_models'] = len(models)  # Update total count
                self._emit_progress(case_id, 'model_selection', {
                    'message': f'Using {len(models)} selected models',
                    'model_count': len(models),
                    'progress': 8
                })
            else:
                # Use all available models only if explicitly not using free models
                os.environ['USE_FREE_MODELS'] = 'false'
                models = None  # Will use default
                analysis_info['total_models'] = 31  # Default full set
            
            # Note: GeneralMedicalPipeline doesn't support progress callbacks
            # We'll update progress at key milestones instead
            
            # Run the improved pipeline analysis
            self._emit_progress(case_id, 'analysis_running', {
                'message': 'Querying AI models with improved pipeline...',
                'progress': 5
            })
            
            # Read the case file content
            with open(analysis_info['case_file'], 'r') as f:
                case_description = f.read()
            
            # Run the pipeline
            pipeline_results = pipeline.run_complete_analysis(
                case_description=case_description,
                case_title=analysis_info.get('title', case_id)
            )
            
            # Read the generated ensemble data from the file created by pipeline
            if pipeline_results.get('data_file'):
                with open(pipeline_results['data_file'], 'r') as f:
                    results = json.load(f)
            else:
                results = pipeline_results.get('consensus_results', {})
            
            # Save results
            self._emit_progress(case_id, 'processing_results', {
                'message': 'Processing consensus...',
                'progress': 90
            })
            
            # JSON file is already saved by pipeline, get the path
            json_file = Path(pipeline_results.get('data_file', ''))
            
            # Generate PDF report
            self._emit_progress(case_id, 'generating_report', {
                'message': 'Generating PDF report...',
                'progress': 95
            })
            
            # PDF report is already generated by the pipeline
            pdf_file = Path(pipeline_results.get('report_file', '')) if pipeline_results.get('report_file') else None
            
            # Update analysis info
            analysis_info['status'] = 'completed'
            analysis_info['progress'] = 100
            analysis_info['end_time'] = datetime.now().isoformat()
            analysis_info['json_file'] = str(json_file)
            analysis_info['pdf_file'] = str(pdf_file) if pdf_file else None
            analysis_info['results'] = {
                'primary_diagnosis': results.get('diagnostic_landscape', {}).get('primary_diagnosis', {}),
                'alternatives_count': len(results.get('diagnostic_landscape', {}).get('strong_alternatives', [])),
                'minority_count': len(results.get('diagnostic_landscape', {}).get('minority_opinions', [])),
                'models_responded': len([r for r in results.get('model_responses', []) if r.get('response')])
            }
            
            # Update database record
            if self.db_manager:
                try:
                    session = self.db_manager.get_session()
                    db_analysis = session.query(Analysis).filter_by(id=case_id).first()
                    if db_analysis:
                        db_analysis.status = 'completed'
                        db_analysis.completed_at = datetime.now()
                        db_analysis.duration_seconds = int((datetime.now() - db_analysis.started_at).total_seconds())
                        
                        # Extract primary diagnosis info
                        primary_diag = results.get('diagnostic_landscape', {}).get('primary_diagnosis', {})
                        db_analysis.primary_diagnosis = primary_diag.get('name', 'Unknown')
                        db_analysis.consensus_rate = primary_diag.get('agreement_percentage', 0.0)
                        
                        db_analysis.models_responded = analysis_info['completed_models']
                        db_analysis.models_failed = analysis_info['failed_models']
                        db_analysis.unique_diagnoses = analysis_info['results']['alternatives_count'] + analysis_info['results']['minority_count'] + 1
                        
                        db_analysis.json_file = str(json_file)
                        db_analysis.pdf_file = str(pdf_file) if pdf_file else None
                        
                        # Calculate actual cost (for free models it's 0)
                        db_analysis.actual_cost = 0.0 if analysis_info['use_free_models'] else analysis_info['completed_models'] * 0.002
                        
                        session.commit()
                    session.close()
                except Exception as e:
                    print(f"⚠️ Database completion update failed: {e}")
            
            # Add to predefined cases dynamically (temporary for session)
            self._register_custom_case(case_id, analysis_info)
            
            # Emit completion
            self._emit_progress(case_id, 'analysis_complete', {
                'message': 'Analysis complete!',
                'progress': 100,
                'case_id': case_id,
                'report_url': f'/case/{case_id}',
                'pdf_url': f'/api/case/{case_id}/pdf',
                'results': analysis_info['results']
            })
            
        except Exception as e:
            # Handle errors
            error_msg = str(e)
            traceback.print_exc()
            
            analysis_info['status'] = 'failed'
            analysis_info['error'] = error_msg
            analysis_info['end_time'] = datetime.now().isoformat()
            
            # Update database with error
            if self.db_manager:
                try:
                    session = self.db_manager.get_session()
                    db_analysis = session.query(Analysis).filter_by(id=case_id).first()
                    if db_analysis:
                        db_analysis.status = 'failed'
                        db_analysis.completed_at = datetime.now()
                        db_analysis.error_message = error_msg
                        if db_analysis.started_at:
                            db_analysis.duration_seconds = int((datetime.now() - db_analysis.started_at).total_seconds())
                        session.commit()
                    session.close()
                except Exception as db_error:
                    print(f"⚠️ Database error update failed: {db_error}")
            
            self._emit_progress(case_id, 'analysis_error', {
                'message': f'Analysis failed: {error_msg}',
                'error': error_msg,
                'progress': analysis_info.get('progress', 0)
            })
    
    def _emit_progress(self, case_id: str, event: str, data: Dict):
        """Emit progress update via WebSocket"""
        # Emit directly without context manager if in thread
        self.socketio.emit(event, {
            'analysis_id': case_id,
            **data
        }, room=f'analysis_{case_id}', namespace='/')
    
    def _get_free_models(self) -> List[Dict]:
        """Get list of free models (comprehensive list)"""
        return [
            # Google Models
            {"id": "google/gemini-2.0-flash-exp:free", "name": "Gemini 2.0 Flash", "origin": "USA"},
            {"id": "google/gemini-1.5-flash:free", "name": "Gemini 1.5 Flash", "origin": "USA"},
            {"id": "google/gemini-1.5-flash-8b:free", "name": "Gemini 1.5 Flash 8B", "origin": "USA"},
            
            # Meta Models
            {"id": "meta-llama/llama-3.2-3b-instruct:free", "name": "Llama 3.2 3B", "origin": "USA"},
            {"id": "meta-llama/llama-3.2-1b-instruct:free", "name": "Llama 3.2 1B", "origin": "USA"},
            {"id": "meta-llama/llama-3.1-8b-instruct:free", "name": "Llama 3.1 8B", "origin": "USA"},
            
            # Microsoft Models
            {"id": "microsoft/phi-3-mini-128k-instruct:free", "name": "Phi-3 Mini", "origin": "USA"},
            {"id": "microsoft/phi-3-medium-128k-instruct:free", "name": "Phi-3 Medium", "origin": "USA"},
            
            # Mistral Models
            {"id": "mistralai/mistral-7b-instruct:free", "name": "Mistral 7B", "origin": "France"},
            {"id": "mistralai/pixtral-12b:free", "name": "Pixtral 12B", "origin": "France"},
            
            # Chinese Models
            {"id": "qwen/qwen-2-7b-instruct:free", "name": "Qwen 2 7B", "origin": "China"},
            {"id": "qwen/qwen-2-vl-7b-instruct:free", "name": "Qwen 2 VL 7B", "origin": "China"},
            
            # Nous Research Models
            {"id": "nousresearch/hermes-3-llama-3.1-8b:free", "name": "Hermes 3 Llama", "origin": "USA"},
            
            # Other Open Source Models
            {"id": "liquid/lfm-40b:free", "name": "Liquid LFM 40B", "origin": "USA"},
            {"id": "thebloke/mythomax-l2-13b:free", "name": "MythoMax L2 13B", "origin": "Community"},
            {"id": "huggingfaceh4/zephyr-7b-beta:free", "name": "Zephyr 7B Beta", "origin": "Community"}
        ]
    
    def _get_selected_models(self, model_names: List[str]) -> List[Dict]:
        """Get selected models by name"""
        all_models = {
            "gpt-4o": {"id": "openai/gpt-4o", "name": "GPT-4o"},
            "claude-opus": {"id": "anthropic/claude-3-opus", "name": "Claude 3 Opus"},
            "gemini-pro": {"id": "google/gemini-pro-1.5", "name": "Gemini Pro 1.5"},
            "deepseek-v3": {"id": "deepseek/deepseek-chat", "name": "DeepSeek V3"},
            "mistral-large": {"id": "mistralai/mistral-large", "name": "Mistral Large"},
            # Add more models as needed
        }
        
        return [all_models[name] for name in model_names if name in all_models]
    
    def _get_model_origin(self, model_name: str) -> str:
        """Get model origin/country based on model name"""
        if 'google' in model_name or 'gemini' in model_name:
            return 'USA'
        elif 'meta-llama' in model_name or 'llama' in model_name:
            return 'USA'
        elif 'microsoft' in model_name or 'phi' in model_name:
            return 'USA'
        elif 'mistralai' in model_name or 'mistral' in model_name:
            return 'France'
        elif 'qwen' in model_name:
            return 'China'
        elif 'deepseek' in model_name:
            return 'China'
        elif 'openai' in model_name or 'gpt' in model_name:
            return 'USA'
        elif 'anthropic' in model_name or 'claude' in model_name:
            return 'USA'
        elif 'nousresearch' in model_name or 'hermes' in model_name:
            return 'USA'
        else:
            return 'Community'
    
    def _register_custom_case(self, case_id: str, analysis_info: Dict):
        """Register custom case for viewing"""
        # This would add the custom case to PREDEFINED_CASES temporarily
        # So it can be viewed at /case/{case_id}
        from web_app import PREDEFINED_CASES
        
        PREDEFINED_CASES[case_id] = {
            'id': case_id.replace('custom_', 'Custom_'),
            'title': analysis_info['title'],
            'file': Path(analysis_info['case_file']).name,
            'specialty': 'Custom Analysis',
            'complexity': 'Variable',
            'description': 'User-submitted case analysis',
            'custom': True,
            'analysis_time': analysis_info.get('end_time')
        }
    
    def get_analysis_status(self, case_id: str) -> Dict:
        """Get current status of an analysis"""
        if case_id not in self.active_analyses:
            return {'error': 'Analysis not found'}
        
        return self.active_analyses[case_id]
    
    def cancel_analysis(self, case_id: str) -> Dict:
        """Cancel an ongoing analysis"""
        if case_id not in self.active_analyses:
            return {'error': 'Analysis not found'}
        
        analysis_info = self.active_analyses[case_id]
        if analysis_info['status'] in ['completed', 'failed', 'cancelled']:
            return {'error': 'Analysis already finished'}
        
        analysis_info['status'] = 'cancelled'
        analysis_info['end_time'] = datetime.now().isoformat()
        
        self._emit_progress(case_id, 'analysis_cancelled', {
            'message': 'Analysis cancelled by user',
            'progress': analysis_info.get('progress', 0)
        })
        
        return {'status': 'cancelled'}
    
    def retry_failed_models(self, case_id: str) -> Dict:
        """Retry failed models in an analysis"""
        if case_id not in self.active_analyses:
            return {'error': 'Analysis not found'}
        
        analysis_info = self.active_analyses[case_id]
        if analysis_info['status'] != 'completed':
            return {'error': 'Analysis not completed'}
        
        # TODO: Implement retry logic for failed models
        return {'status': 'retry_started', 'failed_models': analysis_info['failed_models']}

# Global orchestrator instance (will be initialized in web_app.py)
web_orchestrator = None

def init_orchestrator(socketio, cache_dir, reports_dir, usecases_dir, db_manager=None):
    """Initialize the web orchestrator"""
    global web_orchestrator
    web_orchestrator = WebOrchestrator(socketio, cache_dir, reports_dir, usecases_dir, db_manager)
    return web_orchestrator