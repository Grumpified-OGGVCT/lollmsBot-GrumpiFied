"""lollmsBot package."""

# Export core components
__all__ = [
    "config",
    "lollms_client", 
    "gateway",
    # Exceptions for error handling
    "ValidationError",
    "AgentError",
    "ToolError",
    "StorageError",
]

# Import exceptions for convenience
from lollmsbot.agent import ValidationError, AgentError, ToolError
from lollmsbot.storage.sqlite_store import StorageError
