"""
Response Parser for LLM outputs
Standardizes and structures medical diagnostic responses
"""

import re
import json
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict

@dataclass
class DiagnosticResponse:
    """Structured medical diagnostic response"""
    initial_impression: str
    differential_diagnoses: List[Dict[str, str]]  # List of {diagnosis, reasoning}
    alternative_perspectives: str
    next_steps: str
    uncertainties: str
    population_considerations: Optional[str] = None
    confidence_score: Optional[float] = None
    raw_response: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return asdict(self)

class ResponseParser:
    """Parses and standardizes LLM responses"""
    
    def __init__(self):
        # Patterns for extracting structured sections
        self.section_patterns = {
            "initial_impression": r"\*\*1\.\s*Initial Impression.*?\*\*(.*?)(?=\*\*\d+\.|$)",
            "differential_diagnosis": r"\*\*2\.\s*Primary Differential.*?\*\*(.*?)(?=\*\*\d+\.|$)",
            "alternative_perspectives": r"\*\*3\.\s*Alternative Perspectives.*?\*\*(.*?)(?=\*\*\d+\.|$)",
            "next_steps": r"\*\*[4-6]\.\s*Next Steps.*?\*\*(.*?)(?=\*\*\d+\.|$)",
            "uncertainties": r"uncertain.*?:(.*?)(?=\*\*|\n\n|$)",
            "population_considerations": r"\*\*7\.\s*Population.*?\*\*(.*?)(?=\*\*\d+\.|$)"
        }
        
    def parse_response(self, llm_response: str) -> DiagnosticResponse:
        """Parse LLM response into structured format"""
        
        # Extract sections using regex patterns
        sections = self._extract_sections(llm_response)
        
        # Parse differential diagnoses
        # Always try to parse the full response for diagnoses
        # (Many models don't follow our expected format)
        differential = self._parse_differential_diagnosis(llm_response)
        
        # If nothing found, try the specific section
        if not differential:
            differential = self._parse_differential_diagnosis(
                sections.get("differential_diagnosis", "")
            )
        
        # Extract confidence if mentioned
        confidence = self._extract_confidence(llm_response)
        
        return DiagnosticResponse(
            initial_impression=sections.get("initial_impression", "").strip(),
            differential_diagnoses=differential,
            alternative_perspectives=sections.get("alternative_perspectives", "").strip(),
            next_steps=sections.get("next_steps", "").strip(),
            uncertainties=sections.get("uncertainties", "").strip(),
            population_considerations=sections.get("population_considerations", "").strip(),
            confidence_score=confidence,
            raw_response=llm_response
        )
    
    def _extract_sections(self, text: str) -> Dict[str, str]:
        """Extract sections from response text"""
        sections = {}
        
        for section_name, pattern in self.section_patterns.items():
            match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
            if match:
                sections[section_name] = match.group(1).strip()
        
        # Fallback: if no structured sections found, try simpler extraction
        if not sections:
            sections = self._extract_unstructured(text)
        
        return sections
    
    def _extract_unstructured(self, text: str) -> Dict[str, str]:
        """Extract information from unstructured text"""
        sections = {}
        
        # Split by common headers or numbered points
        paragraphs = text.split("\n\n")
        
        # Try to identify sections by keywords
        for para in paragraphs:
            lower_para = para.lower()
            
            if "initial" in lower_para or "first impression" in lower_para:
                sections["initial_impression"] = para
            elif "differential" in lower_para or "diagnos" in lower_para:
                sections["differential_diagnosis"] = para
            elif "alternative" in lower_para or "perspective" in lower_para:
                sections["alternative_perspectives"] = para
            elif "next step" in lower_para or "additional" in lower_para:
                sections["next_steps"] = para
            elif "uncertain" in lower_para:
                sections["uncertainties"] = para
        
        # If still no sections, use the entire text as initial impression
        if not sections:
            sections["initial_impression"] = text
        
        return sections
    
    def _parse_differential_diagnosis(self, text: str) -> List[Dict[str, str]]:
        """Parse differential diagnosis section into structured list"""
        diagnoses = []
        
        if not text:
            return diagnoses
        
        # Look for explicitly labeled differential diagnosis sections
        diff_diag_pattern = r'(?:differential diagnosis|possible diagnoses?|diagnostic considerations?):\s*\n(.*?)(?:\n\n|\Z)'
        diff_match = re.search(diff_diag_pattern, text, re.IGNORECASE | re.DOTALL)
        if diff_match:
            text = diff_match.group(1)
        
        # First, try to extract FMF and other specific diagnoses mentioned directly
        specific_diseases = [
            r"Familial Mediterranean Fever(?:\s*\(FMF\))?",
            r"FMF(?:\s*\(Familial Mediterranean Fever\))?",
            r"Inflammatory Bowel Disease(?:\s*\(IBD\))?",
            r"Crohn'?s Disease",
            r"Ulcerative Colitis",
            r"Systemic Lupus Erythematosus(?:\s*\(SLE\))?",
            r"Still'?s Disease",
            r"Behcet'?s Disease",
            r"Reactive Arthritis",
            r"Rheumatoid Arthritis",
            r"Periodic Fever Syndrome",
            r"PFAPA Syndrome",
            r"Typhoid Fever",
            r"Septic Arthritis",
            r"Psoriatic Arthritis",
            r"Pericarditis",
            r"Myocarditis",
            r"Sickle Cell (?:Disease|Crisis)",
            r"TRAPS",
            r"HIDS"
        ]
        
        found_diseases = set()
        for disease_pattern in specific_diseases:
            matches = re.findall(disease_pattern, text, re.IGNORECASE)
            for match in matches:
                disease_name = match.strip()
                if disease_name and disease_name not in found_diseases:
                    found_diseases.add(disease_name)
                    # Find reasoning near this diagnosis
                    idx = text.lower().find(disease_name.lower())
                    if idx != -1:
                        # Get surrounding context
                        start = max(0, idx - 50)
                        end = min(len(text), idx + len(disease_name) + 200)
                        reasoning = text[start:end].replace(disease_name, "").strip()
                        reasoning = re.sub(r'^\W+|\W+$', '', reasoning)[:200]
                    else:
                        reasoning = ""
                    
                    diagnoses.append({
                        "diagnosis": disease_name,
                        "reasoning": reasoning
                    })
        
        # If we found specific diseases, return them
        if diagnoses:
            return diagnoses[:5]
        
        # Otherwise, look for numbered or bulleted lists
        lines = text.split("\n")
        current_diagnosis = None
        current_reasoning = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Check if line starts a new diagnosis (numbered or bulleted)
            if re.match(r"^[1-9\-\*•]", line):
                # Save previous diagnosis if exists
                if current_diagnosis:
                    diagnoses.append({
                        "diagnosis": current_diagnosis,
                        "reasoning": " ".join(current_reasoning).strip()
                    })
                
                # Start new diagnosis
                # Remove numbering/bullets and markdown formatting
                clean_line = re.sub(r"^[1-9\.\-\*•)\s]+", "", line)
                clean_line = re.sub(r"\*\*([^*]+)\*\*", r"\1", clean_line)  # Remove bold
                
                # Skip non-medical terms that are clearly not diagnoses
                skip_terms = [
                    "cultural", "linguistic", "factor", "consideration",
                    "genetic factor", "differential", "next step", "testing",
                    "workup", "evaluation", "assessment", "approach",
                    "age", "sex", "gender", "nationality", "language", "history",
                    "patient information", "case id", "title", "analysis",
                    "presentation", "physical exam", "medical history"
                ]
                
                # Check if this looks like a medical diagnosis
                line_lower = clean_line.lower()
                is_skip = any(term in line_lower for term in skip_terms)
                
                # Look for actual medical conditions (positive indicators)
                medical_terms = [
                    "fever", "syndrome", "disease", "disorder", "arthritis",
                    "inflammation", "infection", "cancer", "failure", "deficiency",
                    "fmf", "familial", "mediterranean", "lupus", "still",
                    "behcet", "crohn", "colitis", "spondylo", "hids"
                ]
                is_medical = any(term in line_lower for term in medical_terms)
                
                # Only process if it looks like a medical diagnosis
                if not is_skip or is_medical:
                    # Split diagnosis name from reasoning if on same line
                    if ":" in clean_line or " - " in clean_line:
                        parts = re.split(r"[:|\-]", clean_line, 1)
                        current_diagnosis = parts[0].strip()
                        current_reasoning = [parts[1].strip()] if len(parts) > 1 else []
                    else:
                        current_diagnosis = clean_line
                        current_reasoning = []
                else:
                    # Skip this line, it's not a diagnosis
                    continue
            else:
                # Continue current diagnosis reasoning
                if current_diagnosis:
                    current_reasoning.append(line)
        
        # Save last diagnosis
        if current_diagnosis:
            diagnoses.append({
                "diagnosis": current_diagnosis,
                "reasoning": " ".join(current_reasoning).strip()
            })
        
        # If no structured list found, try to extract any mentioned diagnoses
        if not diagnoses and text:
            # Look for common diagnostic terms
            diagnostic_terms = [
                "pneumonia", "sepsis", "infection", "syndrome", "disease",
                "disorder", "failure", "injury", "fever", "toxicity"
            ]
            
            for term in diagnostic_terms:
                if term in text.lower():
                    # Extract sentence containing the term
                    sentences = text.split(".")
                    for sent in sentences:
                        if term in sent.lower():
                            diagnoses.append({
                                "diagnosis": term.capitalize(),
                                "reasoning": sent.strip()
                            })
                            break
        
        return diagnoses[:5]  # Limit to top 5 diagnoses
    
    def _extract_confidence(self, text: str) -> Optional[float]:
        """Extract confidence score if mentioned"""
        
        # Look for percentage patterns
        percent_match = re.search(r"(\d+)%\s*(?:confidence|certain|likely)", text, re.IGNORECASE)
        if percent_match:
            return float(percent_match.group(1)) / 100
        
        # Look for decimal confidence
        decimal_match = re.search(r"confidence.*?(0\.\d+)", text, re.IGNORECASE)
        if decimal_match:
            return float(decimal_match.group(1))
        
        # Look for qualitative confidence terms
        if re.search(r"high(?:ly)?\s+confident", text, re.IGNORECASE):
            return 0.8
        elif re.search(r"moderate(?:ly)?\s+confident", text, re.IGNORECASE):
            return 0.6
        elif re.search(r"low\s+confidence", text, re.IGNORECASE):
            return 0.3
        
        return None
    
    def standardize_diagnosis_name(self, diagnosis: str) -> str:
        """Standardize diagnosis names for comparison across models"""
        
        # Remove common prefixes/suffixes
        diagnosis = diagnosis.lower().strip()
        diagnosis = re.sub(r"^(possible|probable|likely|suspected)\s+", "", diagnosis)
        diagnosis = re.sub(r"\s+(syndrome|disease|disorder)$", "", diagnosis)
        
        # Map common variations to standard terms
        standardizations = {
            "fmf": "familial mediterranean fever",
            "familial mediterranean fever": "familial mediterranean fever",
            "periodic fever": "periodic fever syndrome",
            "autoinflammatory": "autoinflammatory syndrome",
            "sepsis": "sepsis",
            "infection": "infection",
            "uti": "urinary tract infection",
            "pneumonia": "pneumonia",
            "dementia": "dementia",
            "alzheimer": "alzheimer disease",
            "delirium": "delirium",
            "psychosis": "psychosis",
            "intoxication": "substance intoxication",
            "withdrawal": "substance withdrawal"
        }
        
        for key, value in standardizations.items():
            if key in diagnosis:
                return value
        
        return diagnosis
    
    def compare_responses(
        self,
        responses: List[DiagnosticResponse]
    ) -> Dict[str, Any]:
        """Compare multiple diagnostic responses"""
        
        # Collect all diagnoses
        all_diagnoses = {}
        for i, response in enumerate(responses):
            for diag_dict in response.differential_diagnoses:
                diag_name = self.standardize_diagnosis_name(diag_dict["diagnosis"])
                if diag_name not in all_diagnoses:
                    all_diagnoses[diag_name] = []
                all_diagnoses[diag_name].append(i)
        
        # Calculate consensus
        consensus = {
            "diagnoses": all_diagnoses,
            "agreement_scores": {},
            "unique_perspectives": [],
            "common_uncertainties": []
        }
        
        # Calculate agreement scores
        total_responses = len(responses)
        for diagnosis, responders in all_diagnoses.items():
            consensus["agreement_scores"][diagnosis] = len(responders) / total_responses
        
        # Identify unique perspectives
        for response in responses:
            if response.alternative_perspectives:
                consensus["unique_perspectives"].append(response.alternative_perspectives)
        
        # Common uncertainties
        uncertainty_counts = {}
        for response in responses:
            if response.uncertainties:
                for word in response.uncertainties.lower().split():
                    if len(word) > 4:  # Skip short words
                        uncertainty_counts[word] = uncertainty_counts.get(word, 0) + 1
        
        consensus["common_uncertainties"] = [
            word for word, count in uncertainty_counts.items()
            if count >= total_responses / 2
        ]
        
        return consensus