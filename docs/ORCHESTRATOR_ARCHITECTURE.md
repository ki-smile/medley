# 🎭 MEDLEY Orchestrator Architecture

## Multi-Stage Orchestration System

The MEDLEY orchestrator implements a sophisticated multi-stage analysis pipeline that synthesizes responses from 31 diverse AI models into comprehensive medical insights.

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Architecture Design](#architecture-design)
3. [Prompt Templates](#prompt-templates)
4. [Stage 1: Individual Model Queries](#stage-1-individual-model-queries)
5. [Stage 2: Split Orchestration](#stage-2-split-orchestration)
6. [Stage 3: Final Synthesis](#stage-3-final-synthesis)
7. [Bias Detection System](#bias-detection-system)
8. [Consensus Algorithm](#consensus-algorithm)
9. [Performance Optimizations](#performance-optimizations)

---

## Overview

The orchestrator serves as the brain of MEDLEY, coordinating multiple AI models and synthesizing their outputs into actionable medical insights while preserving diverse perspectives and detecting biases.

### Key Features
- **3-Stage Processing Pipeline**: Parallel queries → Split analysis → Final synthesis
- **Bias-Aware Design**: Actively detects and attributes biases based on model origins
- **Minority Opinion Preservation**: Ensures alternative viewpoints are not lost
- **Efficient Token Management**: Reduced from 130K to 24K characters through optimization

---

## Architecture Design

```
┌──────────────────────────────────────────────────────────┐
│                  ORCHESTRATOR PIPELINE                    │
├──────────────────────────────────────────────────────────┤
│                                                            │
│  Stage 1: Parallel Model Queries (31 Models)              │
│  ┌────────────────────────────────────────────────────┐  │
│  │  Input: Medical Case Description                    │  │
│  │  Output: Individual Diagnostic Responses            │  │
│  │  Models: 7 Free + 24 Paid (Configurable)           │  │
│  │  Timeout: 60s per model                            │  │
│  └────────────────────────────────────────────────────┘  │
│                           ↓                               │
│  Stage 2: Split Orchestration (3 Focused Analyses)        │
│  ┌────────────────────────────────────────────────────┐  │
│  │  A. Diagnostic Analysis                             │  │
│  │     - Primary diagnosis consensus                   │  │
│  │     - Differential diagnoses                        │  │
│  │     - Minority opinions                             │  │
│  │                                                      │  │
│  │  B. Management Strategy Analysis                    │  │
│  │     - Immediate actions                             │  │
│  │     - Diagnostic tests                              │  │
│  │     - Treatment recommendations                     │  │
│  │                                                      │  │
│  │  C. Bias & Evidence Analysis                        │  │
│  │     - Geographic bias patterns                      │  │
│  │     - Cultural considerations                       │  │
│  │     - Model agreement patterns                      │  │
│  └────────────────────────────────────────────────────┘  │
│                           ↓                               │
│  Stage 3: Final Synthesis & Report Generation             │
│  ┌────────────────────────────────────────────────────┐  │
│  │  - Comprehensive PDF report (6 pages)               │  │
│  │  - ICD-10 code mapping                              │  │
│  │  - Clinical pathways                                │  │
│  │  - Decision support matrix                          │  │
│  └────────────────────────────────────────────────────┘  │
│                                                            │
└──────────────────────────────────────────────────────────┘
```

---

## Prompt Templates

### 1. Individual Model Query Prompt

```python
MEDICAL_ANALYSIS_PROMPT = """You are an experienced physician providing a diagnostic assessment.

PATIENT CASE:
{case_description}

Provide a comprehensive medical analysis including:

1. PRIMARY DIAGNOSIS
- Most likely diagnosis based on presented symptoms
- Confidence level (High/Medium/Low)
- Key supporting evidence

2. DIFFERENTIAL DIAGNOSES
- List 3-5 alternative diagnoses
- Brief reasoning for each
- Distinguishing features

3. RECOMMENDED INVESTIGATIONS
- Essential diagnostic tests
- Expected findings
- Priority order

4. MANAGEMENT PLAN
- Immediate interventions
- Medications if applicable
- Follow-up recommendations

5. CRITICAL CONSIDERATIONS
- Red flags to monitor
- Potential complications
- Urgent referrals needed

Format your response as structured JSON."""
```

### 2. Orchestrator Diagnostic Analysis Prompt

```python
ORCHESTRATOR_DIAGNOSTIC_PROMPT = """As the medical synthesis orchestrator, analyze {num_responses} AI model responses for diagnostic consensus.

RESPONSES TO ANALYZE:
{model_responses}

Perform the following analysis:

1. CONSENSUS IDENTIFICATION
   - Identify the primary diagnosis with highest agreement
   - Calculate confidence percentage
   - Note supporting models and their origins

2. DIFFERENTIAL DIAGNOSES
   - List all unique diagnoses mentioned
   - Group by frequency of mention
   - Preserve minority opinions (<10% agreement)

3. DIAGNOSTIC PATTERNS
   - Identify clustering by model origin (US, EU, Asia)
   - Note unusual or outlier diagnoses
   - Flag potential biases

4. EVIDENCE SYNTHESIS
   - Common symptoms identified across models
   - Consistent clinical findings
   - Divergent interpretations

Output format:
{
  "primary_diagnosis": {
    "name": "",
    "icd10_code": "",
    "confidence": 0.0,
    "supporting_models": []
  },
  "differentials": [],
  "minority_opinions": [],
  "bias_indicators": []
}"""
```

### 3. Orchestrator Management Strategy Prompt

```python
ORCHESTRATOR_MANAGEMENT_PROMPT = """Synthesize management recommendations from {num_responses} AI models.

RESPONSES TO ANALYZE:
{model_responses}

Create a unified management strategy covering:

1. IMMEDIATE ACTIONS
   - Life-saving interventions
   - Symptom management
   - Safety precautions

2. DIAGNOSTIC WORKUP
   - Essential tests (>50% agreement)
   - Additional tests (25-50% agreement)
   - Specialized tests (<25% agreement)

3. TREATMENT PLAN
   - First-line therapies
   - Alternative approaches
   - Contraindications

4. FOLLOW-UP STRATEGY
   - Monitoring parameters
   - Reassessment timeline
   - Referral recommendations

Consider geographic variations in treatment approaches.
Highlight any conflicting recommendations with reasoning."""
```

### 4. Orchestrator Bias Analysis Prompt

```python
ORCHESTRATOR_BIAS_PROMPT = """Analyze potential biases in {num_responses} model responses.

MODEL ORIGINS:
{model_metadata}

RESPONSES:
{model_responses}

Identify and analyze:

1. GEOGRAPHIC BIAS PATTERNS
   - Diagnosis preferences by region
   - Treatment approach variations
   - Resource availability assumptions

2. CULTURAL CONSIDERATIONS
   - Population-specific risks mentioned
   - Cultural sensitivity in recommendations
   - Language or terminology differences

3. SYSTEMIC BIASES
   - Age-related assumptions
   - Gender-based considerations
   - Socioeconomic factors

4. MODEL AGREEMENT PATTERNS
   - Clusters by company/origin
   - Outlier responses
   - Confidence correlations

Output structured bias analysis with specific examples."""
```

---

## Stage 1: Individual Model Queries

### Implementation Details

```python
class ModelQueryManager:
    def __init__(self):
        self.max_parallel = 10
        self.timeout = 60
        self.retry_attempts = 2
        
    async def query_all_models(self, case_description, selected_models):
        """
        Query multiple models in parallel batches
        """
        tasks = []
        for batch in self.batch_models(selected_models, self.max_parallel):
            batch_tasks = [
                self.query_single_model(model, case_description)
                for model in batch
            ]
            results = await asyncio.gather(*batch_tasks, return_exceptions=True)
            tasks.extend(results)
        return tasks
```

### Model Selection Strategy

- **Free Tier (7 models)**: Quick analysis, limited perspectives
- **Standard Tier (15 models)**: Balanced coverage, moderate cost
- **Comprehensive (31 models)**: Full diversity, maximum insights

---

## Stage 2: Split Orchestration

### Why Split Architecture?

The original monolithic orchestrator prompt was 130K characters, causing:
- Token limit errors
- Slow processing
- Loss of context
- Reduced quality

### Solution: Three Focused Queries

Each query is optimized for specific analysis:

1. **Diagnostic Focus** (8K chars)
   - Primary: Claude 3.5 Sonnet
   - Fallback: GPT-4o

2. **Management Focus** (8K chars)
   - Primary: Claude 3.5 Sonnet
   - Fallback: Gemini 2.0 Pro

3. **Bias Analysis** (8K chars)
   - Primary: Claude 3.5 Sonnet
   - Fallback: GPT OSS 20B (free)

### Benefits
- 81% reduction in token usage
- 3x faster processing
- Better context retention
- Parallel execution capability

---

## Stage 3: Final Synthesis

### Report Generation Pipeline

```python
class ReportSynthesizer:
    def synthesize(self, diagnostic_results, management_results, bias_results):
        """
        Combine all analyses into final report
        """
        return {
            "executive_summary": self.create_summary(diagnostic_results),
            "diagnostic_landscape": self.merge_diagnoses(diagnostic_results),
            "management_strategies": self.consolidate_management(management_results),
            "bias_analysis": self.format_bias_analysis(bias_results),
            "clinical_pathways": self.generate_pathways(all_results),
            "decision_matrix": self.create_decision_support(all_results)
        }
```

---

## Bias Detection System

### Geographic Bias Mapping

```python
GEOGRAPHIC_BIASES = {
    "US": ["Western medicine focus", "High-tech diagnostic preference", "Litigation awareness"],
    "China": ["TCM integration", "Holistic approach", "Herbal considerations"],
    "France": ["European guidelines", "Conservative medication approach", "Public health focus"],
    "Japan": ["Preventive emphasis", "Minimal intervention preference", "Elderly care focus"],
    "Israel": ["Innovation adoption", "Military medicine influence", "Genetic screening emphasis"],
    "Canada": ["Universal healthcare assumptions", "Resource optimization", "Rural access considerations"]
}
```

### Bias Attribution Algorithm

1. **Pattern Detection**: Identify diagnosis clusters by origin
2. **Statistical Analysis**: Chi-square test for significance
3. **Attribution**: Map patterns to known biases
4. **Reporting**: Present biases transparently with context

---

## Consensus Algorithm

### Weighted Voting System

```python
def calculate_consensus(responses):
    """
    Advanced consensus calculation with minority preservation
    """
    diagnosis_votes = defaultdict(list)
    
    for response in responses:
        diagnosis = response['primary_diagnosis']
        confidence = response['confidence']
        model_origin = response['model_metadata']['origin']
        
        diagnosis_votes[diagnosis].append({
            'model': response['model_id'],
            'confidence': confidence,
            'origin': model_origin
        })
    
    # Calculate weighted consensus
    consensus_scores = {}
    for diagnosis, votes in diagnosis_votes.items():
        # Base score: number of votes
        base_score = len(votes)
        
        # Confidence weighting
        confidence_weight = sum(v['confidence'] for v in votes) / len(votes)
        
        # Diversity bonus (different origins agreeing)
        unique_origins = len(set(v['origin'] for v in votes))
        diversity_bonus = 1 + (unique_origins * 0.1)
        
        consensus_scores[diagnosis] = base_score * confidence_weight * diversity_bonus
    
    return consensus_scores
```

### Minority Opinion Preservation

Opinions with <10% agreement are:
1. Explicitly preserved in reports
2. Analyzed for unique insights
3. Flagged if from reputable models
4. Included in differential diagnoses

---

## Performance Optimizations

### 1. Caching Strategy

```python
CACHE_STRATEGY = {
    "model_responses": {
        "ttl": 86400,  # 24 hours
        "key": "hash(case_content + model_id)"
    },
    "orchestrator_analysis": {
        "ttl": 3600,   # 1 hour
        "key": "hash(response_ids + analysis_type)"
    },
    "reports": {
        "ttl": 604800, # 7 days
        "key": "case_id + timestamp"
    }
}
```

### 2. Parallel Processing

- Stage 1: 10 concurrent model queries
- Stage 2: 3 parallel orchestrator analyses
- Stage 3: Async report generation

### 3. Token Optimization

| Component | Before | After | Reduction |
|-----------|--------|-------|-----------|
| Model Prompt | 2,500 | 800 | 68% |
| Orchestrator | 130,000 | 24,000 | 81% |
| Total/Case | 180,000 | 50,000 | 72% |

### 4. Fallback Mechanisms

```python
FALLBACK_CHAIN = {
    "primary": "anthropic/claude-3-5-sonnet-20241022",
    "secondary": "openai/gpt-4o",
    "tertiary": "google/gemini-2.0-flash-exp:free",
    "emergency": "neversleep/llama-3.1-lumimaid-70b"  # Free tier
}
```

---

## Error Handling

### Graceful Degradation

1. **Model Failure**: Skip and continue with remaining models
2. **Orchestrator Failure**: Use fallback model chain
3. **Timeout**: Return partial results with warning
4. **Token Limit**: Automatically reduce context and retry

### Monitoring

```python
MONITORING_METRICS = {
    "model_success_rate": "Track per model reliability",
    "orchestrator_latency": "Measure synthesis time",
    "cache_hit_rate": "Optimize for common cases",
    "bias_detection_accuracy": "Validate against known cases"
}
```

---

## Future Enhancements

1. **Adaptive Orchestration**: Learn from physician feedback
2. **Dynamic Model Selection**: Choose models based on case type
3. **Real-time Streaming**: Progressive report generation
4. **Federated Learning**: Improve without sharing patient data

---

## Configuration

### Environment Variables

```bash
# Orchestrator Configuration
ORCHESTRATOR_MODEL=anthropic/claude-3-5-sonnet-20241022
ORCHESTRATOR_FALLBACK=openai/gpt-4o
ORCHESTRATOR_TIMEOUT=120
ORCHESTRATOR_MAX_RETRIES=2

# Split Query Configuration
ENABLE_SPLIT_ORCHESTRATION=true
DIAGNOSTIC_QUERY_MODEL=anthropic/claude-3-5-sonnet-20241022
MANAGEMENT_QUERY_MODEL=anthropic/claude-3-5-sonnet-20241022
BIAS_QUERY_MODEL=anthropic/claude-3-5-sonnet-20241022

# Performance Tuning
MAX_PARALLEL_MODELS=10
MODEL_QUERY_TIMEOUT=60
CACHE_ENABLED=true
```

---

## Conclusion

The MEDLEY orchestrator represents a sophisticated approach to medical AI synthesis, balancing efficiency with comprehensive analysis while maintaining transparency about biases and preserving diverse perspectives. The multi-stage architecture ensures scalability while the split orchestration design overcomes token limitations of modern LLMs.

---

**Author**: Farhad Abtahi  
**Institution**: SMAILE at Karolinska Institutet  
**Last Updated**: August 2025