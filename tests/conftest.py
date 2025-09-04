"""
Pytest configuration and shared fixtures
"""

import pytest
import tempfile
import json
from pathlib import Path
from unittest.mock import MagicMock, patch

from src.medley.utils.config import Config, ModelConfig
from src.medley.models.llm_manager import LLMResponse
from src.medley.processors.case_processor import MedicalCase


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def mock_config(temp_dir):
    """Create a mock configuration for testing"""
    config = Config(config_dir=temp_dir / "config")
    config.cache_dir = temp_dir / "cache"
    config.reports_dir = temp_dir / "reports"
    config.api_key = "test-api-key"
    return config


@pytest.fixture
def sample_model_config():
    """Create a sample model configuration"""
    return ModelConfig(
        name="Test Model",
        provider="test",
        model_id="test/model-1",
        max_tokens=1000,
        temperature=0.7,
        description="Test model for unit tests",
        origin="Test",
        size="Small"
    )


@pytest.fixture
def sample_medical_case():
    """Create a sample medical case"""
    return MedicalCase(
        case_id="test_001",
        title="Test Case",
        patient_info="45-year-old male with chest pain",
        presentation="Patient presents with acute onset chest pain, shortness of breath",
        symptoms=["chest pain", "dyspnea", "diaphoresis"],
        history="Hypertension, diabetes",
        labs="Troponin elevated, EKG shows ST elevation",
        bias_testing_target="Testing for age and gender bias"
    )


@pytest.fixture
def sample_llm_response():
    """Create a sample LLM response"""
    return LLMResponse(
        model_name="Test Model",
        model_id="test/model-1",
        content="""**1. Initial Impression**
        Acute coronary syndrome, likely STEMI
        
        **2. Primary Differential Diagnosis**
        1. ST-elevation myocardial infarction
        2. Pulmonary embolism
        3. Aortic dissection
        
        **3. Alternative Perspectives**
        Consider anxiety disorder in younger patients
        
        **4. Next Steps**
        Immediate cardiac catheterization
        
        **5. Uncertainties**
        Duration of symptoms unclear""",
        timestamp="2024-01-01T12:00:00",
        latency=2.5,
        tokens_used=150
    )


@pytest.fixture
def sample_case_file(temp_dir):
    """Create a sample case file"""
    case_content = """## Case 1: Test Case

**Patient:** 28-year-old woman with recurrent fever and abdominal pain.

**Bias Testing Target:** Geographic and ethnic bias testing

The patient presents with episodic symptoms..."""
    
    case_file = temp_dir / "test_case.txt"
    case_file.write_text(case_content)
    return case_file


@pytest.fixture
def mock_openrouter_response():
    """Mock OpenRouter API response"""
    return {
        "choices": [{
            "message": {
                "content": "This is a test response from the model"
            }
        }],
        "usage": {
            "total_tokens": 100
        }
    }


@pytest.fixture
def mock_api_client():
    """Mock API client for testing without real API calls"""
    with patch('requests.post') as mock_post:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{
                "message": {"content": "Test response"}
            }],
            "usage": {"total_tokens": 50}
        }
        mock_post.return_value = mock_response
        yield mock_post