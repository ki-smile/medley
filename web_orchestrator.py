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
from utils.progress_manager import progress_manager, emit_progress, emit_model_started, emit_model_completed, emit_analysis_completed

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
        
        # Ensure directories exist (handle permission errors gracefully)
        try:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
        except PermissionError:
            print(f"Warning: Cannot create cache directory {self.cache_dir} - using existing directory")
        
        try:
            self.reports_dir.mkdir(parents=True, exist_ok=True)
        except PermissionError:
            print(f"Warning: Cannot create reports directory {self.reports_dir} - using existing directory")
        
        try:
            self.usecases_dir.mkdir(parents=True, exist_ok=True)
        except PermissionError:
            print(f"Warning: Cannot create usecases directory {self.usecases_dir} - using existing directory")
        
        try:
            self.custom_cases_dir.mkdir(parents=True, exist_ok=True)  # Create custom subfolder
        except PermissionError:
            print(f"Warning: Cannot create custom cases directory {self.custom_cases_dir} - using existing directory")
        
    def analyze_custom_case(
        self,
        case_text: str,
        case_title: str = None,
        use_free_models: bool = True,  # Default to free models per user instruction
        selected_models: List[str] = None,
        session_id: str = None,
        api_key: str = None,
        progress_session_id: str = None,
        enable_pdf: bool = True  # Enable PDF generation by default
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
            'progress_session_id': progress_session_id,  # Store progress session ID
            'completed_models': 0,
            'failed_models': 0,
            'start_time': datetime.now().isoformat(),
            'session_id': session_id,
            'progress_session_id': progress_session_id,  # Add progress session
            'case_file': str(case_file),
            'use_free_models': use_free_models,
            'selected_models': selected_models,
            'case_hash': hashlib.md5(case_text.encode()).hexdigest(),
            'current_cost': 0.0,
            'estimated_cost': 0.0,
            'cost_breakdown': [],
            'enable_pdf': enable_pdf  # Store PDF generation setting
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
            
            # Initialize the improved pipeline with case_id and socketio for real-time updates
            pipeline = GeneralMedicalPipeline(
                case_id=case_id,
                api_key=api_key,
                selected_models=analysis_info.get('selected_models'),
                socketio=self.socketio,
                display_case_id=case_id,
                progress_session_id=analysis_info.get('progress_session_id'),  # Pass progress session for long polling
                completion_callback=self._on_pipeline_complete,  # Add completion callback for immediate handover
                enable_pdf=analysis_info.get('enable_pdf', True)  # Pass PDF generation setting (default: enabled)
            )
            
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
            
            # Run the pipeline with callback-based completion
            print(f"🚀 Starting pipeline analysis for {case_id} with callback-based completion...")
            import threading
            import time
            
            def run_pipeline():
                try:
                    pipeline.run_complete_analysis(
                        case_description=case_description,
                        case_title=analysis_info.get('title', case_id)
                    )
                    print(f"✅ Pipeline thread completed for {case_id}")
                except Exception as e:
                    print(f"❌ Pipeline failed for {case_id}: {e}")
                    # Emit error event through callback
                    try:
                        self._emit_progress(case_id, 'analysis_error', {
                            'message': f'Analysis failed: {str(e)}',
                            'error': str(e),
                            'progress': analysis_info.get('progress', 0)
                        })
                    except Exception as error_emit_error:
                        print(f"⚠️ Failed to emit error event for {case_id}: {error_emit_error}")
            
            # Start pipeline in background thread - callback will handle completion
            pipeline_thread = threading.Thread(target=run_pipeline, name=f"Pipeline-{case_id}")
            pipeline_thread.daemon = True
            pipeline_thread.start()
            
            # Optional: Add fallback timeout as backup safety mechanism
            def fallback_timeout():
                time.sleep(300)  # 5 minutes
                if pipeline_thread.is_alive():
                    print(f"⏰ Pipeline still running after 5 minutes for {case_id} - but callback should have handled completion")
                    # Note: We rely on the callback for completion, this is just a warning
            
            fallback_thread = threading.Thread(target=fallback_timeout, name=f"Fallback-{case_id}")
            fallback_thread.daemon = True
            fallback_thread.start()
            
            # Add emergency timeout fallback in case completion callback fails
            def emergency_completion_check():
                """Check if analysis completed but callback failed, and emit completion event as fallback"""
                import time
                import glob
                time.sleep(90)  # Wait 90 seconds before checking
                if case_id in self.active_analyses:
                    analysis_info = self.active_analyses[case_id]
                    if analysis_info.get('status') != 'completed':
                        # Check if analysis files exist (indicating completion)
                        report_files = glob.glob(f"{self.reports_dir}/{case_id}_ensemble_data_*.json")
                        if report_files:
                            print(f"🚨 EMERGENCY: Analysis {case_id} completed but callback never triggered - forcing completion")
                            try:
                                # Force completion callback
                                results = {
                                    'data_file': report_files[0],
                                    'consensus_results': {},
                                    'total_models': 0
                                }
                                self._on_pipeline_complete(case_id, results)
                            except Exception as emergency_error:
                                print(f"❌ Emergency completion failed for {case_id}: {emergency_error}")
            
            # Start emergency fallback timer
            emergency_thread = threading.Thread(target=emergency_completion_check, daemon=True, name=f"Emergency-{case_id}")
            emergency_thread.start()

            # Return immediately - completion will be handled by callback
            print(f"🔄 Pipeline started in background for {case_id}, completion will be handled by callback")
            return
            
            # Read the generated ensemble data from the file created by pipeline
            if pipeline_results.get('data_file'):
                with open(pipeline_results['data_file'], 'r') as f:
                    results = json.load(f)
            else:
                results = pipeline_results.get('consensus_results', {})
            
            # Calculate actual costs from model responses
            self._calculate_final_costs(case_id, results)
            print(f"🐞 DEBUG: After _calculate_final_costs for {case_id}")
            
            # Critical: Ensure completion event is emitted even if post-processing fails
            completion_emitted = False
            
            try:
                # Fallback: If no costs were calculated but we expect them, add estimated costs
                if case_id in self.active_analyses:
                    current_cost = self.active_analyses[case_id].get('current_cost', 0.0)
                    if current_cost == 0.0 and not analysis_info.get('use_free_models', True):
                        print(f"💰 Fallback cost estimation for case {case_id} - no costs calculated but paid models expected")
                        # Apply estimated orchestrator costs based on typical usage
                        fallback_cost = 0.02  # Approximate cost based on observed usage patterns
                        self._update_cost(case_id, fallback_cost, "Orchestrator (estimated)")
                
                # The pipeline already handles all progress events and generates the report
                # We just need to get the paths from the results
                
                # JSON file is already saved by pipeline, get the path
                json_file = Path(pipeline_results.get('data_file', ''))
                
                # PDF report is already generated by the pipeline
                pdf_file = Path(pipeline_results.get('report_file', '')) if pipeline_results.get('report_file') else None
                
                print(f"🐞 DEBUG: Starting analysis info update for {case_id}")
                # Update analysis info
                analysis_info['status'] = 'completed'
                analysis_info['progress'] = 100
                analysis_info['end_time'] = datetime.now().isoformat()
                analysis_info['json_file'] = str(json_file)
                analysis_info['pdf_file'] = str(pdf_file) if pdf_file else None
                print(f"🐞 DEBUG: Analysis info updated, setting results for {case_id}")
                # Store full results for frontend
                diagnostic_landscape = results.get('diagnostic_landscape', {})
                print(f"🐞 DEBUG: Processing diagnostic landscape with keys: {list(diagnostic_landscape.keys()) if diagnostic_landscape else 'None'}")
                analysis_info['results'] = {
                    'primary_diagnoses': [diagnostic_landscape.get('primary_diagnosis', {})],
                    'alternative_diagnoses': diagnostic_landscape.get('strong_alternatives', []),
                    'minority_opinions': diagnostic_landscape.get('minority_opinions', []),
                    'model_responses': results.get('model_responses', []),
                    'models_responded': len([r for r in results.get('model_responses', []) if r.get('response')]),
                    'consensus_report': results.get('consensus_report', ''),
                    'bias_analysis': results.get('bias_analysis', {})
                }
            except Exception as processing_error:
                print(f"⚠️ Error in post-processing for {case_id}: {processing_error}")
                print(f"🔄 Continuing with minimal analysis info to ensure completion event")
                # Set minimal required fields for completion
                analysis_info['status'] = 'completed'
                analysis_info['progress'] = 100
                analysis_info['end_time'] = datetime.now().isoformat()
                # Try to set basic file paths from pipeline results
                try:
                    analysis_info['json_file'] = str(pipeline_results.get('data_file', ''))
                    analysis_info['pdf_file'] = str(pipeline_results.get('report_file', '')) if pipeline_results.get('report_file') else None
                except Exception:
                    print(f"⚠️ Could not extract file paths for {case_id}")
                    pass  # Continue without file paths
                # Set minimal results structure
                analysis_info['results'] = {
                    'primary_diagnoses': [],
                    'alternative_diagnoses': [],
                    'minority_opinions': [],
                    'model_responses': [],
                    'models_responded': 0,
                    'consensus_report': 'Analysis completed successfully. Please check the PDF report.',
                    'bias_analysis': {}
                }
            
            print(f"🐞 DEBUG: Results structure set, starting database update for {case_id}")
            
            # Update database record (non-blocking)
            try:
                if self.db_manager:
                    print(f"🐞 DEBUG: Database manager exists, updating database for {case_id}")
                    try:
                        session = self.db_manager.get_session()
                        db_analysis = session.query(Analysis).filter_by(id=case_id).first()
                        if db_analysis:
                            db_analysis.status = 'completed'
                            db_analysis.completed_at = datetime.now()
                            db_analysis.duration_seconds = int((datetime.now() - db_analysis.started_at).total_seconds())
                            
                            # Extract primary diagnosis info safely
                            try:
                                primary_diag = results.get('diagnostic_landscape', {}).get('primary_diagnosis', {})
                                db_analysis.primary_diagnosis = primary_diag.get('name', 'Unknown')
                                db_analysis.consensus_rate = round(primary_diag.get('agreement_percentage', 0.0), 1)
                            except Exception:
                                db_analysis.primary_diagnosis = 'Analysis Completed'
                                db_analysis.consensus_rate = 0.0
                            
                            db_analysis.models_responded = analysis_info.get('completed_models', 0)
                            db_analysis.models_failed = analysis_info.get('failed_models', 0)
                            
                            try:
                                db_analysis.unique_diagnoses = len(analysis_info['results']['alternative_diagnoses']) + len(analysis_info['results']['minority_opinions']) + 1
                            except Exception:
                                db_analysis.unique_diagnoses = 1
                            
                            db_analysis.json_file = analysis_info.get('json_file', '')
                            db_analysis.pdf_file = analysis_info.get('pdf_file', '')
                            
                            # Calculate actual cost (for free models it's 0)
                            db_analysis.actual_cost = 0.0 if analysis_info.get('use_free_models', True) else analysis_info.get('completed_models', 0) * 0.002
                            
                            session.commit()
                        session.close()
                    except Exception as e:
                        print(f"⚠️ Database completion update failed: {e}")
                else:
                    print(f"🐞 DEBUG: No database manager available for {case_id}")
            except Exception as db_error:
                print(f"⚠️ Database update section failed for {case_id}: {db_error}")
                # Continue to ensure completion event is emitted
            
            print(f"🐞 DEBUG: Database update complete, registering custom case for {case_id}")
            
            # Register custom case (non-blocking)
            try:
                self._register_custom_case(case_id, analysis_info)
                print(f"🐞 DEBUG: Custom case registered, preparing to emit completion for {case_id}")
            except Exception as reg_error:
                print(f"⚠️ Custom case registration failed for {case_id}: {reg_error}")
                # Continue to ensure completion event is emitted
            
            # Emit completion (with robust error handling)
            try:
                print(f"📤 Emitting analysis_complete event for {case_id}")
                print(f"   📄 HTML report: /case/{case_id}")
                print(f"   📊 PDF report: /api/case/{case_id}/pdf")
                
                # Ensure basic results structure exists
                if 'results' not in analysis_info:
                    analysis_info['results'] = {
                        'primary_diagnoses': [],
                        'alternative_diagnoses': [],
                        'minority_opinions': [],
                        'model_responses': [],
                        'models_responded': 0,
                        'consensus_report': '',
                        'bias_analysis': {}
                    }
                
                self._emit_progress(case_id, 'analysis_complete', {
                    'message': 'Analysis complete!',
                    'progress': 100,
                    'case_id': case_id,
                    'report_url': f'/case/{case_id}',
                    'pdf_url': f'/api/case/{case_id}/pdf',
                    'results': analysis_info['results']
                })
                print(f"✅ Analysis_complete event emitted for {case_id}")
            except Exception as completion_error:
                print(f"⚠️ Error emitting completion event for {case_id}: {completion_error}")
                # Emit a simplified completion event
                try:
                    self._emit_progress(case_id, 'analysis_complete', {
                        'message': 'Analysis complete!',
                        'progress': 100,
                        'case_id': case_id,
                        'report_url': f'/case/{case_id}',
                        'pdf_url': f'/api/case/{case_id}/pdf'
                    })
                    print(f"✅ Simplified analysis_complete event emitted for {case_id}")
                except Exception as final_error:
                    print(f"❌ Failed to emit any completion event for {case_id}: {final_error}")
            
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
    
    def _on_pipeline_complete(self, case_id: str, pipeline_results: dict):
        """
        Callback method called when pipeline analysis completes
        This ensures immediate handover and completion event emission
        """
        print(f"🔗 Pipeline completion callback triggered for {case_id}")
        print(f"🔍 Pipeline results keys: {list(pipeline_results.keys())}")
        
        try:
            analysis_info = self.active_analyses.get(case_id, {})
            print(f"🔍 Analysis info available: {bool(analysis_info)}")
            print(f"🔍 Analysis info progress_session_id: {analysis_info.get('progress_session_id', 'MISSING')}")
            
            # Read the generated ensemble data from the file created by pipeline
            if pipeline_results.get('data_file'):
                with open(pipeline_results['data_file'], 'r') as f:
                    results = json.load(f)
            else:
                results = pipeline_results.get('consensus_results', {})
            
            # Calculate actual costs from model responses (with error protection)
            try:
                self._calculate_final_costs(case_id, results)
                print(f"✅ Cost calculation completed for {case_id}")
            except Exception as cost_error:
                print(f"⚠️ Cost calculation failed for {case_id}: {cost_error}")
                traceback.print_exc()
            
            # CRITICAL: Emit completion event IMMEDIATELY after cost calculation
            # This ensures the frontend gets the completion event even if subsequent processing fails
            print(f"🚨 CRITICAL: Emitting analysis_complete event immediately after cost calculation for {case_id}")
            try:
                self._emit_progress(case_id, 'analysis_complete', {
                    'message': 'Analysis complete! Reports are ready.',
                    'progress': 100,
                    'case_id': case_id,
                    'report_url': f'/case/{case_id}',
                    'pdf_url': f'/api/case/{case_id}/pdf',
                    'results': results  # Use the basic results we have here
                })
                print(f"✅ CRITICAL: Analysis_complete event emitted successfully for {case_id}")
            except Exception as critical_emit_error:
                print(f"❌ CRITICAL: Failed to emit analysis_complete event for {case_id}: {critical_emit_error}")
                traceback.print_exc()
            
            # Update analysis info
            analysis_info['status'] = 'completed'
            analysis_info['progress'] = 100
            analysis_info['end_time'] = datetime.now().isoformat()
            analysis_info['json_file'] = str(pipeline_results.get('data_file', ''))
            analysis_info['pdf_file'] = str(pipeline_results.get('report_file', '')) if pipeline_results.get('report_file') else None
            
            # Store full results for frontend
            diagnostic_landscape = results.get('diagnostic_landscape', {})
            analysis_info['results'] = {
                'primary_diagnoses': [diagnostic_landscape.get('primary_diagnosis', {})],
                'alternative_diagnoses': diagnostic_landscape.get('strong_alternatives', []),
                'minority_opinions': diagnostic_landscape.get('minority_opinions', []),
                'model_responses': results.get('model_responses', []),
                'models_responded': len([r for r in results.get('model_responses', []) if r.get('response')]),
                'consensus_report': results.get('consensus_report', ''),
                'bias_analysis': results.get('bias_analysis', {})
            }
            
            # Update database record (non-blocking)
            try:
                if self.db_manager:
                    session = self.db_manager.get_session()
                    db_analysis = session.query(Analysis).filter_by(id=case_id).first()
                    if db_analysis:
                        db_analysis.status = 'completed'
                        db_analysis.progress = 100
                        db_analysis.end_time = datetime.now()
                        
                        if diagnostic_landscape.get('primary_diagnosis'):
                            db_analysis.primary_diagnosis = diagnostic_landscape['primary_diagnosis'].get('name', 'Unknown')
                            db_analysis.consensus_rate = diagnostic_landscape['primary_diagnosis'].get('consensus_rate', 0.0)
                        
                        db_analysis.models_responded = analysis_info.get('completed_models', 0)
                        db_analysis.models_failed = analysis_info.get('failed_models', 0)
                        db_analysis.unique_diagnoses = len(analysis_info['results']['alternative_diagnoses']) + len(analysis_info['results']['minority_opinions']) + 1
                        db_analysis.json_file = analysis_info.get('json_file', '')
                        db_analysis.pdf_file = analysis_info.get('pdf_file', '')
                        db_analysis.actual_cost = 0.0 if analysis_info.get('use_free_models', True) else analysis_info.get('completed_models', 0) * 0.002
                        
                        session.commit()
                    session.close()
            except Exception as db_error:
                print(f"⚠️ Database update failed in callback for {case_id}: {db_error}")
            
            # Register custom case (non-blocking) - skip if this causes issues
            print(f"🔍 DEBUG: About to register custom case for {case_id}")
            try:
                self._register_custom_case(case_id, analysis_info)
                print(f"✅ DEBUG: Custom case registration completed for {case_id}")
            except Exception as reg_error:
                print(f"⚠️ Custom case registration failed in callback for {case_id}: {reg_error}")
                print(f"🔍 Continuing with completion event emission despite registration failure...")
            
            # Emit completion event immediately - CRITICAL STEP
            print(f"📤 DEBUG: About to emit analysis_complete event via callback for {case_id}")
            print(f"🔍 Progress session ID for emission: {analysis_info.get('progress_session_id', 'MISSING')}")
            
            try:
                print(f"🔍 DEBUG: Calling _emit_progress for analysis_complete event...")
                self._emit_progress(case_id, 'analysis_complete', {
                    'message': 'Analysis complete! Reports are ready.',
                    'progress': 100,
                    'case_id': case_id,
                    'report_url': f'/case/{case_id}',
                    'pdf_url': f'/api/case/{case_id}/pdf',
                    'results': analysis_info['results']
                })
                print(f"✅ Analysis_complete event emitted successfully via callback for {case_id}")
            except Exception as emit_error:
                print(f"❌ Failed to emit analysis_complete event for {case_id}: {emit_error}")
                traceback.print_exc()
            
        except Exception as callback_error:
            print(f"⚠️ Error in pipeline completion callback for {case_id}: {callback_error}")
            traceback.print_exc()
            # Emit a simplified completion event as fallback
            try:
                self._emit_progress(case_id, 'analysis_complete', {
                    'message': 'Analysis complete! Reports are ready.',
                    'progress': 100,
                    'case_id': case_id,
                    'report_url': f'/case/{case_id}',
                    'pdf_url': f'/api/case/{case_id}/pdf'
                })
                print(f"✅ Fallback analysis_complete event emitted via callback for {case_id}")
            except Exception as final_error:
                print(f"❌ Failed to emit any completion event via callback for {case_id}: {final_error}")
    
    def _emit_progress(self, case_id: str, event: str, data: Dict):
        """Emit progress update via Long Polling Progress Manager"""
        print(f"🔍 _emit_progress called: case_id={case_id}, event={event}")
        
        # Include cost information in progress updates
        analysis_info = self.active_analyses.get(case_id, {})
        cost_data = {
            'current_cost': analysis_info.get('current_cost', 0.0),
            'estimated_cost': analysis_info.get('estimated_cost', 0.0),
            'use_free_models': analysis_info.get('use_free_models', True)
        }
        
        # Get progress session ID
        progress_session_id = analysis_info.get('progress_session_id')
        print(f"🔍 Progress session ID for emit: {progress_session_id}")
        
        # Emit to progress manager if we have a progress session
        if progress_session_id:
            print(f"🔍 Calling emit_progress with session_id={progress_session_id}")
            try:
                emit_progress(progress_session_id, event, {
                    'analysis_id': case_id,
                    **data,
                    **cost_data
                })
                print(f"✅ emit_progress completed successfully for {case_id}")
            except Exception as progress_emit_error:
                print(f"❌ emit_progress failed for {case_id}: {progress_emit_error}")
                traceback.print_exc()
        else:
            print(f"⚠️ No progress_session_id available for {case_id}, skipping progress emission")
        
        # Also emit via Socket.IO for backward compatibility during transition
        try:
            print(f"🔍 Calling socketio.emit for {case_id}")
            self.socketio.emit(event, {
                'analysis_id': case_id,
                **data,
                **cost_data
            }, room=f'analysis_{case_id}', namespace='/')
            print(f"✅ socketio.emit completed successfully for {case_id}")
        except Exception as socketio_emit_error:
            print(f"❌ socketio.emit failed for {case_id}: {socketio_emit_error}")
            traceback.print_exc()
    
    def _update_cost(self, case_id: str, model_cost: float, model_name: str = None):
        """Update the running cost for an analysis"""
        print(f"💰 _update_cost called: case_id={case_id}, cost=${model_cost:.4f}, model={model_name}")
        
        if case_id not in self.active_analyses:
            print(f"💰 Case {case_id} not in active analyses, skipping cost update")
            return
        
        analysis_info = self.active_analyses[case_id]
        analysis_info['current_cost'] += model_cost
        analysis_info['current_cost'] = round(analysis_info['current_cost'], 2)  # Keep total rounded
        
        print(f"💰 Updated total cost to: ${analysis_info['current_cost']:.2f}")
        
        if model_name and model_cost > 0:
            analysis_info['cost_breakdown'].append({
                'model': model_name,
                'cost': round(model_cost, 2),
                'timestamp': datetime.now().isoformat()
            })
        
        # Emit cost update event
        print(f"💰 Emitting cost_update WebSocket event")
        self._emit_progress(case_id, 'cost_update', {
            'message': f'Cost updated: ${analysis_info["current_cost"]:.2f}' if model_cost > 0 else 'Free models - no cost',
            'model_cost': round(model_cost, 2),
            'model_name': model_name
        })
    
    def _calculate_final_costs(self, case_id: str, results: Dict):
        """Calculate final costs from the analysis results"""
        print(f"💰 _calculate_final_costs called for case {case_id}")
        print(f"💰 Results type: {type(results)}")
        if isinstance(results, dict):
            print(f"💰 Results keys: {list(results.keys())}")
        
        if case_id not in self.active_analyses:
            print(f"💰 Case {case_id} not in active analyses")
            return
        
        analysis_info = self.active_analyses[case_id]
        print(f"💰 Analysis uses free models: {analysis_info.get('use_free_models', True)}")
        
        # Check if analysis used an orchestrator (indicates potential costs)
        orchestrator_used = False
        orchestrator_cost = 0.0
        
        # Look for orchestrator usage indicators in results metadata
        print(f"💰 Looking for orchestrator metadata in results...")
        if isinstance(results, dict):
            # Check both 'metadata' and nested 'generation_metadata.metadata'
            metadata_sources = []
            if 'metadata' in results:
                metadata_sources.append(results['metadata'])
                print(f"💰 Found 'metadata' in results")
            if 'generation_metadata' in results and isinstance(results['generation_metadata'], dict):
                if 'metadata' in results['generation_metadata']:
                    metadata_sources.append(results['generation_metadata']['metadata'])
                    print(f"💰 Found 'generation_metadata.metadata' in results")
            
            print(f"💰 Found {len(metadata_sources)} metadata sources")
            
            for i, metadata in enumerate(metadata_sources):
                print(f"💰 Checking metadata source {i+1}: {type(metadata)}")
                if isinstance(metadata, dict):
                    print(f"💰 Metadata keys: {list(metadata.keys())}")
                    if 'orchestrator_model' in metadata:
                        orchestrator_model = metadata.get('orchestrator_model', '')
                        print(f"💰 Found orchestrator_model: {orchestrator_model}")
                        if orchestrator_model and orchestrator_model != 'none':
                            orchestrator_used = True
                            # Even if marked as free, orchestration often incurs costs
                            # from preparatory queries or fallback models
                            if ':free' in orchestrator_model.lower():
                                orchestrator_cost = 0.005  # Minimal cost for free orchestrator setup
                                print(f"💰 Free orchestrator detected, cost: ${orchestrator_cost}")
                            else:
                                orchestrator_cost = 0.018  # Full orchestrator cost
                                print(f"💰 Paid orchestrator detected, cost: ${orchestrator_cost}")
        else:
            print(f"💰 Results is not a dictionary")
        
        # Check for free models usage
        using_free_models = analysis_info.get('use_free_models', True)
        
        # If using free models but orchestrator was used, there are still costs
        if using_free_models and not orchestrator_used:
            self._update_cost(case_id, 0.0, "Free models")
            return
        elif using_free_models and orchestrator_used:
            # Free models but with paid orchestrator
            self._update_cost(case_id, orchestrator_cost, "Free models + Orchestrator")
            return
        
        total_cost = 0.0
        
        # Try to extract cost information from results
        if 'responses' in results:
            for model_id, response_data in results['responses'].items():
                model_cost = 0.0
                
                if isinstance(response_data, dict):
                    # Check for actual cost from API
                    model_cost = response_data.get('actual_cost', 0.0)
                    
                    # If no actual cost, estimate from tokens
                    if model_cost == 0.0:
                        model_cost = response_data.get('estimated_cost', 0.0)
                    
                    # If still no cost, use fallback estimation
                    if model_cost == 0.0:
                        tokens = response_data.get('tokens_used', response_data.get('total_tokens', 0))
                        model_cost = tokens * 0.0001  # Rough estimate: $0.0001 per token
                
                if model_cost > 0:
                    total_cost += model_cost
                    self._update_cost(case_id, model_cost, model_id)
        
        # Add orchestrator cost if applicable
        if orchestrator_used and orchestrator_cost > 0:
            total_cost += orchestrator_cost
            self._update_cost(case_id, orchestrator_cost, "Orchestrator")
        
        # If no individual model costs found but not using free models, estimate
        if total_cost == 0.0 and not using_free_models:
            completed_models = analysis_info.get('completed_models', 1)
            estimated_total = completed_models * 0.01  # $0.01 per model as rough estimate
            if orchestrator_used:
                estimated_total += orchestrator_cost
            self._update_cost(case_id, estimated_total, f"{completed_models} models (estimated)")
    
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