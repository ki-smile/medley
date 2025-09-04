"""
Token Counter Utility
Provides local token counting for medical AI analysis
"""

import re
from typing import Optional

try:
    import tiktoken
    TIKTOKEN_AVAILABLE = True
except ImportError:
    TIKTOKEN_AVAILABLE = False
    tiktoken = None


class TokenCounter:
    """Local token counting utility for various model types"""
    
    def __init__(self):
        """Initialize token counter with appropriate encoders"""
        if TIKTOKEN_AVAILABLE:
            try:
                # Use cl100k_base encoding (used by GPT-4, GPT-3.5-turbo)
                self.encoder = tiktoken.get_encoding("cl100k_base")
            except:
                # Fallback to approximate counting if tiktoken fails
                self.encoder = None
        else:
            # tiktoken not available, use approximation
            self.encoder = None
    
    def count_tokens(self, text: str) -> int:
        """
        Count tokens in text using tiktoken or approximation
        
        Args:
            text: Text to count tokens for
            
        Returns:
            Number of tokens (approximate)
        """
        if not text:
            return 0
            
        if self.encoder:
            try:
                return len(self.encoder.encode(text))
            except:
                pass
        
        # Fallback approximation: ~4 characters per token for English text
        # This is the industry standard approximation
        return max(1, len(text) // 4)
    
    def count_prompt_tokens(self, prompt: str, system_prompt: Optional[str] = None) -> int:
        """
        Count tokens in a prompt (input tokens)
        
        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            
        Returns:
            Total input tokens
        """
        total = 0
        
        if system_prompt:
            total += self.count_tokens(system_prompt)
            
        total += self.count_tokens(prompt)
        
        # Add a few tokens for message formatting overhead
        total += 10
        
        return total
    
    def count_response_tokens(self, response: str) -> int:
        """
        Count tokens in a model response (output tokens)
        
        Args:
            response: Model response text
            
        Returns:
            Output tokens
        """
        return self.count_tokens(response)
    
    def estimate_cost(self, input_tokens: int, output_tokens: int, model_id: str) -> float:
        """
        Estimate cost based on token counts and model pricing
        
        Args:
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens  
            model_id: Model identifier
            
        Returns:
            Estimated cost in USD
        """
        # Import pricing data
        try:
            from .model_pricing import ModelPricing
            pricing = ModelPricing()
            return pricing.estimate_cost(input_tokens, output_tokens, model_id)
        except:
            # Fallback rough estimate: $0.03 per 1000 tokens total
            total_tokens = input_tokens + output_tokens
            return (total_tokens / 1000) * 0.03
    
    def get_token_stats(self, prompt: str, response: str, system_prompt: Optional[str] = None) -> dict:
        """
        Get comprehensive token statistics
        
        Args:
            prompt: User prompt
            response: Model response
            system_prompt: Optional system prompt
            
        Returns:
            Dictionary with token statistics
        """
        input_tokens = self.count_prompt_tokens(prompt, system_prompt)
        output_tokens = self.count_response_tokens(response)
        total_tokens = input_tokens + output_tokens
        
        return {
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": total_tokens,
            "prompt_length": len(prompt),
            "response_length": len(response),
            "system_prompt_length": len(system_prompt) if system_prompt else 0
        }


# Global instance for easy usage
token_counter = TokenCounter()


def count_tokens(text: str) -> int:
    """Convenience function to count tokens in text"""
    return token_counter.count_tokens(text)


def get_token_stats(prompt: str, response: str, system_prompt: Optional[str] = None) -> dict:
    """Convenience function to get token statistics"""
    return token_counter.get_token_stats(prompt, response, system_prompt)