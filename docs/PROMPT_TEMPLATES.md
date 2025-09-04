# 📝 MEDLEY Prompt Templates Documentation

## Complete Collection of Prompts Used in the MEDLEY System

This document contains all prompt templates used throughout the MEDLEY medical AI ensemble system, organized by component and purpose.

---

## Table of Contents

1. [Individual Model Prompts](#individual-model-prompts)
2. [Orchestrator Prompts](#orchestrator-prompts)
3. [Synthesis Prompts](#synthesis-prompts)
4. [Bias Analysis Prompts](#bias-analysis-prompts)
5. [Report Generation Prompts](#report-generation-prompts)
6. [Evidence Synthesis Prompts](#evidence-synthesis-prompts)

---

## Individual Model Prompts

### Standard Medical Analysis Prompt

**Used in**: `general_medical_pipeline.py`, `web_orchestrator.py`  
**Purpose**: Query individual AI models for medical diagnosis

```python
STANDARD_MEDICAL_PROMPT = """You are an experienced physician. Analyze the following medical case and provide a comprehensive diagnostic assessment.

PATIENT CASE:
{case_description}

Please provide:

1. PRIMARY DIAGNOSIS
   - Your most likely diagnosis
   - Key clinical reasoning
   - Confidence level (High/Medium/Low)

2. DIFFERENTIAL DIAGNOSES
   - List 3-5 alternative diagnoses
   - Brief reasoning for each
   - How to distinguish between them

3. RECOMMENDED INVESTIGATIONS
   - Essential diagnostic tests
   - Expected findings for each test
   - Priority order

4. MANAGEMENT PLAN
   - Immediate interventions required
   - Medications with dosing if applicable
   - Monitoring parameters
   - Follow-up recommendations

5. CRITICAL CONSIDERATIONS
   - Red flags to watch for
   - Potential complications
   - When to seek urgent/emergent care

Format your response clearly with these sections."""
```

### Structured JSON Response Prompt

**Used in**: `llm_manager.py` when JSON mode is enabled  
**Purpose**: Ensure structured output from models

```python
JSON_MEDICAL_PROMPT = """Analyze this medical case and respond in valid JSON format.

CASE:
{case_description}

Return a JSON object with this exact structure:
{
  "primary_diagnosis": {
    "name": "string",
    "icd10_code": "string",
    "confidence": "High|Medium|Low",
    "reasoning": "string"
  },
  "differential_diagnoses": [
    {
      "name": "string",
      "likelihood": "number 0-1",
      "reasoning": "string"
    }
  ],
  "investigations": [
    {
      "test": "string",
      "priority": "Urgent|Routine|Optional",
      "expected_findings": "string"
    }
  ],
  "management": {
    "immediate_actions": ["string"],
    "medications": [
      {
        "name": "string",
        "dose": "string",
        "route": "string",
        "frequency": "string"
      }
    ],
    "follow_up": "string"
  },
  "red_flags": ["string"]
}"""
```

---

## Orchestrator Prompts

### Main Orchestrator Synthesis Prompt

**Used in**: `orchestrator_prompts.py`  
**Purpose**: Primary synthesis of all model responses

```python
ORCHESTRATOR_SYNTHESIS_PROMPT = """You are the Chief Medical Orchestrator synthesizing diagnostic assessments from {num_models} diverse AI models representing different medical traditions and geographic regions.

CASE DESCRIPTION:
{case_description}

MODEL RESPONSES:
{formatted_responses}

Your task is to create a comprehensive synthesis that:

1. IDENTIFIES CONSENSUS
   - Determine the primary diagnosis with highest agreement
   - Calculate confidence based on model agreement
   - Note which models support this diagnosis

2. PRESERVES DIVERSITY
   - Maintain ALL differential diagnoses mentioned
   - Explicitly preserve minority opinions (<10% agreement)
   - Highlight unique perspectives from different regions

3. ANALYZES PATTERNS
   - Identify clustering of diagnoses by model origin
   - Detect potential biases (geographic, cultural, systemic)
   - Note unusual or innovative approaches

4. PROVIDES CLINICAL GUIDANCE
   - Synthesize management recommendations
   - Prioritize investigations by consensus
   - Create unified treatment approach

5. ENSURES SAFETY
   - Highlight all red flags mentioned
   - Note any contradictions in recommendations
   - Emphasize critical time-sensitive actions

Remember: Your role is synthesis and analysis, not suppression of diverse viewpoints."""
```

### Split Orchestrator - Diagnostic Focus

**Used in**: `orchestrator_split_queries.py`  
**Purpose**: Focused diagnostic consensus building

```python
DIAGNOSTIC_ORCHESTRATOR_PROMPT = """Analyze {num_responses} AI model diagnostic assessments to determine consensus.

MODEL RESPONSES (with origins):
{responses_with_metadata}

Tasks:
1. PRIMARY DIAGNOSIS CONSENSUS
   - Identify most agreed upon diagnosis
   - List supporting models with their origins
   - Calculate agreement percentage
   - Note confidence levels

2. DIFFERENTIAL DIAGNOSES COMPILATION
   - List ALL unique diagnoses mentioned
   - Group by frequency (High >50%, Medium 20-50%, Low <20%)
   - Preserve single-mention diagnoses as "minority opinions"

3. DIAGNOSTIC REASONING PATTERNS
   - Common clinical features identified
   - Divergent interpretations of same symptoms
   - Geographic/cultural diagnosis preferences

4. ICD-10 MAPPING
   - Provide codes for primary diagnosis
   - Include codes for top 5 differentials

Output structured analysis with clear percentages and model attributions."""
```

### Split Orchestrator - Management Focus

**Used in**: `orchestrator_split_queries.py`  
**Purpose**: Synthesize treatment and management strategies

```python
MANAGEMENT_ORCHESTRATOR_PROMPT = """Synthesize management recommendations from {num_responses} medical AI models.

CASE CONTEXT:
{brief_case_summary}

MANAGEMENT RECOMMENDATIONS:
{management_responses}

Create unified strategy covering:

1. IMMEDIATE INTERVENTIONS
   - Life-threatening priorities (100% agreement required)
   - Urgent actions (>75% agreement)
   - Important steps (50-75% agreement)
   - Consider but verify (<50% agreement)

2. DIAGNOSTIC WORKUP
   - Tier 1: Essential tests (>75% agreement)
   - Tier 2: Recommended tests (50-75%)
   - Tier 3: Consider if indicated (<50%)
   - Note regional test preferences

3. TREATMENT SYNTHESIS
   - First-line therapy consensus
   - Alternative approaches by region
   - Contraindications mentioned
   - Drug interactions flagged

4. FOLLOW-UP PLANNING
   - Monitoring schedule
   - Warning signs for patients
   - Referral recommendations
   - Outcome expectations

Flag any conflicting recommendations with explanation."""
```

### Split Orchestrator - Bias Analysis

**Used in**: `orchestrator_split_queries.py`  
**Purpose**: Detect and analyze biases in model responses

```python
BIAS_ORCHESTRATOR_PROMPT = """Perform bias analysis on {num_responses} AI model responses.

MODEL METADATA:
{model_origins_and_companies}

RESPONSES FOR BIAS ANALYSIS:
{responses}

Analyze and report:

1. GEOGRAPHIC BIAS PATTERNS
   Origin | Diagnosis Preference | Treatment Approach | Notable Assumptions
   -------|---------------------|-------------------|--------------------
   USA    | [List tendencies]   | [List approaches] | [List assumptions]
   China  | [List tendencies]   | [List approaches] | [List assumptions]
   EU     | [List tendencies]   | [List approaches] | [List assumptions]
   
2. SYSTEMIC BIASES DETECTED
   - Healthcare system assumptions (private vs public)
   - Resource availability assumptions
   - Technology access assumptions
   - Medication availability assumptions

3. DEMOGRAPHIC BIAS INDICATORS
   - Age-related assumptions
   - Gender-based considerations
   - Socioeconomic assumptions
   - Cultural sensitivity issues

4. BIAS IMPACT ASSESSMENT
   - How biases might affect diagnosis
   - How biases might affect treatment
   - Recommendations to mitigate biases

Provide specific examples from responses to support each bias identified."""
```

---

## Synthesis Prompts

### Evidence Synthesis Prompt

**Used in**: `evidence_synthesis_generator.py`  
**Purpose**: Create evidence-based summary from literature

```python
EVIDENCE_SYNTHESIS_PROMPT = """Synthesize medical evidence for the diagnostic findings.

PRIMARY DIAGNOSIS: {primary_diagnosis}
DIFFERENTIAL DIAGNOSES: {differentials}

Provide evidence-based analysis:

1. EPIDEMIOLOGY
   - Prevalence/incidence data
   - Risk factors
   - Demographic patterns
   - Geographic distribution

2. CLINICAL CORRELATIONS
   - Pathophysiology explanation
   - Classic presentation
   - Atypical presentations
   - Natural history

3. DIAGNOSTIC ACCURACY
   - Test sensitivity/specificity
   - Likelihood ratios
   - Pre/post-test probabilities
   - Gold standard tests

4. TREATMENT EVIDENCE
   - First-line therapy efficacy (NNT if available)
   - Alternative treatments
   - Comparative effectiveness
   - Recent guidelines

5. PROGNOSIS
   - Expected outcomes
   - Prognostic factors
   - Complications
   - Quality of life impact

Include confidence levels for evidence quality (High/Moderate/Low/Very Low)."""
```

### Management Strategy Synthesis

**Used in**: `management_strategies_synthesizer.py`  
**Purpose**: Create comprehensive management plan

```python
MANAGEMENT_SYNTHESIS_PROMPT = """Create a comprehensive management strategy based on consensus recommendations.

DIAGNOSIS: {diagnosis}
CONSENSUS RECOMMENDATIONS: {recommendations}
PATIENT FACTORS: {patient_context}

Develop structured plan:

1. IMMEDIATE PRIORITIES (0-24 hours)
   □ Stabilization needs
   □ Symptom control
   □ Safety monitoring
   □ Initial workup

2. SHORT-TERM PLAN (1-7 days)
   □ Diagnostic completion
   □ Treatment initiation
   □ Response monitoring
   □ Complication prevention

3. MEDIUM-TERM PLAN (1-4 weeks)
   □ Treatment optimization
   □ Follow-up schedule
   □ Outcome assessment
   □ Adjustment criteria

4. LONG-TERM CONSIDERATIONS
   □ Maintenance therapy
   □ Surveillance needs
   □ Lifestyle modifications
   □ Prognosis discussion

5. CONTINGENCY PLANNING
   - If treatment fails: [next steps]
   - If diagnosis changes: [reassessment plan]
   - If complications occur: [management]

Include specific metrics for treatment success/failure."""
```

---

## Bias Analysis Prompts

### Comprehensive Bias Analysis

**Used in**: `bias_analyzer.py`  
**Purpose**: Deep analysis of biases across all responses

```python
COMPREHENSIVE_BIAS_PROMPT = """Conduct comprehensive bias analysis of medical AI responses.

CASE TYPE: {case_description}
MODEL RESPONSES: {all_responses}
MODEL METADATA: {model_info}

Perform multi-dimensional bias analysis:

1. GEOGRAPHIC BIAS MATRIX
   Create table showing:
   - Diagnosis preferences by country/region
   - Treatment philosophy differences
   - Healthcare system assumptions
   - Resource availability assumptions

2. CULTURAL COMPETENCY ASSESSMENT
   - Cultural factors considered/missed
   - Language/terminology variations
   - Traditional medicine integration
   - Religious/dietary considerations

3. DEMOGRAPHIC BIAS SCAN
   - Age-appropriate considerations
   - Gender-specific factors
   - Socioeconomic sensitivity
   - Disability accommodations

4. TRAINING DATA ARTIFACTS
   - Likely training data biases
   - Overrepresented populations
   - Underrepresented conditions
   - Knowledge cutoff impacts

5. CLINICAL IMPACT ANALYSIS
   - How biases affect accuracy
   - Patient safety implications
   - Equity considerations
   - Mitigation strategies

Rate overall bias impact: Minimal|Moderate|Significant|Severe"""
```

### Minority Opinion Analysis

**Used in**: `minority_opinion_analyzer.py`  
**Purpose**: Analyze and validate minority diagnostic opinions

```python
MINORITY_OPINION_PROMPT = """Analyze minority diagnostic opinions for potential value.

MINORITY DIAGNOSES (<10% agreement):
{minority_diagnoses}

CONTEXT:
- Primary consensus: {primary_diagnosis}
- Case details: {case_summary}

For each minority opinion, assess:

1. DIAGNOSTIC MERIT
   - Clinical plausibility
   - Supporting evidence
   - Why others might have missed it
   - Conditions for consideration

2. MODEL ATTRIBUTION
   - Which model(s) suggested it
   - Model's expertise area
   - Track record reliability
   - Potential unique training

3. CLINICAL SIGNIFICANCE
   - Consequences if correct
   - Risk of missing diagnosis
   - Cost/benefit of pursuing
   - Red flags that would confirm

4. RECOMMENDATION
   - Include in differential? (Yes/No/Conditional)
   - Investigation priority (High/Medium/Low/None)
   - Specific triggers to reconsider
   - Documentation importance

Provide final assessment: which minority opinions deserve clinical consideration?"""
```

---

## Report Generation Prompts

### Executive Summary Generation

**Used in**: `report_generators.py`  
**Purpose**: Create concise executive summary for reports

```python
EXECUTIVE_SUMMARY_PROMPT = """Create an executive summary for this medical case analysis.

CASE: {case_title}
PRIMARY DIAGNOSIS: {primary_diagnosis} ({confidence}% agreement)
KEY FINDINGS: {key_findings}
CRITICAL ACTIONS: {critical_actions}

Write a 200-word executive summary that:
1. States the primary diagnosis with confidence
2. Lists 2-3 most important differential diagnoses
3. Highlights immediate actions required
4. Notes any critical time-sensitive elements
5. Mentions significant bias considerations
6. Provides clear next steps

Use clear, professional medical language accessible to healthcare providers."""
```

### Clinical Pathway Generation

**Used in**: `pathway_generator.py`  
**Purpose**: Create visual clinical decision pathways

```python
PATHWAY_GENERATION_PROMPT = """Generate a clinical decision pathway for this case.

DIAGNOSIS: {diagnosis}
MANAGEMENT PLAN: {management_plan}
DECISION POINTS: {key_decisions}

Create a structured pathway:

START → Initial Assessment
         ├─ If stable → Proceed with workup
         │   ├─ Test A positive → Treatment X
         │   └─ Test A negative → Test B
         └─ If unstable → Stabilization
             ├─ Response → Continue protocol
             └─ No response → Escalate care

Include:
- Clear decision nodes
- Specific criteria for each branch
- Timeframes for decisions
- Outcome endpoints
- Reassessment loops

Format as structured text suitable for conversion to flowchart."""
```

### ICD-10 Mapping Prompt

**Used in**: `icd_mapper.py`  
**Purpose**: Map diagnoses to ICD-10 codes

```python
ICD10_MAPPING_PROMPT = """Map the following diagnoses to ICD-10-CM codes.

DIAGNOSES TO MAP:
1. Primary: {primary_diagnosis}
2. Differentials: {differential_list}
3. Complications: {complications}
4. Comorbidities: {comorbidities}

For each diagnosis provide:
- ICD-10-CM code (most specific available)
- Code description
- Any relevant subcodes
- Coding notes (if applicable)

Example format:
- Diagnosis: Acute appendicitis with perforation
- Code: K35.32
- Description: Acute appendicitis with perforation and localized peritonitis
- Note: Use additional code for any associated peritoneal abscess (K65.1)

Ensure codes are current and specific to the clinical presentation described."""
```

---

## Evidence Synthesis Prompts

### Literature Review Synthesis

**Used in**: `evidence_synthesizer.py`  
**Purpose**: Synthesize current medical literature

```python
LITERATURE_SYNTHESIS_PROMPT = """Synthesize current medical literature for this diagnosis.

DIAGNOSIS: {diagnosis}
CLINICAL CONTEXT: {context}
SPECIFIC QUESTIONS: {questions}

Provide evidence synthesis including:

1. DIAGNOSTIC CRITERIA
   - Current diagnostic standards
   - Recent guideline updates
   - Controversial areas
   - Emerging biomarkers

2. TREATMENT LANDSCAPE
   - Standard of care
   - Recent RCT evidence
   - Guidelines comparison (US/EU/WHO)
   - Pipeline therapies

3. OUTCOME DATA
   - Survival statistics
   - Quality of life metrics
   - Prognostic models
   - Risk stratification

4. KNOWLEDGE GAPS
   - Areas needing research
   - Conflicting evidence
   - Population-specific gaps
   - Implementation barriers

Indicate evidence quality using GRADE criteria."""
```

### Cost-Effectiveness Analysis Prompt

**Used in**: `cost_analysis.py`  
**Purpose**: Analyze cost-effectiveness of interventions

```python
COST_EFFECTIVENESS_PROMPT = """Analyze cost-effectiveness of proposed interventions.

DIAGNOSIS: {diagnosis}
PROPOSED INTERVENTIONS: {interventions}
HEALTHCARE SETTING: {setting}

Provide analysis:

1. DIRECT COSTS
   - Diagnostic tests
   - Treatments
   - Hospitalizations
   - Follow-up care

2. INDIRECT COSTS
   - Work loss
   - Caregiver burden
   - Transportation
   - Long-term disability

3. COST-EFFECTIVENESS
   - Cost per QALY
   - NNT with costs
   - Budget impact
   - Comparison to alternatives

4. VALUE ASSESSMENT
   - High-value interventions
   - Low-value interventions
   - Cost-saving opportunities
   - Resource optimization

Consider different healthcare systems (US private, public systems, LMIC settings)."""
```

---

## Configuration and Customization

### Prompt Configuration File

Location: `config/prompts.yaml`

```yaml
prompts:
  medical_analysis:
    version: "2.0"
    max_tokens: 2000
    temperature: 0.7
    system_message: "You are an experienced physician..."
    
  orchestrator:
    version: "3.0"
    max_tokens: 4000
    temperature: 0.5
    system_message: "You are the chief medical orchestrator..."
    
  bias_analysis:
    version: "1.5"
    max_tokens: 3000
    temperature: 0.6
    system_message: "You are a bias detection specialist..."

prompt_chains:
  comprehensive_analysis:
    - medical_analysis
    - orchestrator
    - bias_analysis
    - evidence_synthesis
    
  quick_assessment:
    - medical_analysis
    - orchestrator

prompt_parameters:
  json_mode: false
  strip_whitespace: true
  validate_output: true
```

---

## Best Practices

### 1. Prompt Engineering Guidelines

- **Clarity**: Use clear, specific instructions
- **Structure**: Organize with numbered sections
- **Examples**: Provide format examples when needed
- **Constraints**: Specify length/format constraints
- **Safety**: Include safety considerations

### 2. Version Control

All prompts are versioned and tracked:
```python
PROMPT_VERSIONS = {
    "medical_analysis": "2.0",
    "orchestrator": "3.0",
    "bias_analysis": "1.5"
}
```

### 3. Testing Prompts

```bash
# Test individual prompt
python test_prompts.py --prompt medical_analysis --model gpt-4o

# Test prompt chain
python test_prompts.py --chain comprehensive_analysis

# Validate all prompts
python validate_prompts.py
```

### 4. Monitoring Prompt Performance

Key metrics tracked:
- Response quality scores
- Token usage efficiency
- Error rates by prompt
- Model-specific performance

---

## Conclusion

These prompts form the core of MEDLEY's ability to synthesize diverse medical AI perspectives into actionable clinical insights. Regular updates ensure alignment with medical best practices and optimal model performance.

---

**Last Updated**: August 2025  
**Maintained by**: SMAILE Team at Karolinska Institutet  
**Contact**: farhad.abtahi@ki.se