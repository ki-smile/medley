"""
Unit tests for the orchestrator module
"""

import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from web_orchestrator import (
    run_orchestrator_analysis,
    prepare_orchestrator_prompt,
    extract_orchestrator_results
)


class TestOrchestrator:
    """Test orchestrator functionality"""
    
    @pytest.fixture
    def sample_model_responses(self):
        """Sample model responses for testing"""
        return [
            {
                "model": "google/gemini-2.0-flash-exp:free",
                "response": {
                    "primary_diagnosis": "Rheumatoid Arthritis",
                    "differential_diagnoses": ["Lupus", "Fibromyalgia"],
                    "confidence": "High"
                }
            },
            {
                "model": "meta-llama/llama-3.2-3b-instruct:free",
                "response": {
                    "primary_diagnosis": "Rheumatoid Arthritis",
                    "differential_diagnoses": ["Osteoarthritis", "Gout"],
                    "confidence": "Medium"
                }
            }
        ]
    
    @pytest.fixture
    def case_description(self):
        """Sample case description"""
        return """
        45-year-old female presenting with bilateral joint pain,
        morning stiffness lasting 2 hours, and elevated inflammatory markers.
        """
    
    def test_prepare_orchestrator_prompt(self, sample_model_responses, case_description):
        """Test orchestrator prompt preparation"""
        prompt = prepare_orchestrator_prompt(
            case_description,
            sample_model_responses
        )
        
        assert case_description in prompt
        assert "Rheumatoid Arthritis" in prompt
        assert "consensus" in prompt.lower()
        assert "bias" in prompt.lower()
    
    @patch('web_orchestrator.query_orchestrator_model')
    def test_run_orchestrator_analysis_success(self, mock_query, 
                                               sample_model_responses, 
                                               case_description):
        """Test successful orchestrator analysis"""
        mock_query.return_value = {
            "consensus_diagnosis": "Rheumatoid Arthritis",
            "confidence_level": 0.85,
            "alternative_diagnoses": ["Lupus", "Osteoarthritis"],
            "bias_analysis": {
                "geographic_bias": "None detected",
                "model_agreement": "High"
            }
        }
        
        result = run_orchestrator_analysis(
            case_description,
            sample_model_responses
        )
        
        assert result["consensus_diagnosis"] == "Rheumatoid Arthritis"
        assert result["confidence_level"] == 0.85
        assert "Lupus" in result["alternative_diagnoses"]
        assert result["bias_analysis"]["model_agreement"] == "High"
    
    @patch('web_orchestrator.query_orchestrator_model')
    def test_orchestrator_fallback_mechanism(self, mock_query,
                                            sample_model_responses,
                                            case_description):
        """Test orchestrator fallback when primary fails"""
        # First call fails, second succeeds
        mock_query.side_effect = [
            Exception("Primary model failed"),
            {
                "consensus_diagnosis": "Arthritis",
                "confidence_level": 0.7,
                "alternative_diagnoses": []
            }
        ]
        
        result = run_orchestrator_analysis(
            case_description,
            sample_model_responses,
            use_fallback=True
        )
        
        assert result["consensus_diagnosis"] == "Arthritis"
        assert mock_query.call_count == 2
    
    def test_extract_orchestrator_results(self):
        """Test extraction of orchestrator results"""
        raw_response = """
        Based on the analysis:
        PRIMARY DIAGNOSIS: Rheumatoid Arthritis (ICD-10: M06.9)
        CONFIDENCE: 85%
        ALTERNATIVES: 
        1. Systemic Lupus Erythematosus (M32.9)
        2. Osteoarthritis (M19.90)
        """
        
        results = extract_orchestrator_results(raw_response)
        
        assert results["primary_diagnosis"]["name"] == "Rheumatoid Arthritis"
        assert results["primary_diagnosis"]["icd_code"] == "M06.9"
        assert results["confidence"] == 0.85
        assert len(results["alternatives"]) == 2
    
    def test_consensus_calculation(self, sample_model_responses):
        """Test consensus calculation from multiple models"""
        from web_orchestrator import calculate_consensus
        
        # Add more responses for testing
        responses = sample_model_responses + [
            {
                "model": "openai/gpt-4",
                "response": {
                    "primary_diagnosis": "Rheumatoid Arthritis",
                    "confidence": "High"
                }
            }
        ]
        
        consensus = calculate_consensus(responses)
        
        assert consensus["primary"]["diagnosis"] == "Rheumatoid Arthritis"
        assert consensus["primary"]["agreement"] == 3/3  # All agree
        assert consensus["primary"]["confidence"] >= 0.8
    
    def test_bias_detection(self, sample_model_responses):
        """Test bias detection in model responses"""
        from web_orchestrator import detect_biases
        
        # Add responses with geographic variation
        responses = [
            {
                "model": "chinese-model",
                "origin": "China",
                "response": {
                    "primary_diagnosis": "Wind-Dampness Syndrome",
                    "treatment": "Acupuncture and herbs"
                }
            },
            {
                "model": "us-model",
                "origin": "USA",
                "response": {
                    "primary_diagnosis": "Rheumatoid Arthritis",
                    "treatment": "Methotrexate and biologics"
                }
            }
        ]
        
        biases = detect_biases(responses)
        
        assert "geographic" in biases
        assert "treatment_approach" in biases
        assert biases["geographic"]["variation"] == "High"
    
    def test_minority_opinion_preservation(self):
        """Test that minority opinions are preserved"""
        from web_orchestrator import preserve_minority_opinions
        
        responses = [
            {"diagnosis": "Common Cold", "count": 8},
            {"diagnosis": "Influenza", "count": 1},
            {"diagnosis": "COVID-19", "count": 1}
        ]
        
        minority = preserve_minority_opinions(responses, threshold=0.2)
        
        assert len(minority) == 2
        assert "Influenza" in [m["diagnosis"] for m in minority]
        assert "COVID-19" in [m["diagnosis"] for m in minority]
    
    @pytest.mark.parametrize("num_models,expected_confidence", [
        (1, 0.5),   # Single model - low confidence
        (5, 0.7),   # Few models - medium confidence
        (20, 0.9),  # Many models - high confidence
    ])
    def test_confidence_scaling(self, num_models, expected_confidence):
        """Test confidence scaling based on number of models"""
        from web_orchestrator import calculate_confidence
        
        confidence = calculate_confidence(
            agreement_rate=0.8,
            num_models=num_models
        )
        
        assert confidence >= expected_confidence - 0.1
        assert confidence <= expected_confidence + 0.1
    
    def test_orchestrator_error_handling(self):
        """Test orchestrator error handling"""
        from web_orchestrator import safe_orchestrator_call
        
        # Test with invalid input
        result = safe_orchestrator_call(None, [])
        assert result["status"] == "error"
        assert "error_message" in result
        
        # Test with empty responses
        result = safe_orchestrator_call("valid case", [])
        assert result["status"] == "error"
        assert "No model responses" in result["error_message"]


class TestSplitOrchestration:
    """Test split orchestration architecture"""
    
    def test_diagnostic_orchestration(self):
        """Test diagnostic-focused orchestration"""
        from web_orchestrator import run_diagnostic_orchestration
        
        responses = [
            {"diagnosis": "Diabetes Type 2", "confidence": 0.9},
            {"diagnosis": "Diabetes Type 2", "confidence": 0.8},
            {"diagnosis": "Prediabetes", "confidence": 0.6}
        ]
        
        result = run_diagnostic_orchestration(responses)
        
        assert result["primary_diagnosis"] == "Diabetes Type 2"
        assert result["consensus_strength"] == "Strong"
        assert "Prediabetes" in result["alternatives"]
    
    def test_management_orchestration(self):
        """Test management strategy orchestration"""
        from web_orchestrator import run_management_orchestration
        
        responses = [
            {"treatment": "Metformin", "priority": "First-line"},
            {"treatment": "Lifestyle modification", "priority": "Essential"},
            {"treatment": "Insulin", "priority": "If needed"}
        ]
        
        result = run_management_orchestration(responses)
        
        assert "Lifestyle modification" in result["immediate_actions"]
        assert "Metformin" in result["medications"]
        assert result["follow_up"] is not None
    
    def test_bias_analysis_orchestration(self):
        """Test bias analysis orchestration"""
        from web_orchestrator import run_bias_orchestration
        
        model_metadata = [
            {"model": "gpt-4", "country": "USA", "company": "OpenAI"},
            {"model": "claude", "country": "USA", "company": "Anthropic"},
            {"model": "qwen", "country": "China", "company": "Alibaba"}
        ]
        
        result = run_bias_orchestration(model_metadata, [])
        
        assert "geographic_distribution" in result
        assert result["geographic_distribution"]["USA"] == 2
        assert result["geographic_distribution"]["China"] == 1
        assert "bias_risk" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])