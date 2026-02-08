"""
Base sub-agent abstract class.

All sub-agents should inherit from this base class.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum, auto
from typing import Any, Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


class SubAgentCapability(Enum):
    """Capabilities that sub-agents can provide."""
    CONSTITUTIONAL_REVIEW = auto()    # Review decisions for ethics/policy
    DEEP_INTROSPECTION = auto()       # Analyze reasoning processes
    SELF_MODIFICATION = auto()         # Propose code improvements
    META_LEARNING = auto()             # Optimize learning strategies
    HEALING = auto()                   # Fix errors and issues
    VISUAL_MONITORING = auto()         # Analyze logs/screenshots


@dataclass
class SubAgentRequest:
    """Request to a sub-agent."""
    capability: SubAgentCapability
    context: Dict[str, Any]
    user_id: Optional[str] = None
    priority: int = 5  # 1-10, higher is more urgent


@dataclass
class SubAgentResponse:
    """Response from a sub-agent."""
    success: bool
    capability: SubAgentCapability
    result: Dict[str, Any]
    reasoning: Optional[str] = None
    confidence: float = 1.0
    metadata: Optional[Dict[str, Any]] = None


class BaseSubAgent(ABC):
    """
    Abstract base class for all sub-agents.
    
    Sub-agents are specialized agents that handle specific advanced tasks
    that the main agent delegates to them.
    """
    
    def __init__(self, name: str, enabled: bool = True):
        """Initialize sub-agent.
        
        Args:
            name: Name of the sub-agent
            enabled: Whether the sub-agent is enabled
        """
        self.name = name
        self.enabled = enabled
        self._logger = logging.getLogger(f"{__name__}.{name}")
    
    @abstractmethod
    async def can_handle(self, request: SubAgentRequest) -> bool:
        """Check if this sub-agent can handle the request.
        
        Args:
            request: The sub-agent request
            
        Returns:
            True if this sub-agent can handle the request
        """
        pass
    
    @abstractmethod
    async def process(self, request: SubAgentRequest) -> SubAgentResponse:
        """Process a request.
        
        Args:
            request: The sub-agent request
            
        Returns:
            Response from processing
        """
        pass
    
    @abstractmethod
    def get_capabilities(self) -> List[SubAgentCapability]:
        """Get list of capabilities this sub-agent provides.
        
        Returns:
            List of capabilities
        """
        pass
    
    def get_status(self) -> Dict[str, Any]:
        """Get sub-agent status.
        
        Returns:
            Status dictionary
        """
        return {
            "name": self.name,
            "enabled": self.enabled,
            "capabilities": [c.name for c in self.get_capabilities()]
        }
