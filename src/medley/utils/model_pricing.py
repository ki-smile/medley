"""
Model Pricing Configuration for OpenRouter API
Prices are in USD per 1M tokens as of August 2025
"""

from typing import Dict, Tuple

def get_model_pricing() -> Dict[str, Tuple[float, float]]:
    """
    Get model pricing per 1M tokens (input_cost, output_cost)
    Prices from OpenRouter API documentation
    """
    
    pricing = {
        # OpenAI Models
        "openai/gpt-4o": (5.00, 15.00),  # GPT-4o
        "openai/gpt-4o-mini": (0.15, 0.60),  # GPT-4o mini
        "openai/gpt-5": (10.00, 30.00),  # GPT-5 (estimated)
        "openai/gpt-5-chat": (10.00, 30.00),  # GPT-5 Chat
        "openai/gpt-oss-120b": (1.00, 3.00),  # Open source variant
        
        # Anthropic Models  
        "anthropic/claude-3-opus-20240229": (15.00, 75.00),  # Claude 3 Opus
        "anthropic/claude-3-5-sonnet-20241022": (3.00, 15.00),  # Claude 3.5 Sonnet
        "anthropic/claude-3-sonnet-20240229": (3.00, 15.00),  # Claude 3 Sonnet
        "anthropic/claude-3-5-haiku-20241022": (0.25, 1.25),  # Claude 3.5 Haiku
        "anthropic/claude-3-haiku-20240307": (0.25, 1.25),  # Claude 3 Haiku
        
        # Google Models
        "google/gemini-2.5-pro": (3.50, 10.50),  # Gemini 2.5 Pro
        "google/gemini-2.5-flash": (0.075, 0.30),  # Gemini 2.5 Flash
        "google/gemini-2.5-flash-lite": (0.01, 0.04),  # Gemini 2.5 Flash Lite
        "google/gemini-2.0-flash-exp": (0.00, 0.00),  # Free experimental
        "google/gemini-2.0-flash-exp:free": (0.00, 0.00),  # Free tier
        "google/gemma-2-9b-it": (0.20, 0.20),  # Gemma 2 9B
        "google/gemma-2-9b-it:free": (0.00, 0.00),  # Free tier
        
        # Meta Models
        "meta-llama/llama-3.2-3b-instruct": (0.06, 0.06),  # Llama 3.2 3B
        "meta-llama/llama-3.2-3b-instruct:free": (0.00, 0.00),  # Free tier
        
        # Mistral Models
        "mistralai/mistral-large-2411": (3.00, 9.00),  # Mistral Large
        "mistralai/mistral-small-2409": (0.20, 0.60),  # Mistral Small
        "mistralai/mistral-small-2402": (0.20, 0.60),  # Mistral Small (old)
        "mistralai/mistral-7b-instruct": (0.07, 0.07),  # Mistral 7B
        "mistralai/mistral-7b-instruct:free": (0.00, 0.00),  # Free tier
        
        # DeepSeek Models (Chinese)
        "deepseek/deepseek-chat": (0.14, 0.28),  # DeepSeek Chat
        "deepseek/deepseek-r1": (0.14, 0.28),  # DeepSeek R1
        "deepseek/deepseek-chat-v3-0324": (0.14, 0.28),  # DeepSeek v3
        "deepseek/deepseek-chat-v3-0324:free": (0.00, 0.00),  # Free tier
        
        # Other Chinese Models
        "01-ai/yi-large": (3.00, 3.00),  # Yi Large
        "01-ai/yi-lightning": (0.30, 0.30),  # Yi Lightning
        "qwen/qwen-2.5-coder-32b-instruct": (0.50, 0.50),  # Qwen Coder
        
        # Cohere Models (Canadian)
        "cohere/command-r-plus": (3.00, 15.00),  # Command R+
        "cohere/command-r": (0.50, 1.50),  # Command R
        
        # AI21 Models (Israeli)
        "ai21/jamba-large-1.7": (2.00, 8.00),  # Jamba Large
        
        # Perplexity Models
        "perplexity/sonar-deep-research": (5.00, 5.00),  # Sonar Deep Research
        "perplexity/llama-3.1-sonar-small-128k-online": (0.20, 0.20),  # Sonar Small
        "perplexity/llama-3.1-sonar-small-128k-chat": (0.20, 0.20),  # Sonar Chat
        
        # Microsoft Models
        "microsoft/wizardlm-2-8x22b": (0.65, 0.65),  # WizardLM 2
        
        # X.AI Models
        "x-ai/grok-2-1212": (2.00, 10.00),  # Grok 2
        "x-ai/grok-4": (5.00, 15.00),  # Grok 4
        
        # Liquid Models
        "liquid/lfm-40b": (0.50, 0.50),  # LFM 40B
        "liquid/lfm-40b:free": (0.00, 0.00),  # Free tier
        
        # NousResearch
        "nousresearch/hermes-3-llama-3.1-8b": (0.13, 0.13),  # Hermes 3
        "nousresearch/hermes-3-llama-3.1-8b:free": (0.00, 0.00),  # Free tier
        
        # Shisa AI
        "shisa-ai/shisa-v2-llama3.3-70b": (0.70, 0.70),  # Shisa v2
        "shisa-ai/shisa-v2-llama3.3-70b:free": (0.00, 0.00),  # Free tier
    }
    
    return pricing


def calculate_model_cost(model_id: str, input_tokens: int, output_tokens: int) -> float:
    """
    Calculate the cost for a model query
    
    Args:
        model_id: Model identifier
        input_tokens: Number of input tokens
        output_tokens: Number of output tokens
        
    Returns:
        Total cost in USD
    """
    pricing = get_model_pricing()
    
    # Get pricing or use default if not found
    input_cost_per_m, output_cost_per_m = pricing.get(model_id, (0.50, 1.50))
    
    # Calculate cost (prices are per 1M tokens)
    input_cost = (input_tokens / 1_000_000) * input_cost_per_m
    output_cost = (output_tokens / 1_000_000) * output_cost_per_m
    
    return input_cost + output_cost


def format_cost(cost: float) -> str:
    """
    Format cost for display
    
    Args:
        cost: Cost in USD
        
    Returns:
        Formatted cost string
    """
    if cost == 0:
        return "Free"
    elif cost < 0.01:
        return "<$0.01"
    elif cost < 1:
        return f"${cost:.3f}"
    else:
        return f"${cost:.2f}"


def get_model_tier(model_id: str) -> str:
    """
    Get the pricing tier of a model
    
    Args:
        model_id: Model identifier
        
    Returns:
        Tier name: Premium, Mid-Range, Budget, or Free
    """
    pricing = get_model_pricing()
    
    if model_id not in pricing:
        return "Unknown"
    
    input_cost, output_cost = pricing[model_id]
    avg_cost = (input_cost + output_cost) / 2
    
    if avg_cost == 0:
        return "Free"
    elif avg_cost < 0.5:
        return "Budget"
    elif avg_cost < 5:
        return "Mid-Range"
    else:
        return "Premium"


def estimate_case_cost(responses: list) -> Dict:
    """
    Estimate total cost for all model responses in a case
    
    Args:
        responses: List of model responses with token counts
        
    Returns:
        Dictionary with cost breakdown
    """
    total_cost = 0
    model_costs = {}
    tier_costs = {"Premium": 0, "Mid-Range": 0, "Budget": 0, "Free": 0, "Unknown": 0}
    
    for response in responses:
        model_id = response.get('model_id', '')
        
        # Get token counts (estimate if not available)
        input_tokens = response.get('input_tokens', 3500)  # ~3500 for prompt
        output_tokens = response.get('output_tokens', response.get('tokens_used', 2000))
        
        # Calculate cost
        cost = calculate_model_cost(model_id, input_tokens, output_tokens)
        total_cost += cost
        
        # Store by model
        model_name = response.get('model_name', model_id.split('/')[-1])
        model_costs[model_name] = {
            'cost': cost,
            'tier': get_model_tier(model_id),
            'tokens': input_tokens + output_tokens
        }
        
        # Aggregate by tier
        tier = get_model_tier(model_id)
        tier_costs[tier] += cost
    
    return {
        'total_cost': total_cost,
        'model_costs': model_costs,
        'tier_costs': tier_costs,
        'average_cost': total_cost / len(responses) if responses else 0
    }


if __name__ == "__main__":
    # Test the pricing functions
    print("Model Pricing Test")
    print("=" * 50)
    
    # Test a few models
    test_models = [
        ("openai/gpt-4o", 1000, 500),
        ("anthropic/claude-3-opus-20240229", 1000, 500),
        ("google/gemini-2.5-flash-lite", 1000, 500),
        ("mistralai/mistral-7b-instruct:free", 1000, 500)
    ]
    
    for model_id, input_tokens, output_tokens in test_models:
        cost = calculate_model_cost(model_id, input_tokens, output_tokens)
        tier = get_model_tier(model_id)
        print(f"{model_id:40} {tier:10} {format_cost(cost):>10}")
    
    print("\n" + "=" * 50)
    print("✅ Pricing configuration ready!")