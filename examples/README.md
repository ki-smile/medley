# 🔬 MEDLEY Examples

This directory contains example scripts and utilities for working with the MEDLEY system.

## 📁 Contents

### Case Generation Scripts

| Script | Description | Usage |
|--------|-------------|-------|
| `generate_case_13.py` | Generate Case 13 analysis | `python generate_case_13.py` |
| `finalize_case_13.py` | Finalize Case 13 report | `python finalize_case_13.py` |
| `regenerate_case_13_fixed.py` | Regenerate Case 13 with fixes | `python regenerate_case_13_fixed.py` |

### Batch Processing

| Script | Description | Usage |
|--------|-------------|-------|
| `run_remaining_cases.sh` | Run analysis on multiple cases | `./run_remaining_cases.sh` |

## 🚀 Quick Start

### Running a Single Case Analysis

```python
# Example: Generate a new case analysis
from general_medical_pipeline import GeneralMedicalPipeline

# Initialize pipeline
pipeline = GeneralMedicalPipeline("Case_14")

# Load case description
with open("usecases/case_014_neurology.txt", "r") as f:
    case_text = f.read()

# Run analysis
results = pipeline.run_complete_analysis(
    case_description=case_text,
    case_title="Complex Neurology Case"
)

print(f"Report generated: {results['report_file']}")
```

### Batch Processing Multiple Cases

```bash
# Process cases 14-20
for i in {14..20}; do
    python general_medical_pipeline.py "Case_$i" "usecases/case_$(printf %03d $i)_*.txt"
done
```

### Using Free Models Only

```bash
# Set environment variable for free models
export USE_FREE_MODELS=true
python general_medical_pipeline.py "Case_15" "usecases/case_015_cardiology.txt"
```

## 📝 Creating Custom Scripts

### Template for New Case Generation

```python
#!/usr/bin/env python
"""
Template for generating new medical case analysis
"""

import os
import sys
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from general_medical_pipeline import GeneralMedicalPipeline

def generate_case(case_number, case_file):
    """Generate analysis for a new case"""
    
    # Set case ID
    case_id = f"Case_{case_number}"
    
    # Initialize pipeline
    pipeline = GeneralMedicalPipeline(case_id)
    
    # Load case
    with open(case_file, 'r') as f:
        case_text = f.read()
    
    # Run analysis
    print(f"Starting analysis for {case_id}...")
    results = pipeline.run_complete_analysis(
        case_description=case_text,
        case_title=case_id
    )
    
    print(f"✅ Analysis complete!")
    print(f"📄 PDF Report: {results['report_file']}")
    print(f"📊 Data File: {results['data_file']}")
    
    return results

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python generate_case.py <case_number> <case_file>")
        sys.exit(1)
    
    case_number = sys.argv[1]
    case_file = sys.argv[2]
    
    generate_case(case_number, case_file)
```

## 🔧 Advanced Examples

### Custom Model Selection

```python
# Select specific models for analysis
from model_metadata_2025 import get_comprehensive_model_metadata

metadata = get_comprehensive_model_metadata()

# Get only US-based models
us_models = [
    model_id for model_id, info in metadata.items() 
    if info.get('country') == 'USA'
]

# Use in pipeline
pipeline.selected_models = us_models[:5]  # Use first 5 US models
```

### Bias-Focused Analysis

```python
# Configure pipeline for bias detection
pipeline_config = {
    "enable_bias_analysis": True,
    "bias_detection_threshold": 0.3,
    "preserve_minority_opinions": True,
    "minimum_models_for_consensus": 5
}

pipeline = GeneralMedicalPipeline("Case_Bias_Test", config=pipeline_config)
```

### Report Customization

```python
# Customize report generation
from comprehensive_report_generator import ComprehensiveReportGenerator

generator = ComprehensiveReportGenerator()
generator.config.update({
    "include_minority_opinions": True,
    "max_differentials": 15,
    "include_evidence_synthesis": True,
    "generate_clinical_pathways": True
})

# Generate custom report
report_path = generator.generate_pdf_report(
    results_data,
    "Custom_Report.pdf"
)
```

## 📊 Performance Testing

### Benchmark Script

```python
# benchmark.py - Test system performance
import time
from statistics import mean, stdev

def benchmark_analysis(case_file, iterations=3):
    """Benchmark analysis performance"""
    times = []
    
    for i in range(iterations):
        start = time.time()
        
        # Run analysis
        pipeline = GeneralMedicalPipeline(f"Benchmark_{i}")
        results = pipeline.run_complete_analysis(case_text)
        
        elapsed = time.time() - start
        times.append(elapsed)
        print(f"Iteration {i+1}: {elapsed:.2f}s")
    
    print(f"\nAverage: {mean(times):.2f}s ± {stdev(times):.2f}s")
    return times
```

## 🐛 Debugging Examples

### Enable Debug Logging

```python
import logging

# Configure detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('debug.log'),
        logging.StreamHandler()
    ]
)

# Run with debug mode
pipeline = GeneralMedicalPipeline("Debug_Case")
pipeline.debug_mode = True
```

### Error Recovery

```python
# Retry failed model queries
max_retries = 3
for attempt in range(max_retries):
    try:
        results = pipeline.run_complete_analysis(case_text)
        break
    except Exception as e:
        print(f"Attempt {attempt + 1} failed: {e}")
        if attempt == max_retries - 1:
            print("All attempts failed, using cached data")
            results = pipeline.load_cached_results()
```

## 📚 Additional Resources

- [Main README](../README.md) - Project overview
- [Documentation](../docs/README.md) - Complete documentation
- [HOW_TO_ADD_NEW_CASES](../docs/HOW_TO_ADD_NEW_CASES.md) - Case creation guide
- [ORCHESTRATOR_ARCHITECTURE](../docs/ORCHESTRATOR_ARCHITECTURE.md) - System design

## 🤝 Contributing Examples

To add new examples:
1. Create descriptive script names
2. Include docstrings and comments
3. Handle errors gracefully
4. Update this README
5. Test thoroughly before committing

---

**Note**: These examples are for demonstration purposes. Always review and adapt for your specific use case.