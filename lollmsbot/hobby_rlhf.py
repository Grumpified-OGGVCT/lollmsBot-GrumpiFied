"""
Phase 3D: RLHF (Reinforcement Learning from Human Feedback) Pipeline

This module collects human feedback on hobby insights and uses it to 
improve the quality of learning activities through reward modeling.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
from enum import Enum
import threading

logger = logging.getLogger(__name__)


class FeedbackType(str, Enum):
    """Types of feedback"""
    RATING = "rating"
    COMMENT = "comment"
    HELPFUL = "helpful"
    NOT_HELPFUL = "not_helpful"
    SUGGESTION = "suggestion"


@dataclass
class Feedback:
    """Human feedback on an insight or activity"""
    feedback_id: str
    target_type: str  # "insight", "pattern", "activity"
    target_id: str
    feedback_type: FeedbackType
    rating: Optional[int]  # 1-5 stars
    comment: Optional[str]
    helpful: Optional[bool]
    metadata: Dict[str, Any]
    created_at: str
    user_id: str
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class RewardSignal:
    """Reward signal derived from feedback"""
    signal_id: str
    target_id: str
    target_type: str
    reward_score: float  # -1.0 to 1.0
    confidence: float  # 0.0 to 1.0
    feedback_count: int
    calculated_at: str
    metadata: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class RLHFManager:
    """Manages RLHF feedback collection and reward modeling"""
    
    def __init__(self, storage_path: Optional[Path] = None):
        """
        Initialize RLHF manager
        
        Args:
            storage_path: Path for storing feedback and models
        """
        self.storage_path = storage_path or Path.home() / ".lollmsbot" / "rlhf"
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        self.feedbacks: Dict[str, Feedback] = {}
        self.reward_signals: Dict[str, RewardSignal] = {}
        
        self._feedback_counter = 0
        self._signal_counter = 0
        self._lock = threading.Lock()
        
        self._load_state()
        
        logger.info(f"RLHF Manager initialized at {self.storage_path}")
    
    def submit_feedback(
        self,
        target_type: str,
        target_id: str,
        feedback_type: FeedbackType,
        user_id: str = "default_user",
        rating: Optional[int] = None,
        comment: Optional[str] = None,
        helpful: Optional[bool] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Feedback:
        """
        Submit feedback on an insight or activity
        
        Args:
            target_type: Type of target ("insight", "pattern", "activity")
            target_id: Target identifier
            feedback_type: Type of feedback
            user_id: User identifier
            rating: Star rating (1-5)
            comment: Text comment
            helpful: Boolean helpful flag
            metadata: Additional metadata
            
        Returns:
            Created Feedback object
        """
        # Validate rating
        if rating is not None and (rating < 1 or rating > 5):
            raise ValueError("Rating must be between 1 and 5")
        
        with self._lock:
            self._feedback_counter += 1
            feedback_id = f"feedback_{self._feedback_counter}_{int(datetime.now().timestamp())}"
        
        feedback = Feedback(
            feedback_id=feedback_id,
            target_type=target_type,
            target_id=target_id,
            feedback_type=feedback_type,
            rating=rating,
            comment=comment,
            helpful=helpful,
            metadata=metadata or {},
            created_at=datetime.now().isoformat(),
            user_id=user_id
        )
        
        self.feedbacks[feedback_id] = feedback
        self._save_state()
        
        # Recalculate reward signal for target
        self._update_reward_signal(target_id, target_type)
        
        logger.info(f"Submitted feedback {feedback_id} for {target_type}:{target_id}")
        return feedback
    
    def get_feedback(self, feedback_id: str) -> Optional[Feedback]:
        """Get feedback by ID"""
        return self.feedbacks.get(feedback_id)
    
    def list_feedbacks(
        self,
        target_type: Optional[str] = None,
        target_id: Optional[str] = None,
        feedback_type: Optional[FeedbackType] = None,
        limit: int = 100
    ) -> List[Feedback]:
        """
        List feedbacks with optional filters
        
        Args:
            target_type: Filter by target type
            target_id: Filter by target ID
            feedback_type: Filter by feedback type
            limit: Maximum results
            
        Returns:
            List of feedbacks
        """
        feedbacks = list(self.feedbacks.values())
        
        if target_type:
            feedbacks = [f for f in feedbacks if f.target_type == target_type]
        
        if target_id:
            feedbacks = [f for f in feedbacks if f.target_id == target_id]
        
        if feedback_type:
            feedbacks = [f for f in feedbacks if f.feedback_type == feedback_type]
        
        # Sort by created_at (most recent first)
        feedbacks.sort(key=lambda f: f.created_at, reverse=True)
        
        return feedbacks[:limit]
    
    def _update_reward_signal(self, target_id: str, target_type: str) -> None:
        """Calculate and update reward signal for a target"""
        # Get all feedback for this target
        target_feedbacks = [
            f for f in self.feedbacks.values()
            if f.target_id == target_id and f.target_type == target_type
        ]
        
        if not target_feedbacks:
            return
        
        # Calculate reward score from feedback
        reward_score = 0.0
        confidence = 0.0
        
        # Rating-based reward
        ratings = [f.rating for f in target_feedbacks if f.rating is not None]
        if ratings:
            avg_rating = sum(ratings) / len(ratings)
            # Convert 1-5 scale to -1 to 1
            reward_score += (avg_rating - 3) / 2.0
            confidence += 0.3 * min(len(ratings) / 5.0, 1.0)
        
        # Helpful/Not helpful binary feedback
        helpful_votes = [f.helpful for f in target_feedbacks if f.helpful is not None]
        if helpful_votes:
            helpful_ratio = sum(1 for h in helpful_votes if h) / len(helpful_votes)
            # Convert to -1 to 1
            reward_score += (helpful_ratio - 0.5) * 2.0
            confidence += 0.4 * min(len(helpful_votes) / 10.0, 1.0)
        
        # Comment-based signal (simple: having detailed comments is positive)
        comments = [f.comment for f in target_feedbacks if f.comment and len(f.comment) > 20]
        if comments:
            reward_score += 0.2
            confidence += 0.3 * min(len(comments) / 3.0, 1.0)
        
        # Normalize
        reward_score = max(-1.0, min(1.0, reward_score))
        confidence = max(0.0, min(1.0, confidence))
        
        with self._lock:
            self._signal_counter += 1
            signal_id = f"signal_{self._signal_counter}_{int(datetime.now().timestamp())}"
        
        signal = RewardSignal(
            signal_id=signal_id,
            target_id=target_id,
            target_type=target_type,
            reward_score=reward_score,
            confidence=confidence,
            feedback_count=len(target_feedbacks),
            calculated_at=datetime.now().isoformat(),
            metadata={}
        )
        
        # Store with target_id as key for easy lookup
        self.reward_signals[target_id] = signal
        self._save_state()
        
        logger.debug(f"Updated reward signal for {target_type}:{target_id}: {reward_score:.2f}")
    
    def get_reward_signal(self, target_id: str) -> Optional[RewardSignal]:
        """Get reward signal for a target"""
        return self.reward_signals.get(target_id)
    
    def get_quality_metrics(self) -> Dict[str, Any]:
        """Get overall quality metrics"""
        if not self.reward_signals:
            return {
                "average_reward": 0.0,
                "high_quality_count": 0,
                "low_quality_count": 0,
                "total_signals": 0
            }
        
        signals = list(self.reward_signals.values())
        rewards = [s.reward_score for s in signals]
        
        high_quality = len([r for r in rewards if r > 0.3])
        low_quality = len([r for r in rewards if r < -0.3])
        
        return {
            "average_reward": sum(rewards) / len(rewards),
            "high_quality_count": high_quality,
            "low_quality_count": low_quality,
            "total_signals": len(signals),
            "high_quality_ratio": high_quality / len(signals)
        }
    
    def get_pending_feedback_items(
        self,
        target_type: Optional[str] = None,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Get items that need feedback (have few or no feedback)
        
        Args:
            target_type: Filter by target type
            limit: Maximum results
            
        Returns:
            List of items needing feedback
        """
        # Count feedback per target
        feedback_counts = {}
        for feedback in self.feedbacks.values():
            if target_type and feedback.target_type != target_type:
                continue
            key = (feedback.target_type, feedback.target_id)
            feedback_counts[key] = feedback_counts.get(key, 0) + 1
        
        # In production, would fetch actual items from activity database
        # For now, return simulated pending items
        pending = []
        for (ttype, tid), count in feedback_counts.items():
            if count < 3:  # Items with less than 3 feedbacks need more
                pending.append({
                    "target_type": ttype,
                    "target_id": tid,
                    "feedback_count": count,
                    "status": "needs_feedback"
                })
        
        return pending[:limit]
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get RLHF system statistics"""
        feedbacks = list(self.feedbacks.values())
        
        by_type = {}
        for feedback in feedbacks:
            by_type[feedback.feedback_type] = by_type.get(feedback.feedback_type, 0) + 1
        
        ratings = [f.rating for f in feedbacks if f.rating is not None]
        
        return {
            "total_feedbacks": len(feedbacks),
            "by_feedback_type": by_type,
            "total_reward_signals": len(self.reward_signals),
            "average_rating": sum(ratings) / len(ratings) if ratings else 0.0,
            "quality_metrics": self.get_quality_metrics()
        }
    
    def _save_state(self) -> None:
        """Save state to disk"""
        state_file = self.storage_path / "rlhf_state.json"
        
        state = {
            "feedbacks": {k: v.to_dict() for k, v in self.feedbacks.items()},
            "reward_signals": {k: v.to_dict() for k, v in self.reward_signals.items()},
            "counters": {
                "feedback": self._feedback_counter,
                "signal": self._signal_counter
            }
        }
        
        try:
            with open(state_file, 'w') as f:
                json.dump(state, f, indent=2)
        except Exception as e:
            logger.warning(f"Failed to save RLHF state: {e}")
    
    def _load_state(self) -> None:
        """Load state from disk"""
        state_file = self.storage_path / "rlhf_state.json"
        
        if not state_file.exists():
            return
        
        try:
            with open(state_file, 'r') as f:
                state = json.load(f)
            
            # Load feedbacks
            for feedback_data in state.get("feedbacks", {}).values():
                feedback = Feedback(**feedback_data)
                self.feedbacks[feedback.feedback_id] = feedback
            
            # Load reward signals
            for signal_data in state.get("reward_signals", {}).values():
                signal = RewardSignal(**signal_data)
                self.reward_signals[signal.target_id] = signal
            
            # Load counters
            counters = state.get("counters", {})
            self._feedback_counter = counters.get("feedback", 0)
            self._signal_counter = counters.get("signal", 0)
            
            logger.info(f"Loaded RLHF state: {len(self.feedbacks)} feedbacks, {len(self.reward_signals)} signals")
            
        except Exception as e:
            logger.warning(f"Failed to load RLHF state: {e}")


# Global instance
_rlhf_manager: Optional[RLHFManager] = None
_rlhf_lock = threading.Lock()


def get_rlhf_manager(storage_path: Optional[Path] = None) -> RLHFManager:
    """
    Get or create global RLHF manager
    
    Args:
        storage_path: Optional storage path
        
    Returns:
        RLHFManager instance
    """
    global _rlhf_manager
    
    if _rlhf_manager is not None:
        return _rlhf_manager
    
    with _rlhf_lock:
        if _rlhf_manager is None:
            _rlhf_manager = RLHFManager(storage_path)
        return _rlhf_manager
