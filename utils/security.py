#!/usr/bin/env python
"""
Security utilities for MEDLEY Web Application
Input validation, sanitization, and rate limiting
"""

import re
import html
import time
from functools import wraps
from typing import Dict, Any, Optional
from flask import request, jsonify, session
from datetime import datetime, timedelta
import hashlib

# Rate limiting storage (in production, use Redis)
rate_limit_storage = {}

class InputValidator:
    """Validate and sanitize user inputs"""
    
    @staticmethod
    def sanitize_text(text: str, max_length: int = 10000) -> str:
        """
        Sanitize text input
        
        Args:
            text: Input text
            max_length: Maximum allowed length
            
        Returns:
            Sanitized text
        """
        if not text:
            return ""
        
        # Truncate to max length
        text = text[:max_length]
        
        # HTML escape
        text = html.escape(text)
        
        # Remove control characters except newlines and tabs
        text = re.sub(r'[\x00-\x08\x0B-\x0C\x0E-\x1F\x7F]', '', text)
        
        # Remove excessive whitespace
        text = re.sub(r'\n{3,}', '\n\n', text)
        text = re.sub(r' {3,}', '  ', text)
        
        return text.strip()
    
    @staticmethod
    def validate_case_text(case_text: str) -> tuple[bool, str]:
        """
        Validate medical case text
        
        Args:
            case_text: Case description
            
        Returns:
            (is_valid, error_message)
        """
        # Check if empty
        if not case_text or not case_text.strip():
            return False, "Case text cannot be empty"
        
        # Check minimum length
        if len(case_text.strip()) < 50:
            return False, "Case description must be at least 50 characters"
        
        # Check maximum length
        if len(case_text) > 10000:
            return False, "Case description cannot exceed 10,000 characters"
        
        # Check for potential injection attempts
        suspicious_patterns = [
            r'<script',
            r'javascript:',
            r'on\w+\s*=',  # Event handlers
            r'data:text/html',
            r'vbscript:',
            r'<iframe',
            r'<embed',
            r'<object',
            r'DROP\s+TABLE',
            r'DELETE\s+FROM',
            r'INSERT\s+INTO',
            r'UPDATE\s+.*\s+SET'
        ]
        
        case_lower = case_text.lower()
        for pattern in suspicious_patterns:
            if re.search(pattern, case_lower, re.IGNORECASE):
                return False, "Invalid content detected"
        
        # Check for minimum medical content (at least some medical terms expected)
        medical_terms = [
            'patient', 'year', 'old', 'presents', 'pain', 'fever', 'history',
            'examination', 'diagnosis', 'treatment', 'symptom', 'condition',
            'medical', 'clinical', 'disease', 'disorder', 'syndrome'
        ]
        
        has_medical_content = any(term in case_lower for term in medical_terms)
        if not has_medical_content:
            return False, "Case text must contain medical content"
        
        return True, ""
    
    @staticmethod
    def validate_api_key(api_key: str) -> bool:
        """
        Validate OpenRouter API key format
        
        Args:
            api_key: API key to validate
            
        Returns:
            True if valid format
        """
        if not api_key:
            return True  # Optional, so empty is valid
        
        # OpenRouter keys typically start with 'sk-or-'
        if not re.match(r'^sk-or-[a-zA-Z0-9-]{20,}$', api_key):
            return False
        
        return True
    
    @staticmethod
    def validate_model_selection(models: list) -> tuple[bool, str]:
        """
        Validate model selection
        
        Args:
            models: List of model IDs
            
        Returns:
            (is_valid, error_message)
        """
        if not models:
            return True, ""  # Empty selection is valid (uses defaults)
        
        if not isinstance(models, list):
            return False, "Models must be a list"
        
        if len(models) > 50:
            return False, "Cannot select more than 50 models"
        
        # Validate each model ID format
        valid_pattern = re.compile(r'^[a-zA-Z0-9-_/:.]+$')
        for model in models:
            if not isinstance(model, str):
                return False, "Each model must be a string"
            if not valid_pattern.match(model):
                return False, f"Invalid model ID: {model}"
            if len(model) > 100:
                return False, f"Model ID too long: {model}"
        
        return True, ""


class RateLimiter:
    """Rate limiting for API endpoints"""
    
    @staticmethod
    def get_client_id(request) -> str:
        """Get unique client identifier"""
        # Use session ID if available
        if 'session_id' in session:
            return f"session:{session['session_id']}"
        
        # Fall back to IP address
        ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)
        if ',' in ip:
            ip = ip.split(',')[0].strip()
        
        return f"ip:{ip}"
    
    @staticmethod
    def rate_limit(
        max_requests: int = 100,
        window_seconds: int = 3600,
        key_prefix: str = "api"
    ):
        """
        Rate limiting decorator
        
        Args:
            max_requests: Maximum requests allowed
            window_seconds: Time window in seconds
            key_prefix: Prefix for rate limit key
        """
        def decorator(f):
            @wraps(f)
            def wrapped(*args, **kwargs):
                # Get client ID
                client_id = RateLimiter.get_client_id(request)
                rate_key = f"{key_prefix}:{client_id}"
                
                # Get current time
                now = time.time()
                
                # Clean old entries
                if rate_key in rate_limit_storage:
                    rate_limit_storage[rate_key] = [
                        t for t in rate_limit_storage[rate_key]
                        if now - t < window_seconds
                    ]
                else:
                    rate_limit_storage[rate_key] = []
                
                # Check rate limit
                request_count = len(rate_limit_storage[rate_key])
                
                if request_count >= max_requests:
                    # Calculate retry time
                    oldest_request = min(rate_limit_storage[rate_key])
                    retry_after = int(window_seconds - (now - oldest_request))
                    
                    response = jsonify({
                        'error': 'Rate limit exceeded',
                        'retry_after': retry_after,
                        'limit': max_requests,
                        'window': window_seconds
                    })
                    response.status_code = 429
                    response.headers['Retry-After'] = str(retry_after)
                    return response
                
                # Record this request
                rate_limit_storage[rate_key].append(now)
                
                # Call original function
                return f(*args, **kwargs)
            
            return wrapped
        return decorator
    
    @staticmethod
    def analysis_rate_limit():
        """Special rate limit for analysis endpoints"""
        # More restrictive for analysis (expensive operation)
        return RateLimiter.rate_limit(
            max_requests=10,  # 10 analyses per hour
            window_seconds=3600,
            key_prefix="analysis"
        )
    
    @staticmethod
    def api_rate_limit():
        """Standard API rate limit"""
        return RateLimiter.rate_limit(
            max_requests=100,  # 100 requests per hour
            window_seconds=3600,
            key_prefix="api"
        )


class SecurityHeaders:
    """Security headers for responses"""
    
    @staticmethod
    def add_security_headers(response):
        """Add security and performance headers to response"""
        from flask import request
        
        # Content Security Policy
        response.headers['Content-Security-Policy'] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://cdn.socket.io; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
            "font-src 'self' https://fonts.gstatic.com; "
            "img-src 'self' data: https:; "
            "connect-src 'self' ws: wss:;"
        )
        
        # Security headers
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'SAMEORIGIN'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        
        # HSTS (only in production with HTTPS)
        if not request.url.startswith('http://localhost'):
            response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        
        # Performance headers - Cache Control based on content type
        
        if request.path.startswith('/static/') or request.path.endswith(('.css', '.js', '.png', '.jpg', '.ico', '.svg', '.woff2')):
            # Static assets - long cache
            response.headers['Cache-Control'] = 'public, max-age=31536000, immutable'  # 1 year
            response.headers['Expires'] = 'Thu, 31 Dec 2025 23:59:59 GMT'
        elif request.path.startswith('/api/'):
            # API responses - short cache
            response.headers['Cache-Control'] = 'public, max-age=300, stale-while-revalidate=60'  # 5 minutes
        elif request.path.endswith('.html') or request.path == '/' or not '.' in request.path.split('/')[-1]:
            # HTML pages - moderate cache
            response.headers['Cache-Control'] = 'public, max-age=300, must-revalidate'  # 5 minutes
            
        # ETag for better caching (only for HTML pages, not static files)
        if not request.path.startswith('/api/') and not request.path.startswith('/static/') and response.status_code == 200:
            import hashlib
            try:
                if response.data:
                    etag = hashlib.md5(response.data).hexdigest()[:16]
                    response.headers['ETag'] = f'"{etag}"'
            except:
                pass  # Skip ETag for file responses
        
        return response


class SessionSecurity:
    """Session security utilities"""
    
    @staticmethod
    def generate_session_id() -> str:
        """Generate secure session ID"""
        # Combine timestamp, random data, and user agent
        data = f"{time.time()}:{request.headers.get('User-Agent', '')}:{os.urandom(32).hex()}"
        return hashlib.sha256(data.encode()).hexdigest()
    
    @staticmethod
    def validate_session() -> bool:
        """Validate current session"""
        if 'session_id' not in session:
            return False
        
        # Check session age
        if 'session_created' in session:
            created = datetime.fromisoformat(session['session_created'])
            if datetime.now() - created > timedelta(hours=24):
                return False
        
        return True
    
    @staticmethod
    def rotate_session():
        """Rotate session ID for security"""
        old_data = dict(session)
        session.clear()
        session['session_id'] = SessionSecurity.generate_session_id()
        session['session_created'] = datetime.now().isoformat()
        
        # Restore non-sensitive data
        for key in ['api_key_set', 'recent_analyses']:
            if key in old_data:
                session[key] = old_data[key]


# Export utilities
__all__ = [
    'InputValidator',
    'RateLimiter',
    'SecurityHeaders',
    'SessionSecurity'
]