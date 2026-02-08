"""Ollama Cloud provider implementation."""

import aiohttp
import asyncio
import time
from typing import List, Dict, Optional
from .base_provider import BaseProvider, ProviderResponse, ProviderError, ProviderConfig


class OllamaProvider(BaseProvider):
    """Ollama Cloud API provider."""
    
    def __init__(self, config: ProviderConfig):
        super().__init__(config)
        if not config.endpoint:
            config.endpoint = "https://ollama.com/api"
    
    async def chat(self, messages: List[Dict[str, str]], model: Optional[str] = None, **kwargs) -> ProviderResponse:
        """Send chat request to Ollama Cloud."""
        if not model:
            raise ProviderError("Ollama requires explicit model specification")
        
        # Load balance between keys
        key = self.get_next_key()
        key_id = self.get_key_id(key)
        
        try:
            start_time = time.time()
            
            async with aiohttp.ClientSession() as session:
                headers = {
                    "Authorization": f"Bearer {key}",
                    "Content-Type": "application/json",
                }
                
                payload = {
                    "model": model,
                    "messages": messages,
                    "stream": False,
                    **kwargs
                }
                
                async with session.post(
                    f"{self.config.endpoint}/chat",
                    headers=headers,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=60)
                ) as response:
                    latency_ms = (time.time() - start_time) * 1000
                    
                    if response.status != 200:
                        error_text = await response.text()
                        raise ProviderError(f"Ollama error {response.status}: {error_text}")
                    
                    data = await response.json()
                    
                    # Extract response
                    content = data['message']['content']
                    tokens = data.get('eval_count', 0) + data.get('prompt_eval_count', 0)
                    
                    # Estimate cost (approximate)
                    cost = tokens * 0.00001  # Rough estimate
                    
                    return ProviderResponse(
                        content=content,
                        model=model,
                        provider="ollama",
                        key_id=key_id,
                        tokens_used=tokens,
                        cost=cost,
                        latency_ms=latency_ms
                    )
        
        except asyncio.TimeoutError:
            raise ProviderError(f"Ollama timeout with key {key_id}")
        except Exception as e:
            raise ProviderError(f"Ollama error with key {key_id}: {e}")
    
    async def list_models(self) -> List[str]:
        """List available models."""
        key = self.config.api_keys[0] if self.config.api_keys else None
        if not key:
            return []
        
        try:
            async with aiohttp.ClientSession() as session:
                headers = {"Authorization": f"Bearer {key}"}
                async with session.get(f"{self.config.endpoint}/tags", headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        return [m['name'] for m in data.get('models', [])]
        except Exception as e:
            self.logger.error(f"Error listing Ollama models: {e}")
        return []
