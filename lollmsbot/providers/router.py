"""Multi-provider router with intelligent fallback."""

import os
import logging
from typing import List, Dict, Optional
from .base_provider import BaseProvider, ProviderResponse, ProviderError, QuotaExhaustedError, ProviderConfig
from .openrouter_provider import OpenRouterProvider
from .ollama_provider import OllamaProvider

logger = logging.getLogger(__name__)


class MultiProviderRouter:
    """Routes requests across multiple providers with intelligent fallback."""
    
    def __init__(self):
        """Initialize router with providers from environment."""
        self.providers: List[BaseProvider] = []
        self._setup_providers()
    
    def _setup_providers(self):
        """Setup providers from environment variables."""
        # OpenRouter (3 keys for free tier cycling)
        openrouter_keys = []
        for i in [1, 2, 3]:
            key = os.getenv(f"OPENROUTER_API_KEY_{i}")
            if key:
                openrouter_keys.append(key)
        
        if openrouter_keys:
            openrouter_config = ProviderConfig(
                name="OpenRouter",
                api_keys=openrouter_keys,
                endpoint="https://openrouter.ai/api/v1",
                enabled=True
            )
            self.providers.append(OpenRouterProvider(openrouter_config))
            logger.info(f"OpenRouter provider initialized with {len(openrouter_keys)} keys")
        
        # Ollama Cloud (2 keys for load balancing)
        ollama_keys = []
        for var in ["OLLAMA_API_KEY", "OLLAMA_API_KEY_2"]:
            key = os.getenv(var)
            if key:
                ollama_keys.append(key)
        
        if ollama_keys:
            ollama_config = ProviderConfig(
                name="Ollama",
                api_keys=ollama_keys,
                endpoint="https://ollama.com/api",
                enabled=True
            )
            self.providers.append(OllamaProvider(ollama_config))
            logger.info(f"Ollama provider initialized with {len(ollama_keys)} keys")
    
    async def chat(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        prefer_provider: Optional[str] = None,
        **kwargs
    ) -> ProviderResponse:
        """Route chat request through providers.
        
        Strategy:
        1. Default to KimiK2.5:cloud (Ollama) if no model specified
        2. Prefer Ollama for default models
        3. Fallback to OpenRouter only if explicitly requested or for specific models
        
        Args:
            messages: Chat messages
            model: Optional model name
            prefer_provider: Force specific provider
            **kwargs: Additional parameters
            
        Returns:
            ProviderResponse from successful provider
            
        Raises:
            ProviderError: If all providers fail
        """
        # User Preference: Default to KimiK2.5:cloud
        if model is None:
            model = "kimi-k2.5:cloud"
            
        # FIX: Force correct model name and format
        # 1. Correct typos
        if model == "kimik2.5":
            model = "kimi-k2.5:cloud"
        if model == "kimi-k2.5":
            model = "kimi-k2.5:cloud"
            
        # 2. Ensure cloud tag is present for Ollama Cloud models (User Instruction)
        # Exception: Gemini 3 Flash might not need/want it
        if model == "gemini-3-flash-preview:cloud":
             model = "gemini-3-flash-preview"
             
        # Check if model is Ollama-specific (skip OpenRouter)
        ollama_models = ["kimi", "deepseek", "cogito", "qwen", "ministral", "nemotron", "gemma", "glm", "devstral"]
        is_ollama_model = model and any(om in model.lower() for om in ollama_models)
        
        # Sort providers: Ollama first by default now
        sorted_providers = sorted(
            self.providers,
            key=lambda p: 0 if isinstance(p, OllamaProvider) else 1
        )
        
        # Try providers in order
        errors = []
        
        for provider in sorted_providers:
            # Skip if not preferred provider (when specified)
            if prefer_provider and provider.config.name.lower() != prefer_provider.lower():
                continue
            
            # Skip OpenRouter for Ollama-specific models
            if isinstance(provider, OpenRouterProvider) and is_ollama_model:
                logger.debug(f"Skipping OpenRouter for Ollama-specific model: {model}")
                continue
            
            # Skip Ollama if OpenRouter explicitly requested (unless it's an Ollama model)
            if isinstance(provider, OllamaProvider) and not is_ollama_model and prefer_provider == "openrouter":
                 continue
            
            try:
                logger.info(f"Trying provider: {provider.config.name} with model {model}")
                response = await provider.chat(messages, model=model, **kwargs)
                logger.info(f"Success with {provider.config.name} using key {response.key_id}")
                return response
            
            except QuotaExhaustedError as e:
                logger.warning(f"{provider.config.name} quota exhausted: {e}")
                errors.append(f"{provider.config.name}: quota exhausted")
            
            except ProviderError as e:
                logger.error(f"{provider.config.name} error: {e}")
                errors.append(f"{provider.config.name}: {e}")
        
        # All providers failed
        error_msg = f"All providers failed: {'; '.join(errors)}"
        logger.error(error_msg)
        raise ProviderError(error_msg)
    
    async def list_models(self, provider_name: Optional[str] = None) -> Dict[str, List[str]]:
        """List models from all providers or specific provider.
        
        Args:
            provider_name: Optional provider name filter
            
        Returns:
            Dict mapping provider names to model lists
        """
        result = {}
        for provider in self.providers:
            if provider_name and provider.config.name.lower() != provider_name.lower():
                continue
            try:
                models = await provider.list_models()
                result[provider.config.name] = models
            except Exception as e:
                logger.error(f"Error listing models from {provider.config.name}: {e}")
        return result
    
    def get_status(self) -> Dict[str, any]:
        """Get router status.
        
        Returns:
            Dict with provider status information
        """
        return {
            "default_model": "kimik2.5:cloud",
            "providers": [
                {
                    "name": p.config.name,
                    "enabled": p.config.enabled,
                    "num_keys": len(p.config.api_keys),
                    "endpoint": p.config.endpoint
                }
                for p in self.providers
            ]
        }
