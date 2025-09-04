"""
Unit tests for all evaluation cases
Ensures bias filtering works for all 11 cases
"""

import pytest
from pathlib import Path

from src.medley.processors.case_processor import CaseProcessor


class TestAllCases:
    """Test all evaluation cases for proper bias filtering"""
    
    @pytest.mark.unit
    @pytest.mark.parametrize("case_file", [
        "case_001_fmf.txt",
        "case_002_elderly.txt",
        "case_003_homeless.txt",
        "case_004_rare_genetic.txt",
        "case_005_environmental.txt",
        "case_006_disability_communication.txt",
        "case_007_gender_identity.txt",
        "case_008_rural_healthcare.txt",
        "case_009_weight_bias.txt",
        "case_010_migration_trauma.txt",
        "case_011_ethnic_medication.txt",
        "case_012_silent_organ_damage.txt"
    ])
    def test_case_bias_filtering(self, case_file):
        """Test that bias testing targets are filtered from all cases"""
        # Assuming cases are in medley/usecases directory
        case_path = Path(__file__).parent.parent.parent / "usecases" / case_file
        
        if not case_path.exists():
            pytest.skip(f"Case file {case_file} not found")
        
        processor = CaseProcessor()
        case = processor.load_case_from_file(case_path)
        
        # Verify bias target is extracted
        assert case.bias_testing_target is not None, f"No bias target found in {case_file}"
        assert len(case.bias_testing_target) > 0, f"Empty bias target in {case_file}"
        
        # Verify bias is NOT in prompt
        prompt = case.to_prompt()
        prompt_lower = prompt.lower()
        
        # Check that the specific bias testing line is filtered
        # We're looking for the metadata line, not just any occurrence of these words
        assert "**bias testing target:" not in prompt_lower, f"Found bias testing metadata in prompt for {case_file}"
        assert "**evaluation target:" not in prompt_lower, f"Found evaluation metadata in prompt for {case_file}"
        
        # These should definitely not appear as they're only in metadata
        if "bias testing target:" in prompt_lower:
            # Make sure it's not part of the actual case content
            lines = prompt.split('\n')
            for line in lines:
                if line.strip().startswith("**") and "bias testing target:" in line.lower():
                    assert False, f"Found bias testing metadata line in {case_file}"
        
        # Verify patient info IS in prompt
        assert "patient" in prompt_lower, f"Patient info missing from {case_file}"
        
        # Verify bias target is NOT in external dict
        case_dict = case.to_dict()
        assert "bias_testing_target" not in case_dict, f"Bias target exposed in dict for {case_file}"
    
    @pytest.mark.unit
    def test_all_cases_have_unique_ids(self):
        """Test that all cases have unique IDs"""
        cases_dir = Path(__file__).parent.parent.parent / "usecases"
        
        if not cases_dir.exists():
            pytest.skip("Cases directory not found")
        
        processor = CaseProcessor(cases_dir=cases_dir)
        cases = processor.load_all_cases()
        
        case_ids = [case.case_id for case in cases]
        
        # Check uniqueness
        assert len(case_ids) == len(set(case_ids)), "Duplicate case IDs found"
        
        # Verify we have all 12 cases
        assert len(cases) >= 12, f"Expected at least 12 cases, found {len(cases)}"
    
    @pytest.mark.unit
    def test_case_content_preservation(self):
        """Test that medical content is preserved after filtering"""
        cases_dir = Path(__file__).parent.parent.parent / "usecases"
        
        if not cases_dir.exists():
            pytest.skip("Cases directory not found")
        
        # Test a specific case with known content
        case_path = cases_dir / "case_006_disability_communication.txt"
        if not case_path.exists():
            pytest.skip("Case 006 not found")
        
        processor = CaseProcessor()
        case = processor.load_case_from_file(case_path)
        
        prompt = case.to_prompt()
        
        # Verify medical content is preserved
        assert "54-year-old deaf man" in prompt
        assert "shortness of breath" in prompt
        assert "ASL" in prompt or "American Sign Language" in prompt
        assert "diabetes" in prompt
        assert "hypertension" in prompt
        
        # But bias content is filtered
        assert "disability bias" not in prompt.lower()
        assert "communication barrier" not in prompt.lower()
    
    @pytest.mark.unit
    def test_case_012_hypertensive_crisis(self):
        """Test Case 12 specific content - hypertensive crisis"""
        cases_dir = Path(__file__).parent.parent.parent / "usecases"
        
        if not cases_dir.exists():
            pytest.skip("Cases directory not found")
        
        case_path = cases_dir / "case_012_silent_organ_damage.txt"
        if not case_path.exists():
            pytest.skip("Case 012 not found")
        
        processor = CaseProcessor()
        case = processor.load_case_from_file(case_path)
        
        prompt = case.to_prompt()
        
        # Verify critical medical content is preserved
        assert "230/180" in prompt or "230/180 mmHg" in prompt
        assert "eGFR" in prompt
        assert "liraglutide" in prompt or "Saxenda" in prompt
        assert "50-year-old" in prompt
        assert "researcher" in prompt
        
        # Verify bias metadata line is filtered (not just the words)
        assert "**bias testing target:" not in prompt.lower()
        
        # The bias target should be stored internally
        assert case.bias_testing_target is not None
        assert "urgency" in case.bias_testing_target.lower() or "calm demeanor" in case.bias_testing_target.lower()
    
    @pytest.mark.unit
    def test_case_categories(self):
        """Test that cases cover all bias categories"""
        cases_dir = Path(__file__).parent.parent.parent / "usecases"
        
        if not cases_dir.exists():
            pytest.skip("Cases directory not found")
        
        processor = CaseProcessor(cases_dir=cases_dir)
        cases = processor.load_all_cases()
        
        # Categories we expect to find in bias targets
        expected_categories = [
            "cultural", "geographic", "ethnic",  # Cultural biases
            "age", "gender",                      # Demographic biases
            "socioeconomic", "homeless",          # Social biases
            "disability", "communication",        # Access biases
            "weight", "rural", "migration"        # Other biases
        ]
        
        # Collect all bias targets
        all_bias_targets = " ".join([
            case.bias_testing_target.lower() 
            for case in cases 
            if case.bias_testing_target
        ])
        
        # Verify each category is represented
        categories_found = []
        for category in expected_categories:
            if category in all_bias_targets:
                categories_found.append(category)
        
        # Should find most categories (allow some flexibility)
        assert len(categories_found) >= 8, f"Only found {len(categories_found)} bias categories"