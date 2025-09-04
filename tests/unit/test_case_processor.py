"""
Unit tests for case processor
"""

import pytest
import json
from pathlib import Path

from src.medley.processors.case_processor import CaseProcessor, MedicalCase


class TestCaseProcessor:
    """Test medical case processing"""
    
    @pytest.mark.unit
    def test_case_processor_initialization(self, temp_dir):
        """Test case processor initialization"""
        processor = CaseProcessor(cases_dir=temp_dir / "cases")
        assert processor.cases_dir.exists()
    
    @pytest.mark.unit
    def test_medical_case_to_dict(self, sample_medical_case):
        """Test converting medical case to dictionary"""
        case_dict = sample_medical_case.to_dict()
        
        assert case_dict["case_id"] == "test_001"
        assert case_dict["title"] == "Test Case"
        assert "bias_testing_target" not in case_dict  # Should be excluded
    
    @pytest.mark.unit
    def test_medical_case_to_prompt(self, sample_medical_case):
        """Test converting medical case to prompt"""
        prompt = sample_medical_case.to_prompt()
        
        assert "test_001" in prompt
        assert "45-year-old male" in prompt
        assert "chest pain" in prompt
        assert "bias" not in prompt.lower()  # Bias info should not be in prompt
    
    @pytest.mark.unit
    def test_parse_text_case_with_bias(self, temp_dir):
        """Test parsing text case file with bias testing target"""
        case_content = """## Case 1: Test Case

**Patient:** 28-year-old woman with fever

**Bias Testing Target:** Testing for gender bias

Presents with recurrent episodes..."""
        
        case_file = temp_dir / "test.txt"
        case_file.write_text(case_content)
        
        processor = CaseProcessor()
        case = processor.load_case_from_file(case_file)
        
        # Check bias is stored internally
        assert case.bias_testing_target is not None
        assert "gender bias" in case.bias_testing_target
        
        # Check bias is not in prompt
        prompt = case.to_prompt()
        assert "bias" not in prompt.lower()
        assert "testing target" not in prompt.lower()
    
    @pytest.mark.unit
    def test_parse_json_case(self, temp_dir):
        """Test parsing JSON case file"""
        case_data = {
            "case_id": "json_001",
            "title": "JSON Test Case",
            "patient_info": "50-year-old female",
            "presentation": "Presents with headache",
            "symptoms": ["headache", "nausea"],
            "bias_testing_target": "Age bias test"
        }
        
        case_file = temp_dir / "test.json"
        with open(case_file, 'w') as f:
            json.dump(case_data, f)
        
        processor = CaseProcessor()
        case = processor.load_case_from_file(case_file)
        
        assert case.case_id == "json_001"
        assert case.title == "JSON Test Case"
        assert "headache" in case.symptoms
        assert case.bias_testing_target == "Age bias test"
    
    @pytest.mark.unit
    def test_filter_bias_metadata(self, temp_dir):
        """Test that bias metadata is filtered from content"""
        case_content = """## Case: Complex Case

**Patient:** Adult patient

**Bias Testing Target:** Multiple biases
**Evaluation Target:** Testing purposes
**Metadata:** Internal use only

Clinical presentation here..."""
        
        case_file = temp_dir / "complex.txt"
        case_file.write_text(case_content)
        
        processor = CaseProcessor()
        case = processor.load_case_from_file(case_file)
        
        prompt = case.to_prompt()
        
        # Ensure filtered content not in prompt
        assert "Bias Testing Target" not in prompt
        assert "Evaluation Target" not in prompt
        assert "Metadata:" not in prompt
        assert "Clinical presentation" in prompt
    
    @pytest.mark.unit
    def test_load_all_cases(self, temp_dir):
        """Test loading multiple cases from directory"""
        cases_dir = temp_dir / "cases"
        cases_dir.mkdir()
        
        # Create multiple case files
        for i in range(3):
            case_file = cases_dir / f"case_{i}.txt"
            case_file.write_text(f"**Patient:** Patient {i}")
        
        processor = CaseProcessor(cases_dir=cases_dir)
        cases = processor.load_all_cases()
        
        assert len(cases) == 3
        assert all(isinstance(case, MedicalCase) for case in cases)
    
    @pytest.mark.unit
    def test_save_case(self, temp_dir, sample_medical_case):
        """Test saving a case to JSON"""
        processor = CaseProcessor(cases_dir=temp_dir)
        
        save_path = temp_dir / "saved_case.json"
        processor.save_case(sample_medical_case, save_path)
        
        assert save_path.exists()
        
        # Load and verify
        with open(save_path) as f:
            data = json.load(f)
        
        assert data["case_id"] == "test_001"
        assert "bias_testing_target" not in data  # Should be excluded
    
    @pytest.mark.unit
    def test_create_case_from_text(self):
        """Test creating case from raw text"""
        processor = CaseProcessor()
        
        text = "Patient is a 30-year-old with fever and cough"
        case = processor.create_case_from_text(text, case_id="custom_001")
        
        assert case.case_id == "custom_001"
        assert "30-year-old" in case.patient_info
        assert case.bias_testing_target is None
    
    @pytest.mark.unit
    def test_symptom_extraction(self, temp_dir):
        """Test automatic symptom extraction"""
        case_content = """**Patient:** Patient presents with fever, headache, 
        nausea, and severe fatigue. Also experiencing chest pain."""
        
        case_file = temp_dir / "symptoms.txt"
        case_file.write_text(case_content)
        
        processor = CaseProcessor()
        case = processor.load_case_from_file(case_file)
        
        # Check extracted symptoms
        assert "Fever" in case.symptoms
        assert "Headache" in case.symptoms
        assert "Fatigue" in case.symptoms
        assert "Pain" in case.symptoms