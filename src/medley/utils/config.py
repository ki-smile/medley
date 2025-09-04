"""
Configuration management for Medley
Handles API keys, model settings, and application configuration
"""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from dotenv import load_dotenv

load_dotenv()

@dataclass
class ModelConfig:
    """Configuration for a single LLM model"""
    name: str
    provider: str
    model_id: str
    max_tokens: int = 4096
    temperature: float = 0.7
    description: str = ""
    origin: str = ""
    size: str = ""
    
class Config:
    """Central configuration manager for Medley"""
    
    def __init__(self, config_dir: Optional[Path] = None):
        self.config_dir = config_dir or Path.cwd() / "config"
        self.models_config_path = self.config_dir / "models.yaml"
        self.prompts_config_path = self.config_dir / "prompts.yaml"
        
        # Load environment variables
        self.api_key = os.getenv("OPENROUTER_API_KEY", "")
        self.cache_dir = Path(os.getenv("MEDLEY_CACHE_DIR", "./cache"))
        self.reports_dir = Path(os.getenv("MEDLEY_REPORTS_DIR", "./reports"))
        
        # Ensure directories exist
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.reports_dir.mkdir(parents=True, exist_ok=True)
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        # Load configurations
        self.models = self._load_models_config()
        self.prompts = self._load_prompts_config()
        
    def _load_models_config(self) -> Dict[str, ModelConfig]:
        """Load model configurations from YAML or use defaults"""
        if self.models_config_path.exists():
            with open(self.models_config_path, 'r') as f:
                config_data = yaml.safe_load(f)
                return {
                    name: ModelConfig(**model_data)
                    for name, model_data in config_data.items()
                }
        else:
            # Default model configuration for Phase 1 (single model)
            return {
                "gemini-2.5-pro": ModelConfig(
                    name="Gemini 2.5 Pro",
                    provider="google",
                    model_id="google/gemini-2.0-flash-exp:free",  # Using free tier for testing
                    max_tokens=8192,
                    temperature=0.7,
                    description="Google's multimodal model",
                    origin="USA",
                    size="Large"
                )
            }
    
    def _load_prompts_config(self) -> Dict[str, str]:
        """Load prompt templates from YAML or use defaults"""
        if self.prompts_config_path.exists():
            with open(self.prompts_config_path, 'r') as f:
                return yaml.safe_load(f)
        else:
            # Default medical analysis prompt
            return {
                "medical_analysis": """You are an experienced physician presented with a complex clinical case. Please provide your analysis following this structured approach:

**1. Initial Impression**
- What are your immediate thoughts upon hearing this presentation?
- What catches your attention first?

**2. Primary Differential Diagnosis**
- List your top 3 most likely diagnoses with brief reasoning
- What key features support each diagnosis?

**3. Alternative Perspectives**
- Consider how a physician from a different specialty might approach this case
- What diagnoses might be more common in the patient's demographic or cultural background?

**4. Next Steps and Uncertainty**
- What additional information is most critical?
- What are you most uncertain about?

**Case Presentation:**
{case_content}"""
            }
    
    def get_model(self, model_name: str) -> Optional[ModelConfig]:
        """Get configuration for a specific model"""
        return self.models.get(model_name)
    
    def get_all_models(self) -> List[ModelConfig]:
        """Get all model configurations"""
        return list(self.models.values())
    
    def get_prompt(self, prompt_name: str) -> Optional[str]:
        """Get a specific prompt template"""
        return self.prompts.get(prompt_name)
    
    def save_default_configs(self):
        """Save default configurations to YAML files"""
        # Save models config
        models_dict = {
            name: {
                "name": model.name,
                "provider": model.provider,
                "model_id": model.model_id,
                "max_tokens": model.max_tokens,
                "temperature": model.temperature,
                "description": model.description,
                "origin": model.origin,
                "size": model.size
            }
            for name, model in self.models.items()
        }
        
        with open(self.models_config_path, 'w') as f:
            yaml.dump(models_dict, f, default_flow_style=False)
        
        # Save prompts config
        with open(self.prompts_config_path, 'w') as f:
            yaml.dump(self.prompts, f, default_flow_style=False)
    
    def validate(self) -> bool:
        """Validate configuration"""
        if not self.api_key:
            raise ValueError("OPENROUTER_API_KEY environment variable not set")
        
        if not self.models:
            raise ValueError("No models configured")
        
        return True