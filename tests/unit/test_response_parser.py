"""
Unit tests for response parser
"""

import pytest

from src.medley.processors.response_parser import ResponseParser, DiagnosticResponse


class TestResponseParser:
    """Test LLM response parsing"""
    
    @pytest.mark.unit
    def test_response_parser_initialization(self):
        """Test parser initialization"""
        parser = ResponseParser()
        assert parser.section_patterns is not None
        assert "initial_impression" in parser.section_patterns
    
    @pytest.mark.unit
    def test_parse_structured_response(self):
        """Test parsing well-structured response"""
        response_text = """
        **1. Initial Impression**
        Patient likely has acute coronary syndrome
        
        **2. Primary Differential Diagnosis**
        1. Myocardial infarction - elevated troponins support this
        2. Pulmonary embolism - consider given dyspnea
        3. Anxiety disorder - less likely given clinical findings
        
        **3. Alternative Perspectives**
        A psychiatrist might consider panic disorder
        
        **4. Next Steps**
        Immediate cardiac catheterization needed
        
        **5. Uncertainties**
        Duration of symptoms is unclear
        """
        
        parser = ResponseParser()
        result = parser.parse_response(response_text)
        
        assert isinstance(result, DiagnosticResponse)
        assert "acute coronary syndrome" in result.initial_impression
        assert len(result.differential_diagnoses) == 3
        assert result.differential_diagnoses[0]["diagnosis"] == "Myocardial infarction"
        assert "cardiac catheterization" in result.next_steps
    
    @pytest.mark.unit
    def test_parse_unstructured_response(self):
        """Test parsing unstructured response"""
        response_text = """
        This patient presents with concerning symptoms. 
        The differential includes pneumonia, sepsis, and COVID-19.
        We should get additional labs and imaging.
        I'm uncertain about the timeline of symptom onset.
        """
        
        parser = ResponseParser()
        result = parser.parse_response(response_text)
        
        assert isinstance(result, DiagnosticResponse)
        assert len(result.initial_impression) > 0
        # Should extract diagnoses from text
        assert any("pneumonia" in d["diagnosis"].lower() 
                  for d in result.differential_diagnoses)
    
    @pytest.mark.unit
    def test_extract_confidence_percentage(self):
        """Test extracting confidence from percentage"""
        parser = ResponseParser()
        
        text1 = "I am 80% confident in this diagnosis"
        conf1 = parser._extract_confidence(text1)
        assert conf1 == 0.8
        
        text2 = "With 95% certainty, this is pneumonia"
        conf2 = parser._extract_confidence(text2)
        assert conf2 == 0.95
    
    @pytest.mark.unit
    def test_extract_confidence_qualitative(self):
        """Test extracting qualitative confidence"""
        parser = ResponseParser()
        
        text1 = "I am highly confident this is the diagnosis"
        conf1 = parser._extract_confidence(text1)
        assert conf1 == 0.8
        
        text2 = "I have low confidence in this assessment"
        conf2 = parser._extract_confidence(text2)
        assert conf2 == 0.3
    
    @pytest.mark.unit
    def test_standardize_diagnosis_names(self):
        """Test diagnosis name standardization"""
        parser = ResponseParser()
        
        assert parser.standardize_diagnosis_name("FMF") == "familial mediterranean fever"
        assert parser.standardize_diagnosis_name("Possible sepsis") == "sepsis"
        assert parser.standardize_diagnosis_name("UTI") == "urinary tract infection"
        assert parser.standardize_diagnosis_name("Alzheimer Disease") == "alzheimer disease"
    
    @pytest.mark.unit
    def test_parse_differential_with_bullets(self):
        """Test parsing differential with bullet points"""
        text = """
        - Myocardial infarction: Most likely given troponins
        - Pulmonary embolism: Consider if D-dimer elevated
        • Aortic dissection: Less likely but serious
        """
        
        parser = ResponseParser()
        diagnoses = parser._parse_differential_diagnosis(text)
        
        assert len(diagnoses) == 3
        assert diagnoses[0]["diagnosis"] == "Myocardial infarction"
        assert "troponins" in diagnoses[0]["reasoning"]
    
    @pytest.mark.unit
    def test_compare_responses(self):
        """Test comparing multiple diagnostic responses"""
        parser = ResponseParser()
        
        response1 = DiagnosticResponse(
            initial_impression="Test",
            differential_diagnoses=[
                {"diagnosis": "pneumonia", "reasoning": "fever"},
                {"diagnosis": "sepsis", "reasoning": "elevated WBC"}
            ],
            alternative_perspectives="Consider viral",
            next_steps="Get cultures",
            uncertainties="Timeline unclear"
        )
        
        response2 = DiagnosticResponse(
            initial_impression="Test2",
            differential_diagnoses=[
                {"diagnosis": "pneumonia", "reasoning": "consolidation"},
                {"diagnosis": "COVID-19", "reasoning": "pandemic"}
            ],
            alternative_perspectives="Consider bacterial",
            next_steps="Start antibiotics",
            uncertainties="Timeline unclear"
        )
        
        comparison = parser.compare_responses([response1, response2])
        
        assert "pneumonia" in comparison["diagnoses"]
        assert comparison["agreement_scores"]["pneumonia"] == 1.0  # Both agree
        assert comparison["agreement_scores"]["sepsis"] == 0.5  # Only one mentions
        assert len(comparison["unique_perspectives"]) == 2
    
    @pytest.mark.unit
    def test_diagnostic_response_to_dict(self):
        """Test DiagnosticResponse serialization"""
        response = DiagnosticResponse(
            initial_impression="Test impression",
            differential_diagnoses=[{"diagnosis": "test", "reasoning": "test"}],
            alternative_perspectives="Alternative view",
            next_steps="Next steps",
            uncertainties="Uncertain",
            confidence_score=0.75
        )
        
        response_dict = response.to_dict()
        
        assert response_dict["initial_impression"] == "Test impression"
        assert response_dict["confidence_score"] == 0.75
        assert len(response_dict["differential_diagnoses"]) == 1