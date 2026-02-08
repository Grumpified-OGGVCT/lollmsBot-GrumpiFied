"""
Narrative Identity Engine - Temporal Continuity for RCL-2

Maintains biographical continuity and coherent self-identity across time.
Implements:
- Life story tracking with autobiographical memory
- Consolidation events during idle time (like sleep)
- Developmental stage tracking and learning curves
- Contradiction detection (prevents dissociative episodes)
- Cognitive maturity metrics

This ensures the agent has temporal continuity - a coherent sense of identity
that evolves consistently over time rather than being a different "person" each session.
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import threading
import time
from collections import deque
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Deque

logger = logging.getLogger("lollmsbot.narrative_identity")


class DevelopmentalStage(Enum):
    """Cognitive developmental stages (inspired by Piaget)."""
    NASCENT = "nascent"           # Just created, learning basics
    EARLY = "early"                # Basic patterns established
    INTERMEDIATE = "intermediate"  # Complex reasoning emerging
    MATURE = "mature"              # Sophisticated self-model
    EXPERT = "expert"              # Deep expertise in domain


@dataclass
class BiographicalEvent:
    """A significant event in the agent's life story."""
    timestamp: datetime
    event_type: str  # interaction, learning, error, achievement, etc.
    description: str
    significance: float  # 0.0-1.0, how important this was
    emotional_valence: float  # -1.0 to 1.0, negative to positive
    consolidated: bool = False
    event_id: str = field(default_factory=lambda: hashlib.sha256(
        f"{datetime.now().isoformat()}{time.time()}".encode()
    ).hexdigest()[:16])
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dict."""
        return {
            "timestamp": self.timestamp.isoformat(),
            "event_type": self.event_type,
            "description": self.description,
            "significance": self.significance,
            "emotional_valence": self.emotional_valence,
            "consolidated": self.consolidated,
            "event_id": self.event_id,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> BiographicalEvent:
        """Deserialize from dict."""
        data["timestamp"] = datetime.fromisoformat(data["timestamp"])
        return cls(**data)


@dataclass
class ConsolidationReport:
    """Report from a consolidation event."""
    timestamp: datetime
    events_consolidated: int
    patterns_identified: List[str]
    contradictions_detected: int
    stage_transition: Optional[str] = None  # e.g., "early -> intermediate"
    consolidation_duration: float = 0.0  # seconds


class NarrativeIdentityEngine:
    """
    Manages the agent's life story and temporal continuity.
    
    Maintains:
    1. Recent events buffer (fast access)
    2. Consolidated life story (long-term)
    3. Developmental stage tracking
    4. Contradiction detection
    5. Identity coherence metrics
    """
    
    def __init__(
        self,
        storage_path: Optional[str] = None,
        buffer_size: int = 100,
        consolidation_interval: int = 3600,  # 1 hour default
    ):
        """
        Initialize narrative identity engine.
        
        Args:
            storage_path: Where to persist life story (default: ~/.lollmsbot/narrative/)
            buffer_size: How many recent events to keep in memory
            consolidation_interval: Seconds between consolidation events
        """
        self.storage_path = Path(storage_path or os.path.expanduser("~/.lollmsbot/narrative"))
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        self.buffer_size = buffer_size
        self.consolidation_interval = consolidation_interval
        
        # Recent events buffer (fast access)
        self.recent_events: Deque[BiographicalEvent] = deque(maxlen=buffer_size)
        
        # Consolidated life story (persisted)
        self.life_story: List[BiographicalEvent] = []
        
        # Developmental tracking
        self.current_stage = DevelopmentalStage.NASCENT
        self.stage_transitions: List[Dict[str, Any]] = []
        self.interaction_count = 0
        self.successful_tasks = 0
        self.errors_encountered = 0
        
        # Consolidation tracking
        self.last_consolidation = datetime.now()
        self.consolidation_history: List[ConsolidationReport] = []
        
        # Thread safety
        self._lock = threading.RLock()
        
        # Load existing data
        self._load_from_disk()
        
        logger.info(
            f"NarrativeIdentityEngine initialized at stage={self.current_stage.value}, "
            f"events={len(self.life_story)}"
        )
    
    def record_event(
        self,
        event_type: str,
        description: str,
        significance: float = 0.5,
        emotional_valence: float = 0.0,
    ) -> str:
        """
        Record a new biographical event.
        
        Args:
            event_type: Type of event (interaction, learning, error, etc.)
            description: Human-readable description
            significance: 0.0-1.0, how important this is
            emotional_valence: -1.0 to 1.0, negative to positive
            
        Returns:
            event_id
        """
        with self._lock:
            event = BiographicalEvent(
                timestamp=datetime.now(),
                event_type=event_type,
                description=description,
                significance=min(1.0, max(0.0, significance)),
                emotional_valence=min(1.0, max(-1.0, emotional_valence)),
            )
            
            self.recent_events.append(event)
            
            # Update counters
            self.interaction_count += 1
            if event_type == "success":
                self.successful_tasks += 1
            elif event_type == "error":
                self.errors_encountered += 1
            
            # Check if consolidation is due
            if self._should_consolidate():
                self._trigger_consolidation()
            
            logger.debug(f"Recorded event: {event.event_type} - {event.description[:50]}")
            return event.event_id
    
    def get_life_story(
        self,
        since: Optional[datetime] = None,
        event_type: Optional[str] = None,
        min_significance: float = 0.0,
    ) -> List[BiographicalEvent]:
        """
        Query the agent's life story.
        
        Args:
            since: Only events after this time
            event_type: Filter by type
            min_significance: Minimum significance threshold
            
        Returns:
            List of events matching criteria
        """
        with self._lock:
            # Combine recent buffer and consolidated story
            all_events = list(self.recent_events) + self.life_story
            
            # Apply filters
            filtered = all_events
            
            if since:
                filtered = [e for e in filtered if e.timestamp >= since]
            
            if event_type:
                filtered = [e for e in filtered if e.event_type == event_type]
            
            filtered = [e for e in filtered if e.significance >= min_significance]
            
            # Sort by timestamp (most recent first)
            filtered.sort(key=lambda e: e.timestamp, reverse=True)
            
            return filtered
    
    def get_identity_summary(self) -> Dict[str, Any]:
        """
        Get a summary of the agent's current identity.
        
        Returns:
            Dict with developmental stage, key metrics, and story summary
        """
        with self._lock:
            total_events = len(self.recent_events) + len(self.life_story)
            
            # Calculate success rate
            success_rate = (
                self.successful_tasks / max(1, self.interaction_count)
                if self.interaction_count > 0
                else 0.0
            )
            
            # Get recent significant events
            recent_significant = [
                e for e in self.get_life_story(
                    since=datetime.now() - timedelta(days=7),
                    min_significance=0.7
                )
            ]
            
            return {
                "current_stage": self.current_stage.value,
                "total_events": total_events,
                "interaction_count": self.interaction_count,
                "successful_tasks": self.successful_tasks,
                "errors_encountered": self.errors_encountered,
                "success_rate": success_rate,
                "stage_transitions": len(self.stage_transitions),
                "last_consolidation": self.last_consolidation.isoformat(),
                "consolidations_performed": len(self.consolidation_history),
                "recent_significant_events": len(recent_significant),
                "identity_age_days": (datetime.now() - self._get_birth_time()).days,
            }
    
    def detect_contradictions(
        self,
        lookback_days: int = 30
    ) -> List[Dict[str, Any]]:
        """
        Detect contradictions in behavior or statements over time.
        
        Args:
            lookback_days: How far back to check
            
        Returns:
            List of detected contradictions
        """
        with self._lock:
            since = datetime.now() - timedelta(days=lookback_days)
            recent = self.get_life_story(since=since)
            
            contradictions = []
            
            # Check for contradictory emotional patterns
            # (e.g., consistently negative followed by consistently positive with no explanation)
            valences = [e.emotional_valence for e in recent]
            if len(valences) > 10:
                first_half_avg = sum(valences[:len(valences)//2]) / (len(valences)//2)
                second_half_avg = sum(valences[len(valences)//2:]) / (len(valences) - len(valences)//2)
                
                if abs(first_half_avg - second_half_avg) > 1.5:
                    contradictions.append({
                        "type": "emotional_shift",
                        "description": f"Large emotional shift detected: {first_half_avg:.2f} -> {second_half_avg:.2f}",
                        "severity": "medium"
                    })
            
            # Check for repeated errors of same type (not learning)
            error_events = [e for e in recent if e.event_type == "error"]
            if len(error_events) > 5:
                contradictions.append({
                    "type": "learning_stagnation",
                    "description": f"Repeated errors ({len(error_events)}) without improvement",
                    "severity": "high"
                })
            
            return contradictions
    
    def _should_consolidate(self) -> bool:
        """Check if consolidation is due."""
        return (datetime.now() - self.last_consolidation).total_seconds() >= self.consolidation_interval
    
    def _trigger_consolidation(self) -> ConsolidationReport:
        """
        Perform a consolidation event.
        
        Consolidates recent events into long-term story,
        identifies patterns, detects contradictions,
        and potentially triggers stage transitions.
        """
        with self._lock:
            start_time = time.time()
            logger.info("Starting consolidation event...")
            
            # Move events from buffer to consolidated story
            events_to_consolidate = list(self.recent_events)
            for event in events_to_consolidate:
                if not event.consolidated:
                    event.consolidated = True
                    self.life_story.append(event)
            
            # Identify patterns
            patterns = self._identify_patterns(events_to_consolidate)
            
            # Detect contradictions
            contradictions = self.detect_contradictions()
            
            # Check for stage transition
            stage_transition = self._check_stage_transition()
            
            # Create report
            report = ConsolidationReport(
                timestamp=datetime.now(),
                events_consolidated=len(events_to_consolidate),
                patterns_identified=patterns,
                contradictions_detected=len(contradictions),
                stage_transition=stage_transition,
                consolidation_duration=time.time() - start_time,
            )
            
            self.consolidation_history.append(report)
            self.last_consolidation = datetime.now()
            
            # Persist to disk
            self._save_to_disk()
            
            logger.info(
                f"Consolidation complete: {len(events_to_consolidate)} events, "
                f"{len(patterns)} patterns, {len(contradictions)} contradictions"
            )
            
            return report
    
    def _identify_patterns(self, events: List[BiographicalEvent]) -> List[str]:
        """Identify patterns in events."""
        patterns = []
        
        if not events:
            return patterns
        
        # Pattern: Consistent success
        successes = [e for e in events if e.event_type == "success"]
        if len(successes) > len(events) * 0.7:
            patterns.append("high_success_rate")
        
        # Pattern: Learning from errors
        errors = [e for e in events if e.event_type == "error"]
        if errors and successes and errors[0].timestamp < successes[-1].timestamp:
            patterns.append("error_recovery")
        
        # Pattern: Increasing complexity
        if len(events) > 5:
            early_sig = sum(e.significance for e in events[:len(events)//2]) / (len(events)//2)
            late_sig = sum(e.significance for e in events[len(events)//2:]) / (len(events) - len(events)//2)
            if late_sig > early_sig * 1.2:
                patterns.append("increasing_complexity")
        
        return patterns
    
    def _check_stage_transition(self) -> Optional[str]:
        """Check if agent should transition to next developmental stage."""
        # Simple heuristic based on interactions and success rate
        success_rate = self.successful_tasks / max(1, self.interaction_count)
        
        old_stage = self.current_stage
        new_stage = old_stage
        
        if self.current_stage == DevelopmentalStage.NASCENT and self.interaction_count > 50:
            new_stage = DevelopmentalStage.EARLY
        elif self.current_stage == DevelopmentalStage.EARLY and self.interaction_count > 200 and success_rate > 0.7:
            new_stage = DevelopmentalStage.INTERMEDIATE
        elif self.current_stage == DevelopmentalStage.INTERMEDIATE and self.interaction_count > 500 and success_rate > 0.8:
            new_stage = DevelopmentalStage.MATURE
        elif self.current_stage == DevelopmentalStage.MATURE and self.interaction_count > 1000 and success_rate > 0.9:
            new_stage = DevelopmentalStage.EXPERT
        
        if new_stage != old_stage:
            self.current_stage = new_stage
            transition = {
                "from": old_stage.value,
                "to": new_stage.value,
                "timestamp": datetime.now().isoformat(),
                "interaction_count": self.interaction_count,
                "success_rate": success_rate,
            }
            self.stage_transitions.append(transition)
            logger.info(f"Stage transition: {old_stage.value} -> {new_stage.value}")
            return f"{old_stage.value} -> {new_stage.value}"
        
        return None
    
    def _get_birth_time(self) -> datetime:
        """Get the agent's birth time (first recorded event)."""
        with self._lock:
            if self.life_story:
                return min(e.timestamp for e in self.life_story)
            elif self.recent_events:
                return min(e.timestamp for e in self.recent_events)
            return datetime.now()
    
    def _save_to_disk(self):
        """Persist life story and metadata to disk."""
        try:
            # Save life story
            story_file = self.storage_path / "life_story.json"
            story_data = [e.to_dict() for e in self.life_story]
            with open(story_file, 'w') as f:
                json.dump(story_data, f, indent=2)
            
            # Save metadata
            meta_file = self.storage_path / "metadata.json"
            metadata = {
                "current_stage": self.current_stage.value,
                "stage_transitions": self.stage_transitions,
                "interaction_count": self.interaction_count,
                "successful_tasks": self.successful_tasks,
                "errors_encountered": self.errors_encountered,
                "last_consolidation": self.last_consolidation.isoformat(),
            }
            with open(meta_file, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            logger.debug(f"Saved narrative identity to {self.storage_path}")
        except Exception as e:
            logger.error(f"Failed to save narrative identity: {e}")
    
    def _load_from_disk(self):
        """Load life story and metadata from disk."""
        try:
            # Load life story
            story_file = self.storage_path / "life_story.json"
            if story_file.exists():
                with open(story_file, 'r') as f:
                    story_data = json.load(f)
                self.life_story = [BiographicalEvent.from_dict(e) for e in story_data]
                logger.info(f"Loaded {len(self.life_story)} life story events")
            
            # Load metadata
            meta_file = self.storage_path / "metadata.json"
            if meta_file.exists():
                with open(meta_file, 'r') as f:
                    metadata = json.load(f)
                self.current_stage = DevelopmentalStage(metadata["current_stage"])
                self.stage_transitions = metadata["stage_transitions"]
                self.interaction_count = metadata["interaction_count"]
                self.successful_tasks = metadata["successful_tasks"]
                self.errors_encountered = metadata["errors_encountered"]
                self.last_consolidation = datetime.fromisoformat(metadata["last_consolidation"])
                logger.info(f"Loaded narrative identity: stage={self.current_stage.value}")
        except Exception as e:
            logger.warning(f"Failed to load narrative identity (starting fresh): {e}")


# Singleton instance
_narrative_engine: Optional[NarrativeIdentityEngine] = None
_engine_lock = threading.Lock()


def get_narrative_engine() -> NarrativeIdentityEngine:
    """Get the singleton narrative identity engine."""
    global _narrative_engine
    if _narrative_engine is None:
        with _engine_lock:
            if _narrative_engine is None:
                _narrative_engine = NarrativeIdentityEngine()
    return _narrative_engine
