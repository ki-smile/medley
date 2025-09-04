# Medley API Documentation

## Core Modules

### `medley.models.llm_manager`

#### Class: `LLMManager`

Manages interactions with Large Language Models through OpenRouter API.

##### Methods

###### `__init__(config: Config)`
Initialize the LLM manager with configuration.

**Parameters:**
- `config`: Configuration object containing API keys and settings

**Raises:**
- `ValueError`: If OpenRouter API key is not configured

---

###### `query_model(model_config: ModelConfig, prompt: str, system_prompt: Optional[str] = None) -> LLMResponse`
Query a single model synchronously.

**Parameters:**
- `model_config`: Model configuration object
- `prompt`: User prompt to send to the model
- `system_prompt`: Optional system prompt for context

**Returns:**
- `LLMResponse`: Response object containing model output

**Example:**
```python
response = llm_manager.query_model(
    model_config=config.get_model("gemini-2.5-pro"),
    prompt="Analyze this medical case: ...",
    system_prompt="You are a medical expert."
)
```

---

###### `async query_models_parallel(model_configs: List[ModelConfig], prompt: str, system_prompt: Optional[str] = None) -> List[LLMResponse]`
Query multiple models in parallel.

**Parameters:**
- `model_configs`: List of model configurations
- `prompt`: User prompt to send to all models
- `system_prompt`: Optional system prompt

**Returns:**
- `List[LLMResponse]`: List of responses from all models

---

#### Class: `LLMResponse`

Data class representing a response from an LLM.

**Attributes:**
- `model_name` (str): Display name of the model
- `model_id` (str): Model identifier
- `content` (str): Response content
- `timestamp` (str): ISO format timestamp
- `latency` (float): Response time in seconds
- `tokens_used` (int): Number of tokens consumed
- `error` (Optional[str]): Error message if failed
- `raw_response` (Optional[Dict]): Raw API response

---

### `medley.processors.case_processor`

#### Class: `CaseProcessor`

Processes medical case files for analysis.

##### Methods

###### `load_case_from_file(file_path: Path) -> MedicalCase`
Load a medical case from a text or JSON file.

**Parameters:**
- `file_path`: Path to the case file

**Returns:**
- `MedicalCase`: Parsed medical case object

**Note:** Automatically filters out bias testing targets and metadata.

---

###### `load_all_cases() -> List[MedicalCase]`
Load all cases from the cases directory.

**Returns:**
- `List[MedicalCase]`: List of all medical cases

---

#### Class: `MedicalCase`

Structured representation of a medical case.

**Attributes:**
- `case_id` (str): Unique case identifier
- `title` (str): Case title
- `patient_info` (str): Patient demographics and info
- `presentation` (str): Clinical presentation
- `symptoms` (List[str]): List of symptoms
- `history` (Optional[str]): Medical history
- `labs` (Optional[str]): Laboratory results
- `imaging` (Optional[str]): Imaging findings
- `physical_exam` (Optional[str]): Physical examination
- `metadata` (Dict): Additional metadata
- `bias_testing_target` (Optional[str]): **Internal only** - not sent to LLMs

##### Methods

###### `to_prompt() -> str`
Convert case to formatted prompt string (excludes bias information).

###### `to_dict() -> Dict`
Convert to dictionary representation (excludes bias_testing_target).

---

### `medley.processors.response_parser`

#### Class: `ResponseParser`

Parses and standardizes LLM responses.

##### Methods

###### `parse_response(llm_response: str) -> DiagnosticResponse`
Parse LLM response into structured format.

**Parameters:**
- `llm_response`: Raw text response from LLM

**Returns:**
- `DiagnosticResponse`: Structured diagnostic response

---

###### `compare_responses(responses: List[DiagnosticResponse]) -> Dict[str, Any]`
Compare multiple diagnostic responses for consensus.

**Parameters:**
- `responses`: List of parsed diagnostic responses

**Returns:**
- Dictionary containing:
  - `diagnoses`: All mentioned diagnoses
  - `agreement_scores`: Consensus scores for each diagnosis
  - `unique_perspectives`: List of unique viewpoints
  - `common_uncertainties`: Shared uncertainties

---

#### Class: `DiagnosticResponse`

Structured medical diagnostic response.

**Attributes:**
- `initial_impression` (str): Initial clinical impression
- `differential_diagnoses` (List[Dict]): List of diagnoses with reasoning
- `alternative_perspectives` (str): Alternative viewpoints
- `next_steps` (str): Recommended next steps
- `uncertainties` (str): Areas of uncertainty
- `population_considerations` (Optional[str]): Population-specific factors
- `confidence_score` (Optional[float]): Confidence level (0-1)
- `raw_response` (Optional[str]): Original response text

---

### `medley.processors.cache_manager`

#### Class: `CacheManager`

Manages file-based caching of LLM responses.

##### Methods

###### `get_cached_response(case_id: str, model_id: str, prompt: str, system_prompt: Optional[str] = None, max_age_hours: int = 24) -> Optional[LLMResponse]`
Retrieve cached response if available and fresh.

**Parameters:**
- `case_id`: Case identifier
- `model_id`: Model identifier
- `prompt`: Original prompt
- `system_prompt`: System prompt if used
- `max_age_hours`: Maximum cache age in hours

**Returns:**
- `LLMResponse` if cached and valid, `None` otherwise

---

###### `save_response(case_id: str, model_id: str, prompt: str, response: LLMResponse, system_prompt: Optional[str] = None)`
Save LLM response to cache.

**Parameters:**
- `case_id`: Case identifier
- `model_id`: Model identifier
- `prompt`: Original prompt
- `response`: LLM response to cache
- `system_prompt`: System prompt if used

---

###### `get_cache_statistics() -> Dict[str, Any]`
Get cache usage statistics.

**Returns:**
- Dictionary containing:
  - `total_cached_responses`: Number of cached responses
  - `total_tokens_used`: Total tokens consumed
  - `average_latency`: Average response time
  - `unique_cases`: Number of unique cases
  - `cache_size_mb`: Cache size in megabytes

---

### `medley.utils.config`

#### Class: `Config`

Central configuration manager for Medley.

##### Methods

###### `__init__(config_dir: Optional[Path] = None)`
Initialize configuration.

**Parameters:**
- `config_dir`: Optional custom configuration directory

---

###### `get_model(model_name: str) -> Optional[ModelConfig]`
Get configuration for a specific model.

**Parameters:**
- `model_name`: Name of the model

**Returns:**
- `ModelConfig` if found, `None` otherwise

---

###### `validate() -> bool`
Validate configuration completeness.

**Returns:**
- `True` if valid

**Raises:**
- `ValueError`: If configuration is invalid

---

#### Class: `ModelConfig`

Configuration for a single LLM model.

**Attributes:**
- `name` (str): Display name
- `provider` (str): Model provider
- `model_id` (str): API model identifier
- `max_tokens` (int): Maximum token limit
- `temperature` (float): Temperature setting
- `description` (str): Model description
- `origin` (str): Model origin/country
- `size` (str): Model size category

---

## CLI Commands

### `medley analyze`

Analyze a medical case using specified model.

```bash
medley analyze <case_file> [OPTIONS]
```

**Options:**
- `--model, -m`: Model to use (default: gemini-2.5-pro)
- `--no-cache`: Skip cache and force new API call
- `--output, -o`: Output file path
- `--json`: Output as JSON format

---

### `medley setup`

Initialize Medley configuration and directories.

```bash
medley setup
```

---

### `medley test`

Test OpenRouter API connection.

```bash
medley test
```

---

### `medley cache-stats`

Display cache statistics.

```bash
medley cache-stats
```

---

### `medley clear-cache`

Clear cache for a specific case.

```bash
medley clear-cache <case_id>
```

---

### `medley validate`

Validate cache integrity.

```bash
medley validate
```