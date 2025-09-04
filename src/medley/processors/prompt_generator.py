"""
Prompt Generator for Medical Diagnosis with Standardized Output
Ensures all models return consistent, structured JSON responses
"""

from typing import Dict, Any, Optional
from datetime import datetime


class DiagnosticPromptGenerator:
    """
    Generates standardized prompts that request structured JSON output
    from all models for consistent analysis
    """
    
    def __init__(self):
        """Initialize the prompt generator"""
        self.system_prompt = self._create_system_prompt()
        self.output_format = self._define_output_format()
        
    def _create_system_prompt(self) -> str:
        """Create the system prompt that defines the model's role"""
        return """You are an expert medical diagnostic AI assistant. Your role is to:
1. Analyze medical cases comprehensively
2. Provide differential diagnoses with confidence levels
3. Recommend diagnostic tests and management strategies
4. Consider various demographic and clinical factors
5. Return your analysis in a structured JSON format

IMPORTANT: You must ALWAYS respond with valid JSON only. No explanatory text outside the JSON structure."""

    def _define_output_format(self) -> str:
        """Define the exact JSON structure expected from models"""
        return """{
    "primary_diagnosis": {
        "name": "string",
        "confidence": 0.0-1.0,
        "icd_code": "string"
    },
    "differential_diagnoses": [
        {
            "name": "string",
            "confidence": 0.0-1.0,
            "icd_code": "string"
        }
    ],
    "key_findings": ["string"],
    "tests": [
        {
            "test": "string",
            "priority": "immediate|urgent|routine"
        }
    ],
    "management": {
        "immediate": ["string"],
        "medications": ["drug: dose, route"],
        "consultations": ["specialty: urgency"]
    },
    "red_flags": ["string"]
}"""

    def generate_diagnostic_prompt(self, case_content: str, model_name: Optional[str] = None) -> str:
        """
        Generate a standardized diagnostic prompt for a medical case
        
        Args:
            case_content: The medical case description
            model_name: Optional model name for model-specific adjustments
            
        Returns:
            Formatted prompt requesting JSON response
        """
        
        prompt = f"""Analyze this medical case. Return ONLY valid JSON.

{case_content}

Output format:
{self.output_format}

Requirements:
- Confidence: 0.0-1.0
- Include 3-5 differential diagnoses
- Provide ICD-10 codes when known
- List tests by priority
- Include specific medication doses
- Return JSON only"""

        return prompt

    def generate_consensus_prompt(self, case_content: str, model_responses: list) -> str:
        """
        Generate a prompt for consensus analysis of multiple model responses
        
        Args:
            case_content: The original medical case
            model_responses: List of model responses to analyze
            
        Returns:
            Prompt for consensus analysis
        """
        
        # Format model responses for analysis
        responses_text = "\n\n".join([
            f"Model {i+1} Assessment:\n{response}"
            for i, response in enumerate(model_responses)
        ])
        
        prompt = f"""As a medical consensus coordinator, analyze the following diagnostic assessments from multiple AI models for this case:

ORIGINAL CASE:
{case_content}

MODEL ASSESSMENTS:
{responses_text}

Provide a consensus analysis in the following JSON format:

{{
    "consensus_diagnosis": {{
        "name": "Most agreed upon diagnosis",
        "agreement_percentage": 0-100,
        "confidence": 0.0-1.0,
        "supporting_models": ["Model 1", "Model 2", ...],
        "dissenting_models": ["Model X", ...]
    }},
    "alternative_diagnoses": [
        {{
            "name": "Alternative diagnosis",
            "agreement_percentage": 0-100,
            "supporting_models": ["Model X", ...]
        }}
    ],
    "critical_agreements": [
        {{
            "finding": "What all/most models agree on",
            "agreement_level": "unanimous|strong|moderate",
            "clinical_significance": "Why this matters"
        }}
    ],
    "critical_disagreements": [
        {{
            "topic": "Area of disagreement",
            "divergent_views": [
                {{"view": "View 1", "models": ["Model X"]}},
                {{"view": "View 2", "models": ["Model Y"]}}
            ],
            "clinical_impact": "How this affects management"
        }}
    ],
    "recommended_tests": [
        {{
            "test": "Test name",
            "consensus_level": 0-100,
            "purpose": "What it resolves"
        }}
    ],
    "management_consensus": {{
        "immediate_actions": ["Action 1", "Action 2"],
        "medications": ["Med 1", "Med 2"],
        "consultations": ["Specialty 1", "Specialty 2"]
    }},
    "uncertainty_areas": [
        "Area where models show low confidence",
        "Area needing more information"
    ],
    "bias_considerations": [
        {{
            "type": "Geographic|Demographic|Training",
            "observation": "Potential bias observed",
            "affected_models": ["Model X", "Model Y"]
        }}
    ],
    "final_recommendation": {{
        "primary_diagnosis": "Recommended diagnosis",
        "confidence": 0.0-1.0,
        "next_steps": ["Step 1", "Step 2", "Step 3"],
        "rationale": "Why this conclusion"
    }}
}}

RESPOND WITH JSON ONLY"""

        return prompt

    def generate_simple_prompt(self, case_content: str) -> str:
        """
        Generate a simpler prompt for models that may struggle with complex JSON
        
        Args:
            case_content: The medical case description
            
        Returns:
            Simplified prompt
        """
        
        prompt = f"""Analyze this medical case and provide your diagnosis:

{case_content}

Please structure your response as follows:

1. PRIMARY DIAGNOSIS: [Name] (Confidence: X%)
2. ALTERNATIVE DIAGNOSES:
   - [Diagnosis 1] (Confidence: X%)
   - [Diagnosis 2] (Confidence: X%)
   - [Diagnosis 3] (Confidence: X%)
3. KEY FINDINGS:
   - [Finding 1]
   - [Finding 2]
4. RECOMMENDED TESTS:
   - [Test 1]: [Purpose]
   - [Test 2]: [Purpose]
5. IMMEDIATE MANAGEMENT:
   - [Action 1]
   - [Action 2]
6. MEDICATIONS:
   - [Drug 1]: [Dose, Route, Duration]
   - [Drug 2]: [Dose, Route, Duration]
7. CONSULTATIONS NEEDED:
   - [Specialty 1]: [Reason]
   - [Specialty 2]: [Reason]
8. RED FLAGS TO WATCH:
   - [Warning 1]
   - [Warning 2]

Be specific and concise."""

        return prompt

    def parse_response(self, response: str, format_type: str = "json") -> Dict[str, Any]:
        """
        Parse model response into structured format
        
        Args:
            response: The model's response text
            format_type: Expected format ("json" or "simple")
            
        Returns:
            Parsed response as dictionary
        """
        import json
        import re
        
        if format_type == "json":
            try:
                # Try to extract JSON from response
                # Some models might add text before/after JSON
                json_match = re.search(r'\{.*\}', response, re.DOTALL)
                if json_match:
                    return json.loads(json_match.group())
                else:
                    # Try direct parsing
                    return json.loads(response)
            except:
                # Fallback to text parsing
                return self._parse_text_response(response)
        else:
            return self._parse_text_response(response)
            
    def _parse_text_response(self, response: str) -> Dict[str, Any]:
        """
        Parse text response into structured format
        
        Args:
            response: Text response from model
            
        Returns:
            Parsed dictionary
        """
        parsed = {
            "primary_diagnosis": {"name": "", "confidence": 0.5, "reasoning": ""},
            "differential_diagnoses": [],
            "key_findings": [],
            "diagnostic_tests": [],
            "management_plan": {
                "immediate_actions": [],
                "medications": [],
                "monitoring": [],
                "consultations": []
            },
            "red_flags": [],
            "uncertainties": []
        }
        
        # Extract primary diagnosis
        primary_match = re.search(r'PRIMARY DIAGNOSIS:?\s*([^\n(]+)(?:\(Confidence:?\s*(\d+)%?\))?', 
                                 response, re.IGNORECASE)
        if primary_match:
            parsed["primary_diagnosis"]["name"] = primary_match.group(1).strip()
            if primary_match.group(2):
                parsed["primary_diagnosis"]["confidence"] = float(primary_match.group(2)) / 100.0
                
        # Extract alternative diagnoses
        alt_section = re.search(r'ALTERNATIVE DIAGNOSES?:?(.*?)(?:KEY FINDINGS?:|RECOMMENDED|$)', 
                                response, re.IGNORECASE | re.DOTALL)
        if alt_section:
            alt_lines = alt_section.group(1).strip().split('\n')
            for line in alt_lines:
                diag_match = re.search(r'[-•]\s*([^(]+)(?:\(Confidence:?\s*(\d+)%?\))?', line)
                if diag_match:
                    parsed["differential_diagnoses"].append({
                        "name": diag_match.group(1).strip(),
                        "confidence": float(diag_match.group(2))/100.0 if diag_match.group(2) else 0.5,
                        "reasoning": ""
                    })
                    
        # Extract key findings
        findings_section = re.search(r'KEY FINDINGS?:?(.*?)(?:RECOMMENDED|IMMEDIATE|$)', 
                                    response, re.IGNORECASE | re.DOTALL)
        if findings_section:
            findings_lines = findings_section.group(1).strip().split('\n')
            for line in findings_lines:
                if re.match(r'^\s*[-•]\s*(.+)', line):
                    finding = re.sub(r'^\s*[-•]\s*', '', line).strip()
                    if finding:
                        parsed["key_findings"].append(finding)
                        
        # Extract tests
        tests_section = re.search(r'RECOMMENDED TESTS?:?(.*?)(?:IMMEDIATE|MEDICATIONS?|$)', 
                                 response, re.IGNORECASE | re.DOTALL)
        if tests_section:
            test_lines = tests_section.group(1).strip().split('\n')
            for line in test_lines:
                test_match = re.search(r'[-•]\s*([^:]+):?\s*(.*)', line)
                if test_match:
                    parsed["diagnostic_tests"].append({
                        "test": test_match.group(1).strip(),
                        "purpose": test_match.group(2).strip() if test_match.group(2) else "",
                        "priority": "urgent"
                    })
                    
        return parsed