"""Base provider interface."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List
import logging

logger = logging.getLogger(__name__)


@dataclass
class ProviderResponse:
    """Response from a provider API call."""
    content: str
    model: str
    provider: str
    key_id: str
    tokens_used: int = 0
    cost: float = 0.0
    latency_ms: float = 0.0


class ProviderError(Exception):
    """Base exception for provider errors."""
    pass


class QuotaExhaustedError(ProviderError):
    """Raised when provider quota is exhausted."""
    pass


@dataclass
class ProviderConfig:
    """Configuration for a provider."""
    name: str
    api_keys: List[str] = field(default_factory=list)
    endpoint: str = ""
    enabled: bool = True


class BaseProvider(ABC):
    """Abstract base class for AI providers."""
    
    def __init__(self, config: ProviderConfig):
        self.config = config
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self._current_key_index = 0
    
    @abstractmethod
    async def chat(self, messages: List[Dict[str, str]], model: Optional[str] = None, **kwargs) -> ProviderResponse:
        """Send chat completion request."""
        pass
    
    @abstractmethod
    async def list_models(self) -> List[str]:
        """List available models."""
        pass
    
    def get_next_key(self) -> str:
        """Get next API key in rotation."""
        if not self.config.api_keys:
            raise ProviderError(f"{self.config.name}: No API keys configured")
        key = self.config.api_keys[self._current_key_index]
        self._current_key_index = (self._current_key_index + 1) % len(self.config.api_keys)
        return key
    
    def get_key_id(self, key: str) -> str:
        """Get masked key ID for logging."""
        if not key:
            return "none"
        return f"{key[:8]}..."
