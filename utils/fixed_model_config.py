#!/usr/bin/env python
"""
Fixed Model Configuration - Working Models Only
Removes models that require special API keys or have no endpoints
"""

def get_working_models():
    """
    Returns list of models that are confirmed to work with standard OpenRouter API
    Excludes:
    - openai/gpt-5 (requires separate key)
    - Models with 404 errors (no endpoints)
    - Models with invalid IDs
    """
    
    return [
        # OpenAI Models (working)
        "openai/gpt-4o",
        "openai/gpt-4o-mini",
        "openai/gpt-4-turbo",
        "openai/gpt-oss-120b",
        "openai/gpt-oss-20b/free",
        
        # Anthropic Models (working)
        "anthropic/claude-3-opus-20240229",
        "anthropic/claude-3.5-sonnet-20241022",
        "anthropic/claude-3.5-haiku-20241022",
        "anthropic/claude-3.7-sonnet",
        "anthropic/claude-sonnet-4",
        
        # Google Models (working)
        "google/gemini-2.5-pro",
        "google/gemini-2.5-flash",
        "google/gemini-2.5-flash-lite",
        "google/gemma-2-9b-it",
        "google/gemma-3-27b-it",
        "google/gemma-3-4b-it/free",
        
        # Meta Models (working)
        "meta-llama/llama-3.2-3b-instruct",
        
        # Mistral Models (working)
        "mistralai/mistral-large-2411",
        "mistralai/mistral-7b-instruct",
        "mistralai/mistral-7b-instruct/free",
        
        # DeepSeek Models (working)
        "deepseek/deepseek-chat",
        "deepseek/deepseek-r1",
        
        # Qwen Models (working)
        "qwen/qwen-2.5-coder-32b-instruct",
        "qwen/qwen-2.5-72b-instruct/free",
        
        # Cohere Models (working)
        "cohere/command-r-plus",
        "cohere/command-r",
        
        # xAI Models (working)
        "x-ai/grok-4",
        "x-ai/grok-2-1212",
        
        # Other Models (working)
        "microsoft/wizardlm-2-8x22b",
        "perplexity/sonar-deep-research",
        "ai21/jamba-large-1.7",
        "liquid/lfm-40b",
    ]

def get_excluded_models():
    """
    Returns list of models that are excluded due to errors
    """
    return {
        "openai/gpt-5": "Requires separate API key",
        "anthropic/claude-3-sonnet-20240229": "No endpoints found (404)",
        "anthropic/claude-3-haiku-20240307": "Invalid model ID",
        "google/gemini-2.0-flash-exp": "No endpoints found (404)",
        "mistralai/mistral-small-2402": "Invalid model ID",
        "01-ai/yi-large": "No endpoints found (404)",
        "shisa-ai/shisa-v2-llama3.3-70b": "Data policy issue",
        "nousresearch/hermes-3-llama-3.1-8b": "Invalid model ID",
        "perplexity/llama-3.1-sonar-small-128k-online": "No endpoints found (404)",
    }