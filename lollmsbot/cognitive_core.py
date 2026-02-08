"""
Cognitive Core - Dual-Process System for Reflective Consciousness Layer v2.0 (RCL-2)

Implements Kahneman's System 1/System 2 dual-process theory adapted for LLM agents:
- System 1: Fast, intuitive, subsymbolic self-awareness
- System 2: Slow, analytical, deliberative metacognition

Architecture based on Global Workspace Theory of consciousness.
"""

from __future__ import annotations

import asyncio
import logging
import time
import numpy as np
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Tuple, Callable
from collections import deque

logger = logging.getLogger("lollmsbot.cognitive_core")


class CognitiveMarker(Enum):
    """Somatic markers - qualitative 'gut feelings' from subsymbolic processing."""
    CONFIDENT = auto()      # Low entropy, high probability
    UNCERTAIN = auto()      # High entropy, flat distribution
    ANXIOUS = auto()        # High uncertainty + high stakes
    CURIOUS = auto()        # Knowledge gap detected
    CONFLICTED = auto()     # Multiple competing hypotheses
    CLEAR = auto()          # Single dominant interpretation
    FAMILIAR = auto()       # Pattern matches past experience
    NOVEL = auto()          # No similar past patterns


class CognitiveJump(Enum):
    """Types of transitions in latent space during reasoning."""
    SMOOTH = auto()         # Incremental, logical progression
    ASSOCIATIVE = auto()    # Metaphor, analogy, creative leap
    DISCONTINUOUS = auto()  # Topic change, context switch
    RECURSIVE = auto()      # Meta-level reasoning about reasoning
    REGRESSIVE = auto()     # Backtracking, error correction


@dataclass
class AttentionSnapshot:
    """Snapshot of attention distribution at a moment in time."""
    timestamp: datetime
    focus_tokens: List[str]  # Tokens receiving high attention
    focus_weights: List[float]  # Attention weights (0.0-1.0)
    context_span: int  # Total context window size
    attention_entropy: float  # Shannon entropy of attention distribution
    peak_positions: List[int]  # Token positions with highest attention


@dataclass
class EntropyGradient:
    """Uncertainty levels across the context window."""
    timestamp: datetime
    position_entropies: List[float]  # Entropy at each position
    mean_entropy: float
    max_entropy: float
    gradient_magnitude: float  # Rate of entropy change
    high_uncertainty_regions: List[Tuple[int, int]]  # (start, end) positions
    
    def to_somatic_marker(self) -> CognitiveMarker:
        """Convert entropy metrics to qualitative feeling."""
        if self.mean_entropy < 0.3:
            return CognitiveMarker.CONFIDENT
        elif self.mean_entropy > 0.7:
            return CognitiveMarker.UNCERTAIN
        elif self.max_entropy > 0.8 and self.gradient_magnitude > 0.5:
            return CognitiveMarker.ANXIOUS
        elif 0.4 < self.mean_entropy < 0.6:
            return CognitiveMarker.CURIOUS
        else:
            return CognitiveMarker.CLEAR


@dataclass
class LatentTrajectory:
    """Movement through embedding space during reasoning."""
    timestamp: datetime
    positions: List[np.ndarray]  # Sequence of embedding vectors
    distances: List[float]  # Euclidean distances between consecutive positions
    jump_type: CognitiveJump
    smoothness_score: float  # 0.0=discontinuous, 1.0=perfectly smooth
    
    def classify_jump(self) -> CognitiveJump:
        """Classify the type of cognitive transition."""
        if not self.distances:
            return CognitiveJump.SMOOTH
        
        mean_dist = np.mean(self.distances)
        max_dist = np.max(self.distances)
        
        if max_dist > 3 * mean_dist:
            return CognitiveJump.DISCONTINUOUS
        elif self.smoothness_score > 0.8:
            return CognitiveJump.SMOOTH
        elif 0.5 < self.smoothness_score <= 0.8:
            return CognitiveJump.ASSOCIATIVE
        else:
            return CognitiveJump.RECURSIVE


@dataclass
class System1State:
    """Current state of System 1 (intuitive) processing."""
    
    # Subsymbolic monitoring
    current_attention: Optional[AttentionSnapshot] = None
    current_entropy: Optional[EntropyGradient] = None
    current_trajectory: Optional[LatentTrajectory] = None
    
    # Somatic markers (gut feelings)
    active_markers: List[CognitiveMarker] = field(default_factory=list)
    marker_strengths: Dict[CognitiveMarker, float] = field(default_factory=dict)
    
    # Reflexive monitoring state
    processing_load: float = 0.0  # 0.0-1.0
    cognitive_temperature: float = 0.5  # 0.0=rigid, 1.0=chaotic
    
    def get_dominant_feeling(self) -> Optional[CognitiveMarker]:
        """Get the strongest somatic marker."""
        if not self.marker_strengths:
            return None
        return max(self.marker_strengths, key=self.marker_strengths.get)


class SomaticMarkerEngine:
    """
    Converts technical metrics (perplexity, entropy, attention) into
    qualitative 'gut feelings' that influence Guardian/Heartbeat systems.
    """
    
    def __init__(self):
        self.marker_history: deque = deque(maxlen=100)
        self.marker_thresholds = {
            CognitiveMarker.CONFIDENT: ("low_entropy", 0.3),
            CognitiveMarker.UNCERTAIN: ("high_entropy", 0.7),
            CognitiveMarker.ANXIOUS: ("high_gradient", 0.5),
            CognitiveMarker.CURIOUS: ("medium_entropy", 0.5),
        }
    
    def generate_marker(self, 
                       entropy: Optional[EntropyGradient] = None,
                       attention: Optional[AttentionSnapshot] = None,
                       trajectory: Optional[LatentTrajectory] = None) -> Tuple[CognitiveMarker, float]:
        """
        Generate a somatic marker from current metrics.
        
        Returns:
            (marker, strength) tuple
        """
        markers = []
        strengths = []
        
        # From entropy
        if entropy:
            marker = entropy.to_somatic_marker()
            strength = abs(entropy.mean_entropy - 0.5) * 2  # 0.0-1.0
            markers.append(marker)
            strengths.append(strength)
        
        # From attention
        if attention and attention.attention_entropy:
            if attention.attention_entropy < 0.3:
                markers.append(CognitiveMarker.CLEAR)
                strengths.append(1.0 - attention.attention_entropy / 0.3)
            elif attention.attention_entropy > 0.7:
                markers.append(CognitiveMarker.CONFLICTED)
                strengths.append((attention.attention_entropy - 0.7) / 0.3)
        
        # From trajectory
        if trajectory:
            if trajectory.jump_type == CognitiveJump.DISCONTINUOUS:
                markers.append(CognitiveMarker.NOVEL)
                strengths.append(1.0 - trajectory.smoothness_score)
            elif trajectory.jump_type == CognitiveJump.SMOOTH:
                markers.append(CognitiveMarker.FAMILIAR)
                strengths.append(trajectory.smoothness_score)
        
        # Return dominant marker
        if markers and strengths:
            idx = np.argmax(strengths)
            result = (markers[idx], strengths[idx])
            self.marker_history.append(result)
            return result
        
        return (CognitiveMarker.CLEAR, 0.5)
    
    def get_marker_trend(self, window: int = 10) -> Optional[CognitiveMarker]:
        """Get most common marker over recent history."""
        if len(self.marker_history) < window:
            return None
        
        recent = list(self.marker_history)[-window:]
        marker_counts = {}
        for marker, _ in recent:
            marker_counts[marker] = marker_counts.get(marker, 0) + 1
        
        return max(marker_counts, key=marker_counts.get)


@dataclass
class CounterfactualPath:
    """One possible execution path for a decision."""
    path_type: str  # "optimistic", "pessimistic", "alternative"
    predicted_outcome: str
    confidence: float
    expected_utility: float
    risk_factors: List[str]
    opportunities: List[str]
    execution_steps: List[str]
    
    def score(self, risk_tolerance: float = 0.5) -> float:
        """Calculate overall path score balancing utility and risk."""
        risk_penalty = len(self.risk_factors) * (1.0 - risk_tolerance)
        opportunity_bonus = len(self.opportunities) * risk_tolerance
        return self.expected_utility * self.confidence + opportunity_bonus - risk_penalty


@dataclass
class EpistemicStatus:
    """Epistemic metadata for beliefs, decisions, and memories."""
    
    # Source reliability
    source_type: str  # "web_search", "training_data", "user_claim", "hallucination"
    reliability_score: float  # 0.0-1.0
    
    # Temporal decay
    created_at: datetime
    last_validated: datetime
    half_life_hours: float  # Knowledge decay rate
    
    # Logical structure
    supports: List[str] = field(default_factory=list)  # IDs of supporting beliefs
    supported_by: List[str] = field(default_factory=list)  # IDs this supports
    contradicts: List[str] = field(default_factory=list)  # IDs of contradictions
    
    # Verification status
    verification_count: int = 0
    contradiction_count: int = 0
    
    def current_confidence(self) -> float:
        """Calculate current confidence considering decay."""
        hours_elapsed = (datetime.now() - self.last_validated).total_seconds() / 3600
        decay_factor = 0.5 ** (hours_elapsed / self.half_life_hours)
        return self.reliability_score * decay_factor
    
    def is_contradicted(self) -> bool:
        """Check if this belief has been contradicted."""
        return len(self.contradicts) > 0 or self.contradiction_count > 0


@dataclass
class System2State:
    """Current state of System 2 (analytical) processing."""
    
    # Counterfactual simulation
    active_simulations: List[CounterfactualPath] = field(default_factory=list)
    selected_path: Optional[CounterfactualPath] = None
    
    # Epistemic tracking
    belief_graph: Dict[str, EpistemicStatus] = field(default_factory=dict)
    active_contradictions: List[Tuple[str, str]] = field(default_factory=list)
    
    # Resource allocation
    allocated_ms: float = 0.0
    used_ms: float = 0.0
    recursion_depth: int = 0
    
    def add_belief(self, belief_id: str, status: EpistemicStatus):
        """Add or update a belief in the epistemic graph."""
        self.belief_graph[belief_id] = status
    
    def check_contradictions(self) -> List[Tuple[str, str]]:
        """Scan for logical contradictions in belief graph."""
        contradictions = []
        
        for id1, status1 in self.belief_graph.items():
            for id2 in status1.contradicts:
                if id2 in self.belief_graph:
                    contradictions.append((id1, id2))
        
        self.active_contradictions = contradictions
        return contradictions
    
    def cascade_invalidate(self, belief_id: str) -> List[str]:
        """Invalidate a belief and all beliefs that depend on it."""
        invalidated = [belief_id]
        
        if belief_id not in self.belief_graph:
            return invalidated
        
        # Find all beliefs supported by this one
        status = self.belief_graph[belief_id]
        for supported_id in status.supports:
            if supported_id in self.belief_graph:
                invalidated.extend(self.cascade_invalidate(supported_id))
        
        return list(set(invalidated))


class CognitiveCore:
    """
    Dual-process cognitive architecture integrating System 1 (fast/intuitive)
    and System 2 (slow/analytical) processing.
    """
    
    def __init__(self, 
                 enable_system1: bool = True,
                 enable_system2: bool = True):
        self.enable_system1 = enable_system1
        self.enable_system2 = enable_system2
        
        # System states
        self.system1 = System1State()
        self.system2 = System2State()
        
        # Engines
        self.somatic_engine = SomaticMarkerEngine()
        
        # Performance tracking
        self._system1_calls = 0
        self._system2_calls = 0
        self._system1_time_ms = 0.0
        self._system2_time_ms = 0.0
        self._system2_escalations = 0
        self._total_processing_ms = 0.0
        
        logger.info(f"CognitiveCore initialized (S1={enable_system1}, S2={enable_system2})")
    
    @property
    def system1_calls(self) -> int:
        """Get number of System 1 calls."""
        return self._system1_calls
    
    @property
    def system2_calls(self) -> int:
        """Get number of System 2 calls."""
        return self._system2_calls
    
    @property
    def system1_time_ms(self) -> float:
        """Get total System 1 processing time in ms."""
        return self._system1_time_ms
    
    @property
    def system2_time_ms(self) -> float:
        """Get total System 2 processing time in ms."""
        return self._system2_time_ms
    
    @property
    def system2_escalations(self) -> int:
        """Get number of System 2 escalations."""
        return self._system2_escalations
    
    async def process_system1(self,
                             entropy: Optional[EntropyGradient] = None,
                             attention: Optional[AttentionSnapshot] = None,
                             trajectory: Optional[LatentTrajectory] = None) -> System1State:
        """
        Fast, intuitive processing (System 1).
        Updates subsymbolic monitoring and generates somatic markers.
        """
        if not self.enable_system1:
            return self.system1
        
        start = time.time()
        self._system1_calls += 1
        
        # Update monitoring state
        if entropy:
            self.system1.current_entropy = entropy
        if attention:
            self.system1.current_attention = attention
        if trajectory:
            self.system1.current_trajectory = trajectory
        
        # Generate somatic marker
        marker, strength = self.somatic_engine.generate_marker(
            entropy, attention, trajectory
        )
        
        self.system1.active_markers.append(marker)
        self.system1.marker_strengths[marker] = strength
        
        # Keep only recent markers
        if len(self.system1.active_markers) > 10:
            old_marker = self.system1.active_markers.pop(0)
            if old_marker in self.system1.marker_strengths:
                del self.system1.marker_strengths[old_marker]
        
        elapsed = (time.time() - start) * 1000
        self._system1_time_ms += elapsed
        self._total_processing_ms += elapsed
        
        logger.debug(f"System1 processed in {elapsed:.1f}ms, marker={marker.name}")
        
        return self.system1
    
    async def process_system2(self,
                             decision: str,
                             context: Dict[str, Any],
                             allocated_ms: float = 300.0) -> System2State:
        """
        Slow, analytical processing (System 2).
        Performs counterfactual simulation and epistemic analysis.
        """
        if not self.enable_system2:
            return self.system2
        
        start = time.time()
        self._system2_calls += 1
        self.system2.allocated_ms = allocated_ms
        
        # Generate 3 counterfactual paths
        paths = await self._generate_counterfactual_paths(decision, context)
        self.system2.active_simulations = paths
        
        # Select best path based on expected utility
        if paths:
            self.system2.selected_path = max(paths, key=lambda p: p.score())
        
        # Check for contradictions in belief graph
        contradictions = self.system2.check_contradictions()
        
        elapsed = (time.time() - start) * 1000
        self.system2.used_ms = elapsed
        self._system2_time_ms += elapsed
        self._total_processing_ms += elapsed
        
        logger.debug(f"System2 processed in {elapsed:.1f}ms, paths={len(paths)}, contradictions={len(contradictions)}")
        
        return self.system2
    
    async def _generate_counterfactual_paths(self,
                                           decision: str,
                                           context: Dict[str, Any]) -> List[CounterfactualPath]:
        """Generate optimistic, pessimistic, and alternative execution paths."""
        paths = []
        
        # Optimistic path
        paths.append(CounterfactualPath(
            path_type="optimistic",
            predicted_outcome="Success with ideal conditions",
            confidence=0.7,
            expected_utility=0.9,
            risk_factors=["optimism_bias"],
            opportunities=["ideal_conditions", "best_case_scenario"],
            execution_steps=["execute", "succeed", "benefit"]
        ))
        
        # Pessimistic path
        paths.append(CounterfactualPath(
            path_type="pessimistic",
            predicted_outcome="Failure or complications",
            confidence=0.6,
            expected_utility=0.2,
            risk_factors=["worst_case", "murphy_law", "complications"],
            opportunities=[],
            execution_steps=["execute", "encounter_issues", "recover"]
        ))
        
        # Alternative path
        paths.append(CounterfactualPath(
            path_type="alternative",
            predicted_outcome="Different approach with moderate success",
            confidence=0.75,
            expected_utility=0.7,
            risk_factors=["unfamiliar_approach"],
            opportunities=["novel_solution", "learning_opportunity"],
            execution_steps=["alternative_approach", "moderate_success"]
        ))
        
        return paths
    
    def get_cognitive_state(self) -> Dict[str, Any]:
        """Get comprehensive cognitive state summary."""
        return {
            "system1": {
                "enabled": self.enable_system1,
                "dominant_feeling": self.system1.get_dominant_feeling().name if self.system1.get_dominant_feeling() else None,
                "active_markers": [m.name for m in self.system1.active_markers],
                "processing_load": self.system1.processing_load,
                "cognitive_temperature": self.system1.cognitive_temperature,
            },
            "system2": {
                "enabled": self.enable_system2,
                "active_simulations": len(self.system2.active_simulations),
                "selected_path": self.system2.selected_path.path_type if self.system2.selected_path else None,
                "belief_count": len(self.system2.belief_graph),
                "contradictions": len(self.system2.active_contradictions),
                "recursion_depth": self.system2.recursion_depth,
            },
            "performance": {
                "system1_calls": self._system1_calls,
                "system2_calls": self._system2_calls,
                "total_processing_ms": self._total_processing_ms,
            }
        }
    
    def should_escalate_to_system2(self) -> bool:
        """Decide if current situation requires System 2 engagement."""
        if not self.enable_system1:
            return True
        
        dominant = self.system1.get_dominant_feeling()
        
        # Escalate on uncertainty, anxiety, conflict
        if dominant in [CognitiveMarker.UNCERTAIN, 
                       CognitiveMarker.ANXIOUS,
                       CognitiveMarker.CONFLICTED]:
            return True
        
        # Escalate on high entropy
        if self.system1.current_entropy:
            if self.system1.current_entropy.mean_entropy > 0.7:
                return True
        
        return False


# Global instance
_cognitive_core: Optional[CognitiveCore] = None


def get_cognitive_core() -> CognitiveCore:
    """Get or create the global cognitive core instance."""
    global _cognitive_core
    if _cognitive_core is None:
        _cognitive_core = CognitiveCore()
    return _cognitive_core
