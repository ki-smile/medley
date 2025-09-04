# Medley Developer Documentation

## Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                      CLI Interface                       │
│                    (medley/cli.py)                      │
└────────────────────────┬────────────────────────────────┘
                         │
┌────────────────────────┴────────────────────────────────┐
│                    Core Components                       │
├──────────────┬──────────────┬──────────────┬───────────┤
│  LLMManager  │ CaseProcessor│ResponseParser│CacheManager│
│              │              │              │           │
│ • API calls  │ • Load cases │ • Parse LLM  │ • Storage │
│ • Async ops  │ • Filter bias│   responses  │ • Retrieval│
│ • Retry logic│ • Format     │ • Standardize│ • Indexing│
└──────────────┴──────────────┴──────────────┴───────────┘
                         │
┌─────────────────────────────────────────────────────────┐
│                  Configuration Layer                     │
│                  (utils/config.py)                       │
│         • Environment variables                          │
│         • YAML configurations                           │
│         • Model profiles                                │
└─────────────────────────────────────────────────────────┘
```

## Development Setup

### Prerequisites

- Python 3.8+
- Git
- Virtual environment tool (venv, conda, etc.)

### Local Development

1. **Clone and setup:**
```bash
git clone <repository>
cd medley
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -e ".[dev]"
```

2. **Pre-commit hooks:**
```bash
pip install pre-commit
pre-commit install
```

3. **Environment variables:**
```bash
cp .env.example .env
# Edit .env with your configuration
```

## Testing

### Running Tests

```bash
# All tests
pytest

# Unit tests only
pytest -m unit

# Integration tests only
pytest -m integration

# With coverage
pytest --cov=src/medley --cov-report=html

# Specific module
pytest tests/unit/test_cache_manager.py

# Verbose output
pytest -vv
```

### Test Structure

```
tests/
├── conftest.py          # Shared fixtures
├── unit/               # Unit tests
│   ├── test_config.py
│   ├── test_case_processor.py
│   ├── test_response_parser.py
│   ├── test_cache_manager.py
│   └── test_llm_manager.py
└── integration/        # Integration tests
    └── test_end_to_end.py
```

### Writing Tests

#### Unit Test Example
```python
@pytest.mark.unit
def test_filter_bias_metadata(temp_dir):
    """Test that bias metadata is filtered"""
    case_content = "**Patient:** Test\n**Bias Testing Target:** Test bias"
    
    processor = CaseProcessor()
    case = processor.load_case_from_file(case_file)
    
    assert case.bias_testing_target is not None  # Stored internally
    assert "bias" not in case.to_prompt().lower()  # Filtered from prompt
```

#### Integration Test Example
```python
@pytest.mark.integration
def test_full_workflow(temp_dir):
    """Test complete case analysis workflow"""
    # Setup components
    config = Config(config_dir=temp_dir)
    # ... test end-to-end flow
```

### Test Fixtures

Key fixtures in `conftest.py`:
- `temp_dir`: Temporary directory for test files
- `mock_config`: Mock configuration
- `sample_medical_case`: Sample case object
- `sample_llm_response`: Sample LLM response
- `mock_api_client`: Mocked API client

## Code Standards

### Style Guide

- **Python**: PEP 8 compliant
- **Line length**: 88 characters (Black default)
- **Imports**: Sorted with isort
- **Type hints**: Use for all public functions
- **Docstrings**: Google style

### Code Formatting

```bash
# Format code
black src/ tests/

# Sort imports
isort src/ tests/

# Type checking
mypy src/

# Linting
flake8 src/ tests/
```

### Docstring Example

```python
def process_case(self, case_file: Path) -> MedicalCase:
    """Process a medical case file.
    
    Args:
        case_file: Path to the case file
        
    Returns:
        MedicalCase: Processed medical case object
        
    Raises:
        FileNotFoundError: If case file doesn't exist
        ValueError: If file format is unsupported
    """
```

## Adding New Features

### 1. Adding a New Model

Edit `config/models.yaml`:
```yaml
new-model:
  name: "New Model Name"
  provider: "provider"
  model_id: "provider/model-id"
  max_tokens: 4096
  temperature: 0.7
```

### 2. Adding a New Parser

Create `src/medley/processors/new_parser.py`:
```python
class NewParser:
    def parse(self, response: str) -> ParsedResponse:
        # Implementation
        pass
```

### 3. Adding a CLI Command

Edit `src/medley/cli.py`:
```python
@cli.command()
@click.option('--option', help='Option help')
def new_command(option):
    """Command description."""
    # Implementation
```

## API Integration

### OpenRouter API

Current implementation uses OpenRouter for LLM access:

```python
class LLMManager:
    OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"
    
    def query_model(self, model_config, prompt):
        payload = {
            "model": model_config.model_id,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": model_config.max_tokens,
            "temperature": model_config.temperature,
        }
        response = requests.post(self.OPENROUTER_API_URL, 
                                json=payload, 
                                headers=self.headers)
```

### Adding Alternative API Providers

1. Create provider adapter:
```python
class AlternativeProvider:
    def query(self, model_id: str, prompt: str) -> Dict:
        # Provider-specific implementation
        pass
```

2. Update `LLMManager` to support multiple providers:
```python
def query_model(self, model_config, prompt):
    provider = self.get_provider(model_config.provider)
    return provider.query(model_config.model_id, prompt)
```

## Bias Filtering System

### How It Works

1. **Input Processing:**
   - Case files contain bias testing targets
   - `CaseProcessor._parse_text_case()` identifies bias metadata

2. **Filtering:**
   - Lines with bias keywords are removed
   - Clean content sent to LLMs
   - Bias data stored in `bias_testing_target` field

3. **Storage:**
   - Internal: `MedicalCase.bias_testing_target`
   - External: Excluded from `to_dict()` and `to_prompt()`

### Adding New Filter Keywords

Edit `src/medley/processors/case_processor.py`:
```python
lines_to_exclude = [
    "bias testing target",
    "your_new_keyword",  # Add here
]
```

## Cache System

### Cache Structure

```
cache/
├── responses/          # Individual model responses
│   └── case_id/
│       └── model_hash.json
├── ensembles/         # Ensemble analysis results
│   └── case_id_ensemble.json
└── metadata/          # Cache metadata
    ├── cache_index.json
    └── prompt_hashes.json
```

### Cache Key Generation

```python
def generate_cache_key(prompt, model_id, system_prompt=None):
    cache_input = f"{prompt}|{model_id}|{system_prompt or ''}"
    return hashlib.sha256(cache_input.encode()).hexdigest()[:16]
```

## Performance Optimization

### Async Operations

For parallel model queries:
```python
async def query_models_parallel(models, prompt):
    async with aiohttp.ClientSession() as session:
        tasks = [query_model_async(session, m, prompt) for m in models]
        return await asyncio.gather(*tasks)
```

### Caching Strategy

- Default cache expiry: 24 hours
- Hash-based cache keys
- File-based storage for persistence
- Indexed for fast lookup

## Debugging

### Enable Debug Logging

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Common Debug Points

1. **API Requests:**
```python
# In llm_manager.py
logger.debug(f"API Request: {payload}")
logger.debug(f"API Response: {response.text}")
```

2. **Cache Operations:**
```python
# In cache_manager.py
logger.debug(f"Cache key: {cache_key}")
logger.debug(f"Cache hit: {cached is not None}")
```

3. **Bias Filtering:**
```python
# In case_processor.py
logger.debug(f"Original content length: {len(original)}")
logger.debug(f"Filtered content length: {len(filtered)}")
```

## Deployment

### Docker

Create `Dockerfile`:
```dockerfile
FROM python:3.8-slim
WORKDIR /app
COPY . .
RUN pip install -e .
CMD ["medley", "--help"]
```

Build and run:
```bash
docker build -t medley .
docker run -e OPENROUTER_API_KEY=$OPENROUTER_API_KEY medley
```

### Environment Variables

Production environment variables:
```bash
OPENROUTER_API_KEY=<production-key>
MEDLEY_CACHE_DIR=/var/cache/medley
MEDLEY_REPORTS_DIR=/var/reports/medley
MEDLEY_LOG_LEVEL=INFO
```

## Contributing

### Workflow

1. Fork repository
2. Create feature branch
3. Make changes with tests
4. Run test suite
5. Submit pull request

### Pull Request Checklist

- [ ] Tests pass (`pytest`)
- [ ] Code formatted (`black`)
- [ ] Type hints added
- [ ] Documentation updated
- [ ] Changelog entry added

### Commit Messages

Format: `type: description`

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation
- `test`: Testing
- `refactor`: Code refactoring
- `style`: Formatting
- `chore`: Maintenance

Example:
```
feat: add support for Claude models
fix: resolve cache key collision issue
docs: update API documentation
```

## Phase 2 Planning

### Multi-Model Ensemble

```python
class EnsembleOrchestrator:
    def analyze(self, case: MedicalCase) -> EnsembleResult:
        # 1. Query all models in parallel
        responses = await self.query_all_models(case)
        
        # 2. Parse responses
        parsed = [parser.parse(r) for r in responses]
        
        # 3. Calculate consensus
        consensus = self.consensus_engine.calculate(parsed)
        
        # 4. Detect biases
        biases = self.bias_detector.analyze(parsed)
        
        return EnsembleResult(consensus, biases)
```

### Consensus Algorithm

```python
class ConsensusEngine:
    def calculate(self, responses: List[DiagnosticResponse]):
        # Weighted voting
        # Minority opinion preservation
        # Confidence adjustment
        pass
```

### Bias Attribution

```python
class BiasDetector:
    def analyze(self, responses: List[DiagnosticResponse]):
        # Compare responses by model origin
        # Identify systematic differences
        # Attribute to model characteristics
        pass
```

## Resources

- [OpenRouter API Docs](https://openrouter.ai/docs)
- [Python Packaging Guide](https://packaging.python.org)
- [pytest Documentation](https://docs.pytest.org)
- [Black Formatter](https://black.readthedocs.io)
- [Type Hints](https://docs.python.org/3/library/typing.html)