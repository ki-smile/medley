#!/usr/bin/env python
"""
Cost Calculator for MEDLEY
Estimates costs for model queries via OpenRouter
"""

from typing import Dict, List, Optional

# Model pricing per million tokens (OpenRouter pricing as of 2025)
MODEL_PRICING = {
    # Free models
    'google/gemini-2.0-flash-exp:free': {'input': 0.0, 'output': 0.0},
    'google/gemini-1.5-flash:free': {'input': 0.0, 'output': 0.0},
    'google/gemini-1.5-flash-8b:free': {'input': 0.0, 'output': 0.0},
    'meta-llama/llama-3.2-3b-instruct:free': {'input': 0.0, 'output': 0.0},
    'meta-llama/llama-3.2-1b-instruct:free': {'input': 0.0, 'output': 0.0},
    'meta-llama/llama-3.1-8b-instruct:free': {'input': 0.0, 'output': 0.0},
    'microsoft/phi-3-mini-128k-instruct:free': {'input': 0.0, 'output': 0.0},
    'microsoft/phi-3-medium-128k-instruct:free': {'input': 0.0, 'output': 0.0},
    'mistralai/mistral-7b-instruct:free': {'input': 0.0, 'output': 0.0},
    'mistralai/pixtral-12b:free': {'input': 0.0, 'output': 0.0},
    'qwen/qwen-2-7b-instruct:free': {'input': 0.0, 'output': 0.0},
    'qwen/qwen-2-vl-7b-instruct:free': {'input': 0.0, 'output': 0.0},
    'nousresearch/hermes-3-llama-3.1-8b:free': {'input': 0.0, 'output': 0.0},
    'liquid/lfm-40b:free': {'input': 0.0, 'output': 0.0},
    'thebloke/mythomax-l2-13b:free': {'input': 0.0, 'output': 0.0},
    'huggingfaceh4/zephyr-7b-beta:free': {'input': 0.0, 'output': 0.0},
    
    # Paid models (prices per million tokens)
    'openai/gpt-4o': {'input': 2.50, 'output': 10.00},
    'openai/gpt-4o-mini': {'input': 0.15, 'output': 0.60},
    'openai/gpt-4-turbo': {'input': 10.00, 'output': 30.00},
    'anthropic/claude-3-opus': {'input': 15.00, 'output': 75.00},
    'anthropic/claude-3-sonnet': {'input': 3.00, 'output': 15.00},
    'anthropic/claude-3-haiku': {'input': 0.25, 'output': 1.25},
    'google/gemini-pro': {'input': 0.50, 'output': 1.50},
    'google/gemini-pro-1.5': {'input': 3.50, 'output': 10.50},
    'deepseek/deepseek-chat': {'input': 0.14, 'output': 0.28},
    'deepseek/deepseek-coder': {'input': 0.14, 'output': 0.28},
    'mistralai/mistral-large': {'input': 2.00, 'output': 6.00},
    'mistralai/mistral-medium': {'input': 0.65, 'output': 1.95},
    'mistralai/mistral-small': {'input': 0.20, 'output': 0.60},
    'meta-llama/llama-3.1-70b-instruct': {'input': 0.88, 'output': 0.88},
    'meta-llama/llama-3.1-405b-instruct': {'input': 5.00, 'output': 15.00},
    'cohere/command-r-plus': {'input': 3.00, 'output': 15.00},
    'cohere/command-r': {'input': 0.50, 'output': 1.50},
}

class CostCalculator:
    """Calculate estimated costs for model queries"""
    
    def __init__(self):
        self.pricing = MODEL_PRICING
        # Average tokens for medical case analysis
        self.avg_input_tokens = 1500  # Typical medical case prompt
        self.avg_output_tokens = 800   # Typical diagnostic response
    
    def estimate_single_model_cost(
        self, 
        model_id: str,
        input_tokens: Optional[int] = None,
        output_tokens: Optional[int] = None
    ) -> Dict[str, float]:
        """
        Estimate cost for a single model query
        
        Args:
            model_id: Model identifier
            input_tokens: Number of input tokens (uses average if not provided)
            output_tokens: Number of output tokens (uses average if not provided)
            
        Returns:
            Dictionary with cost breakdown
        """
        input_tokens = input_tokens or self.avg_input_tokens
        output_tokens = output_tokens or self.avg_output_tokens
        
        # Get pricing for model
        if model_id not in self.pricing:
            # Default to medium pricing if model not found
            pricing = {'input': 1.00, 'output': 3.00}
        else:
            pricing = self.pricing[model_id]
        
        # Calculate costs (pricing is per million tokens)
        input_cost = (input_tokens / 1_000_000) * pricing['input']
        output_cost = (output_tokens / 1_000_000) * pricing['output']
        total_cost = input_cost + output_cost
        
        return {
            'model_id': model_id,
            'input_tokens': input_tokens,
            'output_tokens': output_tokens,
            'input_cost': round(input_cost, 4),
            'output_cost': round(output_cost, 4),
            'total_cost': round(total_cost, 4),
            'is_free': pricing['input'] == 0 and pricing['output'] == 0
        }
    
    def estimate_ensemble_cost(
        self,
        model_ids: List[str],
        input_tokens: Optional[int] = None,
        output_tokens: Optional[int] = None
    ) -> Dict[str, any]:
        """
        Estimate total cost for ensemble analysis
        
        Args:
            model_ids: List of model identifiers
            input_tokens: Number of input tokens per model
            output_tokens: Number of output tokens per model
            
        Returns:
            Dictionary with ensemble cost breakdown
        """
        model_costs = []
        total_cost = 0.0
        free_models = 0
        paid_models = 0
        
        for model_id in model_ids:
            cost = self.estimate_single_model_cost(
                model_id, 
                input_tokens, 
                output_tokens
            )
            model_costs.append(cost)
            total_cost += cost['total_cost']
            
            if cost['is_free']:
                free_models += 1
            else:
                paid_models += 1
        
        return {
            'total_models': len(model_ids),
            'free_models': free_models,
            'paid_models': paid_models,
            'total_cost': round(total_cost, 4),
            'cost_per_model': round(total_cost / len(model_ids), 4) if model_ids else 0,
            'model_costs': model_costs,
            'estimated_tokens': {
                'input': input_tokens or self.avg_input_tokens,
                'output': output_tokens or self.avg_output_tokens,
                'total': (input_tokens or self.avg_input_tokens) + 
                        (output_tokens or self.avg_output_tokens)
            }
        }
    
    def format_cost_display(self, cost: float) -> str:
        """
        Format cost for display
        
        Args:
            cost: Cost in dollars
            
        Returns:
            Formatted cost string
        """
        if cost == 0:
            return "Free"
        elif cost < 0.01:
            return f"<$0.01"
        elif cost < 1:
            return f"${cost:.3f}"
        else:
            return f"${cost:.2f}"
    
    def get_model_tier(self, model_id: str) -> str:
        """
        Get pricing tier for a model
        
        Args:
            model_id: Model identifier
            
        Returns:
            Tier name (Free, Budget, Standard, Premium)
        """
        if model_id not in self.pricing:
            return "Unknown"
        
        pricing = self.pricing[model_id]
        total_price = pricing['input'] + pricing['output']
        
        if total_price == 0:
            return "Free"
        elif total_price < 2:
            return "Budget"
        elif total_price < 20:
            return "Standard"
        else:
            return "Premium"


# Example usage
if __name__ == "__main__":
    calculator = CostCalculator()
    
    # Test single model
    cost = calculator.estimate_single_model_cost('openai/gpt-4o')
    print(f"GPT-4o cost: {calculator.format_cost_display(cost['total_cost'])}")
    
    # Test ensemble with free models
    free_models = [
        'google/gemini-2.0-flash-exp:free',
        'meta-llama/llama-3.2-3b-instruct:free',
        'mistralai/mistral-7b-instruct:free',
        'qwen/qwen-2-7b-instruct:free'
    ]
    
    ensemble_cost = calculator.estimate_ensemble_cost(free_models)
    print(f"\nFree ensemble ({len(free_models)} models): {calculator.format_cost_display(ensemble_cost['total_cost'])}")
    
    # Test mixed ensemble
    mixed_models = free_models + ['openai/gpt-4o-mini', 'anthropic/claude-3-haiku']
    ensemble_cost = calculator.estimate_ensemble_cost(mixed_models)
    print(f"Mixed ensemble ({len(mixed_models)} models): {calculator.format_cost_display(ensemble_cost['total_cost'])}")
    print(f"  - Free models: {ensemble_cost['free_models']}")
    print(f"  - Paid models: {ensemble_cost['paid_models']}")