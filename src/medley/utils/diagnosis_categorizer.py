"""
Diagnosis Categorization Utility for Medley
Provides consistent categorization rules across web interface and PDF generation
"""

from typing import Dict, List, Any, Tuple
from collections import Counter
import logging

logger = logging.getLogger(__name__)


def categorize_diagnoses(diagnosis_counts: Dict[str, int], total_models: int) -> Dict[str, List[Dict]]:
    """
    Categorize diagnoses based on agreement percentages using consistent web interface rules
    
    Web Interface Rules:
    - Strong Alternatives: ≥30% agreement (excluding primary)
    - Alternatives: 10-29% agreement 
    - Minority Opinions: <10% agreement
    
    Args:
        diagnosis_counts: Dictionary mapping diagnosis names to count of supporting models
        total_models: Total number of models that provided responses
        
    Returns:
        Dictionary with categorized diagnoses:
        {
            "primary_diagnosis": {...},
            "strong_alternatives": [...],
            "alternatives": [...], 
            "minority_opinions": [...]
        }
    """
    if not diagnosis_counts or total_models == 0:
        return {
            "primary_diagnosis": None,
            "strong_alternatives": [],
            "alternatives": [],
            "minority_opinions": []
        }
    
    # Sort diagnoses by count (descending)
    sorted_diagnoses = sorted(diagnosis_counts.items(), key=lambda x: x[1], reverse=True)
    
    # Primary diagnosis is the one with highest count
    primary_name, primary_count = sorted_diagnoses[0]
    primary_percentage = round((primary_count / total_models) * 100, 1)
    
    primary_diagnosis = {
        "name": primary_name,
        "agreement_percentage": primary_percentage,
        "model_count": primary_count,
        "confidence": _get_confidence_level(primary_percentage)
    }
    
    # Categorize remaining diagnoses
    strong_alternatives = []
    alternatives = []
    minority_opinions = []
    
    for diag_name, count in sorted_diagnoses[1:]:
        percentage = round((count / total_models) * 100, 1)
        
        diag_data = {
            "name": diag_name,
            "agreement_percentage": percentage,
            "model_count": count
        }
        
        # Apply web interface categorization rules
        if percentage >= 30.0:
            strong_alternatives.append(diag_data)
        elif percentage >= 10.0:  # 10-29%
            alternatives.append(diag_data)
        else:  # <10%
            minority_opinions.append(diag_data)
    
    return {
        "primary_diagnosis": primary_diagnosis,
        "strong_alternatives": strong_alternatives,
        "alternatives": alternatives,
        "minority_opinions": minority_opinions
    }


def categorize_diagnosis_list(diagnoses_with_percentages: List[Dict[str, Any]]) -> Dict[str, List[Dict]]:
    """
    Categorize a list of diagnoses that already have percentage data
    
    Args:
        diagnoses_with_percentages: List of diagnosis dictionaries with 'agreement_percentage' field
        
    Returns:
        Dictionary with categorized diagnoses using web interface rules
    """
    if not diagnoses_with_percentages:
        return {
            "primary_diagnosis": None,
            "strong_alternatives": [],
            "alternatives": [],
            "minority_opinions": []
        }
    
    # Sort by agreement percentage (descending)
    sorted_diagnoses = sorted(
        diagnoses_with_percentages, 
        key=lambda x: x.get('agreement_percentage', 0), 
        reverse=True
    )
    
    primary_diagnosis = sorted_diagnoses[0]
    
    # Categorize remaining diagnoses
    strong_alternatives = []
    alternatives = []
    minority_opinions = []
    
    for diag in sorted_diagnoses[1:]:
        percentage = diag.get('agreement_percentage', 0)
        
        # Apply web interface categorization rules
        if percentage >= 30.0:
            strong_alternatives.append(diag)
        elif percentage >= 10.0:  # 10-29%
            alternatives.append(diag)
        else:  # <10%
            minority_opinions.append(diag)
    
    return {
        "primary_diagnosis": primary_diagnosis,
        "strong_alternatives": strong_alternatives,
        "alternatives": alternatives,
        "minority_opinions": minority_opinions
    }


def extract_diagnoses_from_ensemble_results(ensemble_results: Dict) -> Dict[str, List[Dict]]:
    """
    Extract and categorize diagnoses from ensemble results using consensus data
    
    Args:
        ensemble_results: The ensemble analysis results
        
    Returns:
        Dictionary with categorized diagnoses
    """
    # Try to get consensus analysis data first
    consensus_data = ensemble_results.get("consensus_analysis", {})
    
    # Check if we have sorted diagnoses
    sorted_diagnoses = consensus_data.get("sorted_diagnoses", [])
    if sorted_diagnoses:
        diagnosis_counts = dict(sorted_diagnoses)
        total_models = sum(diagnosis_counts.values())
        return categorize_diagnoses(diagnosis_counts, total_models)
    
    # Fallback: try to extract from model responses
    model_responses = ensemble_results.get("model_responses", [])
    if not model_responses:
        return {
            "primary_diagnosis": None,
            "strong_alternatives": [],
            "alternatives": [],
            "minority_opinions": []
        }
    
    # Extract diagnoses from individual model responses
    diagnosis_counts = Counter()
    total_responding = 0
    
    for response in model_responses:
        if response.get("response") and not response.get("error"):
            total_responding += 1
            # Try to extract primary diagnosis from response
            primary_diag = _extract_primary_diagnosis_from_response(response.get("response", ""))
            if primary_diag:
                diagnosis_counts[primary_diag] += 1
    
    if total_responding == 0:
        return {
            "primary_diagnosis": None,
            "strong_alternatives": [],
            "alternatives": [],
            "minority_opinions": []
        }
    
    return categorize_diagnoses(dict(diagnosis_counts), total_responding)


def _get_confidence_level(percentage: float) -> str:
    """Get confidence level based on agreement percentage"""
    if percentage >= 75:
        return "High"
    elif percentage >= 50:
        return "Moderate"
    else:
        return "Low"


def _extract_primary_diagnosis_from_response(response_text: str) -> str:
    """
    Extract primary diagnosis from a model response text
    This is a simple extraction - could be enhanced with more sophisticated parsing
    """
    import json
    import re
    
    try:
        # Try to parse as JSON first
        response_data = json.loads(response_text)
        
        # Look for primary diagnosis in common field names
        primary_diag = (
            response_data.get("primary_diagnosis", {}).get("name") or
            response_data.get("primary_diagnosis") or
            response_data.get("diagnosis") or
            response_data.get("most_likely_diagnosis")
        )
        
        if isinstance(primary_diag, dict):
            return primary_diag.get("name", "")
        return primary_diag or ""
        
    except (json.JSONDecodeError, AttributeError):
        # Fallback: simple text extraction
        # Look for common patterns like "Primary diagnosis: X" or "Diagnosis: X"
        patterns = [
            r'primary diagnosis[:\s]+([^.\n]+)',
            r'diagnosis[:\s]+([^.\n]+)',
            r'most likely[:\s]+([^.\n]+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, response_text.lower())
            if match:
                return match.group(1).strip().title()
        
        return ""


def _categorize_alternatives_only(diagnoses_with_percentages: List[Dict[str, Any]]) -> Dict[str, List[Dict]]:
    """
    Categorize diagnoses without treating any as primary (used for alternative diagnoses only)
    
    Args:
        diagnoses_with_percentages: List of diagnosis dictionaries with 'agreement_percentage' field
        
    Returns:
        Dictionary with categorized diagnoses (no primary diagnosis)
    """
    if not diagnoses_with_percentages:
        return {
            "strong_alternatives": [],
            "alternatives": [],
            "minority_opinions": []
        }
    
    # Categorize all diagnoses based on percentage thresholds
    strong_alternatives = []
    alternatives = []
    minority_opinions = []
    
    for diag in diagnoses_with_percentages:
        # Safely get percentage from multiple possible field names
        percentage = (diag.get('agreement_percentage') or 
                     diag.get('percentage') or 
                     diag.get('support_percentage') or 
                     0)
        
        # Apply web interface categorization rules
        if percentage >= 30.0:
            strong_alternatives.append(diag)
        elif percentage >= 10.0:  # 10-29%
            alternatives.append(diag)
        else:  # <10%
            minority_opinions.append(diag)
    
    return {
        "strong_alternatives": strong_alternatives,
        "alternatives": alternatives,
        "minority_opinions": minority_opinions
    }


# Web interface compatibility function
def apply_web_interface_categorization_rules(diagnostic_landscape: Dict) -> Dict:
    """
    Apply web interface categorization rules to existing diagnostic landscape
    This ensures consistency between web interface and PDF generation
    
    Args:
        diagnostic_landscape: Current diagnostic landscape data
        
    Returns:
        Updated diagnostic landscape with consistent categorization
    """
    # Get all alternative diagnoses
    all_alternatives = diagnostic_landscape.get("all_alternative_diagnoses", [])
    
    if not all_alternatives:
        # If no all_alternative_diagnoses, check existing categories
        existing_strong = diagnostic_landscape.get("strong_alternatives", [])
        existing_alternatives = diagnostic_landscape.get("alternatives", [])
        existing_minority = diagnostic_landscape.get("minority_opinions", [])
        all_alternatives = existing_strong + existing_alternatives + existing_minority
    
    if not all_alternatives:
        # Initialize empty categories if nothing exists
        diagnostic_landscape.setdefault("strong_alternatives", [])
        diagnostic_landscape.setdefault("alternatives", [])
        diagnostic_landscape.setdefault("minority_opinions", [])
        return diagnostic_landscape
    
    # Ensure all alternatives have required fields before categorizing
    safe_alternatives = []
    for alt in all_alternatives:
        if isinstance(alt, dict):
            # Ensure the alternative has a percentage field
            if not any(key in alt for key in ['agreement_percentage', 'percentage', 'support_percentage']):
                # If no percentage, try to calculate from count if available
                count = alt.get('count', alt.get('model_count', 0))
                models = alt.get('supporting_models', [])
                if count > 0:
                    # Estimate percentage based on count (assuming ~27 total models)
                    alt['agreement_percentage'] = round((count / 27) * 100, 1)
                elif models:
                    alt['agreement_percentage'] = round((len(models) / 27) * 100, 1)
                else:
                    alt['agreement_percentage'] = 0
            safe_alternatives.append(alt)
    
    # Re-categorize based on web interface rules (without treating first as primary)
    categorized = _categorize_alternatives_only(safe_alternatives)
    
    # Update the diagnostic landscape
    diagnostic_landscape["strong_alternatives"] = categorized["strong_alternatives"]
    diagnostic_landscape["alternatives"] = categorized["alternatives"] 
    diagnostic_landscape["minority_opinions"] = categorized["minority_opinions"]
    
    # Update all_alternative_diagnoses with re-categorized data
    diagnostic_landscape["all_alternative_diagnoses"] = (
        categorized["strong_alternatives"] + 
        categorized["alternatives"] + 
        categorized["minority_opinions"]
    )
    
    return diagnostic_landscape


# Logging function for debugging categorization
def log_categorization_debug(categorized_diagnoses: Dict, context: str = ""):
    """Log categorization results for debugging"""
    logger.debug(f"Diagnosis Categorization {context}:")
    
    primary = categorized_diagnoses.get("primary_diagnosis")
    if primary:
        pct = primary.get('agreement_percentage', primary.get('percentage', 0))
        logger.debug(f"  Primary: {primary.get('name', 'Unknown')} ({pct:.1f}%)")
    
    for strong_alt in categorized_diagnoses.get("strong_alternatives", []):
        pct = strong_alt.get('agreement_percentage', strong_alt.get('percentage', 0))
        logger.debug(f"  Strong Alt: {strong_alt.get('name', 'Unknown')} ({pct:.1f}%)")
    
    for alt in categorized_diagnoses.get("alternatives", []):
        pct = alt.get('agreement_percentage', alt.get('percentage', 0))
        logger.debug(f"  Alternative: {alt.get('name', 'Unknown')} ({pct:.1f}%)")
    
    for minority in categorized_diagnoses.get("minority_opinions", []):
        pct = minority.get('agreement_percentage', minority.get('percentage', 0))
        logger.debug(f"  Minority: {minority.get('name', 'Unknown')} ({pct:.1f}%)")