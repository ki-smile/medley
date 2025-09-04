"""
Unit tests for LLM manager
"""

import pytest
import asyncio
from unittest.mock import patch, MagicMock

from src.medley.models.llm_manager import LLMManager, LLMResponse
from src.medley.utils.config import Config, ModelConfig


class TestLLMManager:
    """Test LLM manager functionality"""
    
    @pytest.mark.unit
    def test_llm_manager_initialization(self, mock_config):
        """Test LLM manager initialization"""
        manager = LLMManager(mock_config)
        
        assert manager.config == mock_config
        assert manager.api_key == "test-api-key"
        assert "Authorization" in manager.headers
    
    @pytest.mark.unit
    def test_llm_manager_no_api_key(self, mock_config):
        """Test initialization fails without API key"""
        mock_config.api_key = ""
        
        with pytest.raises(ValueError, match="API key not configured"):
            LLMManager(mock_config)
    
    @pytest.mark.unit
    def test_query_model_success(self, mock_config, sample_model_config, mock_api_client):
        """Test successful model query"""
        manager = LLMManager(mock_config)
        
        response = manager.query_model(
            model_config=sample_model_config,
            prompt="Test prompt"
        )
        
        assert isinstance(response, LLMResponse)
        assert response.model_name == "Test Model"
        assert response.content == "Test response"
        assert response.error is None
        assert response.tokens_used == 50
    
    @pytest.mark.unit
    def test_query_model_with_system_prompt(self, mock_config, sample_model_config):
        """Test query with system prompt"""
        manager = LLMManager(mock_config)
        
        with patch('requests.post') as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "choices": [{"message": {"content": "Response"}}],
                "usage": {"total_tokens": 100}
            }
            mock_post.return_value = mock_response
            
            response = manager.query_model(
                model_config=sample_model_config,
                prompt="User prompt",
                system_prompt="System prompt"
            )
            
            # Verify system prompt was included
            call_args = mock_post.call_args
            messages = call_args[1]["json"]["messages"]
            assert len(messages) == 2
            assert messages[0]["role"] == "system"
            assert messages[0]["content"] == "System prompt"
    
    @pytest.mark.unit
    def test_query_model_api_error(self, mock_config, sample_model_config):
        """Test handling API error"""
        manager = LLMManager(mock_config)
        
        with patch('requests.post') as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 500
            mock_response.text = "Internal Server Error"
            mock_post.return_value = mock_response
            
            response = manager.query_model(
                model_config=sample_model_config,
                prompt="Test"
            )
            
            assert response.error is not None
            assert "API Error 500" in response.error
            assert response.content == ""
    
    @pytest.mark.unit
    def test_query_model_timeout(self, mock_config, sample_model_config):
        """Test handling request timeout"""
        manager = LLMManager(mock_config)
        
        with patch('requests.post') as mock_post:
            mock_post.side_effect = Exception("Timeout")
            
            response = manager.query_model(
                model_config=sample_model_config,
                prompt="Test"
            )
            
            assert response.error is not None
            assert "Timeout" in response.error
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_query_model_async(self, mock_config, sample_model_config):
        """Test async model query"""
        manager = LLMManager(mock_config)
        
        with patch('aiohttp.ClientSession') as mock_session_class:
            mock_session = MagicMock()
            mock_session_class.return_value.__aenter__.return_value = mock_session
            
            mock_response = MagicMock()
            mock_response.status = 200
            mock_response.json = asyncio.coroutine(lambda: {
                "choices": [{"message": {"content": "Async response"}}],
                "usage": {"total_tokens": 75}
            })
            
            mock_session.post.return_value.__aenter__.return_value = mock_response
            
            response = await manager.query_model_async(
                session=mock_session,
                model_config=sample_model_config,
                prompt="Test"
            )
            
            assert response.content == "Async response"
            assert response.tokens_used == 75
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_query_models_parallel(self, mock_config):
        """Test parallel model querying"""
        manager = LLMManager(mock_config)
        
        models = [
            ModelConfig(name=f"Model{i}", provider="test", 
                       model_id=f"test/model-{i}", max_tokens=1000, 
                       temperature=0.7)
            for i in range(3)
        ]
        
        with patch.object(manager, 'query_model_async') as mock_query:
            mock_query.return_value = LLMResponse(
                model_name="Test",
                model_id="test",
                content="Response",
                timestamp="2024-01-01",
                latency=1.0
            )
            
            responses = await manager.query_models_parallel(
                model_configs=models,
                prompt="Test"
            )
            
            assert len(responses) == 3
            assert mock_query.call_count == 3
    
    @pytest.mark.unit
    def test_test_connection_success(self, mock_config):
        """Test successful connection test"""
        manager = LLMManager(mock_config)
        
        with patch('requests.get') as mock_get:
            mock_get.return_value.status_code = 200
            
            result = manager.test_connection()
            assert result is True
    
    @pytest.mark.unit
    def test_test_connection_failure(self, mock_config):
        """Test failed connection test"""
        manager = LLMManager(mock_config)
        
        with patch('requests.get') as mock_get:
            mock_get.side_effect = Exception("Connection error")
            
            result = manager.test_connection()
            assert result is False
    
    @pytest.mark.unit
    def test_llm_response_to_dict(self):
        """Test LLMResponse serialization"""
        response = LLMResponse(
            model_name="Test Model",
            model_id="test/model",
            content="Test content",
            timestamp="2024-01-01T12:00:00",
            latency=2.5,
            tokens_used=100,
            error=None
        )
        
        response_dict = response.to_dict()
        
        assert response_dict["model_name"] == "Test Model"
        assert response_dict["content"] == "Test content"
        assert response_dict["latency"] == 2.5
        assert response_dict["tokens_used"] == 100