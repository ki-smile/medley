# 🧪 MEDLEY Test Suite

## Test Coverage Summary

### Unit Tests (tests/unit/)
| Test File | Coverage | Description |
|-----------|----------|-------------|
| `test_all_cases.py` | ✅ | Tests all 13 medical cases |
| `test_cache_manager.py` | ✅ | Cache operations and validation |
| `test_case_processor.py` | ✅ | Medical case processing |
| `test_config.py` | ✅ | Configuration management |
| `test_llm_manager.py` | ✅ | LLM API interactions |
| `test_llm_manager_enhanced.py` | ✅ | Enhanced LLM features |
| `test_response_parser.py` | ✅ | Response parsing logic |
| `test_orchestrator.py` | ✅ | Orchestrator functionality |

### Integration Tests (tests/integration/)
| Test File | Coverage | Description |
|-----------|----------|-------------|
| `test_end_to_end.py` | ✅ | Complete pipeline testing |
| `test_pipeline_enhanced.py` | ✅ | Enhanced pipeline features |

### Web Tests
| Test File | Coverage | Description |
|-----------|----------|-------------|
| `test_web_app.py` | ✅ | Flask application tests |
| `test_web_integration.py` | ✅ | Web interface integration |

### System Tests
| Test File | Coverage | Description |
|-----------|----------|-------------|
| `health_check.py` | ✅ | System health monitoring |

---

## Running Tests

### Quick Test Commands

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=medley --cov-report=html

# Run specific test file
pytest tests/unit/test_cache_manager.py

# Run with verbose output
pytest -v

# Run only unit tests
pytest tests/unit/

# Run only integration tests
pytest tests/integration/

# Run tests in parallel
pytest -n auto
```

### Using Test Script

```bash
# Make script executable
chmod +x tests/run_tests.sh

# Run all tests with coverage
./tests/run_tests.sh
```

### Test Configuration

The test suite uses `pytest.ini` and `conftest.py` for configuration:

```ini
# pytest.ini
[tool:pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = -ra -q --strict-markers
markers =
    slow: marks tests as slow
    integration: marks tests as integration tests
    unit: marks tests as unit tests
```

---

## Test Categories

### 1. Core Functionality Tests

```python
# Test medical pipeline
def test_complete_medical_analysis():
    pipeline = GeneralMedicalPipeline("Test_Case")
    results = pipeline.run_complete_analysis(case_text)
    assert results['status'] == 'success'
    assert 'primary_diagnosis' in results
```

### 2. Model Integration Tests

```python
# Test model querying
def test_model_query():
    manager = LLMManager(config)
    response = manager.query_model(model_config, prompt)
    assert response.content is not None
    assert response.error is None
```

### 3. Cache Tests

```python
# Test cache operations
def test_cache_storage_and_retrieval():
    cache = CacheManager()
    cache.save_response(case_id, model_id, response)
    cached = cache.get_cached_response(case_id, model_id)
    assert cached == response
```

### 4. Web Interface Tests

```python
# Test web endpoints
def test_analyze_endpoint():
    response = client.post('/analyze', json={
        'case_text': 'Patient symptoms...',
        'models': ['gpt-4', 'claude']
    })
    assert response.status_code == 200
```

### 5. Orchestrator Tests

```python
# Test orchestration
def test_consensus_building():
    orchestrator = Orchestrator()
    consensus = orchestrator.build_consensus(responses)
    assert consensus['primary_diagnosis'] is not None
    assert consensus['confidence'] > 0.5
```

---

## Coverage Report

Current test coverage (as of August 2025):

```
Name                                  Stmts   Miss  Cover
---------------------------------------------------------
medley/__init__.py                       10      0   100%
medley/models/llm_manager.py           245     12    95%
medley/processors/cache_manager.py     156      8    95%
medley/processors/case_processor.py     89      3    97%
medley/reporters/pdf_generator.py      312     18    94%
medley/utils/config.py                  67      2    97%
web_app.py                             425     35    92%
web_orchestrator.py                    198     15    92%
general_medical_pipeline.py           567     42    93%
---------------------------------------------------------
TOTAL                                 2069    135    93%
```

---

## Fixtures and Test Data

### Common Fixtures (conftest.py)

```python
@pytest.fixture
def sample_case():
    """Sample medical case for testing"""
    return {
        'description': 'Patient presents with...',
        'age': 45,
        'gender': 'Female'
    }

@pytest.fixture
def mock_llm_response():
    """Mock LLM response"""
    return {
        'diagnosis': 'Test Diagnosis',
        'confidence': 0.85
    }

@pytest.fixture
def test_config():
    """Test configuration"""
    return Config(test_mode=True)
```

---

## Continuous Integration

### GitHub Actions Workflow

```yaml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: '3.10'
      - run: pip install -r requirements.txt
      - run: pytest --cov=medley
```

---

## Mock Testing

### Mocking External APIs

```python
@patch('medley.models.llm_manager.requests.post')
def test_api_call_with_mock(mock_post):
    mock_post.return_value.json.return_value = {
        'choices': [{'message': {'content': 'Mocked response'}}]
    }
    
    manager = LLMManager()
    response = manager.query_model('gpt-4', 'test prompt')
    assert response == 'Mocked response'
```

---

## Performance Testing

### Load Testing

```python
def test_concurrent_model_queries():
    """Test system under load"""
    import concurrent.futures
    
    def query_model(i):
        return pipeline.query_single_model(f"model_{i}", "test")
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(query_model, i) for i in range(10)]
        results = [f.result() for f in futures]
    
    assert len(results) == 10
```

---

## Test Best Practices

1. **Isolation**: Each test should be independent
2. **Clarity**: Test names should describe what they test
3. **Speed**: Unit tests should run quickly (<1s each)
4. **Coverage**: Aim for >90% code coverage
5. **Mocking**: Mock external dependencies
6. **Fixtures**: Use fixtures for common test data
7. **Markers**: Use pytest markers for test categorization

---

## Debugging Tests

```bash
# Run with debugging output
pytest -vv --tb=short

# Run with pdb on failure
pytest --pdb

# Run specific test with print statements
pytest -s tests/unit/test_cache_manager.py::test_specific

# Generate HTML coverage report
pytest --cov=medley --cov-report=html
open htmlcov/index.html
```

---

## Adding New Tests

Template for new test file:

```python
"""
Tests for [module name]
"""

import pytest
from unittest.mock import Mock, patch
from pathlib import Path
import sys

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from medley.module import YourClass


class TestYourClass:
    """Test suite for YourClass"""
    
    @pytest.fixture
    def instance(self):
        """Create instance for testing"""
        return YourClass()
    
    def test_basic_functionality(self, instance):
        """Test basic functionality"""
        result = instance.method()
        assert result is not None
    
    @pytest.mark.slow
    def test_complex_operation(self, instance):
        """Test complex operation"""
        result = instance.complex_method()
        assert result['status'] == 'success'
```

---

**Maintained by**: SMAILE Team  
**Last Updated**: August 2025