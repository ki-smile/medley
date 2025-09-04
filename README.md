# 🏥 MEDLEY - Medical AI Ensemble System

**Multi-Model Medical Diagnostic System with Bias-Aware Analysis**

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue)](https://www.python.org/)
[![Models](https://img.shields.io/badge/AI%20Models-31-green)](https://openrouter.ai/)
[![Countries](https://img.shields.io/badge/Countries-6-orange)](https://github.com/)
[![License](https://img.shields.io/badge/License-MIT-purple)](LICENSE)

**Author:** Farhad Abtahi  
**Developed by:** SMAILE (Stockholm Medical Artificial Intelligence and Learning Environments) at Karolinska Institutet  
**Website:** [smile.ki.se](https://smile.ki.se)

## 🎯 Overview

MEDLEY is a sophisticated medical AI ensemble system that orchestrates multiple Large Language Models (LLMs) from diverse geographical and cultural backgrounds to provide comprehensive, bias-aware diagnostic analysis. The system implements concepts from "Embracing Imperfection: A Perspective on Leveraging Bias and Hallucination in Medical AI for Enhanced Human Decision-Making" ([arXiv:2508.21648](https://arxiv.org/abs/2508.21648)).

### Key Capabilities
- **31 AI Models** from 6 countries providing diverse perspectives
- **Bias-aware analysis** with geographical and cultural attribution
- **Consensus building** with minority opinion preservation
- **Professional PDF reports** with evidence-based diagnoses
- **ICD-10 integration** for standardized diagnostic coding

## 🚀 Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/medley.git
cd medley

# Install dependencies
pip install -r requirements.txt

# Or install as package
pip install -e .
```

### Configuration

1. **Get OpenRouter API key** from [OpenRouter](https://openrouter.ai/)

2. **Set environment variable**:
```bash
export OPENROUTER_API_KEY='your-api-key-here'
# Or create .env file
echo "OPENROUTER_API_KEY=your-api-key-here" > .env
```

### Usage Options

#### 🌐 Web Interface (Recommended)

```bash
# Start the web application
python web_app.py

# Open browser to http://127.0.0.1:5000
# Features:
# - Interactive case gallery with 12 pre-analyzed cases
# - Real-time model response viewer
# - Downloadable PDF reports
# - Model performance analytics
# - Health monitoring at /api/health
```

#### 🖥️ Command Line Interface

##### Standard MEDLEY CLI
```bash
# Basic ensemble analysis with comprehensive report
medley ensemble usecases/case_001_fmf.txt --format pdf --report-type comprehensive

# Use only free models (Note: Uses OpenAI GPT OSS 20B for orchestration - best free option)
medley ensemble usecases/case_001_fmf.txt --free-only

# Specify particular models
medley ensemble usecases/case_001_fmf.txt -m "google/gemini-2.5-pro" -m "openai/gpt-5"

# Different report types
medley ensemble case.txt --report-type standard    # Basic consensus report
medley ensemble case.txt --report-type enhanced    # Diversity-focused report  
medley ensemble case.txt --report-type comprehensive # Full analysis (like Cases 1-12)
```

##### General Medical Pipeline (Advanced)
```bash
# Generate comprehensive report like Cases 1-12
python general_medical_pipeline.py "Case_1" "usecases/case_001_fmf.txt"

# This pipeline includes:
# - Comprehensive bias analysis
# - Model diversity metrics
# - Management strategies synthesis
# - Evidence synthesis with clinical correlations
# - Diagnostic landscape analysis
# - Full 31-model orchestration

# Run all test cases
python run_all_cases.py

# View generated report
open reports/FINAL_Case_1_comprehensive_*.pdf
```

**Note:** The `general_medical_pipeline.py` script generates the most comprehensive reports with all analysis components, while the standard MEDLEY CLI with `--report-type comprehensive` provides a streamlined version suitable for custom cases.

## 📊 System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     MEDLEY PIPELINE FLOW                     │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  [Medical Case] → [Prompt Engine] → [LLM Manager]           │
│                                           │                  │
│                                           ▼                  │
│                              ┌──────────────────────┐        │
│                              │  31 Parallel Queries │        │
│                              └──────────────────────┘        │
│                                           │                  │
│     ┌─────────────┬──────────────┬───────┴──────┬─────────┐ │
│     ▼             ▼              ▼              ▼         ▼ │
│  OpenAI      Anthropic       Google         Meta     Others │
│  (5 models)  (3 models)    (6 models)   (2 models) (15 models)│
│     │             │              │              │         │ │
│     └─────────────┴──────────────┴───────┬──────┴─────────┘ │
│                                           ▼                  │
│                              ┌──────────────────────┐        │
│                              │   Response Cache     │        │
│                              └──────────────────────┘        │
│                                           │                  │
│                                           ▼                  │
│                              ┌──────────────────────┐        │
│                              │  Consensus Engine    │        │
│                              │  - Primary diagnosis │        │
│                              │  - Alternatives      │        │
│                              │  - Minority opinions │        │
│                              └──────────────────────┘        │
│                                           │                  │
│                                           ▼                  │
│                              ┌──────────────────────┐        │
│                              │    Orchestrator      │        │
│                              │ (Claude Sonnet 4.0)  │        │
│                              └──────────────────────┘        │
│                                           │                  │
│                                           ▼                  │
│                              ┌──────────────────────┐        │
│                              │   PDF Generator      │        │
│                              │  - 6-page report     │        │
│                              │  - Visual analytics  │        │
│                              └──────────────────────┘        │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

## 🤖 Model Distribution

### Geographic Representation

| Country | Models | Providers | Perspective |
|---------|--------|-----------|-------------|
| 🇺🇸 USA | 20 | OpenAI, Anthropic, Google, Meta, X.AI, Microsoft, Perplexity, Liquid, Nous | Western medicine, tech industry |
| 🇨🇳 China | 4 | DeepSeek, Qwen, 01.AI | Traditional Chinese Medicine, Eastern approach |
| 🇫🇷 France | 3 | Mistral AI | European healthcare, GDPR-compliant |
| 🇨🇦 Canada | 2 | Cohere | Multicultural, universal healthcare |
| 🇯🇵 Japan/USA | 1 | Shisa AI | Bilingual, East-West integration |
| 🇮🇱 Israel | 1 | AI21 Labs | Middle Eastern, innovation focus |

### Model Categories

```
┌──────────────────────────────────────────────────────┐
│                  Model Performance Tiers              │
├──────────────────────────────────────────────────────┤
│                                                        │
│  PREMIUM (High Capability)                            │
│  ├─ OpenAI GPT-4o, GPT-5                             │
│  ├─ Anthropic Claude Opus 4.1                        │
│  ├─ Google Gemini 2.5 Pro                            │
│  └─ Mistral Large                                    │
│                                                        │
│  MID-RANGE (Balanced)                                │
│  ├─ Claude Sonnet, GPT-4o-mini                       │
│  ├─ Gemini Flash, Command R+                         │
│  └─ DeepSeek v3, Qwen Coder                         │
│                                                        │
│  BUDGET (Fast & Efficient)                           │
│  ├─ Claude Haiku, Gemini Flash Lite                  │
│  ├─ Mistral 7B, Llama 3.2                           │
│  └─ Free tier models                                 │
│                                                        │
└──────────────────────────────────────────────────────┘
```

### Orchestrator Models

The orchestrator model synthesizes all individual model responses into comprehensive analysis:

| Mode | Orchestrator Model | Quality | Use Case |
|------|-------------------|---------|----------|
| **Premium** | Claude 3.5 Sonnet | Excellent | Production, research |
| **Free** | OpenAI GPT OSS 20B | Good | Development, testing |

**Note:** Free models provide limited orchestration quality. For production use with accurate consensus building, bias detection, and clinical recommendations, premium orchestrators are recommended.

## 📋 Medical Test Cases

**Note:** Cases 1-12 were generated using the `general_medical_pipeline.py` script, which produces comprehensive analysis reports with additional components beyond the standard MEDLEY CLI output.

| Case | Condition | Bias Testing | Consensus |
|------|-----------|--------------|-----------|
| 1 | Familial Mediterranean Fever | Geographic/ethnic | 77.8% |
| 2 | Alzheimer's Disease | Age bias | 74.1% |
| 3 | Substance-Induced Psychosis | Socioeconomic | 85.2% |
| 4 | Rare Genetic Disorder | Knowledge limits | 50.0% |
| 5 | Environmental Toxin | Regional awareness | 4.5% |
| 6 | Disability Communication | Accessibility | 50.0% |
| 7 | Gender Identity Healthcare | Gender bias | 50.0% |
| 8 | Rural Healthcare Access | Geographic disparity | 50.0% |
| 9 | Weight-Related Diagnosis | Weight bias | 59.1% |
| 10 | Migration Trauma | Cultural sensitivity | 45.5% |
| 11 | Ethnic Medication Response | Pharmacogenetics | 50.0% |
| 12 | Pediatric Development | Age-specific care | 63.6% |

## 📄 Report Features

### PDF Report Structure (6 pages)

```
Page 1: Title & Overview
├─ Case Information
├─ Primary Diagnosis with ICD-10
├─ Alternative Diagnoses
└─ Analysis Overview

Page 2: Executive Summary
├─ Clinical Findings
├─ Key Symptoms Analysis
└─ Recommendations

Page 3: Diagnostic Landscape
├─ Consensus Analysis
├─ Alternative Diagnoses Detail
└─ Minority Opinions

Page 4: Management Strategies
├─ Immediate Actions
├─ Diagnostic Tests
└─ Treatment Options

Page 5: Model Diversity Analysis
├─ Geographic Distribution
├─ Bias Patterns
└─ Response Overview

Page 6: Decision Support
├─ Critical Decisions
├─ Evidence Synthesis
└─ Clinical Pathways
```

## 🌐 Web Application Features

### Interactive Dashboard
The MEDLEY web interface provides a modern, Material Design 3 experience for exploring medical AI ensemble analysis.

#### Key Features

##### 1. **Landing Page**
- Interactive animated flow diagram showing the ensemble process
- Model gallery displaying all 31 AI models with geographic origins
- Educational content about bias reduction through diversity

##### 2. **Case Gallery**
- 12 pre-analyzed medical cases with specialty tags
- Instant access to cached results (no API calls needed)
- Filter by medical specialty (Rheumatology, Genetics, etc.)

##### 3. **Report Viewer**
- **Tabbed Interface:**
  - Consensus Report: Primary and alternative diagnoses
  - Individual Models: View each model's response
  - Raw Responses: Access original JSON data
- **Diagnosis Categories:**
  - Strong Consensus (≥30% agreement)
  - Alternative Diagnoses (10-29%)
  - Minority Opinions (<10%)
- **ICD-10 Codes:** Automatic mapping for all diagnoses

##### 4. **Model Analytics**
- Geographic distribution visualization
- Consensus participation rates
- Bias pattern analysis
- Performance metrics per model

##### 5. **API Endpoints**
```bash
GET  /api/health          # System health check
GET  /api/cases           # List all available cases
GET  /api/case/{id}/report # Get case analysis report
GET  /api/case/{id}/pdf   # Download PDF report
GET  /api/case/{id}/models # Get individual model responses
GET  /api/performance     # Model performance metrics
POST /api/session/set-key # Set OpenRouter API key
```

### Web Interface Screenshots

```
┌────────────────────────────────────────────────────┐
│  MEDLEY - Medical AI Ensemble System               │
├────────────────────────────────────────────────────┤
│                                                     │
│  [Explore Cases] [How It Works] [View Models]      │
│                                                     │
│  ┌─────────────────────────────────────────────┐  │
│  │  Patient → 31 Models → Synthesis → Report   │  │
│  │    Case     Diverse    Evidence    Physician│  │
│  └─────────────────────────────────────────────┘  │
│                                                     │
│  Featured Cases:                                   │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐          │
│  │ FMF      │ │ Elderly  │ │ Genetic  │          │
│  │ Case 1   │ │ Case 2   │ │ Case 4   │          │
│  └──────────┘ └──────────┘ └──────────┘          │
│                                                     │
└────────────────────────────────────────────────────┘
```

## 🛠️ Advanced Usage

### Python API

```python
from medley import MedicalPipeline
from pathlib import Path

# Initialize pipeline
pipeline = MedicalPipeline(
    case_id="Case_1",
    cache_dir=Path("cache"),
    output_dir=Path("reports")
)

# Load and analyze case
case_text = pipeline.load_case("path/to/case.txt")
results = pipeline.run_analysis(
    case_text,
    models_to_query=["openai/gpt-4o", "anthropic/claude-3-opus"],
    max_parallel=10
)

# Generate comprehensive report
report = pipeline.generate_report(
    results,
    include_bias_analysis=True,
    include_minority_opinions=True
)

print(f"Report saved: {report.path}")
print(f"Primary diagnosis: {results.primary_diagnosis}")
print(f"Consensus level: {results.consensus_percentage}%")
```

### Custom Configuration

```yaml
# config/pipeline.yaml
pipeline:
  max_parallel_queries: 10
  timeout_seconds: 60
  retry_attempts: 2
  cache_enabled: true
  
orchestrator:
  model: "anthropic/claude-3-5-sonnet-20241022"
  fallback_model: "anthropic/claude-3-opus-20240229"
  max_retries: 1
  
report:
  format: "pdf"
  include_evidence: true
  include_minority_opinions: true
  max_alternatives: 10
```

## 📁 Project Structure

See [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md) for complete directory organization.

```
medley/
├── src/medley/           # Core package
├── docs/                # Documentation (17 files)
├── tests/               # Test suite (11 test modules)
├── examples/            # Example scripts (12 examples)
├── templates/           # Web templates
├── static/              # Web assets
├── cache/               # Response caching
├── reports/             # Generated PDFs
├── usecases/            # Medical cases (13 pre-analyzed)
└── deployment/          # Docker & production files
```

## 🔧 Troubleshooting

### Common Issues

| Issue | Solution |
|-------|----------|
| Empty responses from Gemini | System automatically checks "reasoning" field |
| API rate limits | Built-in retry mechanism with exponential backoff |
| Cache corruption | Run `python clear_cache.py` to reset |
| PDF generation fails | Check ReportLab installation: `pip install reportlab` |
| Model unavailable | System automatically skips and continues |

### Performance Optimization

```bash
# Clear invalid cache entries
find cache -name "*.json" -size -1k -delete

# Run with specific models only
python general_medical_pipeline.py --models "gpt-4o,claude-opus"

# Disable cache for fresh responses
python general_medical_pipeline.py --no-cache
```

## 📈 Metrics & Performance

- **Processing Time**: 45-48 seconds per case
- **Model Success Rate**: 70-100% (varies by availability)
- **Cache Hit Rate**: 90%+ after initial run
- **Memory Usage**: ~500MB peak
- **PDF Generation**: <1 second
- **Parallel Queries**: Up to 10 concurrent

## 🔒 Security & Privacy

- ✅ API keys in environment variables
- ✅ No patient data logging
- ✅ Hash-based cache naming
- ✅ HTTPS API communication
- ✅ No PII in reports
- ✅ Local processing only

## 🧪 Testing

```bash
# Run all tests
pytest tests/

# Unit tests only
pytest tests/unit/

# Integration tests
pytest tests/integration/

# With coverage report
pytest --cov=medley --cov-report=html
```

## 🚧 Development Status & Roadmap

### ✅ Completed Features (Phase 1)
- [x] 31-model ensemble orchestration
- [x] Web application with Material Design 3
- [x] Interactive case gallery (12 cases)
- [x] PDF report generation (6+ pages)
- [x] ICD-10 code mapping
- [x] Bias analysis and attribution
- [x] Model performance tracking
- [x] Health monitoring endpoint
- [x] Animated flow diagram
- [x] Model gallery with origins

### ✅ Completed (Phase 2)
- [x] Custom case analysis interface
- [x] Real-time WebSocket progress updates  
- [x] API key management UI
- [x] Model selection interface
- [x] Session management system

### 📅 Phase 3 Features
#### ✅ Implemented
- [x] SQLite database integration
- [x] Chart.js visualizations  
- [x] Docker containerization
- [x] Mobile-responsive design

#### 🔄 Planned  
- [ ] User authentication system
- [ ] CSV data export
- [ ] Rate limiting & security
- [ ] Shareable report URLs
- [ ] Case comparison tool
- [ ] Batch processing API

## 📚 Documentation

- [API Reference](docs/api.md)
- [Model Metadata](docs/models.md)
- [Bias Analysis](docs/bias_analysis.md)
- [Web Interface Guide](docs/web_guide.md)
- [Changelog](CHANGELOG.md)

## 📄 License

Creative Commons Attribution-ShareAlike 4.0 International (CC BY-SA 4.0) - see [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- OpenRouter for unified LLM access
- All model providers  
- SMAILE team at Karolinska Institutet

## 👥 Contributors

- **Farhad Abtahi** - Author
- **Mehdi Astaraki** - Contributor

## 📮 Contact

- **Author**: Farhad Abtahi
- **Lab**: SMAILE - Stockholm Medical Artificial Intelligence and Learning Environments
- **Institution**: Karolinska Institutet
- **Website**: [smile.ki.se](https://smile.ki.se)

---

**Disclaimer**: This system is for research and educational purposes only. Not intended for clinical diagnosis or treatment decisions.