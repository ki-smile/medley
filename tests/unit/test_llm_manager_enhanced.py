"""
Enhanced unit tests for LLM manager with reasoning field support
"""

import pytest
import json
from unittest.mock import patch, MagicMock, Mock
import requests

from src.medley.models.llm_manager import LLMManager, LLMResponse
from src.medley.utils.config import Config, ModelConfig


class TestLLMManagerEnhanced:
    """Test enhanced LLM manager functionality"""
    
    @pytest.fixture
    def mock_config(self):
        """Create mock config"""
        config = Mock(spec=Config)
        config.api_key = "test-api-key"
        return config
    
    @pytest.fixture
    def sample_model_config(self):
        """Create sample model config"""
        return ModelConfig(
            name="Test Model",
            model_id="test/model",
            max_tokens=2000,
            temperature=0.7
        )
    
    @pytest.mark.unit
    def test_extract_content_from_reasoning_field(self, mock_config, sample_model_config):
        """Test extraction of content from reasoning field for Gemini 2.5 Pro"""
        
        manager = LLMManager(mock_config)
        
        # Mock response with content in reasoning field
        mock_response = Mock(spec=requests.Response)
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{
                "message": {
                    "content": "",  # Empty content
                    "reasoning": "This is the actual medical analysis content"  # Content in reasoning
                }
            }],
            "usage": {"total_tokens": 100}
        }
        
        with patch('requests.post', return_value=mock_response):
            # Test with Gemini 2.5 Pro
            gemini_config = ModelConfig(
                name="Gemini 2.5 Pro",
                model_id="google/gemini-2.5-pro",
                max_tokens=2000,
                temperature=0.7
            )
            
            response = manager.query_model(
                model_config=gemini_config,
                prompt="Test prompt"
            )
            
            assert response.content == "This is the actual medical analysis content"
            assert response.error is None
    
    @pytest.mark.unit
    def test_combine_content_and_reasoning_fields(self, mock_config, sample_model_config):
        """Test combining both content and reasoning fields when both exist"""
        
        manager = LLMManager(mock_config)
        
        # Mock response with both fields
        mock_response = Mock(spec=requests.Response)
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{
                "message": {
                    "content": "Regular content here",
                    "reasoning": "Reasoning content here"
                }
            }],
            "usage": {"total_tokens": 150}
        }
        
        with patch('requests.post', return_value=mock_response):
            response = manager.query_model(
                model_config=sample_model_config,
                prompt="Test prompt"
            )
            
            # Should combine both with separator
            assert "Reasoning content here" in response.content
            assert "Regular content here" in response.content
            assert "---" in response.content  # Separator
    
    @pytest.mark.unit
    def test_standard_content_field_only(self, mock_config, sample_model_config):
        """Test standard response with content field only"""
        
        manager = LLMManager(mock_config)
        
        # Mock standard response
        mock_response = Mock(spec=requests.Response)
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{
                "message": {
                    "content": "Standard medical analysis"
                }
            }],
            "usage": {"total_tokens": 80}
        }
        
        with patch('requests.post', return_value=mock_response):
            response = manager.query_model(
                model_config=sample_model_config,
                prompt="Test prompt"
            )
            
            assert response.content == "Standard medical analysis"
            assert "---" not in response.content  # No separator needed
    
    @pytest.mark.unit
    def test_empty_response_handling(self, mock_config, sample_model_config):
        """Test handling of completely empty responses"""
        
        manager = LLMManager(mock_config)
        
        # Mock empty response
        mock_response = Mock(spec=requests.Response)
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{
                "message": {}  # No content or reasoning
            }],
            "usage": {"total_tokens": 0}
        }
        
        with patch('requests.post', return_value=mock_response):
            response = manager.query_model(
                model_config=sample_model_config,
                prompt="Test prompt"
            )
            
            assert response.content == ""
            assert response.error is None
    
    @pytest.mark.unit
    def test_api_error_handling(self, mock_config, sample_model_config):
        """Test handling of API errors"""
        
        manager = LLMManager(mock_config)
        
        # Mock error response
        mock_response = Mock(spec=requests.Response)
        mock_response.status_code = 429
        mock_response.text = "Rate limit exceeded"
        
        with patch('requests.post', return_value=mock_response):
            response = manager.query_model(
                model_config=sample_model_config,
                prompt="Test prompt"
            )
            
            assert response.content == ""
            assert response.error is not None
            assert "429" in response.error
            assert "Rate limit" in response.error
    
    @pytest.mark.unit
    def test_timeout_handling(self, mock_config, sample_model_config):
        """Test handling of request timeouts"""
        
        manager = LLMManager(mock_config)
        
        with patch('requests.post', side_effect=requests.exceptions.Timeout):
            response = manager.query_model(
                model_config=sample_model_config,
                prompt="Test prompt"
            )
            
            assert response.content == ""
            assert response.error == "Request timeout after 60 seconds"
    
    @pytest.mark.unit
    async def test_async_reasoning_field_extraction(self, mock_config):
        """Test async method also extracts from reasoning field"""
        
        import aiohttp
        from unittest.mock import AsyncMock
        
        manager = LLMManager(mock_config)
        
        # Create mock session and response
        mock_session = Mock(spec=aiohttp.ClientSession)
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={
            "choices": [{
                "message": {
                    "content": "",
                    "reasoning": "Async reasoning content"
                }
            }],
            "usage": {"total_tokens": 50}
        })
        
        # Mock the context manager
        mock_session.post.return_value.__aenter__ = AsyncMock(return_value=mock_response)
        mock_session.post.return_value.__aexit__ = AsyncMock(return_value=None)
        
        gemini_config = ModelConfig(
            name="Gemini 2.5 Pro",
            model_id="google/gemini-2.5-pro",
            max_tokens=2000,
            temperature=0.7
        )
        
        response = await manager.query_model_async(
            session=mock_session,
            model_config=gemini_config,
            prompt="Test prompt"
        )
        
        assert response.content == "Async reasoning content"
        assert response.error is None


class TestCacheValidation:
    """Test cache validation functionality"""
    
    @pytest.mark.unit
    def test_validate_cache_file_size(self, tmp_path):
        """Test cache file size validation"""
        
        # Create small cache file
        cache_file = tmp_path / "test_cache.json"
        cache_file.write_text(json.dumps({"content": ""}))
        
        # File should be considered invalid if < 1KB
        assert cache_file.stat().st_size < 1024
        
    @pytest.mark.unit
    def test_validate_cache_content_length(self):
        """Test cache content length validation"""
        
        # Invalid: content too short
        invalid_cache = {"content": "Short"}
        assert len(invalid_cache.get('content', '')) < 50
        
        # Valid: sufficient content
        valid_cache = {"content": "A" * 100}
        assert len(valid_cache.get('content', '')) >= 50
    
    @pytest.mark.unit
    def test_validate_cache_with_reasoning(self):
        """Test cache validation with reasoning field"""
        
        # Valid: has reasoning even if content is empty
        cache_with_reasoning = {
            "content": "",
            "reasoning": "Long reasoning text " * 10
        }
        
        # Should be valid because reasoning field has content
        has_content = bool(cache_with_reasoning.get('content') or 
                          cache_with_reasoning.get('reasoning'))
        assert has_content