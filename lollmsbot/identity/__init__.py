"""
Identity Module - Cross-Channel User Identity Management

Manages user identities and sessions across multiple communication channels.
"""

from lollmsbot.identity.session_manager import (
    SessionManager,
    UserIdentity,
    Session,
    get_session_manager,
)

__all__ = [
    "SessionManager",
    "UserIdentity",
    "Session",
    "get_session_manager",
]
