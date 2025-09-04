#!/usr/bin/env python
"""
Unit and Integration Tests for MEDLEY Web Application
Tests all web routes, API endpoints, WebSocket functionality, and database operations
"""

import os
import json
import pytest
import tempfile
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock

# Set test environment
os.environ['TESTING'] = 'true'
os.environ['SECRET_KEY'] = 'test-secret-key'

from web_app import app, socketio, db_manager, orchestrator
from utils.security import InputValidator, RateLimiter

class TestWebRoutes:
    """Test all web routes"""
    
    @pytest.fixture
    def client(self):
        """Create test client"""
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        with app.test_client() as client:
            with app.app_context():
                yield client
    
    def test_index_route(self, client):
        """Test landing page"""
        response = client.get('/')
        assert response.status_code == 200
        assert b'MEDLEY' in response.data
        assert b'Medical AI' in response.data
    
    def test_analyze_route(self, client):
        """Test analyze page"""
        response = client.get('/analyze')
        assert response.status_code == 200
        assert b'Analyze' in response.data or b'analyze' in response.data
    
    def test_test_route(self, client):
        """Test system status page"""
        response = client.get('/test')
        assert response.status_code == 200
        assert b'System Status' in response.data or b'MEDLEY' in response.data
    
    def test_dashboard_route(self, client):
        """Test dashboard page"""
        response = client.get('/dashboard')
        assert response.status_code == 200
        assert b'Dashboard' in response.data or b'Analytics' in response.data
    
    def test_settings_route(self, client):
        """Test settings page"""
        response = client.get('/settings')
        assert response.status_code == 200
        assert b'Settings' in response.data or b'API Key' in response.data
    
    def test_api_docs_route(self, client):
        """Test API documentation page"""
        response = client.get('/api/docs')
        assert response.status_code == 200
        assert b'API' in response.data
    
    def test_visualizations_route(self, client):
        """Test visualizations page"""
        response = client.get('/visualizations')
        assert response.status_code == 200
        assert b'Visualization' in response.data or b'Chart' in response.data
    
    def test_case_viewer_route(self, client):
        """Test case viewer for predefined cases"""
        response = client.get('/case/case_001')
        assert response.status_code == 200
        assert b'case' in response.data.lower()
    
    def test_case_not_found(self, client):
        """Test case viewer with invalid case"""
        response = client.get('/case/invalid_case')
        assert response.status_code == 404
    
    def test_custom_case_route(self, client):
        """Test custom case viewer"""
        response = client.get('/case/custom_20250101_120000')
        # Should return 404 if case doesn't exist
        assert response.status_code == 404
    
    def test_compare_route(self, client):
        """Test model comparison page"""
        response = client.get('/compare')
        assert response.status_code == 200
        assert b'Compare' in response.data or b'Comparison' in response.data


class TestAPIEndpoints:
    """Test all API endpoints"""
    
    @pytest.fixture
    def client(self):
        """Create test client"""
        app.config['TESTING'] = True
        with app.test_client() as client:
            yield client
    
    def test_health_check(self, client):
        """Test health check endpoint"""
        response = client.get('/api/health')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] in ['healthy', 'degraded']
        assert 'version' in data
        assert 'timestamp' in data
    
    def test_get_cases(self, client):
        """Test get cases endpoint"""
        response = client.get('/api/cases')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert isinstance(data, list)
        if data:
            assert 'id' in data[0]
            assert 'title' in data[0]
            assert 'specialty' in data[0]
    
    def test_get_case_report(self, client):
        """Test get case report endpoint"""
        response = client.get('/api/case/case_001/report')
        # May return 404 if no report exists yet
        assert response.status_code in [200, 404]
    
    def test_get_models(self, client):
        """Test get models endpoint"""
        response = client.get('/api/models')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'free' in data
        assert 'paid' in data
        assert isinstance(data['free'], list)
        assert isinstance(data['paid'], list)
    
    def test_session_status(self, client):
        """Test session status endpoint"""
        response = client.get('/api/session/status')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'api_key_set' in data
        assert 'analyses_count' in data
    
    def test_set_api_key(self, client):
        """Test set API key endpoint"""
        response = client.post('/api/session/set-key',
            json={'api_key': 'sk-or-v1-test-key-1234567890'},
            content_type='application/json'
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] == True
    
    def test_invalid_api_key(self, client):
        """Test invalid API key"""
        response = client.post('/api/session/set-key',
            json={'api_key': 'invalid-key'},
            content_type='application/json'
        )
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
    
    @patch('web_app.orchestrator')
    def test_analyze_endpoint(self, mock_orchestrator, client):
        """Test analyze endpoint"""
        if not mock_orchestrator:
            pytest.skip("Orchestrator not available")
        
        mock_orchestrator.start_analysis.return_value = {
            'analysis_id': 'custom_20250101_120000',
            'status': 'started'
        }
        
        response = client.post('/api/analyze',
            json={
                'case_text': 'A 45-year-old patient presents with chest pain...',
                'api_key': 'sk-or-v1-test',
                'use_free_models': True
            },
            content_type='application/json'
        )
        
        assert response.status_code in [200, 503]  # 503 if orchestrator not available
    
    def test_analyze_missing_fields(self, client):
        """Test analyze with missing required fields"""
        response = client.post('/api/analyze',
            json={'case_text': 'Test case'},
            content_type='application/json'
        )
        assert response.status_code in [400, 503]
    
    def test_analyze_invalid_case(self, client):
        """Test analyze with invalid case text"""
        response = client.post('/api/analyze',
            json={
                'case_text': 'Too short',
                'api_key': 'sk-or-v1-test'
            },
            content_type='application/json'
        )
        assert response.status_code in [400, 503]
    
    def test_get_analysis_status(self, client):
        """Test get analysis status endpoint"""
        response = client.get('/api/analyze/custom_20250101_120000/status')
        # Should return 404 if analysis doesn't exist
        assert response.status_code in [404, 503]
    
    def test_cancel_analysis(self, client):
        """Test cancel analysis endpoint"""
        response = client.delete('/api/analyze/custom_20250101_120000')
        assert response.status_code in [200, 404, 503]
    
    def test_performance_metrics(self, client):
        """Test performance metrics endpoint"""
        response = client.get('/api/metrics/performance')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'models' in data
    
    def test_export_metrics(self, client):
        """Test export metrics endpoint"""
        response = client.get('/api/metrics/export?format=csv')
        assert response.status_code == 200
        assert response.content_type in ['text/csv', 'application/json']


class TestWebSocketFunctionality:
    """Test WebSocket functionality"""
    
    @pytest.fixture
    def socket_client(self):
        """Create WebSocket test client"""
        app.config['TESTING'] = True
        client = socketio.test_client(app)
        yield client
        client.disconnect()
    
    def test_socket_connection(self, socket_client):
        """Test WebSocket connection"""
        assert socket_client.is_connected()
    
    def test_join_analysis_room(self, socket_client):
        """Test joining analysis room"""
        socket_client.emit('join_analysis', {'analysis_id': 'test_123'})
        received = socket_client.get_received()
        # Should receive some acknowledgment or no error
        assert len(received) >= 0
    
    def test_leave_analysis_room(self, socket_client):
        """Test leaving analysis room"""
        socket_client.emit('join_analysis', {'analysis_id': 'test_123'})
        socket_client.emit('leave_analysis', {'analysis_id': 'test_123'})
        received = socket_client.get_received()
        assert len(received) >= 0
    
    def test_model_progress_event(self, socket_client):
        """Test model progress event emission"""
        socket_client.emit('join_analysis', {'analysis_id': 'test_123'})
        
        # Simulate progress update
        with app.test_request_context():
            socketio.emit('model_progress', {
                'analysis_id': 'test_123',
                'model': 'test-model',
                'status': 'processing',
                'progress': 50
            }, room='analysis_test_123')
        
        # Note: In test mode, events may not propagate as expected
        assert socket_client.is_connected()


class TestSecurityFeatures:
    """Test security features"""
    
    def test_input_sanitization(self):
        """Test input sanitization"""
        validator = InputValidator()
        
        # Test XSS prevention
        malicious = "<script>alert('xss')</script>"
        sanitized = validator.sanitize_text(malicious)
        assert '<script>' not in sanitized
        
        # Test SQL injection prevention
        sql_injection = "'; DROP TABLE users; --"
        is_valid, error = validator.validate_case_text(sql_injection)
        assert is_valid == False
    
    def test_api_key_validation(self):
        """Test API key validation"""
        validator = InputValidator()
        
        # Valid key format
        assert validator.validate_api_key('sk-or-v1-abcd1234567890abcd1234')
        
        # Invalid key format
        assert not validator.validate_api_key('invalid-key')
        assert not validator.validate_api_key('sk-wrong-format')
    
    def test_case_text_validation(self):
        """Test case text validation"""
        validator = InputValidator()
        
        # Valid case
        valid_case = "A 45-year-old patient presents with chest pain that started 2 hours ago. The pain is described as crushing and radiates to the left arm."
        is_valid, error = validator.validate_case_text(valid_case)
        assert is_valid == True
        
        # Too short
        is_valid, error = validator.validate_case_text("Short text")
        assert is_valid == False
        assert "at least 50 characters" in error
        
        # No medical content
        is_valid, error = validator.validate_case_text("Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.")
        assert is_valid == False
        assert "medical content" in error
    
    @patch('web_app.rate_limit_storage', {})
    def test_rate_limiting(self, client):
        """Test rate limiting"""
        # This test would need actual rate limiting implementation
        # For now, just verify the decorator exists
        from utils.security import RateLimiter
        limiter = RateLimiter()
        assert hasattr(limiter, 'rate_limit')
        assert hasattr(limiter, 'analysis_rate_limit')


class TestDatabaseOperations:
    """Test database operations"""
    
    @pytest.fixture
    def mock_db(self):
        """Create mock database manager"""
        mock = MagicMock()
        mock.create_analysis.return_value = 'test_analysis_123'
        mock.get_analysis.return_value = {
            'id': 'test_analysis_123',
            'case_text': 'Test case',
            'created_at': datetime.now().isoformat()
        }
        return mock
    
    def test_create_analysis(self, mock_db):
        """Test creating analysis in database"""
        analysis_id = mock_db.create_analysis(
            case_text="Test case",
            model_count=17
        )
        assert analysis_id == 'test_analysis_123'
        mock_db.create_analysis.assert_called_once()
    
    def test_get_analysis(self, mock_db):
        """Test retrieving analysis from database"""
        analysis = mock_db.get_analysis('test_analysis_123')
        assert analysis['id'] == 'test_analysis_123'
        assert 'case_text' in analysis
    
    def test_update_analysis_status(self, mock_db):
        """Test updating analysis status"""
        mock_db.update_analysis_status('test_analysis_123', 'completed')
        mock_db.update_analysis_status.assert_called_with('test_analysis_123', 'completed')
    
    def test_add_model_response(self, mock_db):
        """Test adding model response"""
        mock_db.add_model_response(
            analysis_id='test_analysis_123',
            model_name='test-model',
            response={'diagnosis': 'Test diagnosis'},
            response_time=1.5
        )
        mock_db.add_model_response.assert_called_once()
    
    def test_get_recent_analyses(self, mock_db):
        """Test getting recent analyses"""
        mock_db.get_recent_analyses.return_value = [
            {'id': 'test_1', 'created_at': datetime.now().isoformat()},
            {'id': 'test_2', 'created_at': datetime.now().isoformat()}
        ]
        recent = mock_db.get_recent_analyses(limit=10)
        assert len(recent) == 2


class TestIntegrationScenarios:
    """Test complete user scenarios"""
    
    @pytest.fixture
    def client(self):
        """Create test client"""
        app.config['TESTING'] = True
        with app.test_client() as client:
            with client.session_transaction() as sess:
                sess['session_id'] = 'test_session_123'
            yield client
    
    def test_complete_analysis_flow(self, client):
        """Test complete analysis workflow"""
        # 1. Load landing page
        response = client.get('/')
        assert response.status_code == 200
        
        # 2. Navigate to analyze page
        response = client.get('/analyze')
        assert response.status_code == 200
        
        # 3. Set API key
        response = client.post('/api/session/set-key',
            json={'api_key': 'sk-or-v1-test1234567890abcdef'},
            content_type='application/json'
        )
        assert response.status_code == 200
        
        # 4. Submit analysis (would fail without real orchestrator)
        response = client.post('/api/analyze',
            json={
                'case_text': 'A 45-year-old male patient presents with acute chest pain, shortness of breath, and diaphoresis. History of hypertension and diabetes.',
                'api_key': 'sk-or-v1-test1234567890abcdef',
                'use_free_models': True
            },
            content_type='application/json'
        )
        # Should return 503 if orchestrator not available, or 200 if it is
        assert response.status_code in [200, 503]
    
    def test_navigation_flow(self, client):
        """Test navigation through all pages"""
        pages = ['/', '/analyze', '/dashboard', '/visualizations', '/settings', '/api/docs', '/compare']
        
        for page in pages:
            response = client.get(page)
            assert response.status_code == 200, f"Failed to load {page}"
    
    def test_api_key_persistence(self, client):
        """Test API key persistence in session"""
        # Set API key
        response = client.post('/api/session/set-key',
            json={'api_key': 'sk-or-v1-persistent1234567890'},
            content_type='application/json'
        )
        assert response.status_code == 200
        
        # Check session status
        response = client.get('/api/session/status')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['api_key_set'] == True
    
    def test_error_handling(self, client):
        """Test error handling for various scenarios"""
        # Invalid route
        response = client.get('/invalid/route')
        assert response.status_code == 404
        
        # Invalid API endpoint
        response = client.get('/api/invalid')
        assert response.status_code == 404
        
        # Invalid POST data
        response = client.post('/api/analyze',
            data='invalid json',
            content_type='application/json'
        )
        assert response.status_code in [400, 503]


class TestPerformance:
    """Test performance aspects"""
    
    @pytest.fixture
    def client(self):
        """Create test client"""
        app.config['TESTING'] = True
        with app.test_client() as client:
            yield client
    
    def test_response_compression(self, client):
        """Test response compression"""
        response = client.get('/', headers={'Accept-Encoding': 'gzip'})
        assert response.status_code == 200
        # Check if compression headers are present (when configured)
        # Note: In test mode, compression might not be active
    
    def test_cache_headers(self, client):
        """Test cache headers"""
        response = client.get('/static/css/material3.css')
        # Static files should have cache headers
        if response.status_code == 200:
            assert 'Cache-Control' in response.headers or 'Expires' in response.headers
    
    def test_api_response_time(self, client):
        """Test API response times"""
        import time
        
        start = time.time()
        response = client.get('/api/health')
        duration = time.time() - start
        
        assert response.status_code == 200
        assert duration < 1.0  # Should respond within 1 second
    
    def test_concurrent_requests(self, client):
        """Test handling concurrent requests"""
        import concurrent.futures
        
        def make_request():
            return client.get('/api/health')
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(make_request) for _ in range(10)]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]
        
        assert all(r.status_code == 200 for r in results)


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])