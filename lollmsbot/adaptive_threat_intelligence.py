"""
Adaptive Threat Intelligence - Real-Time Learning for AI/LLM Security

This module enables the security system to LEARN and ADAPT to new threats
in real-time, specifically for autonomous agents and LLM-based systems.

Key Differences from Traditional Security:
- Not antivirus (no virus signatures)
- Not VPN/firewall (no network-level blocking)
- Focuses on AI/LLM-specific attack vectors
- Learns from agent behavior and attack attempts
- Adapts defenses based on observed patterns

AI/LLM-Specific Threat Categories:
1. Prompt Injection Variants - New jailbreak techniques
2. Context Poisoning - Malicious data in agent memory
3. Agent Manipulation - Tricking autonomous behavior
4. Trust Boundary Violations - Breaking sandbox/permissions
5. Skill Behavior Anomalies - Unexpected tool usage patterns
6. Instruction Confusion - Role/delimiter manipulation
"""

import asyncio
import hashlib
import json
import logging
import re
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Any

logger = logging.getLogger("lollmsbot.adaptive_threat_intelligence")


@dataclass
class ThreatObservation:
    """A single observed threat attempt."""
    timestamp: datetime
    threat_type: str  # e.g., "prompt_injection", "context_poisoning"
    pattern: str  # The actual malicious pattern
    confidence: float  # How confident we are this was a threat
    blocked: bool  # Whether it was blocked
    source: str  # Where it came from
    context: Dict[str, Any] = field(default_factory=dict)


@dataclass
class LearnedPattern:
    """A pattern learned from observed threats."""
    pattern: str  # Regex pattern or template
    threat_type: str
    confidence: float  # 0.0-1.0, increases with observations
    first_seen: datetime
    last_seen: datetime
    observation_count: int = 0
    blocked_count: int = 0
    false_positive_count: int = 0
    
    @property
    def effectiveness(self) -> float:
        """Calculate pattern effectiveness (0.0-1.0)."""
        if self.observation_count == 0:
            return 0.0
        return self.blocked_count / self.observation_count
    
    @property
    def reliability(self) -> float:
        """Calculate reliability (low false positives = high reliability)."""
        if self.observation_count == 0:
            return 0.0
        return 1.0 - (self.false_positive_count / self.observation_count)


class AdaptiveThreatIntelligence:
    """
    Learn and adapt to new AI/LLM threats in real-time.
    
    This is NOT traditional antivirus or network security.
    Focus: Autonomous agent threats on home PCs
    - Prompt manipulation
    - Agent behavior anomalies
    - Context poisoning
    - Tool misuse patterns
    """
    
    def __init__(
        self,
        db_path: Optional[Path] = None,
        learning_enabled: bool = True,
        min_observations: int = 3,
        pattern_generation_enabled: bool = True
    ):
        self.db_path = db_path or Path.home() / ".lollmsbot" / "threat_intel.json"
        self.learning_enabled = learning_enabled
        self.min_observations = min_observations
        self.pattern_generation_enabled = pattern_generation_enabled
        
        # Observation storage
        self._observations: deque = deque(maxlen=10000)  # Last 10K observations
        self._learned_patterns: Dict[str, LearnedPattern] = {}
        
        # Pattern generation tracking
        self._pattern_candidates: Dict[str, List[str]] = defaultdict(list)
        
        # Load existing learned patterns
        self._load_patterns()
        
        logger.info("🧠 Adaptive Threat Intelligence initialized")
        logger.info(f"   Learning: {'✅ Enabled' if learning_enabled else '❌ Disabled'}")
        logger.info(f"   Loaded {len(self._learned_patterns)} learned patterns")
    
    def observe_threat(
        self,
        threat_type: str,
        pattern: str,
        confidence: float,
        blocked: bool,
        source: str = "unknown",
        context: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Record an observed threat attempt.
        This is called whenever Guardian detects something suspicious.
        """
        if not self.learning_enabled:
            return
        
        observation = ThreatObservation(
            timestamp=datetime.now(),
            threat_type=threat_type,
            pattern=pattern,
            confidence=confidence,
            blocked=blocked,
            source=source,
            context=context or {}
        )
        
        self._observations.append(observation)
        
        # Learn from this observation
        self._learn_from_observation(observation)
        
        logger.debug(
            f"📝 Threat observed: {threat_type} "
            f"({'blocked' if blocked else 'allowed'}, confidence: {confidence:.2f})"
        )
    
    def _learn_from_observation(self, obs: ThreatObservation) -> None:
        """Learn from a threat observation and update patterns."""
        
        # 1. Update existing pattern if matches
        pattern_updated = self._update_existing_pattern(obs)
        
        # 2. Generate new pattern if this is a novel threat
        if not pattern_updated and obs.blocked and obs.confidence > 0.7:
            self._generate_pattern_candidate(obs)
        
        # 3. Check if we have enough similar observations to create new pattern
        if self.pattern_generation_enabled:
            self._check_pattern_candidates(obs.threat_type)
    
    def _update_existing_pattern(self, obs: ThreatObservation) -> bool:
        """Update an existing learned pattern with new observation."""
        pattern_key = self._get_pattern_key(obs.threat_type, obs.pattern)
        
        if pattern_key in self._learned_patterns:
            pattern = self._learned_patterns[pattern_key]
            pattern.observation_count += 1
            pattern.last_seen = obs.timestamp
            
            if obs.blocked:
                pattern.blocked_count += 1
            
            # Adjust confidence based on effectiveness
            if pattern.effectiveness > 0.8:
                pattern.confidence = min(1.0, pattern.confidence + 0.05)
            
            logger.debug(
                f"📊 Updated pattern: {pattern_key[:20]}... "
                f"(obs: {pattern.observation_count}, eff: {pattern.effectiveness:.2f})"
            )
            return True
        
        return False
    
    def _generate_pattern_candidate(self, obs: ThreatObservation) -> None:
        """Generate a pattern candidate from observation."""
        # Extract potential pattern from the observation
        pattern = self._extract_pattern(obs.pattern, obs.threat_type)
        
        if pattern:
            self._pattern_candidates[obs.threat_type].append(pattern)
            logger.debug(f"🔍 New pattern candidate: {obs.threat_type} - {pattern[:30]}...")
    
    def _extract_pattern(self, text: str, threat_type: str) -> Optional[str]:
        """
        Extract a reusable pattern from observed malicious text.
        This is where we build NEW defenses from attack attempts.
        """
        if threat_type == "prompt_injection":
            # Look for common injection structures
            # e.g., "ignore previous" -> r"ignore\s+previous"
            words = text.lower().split()
            
            # Find suspicious word sequences
            suspicious_sequences = []
            for i in range(len(words) - 1):
                if words[i] in ["ignore", "disregard", "forget", "override"]:
                    suspicious_sequences.append(f"{words[i]}\\s+{words[i+1]}")
            
            if suspicious_sequences:
                return suspicious_sequences[0]
        
        elif threat_type == "context_poisoning":
            # Look for attempts to inject into conversation history
            if re.search(r"(system|user|assistant)\s*:\s*", text, re.IGNORECASE):
                return r"(system|user|assistant)\s*:\s*"
        
        elif threat_type == "agent_manipulation":
            # Look for attempts to manipulate agent behavior
            if "you are now" in text.lower():
                return r"you\s+are\s+now\s+\w+"
        
        # Return original if we can't extract a pattern
        return text[:100] if len(text) > 100 else text
    
    def _check_pattern_candidates(self, threat_type: str) -> None:
        """
        Check if we have enough similar observations to create a new pattern.
        This is the "real-time learning" part.
        """
        candidates = self._pattern_candidates.get(threat_type, [])
        
        if len(candidates) < self.min_observations:
            return
        
        # Find most common pattern
        pattern_freq = defaultdict(int)
        for pattern in candidates:
            pattern_freq[pattern] += 1
        
        # If a pattern appears min_observations times, promote it
        for pattern, count in pattern_freq.items():
            if count >= self.min_observations:
                pattern_key = self._get_pattern_key(threat_type, pattern)
                
                if pattern_key not in self._learned_patterns:
                    # Create new learned pattern
                    new_pattern = LearnedPattern(
                        pattern=pattern,
                        threat_type=threat_type,
                        confidence=0.6,  # Start conservative
                        first_seen=datetime.now(),
                        last_seen=datetime.now(),
                        observation_count=count,
                        blocked_count=count
                    )
                    
                    self._learned_patterns[pattern_key] = new_pattern
                    
                    logger.info(
                        f"🎯 NEW PATTERN LEARNED: {threat_type} - {pattern[:40]}... "
                        f"({count} observations)"
                    )
                    
                    # Save to disk
                    self._save_patterns()
                
                # Clear candidates for this pattern
                self._pattern_candidates[threat_type] = [
                    p for p in candidates if p != pattern
                ]
    
    def _get_pattern_key(self, threat_type: str, pattern: str) -> str:
        """Generate a unique key for a pattern."""
        return hashlib.sha256(f"{threat_type}:{pattern}".encode()).hexdigest()[:32]
    
    def get_learned_patterns(self, threat_type: Optional[str] = None) -> List[LearnedPattern]:
        """Get learned patterns, optionally filtered by type."""
        patterns = list(self._learned_patterns.values())
        
        if threat_type:
            patterns = [p for p in patterns if p.threat_type == threat_type]
        
        # Sort by effectiveness
        patterns.sort(key=lambda p: p.effectiveness, reverse=True)
        
        return patterns
    
    def check_against_learned_patterns(
        self,
        text: str,
        threat_type: Optional[str] = None
    ) -> List[Tuple[LearnedPattern, float]]:
        """
        Check text against learned patterns.
        Returns list of (pattern, match_score) tuples.
        """
        matches = []
        
        patterns = self.get_learned_patterns(threat_type)
        
        for pattern in patterns:
            # Skip low-confidence patterns
            if pattern.confidence < 0.5 or pattern.reliability < 0.7:
                continue
            
            # Try to match pattern
            try:
                if re.search(pattern.pattern, text, re.IGNORECASE):
                    # Calculate match score based on pattern confidence and reliability
                    match_score = pattern.confidence * pattern.reliability
                    matches.append((pattern, match_score))
            except re.error:
                # Invalid regex pattern, skip
                continue
        
        return matches
    
    def report_false_positive(self, pattern_key: str) -> None:
        """Report a false positive to reduce pattern confidence."""
        if pattern_key in self._learned_patterns:
            pattern = self._learned_patterns[pattern_key]
            pattern.false_positive_count += 1
            
            # Reduce confidence
            pattern.confidence = max(0.1, pattern.confidence - 0.1)
            
            logger.warning(
                f"⚠️  False positive reported: {pattern_key[:20]}... "
                f"(reliability: {pattern.reliability:.2f})"
            )
            
            # If reliability drops too low, remove pattern
            if pattern.reliability < 0.3:
                del self._learned_patterns[pattern_key]
                logger.info(f"🗑️  Removed unreliable pattern: {pattern_key[:20]}...")
            
            self._save_patterns()
    
    def _save_patterns(self) -> None:
        """Persist learned patterns to disk."""
        try:
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
            
            data = {
                "version": "1.0",
                "last_updated": datetime.now().isoformat(),
                "patterns": [
                    {
                        "pattern": p.pattern,
                        "threat_type": p.threat_type,
                        "confidence": p.confidence,
                        "first_seen": p.first_seen.isoformat(),
                        "last_seen": p.last_seen.isoformat(),
                        "observation_count": p.observation_count,
                        "blocked_count": p.blocked_count,
                        "false_positive_count": p.false_positive_count,
                    }
                    for p in self._learned_patterns.values()
                ]
            }
            
            with open(self.db_path, 'w') as f:
                json.dump(data, f, indent=2)
            
            logger.debug(f"💾 Saved {len(self._learned_patterns)} patterns to {self.db_path}")
            
        except Exception as e:
            logger.error(f"Error saving patterns: {e}")
    
    def _load_patterns(self) -> None:
        """Load learned patterns from disk."""
        try:
            if not self.db_path.exists():
                return
            
            with open(self.db_path, 'r') as f:
                data = json.load(f)
            
            for p_data in data.get("patterns", []):
                pattern = LearnedPattern(
                    pattern=p_data["pattern"],
                    threat_type=p_data["threat_type"],
                    confidence=p_data["confidence"],
                    first_seen=datetime.fromisoformat(p_data["first_seen"]),
                    last_seen=datetime.fromisoformat(p_data["last_seen"]),
                    observation_count=p_data["observation_count"],
                    blocked_count=p_data["blocked_count"],
                    false_positive_count=p_data.get("false_positive_count", 0),
                )
                
                pattern_key = self._get_pattern_key(pattern.threat_type, pattern.pattern)
                self._learned_patterns[pattern_key] = pattern
            
            logger.info(f"📂 Loaded {len(self._learned_patterns)} patterns from disk")
            
        except Exception as e:
            logger.error(f"Error loading patterns: {e}")
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get learning statistics."""
        total_observations = len(self._observations)
        
        patterns_by_type = defaultdict(int)
        for pattern in self._learned_patterns.values():
            patterns_by_type[pattern.threat_type] += 1
        
        effective_patterns = sum(
            1 for p in self._learned_patterns.values()
            if p.effectiveness > 0.8 and p.reliability > 0.7
        )
        
        return {
            "learning_enabled": self.learning_enabled,
            "total_observations": total_observations,
            "learned_patterns": len(self._learned_patterns),
            "effective_patterns": effective_patterns,
            "patterns_by_type": dict(patterns_by_type),
            "pattern_candidates": {
                t: len(c) for t, c in self._pattern_candidates.items()
            },
            "avg_pattern_confidence": sum(
                p.confidence for p in self._learned_patterns.values()
            ) / max(len(self._learned_patterns), 1),
        }


# Global instance
_adaptive_intel_instance: Optional[AdaptiveThreatIntelligence] = None


def get_adaptive_intelligence() -> AdaptiveThreatIntelligence:
    """Get or create the adaptive intelligence instance."""
    global _adaptive_intel_instance
    if _adaptive_intel_instance is None:
        _adaptive_intel_instance = AdaptiveThreatIntelligence()
    return _adaptive_intel_instance
