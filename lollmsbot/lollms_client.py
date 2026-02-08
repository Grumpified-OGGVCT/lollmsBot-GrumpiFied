from __future__ import annotations

from typing import Any, Optional, Dict, List
from urllib.parse import urlparse
import logging
import os

from lollms_client import LollmsClient  # from lollms-client package[web:21][web:41]

from .config import LollmsSettings

logger = logging.getLogger(__name__)

# Try to import multi-provider system (optional)
try:
    from lollmsbot.providers import MultiProviderRouter
    MULTI_PROVIDER_AVAILABLE = True
except ImportError:
    MULTI_PROVIDER_AVAILABLE = False
    MultiProviderRouter = None


def validate_url(url: str) -> bool:
    """Validate URL format.
    
    Args:
        url: URL to validate
        
    Returns:
        True if URL is valid, False otherwise
    """
    if not url or not isinstance(url, str):
        return False
    
    try:
        result = urlparse(url)
        # Must have scheme (http/https) and netloc (domain)
        return all([result.scheme in ('http', 'https', 'ws', 'wss'), result.netloc])
    except Exception:
        return False


def build_lollms_client(
    settings: LollmsSettings | None = None,
    use_multi_provider: bool = None
) -> LollmsClient:
    """
    Build a LollmsClient either in 'LoLLMS server' mode or 'direct binding' mode
    depending on env settings.
    
    Can optionally use multi-provider system (OpenRouter + Ollama) for cost optimization.
    
    Args:
        settings: Optional LollmsSettings instance. If None, loads from environment.
        use_multi_provider: If True, use multi-provider router. If None, auto-detect.
        
    Returns:
        Configured LollmsClient instance (or MultiProviderAdapter)
        
    Raises:
        ValueError: If settings are invalid
    """
    if settings is None:
        settings = LollmsSettings.from_env()

    # Auto-detect multi-provider usage
    if use_multi_provider is None:
        use_multi_provider = os.environ.get('USE_MULTI_PROVIDER', 'false').lower() == 'true'
    
    # Try multi-provider if available and enabled
    if use_multi_provider and MULTI_PROVIDER_AVAILABLE:
        try:
            logger.info("Using multi-provider system (OpenRouter + Ollama)")
            router = MultiProviderRouter()
            return MultiProviderLollmsAdapter(router)
        except Exception as e:
            logger.warning(f"Multi-provider initialization failed: {e}, falling back to standard client")
    
    # Standard LollmsClient (original behavior)
    # Validate host_address if provided
    if settings.host_address:
        if not validate_url(settings.host_address):
            raise ValueError(f"Invalid host_address URL: {settings.host_address}")
        logger.info(f"Using LoLLMS host: {settings.host_address}")
    
    # Validate API key format if provided (basic check for non-empty string)
    if settings.api_key:
        if not isinstance(settings.api_key, str) or len(settings.api_key) < 10:
            logger.warning("API key seems too short or invalid format")
    
    # Validate context size
    if settings.context_size and (settings.context_size < 512 or settings.context_size > 128000):
        logger.warning(f"Context size {settings.context_size} is outside normal range (512-128000)")

    # Basic shared kwargs
    client_kwargs: dict[str, Any] = {}

    if settings.host_address:
        client_kwargs["host_address"] = settings.host_address

    # Some lollms_client versions support verify_ssl; if not, this can be removed
    if settings.verify_ssl is False:
        client_kwargs["verify_ssl"] = False

    # Direct binding mode
    return LollmsClient(
        llm_binding_name= settings.binding_name or "lollms",
        llm_binding_config={
            "host_address":settings.host_address,
            "model_name":settings.model_name,
            "service_key":settings.api_key,
            "ctx_size":settings.context_size,
        },
    )


class MultiProviderLollmsAdapter:
    """
    Adapter to make MultiProviderRouter compatible with LollmsClient interface.
    
    This allows Agent to use multi-provider system transparently.
    """
    
    def __init__(self, router: Any):
        """Initialize adapter with router."""
        self.router = router
        logger.info("MultiProviderLollmsAdapter initialized")
    
    async def generate_text(
        self,
        prompt: str,
        model: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        **kwargs
    ) -> str:
        """Generate text using multi-provider router.
        
        Args:
            prompt: Text prompt
            model: Optional specific model name
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            **kwargs: Additional arguments
            
        Returns:
            Generated text
        """
        messages = [{"role": "user", "content": prompt}]
        
        try:
            response = await self.router.chat(
                messages=messages,
                model=model,
                max_tokens=max_tokens,
                temperature=temperature,
                **kwargs
            )
            return response.get("content", "")
        except Exception as e:
            logger.error(f"Multi-provider generation failed: {e}")
            raise
    
    async def chat(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Chat using multi-provider router.
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            model: Optional specific model name
            **kwargs: Additional arguments
            
        Returns:
            Response dict with 'content' and metadata
        """
        try:
            return await self.router.chat(
                messages=messages,
                model=model,
                **kwargs
            )
        except Exception as e:
            logger.error(f"Multi-provider chat failed: {e}")
            raise
    
    def get_status(self) -> Dict[str, Any]:
        """Get multi-provider router status.
        
        Returns:
            Status dict with provider info
        """
        return self.router.get_status()
