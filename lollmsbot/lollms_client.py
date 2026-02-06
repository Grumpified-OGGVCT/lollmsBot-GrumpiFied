from __future__ import annotations

from typing import Any
from urllib.parse import urlparse
import logging

from lollms_client import LollmsClient  # from lollms-client package[web:21][web:41]

from .config import LollmsSettings

logger = logging.getLogger(__name__)


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


def build_lollms_client(settings: LollmsSettings | None = None) -> LollmsClient:
    """
    Build a LollmsClient either in 'LoLLMS server' mode or 'direct binding' mode
    depending on env settings.
    
    Args:
        settings: Optional LollmsSettings instance. If None, loads from environment.
        
    Returns:
        Configured LollmsClient instance
        
    Raises:
        ValueError: If settings are invalid
    """
    if settings is None:
        settings = LollmsSettings.from_env()

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
