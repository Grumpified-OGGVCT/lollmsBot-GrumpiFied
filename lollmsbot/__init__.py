"""
LollmsBot - A multi-channel AI agent platform.

LollmsBot provides a framework for building AI agents that can interact
across multiple communication channels including Telegram, Discord, and
web-based interfaces. It integrates with the LoLLMs ecosystem for
language model interactions.

Example:
    >>> from lollmsbot import Agent, Gateway, LollmsClient
    >>> agent = Agent()
    >>> gateway = Gateway(agent=agent)
    >>> gateway.start()
"""

__version__ = "0.1.0"

from lollmsbot.agent import Agent
from lollmsbot.gateway import Gateway
from lollmsbot.lollms_client import LollmsClient

__all__ = [
    "Agent",
    "Gateway",
    "LollmsClient",
    "__version__",
]