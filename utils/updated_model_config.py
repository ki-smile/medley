#!/usr/bin/env python
"""
Updated Model Configuration with Corrected IDs and Retry Logic
Based on analysis of failed models across all 11 cases
"""

from typing import Dict, List, Optional

def get_updated_model_list() -> List[Dict]:
    """
    Returns updated list of models with corrected IDs and retry settings.
    Removes deprecated models and adds alternatives where available.
    """
    
    models = [
        # OpenAI Models
        {"id": "openai/gpt-4o", "name": "GPT-4o", "country": "USA", "retry_empty": True},
        {"id": "openai/gpt-4o-mini", "name": "GPT-4o Mini", "country": "USA", "retry_empty": True},
        # GPT-5 requires special configuration - marking as optional
        {"id": "openai/gpt-5-chat", "name": "GPT-5 Chat", "country": "USA", "optional": True, "retry_empty": True},
        {"id": "openai/gpt-oss-120b", "name": "GPT OSS 120B", "country": "USA", "retry_empty": True},
        
        # Anthropic Models - Updated IDs
        {"id": "anthropic/claude-3-opus-20240229", "name": "Claude 3 Opus", "country": "USA", "retry_empty": True},
        {"id": "anthropic/claude-3-5-sonnet-20241022", "name": "Claude 3.5 Sonnet", "country": "USA", "retry_empty": True},  # Updated ID
        {"id": "anthropic/claude-3-5-haiku-20241022", "name": "Claude 3.5 Haiku", "country": "USA", "retry_empty": True},  # Updated ID
        
        # Google Models - Special handling for Gemini 2.5 Pro
        {"id": "google/gemini-2.5-pro", "name": "Gemini 2.5 Pro", "country": "USA", 
         "retry_empty": True, "max_retries": 3, "retry_delay": 5},  # Special retry for empty responses
        {"id": "google/gemini-2.5-flash", "name": "Gemini 2.5 Flash", "country": "USA", "retry_empty": True},
        {"id": "google/gemini-2.5-flash-lite", "name": "Gemini 2.5 Flash Lite", "country": "USA", 
         "retry_empty": True, "max_retries": 3, "retry_delay": 3},  # Lightweight model with retry
        {"id": "google/gemini-2.0-flash-exp:free", "name": "Gemini 2.0 Flash Exp", "country": "USA", "optional": True},  # Free tier
        {"id": "google/gemma-2-9b-it", "name": "Gemma 2 9B", "country": "USA", "retry_empty": True},
        {"id": "google/gemma-2-9b-it:free", "name": "Gemma 2 9B Free", "country": "USA", "optional": True},
        
        # Meta Models
        {"id": "meta-llama/llama-3.2-3b-instruct", "name": "Llama 3.2 3B", "country": "USA", "retry_empty": True},
        {"id": "meta-llama/llama-3.2-3b-instruct:free", "name": "Llama 3.2 3B Free", "country": "USA", "optional": True},
        
        # Mistral Models - Updated IDs
        {"id": "mistralai/mistral-large-2411", "name": "Mistral Large", "country": "France", "retry_empty": True},
        {"id": "mistralai/mistral-small-2409", "name": "Mistral Small", "country": "France", "retry_empty": True},  # Updated ID
        {"id": "mistralai/mistral-7b-instruct", "name": "Mistral 7B", "country": "France", "retry_empty": True},
        {"id": "mistralai/mistral-7b-instruct:free", "name": "Mistral 7B Free", "country": "France", "optional": True},
        
        # DeepSeek Models (China)
        {"id": "deepseek/deepseek-chat", "name": "DeepSeek Chat", "country": "China", "retry_empty": True},
        {"id": "deepseek/deepseek-r1", "name": "DeepSeek R1", "country": "China", "retry_empty": True},
        {"id": "deepseek/deepseek-chat-v3-0324", "name": "DeepSeek v3", "country": "China", "retry_empty": True},
        {"id": "deepseek/deepseek-chat-v3-0324:free", "name": "DeepSeek v3 Free", "country": "China", "optional": True},
        
        # 01-ai Models - Updated ID
        {"id": "01-ai/yi-lightning", "name": "Yi Lightning", "country": "China", "retry_empty": True},  # Alternative to yi-large
        
        # Qwen Models (China)
        {"id": "qwen/qwen-2.5-coder-32b-instruct", "name": "Qwen 2.5 Coder", "country": "China", "retry_empty": True},
        
        # Cohere Models (Canada)
        {"id": "cohere/command-r-plus", "name": "Command R+", "country": "Canada", "retry_empty": True},
        {"id": "cohere/command-r", "name": "Command R", "country": "Canada", "retry_empty": True},
        
        # AI21 Models (Israel)
        {"id": "ai21/jamba-large-1.7", "name": "Jamba Large", "country": "Israel", "retry_empty": True},
        
        # Perplexity Models - Updated IDs
        {"id": "perplexity/sonar-deep-research", "name": "Sonar Deep Research", "country": "USA", "retry_empty": True},
        {"id": "perplexity/llama-3.1-sonar-small-128k-chat", "name": "Sonar Small Chat", "country": "USA", "retry_empty": True},  # Alternative
        
        # Microsoft Models
        {"id": "microsoft/wizardlm-2-8x22b", "name": "WizardLM 2", "country": "USA", "retry_empty": True},
        
        # X.AI Models
        {"id": "x-ai/grok-2-1212", "name": "Grok 2", "country": "USA", "retry_empty": True},
        {"id": "x-ai/grok-4", "name": "Grok 4", "country": "USA", "retry_empty": True},
        
        # Liquid Models
        {"id": "liquid/lfm-40b", "name": "LFM 40B", "country": "USA", "retry_empty": True},
        {"id": "liquid/lfm-40b:free", "name": "LFM 40B Free", "country": "USA", "optional": True},
        
        # NousResearch - Updated ID
        {"id": "nousresearch/hermes-3-llama-3.1-8b:free", "name": "Hermes 3", "country": "USA", "optional": True},  # Free tier only
        
        # Shisa AI - Requires privacy settings
        {"id": "shisa-ai/shisa-v2-llama3.3-70b:free", "name": "Shisa v2", "country": "Japan/USA", 
         "optional": True, "requires_privacy_setting": True},
    ]
    
    return models


def get_retry_config() -> Dict:
    """
    Returns retry configuration for handling empty/failed responses.
    """
    return {
        "empty_response_retry": {
            "enabled": True,
            "max_attempts": 2,  # Quick retries, not blocking
            "delay_seconds": 3,
            "models_with_special_handling": {
                "google/gemini-2.5-pro": {
                    "max_attempts": 3,
                    "delay_seconds": 5,
                    "add_prompt_prefix": "Please provide a detailed medical analysis: "
                }
            }
        },
        "failed_response_retry": {
            "enabled": True,
            "retry_on_codes": [429, 500, 502, 503, 504],  # Rate limit and server errors
            "max_attempts": 1,
            "delay_seconds": 10
        },
        "cache_validation": {
            "check_empty_content": True,
            "min_response_length": 50,  # Minimum characters for valid response
            "revalidate_on_rerun": True  # Check cached responses on pipeline rerun
        }
    }


def should_retry_model(model_id: str, cached_response: Optional[Dict]) -> bool:
    """
    Determines if a model should be retried based on cached response.
    
    Args:
        model_id: The model identifier
        cached_response: The cached response dictionary (if exists)
        
    Returns:
        True if model should be retried, False otherwise
    """
    if cached_response is None:
        return True  # No cache, should query
    
    # Check for empty content
    content = cached_response.get('content', '')
    if not content or len(content.strip()) < 50:
        return True  # Empty or too short, retry
    
    # Check for error field
    if cached_response.get('error'):
        error_code = cached_response.get('error_code', 0)
        # Retry on temporary errors
        if error_code in [429, 500, 502, 503, 504]:
            return True
    
    return False  # Valid cached response


def get_alternative_model_mapping() -> Dict[str, str]:
    """
    Maps deprecated/failed model IDs to their alternatives.
    """
    return {
        "anthropic/claude-3-sonnet-20240229": "anthropic/claude-3-5-sonnet-20241022",
        "anthropic/claude-3-haiku-20240307": "anthropic/claude-3-5-haiku-20241022",
        "mistralai/mistral-small-2402": "mistralai/mistral-small-2409",
        "01-ai/yi-large": "01-ai/yi-lightning",
        "perplexity/llama-3.1-sonar-small-128k-online": "perplexity/llama-3.1-sonar-small-128k-chat",
        "google/gemini-2.0-flash-exp": "google/gemini-2.0-flash-exp:free",
        "nousresearch/hermes-3-llama-3.1-8b": "nousresearch/hermes-3-llama-3.1-8b:free"
    }


if __name__ == "__main__":
    # Test the configuration
    models = get_updated_model_list()
    print(f"Total models configured: {len(models)}")
    
    # Count by country
    countries = {}
    for model in models:
        country = model.get('country', 'Unknown')
        countries[country] = countries.get(country, 0) + 1
    
    print("\nModels by country:")
    for country, count in sorted(countries.items()):
        print(f"  {country}: {count}")
    
    # Show models with special retry settings
    print("\nModels with special retry settings:")
    for model in models:
        if model.get('max_retries') or model.get('requires_privacy_setting'):
            print(f"  {model['id']}: {model.get('name')}")