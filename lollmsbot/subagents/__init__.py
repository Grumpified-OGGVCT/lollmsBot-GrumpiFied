"""
Sub-agent system for LollmsBot.

Sub-agents are specialized agents that handle specific tasks that require
advanced capabilities beyond normal chat interactions.
"""

from .base_subagent import BaseSubAgent, SubAgentCapability
from .rc2_subagent import RC2SubAgent

__all__ = [
    "BaseSubAgent",
    "SubAgentCapability",
    "RC2SubAgent",
]
