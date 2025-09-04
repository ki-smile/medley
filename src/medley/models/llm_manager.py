"""
LLM Manager for OpenRouter API integration
Handles model queries, responses, and error management
"""

import json
import time
import asyncio
import aiohttp
import requests
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
from datetime import datetime

from ..utils.config import Config, ModelConfig
from ..utils.token_counter import get_token_stats

@dataclass
class LLMResponse:
    """Structured response from an LLM"""
    model_name: str
    model_id: str
    content: str
    timestamp: str
    latency: float
    tokens_used: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    error: Optional[str] = None
    raw_response: Optional[Dict] = None
    
    def to_dict(self) -> Dict:
        return asdict(self)

class LLMManager:
    """Manages interactions with LLMs through OpenRouter API"""
    
    OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"
    
    def __init__(self, config: Config):
        self.config = config
        self.api_key = config.api_key
        
        if not self.api_key:
            raise ValueError("OpenRouter API key not configured")
        
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/medley",
            "X-Title": "Medley Medical AI Ensemble"
        }
        
    def query_model(
        self,
        model_config: ModelConfig,
        prompt: str,
        system_prompt: Optional[str] = None
    ) -> LLMResponse:
        """Query a single model synchronously"""
        
        start_time = time.time()
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        payload = {
            "model": model_config.model_id,
            "messages": messages,
            "max_tokens": model_config.max_tokens,
            "temperature": model_config.temperature,
        }
        
        try:
            response = requests.post(
                self.OPENROUTER_API_URL,
                headers=self.headers,
                json=payload,
                timeout=60
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Extract response content from both content and reasoning fields
                message = data.get("choices", [{}])[0].get("message", {})
                content_field = message.get("content", "")
                reasoning_field = message.get("reasoning", "")
                
                # Combine both fields if they exist
                content_parts = []
                if reasoning_field:
                    content_parts.append(reasoning_field)
                if content_field:
                    content_parts.append(content_field)
                
                # Join with separator if we have both
                if len(content_parts) == 2:
                    content = "\n\n---\n\n".join(content_parts)
                    print(f"    ℹ️  Combined reasoning and content fields for {model_config.model_id}")
                elif content_parts:
                    content = content_parts[0]
                    if reasoning_field and not content_field:
                        print(f"    ℹ️  Using reasoning field as content for {model_config.model_id}")
                else:
                    content = ""
                
                # Extract token usage from API response
                usage = data.get("usage", {})
                api_total_tokens = usage.get("total_tokens", 0)
                api_input_tokens = usage.get("prompt_tokens", 0)
                api_output_tokens = usage.get("completion_tokens", 0)
                
                # Calculate local token stats as backup
                token_stats = get_token_stats(
                    prompt=prompt,
                    response=content,
                    system_prompt=system_prompt
                )
                
                # Use API tokens if available, otherwise use local calculation
                final_total_tokens = api_total_tokens if api_total_tokens > 0 else token_stats["total_tokens"]
                final_input_tokens = api_input_tokens if api_input_tokens > 0 else token_stats["input_tokens"]
                final_output_tokens = api_output_tokens if api_output_tokens > 0 else token_stats["output_tokens"]
                
                return LLMResponse(
                    model_name=model_config.name,
                    model_id=model_config.model_id,
                    content=content,
                    timestamp=datetime.now().isoformat(),
                    latency=time.time() - start_time,
                    tokens_used=final_total_tokens,
                    input_tokens=final_input_tokens,
                    output_tokens=final_output_tokens,
                    raw_response=data
                )
            else:
                error_msg = f"API Error {response.status_code}: {response.text}"
                return LLMResponse(
                    model_name=model_config.name,
                    model_id=model_config.model_id,
                    content="",
                    timestamp=datetime.now().isoformat(),
                    latency=time.time() - start_time,
                    error=error_msg
                )
                
        except requests.exceptions.Timeout:
            return LLMResponse(
                model_name=model_config.name,
                model_id=model_config.model_id,
                content="",
                timestamp=datetime.now().isoformat(),
                latency=time.time() - start_time,
                error="Request timeout after 60 seconds"
            )
        except Exception as e:
            return LLMResponse(
                model_name=model_config.name,
                model_id=model_config.model_id,
                content="",
                timestamp=datetime.now().isoformat(),
                latency=time.time() - start_time,
                error=str(e)
            )
    
    async def query_model_async(
        self,
        session: aiohttp.ClientSession,
        model_config: ModelConfig,
        prompt: str,
        system_prompt: Optional[str] = None
    ) -> LLMResponse:
        """Query a single model asynchronously"""
        
        start_time = time.time()
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        payload = {
            "model": model_config.model_id,
            "messages": messages,
            "max_tokens": model_config.max_tokens,
            "temperature": model_config.temperature,
        }
        
        try:
            async with session.post(
                self.OPENROUTER_API_URL,
                headers=self.headers,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=60)
            ) as response:
                
                if response.status == 200:
                    data = await response.json()
                    
                    # Extract response content from both content and reasoning fields
                    message = data.get("choices", [{}])[0].get("message", {})
                    content_field = message.get("content", "")
                    reasoning_field = message.get("reasoning", "")
                    
                    # Combine both fields if they exist
                    content_parts = []
                    if reasoning_field:
                        content_parts.append(reasoning_field)
                    if content_field:
                        content_parts.append(content_field)
                    
                    # Join with separator if we have both
                    if len(content_parts) == 2:
                        content = "\n\n---\n\n".join(content_parts)
                        print(f"    ℹ️  Combined reasoning and content fields for {model_config.model_id}")
                    elif content_parts:
                        content = content_parts[0]
                        if reasoning_field and not content_field:
                            print(f"    ℹ️  Using reasoning field as content for {model_config.model_id}")
                    else:
                        content = ""
                    
                    # Extract token usage from API response
                    usage = data.get("usage", {})
                    api_total_tokens = usage.get("total_tokens", 0)
                    api_input_tokens = usage.get("prompt_tokens", 0)
                    api_output_tokens = usage.get("completion_tokens", 0)
                    
                    # Calculate local token stats as backup
                    token_stats = get_token_stats(
                        prompt=prompt,
                        response=content,
                        system_prompt=system_prompt
                    )
                    
                    # Use API tokens if available, otherwise use local calculation
                    final_total_tokens = api_total_tokens if api_total_tokens > 0 else token_stats["total_tokens"]
                    final_input_tokens = api_input_tokens if api_input_tokens > 0 else token_stats["input_tokens"]
                    final_output_tokens = api_output_tokens if api_output_tokens > 0 else token_stats["output_tokens"]
                    
                    return LLMResponse(
                        model_name=model_config.name,
                        model_id=model_config.model_id,
                        content=content,
                        timestamp=datetime.now().isoformat(),
                        latency=time.time() - start_time,
                        tokens_used=final_total_tokens,
                        input_tokens=final_input_tokens,
                        output_tokens=final_output_tokens,
                        raw_response=data
                    )
                else:
                    error_text = await response.text()
                    error_msg = f"API Error {response.status}: {error_text}"
                    return LLMResponse(
                        model_name=model_config.name,
                        model_id=model_config.model_id,
                        content="",
                        timestamp=datetime.now().isoformat(),
                        latency=time.time() - start_time,
                        error=error_msg
                    )
                    
        except asyncio.TimeoutError:
            return LLMResponse(
                model_name=model_config.name,
                model_id=model_config.model_id,
                content="",
                timestamp=datetime.now().isoformat(),
                latency=time.time() - start_time,
                error="Request timeout after 60 seconds"
            )
        except Exception as e:
            return LLMResponse(
                model_name=model_config.name,
                model_id=model_config.model_id,
                content="",
                timestamp=datetime.now().isoformat(),
                latency=time.time() - start_time,
                error=str(e)
            )
    
    async def query_models_parallel(
        self,
        model_configs: List[ModelConfig],
        prompt: str,
        system_prompt: Optional[str] = None
    ) -> List[LLMResponse]:
        """Query multiple models in parallel"""
        
        async with aiohttp.ClientSession() as session:
            tasks = [
                self.query_model_async(session, model, prompt, system_prompt)
                for model in model_configs
            ]
            responses = await asyncio.gather(*tasks)
            
        return responses
    
    def test_connection(self) -> bool:
        """Test OpenRouter API connection"""
        try:
            response = requests.get(
                "https://openrouter.ai/api/v1/models",
                headers={"Authorization": f"Bearer {self.api_key}"},
                timeout=10
            )
            return response.status_code == 200
        except:
            return False