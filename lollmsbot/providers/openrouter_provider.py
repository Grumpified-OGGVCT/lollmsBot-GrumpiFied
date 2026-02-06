"""OpenRouter provider implementation."""

import aiohttp
import asyncio
import time
from typing import List, Dict, Optional
from .base_provider import BaseProvider, ProviderResponse, ProviderError, QuotaExhaustedError, ProviderConfig


class OpenRouterProvider(BaseProvider):
    """OpenRouter API provider with free tier support."""
    
    DEFAULT_MODEL = "openrouter/free"  # Automatic free model router
    
    def __init__(self, config: ProviderConfig):
        super().__init__(config)
        if not config.endpoint:
            config.endpoint = "https://openrouter.ai/api/v1"
        self._quota_status = {key: {"exhausted": False, "attempts": 0} for key in config.api_keys}
    
    async def chat(self, messages: List[Dict[str, str]], model: Optional[str] = None, **kwargs) -> ProviderResponse:
        """Send chat request to OpenRouter."""
        if model is None:
            model = self.DEFAULT_MODEL
        
        # Try all keys in sequence
        for attempt in range(len(self.config.api_keys)):
            key = self.get_next_key()
            key_id = self.get_key_id(key)
            
            # Skip if this key is known to be exhausted
            if self._quota_status[key]["exhausted"]:
                self.logger.debug(f"Skipping exhausted key {key_id}")
                continue
            
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
                        **kwargs
                    }
                    
                    async with session.post(
                        f"{self.config.endpoint}/chat/completions",
                        headers=headers,
                        json=payload,
                        timeout=aiohttp.ClientTimeout(total=60)
                    ) as response:
                        latency_ms = (time.time() - start_time) * 1000
                        
                        if response.status == 429:
                            # Quota exhausted for this key
                            self._quota_status[key]["exhausted"] = True
                            self.logger.warning(f"OpenRouter key {key_id} quota exhausted (429)")
                            continue
                        
                        if response.status != 200:
                            error_text = await response.text()
                            raise ProviderError(f"OpenRouter error {response.status}: {error_text}")
                        
                        data = await response.json()
                        
                        # Extract response
                        content = data['choices'][0]['message']['content']
                        actual_model = data.get('model', model)
                        tokens = data.get('usage', {}).get('total_tokens', 0)
                        
                        # Reset exhausted status on success
                        self._quota_status[key]["exhausted"] = False
                        
                        return ProviderResponse(
                            content=content,
                            model=actual_model,
                            provider="openrouter",
                            key_id=key_id,
                            tokens_used=tokens,
                            cost=0.0,  # Free tier
                            latency_ms=latency_ms
                        )
            
            except asyncio.TimeoutError:
                self.logger.error(f"OpenRouter timeout with key {key_id}")
                continue
            except Exception as e:
                self.logger.error(f"OpenRouter error with key {key_id}: {e}")
                continue
        
        # All keys exhausted
        raise QuotaExhaustedError("All OpenRouter keys exhausted")
    
    async def list_models(self) -> List[str]:
        """List available models."""
        # Use first available key
        for key in self.config.api_keys:
            if not self._quota_status[key]["exhausted"]:
                try:
                    async with aiohttp.ClientSession() as session:
                        headers = {"Authorization": f"Bearer {key}"}
                        async with session.get(f"{self.config.endpoint}/models", headers=headers) as response:
                            if response.status == 200:
                                data = await response.json()
                                return [m['id'] for m in data.get('data', [])]
                except Exception as e:
                    self.logger.error(f"Error listing OpenRouter models: {e}")
        return []
