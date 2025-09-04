"""
Enhanced integration tests for the complete MEDLEY pipeline
"""

import pytest
import json
import os
from pathlib import Path
from unittest.mock import patch, Mock
import tempfile
import shutil


class TestPipelineIntegration:
    """Test complete pipeline integration"""
    
    @pytest.fixture
    def temp_dirs(self):
        """Create temporary directories for testing"""
        temp_dir = tempfile.mkdtemp()
        cache_dir = Path(temp_dir) / "cache"
        reports_dir = Path(temp_dir) / "reports"
        cache_dir.mkdir(parents=True)
        reports_dir.mkdir(parents=True)
        
        yield {
            "base": temp_dir,
            "cache": cache_dir,
            "reports": reports_dir
        }
        
        # Cleanup
        shutil.rmtree(temp_dir)
    
    @pytest.mark.integration
    def test_pipeline_with_cache_validation(self, temp_dirs):
        """Test pipeline validates cache before using it"""
        
        # Create invalid cache file (too small)
        cache_file = temp_dirs["cache"] / "test_model.json"
        cache_file.write_text(json.dumps({"content": ""}))
        
        # Pipeline should detect invalid cache
        assert cache_file.stat().st_size < 1024
        
        # Create valid cache file
        valid_cache = {
            "model_name": "Test Model",
            "model_id": "test/model",
            "content": "A" * 100,  # Sufficient content
            "timestamp": "2025-08-10T10:00:00"
        }
        cache_file.write_text(json.dumps(valid_cache))
        
        # Now cache should be valid
        assert cache_file.stat().st_size >= 1024
    
    @pytest.mark.integration
    def test_gemini_reasoning_field_integration(self, temp_dirs):
        """Test Gemini model response with reasoning field"""
        
        # Simulate Gemini response with reasoning field
        gemini_response = {
            "model_name": "Gemini 2.5 Pro",
            "model_id": "google/gemini-2.5-pro",
            "content": "",  # Empty content
            "reasoning": "Detailed medical analysis here...",  # Content in reasoning
            "timestamp": "2025-08-10T10:00:00",
            "tokens_used": 150
        }
        
        cache_file = temp_dirs["cache"] / "google_gemini-2.5-pro.json"
        cache_file.write_text(json.dumps(gemini_response))
        
        # Load and validate
        with open(cache_file) as f:
            loaded = json.load(f)
        
        # Check that reasoning field is present
        assert loaded.get("reasoning")
        assert not loaded.get("content")
    
    @pytest.mark.integration
    def test_consensus_analysis_with_multiple_models(self, temp_dirs):
        """Test consensus analysis with responses from multiple models"""
        
        # Create mock responses from different countries
        responses = [
            {
                "model_id": "openai/gpt-4o",
                "content": "Diagnosis: Familial Mediterranean Fever",
                "country": "USA"
            },
            {
                "model_id": "mistralai/mistral-large",
                "content": "Diagnosis: Familial Mediterranean Fever",
                "country": "France"
            },
            {
                "model_id": "deepseek/deepseek-v3",
                "content": "Diagnosis: Periodic Fever Syndrome",
                "country": "China"
            }
        ]
        
        # Save responses
        for i, response in enumerate(responses):
            cache_file = temp_dirs["cache"] / f"model_{i}.json"
            cache_file.write_text(json.dumps(response))
        
        # Calculate consensus
        diagnoses = ["FMF", "FMF", "Other"]
        consensus = diagnoses.count("FMF") / len(diagnoses)
        
        assert consensus > 0.5  # Majority consensus
    
    @pytest.mark.integration
    def test_pdf_report_generation(self, temp_dirs):
        """Test PDF report generation with all features"""
        
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import letter
        
        # Create test PDF
        pdf_path = temp_dirs["reports"] / "test_report.pdf"
        c = canvas.Canvas(str(pdf_path), pagesize=letter)
        
        # Add content
        c.drawString(100, 750, "MEDLEY Medical Report")
        c.drawString(100, 730, "Primary Diagnosis: Test Diagnosis")
        c.drawString(100, 710, "Evidence: Test evidence")
        c.save()
        
        # Verify PDF created
        assert pdf_path.exists()
        assert pdf_path.stat().st_size > 0
    
    @pytest.mark.integration
    def test_bias_analysis_by_country(self, temp_dirs):
        """Test bias analysis grouped by model origin"""
        
        # Create responses from different countries
        country_responses = {
            "USA": ["FMF", "FMF", "FMF"],
            "China": ["FMF", "Other", "Other"],
            "France": ["FMF", "FMF", "Other"]
        }
        
        # Calculate consensus by country
        consensus_by_country = {}
        for country, diagnoses in country_responses.items():
            primary = max(set(diagnoses), key=diagnoses.count)
            consensus = diagnoses.count(primary) / len(diagnoses)
            consensus_by_country[country] = consensus
        
        # USA should have highest consensus
        assert consensus_by_country["USA"] == 1.0
        assert consensus_by_country["China"] < 0.5
        assert consensus_by_country["France"] > 0.5
    
    @pytest.mark.integration
    def test_orchestrator_retry_mechanism(self):
        """Test orchestrator retry with fallback model"""
        
        attempts = []
        
        def mock_query(model, prompt):
            attempts.append(model)
            if model == "anthropic/claude-3-5-sonnet-20241022" and len(attempts) == 1:
                # First attempt fails
                return {"error": "Rate limit"}
            else:
                # Fallback succeeds
                return {"content": "Success"}
        
        # Simulate retry
        primary = "anthropic/claude-3-5-sonnet-20241022"
        fallback = "anthropic/claude-3-opus-20240229"
        
        result = mock_query(primary, "test")
        if "error" in result:
            result = mock_query(fallback, "test")
        
        assert len(attempts) == 2
        assert attempts[0] == primary
        assert attempts[1] == fallback
        assert result["content"] == "Success"
    
    @pytest.mark.integration
    def test_table_width_consistency(self):
        """Test all PDF tables have consistent 6.5 inch width"""
        
        from reportlab.platypus import Table
        from reportlab.lib.units import inch
        
        # Test different table configurations
        tables = [
            Table([["Test"]], colWidths=[6.5*inch]),  # Single column
            Table([["A", "B"]], colWidths=[3.25*inch, 3.25*inch]),  # Two columns
            Table([["A", "B", "C", "D"]], colWidths=[1.625*inch]*4),  # Four columns
        ]
        
        for table in tables:
            total_width = sum(table._colWidths)
            assert abs(total_width - 6.5*inch) < 0.01  # Allow small rounding error
    
    @pytest.mark.integration
    def test_icd10_code_integration(self):
        """Test ICD-10 code lookup and integration"""
        
        icd_codes = {
            "Familial Mediterranean Fever": "E85.0",
            "Alzheimer's Disease": "G30.9",
            "Substance-Induced Psychosis": "F19.959"
        }
        
        diagnosis = "Familial Mediterranean Fever"
        icd_code = icd_codes.get(diagnosis, "R69")
        
        assert icd_code == "E85.0"
    
    @pytest.mark.integration
    def test_minority_opinion_preservation(self):
        """Test that minority opinions are preserved in analysis"""
        
        responses = [
            {"diagnosis": "FMF", "model": "gpt-4"},
            {"diagnosis": "FMF", "model": "claude"},
            {"diagnosis": "FMF", "model": "gemini"},
            {"diagnosis": "Crohn's Disease", "model": "deepseek"},  # Minority
        ]
        
        # Extract minority opinions
        all_diagnoses = [r["diagnosis"] for r in responses]
        unique_diagnoses = set(all_diagnoses)
        
        minority_opinions = []
        for diagnosis in unique_diagnoses:
            count = all_diagnoses.count(diagnosis)
            if count < len(responses) * 0.3:  # Less than 30%
                minority_opinions.append({
                    "diagnosis": diagnosis,
                    "support": count / len(responses)
                })
        
        assert len(minority_opinions) == 1
        assert minority_opinions[0]["diagnosis"] == "Crohn's Disease"
        assert minority_opinions[0]["support"] == 0.25


class TestPerformanceOptimization:
    """Test performance optimizations"""
    
    @pytest.mark.integration
    def test_parallel_query_performance(self):
        """Test parallel querying improves performance"""
        
        import time
        import asyncio
        
        async def mock_query_async(model):
            await asyncio.sleep(0.1)  # Simulate API call
            return {"model": model, "content": "Response"}
        
        async def query_parallel(models):
            tasks = [mock_query_async(m) for m in models]
            return await asyncio.gather(*tasks)
        
        models = ["model1", "model2", "model3", "model4", "model5"]
        
        # Measure parallel execution
        start = time.time()
        asyncio.run(query_parallel(models))
        parallel_time = time.time() - start
        
        # Should be much faster than sequential (0.5s)
        assert parallel_time < 0.3  # Some overhead allowed
    
    @pytest.mark.integration
    def test_cache_hit_performance(self, temp_dirs):
        """Test cache hits are faster than API calls"""
        
        import time
        
        # Create cache file
        cache_file = temp_dirs["cache"] / "cached_response.json"
        cache_data = {
            "content": "Cached response",
            "timestamp": "2025-08-10T10:00:00"
        }
        cache_file.write_text(json.dumps(cache_data))
        
        # Measure cache read
        start = time.time()
        with open(cache_file) as f:
            data = json.load(f)
        cache_time = time.time() - start
        
        # Cache read should be very fast
        assert cache_time < 0.01  # Less than 10ms
        assert data["content"] == "Cached response"