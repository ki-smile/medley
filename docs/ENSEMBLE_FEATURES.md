# Medley Ensemble Features

## Model Selection and Requirements

### Minimum Models Requirement
- **Minimum 3 models** are always required for ensemble analysis
- System automatically adds more models if user specifies fewer than 3
- Warnings displayed if fewer than 3 models respond successfully

### Model Categories

#### Free Models (7 available)
1. **Mistral 7B** (France) - mistralai/mistral-7b-instruct:free
2. **Gemma 2 9B** (USA) - google/gemma-2-9b-it:free  
3. **Llama 3.2 3B** (USA) - meta-llama/llama-3.2-3b-instruct:free
4. **Qwen 2.5 Coder 32B** (China) - qwen/qwen-2.5-coder-32b-instruct
5. **Phi 3.5 Mini** (USA) - microsoft/phi-3.5-mini-instruct:free
6. **LFM 40B** (USA) - liquid/lfm-40b:free
7. **Hermes 3** (USA) - nousresearch/hermes-3-llama-3.1-8b:free

#### Paid Models (8 available)
1. **Claude 3 Haiku** (USA) - $0.25/$1.25 per 1M tokens
2. **GPT-4o Mini** (USA) - $0.15/$0.60 per 1M tokens
3. **Mistral Small** (France) - $0.20/$0.60 per 1M tokens
4. **DeepSeek Chat** (China) - $0.14/$0.28 per 1M tokens
5. **Gemini Flash 1.5** (USA) - $0.075/$0.30 per 1M tokens
6. **Perplexity Sonar** (USA) - $0.20/$0.20 per 1M tokens
7. **Command-R** (Canada) - $0.15/$0.60 per 1M tokens
8. **Grok 2 Mini** (USA) - $2/$10 per 1M tokens

## CLI Usage

### Basic Ensemble Analysis
```bash
# Default: uses mix of free and paid models
medley ensemble case_file.txt

# Generate PDF report
medley ensemble case_file.txt --format pdf

# Custom output directory
medley ensemble case_file.txt --output-dir reports/
```

### Model Selection Options
```bash
# Use only free models
medley ensemble case_file.txt --free-only

# Use paid models with limit
medley ensemble case_file.txt --use-paid --max-paid 3

# Specify exact models to use
medley ensemble case_file.txt -m mistral -m gemma -m claude

# Skip cache for fresh responses
medley ensemble case_file.txt --no-cache
```

### Report Format Options
```bash
# Markdown (default)
medley ensemble case_file.txt --format markdown

# PDF for professional reports
medley ensemble case_file.txt --format pdf

# HTML for web viewing
medley ensemble case_file.txt --format html

# Plain text
medley ensemble case_file.txt --format text
```

## Python API Usage

```python
from medley.models.ensemble import EnsembleOrchestrator
from medley.reporters.consensus_report import ConsensusReportGenerator
from medley.utils.config import Config

# Initialize
config = Config()
orchestrator = EnsembleOrchestrator(config)
report_generator = ConsensusReportGenerator()

# Run ensemble analysis
results = orchestrator.run_ensemble_analysis(
    case_file="case.txt",
    models=None,  # Use defaults
    output_dir="results/",
    use_paid_models=True,  # Include paid models
    max_paid_models=3  # Limit paid models
)

# Generate report
report_generator.generate_report(
    ensemble_results=results,
    output_format="pdf",
    output_file="report.pdf"
)
```

## Key Features

### Automatic Model Management
- Ensures minimum 3 models for statistical validity
- Automatically selects diverse models (different origins)
- Gracefully handles model failures
- Caches responses to minimize API costs

### Consensus Analysis
- Calculates agreement levels across models
- Identifies geographic/origin patterns
- Preserves minority opinions
- Detects potential biases

### Smart Model Selection
1. **Free models first** - Always tries free models to minimize costs
2. **Geographic diversity** - Selects models from different regions
3. **Fallback mechanism** - Adds backup models if primary ones fail
4. **Cost optimization** - Limits paid model usage based on settings

### Response Validation
- Tracks successful vs failed responses
- Warns if below minimum threshold
- Proceeds with available models when possible
- Clear error reporting for troubleshooting

## Configuration

### Environment Variables
```bash
# Required: OpenRouter API key
export OPENROUTER_API_KEY="your-api-key"
```

### Default Behavior
- Minimum 3 models required
- Mix of free and paid models (if API key has credits)
- Maximum 3 paid models by default
- Caching enabled by default

### Customization
- Specify exact models with `-m` flag
- Control paid model usage with `--free-only` or `--max-paid`
- Skip cache with `--no-cache` for fresh responses
- Choose report format with `--format`

## Cost Considerations

### Free Tier Usage
```bash
# Use only free models (no charges)
medley ensemble case.txt --free-only
```

### Mixed Usage (Recommended)
```bash
# Default: up to 3 paid models for better diversity
medley ensemble case.txt --use-paid --max-paid 3
```

### Cost Estimates (per query)
- **Free only**: $0
- **With 2 paid models**: ~$0.001-0.003
- **With 3 paid models**: ~$0.002-0.005
- **Premium models**: ~$0.01-0.02

*Note: Actual costs depend on prompt length and model selection*

## Success Metrics

The system tracks and reports:
- **Models Queried**: Total attempted
- **Successful Responses**: Models that responded
- **Consensus Level**: Strong/Partial/None
- **Primary Diagnosis Confidence**: Percentage agreement
- **Geographic Patterns**: Regional diagnostic variations
- **Bias Considerations**: Identified potential biases

## Error Handling

- **Model Failures**: Continues with available models
- **Below Minimum**: Warns but proceeds if possible
- **No Responses**: Raises error, cannot proceed
- **API Errors**: Cached responses used when available
- **Rate Limits**: Automatically handled by OpenRouter

## Best Practices

1. **Always use at least 3 models** for reliable consensus
2. **Mix free and paid models** for optimal diversity
3. **Include models from different regions** for bias detection
4. **Use caching** to minimize API costs during development
5. **Generate PDF reports** for professional documentation
6. **Monitor success rates** to ensure quality results