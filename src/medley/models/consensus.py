"""
Consensus Engine for analyzing agreement across multiple model responses
"""

from typing import List, Dict, Any, Optional, Tuple
from collections import Counter
from dataclasses import dataclass, asdict
from datetime import datetime

@dataclass
class ConsensusResult:
    """Structured consensus analysis result"""
    total_models: int
    responding_models: int
    consensus_level: str  # "Strong", "Partial", "None"
    primary_diagnosis: Optional[str]
    primary_confidence: float
    alternative_diagnoses: List[Dict[str, Any]]
    minority_opinions: List[Dict[str, Any]]
    agreement_scores: Dict[str, float]
    geographic_patterns: Dict[str, List[str]]
    action_required: str
    clinical_recommendation: str
    bias_considerations: List[str]
    
    def to_dict(self) -> Dict:
        return asdict(self)

class ConsensusEngine:
    """Analyzes consensus across multiple diagnostic responses"""
    
    def __init__(self, config=None):
        self.config = config
        self.diagnosis_standardization = {
            # FMF variations
            "fmf": "Familial Mediterranean Fever",
            "familial mediterranean fever": "Familial Mediterranean Fever",
            "familial mediterranean fever (fmf)": "Familial Mediterranean Fever",
            "mediterranean fever": "Familial Mediterranean Fever",
            
            # Periodic fever variations
            "periodic fever": "Periodic Fever Syndrome",
            "periodic fever syndrome": "Periodic Fever Syndrome",
            "hereditary periodic fever": "Periodic Fever Syndrome",
            
            # Autoimmune variations
            "sle": "Systemic Lupus Erythematosus",
            "lupus": "Systemic Lupus Erythematosus",
            "systemic lupus": "Systemic Lupus Erythematosus",
            
            # Still's disease
            "still disease": "Adult Still's Disease",
            "adult still": "Adult Still's Disease",
            "adult still's disease": "Adult Still's Disease",
            
            # IBD variations
            "ibd": "Inflammatory Bowel Disease",
            "crohn": "Crohn's Disease",
            "ulcerative colitis": "Ulcerative Colitis",
            
            # Behcet variations
            "behcet": "Behcet's Disease",
            "behcet's": "Behcet's Disease",
            "behcet disease": "Behcet's Disease",
        }
    
    def analyze_consensus(
        self,
        model_responses: List[Dict[str, Any]],
        parsed_responses: List[Dict[str, Any]]
    ) -> ConsensusResult:
        """
        Analyze consensus across multiple model responses
        
        Args:
            model_responses: Raw responses from models with metadata
            parsed_responses: Parsed diagnostic responses
            
        Returns:
            ConsensusResult with comprehensive analysis
        """
        
        # Filter successful responses
        successful_responses = [
            (model, parsed) 
            for model, parsed in zip(model_responses, parsed_responses)
            if not model.get('error') and parsed
        ]
        
        total_models = len(model_responses)
        responding_models = len(successful_responses)
        
        if responding_models == 0:
            return self._create_empty_consensus(total_models)
        
        # Analyze diagnoses
        diagnosis_analysis = self._analyze_diagnoses(successful_responses)
        
        # Determine consensus level
        consensus_level = self._determine_consensus_level(
            diagnosis_analysis['agreement_scores'],
            responding_models
        )
        
        # Get primary diagnosis
        primary = self._get_primary_diagnosis(diagnosis_analysis['diagnoses'])
        
        # Analyze geographic patterns
        geographic_patterns = self._analyze_geographic_patterns(
            successful_responses,
            diagnosis_analysis['diagnosis_by_model']
        )
        
        # Generate recommendations
        clinical_rec = self._generate_clinical_recommendation(
            primary,
            consensus_level,
            diagnosis_analysis
        )
        
        # Identify bias considerations
        bias_considerations = self._identify_bias_patterns(
            geographic_patterns,
            diagnosis_analysis,
            responding_models,
            total_models
        )
        
        return ConsensusResult(
            total_models=total_models,
            responding_models=responding_models,
            consensus_level=consensus_level,
            primary_diagnosis=primary['diagnosis'] if primary else None,
            primary_confidence=primary['confidence'] if primary else 0.0,
            alternative_diagnoses=diagnosis_analysis['alternatives'],
            minority_opinions=diagnosis_analysis['minority_opinions'],
            agreement_scores=diagnosis_analysis['agreement_scores'],
            geographic_patterns=geographic_patterns,
            action_required=self._determine_action_required(consensus_level),
            clinical_recommendation=clinical_rec,
            bias_considerations=bias_considerations
        )
    
    def _analyze_diagnoses(
        self,
        successful_responses: List[Tuple[Dict, Dict]]
    ) -> Dict[str, Any]:
        """Analyze all diagnoses from successful responses"""
        
        all_diagnoses = {}
        diagnosis_by_model = {}
        
        for model_resp, parsed_resp in successful_responses:
            model_name = model_resp.get('model_name', 'Unknown')
            model_origin = model_resp.get('origin', 'Unknown')
            diagnosis_by_model[model_name] = []
            
            # Track diagnoses already counted for this model
            model_diagnoses_seen = set()
            
            # Extract diagnoses from parsed response
            if hasattr(parsed_resp, 'differential_diagnoses') and parsed_resp.differential_diagnoses:
                for diag_entry in parsed_resp.differential_diagnoses:
                    diagnosis = diag_entry.get('diagnosis', '').strip()
                    if not diagnosis:
                        continue
                    
                    # Standardize diagnosis name
                    diagnosis_std = self._standardize_diagnosis(diagnosis)
                    
                    # Skip if it's not a valid medical diagnosis
                    if diagnosis_std is None:
                        continue
                    
                    # Skip if we've already counted this diagnosis for this model
                    if diagnosis_std in model_diagnoses_seen:
                        continue
                    model_diagnoses_seen.add(diagnosis_std)
                    
                    if diagnosis_std not in all_diagnoses:
                        all_diagnoses[diagnosis_std] = {
                            'count': 0,
                            'models': [],
                            'origins': [],
                            'reasoning': [],
                            'confidence_scores': []
                        }
                    
                    all_diagnoses[diagnosis_std]['count'] += 1
                    all_diagnoses[diagnosis_std]['models'].append(model_name)
                    all_diagnoses[diagnosis_std]['origins'].append(model_origin)
                    all_diagnoses[diagnosis_std]['reasoning'].append(
                        diag_entry.get('reasoning', '')
                    )
                    
                    diagnosis_by_model[model_name].append(diagnosis_std)
        
        # Calculate agreement scores
        total_responding = len(successful_responses)
        agreement_scores = {}
        diagnoses_list = []
        
        for diagnosis, info in all_diagnoses.items():
            agreement = info['count'] / total_responding
            agreement_scores[diagnosis] = agreement
            
            diagnoses_list.append({
                'diagnosis': diagnosis,
                'confidence': agreement,
                'model_count': info['count'],
                'supporting_models': info['models'],
                'origins': list(set(info['origins'])),
                'sample_reasoning': info['reasoning'][0] if info['reasoning'] else ""
            })
        
        # Sort by confidence
        diagnoses_list.sort(key=lambda x: x['confidence'], reverse=True)
        
        # Identify minority opinions (1-2 models only)
        minority_opinions = [
            d for d in diagnoses_list 
            if d['model_count'] <= 2 and d['model_count'] > 0
        ]
        
        # Get alternatives (exclude primary)
        alternatives = diagnoses_list[1:5] if len(diagnoses_list) > 1 else []
        
        return {
            'diagnoses': diagnoses_list,
            'alternatives': alternatives,
            'minority_opinions': minority_opinions,
            'agreement_scores': agreement_scores,
            'diagnosis_by_model': diagnosis_by_model
        }
    
    def _standardize_diagnosis(self, diagnosis: str) -> str:
        """Standardize diagnosis name for comparison"""
        
        diagnosis_lower = diagnosis.lower().strip()
        
        # Filter out non-medical metadata terms
        non_medical_terms = [
            "age", "sex", "gender", "nationality", "language", "history",
            "patient information", "case id", "title", "analysis",
            "presentation", "physical exam", "medical history",
            "chief complaint", "case", "patient", "information"
        ]
        
        # Check if this is a non-medical term
        for term in non_medical_terms:
            if diagnosis_lower == term or diagnosis_lower.startswith(term + ":"):
                return None  # This will be filtered out
        
        # Check if it's too long to be a diagnosis (likely a sentence)
        if len(diagnosis) > 100:
            # Try to extract a medical term from it
            medical_keywords = ["fever", "syndrome", "disease", "disorder", "arthritis"]
            for keyword in medical_keywords:
                if keyword in diagnosis_lower:
                    # Return a generic diagnosis based on the keyword
                    if "fever" in diagnosis_lower:
                        if "mediterranean" in diagnosis_lower:
                            return "Familial Mediterranean Fever"
                        else:
                            return "Periodic Fever Syndrome"
                    elif "arthritis" in diagnosis_lower:
                        return "Arthritis (Unspecified)"
                    else:
                        return keyword.title()
            return None  # Too long and no medical term found
        
        # Check standardization map
        for pattern, standard in self.diagnosis_standardization.items():
            if pattern in diagnosis_lower:
                return standard
        
        # Check for inflammatory conditions
        if "inflammatory" in diagnosis_lower:
            if "bowel" in diagnosis_lower:
                return "Inflammatory Bowel Disease"
            elif "cardiac" in diagnosis_lower or "heart" in diagnosis_lower:
                return "Inflammatory Cardiac Condition"
            else:
                return "Inflammatory Disorder (Unspecified)"
        
        # Default: capitalize properly
        return diagnosis.title()
    
    def _determine_consensus_level(
        self,
        agreement_scores: Dict[str, float],
        responding_models: int
    ) -> str:
        """Determine the level of consensus"""
        
        if not agreement_scores or responding_models == 0:
            return "None"
        
        max_agreement = max(agreement_scores.values())
        
        if max_agreement >= 0.75:
            return "Strong"
        elif max_agreement >= 0.5:
            return "Partial"
        else:
            return "None"
    
    def _get_primary_diagnosis(
        self,
        diagnoses: List[Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        """Get the primary diagnosis with highest agreement"""
        
        if not diagnoses:
            return None
        
        return diagnoses[0]
    
    def _analyze_geographic_patterns(
        self,
        successful_responses: List[Tuple[Dict, Dict]],
        diagnosis_by_model: Dict[str, List[str]]
    ) -> Dict[str, List[str]]:
        """Analyze diagnostic patterns by geographic origin"""
        
        patterns = {}
        
        for model_resp, _ in successful_responses:
            origin = model_resp.get('origin', 'Unknown')
            model_name = model_resp.get('model_name', 'Unknown')
            
            if origin not in patterns:
                patterns[origin] = []
            
            if model_name in diagnosis_by_model:
                patterns[origin].extend(diagnosis_by_model[model_name])
        
        # Get unique diagnoses per origin
        for origin in patterns:
            diagnoses = patterns[origin]
            if diagnoses:
                # Count frequency and get top 3
                counter = Counter(diagnoses)
                top_diagnoses = [diag for diag, _ in counter.most_common(3)]
                patterns[origin] = top_diagnoses
        
        return patterns
    
    def _generate_clinical_recommendation(
        self,
        primary: Optional[Dict[str, Any]],
        consensus_level: str,
        diagnosis_analysis: Dict[str, Any]
    ) -> str:
        """Generate clinical recommendation based on consensus"""
        
        if consensus_level == "Strong" and primary:
            return f"Strong consensus on {primary['diagnosis']}. Proceed with targeted testing and treatment."
        
        elif consensus_level == "Partial" and primary:
            alternatives = diagnosis_analysis.get('alternatives', [])
            alt_names = [alt['diagnosis'] for alt in alternatives[:2]]
            
            return (f"Partial consensus on {primary['diagnosis']}. "
                   f"Consider alternatives: {', '.join(alt_names)}. "
                   f"Additional testing recommended to differentiate.")
        
        else:
            minority = diagnosis_analysis.get('minority_opinions', [])
            if minority:
                minority_names = [m['diagnosis'] for m in minority[:2]]
                return (f"No clear consensus. Divergent opinions include: {', '.join(minority_names)}. "
                       f"Active clinical judgment and comprehensive testing required.")
            else:
                return "No consensus achieved. Comprehensive clinical evaluation required."
    
    def _determine_action_required(self, consensus_level: str) -> str:
        """Determine required clinical action based on consensus"""
        
        actions = {
            "Strong": "Proceed with consensus diagnosis and targeted testing",
            "Partial": "Additional differential testing recommended",
            "None": "Active clinical judgment and specialist consultation needed"
        }
        
        return actions.get(consensus_level, "Clinical evaluation required")
    
    def _identify_bias_patterns(
        self,
        geographic_patterns: Dict[str, List[str]],
        diagnosis_analysis: Dict[str, Any],
        responding_models: int,
        total_models: int
    ) -> List[str]:
        """Identify potential bias patterns in responses"""
        
        biases = []
        
        # Check response rate bias
        response_rate = responding_models / total_models if total_models > 0 else 0
        if response_rate < 0.5:
            biases.append(f"Low response rate ({responding_models}/{total_models}) may indicate model limitations")
        
        # Check geographic variation
        if len(geographic_patterns) > 1:
            origins = list(geographic_patterns.keys())
            diagnoses_vary = False
            
            # Compare diagnoses across origins
            for i, origin1 in enumerate(origins):
                for origin2 in origins[i+1:]:
                    diags1 = set(geographic_patterns.get(origin1, []))
                    diags2 = set(geographic_patterns.get(origin2, []))
                    
                    if diags1 and diags2 and diags1 != diags2:
                        diagnoses_vary = True
                        break
            
            if diagnoses_vary:
                biases.append("Geographic variation in diagnostic patterns detected")
        
        # Check for minority opinion importance
        minority = diagnosis_analysis.get('minority_opinions', [])
        if minority:
            # Check if minority includes region-specific diseases
            for opinion in minority:
                diag_lower = opinion['diagnosis'].lower()
                if any(term in diag_lower for term in ['mediterranean', 'familial', 'endemic']):
                    biases.append(f"Regional disease ({opinion['diagnosis']}) only recognized by minority")
        
        # Check for low overall agreement
        agreement_scores = diagnosis_analysis.get('agreement_scores', {})
        if agreement_scores:
            max_agreement = max(agreement_scores.values())
            if max_agreement < 0.5:
                biases.append("Low inter-model agreement suggests need for specialist input")
        
        return biases
    
    def analyze_consensus_with_ai(
        self,
        model_responses: List[Dict[str, Any]],
        parsed_responses: List[Dict[str, Any]],
        case_info: Dict[str, Any],
        consensus_model: str = "google/gemini-2.5-pro"
    ) -> ConsensusResult:
        """
        Analyze consensus using an AI model to synthesize all responses
        
        Args:
            model_responses: Raw responses from models with metadata
            parsed_responses: Parsed diagnostic responses
            case_info: Case information
            consensus_model: Model to use for AI consensus analysis
            
        Returns:
            ConsensusResult with AI-enhanced analysis
        """
        
        # First get statistical consensus
        statistical_consensus = self.analyze_consensus(model_responses, parsed_responses)
        
        # Filter successful responses
        successful_responses = [
            (model, parsed, raw) 
            for model, parsed, raw in zip(model_responses, parsed_responses, model_responses)
            if not model.get('error') and parsed
        ]
        
        if len(successful_responses) == 0:
            return statistical_consensus
        
        # Prepare prompt for AI consensus analysis
        prompt = self._create_ai_consensus_prompt(successful_responses, case_info, statistical_consensus)
        
        # Query consensus model
        try:
            from ..models.llm_manager import LLMManager
            from ..utils.config import ModelConfig
            
            if not self.config:
                from ..utils.config import Config
                self.config = Config()
            
            llm_manager = LLMManager(self.config)
            
            # Create model config for consensus model
            model_cfg = ModelConfig(
                name=consensus_model,
                model_id=consensus_model,
                provider="openrouter",
                max_tokens=8192,
                temperature=0.3  # Lower temperature for more consistent analysis
            )
            
            # Query with retries
            max_retries = 3
            for attempt in range(max_retries):
                response = llm_manager.query_model(model_cfg, prompt)
                
                if not response.error:
                    # Parse AI consensus response
                    ai_analysis = self._parse_ai_consensus(response.content, statistical_consensus)
                    return ai_analysis
                
                if attempt < max_retries - 1:
                    import time
                    time.sleep(5)
            
        except Exception as e:
            print(f"AI consensus analysis failed: {e}")
        
        # Fallback to statistical consensus
        return statistical_consensus
    
    def _create_ai_consensus_prompt(
        self, 
        successful_responses: List[Tuple],
        case_info: Dict[str, Any],
        statistical_consensus: ConsensusResult
    ) -> str:
        """Create prompt for AI consensus analysis"""
        
        prompt = """You are an expert medical AI consensus analyzer. Review the following diagnostic responses from multiple AI models for a medical case and provide a comprehensive consensus analysis.

**CASE PRESENTATION:**
{case_presentation}

**MODEL RESPONSES:**
{model_responses}

**STATISTICAL CONSENSUS:**
Primary Diagnosis: {primary_diagnosis} ({primary_confidence}% agreement)
Consensus Level: {consensus_level}
Total Models: {total_models}
Responding Models: {responding_models}

**YOUR TASK:**
Analyze all model responses and provide:

1. **PRIMARY CONSENSUS DIAGNOSIS**: The most clinically appropriate diagnosis based on ALL responses
2. **CONFIDENCE ASSESSMENT**: Your confidence in the primary diagnosis (0-100%)
3. **KEY ALTERNATIVE DIAGNOSES**: Up to 3 important alternatives to consider
4. **CRITICAL MINORITY OPINIONS**: Any important diagnoses mentioned by few models that shouldn't be ignored
5. **CLINICAL RECOMMENDATION**: Specific next steps based on the ensemble analysis
6. **BIAS CONSIDERATIONS**: Any geographic, demographic, or model-origin biases detected
7. **DIAGNOSTIC AGREEMENT PATTERN**: How models from different origins/backgrounds diagnosed differently

Format your response as:
PRIMARY_DIAGNOSIS: [diagnosis name]
CONFIDENCE: [percentage]
ALTERNATIVES: [diagnosis1], [diagnosis2], [diagnosis3]
MINORITY_OPINIONS: [important minority diagnoses]
CLINICAL_RECOMMENDATION: [specific actionable recommendation]
BIAS_PATTERNS: [detected biases]
GEOGRAPHIC_VARIATION: [patterns by model origin]
"""
        
        # Format case presentation
        case_presentation = f"""
Patient: {case_info.get('patient_info', 'Unknown')}
Presentation: {case_info.get('presentation', 'Unknown')}
Symptoms: {', '.join(case_info.get('symptoms', []))}
"""
        
        # Format model responses
        model_responses_text = ""
        for model, parsed, raw in successful_responses:
            model_name = model.get('model_name', 'Unknown')
            origin = model.get('origin', 'Unknown')
            
            diagnoses = []
            if hasattr(parsed, 'differential_diagnoses'):
                for diag in parsed.differential_diagnoses[:3]:
                    diagnoses.append(diag.get('diagnosis', 'Unknown'))
            
            model_responses_text += f"\n**{model_name} ({origin}):**\n"
            model_responses_text += f"Diagnoses: {', '.join(diagnoses) if diagnoses else 'None extracted'}\n"
            model_responses_text += f"---\n"
        
        # Fill in the prompt
        prompt = prompt.format(
            case_presentation=case_presentation,
            model_responses=model_responses_text,
            primary_diagnosis=statistical_consensus.primary_diagnosis or "No consensus",
            primary_confidence=int(statistical_consensus.primary_confidence * 100),
            consensus_level=statistical_consensus.consensus_level,
            total_models=statistical_consensus.total_models,
            responding_models=statistical_consensus.responding_models
        )
        
        return prompt
    
    def _parse_ai_consensus(self, ai_response: str, fallback: ConsensusResult) -> ConsensusResult:
        """Parse AI consensus response into ConsensusResult"""
        
        import re
        
        # Extract components from AI response
        primary_match = re.search(r'PRIMARY_DIAGNOSIS:\s*(.+)', ai_response)
        confidence_match = re.search(r'CONFIDENCE:\s*(\d+)', ai_response)
        alternatives_match = re.search(r'ALTERNATIVES:\s*(.+)', ai_response)
        minority_match = re.search(r'MINORITY_OPINIONS:\s*(.+)', ai_response)
        recommendation_match = re.search(r'CLINICAL_RECOMMENDATION:\s*(.+)', ai_response)
        bias_match = re.search(r'BIAS_PATTERNS:\s*(.+)', ai_response)
        geographic_match = re.search(r'GEOGRAPHIC_VARIATION:\s*(.+)', ai_response)
        
        # Parse primary diagnosis
        primary_diagnosis = primary_match.group(1).strip() if primary_match else fallback.primary_diagnosis
        
        # Parse confidence
        confidence = float(confidence_match.group(1)) / 100 if confidence_match else fallback.primary_confidence
        
        # Parse alternatives
        alternatives = []
        if alternatives_match:
            alt_text = alternatives_match.group(1).strip()
            for alt in alt_text.split(','):
                alt = alt.strip()
                if alt and alt.lower() not in ['none', 'n/a']:
                    alternatives.append({
                        'diagnosis': alt,
                        'confidence': 0.5,  # Default confidence
                        'model_count': 0,
                        'supporting_models': []
                    })
        
        # Parse minority opinions
        minority_opinions = []
        if minority_match:
            minority_text = minority_match.group(1).strip()
            for opinion in minority_text.split(','):
                opinion = opinion.strip()
                if opinion and opinion.lower() not in ['none', 'n/a']:
                    minority_opinions.append({
                        'diagnosis': opinion,
                        'models': [],
                        'confidence': 0.25
                    })
        
        # Parse clinical recommendation
        clinical_recommendation = recommendation_match.group(1).strip() if recommendation_match else fallback.clinical_recommendation
        
        # Parse bias considerations
        bias_considerations = []
        if bias_match:
            bias_text = bias_match.group(1).strip()
            if bias_text.lower() not in ['none', 'n/a']:
                bias_considerations = [b.strip() for b in bias_text.split(';')]
        
        # Determine consensus level based on AI confidence
        if confidence >= 0.75:
            consensus_level = "Strong"
        elif confidence >= 0.5:
            consensus_level = "Partial"
        else:
            consensus_level = "Weak"
        
        # Create enhanced ConsensusResult
        return ConsensusResult(
            total_models=fallback.total_models,
            responding_models=fallback.responding_models,
            consensus_level=consensus_level,
            primary_diagnosis=primary_diagnosis,
            primary_confidence=confidence,
            alternative_diagnoses=alternatives if alternatives else fallback.alternative_diagnoses,
            minority_opinions=minority_opinions if minority_opinions else fallback.minority_opinions,
            agreement_scores=fallback.agreement_scores,
            geographic_patterns=fallback.geographic_patterns,
            action_required="AI-enhanced clinical judgment recommended",
            clinical_recommendation=clinical_recommendation,
            bias_considerations=bias_considerations if bias_considerations else fallback.bias_considerations
        )
    
    def _create_empty_consensus(self, total_models: int) -> ConsensusResult:
        """Create empty consensus result when no models respond"""
        
        return ConsensusResult(
            total_models=total_models,
            responding_models=0,
            consensus_level="None",
            primary_diagnosis=None,
            primary_confidence=0.0,
            alternative_diagnoses=[],
            minority_opinions=[],
            agreement_scores={},
            geographic_patterns={},
            action_required="Unable to analyze - no model responses",
            clinical_recommendation="Manual clinical evaluation required",
            bias_considerations=["All models failed to respond - technical issues"]
        )