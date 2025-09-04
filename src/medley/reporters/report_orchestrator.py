"""
Report Orchestrator - Intelligent Agent for Medical Report Analysis
Uses LLM to analyze ensemble results and generate structured report data
"""

import json
import logging
import time
from typing import Dict, Any, List, Optional
from datetime import datetime
from pathlib import Path

# Import ModelConfig at module level to avoid import issues
try:
    from src.medley.utils.config import ModelConfig
except ImportError:
    from ...utils.config import ModelConfig

logger = logging.getLogger(__name__)


class ReportOrchestrator:
    """
    Intelligent orchestrator that uses LLM as an agent to analyze
    medical ensemble results and produce structured report data
    """
    
    def __init__(self, llm_manager):
        """
        Initialize the orchestrator
        
        Args:
            llm_manager: LLM manager for querying models
        """
        self.llm_manager = llm_manager
        self.orchestrator_model = "anthropic/claude-sonnet-4"  # Claude Sonnet 4.0 primary orchestrator
        # NEVER use anthropic/claude-3-5-sonnet-20241022 - it doesn't follow instructions properly
        self.fallback_models = [
            "openai/gpt-4o",  # First backup orchestrator
            "google/gemini-2.5-pro",  # Second backup orchestrator
        ]
        self.fallback_model = self.fallback_models[0]  # Default fallback for compatibility
        self.max_retries = 1
        self.retry_delay = 30  # seconds
        self.cache_dir = Path.cwd() / "cache"
        
    def create_orchestrator_prompt(self, ensemble_results: Dict, analysis_type: str) -> str:
        """
        Create a comprehensive prompt that defines the orchestrator's role as an agent
        
        Args:
            ensemble_results: The ensemble analysis results
            analysis_type: Type of analysis needed
            
        Returns:
            Formatted prompt for the orchestrator
        """
        
        # Filter and truncate model responses to avoid token limits
        truncated_results = ensemble_results.copy()
        
        # CRITICAL: Filter model_responses EARLY to only include max 5 models
        # This prevents the prompt from becoming too large
        max_models_for_prompt = 5
        
        # Apply early filtering to prevent huge prompts
        if 'model_responses' in truncated_results:
            # Prioritize high-quality models
            high_priority_models = ['gpt-4', 'claude', 'gemini', 'grok', 'deepseek']
            
            responses = truncated_results['model_responses']
            original_count = len(responses)
            
            print(f"🔍 Filtering model responses: {original_count} models found")
            
            high_priority_responses = []
            other_responses = []
            
            for response in responses:
                model_name = response.get('model_name', '').lower()
                if any(hp in model_name for hp in high_priority_models):
                    high_priority_responses.append(response)
                else:
                    other_responses.append(response)
            
            print(f"  📊 High priority: {len(high_priority_responses)} models")
            print(f"  📊 Other models: {len(other_responses)} models")
            
            # Take up to max_models_for_prompt, prioritizing high-quality models
            filtered = high_priority_responses[:max_models_for_prompt]
            if len(filtered) < max_models_for_prompt:
                filtered.extend(other_responses[:max_models_for_prompt - len(filtered)])
            
            truncated_results['model_responses'] = filtered
            
            print(f"✂️ FILTERED: Reduced from {original_count} to {len(filtered)} models")
            print(f"  📋 Selected models: {[r.get('model_name', 'N/A')[:20] for r in filtered]}")
            
            # Calculate size reduction
            import json
            original_size = len(json.dumps(ensemble_results))
            filtered_size = len(json.dumps(truncated_results))
            reduction = (1 - filtered_size/original_size) * 100
            print(f"  📉 Size reduction: {reduction:.1f}% ({original_size:,} → {filtered_size:,} chars)")
            
            logger.info(f"Early filtering: {original_count} → {len(filtered)} models, {reduction:.1f}% size reduction")
        
        # Token limits for orchestrator models (conservative estimates)
        ORCHESTRATOR_TOKEN_LIMITS = {
            "anthropic/claude-sonnet-4": 30000,              # Claude Sonnet 4.0 - PRIMARY
            "google/gemini-2.5-pro": 40000,                  # Gemini 2.5 Pro - fallback
            "openai/gpt-4o": 30000,                          # GPT-4o - fallback
            "anthropic/claude-3-opus-20240229": 20000,      # Claude Opus 4.1 - fallback
            # DO NOT USE: "anthropic/claude-3-5-sonnet-20241022" - doesn't follow instructions
        }
        
        # Use primary orchestrator's limit
        max_tokens = ORCHESTRATOR_TOKEN_LIMITS.get(self.orchestrator_model, 20000)
        
        # Reserve tokens for prompt structure, metadata, etc.
        reserved_tokens = 5000
        available_tokens = max_tokens - reserved_tokens
        
        # Truncate individual responses if needed
        if 'model_responses' in truncated_results:
            max_response_chars = 500  # Limit each response to 500 chars
            for response in truncated_results['model_responses']:
                if 'response' in response and isinstance(response['response'], str):
                    if len(response['response']) > max_response_chars:
                        response['response'] = response['response'][:max_response_chars] + "... [truncated]"
        
        # Further reduce ensemble data for orchestrator
        # Only keep essential fields to prevent prompt from being too large
        essential_data = {
            "case_id": truncated_results.get("case_id"),
            "model_responses": truncated_results.get("model_responses", [])[:5],  # Max 5 models
            "diagnostic_landscape": {
                "primary_diagnosis": truncated_results.get("diagnostic_landscape", {}).get("primary_diagnosis"),
                "strong_alternatives": truncated_results.get("diagnostic_landscape", {}).get("strong_alternatives", [])[:3],
                "alternatives": truncated_results.get("diagnostic_landscape", {}).get("alternatives", [])[:3],
                "minority_opinions": truncated_results.get("diagnostic_landscape", {}).get("minority_opinions", [])[:2]
            },
            "total_models_analyzed": truncated_results.get("total_models_analyzed", 0)
        }
        
        # Convert ensemble results to clean JSON
        ensemble_json = json.dumps(essential_data, indent=2)
        
        print(f"  📊 Reduced ensemble data from {len(json.dumps(truncated_results)):,} to {len(ensemble_json):,} chars")
        
        # Get metadata ONLY for models actually being analyzed
        analyzed_models = set()
        if 'model_responses' in truncated_results:
            for response in truncated_results['model_responses']:
                model_name = response.get('model_name', '')
                if model_name:
                    analyzed_models.add(model_name)
        
        # Get filtered metadata for only analyzed models
        all_metadata = self._get_comprehensive_model_metadata()
        filtered_metadata = {
            "individual_models": {
                model: data for model, data in all_metadata.get("individual_models", {}).items()
                if model in analyzed_models
            }
        }
        
        print(f"  📊 Including metadata for {len(filtered_metadata['individual_models'])} models (was {len(all_metadata.get('individual_models', {}))})")
        metadata_json = json.dumps(filtered_metadata, indent=2)
        
        # Skip cross-case context to reduce prompt size
        # cross_case_context = self._get_cross_case_context()
        cross_case_json = "{}"  # Empty for now to reduce prompt size
        
        base_prompt = f"""
You are a Medical Report Analysis Agent specialized in synthesizing diverse AI model opinions 
into comprehensive clinical decision support reports. Your role is to analyze multiple AI model
responses about medical cases and extract actionable insights for physicians.

AGENT CAPABILITIES:
- Extract and categorize diagnoses with consensus percentages
- Identify management strategies and group them by urgency
- Detect critical decision points where models diverge
- Analyze potential biases based on model characteristics
- Synthesize evidence and create diagnostic correlation matrices
- Generate structured JSON output for report generation

MODEL BIAS METADATA:
Use this comprehensive metadata to inform your bias analysis:
{metadata_json}

CROSS-CASE CONTEXT:
Available cached responses across all cases for comparison:
{cross_case_json}

ENSEMBLE DATA TO ANALYZE:
{ensemble_json}

YOUR TASK:
"""
        
        if analysis_type == "simplified_analysis":
            # NEW: Simplified 50-line JSON structure
            return base_prompt + """
Analyze the ensemble model responses and extract the essential diagnostic information.

FOCUS ON: Primary diagnosis, all differential diagnoses with ICD codes, key evidence, and immediate actions.

Return this SIMPLIFIED JSON structure (exactly as shown):
{
  "primary_diagnosis": {
    "name": "Most agreed upon diagnosis",
    "icd_code": "ICD-10 code (use lookup below)",
    "confidence": 0.0-1.0,
    "agreement_percentage": percentage,
    "supporting_models": ["model1", "model2"]
  },
  "differential_diagnoses": [
    {
      "name": "Alternative diagnosis",
      "icd_code": "ICD-10 code",
      "frequency": number of models suggesting this diagnosis,
      "percentage": percentage of models (frequency/total * 100)
    }
  ],
  "key_evidence": ["symptom1", "symptom2", "finding1"],
  "immediate_actions": ["action1", "action2"],
  "critical_tests": ["test1", "test2"],
  "decision_points": ["critical decision 1", "critical decision 2"]
}

ICD-10 LOOKUP (use these codes):
- IgA Nephropathy: N02.8
- Lupus Nephritis: M32.14
- SLE: M32.9
- Membranoproliferative Glomerulonephritis: N03.5
- Post-infectious Glomerulonephritis: N05.9
- Acute Interstitial Nephritis: N10
- ANCA-Associated Vasculitis: M31.7
- Chronic Kidney Disease: N18.9
- Pyelonephritis: N10
- Familial Mediterranean Fever: E85.0
- Inflammatory Bowel Disease: K50.9

IMPORTANT:
1. Include ALL diagnoses mentioned by ANY model in differential_diagnoses
2. Calculate percentages based on total models analyzed
3. Keep responses concise - single values or short lists
4. Return ONLY the JSON structure above, no additional text
"""
        
        elif analysis_type == "comprehensive_analysis":
            return base_prompt + """
Perform a comprehensive analysis and return a JSON object with the following structure.

IMPORTANT REQUIREMENTS:
1. Categorize diagnoses using these thresholds:
   - Primary diagnosis: Highest agreement percentage
   - Strong alternatives: ≥30% agreement (excluding primary)
   - Alternatives: 10-29% agreement
   - Minority opinions: <10% agreement
   - ALL diagnoses should appear in "all_alternative_diagnoses" regardless of percentage

2. Generate case-specific decision trees based on the actual primary diagnosis:
   - For dementia/cognitive cases: Start with cognitive assessment (MMSE/MoCA), then brain imaging, metabolic panel, etc.
   - For inflammatory/genetic disorders: Start with specific genetic testing, then inflammatory markers, autoimmune workup
   - For metabolic disorders: Start with metabolic panel, then specific tests for the suspected condition
   - For malignancies: Start with screening labs, then imaging, then tissue diagnosis
   The decision tree should be SPECIFIC to the diagnosed condition, not generic.

3. For "all_alternative_diagnoses": 
   - Compile a comprehensive list of ALL diagnoses considered by the models
   - Include diagnoses from all categories (primary, alternatives, minority)
   - Add appropriate ICD-10 codes where applicable
   - Sort by number of supporting models (descending)
   - Aim for 10-20 most relevant diagnoses
   Common ICD-10 codes include:
   - Familial Mediterranean Fever (FMF): E85.0
   - Systemic Lupus Erythematosus (SLE): M32.9
   - Lupus Nephritis: M32.14
   - IgA Nephropathy: N02.8
   - ANCA-Associated Vasculitis: M31.7
   - Membranoproliferative Glomerulonephritis: N03.5
   - Post-infectious Glomerulonephritis: N05.9
   - Acute Interstitial Nephritis: N10
   - Anti-GBM Disease/Goodpasture: M31.0
   - Alport Syndrome: Q87.81
   - Thin Basement Membrane Disease: N02.9
   - Henoch-Schönlein Purpura: D69.0
   - Focal Segmental Glomerulosclerosis: N04.1
   - Minimal Change Disease: N04.0
   - Membranous Nephropathy: N04.2
   - Inflammatory Bowel Disease: K50.9
   - Adult Still's Disease: M06.1
   - Behçet's Disease: M35.2
   - TRAPS: M04.1
   - Look up appropriate codes for ALL other conditions mentioned

{
  "diagnostic_landscape": {
    "primary_diagnosis": {
      "name": "string",
      "agreement_percentage": number,
      "supporting_models": ["model1", "model2"],
      "evidence": ["symptom1", "symptom2"],
      "confidence": "High|Moderate|Low"
    },
    "strong_alternatives": [
      {
        "name": "string",
        "icd10_code": "string",
        "agreement_percentage": number,
        "supporting_models": ["model1", "model2"],
        "evidence": ["symptom1", "symptom2"]
      }
    ],
    "alternatives": [
      {
        "name": "string",
        "icd10_code": "string", 
        "agreement_percentage": number,
        "supporting_models": ["model1", "model2"],
        "evidence": ["symptom1", "symptom2"]
      }
    ],
    "minority_opinions": [
      {
        "name": "string",
        "icd10_code": "string",
        "agreement_percentage": number,
        "supporting_models": ["model1"],
        "clinical_significance": "string"
      }
    ],
    "all_alternative_diagnoses": [
      {
        "name": "Diagnosis name",
        "icd10_code": "string",
        "supporting_models": ["model1", "model2"],
        "count": number,
        "percentage": number,
        "evidence": ["key symptom or finding"]
      }
      // Include 10-20 most relevant diagnoses from all categories
    ]
  },
  "management_strategies": {
    "immediate_actions": [
      {
        "action": "string",
        "consensus_percentage": number,
        "supporting_models": ["model1", "model2"],
        "urgency": "Critical|High|Moderate"
      }
    ],
    "differential_testing": [
      {
        "test": "string",
        "purpose": "string",
        "consensus_percentage": number,
        "conditions_to_rule_out": ["condition1", "condition2"]
      }
    ],
    "treatment_options": [
      {
        "treatment": "string",
        "dosage": "string",
        "consensus_percentage": number,
        "contraindications": ["string"]
      }
    ],
    "specialist_consultations": [
      {
        "specialty": "string",
        "reason": "string",
        "consensus_percentage": number,
        "timing": "Immediate|Within 48h|Routine"
      }
    ]
  },
  "critical_decision_points": [
    {
      "topic": "string",
      "divergence_description": "string",
      "option_1": {
        "approach": "string",
        "supporting_models": ["model1", "model2"],
        "percentage": number,
        "rationale": "string"
      },
      "option_2": {
        "approach": "string",
        "supporting_models": ["model3", "model4"],
        "percentage": number,
        "rationale": "string"
      },
      "clinical_impact": "string"
    }
  ],
  "ai_model_bias_analysis": {
    "primary_diagnosis_bias_factors": {
      "cultural_bias": {
        "description": "Analysis of how cultural backgrounds of models affected primary diagnosis",
        "affected_models": ["model1", "model2"],
        "bias_impact": "High|Moderate|Low",
        "specific_concerns": ["concern1", "concern2"]
      },
      "geographic_bias": {
        "description": "Regional medical practice influences on diagnosis",
        "western_models_pattern": "string",
        "asian_models_pattern": "string", 
        "european_models_pattern": "string",
        "impact_on_diagnosis": "string"
      },
      "training_data_bias": {
        "description": "How training data limitations affected diagnostic accuracy",
        "newer_models_advantage": "string",
        "older_models_limitation": "string",
        "knowledge_gaps": ["gap1", "gap2"]
      }
    },
    "alternative_diagnoses_bias": {
      "missed_diagnoses_due_to_bias": [
        {
          "diagnosis": "string",
          "bias_type": "cultural|geographic|temporal|architectural",
          "affected_model_regions": ["USA", "Europe", "China"],
          "explanation": "Why this diagnosis was missed"
        }
      ],
      "overrepresented_diagnoses": [
        {
          "diagnosis": "string", 
          "bias_source": "string",
          "frequency_bias": "Models from certain regions over-diagnosed this"
        }
      ]
    },
    "model_architecture_patterns": {
      "multimodal_vs_text_only": {
        "diagnostic_differences": "string",
        "strengths_limitations": "string"
      },
      "model_size_impact": {
        "large_model_patterns": "string",
        "small_model_patterns": "string",
        "diagnostic_accuracy_correlation": "string"
      }
    },
    "bias_mitigation_recommendations": [
      {
        "bias_type": "string",
        "recommendation": "string",
        "implementation": "string"
      }
    ]
  },
  "evidence_synthesis": {
    "symptom_diagnosis_matrix": {
      "symptoms": ["fever", "pain", "arthritis"],
      "diagnoses": ["FMF", "IBD", "SLE"],
      "correlations": [
        {"symptom": "fever", "diagnosis": "FMF", "strength": "+++"},
        {"symptom": "fever", "diagnosis": "IBD", "strength": "+"},
        {"symptom": "pain", "diagnosis": "FMF", "strength": "+++"}
      ]
    },
    "key_clinical_findings": [
      {
        "finding": "string",
        "diagnostic_significance": "string",
        "mentioned_by_models": number
      }
    ],
    "diagnostic_certainty": {
      "high_confidence_findings": ["string"],
      "moderate_confidence_findings": ["string"],
      "areas_of_uncertainty": ["string"]
    }
  },
  "clinical_decision_tree": {
    "initial_test": "SPECIFIC initial test based on the primary diagnosis identified above",
    "branches": [
      {
        "test": "Specific diagnostic test name (not generic)",
        "if_positive": "Specific action for positive result",
        "if_negative": "Specific action for negative result",
        "condition": "Test result interpretation",
        "next_action": "Follow-up action specific to diagnosis",
        "sub_branches": []
      },
      {
        "test": "Alternative test if first is negative",
        "if_positive": "Action for this specific test",
        "if_negative": "Next differential approach",
        "condition": "Result interpretation",
        "next_action": "Disease-specific next steps",
        "sub_branches": []
      }
    ]
  },
  "primary_diagnosis_summaries": {
    "key_clinical_findings": [
      {
        "finding": "string",
        "supporting_evidence": "string",
        "model_support": number,
        "reasoning": "string"
      }
    ],
    "recommended_tests": [
      {
        "test_name": "string",
        "test_type": "Laboratory|Imaging|Biopsy|Other",
        "rationale": "string",
        "priority": "Urgent|High|Moderate|Routine",
        "model_support": number,
        "reasoning": "string"
      }
    ],
    "immediate_management": [
      {
        "intervention": "string",
        "category": "Medication|Procedure|Lifestyle|Monitoring",
        "urgency": "Immediate|Within hours|Within days",
        "model_support": number,
        "reasoning": "string"
      }
    ],
    "medications": [
      {
        "medication_name": "string",
        "dosage": "string",
        "route": "string",
        "frequency": "string",
        "duration": "string",
        "indication": "string",
        "model_support": number,
        "reasoning": "string"
      }
    ]
  },
  "quality_metrics": {
    "total_models_analyzed": number,
    "successful_responses": number,
    "consensus_strength": "Strong|Moderate|Weak",
    "diagnostic_diversity_index": number,
    "confidence_in_primary_diagnosis": number
  }
}


IMPORTANT INSTRUCTIONS:
1. Extract actual model names from the ensemble data (use short names if available)
2. Calculate real percentages based on model agreement
3. Identify genuine divergence points from the responses
4. Use the provided MODEL BIAS METADATA to analyze potential bias sources for both primary and alternative diagnoses
5. For ai_model_bias_analysis section, specifically examine:
   - How cultural backgrounds (USA/Europe/China) of models influenced diagnostic decisions
   - Whether training data limitations led to missed or over-represented diagnoses
   - Impact of model architecture and size on diagnostic accuracy
   - Specific bias mitigation strategies based on the observed patterns
6. Create evidence correlations based on symptoms mentioned in responses
7. Build a practical decision tree based on the consensus recommendations
8. For "primary_diagnosis_summaries" section, organize findings, tests, management, and medications specifically for the identified primary diagnosis. Include reasoning for each recommendation.
9. Return ONLY valid JSON without any markdown formatting or explanations
"""
        
        elif analysis_type == "management_focus":
            return base_prompt + """
Focus specifically on extracting management strategies and treatment recommendations.
Analyze which treatments are recommended, by which models, and with what level of consensus.

Return a JSON object with detailed management pathways:
{
  "immediate_interventions": [],
  "diagnostic_workup": [],
  "treatment_algorithms": [],
  "monitoring_plan": [],
  "red_flags": []
}
"""
        
        elif analysis_type == "bias_detection":
            return base_prompt + """
Focus on detecting and analyzing potential biases in the model responses.
Look for patterns based on model origin, size, training data, and architecture.

Return a JSON object with detailed bias analysis:
{
  "geographic_biases": {},
  "temporal_biases": {},
  "architectural_biases": {},
  "training_data_biases": {},
  "mitigation_strategies": []
}
"""
        
        return base_prompt + "Perform a general analysis of the ensemble results."
    
    def _get_cross_case_context(self) -> Dict:
        """
        Load cached responses from all cases to provide cross-case context
        
        Returns:
            Dictionary with responses organized by case
        """
        cross_case_data = {}
        responses_dir = self.cache_dir / "responses"
        
        if not responses_dir.exists():
            return {}
        
        for case_dir in responses_dir.iterdir():
            if case_dir.is_dir():
                case_name = case_dir.name
                cross_case_data[case_name] = {
                    "responses": [],
                    "model_count": 0
                }
                
                # Load cached responses for this case
                for cache_file in case_dir.glob("*.json"):
                    try:
                        with open(cache_file, 'r') as f:
                            data = json.load(f)
                        
                        if data.get('content'):
                            model_name = cache_file.stem.replace('_', '/')
                            cross_case_data[case_name]["responses"].append({
                                "model_name": model_name,
                                "content_length": len(data.get('content', '')),
                                "timestamp": data.get('timestamp', 'Unknown'),
                                "has_valid_response": bool(data.get('content'))
                            })
                            
                    except Exception as e:
                        logger.warning(f"Error loading {cache_file}: {e}")
                
                cross_case_data[case_name]["model_count"] = len(cross_case_data[case_name]["responses"])
        
        return cross_case_data
        
    def _get_comprehensive_model_metadata(self) -> Dict:
        """
        Get comprehensive model metadata for bias analysis based on 2025 research
        
        Returns:
            Dictionary with comprehensive model characteristics and bias profiles
        """
        # Try to import the 2025 comprehensive metadata
        try:
            from model_metadata_2025 import get_comprehensive_model_metadata, get_geographical_distribution
            comprehensive_metadata = get_comprehensive_model_metadata()
            geo_distribution = get_geographical_distribution()
            
            # Add summary statistics and bias insights
            metadata_with_analysis = {
                "individual_models": comprehensive_metadata,
                "geographical_distribution": geo_distribution,
                "bias_summary": {
                    "total_models": len(comprehensive_metadata),
                    "countries_represented": len(geo_distribution),
                    "western_dominance": len(geo_distribution.get('USA', [])) + len(geo_distribution.get('Canada', [])) + len(geo_distribution.get('France', [])),
                    "eastern_representation": len(geo_distribution.get('China', [])) + len(geo_distribution.get('Japan/USA', [])),
                    "key_bias_concerns": [
                        "Western medical paradigm dominance",
                        "English language training bias", 
                        "Limited Global South representation",
                        "Tech industry cultural influence",
                        "Socioeconomic status assumptions"
                    ]
                }
            }
            
            return metadata_with_analysis
            
        except ImportError:
            # Fallback to basic metadata if import fails
            pass
        return {
            'USA': {
                'medical_bias_characteristics': [
                    'Western medicine focus',
                    'Individualistic treatment approach',
                    'Technology-heavy diagnostics preference',
                    'Subspecialty care emphasis'
                ],
                'cultural_limitations': [
                    'Limited understanding of traditional medicine',
                    'Western-centric symptom interpretation',
                    'English-language training bias',
                    'American healthcare system assumptions'
                ],
                'diagnostic_tendencies': 'Favor high-tech diagnostics, subspecialist referrals, and evidence-based protocols'
            },
            'Europe': {
                'medical_bias_characteristics': [
                    'Holistic patient care approach',
                    'Primary care emphasis',
                    'Conservative treatment preferences',
                    'Public health perspective'
                ],
                'cultural_limitations': [
                    'European healthcare system bias',
                    'Limited non-European disease knowledge',
                    'Regulatory framework assumptions',
                    'Population-specific epidemiology focus'
                ],
                'diagnostic_tendencies': 'Emphasize conservative management, primary care coordination, and population health'
            },
            'China': {
                'medical_bias_characteristics': [
                    'Traditional Chinese Medicine integration',
                    'Collective healthcare approach',
                    'Prevention-focused methodology',
                    'East Asian population genetics consideration'
                ],
                'cultural_limitations': [
                    'Limited Western rare disease knowledge',
                    'Chinese regulatory framework bias',
                    'Mandarin language training preference',
                    'Asian-centric symptom patterns'
                ],
                'diagnostic_tendencies': 'Integrate TCM approaches, emphasize prevention, consider genetic factors specific to East Asian populations'
            },
            'General': {
                'model_size_bias': {
                    'large_models': 'More comprehensive but potentially overconfident',
                    'small_models': 'More focused but may miss rare conditions'
                },
                'training_data_bias': {
                    '2024_models': 'Most current medical knowledge, recent research',
                    '2023_models': 'May lack latest treatment guidelines',
                    '2022_models': 'Missing COVID-19 long-term effects data'
                },
                'architectural_bias': {
                    'multimodal_models': 'Better at imaging interpretation',
                    'text_only_models': 'May miss visual diagnostic cues',
                    'specialized_models': 'Domain-specific strengths and limitations'
                }
            }
        }
    
    def _query_orchestrator_with_retry(self, prompt: str, attempt: int = 1, use_fallback: bool = False) -> tuple:
        """
        Query orchestrator model with retry mechanism and fallback
        
        Args:
            prompt: The orchestrator prompt
            attempt: Current attempt number (1-based)
            use_fallback: Whether to use fallback model
            
        Returns:
            Tuple of (success: bool, response_content: str, error: str)
        """
        model_id = self.fallback_model if use_fallback else self.orchestrator_model
        model_name = model_id  # Use actual model ID as name
        
        try:
            # Create model config for orchestrator
            orchestrator_config = ModelConfig(
                name=f"Orchestrator-{model_name}",
                provider="anthropic",
                model_id=model_id,
                temperature=0.2,  # Low temperature for consistent structured output
                max_tokens=4000  # Enough for comprehensive analysis
            )
            
            logger.info(f"🔄 Orchestrator attempt {attempt}/{self.max_retries} using {model_name} ({model_id})")
            
            # Query the model - check prompt size first
            print(f"  📤 Sending prompt ({len(prompt):,} chars) to {model_name}...")
            
            # CRITICAL: If prompt is too large, truncate it
            # Claude Sonnet 4.0 supports 200K tokens (~800K chars)
            # We'll use 100K chars as a safe limit (about 25K tokens)
            max_prompt_chars = 100000
            if len(prompt) > max_prompt_chars:
                print(f"  ⚠️ Prompt too large! Truncating from {len(prompt):,} to {max_prompt_chars:,} chars")
                # Truncate but ensure we keep the JSON template at the end
                prompt = prompt[:max_prompt_chars] + "\n\nReturn JSON only."
            
            import time
            start_time = time.time()
            
            try:
                response = self.llm_manager.query_model(
                    model_config=orchestrator_config,
                    prompt=prompt
                )
                elapsed = time.time() - start_time
                print(f"  📥 Response received after {elapsed:.2f}s")
                
            except Exception as e:
                elapsed = time.time() - start_time
                error_msg = f"Query failed after {elapsed:.2f}s: {str(e)}"
                print(f"  ❌ {error_msg}")
                logger.warning(error_msg)
                return False, "", error_msg
            
            # Check for errors
            if response.error:
                error_msg = f"Model {model_name} query failed: {response.error}"
                logger.warning(error_msg)
                return False, "", error_msg
                
            response_text = response.content
            
            if not response_text or len(response_text.strip()) < 50:
                error_msg = f"Model {model_name} returned empty or very short response"
                logger.warning(error_msg)
                return False, "", error_msg
            
            logger.info(f"✅ Orchestrator {model_name} succeeded on attempt {attempt}")
            return True, response_text, ""
            
        except Exception as e:
            error_msg = f"Exception during {model_name} query: {str(e)}"
            logger.error(error_msg)
            return False, "", error_msg
        
    def orchestrate_analysis(self, ensemble_results: Dict) -> Dict:
        """
        Orchestrate comprehensive analysis using LLM as an intelligent agent with retry mechanism
        
        Args:
            ensemble_results: The ensemble analysis results
            
        Returns:
            Structured analysis results
        """
        print(f"🔍 Orchestrator received ensemble data with {len(ensemble_results.get('model_responses', []))} model responses")
        
        try:
            # First try the split orchestrator approach
            split_result = self._run_split_orchestrator(ensemble_results)
            if split_result:
                return split_result
            
            # Fall back to simplified single query
            print("\n🔄 Split orchestrator failed, trying simplified single query...")
            
            # Create the orchestrator prompt
            # Use simplified prompt for complex cases
            prompt = self.create_orchestrator_prompt(
                ensemble_results, 
                "simplified_analysis"  # Changed from "comprehensive_analysis"
            )
            
            logger.info(f"🧠 Starting simplified orchestrator analysis with {self.max_retries} max retries")
            
            # Try primary model with retries
            for attempt in range(1, self.max_retries + 1):
                print(f"\n🔄 Orchestrator attempt {attempt}/{self.max_retries} using {self.orchestrator_model}...")
                
                success, response_text, error = self._query_orchestrator_with_retry(
                    prompt, attempt, use_fallback=False
                )
                
                if success:
                    # Try to parse the JSON response
                    try:
                        # Clean the response (remove markdown if present)
                        clean_response = response_text.strip()
                        if clean_response.startswith("```json"):
                            clean_response = clean_response[7:]
                        if clean_response.startswith("```"):
                            clean_response = clean_response[3:]
                        if clean_response.endswith("```"):
                            clean_response = clean_response[:-3]
                            
                        analysis_result = json.loads(clean_response)
                        
                        # Validate and enhance the result
                        analysis_result = self._validate_and_enhance(analysis_result, ensemble_results)
                        
                        print(f"✅ Orchestrator analysis completed successfully on attempt {attempt}")
                        return analysis_result
                        
                    except json.JSONDecodeError as e:
                        logger.warning(f"Attempt {attempt}: Failed to parse JSON response: {e}")
                        if attempt < self.max_retries:
                            print(f"⏳ Waiting {self.retry_delay} seconds before retry...")
                            time.sleep(self.retry_delay)
                            continue
                else:
                    logger.warning(f"Attempt {attempt} failed: {error}")
                    if attempt < self.max_retries:
                        print(f"⏳ Waiting {self.retry_delay} seconds before retry...")
                        time.sleep(self.retry_delay)
            
            # Try fallback models: GPT-4o and Gemini 2.5 Pro
            logger.warning(f"🔄 All {self.orchestrator_model} attempts failed, trying backup orchestrators...")
            
            # Only use GPT-4o and Gemini 2.5 Pro as backups
            backup_models = ["openai/gpt-4o", "google/gemini-2.5-pro"]
            
            for fallback_model in backup_models:
                print(f"\n🔄 Trying backup orchestrator: {fallback_model}...")
                self.fallback_model = fallback_model  # Update current fallback
                
                success, response_text, error = self._query_orchestrator_with_retry(
                    prompt, attempt=1, use_fallback=True
                )
                
                if success:
                    try:
                        # Clean the response (remove markdown if present)
                        clean_response = response_text.strip()
                        if clean_response.startswith("```json"):
                            clean_response = clean_response[7:]
                        if clean_response.startswith("```"):
                            clean_response = clean_response[3:]
                        if clean_response.endswith("```"):
                            clean_response = clean_response[:-3]
                        
                        analysis_result = json.loads(clean_response)
                        
                        # Validate and enhance the result
                        analysis_result = self._validate_and_enhance(analysis_result, ensemble_results)
                        
                        print(f"✅ Orchestrator analysis completed successfully using {fallback_model}")
                        return analysis_result
                        
                    except json.JSONDecodeError as e:
                        logger.error(f"Backup {fallback_model} failed to parse JSON: {e}")
                        print(f"❌ {fallback_model} failed JSON parsing")
                        continue  # Try next backup
                else:
                    logger.error(f"Backup {fallback_model} failed: {error}")
                    print(f"❌ {fallback_model} failed: {error}")
                    continue  # Try next backup
            
            # If all models failed, use fallback extraction
            logger.error("All orchestrator models failed, using basic extraction")
            print(f"⚠️  All orchestrator models failed, using basic extraction")
            return self._fallback_extraction(ensemble_results)
                
        except Exception as e:
            logger.error(f"Orchestration completely failed: {e}")
            print(f"💥 Orchestration completely failed: {e}")
            import traceback
            print(f"Full traceback:")
            traceback.print_exc()
            return self._fallback_extraction(ensemble_results)
            
    def _run_split_orchestrator(self, ensemble_results: Dict) -> Dict:
        """
        Run orchestrator in 3 focused queries for better reliability
        
        Args:
            ensemble_results: The ensemble analysis results
            
        Returns:
            Combined analysis results from all queries
        """
        try:
            print("🔄 Starting split orchestrator approach (3 focused queries)...")
            
            # Query 1: Diagnostic Analysis
            print("\n📊 Query 1: Diagnostic Analysis...")
            diagnostic_prompt = self._create_diagnostic_focused_prompt(ensemble_results)
            success1, diag_response, _ = self._query_orchestrator_with_retry(
                diagnostic_prompt, attempt=1, use_fallback=False
            )
            
            diagnostic_data = {}
            if success1:
                try:
                    clean_response = diag_response.strip()
                    if clean_response.startswith("```json"):
                        clean_response = clean_response[7:]
                    if clean_response.startswith("```"):
                        clean_response = clean_response[3:]
                    if clean_response.endswith("```"):
                        clean_response = clean_response[:-3]
                    diagnostic_data = json.loads(clean_response)
                    print("  ✅ Diagnostic analysis successful")
                except json.JSONDecodeError as e:
                    print(f"  ❌ Failed to parse diagnostic response: {e}")
                    return None
            else:
                print("  ❌ Diagnostic query failed")
                return None
            
            # Query 2: Management Strategies
            print("\n💊 Query 2: Management Strategies...")
            management_prompt = self._create_management_focused_prompt(ensemble_results, diagnostic_data)
            success2, mgmt_response, _ = self._query_orchestrator_with_retry(
                management_prompt, attempt=1, use_fallback=False
            )
            
            management_data = {}
            if success2:
                try:
                    clean_response = mgmt_response.strip()
                    if clean_response.startswith("```json"):
                        clean_response = clean_response[7:]
                    if clean_response.startswith("```"):
                        clean_response = clean_response[3:]
                    if clean_response.endswith("```"):
                        clean_response = clean_response[:-3]
                    management_data = json.loads(clean_response)
                    print("  ✅ Management analysis successful")
                except json.JSONDecodeError as e:
                    print(f"  ❌ Failed to parse management response: {e}")
                    # Continue with partial data
            else:
                print("  ⚠️ Management query failed, continuing with partial data")
            
            # Query 3: Bias Analysis
            print("\n🔍 Query 3: Bias Analysis...")
            bias_prompt = self._create_bias_focused_prompt(ensemble_results, diagnostic_data)
            success3, bias_response, _ = self._query_orchestrator_with_retry(
                bias_prompt, attempt=1, use_fallback=False
            )
            
            bias_data = {}
            if success3:
                try:
                    clean_response = bias_response.strip()
                    if clean_response.startswith("```json"):
                        clean_response = clean_response[7:]
                    if clean_response.startswith("```"):
                        clean_response = clean_response[3:]
                    if clean_response.endswith("```"):
                        clean_response = clean_response[:-3]
                    bias_data = json.loads(clean_response)
                    print("  ✅ Bias analysis successful")
                except json.JSONDecodeError as e:
                    print(f"  ⚠️ Failed to parse bias response: {e}")
                    # Continue with partial data
            else:
                print("  ⚠️ Bias query failed, continuing with partial data")
            
            # Combine all responses into full structure
            print("\n🔗 Combining split query results...")
            combined_analysis = self._combine_split_responses(
                diagnostic_data, 
                management_data, 
                bias_data,
                ensemble_results
            )
            
            # Validate and enhance
            combined_analysis = self._validate_and_enhance(combined_analysis, ensemble_results)
            
            print("✅ Split orchestrator completed successfully")
            return combined_analysis
            
        except Exception as e:
            logger.error(f"Split orchestrator failed: {e}")
            print(f"❌ Split orchestrator failed: {e}")
            return None
    
    def _filter_model_responses(self, model_responses: List[Dict]) -> List[Dict]:
        """
        Filter model responses to reduce size for prompts
        
        Args:
            model_responses: List of model response dictionaries
            
        Returns:
            Filtered list with essential information only
        """
        filtered = []
        for response in model_responses:
            if response.get("response"):
                # Extract key information only
                filtered_response = {
                    "model": response.get("model", "Unknown"),
                    "primary_diagnosis": None,
                    "differential_diagnoses": [],
                    "tests": [],
                    "treatment": []
                }
                
                try:
                    # Parse response if it's a string
                    resp_data = response["response"]
                    if isinstance(resp_data, str):
                        import json
                        resp_data = json.loads(resp_data)
                    
                    # Extract primary diagnosis
                    if "diagnosis" in resp_data:
                        diag = resp_data["diagnosis"]
                        if isinstance(diag, dict):
                            filtered_response["primary_diagnosis"] = diag.get("primary", diag.get("name"))
                        elif isinstance(diag, str):
                            filtered_response["primary_diagnosis"] = diag
                    
                    # Extract differentials
                    if "differential_diagnosis" in resp_data:
                        diffs = resp_data["differential_diagnosis"]
                        if isinstance(diffs, list):
                            filtered_response["differential_diagnoses"] = diffs[:5]
                    
                    # Extract tests
                    if "tests" in resp_data:
                        tests = resp_data["tests"]
                        if isinstance(tests, list):
                            filtered_response["tests"] = tests[:3]
                    
                    # Extract treatment
                    if "treatment" in resp_data:
                        treatment = resp_data["treatment"]
                        if isinstance(treatment, list):
                            filtered_response["treatment"] = treatment[:3]
                        elif isinstance(treatment, dict):
                            filtered_response["treatment"] = [treatment]
                    
                except (json.JSONDecodeError, TypeError, KeyError):
                    # If parsing fails, include raw response (truncated)
                    filtered_response["raw"] = str(response.get("response", ""))[:500]
                
                filtered.append(filtered_response)
        
        return filtered
    
    def _create_diagnostic_focused_prompt(self, ensemble_results: Dict) -> str:
        """Create prompt focused on diagnostic analysis"""
        model_responses = self._filter_model_responses(ensemble_results.get("model_responses", []))
        
        prompt = f"""Analyze the following {len(model_responses)} model responses and provide a diagnostic synthesis.

MODEL RESPONSES:
{json.dumps(model_responses, indent=2)[:30000]}

Return a JSON object with ONLY these fields:
{{
  "primary_diagnosis": {{
    "name": "string",
    "icd_code": "string",
    "confidence": "High|Medium|Low",
    "supporting_models": ["model1", "model2"],
    "percentage": number,
    "evidence": ["key supporting evidence 1", "key supporting evidence 2"]
  }},
  "differential_diagnoses": [
    {{
      "name": "string",
      "icd_code": "string",
      "frequency": number,
      "supporting_models": ["model1", "model2"],
      "evidence": ["supporting evidence for this diagnosis"]
    }}
  ],
  "key_evidence": ["finding1", "finding2", "finding3", "finding4", "finding5"],
  "symptom_diagnosis_matrix": {{
    "symptoms": ["symptom1", "symptom2", "symptom3"],
    "diagnoses": ["diagnosis1", "diagnosis2", "diagnosis3"],
    "correlations": [
      {{"symptom": "symptom1", "diagnosis": "diagnosis1", "strength": "Strong"}}
    ]
  }}
}}

Include at least 10 differential diagnoses if available from the model responses.

Return ONLY valid JSON, no explanations."""
        return prompt
    
    def _create_management_focused_prompt(self, ensemble_results: Dict, diagnostic_data: Dict) -> str:
        """Create prompt focused on management strategies"""
        primary_diagnosis = diagnostic_data.get("primary_diagnosis", {}).get("name", "Unknown")
        
        model_responses = self._filter_model_responses(ensemble_results.get("model_responses", []))[:10]
        
        prompt = f"""Given the primary diagnosis of {primary_diagnosis}, analyze management recommendations from the models.

MODEL RESPONSES (subset):
{json.dumps(model_responses, indent=2)[:20000]}

Return a JSON object with ONLY these fields:
{{
  "immediate_actions": ["action1", "action2"],
  "critical_tests": ["test1", "test2"],
  "medications": [
    {{
      "medication_name": "string",
      "dosage": "string",
      "route": "string",
      "frequency": "string",
      "duration": "string",
      "indication": "string"
    }}
  ],
  "monitoring_plan": ["item1", "item2"],
  "decision_points": ["point1", "point2"]
}}

Return ONLY valid JSON, no explanations."""
        return prompt
    
    def _create_bias_focused_prompt(self, ensemble_results: Dict, diagnostic_data: Dict) -> str:
        """Create prompt focused on bias analysis"""
        model_metadata = self._get_comprehensive_model_metadata()
        primary_diagnosis = diagnostic_data.get("primary_diagnosis", {}).get("name", "Unknown")
        
        prompt = f"""Analyze potential biases in the diagnostic consensus for {primary_diagnosis}.

MODEL METADATA:
{json.dumps(model_metadata, indent=2)[:10000]}

DIAGNOSTIC CONSENSUS:
Primary: {primary_diagnosis}
Alternatives: {json.dumps(diagnostic_data.get("differential_diagnoses", [])[:5], indent=2)}

Return a JSON object with ONLY these fields:
{{
  "geographic_bias": {{
    "detected": boolean,
    "description": "string",
    "mitigation": "string"
  }},
  "training_bias": {{
    "detected": boolean,
    "description": "string",
    "mitigation": "string"
  }},
  "consensus_strength": "Strong|Moderate|Weak",
  "minority_opinions": ["opinion1", "opinion2"]
}}

Return ONLY valid JSON, no explanations."""
        return prompt
    
    def _combine_split_responses(self, diagnostic_data: Dict, management_data: Dict, 
                                bias_data: Dict, ensemble_results: Dict) -> Dict:
        """Combine responses from split queries into full structure"""
        
        # Start with basic structure
        # Ensure primary diagnosis includes evidence
        primary = diagnostic_data.get("primary_diagnosis", {})
        if primary and "evidence" not in primary:
            primary["evidence"] = diagnostic_data.get("key_evidence", [])[:3]
        
        combined = {
            "diagnostic_landscape": {
                "primary_diagnosis": primary,
                "strong_alternatives": [],
                "alternatives": [],
                "minority_opinions": bias_data.get("minority_opinions", []),
                "all_alternative_diagnoses": diagnostic_data.get("differential_diagnoses", [])
            },
            "management_strategies": {
                "immediate_actions": [
                    {"action": action, "consensus_percentage": 0, "urgency": "High"}
                    for action in management_data.get("immediate_actions", [])
                ],
                "differential_testing": [
                    {"test": test, "purpose": "Diagnostic confirmation"}
                    for test in management_data.get("critical_tests", [])
                ],
                "medications": management_data.get("medications", [])
            },
            "critical_decision_points": management_data.get("decision_points", []),
            "ai_model_bias_analysis": {
                "geographic_bias": bias_data.get("geographic_bias", {}),
                "training_bias": bias_data.get("training_bias", {}),
                "consensus_strength": bias_data.get("consensus_strength", "Unknown")
            },
            "evidence_synthesis": {
                "key_clinical_findings": [
                    {"finding": finding, "diagnostic_significance": "High"}
                    for finding in diagnostic_data.get("key_evidence", [])
                ],
                "symptom_diagnosis_matrix": diagnostic_data.get("symptom_diagnosis_matrix", {
                    "symptoms": [],
                    "diagnoses": [],
                    "correlations": []
                })
            },
            "clinical_decision_tree": {
                "initial_assessment": "Evaluate presenting symptoms",
                "diagnostic_tests": management_data.get("critical_tests", []),
                "decision_points": management_data.get("decision_points", [])
            },
            "primary_diagnosis_summaries": self._create_primary_diagnosis_summary_from_split(
                diagnostic_data, management_data, ensemble_results
            ),
            "quality_metrics": {
                "total_models_analyzed": len(ensemble_results.get("model_responses", [])),
                "consensus_strength": bias_data.get("consensus_strength", "Unknown")
            }
        }
        
        # Process differential diagnoses into categories (increased to 10)
        differentials = diagnostic_data.get("differential_diagnoses", [])
        for i, diag in enumerate(differentials[:10]):  # Limit to 10 total
            if i < 3:  # First 3 as strong alternatives
                combined["diagnostic_landscape"]["strong_alternatives"].append(diag)
            elif i < 7:  # Next 4 as alternatives
                combined["diagnostic_landscape"]["alternatives"].append(diag)
            # All are in all_alternative_diagnoses already
        
        return combined
    
    def _create_primary_diagnosis_summary_from_split(self, diagnostic_data: Dict, 
                                                    management_data: Dict, 
                                                    ensemble_results: Dict) -> Dict:
        """
        Create primary diagnosis summaries from split orchestrator data
        """
        primary = diagnostic_data.get("primary_diagnosis", {})
        if not primary:
            return {}
        
        return {
            "key_clinical_findings": [
                {
                    "finding": finding,
                    "supporting_evidence": "Clinical presentation",
                    "model_support": len(primary.get("supporting_models", [])),
                    "reasoning": "Key diagnostic indicator"
                }
                for finding in diagnostic_data.get("key_evidence", [])[:5]
            ],
            "recommended_tests": [
                {
                    "test_name": test,
                    "test_type": "Laboratory",
                    "rationale": "Diagnostic confirmation",
                    "priority": "Urgent",
                    "model_support": len(ensemble_results.get("model_responses", [])) // 2,
                    "reasoning": "Essential for diagnosis"
                }
                for test in management_data.get("critical_tests", [])[:5]
            ],
            "immediate_management": [
                {
                    "intervention": action,
                    "category": "Medical",
                    "urgency": "Immediate",
                    "model_support": len(ensemble_results.get("model_responses", [])) // 2,
                    "reasoning": "Critical intervention"
                }
                for action in management_data.get("immediate_actions", [])[:5]
            ],
            "medications": [
                {
                    "medication_name": med.get("medication_name", med.get("name", "Not specified")),
                    "dosage": med.get("dosage", "As indicated"),
                    "route": med.get("route", "Oral"),
                    "frequency": med.get("frequency", "Daily"),
                    "duration": med.get("duration", "As directed"),
                    "indication": med.get("indication", "Treatment"),
                    "model_support": len(ensemble_results.get("model_responses", [])) // 3,
                    "reasoning": med.get("indication", "Clinical indication")
                }
                for med in management_data.get("medications", [])[:5]
            ]
        }
    
    def _convert_simplified_to_full(self, simplified: Dict, ensemble_results: Dict) -> Dict:
        """
        Convert simplified orchestrator response to full structure
        """
        # Build full structure from simplified response
        full_analysis = {
            "diagnostic_landscape": {
                "primary_diagnosis": simplified.get("primary_diagnosis", {}),
                "strong_alternatives": [],
                "alternatives": [],
                "minority_opinions": [],
                "all_alternative_diagnoses": []
            },
            "management_strategies": {
                "immediate_actions": [
                    {"action": action, "consensus_percentage": 0, "urgency": "High"}
                    for action in simplified.get("immediate_actions", [])
                ],
                "differential_testing": [
                    {"test": test, "purpose": "Diagnostic confirmation"}
                    for test in simplified.get("critical_tests", [])
                ]
            },
            "critical_decision_points": simplified.get("decision_points", []),
            "evidence_synthesis": {
                "key_clinical_findings": [
                    {"finding": finding, "diagnostic_significance": "High"}
                    for finding in simplified.get("key_evidence", [])
                ]
            },
            "clinical_decision_tree": {},
            "primary_diagnosis_summaries": {},
            "quality_metrics": {}
        }
        
        # Process differential diagnoses
        for diff in simplified.get("differential_diagnoses", []):
            # Calculate number of supporting models from frequency or percentage
            frequency = diff.get("frequency", 0)
            percentage = diff.get("percentage", 0)
            total_models = simplified.get("primary_diagnosis", {}).get("supporting_models", [])
            
            # If we have frequency, use it; otherwise calculate from percentage
            if frequency > 0:
                num_models = frequency
            elif percentage > 0 and len(ensemble_results.get("model_responses", [])) > 0:
                total = len(ensemble_results.get("model_responses", []))
                num_models = max(1, int((percentage / 100) * total))
            else:
                num_models = 0
            
            # Create mock supporting models list (since simplified doesn't include actual names)
            supporting_models = [f"Model_{i+1}" for i in range(num_models)]
            
            diagnosis_entry = {
                "name": diff.get("name", ""),
                "icd10_code": diff.get("icd_code", ""),
                "agreement_percentage": diff.get("percentage", 0),
                "supporting_models": supporting_models,
                "frequency": frequency if frequency > 0 else num_models
            }
            
            # Categorize based on percentage
            percentage = diff.get("percentage", 0)
            if percentage >= 30:
                full_analysis["diagnostic_landscape"]["strong_alternatives"].append(diagnosis_entry)
            elif percentage >= 10:
                full_analysis["diagnostic_landscape"]["alternatives"].append(diagnosis_entry)
            else:
                full_analysis["diagnostic_landscape"]["minority_opinions"].append(diagnosis_entry)
            
            # Add to all_alternative_diagnoses
            full_analysis["diagnostic_landscape"]["all_alternative_diagnoses"].append(diagnosis_entry)
        
        return full_analysis
    
    def _validate_and_enhance(self, analysis: Dict, ensemble_results: Dict) -> Dict:
        """
        Validate and enhance the orchestrator's analysis
        
        Args:
            analysis: The parsed analysis from orchestrator
            ensemble_results: Original ensemble results
            
        Returns:
            Validated and enhanced analysis
        """
        # Check if this is a simplified response (has differential_diagnoses at root)
        if "differential_diagnoses" in analysis and "diagnostic_landscape" not in analysis:
            print("  🔄 Converting simplified response to full structure")
            analysis = self._convert_simplified_to_full(analysis, ensemble_results)
        
        # Ensure all required sections exist
        required_sections = [
            "diagnostic_landscape",
            "management_strategies", 
            "critical_decision_points",
            "ai_model_bias_analysis",
            "evidence_synthesis",
            "clinical_decision_tree",
            "primary_diagnosis_summaries",
            "quality_metrics"
        ]
        
        for section in required_sections:
            if section not in analysis:
                analysis[section] = {}
                
        # Add metadata
        analysis["metadata"] = {
            "analysis_timestamp": datetime.now().isoformat(),
            "orchestrator_model": self.orchestrator_model,
            "case_id": ensemble_results.get("case_id", "unknown"),
            "case_title": ensemble_results.get("case_title", "unknown")
        }
        
        # Validate quality metrics
        if "quality_metrics" in analysis:
            metrics = analysis["quality_metrics"]
            if "total_models_analyzed" not in metrics:
                metrics["total_models_analyzed"] = len(ensemble_results.get("model_responses", []))
            if "successful_responses" not in metrics:
                successful = sum(1 for r in ensemble_results.get("model_responses", []) 
                               if r.get("response") and not r.get("error"))
                metrics["successful_responses"] = successful
        
        # Apply consistent categorization rules to ensure web interface compatibility
        if "diagnostic_landscape" in analysis:
            from ..utils.diagnosis_categorizer import apply_web_interface_categorization_rules, log_categorization_debug
            
            # Get the landscape reference
            landscape = analysis["diagnostic_landscape"]
            
            # If primary diagnosis is missing, fill from ensemble data
            if not landscape.get("primary_diagnosis") or landscape.get("primary_diagnosis") is None:
                ensemble_landscape = ensemble_results.get("diagnostic_landscape", {})
                if ensemble_landscape.get("primary_diagnosis"):
                    landscape["primary_diagnosis"] = ensemble_landscape["primary_diagnosis"]
                    print(f"  ✅ Restored primary diagnosis from ensemble: {landscape['primary_diagnosis'].get('name')}")
            
            # If other key fields are empty, fill from ensemble
            if not landscape.get("strong_alternatives"):
                landscape["strong_alternatives"] = ensemble_results.get("diagnostic_landscape", {}).get("strong_alternatives", [])
            if not landscape.get("alternatives"):
                landscape["alternatives"] = ensemble_results.get("diagnostic_landscape", {}).get("alternatives", [])
            if not landscape.get("minority_opinions"):
                landscape["minority_opinions"] = ensemble_results.get("diagnostic_landscape", {}).get("minority_opinions", [])
            
            analysis["diagnostic_landscape"] = apply_web_interface_categorization_rules(landscape)
            log_categorization_debug(analysis["diagnostic_landscape"], "Enhanced Analysis")
            
            # Check if all_alternative_diagnoses exists at root level (from orchestrator response)
            if "all_alternative_diagnoses" in analysis and analysis["all_alternative_diagnoses"]:
                # Move it to diagnostic_landscape with proper structure
                root_alts = analysis["all_alternative_diagnoses"]
                landscape["all_alternative_diagnoses"] = root_alts
                print(f"  ✅ Moved {len(root_alts)} alternative diagnoses to diagnostic_landscape")
                
                # Calculate percentages based on total models
                total_models = len(ensemble_results.get("model_responses", []))
                for alt in landscape["all_alternative_diagnoses"]:
                    if isinstance(alt, dict):
                        # Add percentage if frequency is available
                        if "frequency" in alt and total_models > 0:
                            alt["percentage"] = round((alt["frequency"] / total_models) * 100, 1)
            else:
                # Build all_alternative_diagnoses list combining all non-primary diagnoses
                all_alternatives = []
                
                # Add strong alternatives
                for alt in landscape.get("strong_alternatives", []):
                    if isinstance(alt, dict) and alt not in all_alternatives:
                        all_alternatives.append(alt)
                    elif isinstance(alt, str):
                        all_alternatives.append({"name": alt})
                
                # Add alternatives
                for alt in landscape.get("alternatives", []):
                    if isinstance(alt, dict) and alt not in all_alternatives:
                        all_alternatives.append(alt)
                    elif isinstance(alt, str) and not any(a.get("name") == alt for a in all_alternatives):
                        all_alternatives.append({"name": alt})
                
                # Add minority opinions
                for opinion in landscape.get("minority_opinions", []):
                    if isinstance(opinion, dict) and opinion not in all_alternatives:
                        all_alternatives.append(opinion)
                    elif isinstance(opinion, str) and not any(a.get("name") == opinion for a in all_alternatives):
                        all_alternatives.append({"name": opinion})
                
                # Set the all_alternative_diagnoses field
                analysis["diagnostic_landscape"]["all_alternative_diagnoses"] = all_alternatives
                print(f"  ✅ Built all_alternative_diagnoses with {len(all_alternatives)} items")
        
        # Fill evidence_synthesis if empty
        if not analysis.get("evidence_synthesis") or len(analysis.get("evidence_synthesis", {})) == 0:
            # Use data from ensemble if available
            if "evidence_synthesis" in ensemble_results:
                analysis["evidence_synthesis"] = ensemble_results["evidence_synthesis"]
            else:
                # Create basic evidence synthesis from model responses
                analysis["evidence_synthesis"] = self._create_basic_evidence_synthesis(ensemble_results)
            print("  ✅ Populated evidence_synthesis from ensemble data")
        
        # Fill clinical_decision_tree if empty
        if not analysis.get("clinical_decision_tree") or len(analysis.get("clinical_decision_tree", {})) == 0:
            if "decision_tree" in ensemble_results:
                analysis["clinical_decision_tree"] = ensemble_results["decision_tree"]
            else:
                # Create basic decision tree
                analysis["clinical_decision_tree"] = {
                    "initial_assessment": "Evaluate presenting symptoms",
                    "diagnostic_tests": [],
                    "decision_points": []
                }
            print("  ✅ Populated clinical_decision_tree")
        
        # Fill primary_diagnosis_summaries if empty
        if not analysis.get("primary_diagnosis_summaries") or len(analysis.get("primary_diagnosis_summaries", {})) == 0:
            primary = analysis.get("diagnostic_landscape", {}).get("primary_diagnosis", {})
            if primary:
                analysis["primary_diagnosis_summaries"] = {
                    primary.get("name", "Unknown"): {
                        "supporting_models": primary.get("models", []),
                        "confidence": primary.get("confidence", "Unknown"),
                        "key_evidence": primary.get("evidence", [])
                    }
                }
            print("  ✅ Created primary_diagnosis_summaries")
        
        # Remove case_content from output to save space
        if "case_content" in analysis:
            del analysis["case_content"]
            print("  📉 Removed case_content from output to save space")
                
        return analysis
        
    def _create_basic_evidence_synthesis(self, ensemble_results: Dict) -> Dict:
        """
        Create basic evidence synthesis from ensemble results
        """
        # Extract symptoms and diagnoses for matrix
        symptoms = set()
        diagnoses = []
        
        # Get primary diagnosis
        primary = ensemble_results.get("diagnostic_landscape", {}).get("primary_diagnosis", {})
        if primary:
            diagnoses.append(primary.get("name", "Unknown"))
        
        # Get top alternatives
        for alt in ensemble_results.get("diagnostic_landscape", {}).get("strong_alternatives", [])[:3]:
            if isinstance(alt, dict):
                diagnoses.append(alt.get("name", ""))
            else:
                diagnoses.append(str(alt))
        
        # Extract symptoms from model responses
        for response in ensemble_results.get("model_responses", [])[:5]:
            if response.get("response"):
                try:
                    import json
                    resp_data = json.loads(response["response"]) if isinstance(response["response"], str) else response["response"]
                    
                    # Look for symptoms/findings
                    if "key_findings" in resp_data:
                        for finding in resp_data["key_findings"][:3]:
                            if isinstance(finding, str):
                                symptoms.add(finding)
                                
                except (json.JSONDecodeError, TypeError):
                    continue
        
        symptoms = list(symptoms)[:5]
        
        return {
            "symptom_diagnosis_matrix": {
                "symptoms": symptoms,
                "diagnoses": diagnoses[:4],
                "correlations": []
            },
            "key_clinical_findings": [
                {
                    "finding": symptom,
                    "diagnostic_significance": "High",
                    "mentioned_by_models": 1
                } for symptom in symptoms[:3]
            ],
            "diagnostic_certainty": {
                "high_confidence_findings": symptoms[:2],
                "moderate_confidence_findings": symptoms[2:4],
                "areas_of_uncertainty": ["Differential diagnosis specificity", "Long-term prognosis"]
            }
        }
    
    def _create_primary_diagnosis_summary(self, primary_diagnosis: Dict, ensemble_results: Dict) -> Dict:
        """
        Create a clinical summary for the primary diagnosis
        """
        diag_name = primary_diagnosis.get("name", "Unknown")
        
        # Extract key findings from model responses
        key_findings = []
        tests = []
        management = []
        
        # Parse model responses for clinical data
        for response in ensemble_results.get("model_responses", [])[:5]:
            if response.get("response"):
                try:
                    # Try to parse as JSON
                    import json
                    resp_data = json.loads(response["response"]) if isinstance(response["response"], str) else response["response"]
                    
                    # Extract findings
                    if "key_findings" in resp_data:
                        key_findings.extend(resp_data["key_findings"][:2])
                    
                    # Extract tests
                    if "tests" in resp_data:
                        for test in resp_data["tests"][:2]:
                            if isinstance(test, str):
                                tests.append(test)
                            elif isinstance(test, dict):
                                tests.append(test.get("test", test.get("name", str(test))))
                    elif "diagnostic_tests" in resp_data:
                        for test in resp_data["diagnostic_tests"][:2]:
                            if isinstance(test, str):
                                tests.append(test)
                            elif isinstance(test, dict):
                                tests.append(test.get("test", test.get("name", str(test))))
                    
                    # Extract management
                    if "management" in resp_data:
                        mgmt = resp_data["management"]
                        if isinstance(mgmt, dict):
                            if "immediate" in mgmt:
                                management.extend(mgmt["immediate"][:2])
                        elif isinstance(mgmt, list):
                            management.extend(mgmt[:2])
                            
                except (json.JSONDecodeError, TypeError):
                    continue
        
        # Remove duplicates
        key_findings = list(dict.fromkeys(key_findings))[:5]
        tests = list(dict.fromkeys(tests))[:5]
        management = list(dict.fromkeys(management))[:5]
        
        return {
            diag_name: {
                "supporting_models": primary_diagnosis.get("supporting_models", []),
                "confidence": primary_diagnosis.get("confidence", "Moderate"),
                "key_evidence": primary_diagnosis.get("evidence", key_findings),
                "diagnostic_tests": tests if tests else ["Complete blood count", "Metabolic panel", "Urinalysis"],
                "immediate_actions": management if management else ["Monitor vital signs", "Symptom documentation"],
                "icd_code": primary_diagnosis.get("icd10_code", self._get_icd_code(diag_name))
            }
        }
    
    def _get_icd_code(self, diagnosis_name: str) -> str:
        """
        Get ICD-10 code for a diagnosis name
        """
        # Common ICD-10 codes lookup table
        icd_codes = {
            # Kidney/Nephrology
            "iga nephropathy": "N02.8",
            "lupus nephritis": "M32.14",
            "systemic lupus erythematosus": "M32.9",
            "sle": "M32.9",
            "membranoproliferative glomerulonephritis": "N03.5",
            "mpgn": "N03.5",
            "post-infectious glomerulonephritis": "N05.9",
            "acute interstitial nephritis": "N10",
            "anca-associated vasculitis": "M31.7",
            "anca vasculitis": "M31.7",
            "anti-gbm disease": "M31.0",
            "goodpasture syndrome": "M31.0",
            "alport syndrome": "Q87.81",
            "thin basement membrane disease": "N02.9",
            "henoch-schönlein purpura": "D69.0",
            "hsp nephritis": "D69.0",
            "focal segmental glomerulosclerosis": "N04.1",
            "fsgs": "N04.1",
            "minimal change disease": "N04.0",
            "membranous nephropathy": "N04.2",
            "chronic kidney disease": "N18.9",
            "ckd": "N18.9",
            "acute kidney injury": "N17.9",
            "aki": "N17.9",
            "pyelonephritis": "N10",
            "acute pyelonephritis": "N10",
            "glomerulonephritis": "N05.9",
            
            # Inflammatory/Genetic
            "familial mediterranean fever": "E85.0",
            "fmf": "E85.0",
            "inflammatory bowel disease": "K50.9",
            "ibd": "K50.9",
            "crohn's disease": "K50.9",
            "ulcerative colitis": "K51.9",
            "adult still's disease": "M06.1",
            "behçet's disease": "M35.2",
            "behcet's disease": "M35.2",
            "traps": "M04.1",
            
            # Infections
            "urinary tract infection": "N39.0",
            "uti": "N39.0",
            "recurrent urinary tract infection": "N39.0",
            "sepsis": "A41.9",
            "tuberculosis": "A15.9",
            
            # Other
            "hypertension": "I10",
            "diabetes mellitus": "E11.9",
            "anemia": "D64.9",
        }
        
        # Normalize the diagnosis name
        normalized = diagnosis_name.lower().strip()
        
        # Direct lookup
        if normalized in icd_codes:
            return icd_codes[normalized]
        
        # Partial match
        for key, code in icd_codes.items():
            if key in normalized or normalized in key:
                return code
        
        # Return empty string if not found
        return ""
    
    def _fallback_extraction(self, ensemble_results: Dict) -> Dict:
        """
        Fallback extraction when orchestrator fails
        
        Args:
            ensemble_results: The ensemble analysis results
            
        Returns:
            Basic extracted analysis
        """
        logger.info("Using fallback extraction method")
        
        # Use consistent categorization logic
        from ..utils.diagnosis_categorizer import extract_diagnoses_from_ensemble_results, log_categorization_debug
        
        categorized_diagnoses = extract_diagnoses_from_ensemble_results(ensemble_results)
        log_categorization_debug(categorized_diagnoses, "Fallback Extraction")
        
        # Build diagnostic landscape with consistent categorization
        primary_diagnosis = categorized_diagnoses.get("primary_diagnosis")
        if not primary_diagnosis:
            primary_diagnosis = {
                "name": ensemble_results.get("consensus_analysis", {}).get("primary_diagnosis", "Unknown"),
                "agreement_percentage": 0,
                "supporting_models": [],
                "evidence": [],
                "confidence": "Low"
            }
        else:
            # Enhance primary diagnosis with missing fields and ICD code
            primary_name = primary_diagnosis.get("name", "")
            if primary_name and not primary_diagnosis.get("icd10_code"):
                primary_diagnosis["icd10_code"] = self._get_icd_code(primary_name)
            
            primary_diagnosis.update({
                "supporting_models": primary_diagnosis.get("supporting_models", []),
                "evidence": primary_diagnosis.get("evidence", []),
                "confidence": primary_diagnosis.get("confidence", "Low")
            })
        
        # Collect ALL diagnoses from all categories
        all_diagnoses_list = []
        
        # Add strong alternatives
        for diag in categorized_diagnoses.get("strong_alternatives", []):
            diag_name = diag.get("name", "")
            icd_code = diag.get("icd10_code", "") or self._get_icd_code(diag_name)
            all_diagnoses_list.append({
                "name": diag_name,
                "icd10_code": icd_code,
                "supporting_models": diag.get("supporting_models", []),
                "count": len(diag.get("supporting_models", [])),
                "percentage": diag.get("agreement_percentage", 0),
                "evidence": diag.get("evidence", [])
            })
        
        # Add alternatives
        for diag in categorized_diagnoses.get("alternatives", []):
            diag_name = diag.get("name", "")
            icd_code = diag.get("icd10_code", "") or self._get_icd_code(diag_name)
            all_diagnoses_list.append({
                "name": diag_name,
                "icd10_code": icd_code,
                "supporting_models": diag.get("supporting_models", []),
                "count": len(diag.get("supporting_models", [])),
                "percentage": diag.get("agreement_percentage", 0),
                "evidence": diag.get("evidence", [])
            })
        
        # Add minority opinions
        for diag in categorized_diagnoses.get("minority_opinions", []):
            diag_name = diag.get("name", "")
            icd_code = diag.get("icd10_code", "") or self._get_icd_code(diag_name)
            all_diagnoses_list.append({
                "name": diag_name,
                "icd10_code": icd_code,
                "supporting_models": diag.get("supporting_models", []),
                "count": len(diag.get("supporting_models", [])),
                "percentage": diag.get("agreement_percentage", 0),
                "evidence": diag.get("evidence", [])
            })
        
        # Basic extraction logic
        analysis = {
            "diagnostic_landscape": {
                "primary_diagnosis": primary_diagnosis,
                "strong_alternatives": categorized_diagnoses.get("strong_alternatives", []),
                "alternatives": categorized_diagnoses.get("alternatives", []),
                "minority_opinions": categorized_diagnoses.get("minority_opinions", []),
                "all_alternative_diagnoses": all_diagnoses_list
            },
            "management_strategies": {
                "immediate_actions": [],
                "differential_testing": [],
                "treatment_options": [],
                "specialist_consultations": []
            },
            "critical_decision_points": [],
            "ai_model_bias_analysis": {
                "primary_diagnosis_bias_factors": {
                    "cultural_bias": {
                        "description": "Fallback analysis - limited bias assessment available",
                        "affected_models": [],
                        "bias_impact": "Low",
                        "specific_concerns": []
                    },
                    "geographic_bias": {
                        "description": "Geographic bias analysis not available in fallback mode",
                        "western_models_pattern": "Unknown",
                        "asian_models_pattern": "Unknown", 
                        "european_models_pattern": "Unknown",
                        "impact_on_diagnosis": "Cannot assess without orchestrator"
                    },
                    "training_data_bias": {
                        "description": "Training data bias analysis requires orchestrator",
                        "newer_models_advantage": "Unknown",
                        "older_models_limitation": "Unknown",
                        "knowledge_gaps": []
                    }
                },
                "alternative_diagnoses_bias": {
                    "missed_diagnoses_due_to_bias": [],
                    "overrepresented_diagnoses": []
                },
                "model_architecture_patterns": {
                    "multimodal_vs_text_only": {
                        "diagnostic_differences": "Unknown",
                        "strengths_limitations": "Unknown"
                    },
                    "model_size_impact": {
                        "large_model_patterns": "Unknown",
                        "small_model_patterns": "Unknown",
                        "diagnostic_accuracy_correlation": "Unknown"
                    }
                },
                "bias_mitigation_recommendations": []
            },
            "evidence_synthesis": {
                "symptom_diagnosis_matrix": {
                    "symptoms": [],
                    "diagnoses": [],
                    "correlations": []
                },
                "key_clinical_findings": [],
                "diagnostic_certainty": {
                    "high_confidence_findings": [],
                    "moderate_confidence_findings": [],
                    "areas_of_uncertainty": []
                }
            },
            "clinical_decision_tree": {
                "initial_test": "Genetic testing",
                "branches": []
            },
            "primary_diagnosis_summaries": self._create_primary_diagnosis_summary(
                primary_diagnosis, 
                ensemble_results
            ),
            "quality_metrics": {
                "total_models_analyzed": len(ensemble_results.get("model_responses", [])),
                "successful_responses": sum(1 for r in ensemble_results.get("model_responses", []) 
                                          if r.get("response")),
                "consensus_strength": "Weak",
                "diagnostic_diversity_index": 0,
                "confidence_in_primary_diagnosis": 0
            },
            "metadata": {
                "analysis_timestamp": datetime.now().isoformat(),
                "orchestrator_model": "fallback",
                "case_id": ensemble_results.get("case_id", "unknown"),
                "case_title": ensemble_results.get("case_title", "unknown")
            }
        }
        
        return analysis
        
    def generate_orchestrated_report(self, 
                                    ensemble_results: Dict,
                                    output_format: str = 'json',
                                    output_file: Optional[str] = None) -> str:
        """
        Generate an orchestrated report using LLM analysis
        
        Args:
            ensemble_results: Results from ensemble analysis
            output_format: 'json', 'pdf', or 'markdown'  
            output_file: Output file path
            
        Returns:
            Path to generated report
        """
        # Run orchestration
        analysis = self.orchestrate_analysis(ensemble_results)
        
        # Generate output based on format
        if not output_file:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            ext = 'json' if output_format == 'json' else 'md' if output_format == 'markdown' else 'pdf'
            output_file = f"orchestrated_report_{timestamp}.{ext}"
            
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        if output_format == 'json':
            with open(output_path, 'w') as f:
                json.dump(analysis, f, indent=2)
                
        elif output_format == 'markdown':
            markdown = self._convert_to_markdown(analysis)
            with open(output_path, 'w') as f:
                f.write(markdown)
                
        elif output_format == 'pdf':
            # Import comprehensive report generator and use orchestrated data
            from .comprehensive_report import ComprehensiveReportGenerator
            
            report_gen = ComprehensiveReportGenerator()
            # Pass the orchestrated analysis to the PDF generator
            return report_gen.generate_orchestrated_pdf(analysis, ensemble_results, output_file)
            
        return str(output_path)
        
    def _convert_to_markdown(self, analysis: Dict) -> str:
        """
        Convert orchestrated analysis to markdown format
        
        Args:
            analysis: The orchestrated analysis
            
        Returns:
            Markdown formatted report
        """
        lines = []
        
        # Header
        lines.append("# MEDLEY Orchestrated Clinical Decision Report\n")
        
        metadata = analysis.get("metadata", {})
        lines.append(f"**Case**: {metadata.get('case_title', 'Unknown')}")
        lines.append(f"**Analysis Date**: {metadata.get('analysis_timestamp', 'Unknown')}")
        lines.append(f"**Orchestrator**: {metadata.get('orchestrator_model', 'Unknown')}\n")
        
        # Diagnostic Landscape
        lines.append("## Diagnostic Landscape\n")
        
        diag_landscape = analysis.get("diagnostic_landscape", {})
        primary = diag_landscape.get("primary_diagnosis", {})
        
        if primary:
            lines.append(f"### Primary Diagnosis: {primary.get('name', 'Unknown')}")
            lines.append(f"- **Agreement**: {primary.get('agreement_percentage', 0):.1f}%")
            lines.append(f"- **Confidence**: {primary.get('confidence', 'Unknown')}")
            lines.append(f"- **Evidence**: {', '.join(primary.get('evidence', []))}")
            lines.append(f"- **Supporting Models**: {', '.join(primary.get('supporting_models', []))}\n")
            
        # Strong Alternatives
        alts = diag_landscape.get("strong_alternatives", [])
        if alts:
            lines.append("### Strong Alternative Diagnoses")
            for alt in alts:
                lines.append(f"- **{alt.get('name', 'Unknown')}** ({alt.get('agreement_percentage', 0):.1f}%)")
                lines.append(f"  - Evidence: {', '.join(alt.get('evidence', []))}")
            lines.append("")
            
        # Management Strategies
        lines.append("## Management Strategies\n")
        
        mgmt = analysis.get("management_strategies", {})
        
        # Immediate Actions
        immediate = mgmt.get("immediate_actions", [])
        if immediate:
            lines.append("### Immediate Actions")
            for action in immediate:
                lines.append(f"- [ ] {action.get('action', 'Unknown')}")
                lines.append(f"  - Consensus: {action.get('consensus_percentage', 0):.1f}%")
                lines.append(f"  - Urgency: {action.get('urgency', 'Unknown')}")
            lines.append("")
            
        # Differential Testing
        testing = mgmt.get("differential_testing", [])
        if testing:
            lines.append("### Differential Testing")
            for test in testing:
                lines.append(f"- **{test.get('test', 'Unknown')}**")
                lines.append(f"  - Purpose: {test.get('purpose', 'Unknown')}")
                lines.append(f"  - Rules out: {', '.join(test.get('conditions_to_rule_out', []))}")
            lines.append("")
            
        # Critical Decision Points
        decisions = analysis.get("critical_decision_points", [])
        if decisions:
            lines.append("## Critical Decision Points\n")
            for decision in decisions:
                lines.append(f"### {decision.get('topic', 'Unknown')}")
                lines.append(f"{decision.get('divergence_description', '')}")
                
                opt1 = decision.get("option_1", {})
                opt2 = decision.get("option_2", {})
                
                lines.append(f"\n**Option 1**: {opt1.get('approach', 'Unknown')}")
                lines.append(f"- Support: {opt1.get('percentage', 0):.1f}%")
                lines.append(f"- Rationale: {opt1.get('rationale', 'Unknown')}")
                
                lines.append(f"\n**Option 2**: {opt2.get('approach', 'Unknown')}")
                lines.append(f"- Support: {opt2.get('percentage', 0):.1f}%")
                lines.append(f"- Rationale: {opt2.get('rationale', 'Unknown')}")
                lines.append("")
                
        # Quality Metrics
        metrics = analysis.get("quality_metrics", {})
        if metrics:
            lines.append("## Analysis Quality Metrics\n")
            lines.append(f"- **Models Analyzed**: {metrics.get('total_models_analyzed', 0)}")
            lines.append(f"- **Successful Responses**: {metrics.get('successful_responses', 0)}")
            lines.append(f"- **Consensus Strength**: {metrics.get('consensus_strength', 'Unknown')}")
            lines.append(f"- **Diagnostic Confidence**: {metrics.get('confidence_in_primary_diagnosis', 0):.1f}%\n")
            
        # Footer
        lines.append("---")
        lines.append("*Report generated by Medley Medical AI Ensemble System*")
        lines.append("*Developed by Farhad Abtahi - SMAILE at Karolinska Institutet*")
        
        return '\n'.join(lines)