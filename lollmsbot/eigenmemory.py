"""
Eigenmemory System - Metamemory and Source Monitoring for RCL-2

Implements memory about memory - metacognitive awareness of what's known/unknown.

Features:
- Source monitoring: Distinguish episodic/semantic/confabulated memories
- Metamemory queries: "Do I know X?", "Do I remember saying Y?"
- Strategic forgetting: Decay low-value memories, consolidate important patterns
- Intentional amnesia: GDPR-compliant ability to forget on command
- Memory confidence scoring
- False memory detection

This ensures the agent has accurate self-knowledge about its own memory capabilities
and limitations, preventing false confidence in unreliable memories.
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import threading
import time
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

logger = logging.getLogger("lollmsbot.eigenmemory")


class MemorySource(Enum):
    """Source types for memories."""
    EPISODIC = "episodic"          # Experienced directly (conversation, interaction)
    SEMANTIC = "semantic"           # Factual knowledge (learned, not experienced)
    PROCEDURAL = "procedural"       # How-to knowledge (skills, procedures)
    CONFABULATED = "confabulated"   # Generated to fill gaps (unreliable)
    INHERITED = "inherited"         # From training data or external source
    INFERRED = "inferred"           # Derived from other memories


class MemoryStrength(Enum):
    """Memory strength categories."""
    STRONG = "strong"       # High confidence, recent access
    MODERATE = "moderate"   # Medium confidence or less recent
    WEAK = "weak"           # Low confidence or very old
    FORGOTTEN = "forgotten" # Below retrieval threshold


@dataclass
class MemoryTrace:
    """A single memory trace with metadata."""
    memory_id: str
    content: str
    source: MemorySource
    confidence: float  # 0.0-1.0
    timestamp_created: datetime
    timestamp_accessed: datetime
    access_count: int = 0
    importance: float = 0.5  # 0.0-1.0
    decay_rate: float = 0.1  # 0.0-1.0, higher = faster decay
    strength: MemoryStrength = MemoryStrength.MODERATE
    tags: Set[str] = field(default_factory=set)
    related_memories: Set[str] = field(default_factory=set)
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dict."""
        return {
            "memory_id": self.memory_id,
            "content": self.content,
            "source": self.source.value,
            "confidence": self.confidence,
            "timestamp_created": self.timestamp_created.isoformat(),
            "timestamp_accessed": self.timestamp_accessed.isoformat(),
            "access_count": self.access_count,
            "importance": self.importance,
            "decay_rate": self.decay_rate,
            "strength": self.strength.value,
            "tags": list(self.tags),
            "related_memories": list(self.related_memories),
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> MemoryTrace:
        """Deserialize from dict."""
        data["source"] = MemorySource(data["source"])
        data["strength"] = MemoryStrength(data["strength"])
        data["timestamp_created"] = datetime.fromisoformat(data["timestamp_created"])
        data["timestamp_accessed"] = datetime.fromisoformat(data["timestamp_accessed"])
        data["tags"] = set(data["tags"])
        data["related_memories"] = set(data["related_memories"])
        return cls(**data)
    
    def calculate_current_strength(self) -> float:
        """
        Calculate current memory strength based on decay.
        
        Returns:
            Strength value 0.0-1.0
        """
        # Time-based decay
        age_hours = (datetime.now() - self.timestamp_accessed).total_seconds() / 3600
        time_decay = max(0.0, 1.0 - (self.decay_rate * age_hours / 168))  # 168 hours = 1 week
        
        # Access reinforcement
        access_boost = min(1.0, self.access_count * 0.1)
        
        # Importance amplification
        importance_factor = 0.5 + (self.importance * 0.5)
        
        # Confidence factor
        confidence_factor = self.confidence
        
        # Combined strength
        strength = (time_decay * 0.4 + access_boost * 0.2 + 
                   importance_factor * 0.2 + confidence_factor * 0.2)
        
        return min(1.0, max(0.0, strength))
    
    def update_strength_category(self):
        """Update the strength category based on calculated strength."""
        current = self.calculate_current_strength()
        
        if current >= 0.7:
            self.strength = MemoryStrength.STRONG
        elif current >= 0.4:
            self.strength = MemoryStrength.MODERATE
        elif current >= 0.2:
            self.strength = MemoryStrength.WEAK
        else:
            self.strength = MemoryStrength.FORGOTTEN


@dataclass
class MetamemoryQuery:
    """A query about memory contents or capabilities."""
    query_type: str  # know, remember, forget, confidence, etc.
    subject: str
    timestamp: datetime
    result: Optional[Any] = None


class EigenmemorySystem:
    """
    Metamemory system for self-awareness about memory.
    
    Maintains:
    1. Memory trace registry with source monitoring
    2. Metamemory query interface
    3. Strategic forgetting with decay
    4. False memory detection
    5. GDPR-compliant intentional amnesia
    """
    
    def __init__(
        self,
        storage_path: Optional[str] = None,
        decay_check_interval: int = 3600,  # Check decay every hour
        forgetting_threshold: float = 0.15,  # Forget below this strength
    ):
        """
        Initialize eigenmemory system.
        
        Args:
            storage_path: Where to persist memory traces
            decay_check_interval: Seconds between decay checks
            forgetting_threshold: Strength below which memories are forgotten
        """
        self.storage_path = Path(storage_path or os.path.expanduser("~/.lollmsbot/eigenmemory"))
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        self.decay_check_interval = decay_check_interval
        self.forgetting_threshold = forgetting_threshold
        
        # Memory registry
        self.memories: Dict[str, MemoryTrace] = {}
        
        # Indexes for fast lookup
        self.source_index: Dict[MemorySource, Set[str]] = defaultdict(set)
        self.tag_index: Dict[str, Set[str]] = defaultdict(set)
        
        # Metamemory tracking
        self.query_history: List[MetamemoryQuery] = []
        self.forgotten_count = 0
        self.confabulation_detected = 0
        
        # Decay tracking
        self.last_decay_check = datetime.now()
        
        # Thread safety
        self._lock = threading.RLock()
        
        # Load existing data
        self._load_from_disk()
        
        logger.info(
            f"EigenmemorySystem initialized with {len(self.memories)} memories"
        )
    
    def store_memory(
        self,
        content: str,
        source: MemorySource,
        confidence: float = 0.8,
        importance: float = 0.5,
        tags: Optional[Set[str]] = None,
    ) -> str:
        """
        Store a new memory with source monitoring.
        
        Args:
            content: The memory content
            source: Where this memory came from
            confidence: How confident we are (0.0-1.0)
            importance: How important this is (0.0-1.0)
            tags: Optional tags for categorization
            
        Returns:
            memory_id
        """
        with self._lock:
            memory_id = hashlib.sha256(
                f"{content}{datetime.now().isoformat()}{time.time()}".encode()
            ).hexdigest()[:16]
            
            # Adjust decay rate based on source
            decay_rate = {
                MemorySource.EPISODIC: 0.05,      # Slow decay (experienced)
                MemorySource.SEMANTIC: 0.03,      # Very slow (facts)
                MemorySource.PROCEDURAL: 0.02,    # Extremely slow (skills)
                MemorySource.CONFABULATED: 0.2,   # Fast decay (unreliable)
                MemorySource.INHERITED: 0.04,     # Slow (from training)
                MemorySource.INFERRED: 0.08,      # Moderate (derived)
            }.get(source, 0.1)
            
            trace = MemoryTrace(
                memory_id=memory_id,
                content=content,
                source=source,
                confidence=min(1.0, max(0.0, confidence)),
                timestamp_created=datetime.now(),
                timestamp_accessed=datetime.now(),
                importance=min(1.0, max(0.0, importance)),
                decay_rate=decay_rate,
                tags=tags or set(),
            )
            
            self.memories[memory_id] = trace
            
            # Update indexes
            self.source_index[source].add(memory_id)
            for tag in trace.tags:
                self.tag_index[tag].add(memory_id)
            
            logger.debug(f"Stored {source.value} memory: {content[:50]}...")
            
            # Check if decay is due
            if self._should_check_decay():
                self._perform_decay_check()
            
            return memory_id
    
    def query_knowledge(self, subject: str) -> Dict[str, Any]:
        """
        Metamemory query: "Do I know about X?"
        
        Args:
            subject: What to check knowledge about
            
        Returns:
            Dict with knowledge assessment
        """
        with self._lock:
            query = MetamemoryQuery(
                query_type="know",
                subject=subject,
                timestamp=datetime.now(),
            )
            
            # Search memories containing subject
            relevant = []
            for mem_id, trace in self.memories.items():
                if subject.lower() in trace.content.lower():
                    trace.timestamp_accessed = datetime.now()
                    trace.access_count += 1
                    trace.update_strength_category()
                    relevant.append(trace)
            
            # Assess knowledge
            if not relevant:
                result = {
                    "knows": False,
                    "confidence": 0.0,
                    "sources": [],
                    "explanation": f"No memories found about '{subject}'",
                }
            else:
                # Calculate aggregate confidence
                strengths = [m.calculate_current_strength() for m in relevant]
                avg_confidence = sum(strengths) / len(strengths)
                
                # Get source distribution
                sources = [m.source.value for m in relevant]
                
                result = {
                    "knows": True,
                    "confidence": avg_confidence,
                    "memory_count": len(relevant),
                    "sources": sources,
                    "strongest_memories": [
                        {
                            "content": m.content[:100],
                            "source": m.source.value,
                            "strength": m.calculate_current_strength(),
                        }
                        for m in sorted(relevant, key=lambda x: x.calculate_current_strength(), reverse=True)[:3]
                    ],
                    "explanation": f"Found {len(relevant)} memories about '{subject}' with avg confidence {avg_confidence:.2f}",
                }
            
            query.result = result
            self.query_history.append(query)
            
            return result
    
    def query_remember(self, content: str, threshold: float = 0.6) -> Dict[str, Any]:
        """
        Metamemory query: "Do I remember saying/doing X?"
        
        Args:
            content: What to check for
            threshold: Minimum similarity threshold
            
        Returns:
            Dict with memory search results
        """
        with self._lock:
            query = MetamemoryQuery(
                query_type="remember",
                subject=content,
                timestamp=datetime.now(),
            )
            
            # Simple substring search (could be enhanced with embeddings)
            matches = []
            for mem_id, trace in self.memories.items():
                # Calculate simple similarity (could use better algorithm)
                similarity = self._calculate_similarity(content, trace.content)
                if similarity >= threshold:
                    trace.timestamp_accessed = datetime.now()
                    trace.access_count += 1
                    matches.append((trace, similarity))
            
            if not matches:
                result = {
                    "remembers": False,
                    "confidence": 0.0,
                    "explanation": f"No memory of '{content[:50]}...'",
                }
            else:
                # Sort by similarity
                matches.sort(key=lambda x: x[1], reverse=True)
                best_match = matches[0]
                
                result = {
                    "remembers": True,
                    "confidence": best_match[0].confidence * best_match[1],
                    "match_count": len(matches),
                    "best_match": {
                        "content": best_match[0].content,
                        "source": best_match[0].source.value,
                        "similarity": best_match[1],
                        "timestamp": best_match[0].timestamp_created.isoformat(),
                    },
                    "all_matches": [
                        {
                            "content": m[0].content[:100],
                            "similarity": m[1],
                            "source": m[0].source.value,
                        }
                        for m in matches[:5]
                    ],
                    "explanation": f"Found {len(matches)} similar memories (best: {best_match[1]:.2f} similarity)",
                }
            
            query.result = result
            self.query_history.append(query)
            
            return result
    
    def forget_by_subject(self, subject: str, require_confirmation: bool = True) -> Dict[str, Any]:
        """
        Intentional amnesia: Forget memories about a subject (GDPR-compliant).
        
        Args:
            subject: What to forget
            require_confirmation: Safety flag
            
        Returns:
            Dict with forgetting results
        """
        if not require_confirmation:
            logger.error("Forgetting requires confirmation flag for safety")
            return {"error": "Confirmation required"}
        
        with self._lock:
            # Find relevant memories
            to_forget = []
            for mem_id, trace in list(self.memories.items()):
                if subject.lower() in trace.content.lower():
                    to_forget.append(mem_id)
            
            # Remove them
            for mem_id in to_forget:
                trace = self.memories[mem_id]
                del self.memories[mem_id]
                
                # Update indexes
                self.source_index[trace.source].discard(mem_id)
                for tag in trace.tags:
                    self.tag_index[tag].discard(mem_id)
                
                self.forgotten_count += 1
            
            # Persist changes
            self._save_to_disk()
            
            result = {
                "forgot": len(to_forget),
                "subject": subject,
                "timestamp": datetime.now().isoformat(),
            }
            
            logger.info(f"Intentionally forgot {len(to_forget)} memories about '{subject}'")
            return result
    
    def detect_confabulations(self) -> List[Dict[str, Any]]:
        """
        Detect likely confabulated (false) memories.
        
        Returns:
            List of suspected confabulations
        """
        with self._lock:
            confabulations = []
            
            for mem_id, trace in self.memories.items():
                # Explicit confabulation marking
                if trace.source == MemorySource.CONFABULATED:
                    confabulations.append({
                        "memory_id": mem_id,
                        "content": trace.content[:100],
                        "reason": "Explicitly marked as confabulated",
                        "confidence": trace.confidence,
                    })
                    continue
                
                # Low confidence + inferred = likely confabulation
                if trace.source == MemorySource.INFERRED and trace.confidence < 0.3:
                    confabulations.append({
                        "memory_id": mem_id,
                        "content": trace.content[:100],
                        "reason": "Inferred with very low confidence",
                        "confidence": trace.confidence,
                    })
                
                # Contradicts strong memories
                # (Simplified - real implementation would use semantic similarity)
                # Skip for now to keep it simple
            
            self.confabulation_detected = len(confabulations)
            return confabulations
    
    def get_memory_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about the memory system.
        
        Returns:
            Dict with memory stats
        """
        with self._lock:
            total = len(self.memories)
            
            if total == 0:
                return {
                    "total_memories": 0,
                    "message": "No memories stored yet",
                }
            
            # Source distribution
            source_dist = {
                source.value: len(mem_ids)
                for source, mem_ids in self.source_index.items()
            }
            
            # Strength distribution
            strength_dist = defaultdict(int)
            for trace in self.memories.values():
                trace.update_strength_category()
                strength_dist[trace.strength.value] += 1
            
            # Average confidence
            avg_confidence = sum(t.confidence for t in self.memories.values()) / total
            
            # Most accessed
            most_accessed = sorted(
                self.memories.values(),
                key=lambda x: x.access_count,
                reverse=True
            )[:5]
            
            return {
                "total_memories": total,
                "source_distribution": source_dist,
                "strength_distribution": dict(strength_dist),
                "average_confidence": avg_confidence,
                "forgotten_count": self.forgotten_count,
                "confabulations_detected": self.confabulation_detected,
                "query_count": len(self.query_history),
                "most_accessed": [
                    {
                        "content": m.content[:50],
                        "access_count": m.access_count,
                        "source": m.source.value,
                    }
                    for m in most_accessed
                ],
            }
    
    def _should_check_decay(self) -> bool:
        """Check if decay check is due."""
        return (datetime.now() - self.last_decay_check).total_seconds() >= self.decay_check_interval
    
    def _perform_decay_check(self):
        """Perform strategic forgetting based on decay."""
        with self._lock:
            to_forget = []
            
            for mem_id, trace in self.memories.items():
                trace.update_strength_category()
                current_strength = trace.calculate_current_strength()
                
                if current_strength < self.forgetting_threshold:
                    to_forget.append(mem_id)
            
            # Forget weak memories
            for mem_id in to_forget:
                trace = self.memories[mem_id]
                del self.memories[mem_id]
                
                # Update indexes
                self.source_index[trace.source].discard(mem_id)
                for tag in trace.tags:
                    self.tag_index[tag].discard(mem_id)
                
                self.forgotten_count += 1
            
            self.last_decay_check = datetime.now()
            
            if to_forget:
                logger.info(f"Forgot {len(to_forget)} weak memories during decay check")
                self._save_to_disk()
    
    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """
        Calculate simple text similarity.
        
        Note: This is a basic implementation. Could be enhanced with:
        - Edit distance (Levenshtein)
        - TF-IDF cosine similarity
        - Embedding-based similarity
        """
        # Convert to lowercase word sets
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        if not words1 or not words2:
            return 0.0
        
        # Jaccard similarity
        intersection = len(words1 & words2)
        union = len(words1 | words2)
        
        return intersection / union if union > 0 else 0.0
    
    def _save_to_disk(self):
        """Persist memory traces to disk."""
        try:
            # Save memories
            memories_file = self.storage_path / "memories.json"
            memory_data = {mem_id: trace.to_dict() for mem_id, trace in self.memories.items()}
            with open(memories_file, 'w') as f:
                json.dump(memory_data, f, indent=2)
            
            # Save metadata
            meta_file = self.storage_path / "metadata.json"
            metadata = {
                "forgotten_count": self.forgotten_count,
                "confabulation_detected": self.confabulation_detected,
                "last_decay_check": self.last_decay_check.isoformat(),
            }
            with open(meta_file, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            logger.debug(f"Saved eigenmemory system to {self.storage_path}")
        except Exception as e:
            logger.error(f"Failed to save eigenmemory: {e}")
    
    def _load_from_disk(self):
        """Load memory traces from disk."""
        try:
            # Load memories
            memories_file = self.storage_path / "memories.json"
            if memories_file.exists():
                with open(memories_file, 'r') as f:
                    memory_data = json.load(f)
                
                for mem_id, data in memory_data.items():
                    trace = MemoryTrace.from_dict(data)
                    self.memories[mem_id] = trace
                    
                    # Rebuild indexes
                    self.source_index[trace.source].add(mem_id)
                    for tag in trace.tags:
                        self.tag_index[tag].add(mem_id)
                
                logger.info(f"Loaded {len(self.memories)} memories")
            
            # Load metadata
            meta_file = self.storage_path / "metadata.json"
            if meta_file.exists():
                with open(meta_file, 'r') as f:
                    metadata = json.load(f)
                self.forgotten_count = metadata["forgotten_count"]
                self.confabulation_detected = metadata["confabulation_detected"]
                self.last_decay_check = datetime.fromisoformat(metadata["last_decay_check"])
        except Exception as e:
            logger.warning(f"Failed to load eigenmemory (starting fresh): {e}")


# Singleton instance
_eigenmemory: Optional[EigenmemorySystem] = None
_memory_lock = threading.Lock()


def get_eigenmemory() -> EigenmemorySystem:
    """Get the singleton eigenmemory system."""
    global _eigenmemory
    if _eigenmemory is None:
        with _memory_lock:
            if _eigenmemory is None:
                _eigenmemory = EigenmemorySystem()
    return _eigenmemory
