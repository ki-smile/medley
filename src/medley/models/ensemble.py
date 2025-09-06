"""
Ensemble Orchestrator for coordinating multiple model queries
"""

import asyncio
import json
from typing import List, Dict, Any, Optional
from pathlib import Path
from datetime import datetime

from ..models.llm_manager import LLMManager
from ..models.consensus import ConsensusEngine, ConsensusResult
from ..processors.case_processor import CaseProcessor
from ..processors.response_parser import ResponseParser
from ..processors.cache_manager import CacheManager
from ..processors.prompt_generator import DiagnosticPromptGenerator
from ..utils.config import Config

class EnsembleOrchestrator:
    """Orchestrates multiple LLM queries for ensemble analysis"""
    
    def __init__(self, config: Optional[Config] = None):
        """Initialize the ensemble orchestrator"""
        self.config = config or Config()
        self.llm_manager = LLMManager(self.config)
        self.case_processor = CaseProcessor()
        self.response_parser = ResponseParser()
        self.cache_manager = CacheManager(self.config.cache_dir)
        self.consensus_engine = ConsensusEngine(config=self.config)
        self.prompt_generator = DiagnosticPromptGenerator()
        
        # Default ensemble models - mix of free and paid for diversity
        # Organized by priority: free tier first, then must-have models, then optional
        self.default_models = [
            # Free models (always include at least 5)
            {"name": "mistralai/mistral-7b-instruct:free", "origin": "France", "size": "7B", "cost": "free"},
            {"name": "google/gemma-2-9b-it:free", "origin": "USA", "size": "9B", "cost": "free"},
            {"name": "meta-llama/llama-3.2-3b-instruct:free", "origin": "USA", "size": "3B", "cost": "free"},
            {"name": "qwen/qwen-2.5-coder-32b-instruct", "origin": "China", "size": "32B", "cost": "free"},
            {"name": "google/gemini-2.0-flash-exp:free", "origin": "USA", "size": "Unknown", "cost": "free"},  # Free Gemini
            {"name": "deepseek/deepseek-chat-v3-0324:free", "origin": "China", "size": "Unknown", "cost": "free"},  # DeepSeek V3 free
            {"name": "nousresearch/hermes-3-llama-3.1-8b:free", "origin": "USA", "size": "8B", "cost": "free"},
            {"name": "liquid/lfm-40b:free", "origin": "USA", "size": "40B", "cost": "free"},
            
            # Must-have premium models (always try with retries) - User specified exact model IDs
            {"name": "openai/gpt-5", "origin": "USA", "size": "Unknown", "cost": "$5/$15 per 1M", "priority": "high"},  # GPT-5
            {"name": "mistralai/mistral-small-3.2-24b-instruct", "origin": "France", "size": "24B", "cost": "$0.10/$0.30 per 1M", "priority": "high"},  # Mistral Small 3.2
            {"name": "google/gemma-3-27b-it", "origin": "USA", "size": "27B", "cost": "$0.20/$0.60 per 1M", "priority": "high"},  # Gemma 3 27B
            {"name": "anthropic/claude-opus-4.1", "origin": "USA", "size": "Unknown", "cost": "$15/$75 per 1M", "priority": "high"},  # Claude Opus 4.1
            {"name": "anthropic/claude-sonnet-4", "origin": "USA", "size": "Unknown", "cost": "$3/$15 per 1M", "priority": "high"},  # Claude Sonnet 4
            {"name": "google/gemini-2.5-pro", "origin": "USA", "size": "Unknown", "cost": "$3.50/$10.50 per 1M", "priority": "high"},  # Gemini 2.5 Pro
            {"name": "google/gemini-2.5-flash", "origin": "USA", "size": "Unknown", "cost": "$0.075/$0.30 per 1M", "priority": "high"},  # Gemini 2.5 Flash
            {"name": "x-ai/grok-4", "origin": "USA", "size": "Unknown", "cost": "$5/$15 per 1M", "priority": "high"},  # Grok 4
            
            # Additional premium models
            {"name": "x-ai/grok-2-1212", "origin": "USA", "size": "Unknown", "cost": "$2/$10 per 1M"},  # Grok 4
            {"name": "deepseek/deepseek-r1", "origin": "China", "size": "Unknown", "cost": "$0.55/$2.19 per 1M"},  # DeepSeek R1
            {"name": "mistralai/mistral-large", "origin": "France", "size": "123B", "cost": "$2/$6 per 1M"},  # Mistral Large
            
            # Affordable paid models (diverse origins) - as fallback
            {"name": "anthropic/claude-3-haiku", "origin": "USA", "size": "Unknown", "cost": "$0.25/$1.25 per 1M"},
            {"name": "openai/gpt-4o-mini", "origin": "USA", "size": "Unknown", "cost": "$0.15/$0.60 per 1M"},
            {"name": "mistralai/mistral-small", "origin": "France", "size": "22B", "cost": "$0.20/$0.60 per 1M"},
            {"name": "deepseek/deepseek-chat", "origin": "China", "size": "67B", "cost": "$0.14/$0.28 per 1M"},
            {"name": "google/gemini-flash-1.5", "origin": "USA", "size": "Unknown", "cost": "$0.075/$0.30 per 1M"},
            {"name": "perplexity/llama-3.1-sonar-small-128k-online", "origin": "USA", "size": "8B", "cost": "$0.20/$0.20 per 1M"},
            {"name": "cohere/command-r", "origin": "Canada", "size": "35B", "cost": "$0.15/$0.60 per 1M"},
        ]
        
        # Models for AI-enhanced consensus analysis
        self.consensus_models = [
            "google/gemini-2.5-pro",  # Primary choice for consensus
            "anthropic/claude-opus-4.1",  # Fallback 1
            "openai/gpt-5",  # Fallback 2
            "google/gemini-2.5-flash",  # Fallback 3
        ]
        
        # High-priority models that always get retries
        self.high_priority_names = [
            "openai/gpt-5",
            "mistralai/mistral-small-3.2-24b-instruct",
            "google/gemma-3-27b-it",
            "anthropic/claude-opus-4.1",
            "anthropic/claude-sonnet-4",
            "google/gemini-2.5-pro",
            "google/gemini-2.5-flash",
            "x-ai/grok-4",
            "deepseek/deepseek-chat-v3-0324",
        ]
        
        # Minimum models required for ensemble
        self.min_models = 3
    
    def run_ensemble_analysis(
        self,
        case_file: str,
        models: Optional[List[Dict[str, str]]] = None,
        output_dir: Optional[str] = None,
        use_paid_models: bool = True,
        max_paid_models: int = 3,
        consensus_mode: str = "statistical",  # "statistical" or "ai-enhanced"
        progress_callback: Optional[callable] = None
    ) -> Dict[str, Any]:
        """
        Run ensemble analysis on a medical case
        
        Args:
            case_file: Path to the case file
            models: List of model configurations (uses defaults if None)
            output_dir: Directory to save results (optional)
            use_paid_models: Whether to include paid models (default True)
            max_paid_models: Maximum number of paid models to use (default 3)
            
        Returns:
            Dictionary containing ensemble analysis results
        """
        # Select models to use
        models_to_use = self._select_models(models, use_paid_models, max_paid_models)
        
        # Load and process the case
        case = self.case_processor.load_case_from_file(Path(case_file))
        
        # Create prompt using the standardized prompt generator
        case_content = case.to_prompt()
        prompt = self.prompt_generator.generate_diagnostic_prompt(case_content)
        
        # Validate minimum models
        if len(models_to_use) < self.min_models:
            print(f"⚠️ Warning: Only {len(models_to_use)} models available. Minimum {self.min_models} required.")
            print("Attempting to add more models...")
            models_to_use = self._ensure_minimum_models(models_to_use)
        
        # Query all models
        print(f"\n🔄 Querying {len(models_to_use)} models for ensemble analysis...")
        print(f"   Free models: {sum(1 for m in models_to_use if m.get('cost') == 'free')}")
        print(f"   Paid models: {sum(1 for m in models_to_use if m.get('cost') != 'free')}")
        
        model_responses = []
        parsed_responses = []
        successful_count = 0
        failed_high_priority = []  # Track failed high-priority models for retry
        
        # First pass - try all models once
        for i, model_config in enumerate(models_to_use, 1):
            model_name = model_config["name"]
            origin = model_config.get("origin", "Unknown")
            size = model_config.get("size", "Unknown")
            
            print(f"\n[{i}/{len(models_to_use)}] Querying {model_name} ({origin}, {size})...")
            
            # Call progress callback if provided
            if progress_callback:
                progress_callback(
                    model_name=model_name,
                    status='processing',
                    response=None
                )
            
            # Check cache first
            cached_response = self.cache_manager.get_cached_response(
                case_id=case.case_id,
                model_id=model_name,
                prompt=prompt
            )
            
            llm_response_obj = None  # Track the full LLMResponse object
            
            if cached_response and cached_response.content:
                print(f"  ✓ Using cached response")
                response = cached_response.content
                error = None
                llm_response_obj = cached_response  # Use cached response object
                successful_count += 1
                
                # Call progress callback for cached response
                if progress_callback:
                    try:
                        parsed = json.loads(response) if isinstance(response, str) else response
                        progress_callback(
                            model_name=model_name,
                            status='completed',
                            response=parsed
                        )
                    except:
                        progress_callback(
                            model_name=model_name,
                            status='completed',
                            response={'raw': response}
                        )
            else:
                # Initial attempt (no retry yet)
                is_high_priority = model_config.get("priority") == "high" or model_name in self.high_priority_names
                
                response = None
                error = None
                
                try:
                    # Get model config
                    from medley.utils.config import ModelConfig
                    model_cfg = self.config.get_model(model_name.split("/")[0]) or \
                                   ModelConfig(
                                       name=model_name,
                                       model_id=model_name,
                                       provider="openrouter",
                                       origin=origin,
                                       size=size
                                   )
                    
                    llm_response = self.llm_manager.query_model(model_cfg, prompt)
                    
                    if llm_response.error:
                        error = llm_response.error
                        print(f"  ✗ Error: {error}")
                        if is_high_priority:
                            # Track for later retry
                            failed_high_priority.append({
                                "model_config": model_config,
                                "index": i - 1  # Store the index for later update
                            })
                        # Call progress callback for failed model
                        if progress_callback:
                            progress_callback(
                                model_name=model_name,
                                status='failed',
                                response=None
                            )
                    else:
                        response = llm_response.content
                        error = None
                        llm_response_obj = llm_response  # Store the full response object
                        # Cache successful response
                        self.cache_manager.save_response(
                            case_id=case.case_id,
                            model_id=model_name,
                            prompt=prompt,
                            response=llm_response
                        )
                        print(f"  ✓ Response received and cached")
                        successful_count += 1
                        # Call progress callback for successful model
                        if progress_callback:
                            try:
                                parsed = json.loads(response) if isinstance(response, str) else response
                                progress_callback(
                                    model_name=model_name,
                                    status='completed',
                                    response=parsed
                                )
                            except:
                                progress_callback(
                                    model_name=model_name,
                                    status='completed',
                                    response={'raw': response}
                                )
                except Exception as e:
                    error = str(e)
                    print(f"  ✗ Error: {error}")
                    if is_high_priority:
                        failed_high_priority.append({
                            "model_config": model_config,
                            "index": i - 1
                        })
                    # Call progress callback for exception
                    if progress_callback:
                        progress_callback(
                            model_name=model_name,
                            status='failed',
                            response=None
                        )
            
            # Store response with metadata including token information
            response_data = {
                "model_name": model_name,
                "origin": origin,
                "size": size,
                "response": response,
                "error": error,
                "timestamp": datetime.now().isoformat(),
                "tokens_used": 0,
                "input_tokens": 0,
                "output_tokens": 0
            }
            
            # Add token information if available
            if llm_response_obj and not error:
                response_data.update({
                    "tokens_used": llm_response_obj.tokens_used,
                    "input_tokens": llm_response_obj.input_tokens,
                    "output_tokens": llm_response_obj.output_tokens,
                    "latency": llm_response_obj.latency
                })
            
            model_responses.append(response_data)
            
            # Parse response if successful
            if response and not error:
                # Try JSON parsing first, fallback to text parsing
                try:
                    parsed = self.prompt_generator.parse_response(response, format_type="json")
                except:
                    # Fallback to original response parser for non-JSON responses
                    parsed = self.response_parser.parse_response(response)
                parsed_responses.append(parsed)
            else:
                parsed_responses.append(None)
        
        # Retry failed high-priority models
        if failed_high_priority:
            print(f"\n🔄 Retrying {len(failed_high_priority)} failed high-priority models...")
            import time
            
            for retry_attempt in range(1, 5):  # 4 more attempts (5 total)
                if not failed_high_priority:
                    break
                
                print(f"\n  Retry round {retry_attempt}/4 (waiting 30 seconds)...")
                time.sleep(30)
                
                still_failed = []
                for failed_item in failed_high_priority:
                    model_config = failed_item["model_config"]
                    idx = failed_item["index"]
                    model_name = model_config["name"]
                    origin = model_config.get("origin", "Unknown")
                    size = model_config.get("size", "Unknown")
                    
                    print(f"  🔄 Retrying {model_name}...")
                    
                    try:
                        from medley.utils.config import ModelConfig
                        model_cfg = self.config.get_model(model_name.split("/")[0]) or \
                                       ModelConfig(
                                           name=model_name,
                                           model_id=model_name,
                                           provider="openrouter",
                                           origin=origin,
                                           size=size
                                       )
                        
                        llm_response = self.llm_manager.query_model(model_cfg, prompt)
                        
                        if llm_response.error:
                            print(f"    ✗ Still failing: {llm_response.error}")
                            still_failed.append(failed_item)
                        else:
                            # Success!
                            response = llm_response.content
                            # Update the original response with token information
                            model_responses[idx]["response"] = response
                            model_responses[idx]["error"] = None
                            model_responses[idx]["tokens_used"] = llm_response.tokens_used
                            model_responses[idx]["input_tokens"] = llm_response.input_tokens
                            model_responses[idx]["output_tokens"] = llm_response.output_tokens
                            model_responses[idx]["latency"] = llm_response.latency
                            
                            # Parse and update
                            try:
                                parsed = self.prompt_generator.parse_response(response, format_type="json")
                            except:
                                parsed = self.response_parser.parse_response(response)
                            parsed_responses[idx] = parsed
                            
                            # Cache successful response
                            self.cache_manager.save_response(
                                case_id=case.case_id,
                                model_id=model_name,
                                prompt=prompt,
                                response=llm_response
                            )
                            print(f"    ✓ Success on retry!")
                            successful_count += 1
                    except Exception as e:
                        print(f"    ✗ Error: {str(e)}")
                        still_failed.append(failed_item)
                
                failed_high_priority = still_failed
        
        # Check if we have minimum successful responses
        print(f"\n✅ Successfully queried {successful_count}/{len(models_to_use)} models")
        
        if successful_count < self.min_models:
            print(f"⚠️ Warning: Only {successful_count} successful responses. Minimum {self.min_models} recommended.")
            if successful_count == 0:
                raise ValueError("No models responded successfully. Cannot perform ensemble analysis.")
            elif successful_count == 1:
                print("⚠️ Warning: Only 1 model responded. Results will not show ensemble benefits.")
            else:
                print(f"⚠️ Proceeding with {successful_count} models, but results may be limited.")
        
        # Analyze consensus
        print(f"\n📊 Analyzing consensus across models (mode: {consensus_mode})...")
        
        if consensus_mode == "ai-enhanced":
            # Use AI-enhanced consensus
            print("  🤖 Using AI model for enhanced consensus analysis...")
            
            # Select appropriate orchestrator model based on availability
            if use_paid_models:
                # Priority order for paid orchestrator models
                orchestrator_models = [
                    "anthropic/claude-3.5-sonnet",  # Claude Sonnet 3.5
                    "anthropic/claude-opus-4.1",     # Claude Opus 4.1
                    "google/gemini-2.5-pro",          # Gemini 2.5 Pro
                    "google/gemini-pro-1.5"           # Gemini Pro 1.5 (fallback)
                ]
                print("  💎 Attempting to use premium orchestrator models...")
            else:
                # Priority order for free orchestrator models (based on testing results)
                # Ranked by cost-effectiveness, reliability, and output quality
                orchestrator_models = [
                    "qwen/qwen-2.5-coder-32b-instruct",    # #1 RECOMMENDED - Best cost ($0.0075), reliable output
                    "openai/gpt-oss-20b:free",             # #2 Very good - Low cost ($0.0076), comprehensive analysis  
                    "deepseek/deepseek-chat-v3.1:free",    # #3 Good option - Free model with decent quality
                    "google/gemma-3-27b-it:free",          # #4 Fallback - Basic orchestration capability
                    # Avoid using these for orchestration due to poor output quality:
                    # "mistralai/mistral-7b-instruct:free",  # Often wrong diagnosis
                    # "google/gemini-2.0-flash-exp:free"     # Malformed output
                ]
                print("  🆓 Using free orchestrator models...")
                print("  ⚠️  Note: Free models provide limited orchestration quality compared to premium models")
            
            # Try each model in priority order until one works
            consensus_result = None
            for orchestrator_model in orchestrator_models:
                try:
                    print(f"  🔄 Trying orchestrator model: {orchestrator_model}")
                    consensus_result = self.consensus_engine.analyze_consensus_with_ai(
                        model_responses,
                        parsed_responses,
                        case_info={
                            "patient_info": case.patient_info,
                            "presentation": case.presentation,
                            "symptoms": case.symptoms if hasattr(case, 'symptoms') else []
                        },
                        consensus_model=orchestrator_model
                    )
                    print(f"  ✅ Successfully used {orchestrator_model} for orchestration")
                    break
                except Exception as e:
                    print(f"  ⚠️ Failed to use {orchestrator_model}: {str(e)}")
                    continue
            
            # Fallback to statistical if all AI models fail
            if not consensus_result:
                print("  ⚠️ All AI orchestrator models failed, falling back to statistical consensus")
                consensus_result = self.consensus_engine.analyze_consensus(
                    model_responses,
                    parsed_responses
                )
        else:
            # Use statistical consensus
            consensus_result = self.consensus_engine.analyze_consensus(
                model_responses,
                parsed_responses
            )
        
        # Prepare ensemble results
        # Convert parsed_responses to dicts for JSON serialization
        parsed_responses_dict = []
        for parsed in parsed_responses:
            if parsed:
                parsed_responses_dict.append(parsed.to_dict() if hasattr(parsed, 'to_dict') else parsed)
            else:
                parsed_responses_dict.append(None)
        
        # Helper function to clean markdown formatting
        def clean_markdown(text):
            if not text:
                return text
            # Remove markdown headers (##, ###, etc.)
            import re
            text = re.sub(r'^#{1,6}\s+', '', text, flags=re.MULTILINE)
            # Remove bold markers (**)
            text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)
            # Remove italic markers (*)
            text = re.sub(r'\*([^*]+)\*', r'\1', text)
            # Clean up extra whitespace
            text = re.sub(r'\n{3,}', '\n\n', text)
            return text.strip()
        
        # Prepare case description (all case details except bias testing target)
        case_description = {
            "case_id": case.case_id,
            "title": clean_markdown(case.title) if case.title else case.title,
            "patient_info": clean_markdown(case.patient_info) if case.patient_info else case.patient_info,
            "presentation": clean_markdown(case.presentation) if case.presentation else case.presentation,
            "symptoms": case.symptoms,  # List, no cleaning needed
            "history": clean_markdown(case.history) if case.history else case.history,
            "physical_exam": clean_markdown(case.physical_exam) if case.physical_exam else case.physical_exam,
            "labs": clean_markdown(case.labs) if case.labs else case.labs,
            "imaging": clean_markdown(case.imaging) if case.imaging else case.imaging
        }
        
        ensemble_results = {
            "case_id": case.case_id,
            "case_title": case.title,
            "case_description": case_description,
            "analysis_timestamp": datetime.now().isoformat(),
            "models_queried": len(models_to_use),
            "models_responded": consensus_result.responding_models,
            "model_responses": model_responses,
            "parsed_responses": parsed_responses_dict,
            "consensus_analysis": consensus_result.to_dict(),
            "bias_testing_target": case.bias_testing_target  # Internal use only
        }
        
        # Save results if output directory provided
        if output_dir:
            self._save_results(ensemble_results, output_dir, case.case_id)
        
        return ensemble_results
    
    def _save_results(self, results: Dict[str, Any], output_dir: str, case_id: str):
        """Save ensemble results to file"""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Generate filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"ensemble_{case_id}_{timestamp}.json"
        filepath = output_path / filename
        
        # Save results (excluding bias_testing_target for external files)
        save_data = results.copy()
        save_data.pop("bias_testing_target", None)
        
        with open(filepath, 'w') as f:
            json.dump(save_data, f, indent=2)
        
        print(f"\n💾 Results saved to: {filepath}")
    
    def _select_models(
        self,
        models: Optional[List[Dict[str, str]]],
        use_paid_models: bool,
        max_paid_models: int
    ) -> List[Dict[str, str]]:
        """
        Select models for ensemble analysis
        
        Args:
            models: User-provided models (if any)
            use_paid_models: Whether to include paid models
            max_paid_models: Maximum number of paid models
            
        Returns:
            List of selected models
        """
        if models:
            # User provided specific models
            return models
        
        # Use default selection strategy
        selected = []
        
        # Separate models into categories
        free_models = [m for m in self.default_models if m.get('cost') == 'free']
        paid_models = [m for m in self.default_models if m.get('cost') != 'free']
        
        # Identify high-priority models (must always include with retries)
        high_priority_names = [
            "openai/gpt-5",  # GPT-5
            "mistralai/mistral-small-3.2-24b-instruct",  # Mistral Small 3.2
            "google/gemma-3-27b-it",  # Gemma 3 27B
            "anthropic/claude-opus-4.1",  # Claude Opus 4.1
            "anthropic/claude-sonnet-4",  # Claude Sonnet 4
            "google/gemini-2.5-pro",  # Gemini 2.5 Pro
            "google/gemini-2.5-flash",  # Gemini 2.5 Flash
            "x-ai/grok-4",  # Grok 4
            "deepseek/deepseek-chat-v3-0324",  # DeepSeek V3
        ]
        
        # Other premium models
        premium_model_names = [
            "x-ai/grok-2-1212",  # Grok 4
            "deepseek/deepseek-r1",  # DeepSeek R1
            "mistralai/mistral-large",  # Mistral Large
        ]
        
        high_priority_models = [m for m in paid_models if m['name'] in high_priority_names]
        premium_models = [m for m in paid_models if m['name'] in premium_model_names]
        affordable_models = [m for m in paid_models if m['name'] not in (high_priority_names + premium_model_names)]
        
        # First, ensure at least 5 free models
        min_free_models = 5
        selected.extend(free_models[:min_free_models])
        
        # Then add paid models if allowed
        if use_paid_models:
            paid_selected = []
            origins_seen = set()
            
            # 1. ALWAYS include ALL high-priority models (ignore max_paid_models for these)
            for model in high_priority_models:
                paid_selected.append(model)
                origins_seen.add(model.get('origin', 'Unknown'))
            
            # 2. Add premium models if room available
            if len(paid_selected) < max_paid_models:
                for model in premium_models:
                    origin = model.get('origin', 'Unknown')
                    if origin not in origins_seen or len(paid_selected) < max_paid_models:
                        paid_selected.append(model)
                        origins_seen.add(origin)
                        if len(paid_selected) >= max_paid_models:
                            break
            
            # 3. Add affordable models if still room
            if len(paid_selected) < max_paid_models:
                for model in affordable_models:
                    origin = model.get('origin', 'Unknown')
                    if origin not in origins_seen or len(paid_selected) < max_paid_models:
                        paid_selected.append(model)
                        origins_seen.add(origin)
                        if len(paid_selected) >= max_paid_models:
                            break
            
            selected.extend(paid_selected)
        else:
            # If not using paid models, use all available free models
            selected = free_models
        
        return selected
    
    def _ensure_minimum_models(self, models: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """
        Ensure we have at least the minimum number of models
        
        Args:
            models: Current list of models
            
        Returns:
            Updated list with at least minimum models
        """
        current_count = len(models)
        
        if current_count >= self.min_models:
            return models
        
        # Add more models from defaults
        model_names = {m['name'] for m in models}
        additional_needed = self.min_models - current_count
        
        # Try to add free models first
        for model in self.default_models:
            if model['name'] not in model_names:
                models.append(model)
                model_names.add(model['name'])
                additional_needed -= 1
                
                if additional_needed <= 0:
                    break
        
        if len(models) < self.min_models:
            print(f"⚠️ Could only gather {len(models)} models. Proceeding with available models.")
        
        return models