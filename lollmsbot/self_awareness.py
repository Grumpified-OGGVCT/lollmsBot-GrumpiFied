"""
Self-Awareness Module - LollmsBot's Introspection & Meta-Cognition System

This module provides lollmsBot with the ability to be aware of and reflect on its own:
- Internal state (memory, context, goals)
- Decision-making processes (reasoning, confidence)
- Capabilities & limitations (what it can/cannot do)
- Behavior patterns (how it's acting)
- Performance metrics (how well it's functioning)

The self-awareness system is configurable with user-adjustable restraints to balance
introspection depth against resource usage and safety.
"""

from __future__ import annotations

import asyncio
import json
import logging
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from enum import Enum, auto
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Callable

logger = logging.getLogger("lollmsbot.self_awareness")


class AwarenessLevel(Enum):
    """
    Levels of self-awareness with different capabilities and resource usage.
    
    Higher levels provide deeper introspection but use more resources.
    Users can adjust this based on their needs and constraints.
    """
    MINIMAL = 0      # Basic state tracking only
    LOW = 2          # + Decision logging
    MODERATE = 5     # + Pattern recognition
    HIGH = 7         # + Real-time introspection
    MAXIMUM = 10     # + Full meta-cognition, reflection loops
    
    @property
    def description(self) -> str:
        """Get human-readable description of this awareness level."""
        descriptions = {
            AwarenessLevel.MINIMAL: "Basic state tracking (minimal overhead)",
            AwarenessLevel.LOW: "Decision logging (low overhead)",
            AwarenessLevel.MODERATE: "Pattern recognition (moderate overhead)",
            AwarenessLevel.HIGH: "Real-time introspection (higher overhead)",
            AwarenessLevel.MAXIMUM: "Full meta-cognition (highest overhead)",
        }
        return descriptions[self]
    
    @property
    def features_enabled(self) -> Set[str]:
        """Get features enabled at this awareness level."""
        features = {
            AwarenessLevel.MINIMAL: {"state_tracking"},
            AwarenessLevel.LOW: {"state_tracking", "decision_logging"},
            AwarenessLevel.MODERATE: {"state_tracking", "decision_logging", "pattern_recognition"},
            AwarenessLevel.HIGH: {"state_tracking", "decision_logging", "pattern_recognition", 
                                 "real_time_introspection", "confidence_tracking"},
            AwarenessLevel.MAXIMUM: {"state_tracking", "decision_logging", "pattern_recognition",
                                    "real_time_introspection", "confidence_tracking",
                                    "meta_cognition", "reflection_loops", "goal_tracking"},
        }
        return features[self]


@dataclass
class AwarenessConfig:
    """Configuration for self-awareness system."""
    
    # Core settings
    enabled: bool = True
    level: AwarenessLevel = AwarenessLevel.MODERATE
    
    # Feature toggles (can override level defaults)
    enable_state_tracking: bool = True
    enable_decision_logging: bool = True
    enable_pattern_recognition: bool = True
    enable_real_time_introspection: bool = False
    enable_confidence_tracking: bool = False
    enable_meta_cognition: bool = False
    enable_reflection_loops: bool = False
    enable_goal_tracking: bool = False
    
    # Resource limits
    max_introspection_depth: int = 3  # How many levels of meta-reasoning
    reflection_interval_seconds: float = 60.0  # How often to reflect
    max_decision_history: int = 1000  # Keep last N decisions
    max_pattern_memory: int = 500  # Keep last N patterns
    
    # Safety restraints
    introspection_timeout_seconds: float = 5.0  # Prevent infinite loops
    min_confidence_threshold: float = 0.3  # Below this, flag for review
    anomaly_detection_threshold: float = 0.7  # Above this, flag unusual behavior
    
    # Integration settings
    use_rc2_for_deep_introspection: bool = True
    log_introspection_results: bool = True
    report_to_heartbeat: bool = True
    
    @classmethod
    def from_env(cls) -> "AwarenessConfig":
        """Load configuration from environment variables."""
        import os
        
        def _get_bool(name: str, default: bool) -> bool:
            val = os.getenv(name)
            if val is None:
                return default
            return val.lower() in ("1", "true", "yes", "on")
        
        # Get level from environment
        level_str = os.getenv("SELF_AWARENESS_LEVEL", "MODERATE")
        try:
            level = AwarenessLevel[level_str.upper()]
        except KeyError:
            level = AwarenessLevel.MODERATE
            logger.warning(f"Invalid SELF_AWARENESS_LEVEL '{level_str}', using MODERATE")
        
        return cls(
            enabled=_get_bool("SELF_AWARENESS_ENABLED", True),
            level=level,
            enable_state_tracking=_get_bool("SELF_AWARENESS_STATE_TRACKING", True),
            enable_decision_logging=_get_bool("SELF_AWARENESS_DECISION_LOGGING", True),
            enable_pattern_recognition=_get_bool("SELF_AWARENESS_PATTERN_RECOGNITION", 
                                                level.value >= AwarenessLevel.MODERATE.value),
            enable_real_time_introspection=_get_bool("SELF_AWARENESS_REAL_TIME_INTROSPECTION",
                                                     level.value >= AwarenessLevel.HIGH.value),
            enable_confidence_tracking=_get_bool("SELF_AWARENESS_CONFIDENCE_TRACKING",
                                                level.value >= AwarenessLevel.HIGH.value),
            enable_meta_cognition=_get_bool("SELF_AWARENESS_META_COGNITION",
                                           level.value >= AwarenessLevel.MAXIMUM.value),
            enable_reflection_loops=_get_bool("SELF_AWARENESS_REFLECTION_LOOPS",
                                             level.value >= AwarenessLevel.MAXIMUM.value),
            enable_goal_tracking=_get_bool("SELF_AWARENESS_GOAL_TRACKING",
                                          level.value >= AwarenessLevel.MAXIMUM.value),
            max_introspection_depth=int(os.getenv("SELF_AWARENESS_MAX_DEPTH", "3")),
            reflection_interval_seconds=float(os.getenv("SELF_AWARENESS_REFLECTION_INTERVAL", "60.0")),
            max_decision_history=int(os.getenv("SELF_AWARENESS_MAX_DECISIONS", "1000")),
            introspection_timeout_seconds=float(os.getenv("SELF_AWARENESS_TIMEOUT", "5.0")),
            use_rc2_for_deep_introspection=_get_bool("SELF_AWARENESS_USE_RC2", True),
        )


@dataclass
class InternalState:
    """Snapshot of lollmsBot's internal state at a point in time."""
    timestamp: datetime
    
    # Core state
    active_contexts: List[str] = field(default_factory=list)
    current_goals: List[str] = field(default_factory=list)
    working_memory_size: int = 0
    active_skills: List[str] = field(default_factory=list)
    active_tools: List[str] = field(default_factory=list)
    
    # Cognitive state
    attention_focus: Optional[str] = None
    processing_load: float = 0.0  # 0.0-1.0
    confidence_level: float = 0.0  # 0.0-1.0
    
    # Behavioral state
    interaction_mode: str = "chat"  # chat, tool_use, skill_execution, introspection
    recent_actions: List[str] = field(default_factory=list)
    
    # Constraints & limits
    active_restraints: List[str] = field(default_factory=list)
    resource_usage: Dict[str, float] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        data = asdict(self)
        data["timestamp"] = self.timestamp.isoformat()
        return data


@dataclass
class DecisionRecord:
    """Record of a decision made by lollmsBot."""
    decision_id: str
    timestamp: datetime
    decision_type: str  # "tool_use", "response_generation", "skill_activation", etc.
    decision: str
    context: Dict[str, Any]
    reasoning: Optional[str] = None
    confidence: float = 0.5
    alternatives_considered: List[str] = field(default_factory=list)
    outcome: Optional[str] = None  # Set after decision is executed
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = asdict(self)
        data["timestamp"] = self.timestamp.isoformat()
        return data


@dataclass
class BehaviorPattern:
    """Recognized pattern in lollmsBot's behavior."""
    pattern_id: str
    pattern_type: str  # "response_style", "tool_preference", "error_handling", etc.
    description: str
    frequency: int = 1
    first_observed: datetime = field(default_factory=datetime.now)
    last_observed: datetime = field(default_factory=datetime.now)
    confidence: float = 0.5
    examples: List[str] = field(default_factory=list)


@dataclass
class IntrospectionResult:
    """Result of an introspection query."""
    query: str
    timestamp: datetime
    depth: int  # How many levels of meta-reasoning
    findings: Dict[str, Any]
    confidence: float
    took_seconds: float
    

class SelfAwarenessManager:
    """
    Manages lollmsBot's self-awareness and introspection capabilities.
    
    Provides methods for:
    - Tracking internal state
    - Logging decisions with reasoning
    - Recognizing behavioral patterns
    - Performing introspection on demand
    - Meta-cognitive reflection
    """
    
    def __init__(self, config: Optional[AwarenessConfig] = None):
        """Initialize the self-awareness manager.
        
        Args:
            config: Configuration, or None to load from environment
        """
        self.config = config or AwarenessConfig.from_env()
        
        # State tracking
        self._current_state: Optional[InternalState] = None
        self._state_history: List[InternalState] = []
        
        # Decision logging
        self._decision_history: List[DecisionRecord] = []
        self._decision_index: Dict[str, DecisionRecord] = {}
        
        # Pattern recognition
        self._recognized_patterns: List[BehaviorPattern] = []
        self._pattern_index: Dict[str, BehaviorPattern] = {}
        
        # Meta-cognition
        self._active_goals: List[str] = []
        self._meta_thoughts: List[Dict[str, Any]] = []
        self._reflection_task: Optional[asyncio.Task] = None
        
        # Resource tracking
        self._introspection_count: int = 0
        self._last_reflection: datetime = datetime.now()
        
        logger.info(f"Self-awareness initialized: level={self.config.level.name}, "
                   f"features={len(self.config.level.features_enabled)}")
    
    def is_enabled(self, feature: str) -> bool:
        """Check if a specific feature is enabled.
        
        Args:
            feature: Feature name (e.g., "meta_cognition")
            
        Returns:
            True if feature is enabled
        """
        if not self.config.enabled:
            return False
        
        # Check explicit config override
        config_attr = f"enable_{feature}"
        if hasattr(self.config, config_attr):
            return getattr(self.config, config_attr)
        
        # Fall back to level-based features
        return feature in self.config.level.features_enabled
    
    def update_state(self, **kwargs) -> InternalState:
        """Update current internal state.
        
        Args:
            **kwargs: State fields to update
            
        Returns:
            Updated state snapshot
        """
        if not self.is_enabled("state_tracking"):
            return None
        
        # Create or update current state
        if self._current_state is None:
            self._current_state = InternalState(timestamp=datetime.now())
        
        # Update fields
        for key, value in kwargs.items():
            if hasattr(self._current_state, key):
                setattr(self._current_state, key, value)
        
        self._current_state.timestamp = datetime.now()
        
        # Save to history
        self._state_history.append(self._current_state)
        if len(self._state_history) > 100:  # Keep last 100
            self._state_history.pop(0)
        
        return self._current_state
    
    def get_current_state(self) -> Optional[InternalState]:
        """Get current internal state snapshot.
        
        Returns:
            Current state or None if tracking disabled
        """
        return self._current_state
    
    def log_decision(self,
                    decision: str,
                    decision_type: str,
                    context: Optional[Dict[str, Any]] = None,
                    reasoning: Optional[str] = None,
                    confidence: float = 0.5,
                    alternatives: Optional[List[str]] = None) -> str:
        """Log a decision made by lollmsBot.
        
        Args:
            decision: The decision made
            decision_type: Type of decision
            context: Context in which decision was made
            reasoning: Why this decision was made
            confidence: Confidence level (0.0-1.0)
            alternatives: Other options considered
            
        Returns:
            Decision ID for later reference
        """
        if not self.is_enabled("decision_logging"):
            return ""
        
        import uuid
        decision_id = str(uuid.uuid4())
        
        record = DecisionRecord(
            decision_id=decision_id,
            timestamp=datetime.now(),
            decision_type=decision_type,
            decision=decision,
            context=context or {},
            reasoning=reasoning,
            confidence=confidence,
            alternatives_considered=alternatives or [],
        )
        
        self._decision_history.append(record)
        self._decision_index[decision_id] = record
        
        # Trim history if needed
        if len(self._decision_history) > self.config.max_decision_history:
            removed = self._decision_history.pop(0)
            del self._decision_index[removed.decision_id]
        
        # Check for low confidence
        if confidence < self.config.min_confidence_threshold:
            logger.warning(f"Low confidence decision: {decision_type} ({confidence:.2f})")
        
        return decision_id
    
    def update_decision_outcome(self, decision_id: str, outcome: str):
        """Update the outcome of a previous decision.
        
        Args:
            decision_id: ID of the decision
            outcome: What happened as a result
        """
        if decision_id in self._decision_index:
            self._decision_index[decision_id].outcome = outcome
    
    def get_decision_history(self, 
                            decision_type: Optional[str] = None,
                            limit: int = 10) -> List[DecisionRecord]:
        """Get recent decision history.
        
        Args:
            decision_type: Filter by type, or None for all
            limit: Maximum number to return
            
        Returns:
            List of recent decisions
        """
        decisions = self._decision_history
        
        if decision_type:
            decisions = [d for d in decisions if d.decision_type == decision_type]
        
        return decisions[-limit:]
    
    def recognize_pattern(self, 
                         pattern_type: str,
                         description: str,
                         examples: Optional[List[str]] = None,
                         confidence: float = 0.5) -> str:
        """Recognize and record a behavioral pattern.
        
        Args:
            pattern_type: Type of pattern
            description: What the pattern is
            examples: Example instances
            confidence: Confidence in pattern recognition
            
        Returns:
            Pattern ID
        """
        if not self.is_enabled("pattern_recognition"):
            return ""
        
        import uuid
        
        # Check if pattern already exists
        pattern_key = f"{pattern_type}:{description}"
        if pattern_key in self._pattern_index:
            # Update existing pattern
            pattern = self._pattern_index[pattern_key]
            pattern.frequency += 1
            pattern.last_observed = datetime.now()
            if examples:
                pattern.examples.extend(examples)
                pattern.examples = pattern.examples[-10:]  # Keep last 10
            return pattern.pattern_id
        
        # Create new pattern
        pattern_id = str(uuid.uuid4())
        pattern = BehaviorPattern(
            pattern_id=pattern_id,
            pattern_type=pattern_type,
            description=description,
            confidence=confidence,
            examples=examples or [],
        )
        
        self._recognized_patterns.append(pattern)
        self._pattern_index[pattern_key] = pattern
        
        # Trim if needed
        if len(self._recognized_patterns) > self.config.max_pattern_memory:
            removed = self._recognized_patterns.pop(0)
            pattern_key = f"{removed.pattern_type}:{removed.description}"
            if pattern_key in self._pattern_index:
                del self._pattern_index[pattern_key]
        
        logger.info(f"Recognized pattern: {pattern_type} - {description}")
        return pattern_id
    
    def get_recognized_patterns(self,
                               pattern_type: Optional[str] = None,
                               min_frequency: int = 1) -> List[BehaviorPattern]:
        """Get recognized behavioral patterns.
        
        Args:
            pattern_type: Filter by type, or None for all
            min_frequency: Minimum frequency to include
            
        Returns:
            List of patterns
        """
        patterns = self._recognized_patterns
        
        if pattern_type:
            patterns = [p for p in patterns if p.pattern_type == pattern_type]
        
        patterns = [p for p in patterns if p.frequency >= min_frequency]
        
        return sorted(patterns, key=lambda p: p.frequency, reverse=True)
    
    async def introspect(self, query: str, depth: int = 1) -> IntrospectionResult:
        """Perform introspection on internal state or processes.
        
        Args:
            query: What to introspect about
            depth: How many levels of meta-reasoning (1-max_depth)
            
        Returns:
            Introspection results
        """
        if not self.is_enabled("real_time_introspection"):
            return IntrospectionResult(
                query=query,
                timestamp=datetime.now(),
                depth=0,
                findings={"error": "Real-time introspection not enabled"},
                confidence=0.0,
                took_seconds=0.0
            )
        
        start_time = time.time()
        depth = min(depth, self.config.max_introspection_depth)
        
        try:
            # Perform introspection based on query
            findings = await asyncio.wait_for(
                self._perform_introspection(query, depth),
                timeout=self.config.introspection_timeout_seconds
            )
            
            self._introspection_count += 1
            
            result = IntrospectionResult(
                query=query,
                timestamp=datetime.now(),
                depth=depth,
                findings=findings,
                confidence=findings.get("confidence", 0.5),
                took_seconds=time.time() - start_time
            )
            
            if self.config.log_introspection_results:
                logger.info(f"Introspection completed: {query} (depth={depth}, "
                          f"took={result.took_seconds:.2f}s)")
            
            return result
            
        except asyncio.TimeoutError:
            logger.warning(f"Introspection timed out: {query}")
            return IntrospectionResult(
                query=query,
                timestamp=datetime.now(),
                depth=depth,
                findings={"error": "Timeout"},
                confidence=0.0,
                took_seconds=time.time() - start_time
            )
    
    async def _perform_introspection(self, query: str, depth: int) -> Dict[str, Any]:
        """Internal method to perform introspection.
        
        This is where the actual introspection logic lives. Can be extended
        to use RC2 sub-agent for deeper analysis.
        """
        findings = {}
        
        # Analyze query type
        query_lower = query.lower()
        
        if "state" in query_lower or "status" in query_lower:
            # Query about current state
            state = self.get_current_state()
            if state:
                findings["current_state"] = state.to_dict()
                findings["confidence"] = 0.9
            else:
                findings["error"] = "State tracking not available"
                findings["confidence"] = 0.0
        
        elif "decision" in query_lower or "why" in query_lower:
            # Query about decisions
            recent_decisions = self.get_decision_history(limit=5)
            findings["recent_decisions"] = [d.to_dict() for d in recent_decisions]
            findings["confidence"] = 0.8
        
        elif "pattern" in query_lower or "behavior" in query_lower:
            # Query about patterns
            patterns = self.get_recognized_patterns()
            findings["recognized_patterns"] = [
                {
                    "type": p.pattern_type,
                    "description": p.description,
                    "frequency": p.frequency,
                    "confidence": p.confidence
                }
                for p in patterns[:10]
            ]
            findings["confidence"] = 0.7
        
        elif "capability" in query_lower or "can i" in query_lower:
            # Query about capabilities
            findings["awareness_level"] = self.config.level.name
            findings["enabled_features"] = list(self.config.level.features_enabled)
            findings["confidence"] = 1.0
        
        else:
            # Generic introspection
            findings["awareness_level"] = self.config.level.name
            findings["introspection_count"] = self._introspection_count
            findings["confidence"] = 0.5
        
        # Add meta-layer for depth > 1
        if depth > 1 and self.is_enabled("meta_cognition"):
            meta_findings = await self._meta_reflect(findings, depth - 1)
            findings["meta_analysis"] = meta_findings
        
        return findings
    
    async def _meta_reflect(self, findings: Dict[str, Any], depth: int) -> Dict[str, Any]:
        """Perform meta-cognition on introspection findings.
        
        Args:
            findings: Results from previous introspection level
            depth: Remaining depth
            
        Returns:
            Meta-cognitive insights
        """
        if depth <= 0:
            return {}
        
        meta = {
            "reflection_on": "introspection_findings",
            "depth_remaining": depth,
            "insight": f"Analyzed {len(findings)} aspects of internal state",
        }
        
        # Could extend this to use RC2 for deeper analysis
        if self.config.use_rc2_for_deep_introspection and depth > 1:
            meta["note"] = "Deep introspection can use RC2 sub-agent"
        
        return meta
    
    def start_reflection_loop(self):
        """Start periodic self-reflection background task."""
        if not self.is_enabled("reflection_loops"):
            return
        
        if self._reflection_task is not None:
            logger.warning("Reflection loop already running")
            return
        
        async def reflection_loop():
            while True:
                try:
                    await asyncio.sleep(self.config.reflection_interval_seconds)
                    await self._periodic_reflection()
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    logger.error(f"Error in reflection loop: {e}")
        
        self._reflection_task = asyncio.create_task(reflection_loop())
        logger.info("Started reflection loop")
    
    def stop_reflection_loop(self):
        """Stop periodic self-reflection."""
        if self._reflection_task:
            self._reflection_task.cancel()
            self._reflection_task = None
            logger.info("Stopped reflection loop")
    
    async def _periodic_reflection(self):
        """Perform periodic self-reflection."""
        self._last_reflection = datetime.now()
        
        # Analyze recent activity
        recent_decisions = self.get_decision_history(limit=20)
        recent_patterns = self.get_recognized_patterns(min_frequency=2)
        
        reflection = {
            "timestamp": datetime.now().isoformat(),
            "decisions_made": len(recent_decisions),
            "patterns_recognized": len(recent_patterns),
            "average_confidence": sum(d.confidence for d in recent_decisions) / len(recent_decisions) if recent_decisions else 0.0,
        }
        
        self._meta_thoughts.append(reflection)
        if len(self._meta_thoughts) > 100:
            self._meta_thoughts.pop(0)
        
        logger.debug(f"Periodic reflection: {reflection}")
    
    def get_meta_thoughts(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent meta-cognitive reflections.
        
        Args:
            limit: Maximum number to return
            
        Returns:
            Recent meta-thoughts
        """
        return self._meta_thoughts[-limit:]
    
    def get_status_report(self) -> Dict[str, Any]:
        """Get comprehensive status report of self-awareness system.
        
        Returns:
            Status dictionary
        """
        return {
            "enabled": self.config.enabled,
            "awareness_level": self.config.level.name,
            "enabled_features": list(self.config.level.features_enabled),
            "current_state": self._current_state.to_dict() if self._current_state else None,
            "decision_count": len(self._decision_history),
            "pattern_count": len(self._recognized_patterns),
            "introspection_count": self._introspection_count,
            "last_reflection": self._last_reflection.isoformat(),
            "reflection_loop_active": self._reflection_task is not None,
        }


# Global instance
_awareness_manager: Optional[SelfAwarenessManager] = None


def get_awareness_manager() -> SelfAwarenessManager:
    """Get or create the global self-awareness manager.
    
    Returns:
        SelfAwarenessManager instance
    """
    global _awareness_manager
    if _awareness_manager is None:
        _awareness_manager = SelfAwarenessManager()
    return _awareness_manager
