"""
Updated Model List for MEDLEY - August 2025
Total: 34 models (10 free + 24 paid)
"""

# FREE MODELS (10)
FREE_MODELS = [
    "deepseek/deepseek-r1:free",
    "deepseek/deepseek-chat:free", 
    "meta-llama/llama-3.1-70b-instruct:free",
    "google/gemma-3-27b-it:free",
    "qwen/qwen-2.5-72b-instruct:free",
    "nvidia/llama-3.1-nemotron-70b-instruct:free",
    "mistralai/mistral-7b-instruct:free",
    "openai/gpt-oss-20b:free",
    "google/gemma-3-4b-it:free",
    "meta-llama/llama-3.2-3b-instruct:free"
]

# PAID MODELS (24)
PAID_MODELS = [
    "anthropic/claude-sonnet-4",
    "openai/gpt-4o",
    "anthropic/claude-3.7-sonnet",
    "anthropic/claude-3.5-sonnet-20241022",
    "anthropic/claude-3-opus-20240229",
    "google/gemini-2.5-pro",
    "deepseek/deepseek-r1",
    "deepseek/deepseek-chat",
    "openai/gpt-4o-mini",
    "anthropic/claude-3-haiku-20240307",
    "google/gemini-2.5-flash",
    "openai/gpt-4-turbo",
    "meta-llama/llama-3.1-70b-instruct",
    "google/gemini-2.5-flash-lite",
    "qwen/qwen-2.5-coder-32b-instruct",
    "mistralai/mistral-large-2411",
    "anthropic/claude-3.5-haiku-20241022",
    "x-ai/grok-4",
    "cohere/command-r-plus",
    "x-ai/grok-2-1212",
    "openrouter/horizon-beta",
    "perplexity/llama-3.1-sonar-large-128k-online",
    "ai21/jamba-1.5-large",
    "microsoft/wizardlm-2-8x22b"
]

# ALL MODELS
ALL_MODELS = FREE_MODELS + PAID_MODELS

# Model metadata for comprehensive analysis
MODEL_METADATA = {
    # Free Models
    "deepseek/deepseek-r1:free": {
        "provider": "DeepSeek",
        "origin_country": "China",
        "architecture": "DeepSeek-R1",
        "type": "free"
    },
    "deepseek/deepseek-chat:free": {
        "provider": "DeepSeek", 
        "origin_country": "China",
        "architecture": "DeepSeek",
        "type": "free"
    },
    "meta-llama/llama-3.1-70b-instruct:free": {
        "provider": "Meta",
        "origin_country": "USA",
        "architecture": "Llama-3.1",
        "type": "free"
    },
    "google/gemma-3-27b-it:free": {
        "provider": "Google",
        "origin_country": "USA",
        "architecture": "Gemma-3",
        "type": "free"
    },
    "qwen/qwen-2.5-72b-instruct:free": {
        "provider": "Alibaba",
        "origin_country": "China",
        "architecture": "Qwen-2.5",
        "type": "free"
    },
    "nvidia/llama-3.1-nemotron-70b-instruct:free": {
        "provider": "NVIDIA",
        "origin_country": "USA",
        "architecture": "Nemotron",
        "type": "free"
    },
    "mistralai/mistral-7b-instruct:free": {
        "provider": "Mistral AI",
        "origin_country": "France",
        "architecture": "Mistral",
        "type": "free"
    },
    "openai/gpt-oss-20b:free": {
        "provider": "OpenAI",
        "origin_country": "USA",
        "architecture": "GPT-OSS",
        "type": "free"
    },
    "google/gemma-3-4b-it:free": {
        "provider": "Google",
        "origin_country": "USA",
        "architecture": "Gemma-3",
        "type": "free"
    },
    "meta-llama/llama-3.2-3b-instruct:free": {
        "provider": "Meta",
        "origin_country": "USA",
        "architecture": "Llama-3.2",
        "type": "free"
    },
    
    # Paid Models
    "anthropic/claude-sonnet-4": {
        "provider": "Anthropic",
        "origin_country": "USA",
        "architecture": "Claude-4",
        "type": "paid"
    },
    "openai/gpt-4o": {
        "provider": "OpenAI",
        "origin_country": "USA",
        "architecture": "GPT-4",
        "type": "paid"
    },
    "anthropic/claude-3.7-sonnet": {
        "provider": "Anthropic",
        "origin_country": "USA",
        "architecture": "Claude-3.7",
        "type": "paid"
    },
    "anthropic/claude-3.5-sonnet-20241022": {
        "provider": "Anthropic",
        "origin_country": "USA",
        "architecture": "Claude-3.5",
        "type": "paid"
    },
    "anthropic/claude-3-opus-20240229": {
        "provider": "Anthropic",
        "origin_country": "USA",
        "architecture": "Claude-3",
        "type": "paid"
    },
    "google/gemini-2.5-pro": {
        "provider": "Google",
        "origin_country": "USA",
        "architecture": "Gemini-2.5",
        "type": "paid"
    },
    "deepseek/deepseek-r1": {
        "provider": "DeepSeek",
        "origin_country": "China",
        "architecture": "DeepSeek-R1",
        "type": "paid"
    },
    "deepseek/deepseek-chat": {
        "provider": "DeepSeek",
        "origin_country": "China",
        "architecture": "DeepSeek",
        "type": "paid"
    },
    "openai/gpt-4o-mini": {
        "provider": "OpenAI",
        "origin_country": "USA",
        "architecture": "GPT-4",
        "type": "paid"
    },
    "anthropic/claude-3-haiku-20240307": {
        "provider": "Anthropic",
        "origin_country": "USA",
        "architecture": "Claude-3",
        "type": "paid"
    },
    "google/gemini-2.5-flash": {
        "provider": "Google",
        "origin_country": "USA",
        "architecture": "Gemini-2.5",
        "type": "paid"
    },
    "openai/gpt-4-turbo": {
        "provider": "OpenAI",
        "origin_country": "USA",
        "architecture": "GPT-4",
        "type": "paid"
    },
    "meta-llama/llama-3.1-70b-instruct": {
        "provider": "Meta",
        "origin_country": "USA",
        "architecture": "Llama-3.1",
        "type": "paid"
    },
    "google/gemini-2.5-flash-lite": {
        "provider": "Google",
        "origin_country": "USA",
        "architecture": "Gemini-2.5",
        "type": "paid"
    },
    "qwen/qwen-2.5-coder-32b-instruct": {
        "provider": "Alibaba",
        "origin_country": "China",
        "architecture": "Qwen-2.5",
        "type": "paid"
    },
    "mistralai/mistral-large-2411": {
        "provider": "Mistral AI",
        "origin_country": "France",
        "architecture": "Mistral",
        "type": "paid"
    },
    "anthropic/claude-3.5-haiku-20241022": {
        "provider": "Anthropic",
        "origin_country": "USA",
        "architecture": "Claude-3.5",
        "type": "paid"
    },
    "x-ai/grok-4": {
        "provider": "xAI",
        "origin_country": "USA",
        "architecture": "Grok",
        "type": "paid"
    },
    "cohere/command-r-plus": {
        "provider": "Cohere",
        "origin_country": "Canada",
        "architecture": "Command-R",
        "type": "paid"
    },
    "x-ai/grok-2-1212": {
        "provider": "xAI",
        "origin_country": "USA",
        "architecture": "Grok",
        "type": "paid"
    },
    "openrouter/horizon-beta": {
        "provider": "OpenRouter",
        "origin_country": "USA",
        "architecture": "Unknown",
        "type": "paid"
    },
    "perplexity/llama-3.1-sonar-large-128k-online": {
        "provider": "Perplexity",
        "origin_country": "USA",
        "architecture": "Sonar",
        "type": "paid"
    },
    "ai21/jamba-1.5-large": {
        "provider": "AI21 Labs",
        "origin_country": "Israel",
        "architecture": "Jamba",
        "type": "paid"
    },
    "microsoft/wizardlm-2-8x22b": {
        "provider": "Microsoft",
        "origin_country": "USA",
        "architecture": "WizardLM",
        "type": "paid"
    }
}

def get_model_list(use_free_only=False):
    """Get list of models to use"""
    if use_free_only:
        return FREE_MODELS
    return ALL_MODELS

def get_geographical_distribution():
    """Get geographical distribution of models"""
    distribution = {}
    for model, metadata in MODEL_METADATA.items():
        country = metadata.get('origin_country', 'Unknown')
        if country not in distribution:
            distribution[country] = []
        distribution[country].append(model)
    return distribution

def get_orchestrator_models(use_free_only=False):
    """Get best orchestrator models"""
    if use_free_only:
        return [
            "openai/gpt-oss-20b:free",  # Best free orchestrator
            "qwen/qwen-2.5-72b-instruct:free",  # Backup
            "google/gemma-3-27b-it:free"  # Third choice
        ]
    else:
        return [
            "anthropic/claude-3-opus-20240229",  # Best overall
            "anthropic/claude-3.5-sonnet-20241022",  # Second best
            "openai/gpt-4o",  # Third choice
            "google/gemini-2.5-pro"  # Fourth choice
        ]

# Statistics
def print_statistics():
    """Print model statistics"""
    geo_dist = get_geographical_distribution()
    
    print(f"Total Models: {len(ALL_MODELS)}")
    print(f"  - Free: {len(FREE_MODELS)}")
    print(f"  - Paid: {len(PAID_MODELS)}")
    print("\nGeographical Distribution:")
    for country, models in sorted(geo_dist.items(), key=lambda x: len(x[1]), reverse=True):
        print(f"  {country}: {len(models)} models ({len(models)/len(ALL_MODELS)*100:.1f}%)")
    
    print("\nProviders:")
    providers = {}
    for metadata in MODEL_METADATA.values():
        provider = metadata.get('provider', 'Unknown')
        providers[provider] = providers.get(provider, 0) + 1
    
    for provider, count in sorted(providers.items(), key=lambda x: x[1], reverse=True):
        print(f"  {provider}: {count} models")

if __name__ == "__main__":
    print_statistics()