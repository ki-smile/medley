"""
Unit tests for cache manager
"""

import pytest
import json
from pathlib import Path
from datetime import datetime, timedelta

from src.medley.processors.cache_manager import CacheManager
from src.medley.models.llm_manager import LLMResponse


class TestCacheManager:
    """Test cache management functionality"""
    
    @pytest.mark.unit
    def test_cache_manager_initialization(self, temp_dir):
        """Test cache manager initialization"""
        cache_manager = CacheManager(cache_dir=temp_dir)
        
        assert cache_manager.cache_dir == temp_dir
        assert cache_manager.responses_dir.exists()
        assert cache_manager.ensembles_dir.exists()
        assert cache_manager.metadata_dir.exists()
    
    @pytest.mark.unit
    def test_generate_cache_key(self, temp_dir):
        """Test cache key generation"""
        cache_manager = CacheManager(cache_dir=temp_dir)
        
        key1 = cache_manager.generate_cache_key("prompt1", "model1")
        key2 = cache_manager.generate_cache_key("prompt1", "model1")
        key3 = cache_manager.generate_cache_key("prompt2", "model1")
        
        assert key1 == key2  # Same input = same key
        assert key1 != key3  # Different input = different key
        assert len(key1) == 16  # Key length
    
    @pytest.mark.unit
    def test_save_and_retrieve_response(self, temp_dir, sample_llm_response):
        """Test saving and retrieving cached response"""
        cache_manager = CacheManager(cache_dir=temp_dir)
        
        # Save response
        cache_manager.save_response(
            case_id="test_case",
            model_id="test/model",
            prompt="test prompt",
            response=sample_llm_response
        )
        
        # Retrieve response
        cached = cache_manager.get_cached_response(
            case_id="test_case",
            model_id="test/model",
            prompt="test prompt"
        )
        
        assert cached is not None
        assert cached.model_name == sample_llm_response.model_name
        assert cached.content == sample_llm_response.content
    
    @pytest.mark.unit
    def test_cache_expiry(self, temp_dir, sample_llm_response):
        """Test cache expiry based on age"""
        cache_manager = CacheManager(cache_dir=temp_dir)
        
        # Save response
        cache_manager.save_response(
            case_id="test_case",
            model_id="test/model",
            prompt="test prompt",
            response=sample_llm_response
        )
        
        # Modify cache timestamp to be old
        cache_key = cache_manager.generate_cache_key("test prompt", "test/model")
        cache_manager.cache_index[cache_key]["timestamp"] = (
            datetime.now() - timedelta(hours=25)
        ).isoformat()
        
        # Try to retrieve with 24-hour max age
        cached = cache_manager.get_cached_response(
            case_id="test_case",
            model_id="test/model",
            prompt="test prompt",
            max_age_hours=24
        )
        
        assert cached is None  # Should be expired
    
    @pytest.mark.unit
    def test_get_case_responses(self, temp_dir):
        """Test getting all responses for a case"""
        cache_manager = CacheManager(cache_dir=temp_dir)
        
        # Save multiple responses
        for i in range(3):
            response = LLMResponse(
                model_name=f"Model {i}",
                model_id=f"model_{i}",
                content=f"Response {i}",
                timestamp=datetime.now().isoformat(),
                latency=1.0,
                tokens_used=100
            )
            cache_manager.save_response(
                case_id="test_case",
                model_id=f"model_{i}",
                prompt="test",
                response=response
            )
        
        # Get all responses
        responses = cache_manager.get_case_responses("test_case")
        
        assert len(responses) == 3
        assert all(isinstance(r, LLMResponse) for r in responses)
    
    @pytest.mark.unit
    def test_save_and_get_ensemble_result(self, temp_dir):
        """Test saving and retrieving ensemble results"""
        cache_manager = CacheManager(cache_dir=temp_dir)
        
        ensemble_data = {
            "consensus": "Test diagnosis",
            "agreement_score": 0.8,
            "models": ["model1", "model2"]
        }
        
        cache_manager.save_ensemble_result("test_case", ensemble_data)
        
        result = cache_manager.get_ensemble_result("test_case")
        
        assert result is not None
        assert result["consensus"] == "Test diagnosis"
        assert result["case_id"] == "test_case"
        assert "timestamp" in result
    
    @pytest.mark.unit
    def test_clear_case_cache(self, temp_dir, sample_llm_response):
        """Test clearing cache for specific case"""
        cache_manager = CacheManager(cache_dir=temp_dir)
        
        # Save data
        cache_manager.save_response(
            case_id="test_case",
            model_id="test/model",
            prompt="test",
            response=sample_llm_response
        )
        cache_manager.save_ensemble_result("test_case", {"test": "data"})
        
        # Clear cache
        cache_manager.clear_case_cache("test_case")
        
        # Verify cleared
        assert len(cache_manager.get_case_responses("test_case")) == 0
        assert cache_manager.get_ensemble_result("test_case") is None
    
    @pytest.mark.unit
    def test_cache_statistics(self, temp_dir, sample_llm_response):
        """Test cache statistics calculation"""
        cache_manager = CacheManager(cache_dir=temp_dir)
        
        # Save some responses
        for i in range(2):
            cache_manager.save_response(
                case_id=f"case_{i}",
                model_id="test/model",
                prompt=f"prompt_{i}",
                response=sample_llm_response
            )
        
        stats = cache_manager.get_cache_statistics()
        
        assert stats["total_cached_responses"] == 2
        assert stats["unique_cases"] == 2
        assert stats["total_tokens_used"] == 300  # 150 * 2
        assert "cache_size_mb" in stats
    
    @pytest.mark.unit
    def test_validate_cache(self, temp_dir, sample_llm_response):
        """Test cache validation"""
        cache_manager = CacheManager(cache_dir=temp_dir)
        
        # Save valid response
        cache_manager.save_response(
            case_id="test",
            model_id="model",
            prompt="prompt",
            response=sample_llm_response
        )
        
        # Validate - should be valid
        validation = cache_manager.validate_cache()
        assert validation["valid"] is True
        assert len(validation["issues"]) == 0
        
        # Corrupt cache by removing file
        case_dir = cache_manager.responses_dir / "test"
        for file in case_dir.glob("*.json"):
            file.unlink()
        
        # Validate again - should find issue
        validation = cache_manager.validate_cache()
        assert validation["valid"] is False
        assert len(validation["issues"]) > 0
    
    @pytest.mark.unit
    def test_prompt_hash_mapping(self, temp_dir):
        """Test prompt hash mapping storage"""
        cache_manager = CacheManager(cache_dir=temp_dir)
        
        key = cache_manager.generate_cache_key("Long prompt text...", "model")
        
        # Check hash mapping was saved
        assert key in cache_manager.prompt_hashes
        assert "prompt_preview" in cache_manager.prompt_hashes[key]
        assert "model_id" in cache_manager.prompt_hashes[key]
        
        # Verify saved to file
        assert cache_manager.prompt_hashes_file.exists()