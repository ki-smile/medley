"""
Validators for response validation
"""

from typing import Dict, Any, Optional

class ResponseValidator:
    """Validates LLM responses for completeness and quality"""
    
    @staticmethod
    def validate_response(response: Dict[str, Any]) -> bool:
        """Basic validation of response structure"""
        required_fields = ["content", "model_name"]
        return all(field in response for field in required_fields)
    
    @staticmethod
    def validate_medical_response(response: str) -> bool:
        """Validate that response contains medical analysis"""
        # Basic check for medical content
        medical_indicators = [
            "diagnosis", "patient", "symptoms", "treatment",
            "examination", "history", "clinical"
        ]
        response_lower = response.lower()
        return any(indicator in response_lower for indicator in medical_indicators)