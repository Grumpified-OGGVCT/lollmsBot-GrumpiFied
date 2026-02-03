"""Channel adapters for LollmsBot.

This package provides channel implementations for various messaging platforms.
Each channel handles the protocol-specific communication while providing a
unified interface for message sending and receiving.
"""

from abc import ABC, abstractmethod
from typing import Any, Awaitable, Callable, Optional, TYPE_CHECKING


class Channel(ABC):
    """Abstract base class for all messaging channels.
    
    All channel implementations must inherit from this class and implement
    the required methods for starting, stopping, and sending messages.
    
    Attributes:
        name: Unique identifier for this channel.
        agent: Optional Agent instance for processing messages.
        _is_running: Whether the channel is currently active.
    """
    
    def __init__(
        self,
        name: str,
        agent: Optional[Any] = None,
    ) -> None:
        """Initialize the channel.
        
        Args:
            name: Unique identifier for this channel.
            agent: Optional Agent instance for message processing.
        """
        self.name: str = name
        self.agent: Optional[Any] = agent
        self._is_running: bool = False
        self._message_callback: Optional[Callable[[str, str], Awaitable[None]]] = None
    
    @abstractmethod
    async def start(self) -> None:
        """Start the channel and begin listening for messages."""
        pass
    
    @abstractmethod
    async def stop(self) -> None:
        """Stop the channel and cleanup resources."""
        pass
    
    @abstractmethod
    async def send_message(self, to: str, content: str) -> bool:
        """Send a message to a specific recipient.
        
        Args:
            to: Recipient identifier (format depends on channel).
            content: Message text to send.
            
        Returns:
            True if message was sent successfully, False otherwise.
        """
        pass
    
    @abstractmethod
    def on_message(self, callback: Callable[[str, str], Awaitable[None]]) -> None:
        """Register a callback for incoming messages.
        
        Args:
            callback: Async function receiving (sender_id, message).
        """
        pass
    
    def __repr__(self) -> str:
        status = "running" if self._is_running else "stopped"
        return f"{self.__class__.__name__}({self.name}, {status})"


# Lazy import helpers - these avoid loading optional dependencies until needed
def _import_discord_channel():
    """Lazy import DiscordChannel to avoid discord.py dependency when not used."""
    try:
        from .discord import DiscordChannel
        return DiscordChannel
    except ImportError as exc:
        raise ImportError(
            "Discord support requires 'discord.py'. "
            "Install with: pip install 'discord.py[voice]'"
        ) from exc


def _import_telegram_channel():
    """Lazy import TelegramChannel to avoid python-telegram-bot dependency when not used."""
    try:
        from .telegram import TelegramChannel
        return TelegramChannel
    except ImportError as exc:
        raise ImportError(
            "Telegram support requires 'python-telegram-bot'. "
            "Install with: pip install python-telegram-bot"
        ) from exc


def _import_http_api_channel():
    """Lazy import HttpApiChannel (usually available since it uses standard deps)."""
    from .http_api import HttpApiChannel
    return HttpApiChannel


# Channel registry for lazy loading
_CHANNEL_IMPORTERS = {
    "discord": _import_discord_channel,
    "telegram": _import_telegram_channel,
    "http_api": _import_http_api_channel,
}


def get_channel_class(channel_type: str):
    """Get a channel class by type name (lazy import).
    
    Args:
        channel_type: Channel type identifier ('discord', 'telegram', 'http_api').
        
    Returns:
        Channel class (not instance).
        
    Raises:
        ValueError: If channel_type is unknown.
        ImportError: If required dependencies are missing.
    """
    importer = _CHANNEL_IMPORTERS.get(channel_type.lower())
    if importer is None:
        raise ValueError(f"Unknown channel type: '{channel_type}'. "
                        f"Available: {list(_CHANNEL_IMPORTERS.keys())}")
    return importer()


def create_channel(channel_type: str, **kwargs):
    """Factory function to create a channel instance (lazy import).
    
    Args:
        channel_type: Channel type identifier.
        **kwargs: Constructor arguments for the channel.
        
    Returns:
        Channel instance.
    """
    channel_class = get_channel_class(channel_type)
    return channel_class(**kwargs)


# For backwards compatibility, expose class references via module-level properties
# These will raise ImportError on access if dependencies are missing
class _LazyChannelAccessor:
    """Descriptor for lazy channel class access."""
    
    def __init__(self, channel_type: str):
        self.channel_type = channel_type
        self._cached_class = None
    
    def __get__(self, obj, objtype=None):
        if self._cached_class is None:
            self._cached_class = get_channel_class(self.channel_type)
        return self._cached_class


# Module-level lazy accessors - these import on first access
DiscordChannel = _LazyChannelAccessor("discord")
TelegramChannel = _LazyChannelAccessor("telegram")
HttpApiChannel = _LazyChannelAccessor("http_api")


__all__ = [
    "Channel",
    "DiscordChannel",
    "HttpApiChannel", 
    "TelegramChannel",
    "get_channel_class",
    "create_channel",
]
