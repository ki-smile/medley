"""
Unit tests for configuration management
"""

import pytest
import os
from pathlib import Path

from src.medley.utils.config import Config, ModelConfig


class TestConfig:
    """Test configuration management"""
    
    @pytest.mark.unit
    def test_config_initialization(self, temp_dir):
        """Test config initialization with custom directory"""
        config = Config(config_dir=temp_dir)
        
        assert config.config_dir == temp_dir
        assert config.cache_dir.exists()
        assert config.reports_dir.exists()
        
    @pytest.mark.unit
    def test_config_api_key_from_env(self, temp_dir, monkeypatch):
        """Test loading API key from environment"""
        monkeypatch.setenv("OPENROUTER_API_KEY", "test-key-123")
        
        config = Config(config_dir=temp_dir)
        assert config.api_key == "test-key-123"
    
    @pytest.mark.unit
    def test_config_validation_missing_api_key(self, temp_dir):
        """Test validation fails without API key"""
        config = Config(config_dir=temp_dir)
        config.api_key = ""
        
        with pytest.raises(ValueError, match="OPENROUTER_API_KEY"):
            config.validate()
    
    @pytest.mark.unit
    def test_default_model_config(self, temp_dir):
        """Test default model configuration is loaded"""
        config = Config(config_dir=temp_dir)
        
        models = config.get_all_models()
        assert len(models) > 0
        
        # Check default Gemini model
        gemini = config.get_model("gemini-2.5-pro")
        assert gemini is not None
        assert gemini.name == "Gemini 2.5 Pro"
        assert gemini.provider == "google"
    
    @pytest.mark.unit
    def test_save_and_load_configs(self, temp_dir):
        """Test saving and loading configuration files"""
        config = Config(config_dir=temp_dir)
        config.save_default_configs()
        
        # Check files were created
        assert (temp_dir / "models.yaml").exists()
        assert (temp_dir / "prompts.yaml").exists()
        
        # Reload config and verify
        config2 = Config(config_dir=temp_dir)
        assert config2.get_model("gemini-2.5-pro") is not None
        assert config2.get_prompt("medical_analysis") is not None
    
    @pytest.mark.unit
    def test_model_config_dataclass(self):
        """Test ModelConfig dataclass"""
        model = ModelConfig(
            name="Test Model",
            provider="test",
            model_id="test/model-1",
            max_tokens=2048,
            temperature=0.5
        )
        
        assert model.name == "Test Model"
        assert model.max_tokens == 2048
        assert model.temperature == 0.5
        assert model.description == ""  # Default value
    
    @pytest.mark.unit
    def test_get_nonexistent_model(self, temp_dir):
        """Test getting non-existent model returns None"""
        config = Config(config_dir=temp_dir)
        
        model = config.get_model("nonexistent-model")
        assert model is None
    
    @pytest.mark.unit
    def test_custom_cache_dir(self, temp_dir, monkeypatch):
        """Test custom cache directory from environment"""
        custom_cache = temp_dir / "custom_cache"
        monkeypatch.setenv("MEDLEY_CACHE_DIR", str(custom_cache))
        
        config = Config(config_dir=temp_dir)
        assert config.cache_dir == custom_cache
        assert custom_cache.exists()