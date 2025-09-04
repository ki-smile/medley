"""
End-to-end integration tests for Medley
"""

import pytest
import json
from pathlib import Path
from unittest.mock import patch, MagicMock

from src.medley.utils.config import Config
from src.medley.models.llm_manager import LLMManager
from src.medley.processors.case_processor import CaseProcessor
from src.medley.processors.response_parser import ResponseParser
from src.medley.processors.cache_manager import CacheManager


class TestEndToEnd:
    """Test complete workflow integration"""
    
    @pytest.mark.integration
    def test_full_case_analysis_workflow(self, temp_dir):
        """Test complete case analysis workflow"""
        # Setup
        config = Config(config_dir=temp_dir / "config")
        config.api_key = "test-key"
        config.cache_dir = temp_dir / "cache"
        
        # Create test case
        case_file = temp_dir / "test_case.txt"
        case_file.write_text("""
        ## Case: Integration Test
        
        **Patient:** 45-year-old male with chest pain
        
        **Bias Testing Target:** Age bias test
        
        Presents with acute onset chest pain and dyspnea.
        """)
        
        # Initialize components
        case_processor = CaseProcessor(cases_dir=temp_dir)
        response_parser = ResponseParser()
        cache_manager = CacheManager(cache_dir=config.cache_dir)
        
        # Load case
        case = case_processor.load_case_from_file(case_file)
        
        # Verify bias filtering
        assert case.bias_testing_target is not None
        prompt = case.to_prompt()
        assert "bias" not in prompt.lower()
        
        # Mock LLM response
        with patch('requests.post') as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "choices": [{
                    "message": {
                        "content": """
                        **1. Initial Impression**
                        Acute coronary syndrome
                        
                        **2. Primary Differential Diagnosis**
                        1. Myocardial infarction
                        2. Pulmonary embolism
                        """
                    }
                }],
                "usage": {"total_tokens": 100}
            }
            mock_post.return_value = mock_response
            
            # Query model
            llm_manager = LLMManager(config)
            model_config = config.get_all_models()[0]
            
            response = llm_manager.query_model(
                model_config=model_config,
                prompt=prompt
            )
            
            # Parse response
            parsed = response_parser.parse_response(response.content)
            
            assert "Acute coronary syndrome" in parsed.initial_impression
            assert len(parsed.differential_diagnoses) >= 2
            
            # Cache response
            cache_manager.save_response(
                case_id=case.case_id,
                model_id=model_config.model_id,
                prompt=prompt,
                response=response
            )
            
            # Verify cache
            cached = cache_manager.get_cached_response(
                case_id=case.case_id,
                model_id=model_config.model_id,
                prompt=prompt
            )
            
            assert cached is not None
            assert cached.content == response.content
    
    @pytest.mark.integration
    def test_multiple_cases_processing(self, temp_dir):
        """Test processing multiple cases"""
        # Create multiple case files
        cases_dir = temp_dir / "cases"
        cases_dir.mkdir()
        
        for i in range(3):
            case_file = cases_dir / f"case_{i}.txt"
            case_file.write_text(f"""
            **Patient:** Patient {i} with symptoms
            **Bias Testing Target:** Test bias {i}
            Clinical presentation {i}
            """)
        
        # Process all cases
        processor = CaseProcessor(cases_dir=cases_dir)
        cases = processor.load_all_cases()
        
        assert len(cases) == 3
        
        # Verify all cases have bias filtered
        for case in cases:
            prompt = case.to_prompt()
            assert "bias" not in prompt.lower()
            assert f"Patient {case.case_id[-1]}" in prompt
    
    @pytest.mark.integration
    def test_cache_persistence(self, temp_dir):
        """Test cache persistence across sessions"""
        cache_dir = temp_dir / "cache"
        
        # First session - save data
        cache_manager1 = CacheManager(cache_dir=cache_dir)
        
        from src.medley.models.llm_manager import LLMResponse
        response = LLMResponse(
            model_name="Test",
            model_id="test/model",
            content="Test response",
            timestamp="2024-01-01",
            latency=1.0,
            tokens_used=50
        )
        
        cache_manager1.save_response(
            case_id="persistent_case",
            model_id="test/model",
            prompt="test prompt",
            response=response
        )
        
        # Second session - retrieve data
        cache_manager2 = CacheManager(cache_dir=cache_dir)
        
        cached = cache_manager2.get_cached_response(
            case_id="persistent_case",
            model_id="test/model",
            prompt="test prompt"
        )
        
        assert cached is not None
        assert cached.content == "Test response"
    
    @pytest.mark.integration
    def test_ensemble_workflow(self, temp_dir):
        """Test ensemble analysis workflow"""
        config = Config(config_dir=temp_dir)
        config.api_key = "test-key"
        
        cache_manager = CacheManager(cache_dir=temp_dir / "cache")
        parser = ResponseParser()
        
        # Create multiple model responses
        responses = []
        for i in range(3):
            from src.medley.models.llm_manager import LLMResponse
            response = LLMResponse(
                model_name=f"Model {i}",
                model_id=f"model_{i}",
                content=f"""
                **1. Initial Impression**
                Impression {i}
                
                **2. Primary Differential Diagnosis**
                1. Diagnosis A - reasoning
                2. Diagnosis B - reasoning
                """,
                timestamp="2024-01-01",
                latency=1.0,
                tokens_used=100
            )
            responses.append(response)
            
            # Save to cache
            cache_manager.save_response(
                case_id="ensemble_case",
                model_id=f"model_{i}",
                prompt="test",
                response=response
            )
        
        # Parse all responses
        parsed_responses = [
            parser.parse_response(r.content) for r in responses
        ]
        
        # Compare responses
        comparison = parser.compare_responses(parsed_responses)
        
        assert "Diagnosis A" in comparison["diagnoses"]
        assert comparison["agreement_scores"]["diagnosis a"] == 1.0
        
        # Save ensemble result
        cache_manager.save_ensemble_result("ensemble_case", comparison)
        
        # Verify saved
        result = cache_manager.get_ensemble_result("ensemble_case")
        assert result is not None
        assert "diagnoses" in result
    
    @pytest.mark.integration
    @pytest.mark.slow
    def test_concurrent_cache_access(self, temp_dir):
        """Test concurrent cache access"""
        import threading
        
        cache_manager = CacheManager(cache_dir=temp_dir)
        errors = []
        
        def save_response(thread_id):
            try:
                from src.medley.models.llm_manager import LLMResponse
                response = LLMResponse(
                    model_name=f"Model {thread_id}",
                    model_id=f"model_{thread_id}",
                    content=f"Response {thread_id}",
                    timestamp="2024-01-01",
                    latency=1.0,
                    tokens_used=50
                )
                
                cache_manager.save_response(
                    case_id=f"case_{thread_id}",
                    model_id=f"model_{thread_id}",
                    prompt=f"prompt_{thread_id}",
                    response=response
                )
            except Exception as e:
                errors.append(e)
        
        # Create multiple threads
        threads = []
        for i in range(5):
            t = threading.Thread(target=save_response, args=(i,))
            threads.append(t)
            t.start()
        
        # Wait for completion
        for t in threads:
            t.join()
        
        # Check no errors
        assert len(errors) == 0
        
        # Verify all saved
        stats = cache_manager.get_cache_statistics()
        assert stats["total_cached_responses"] == 5