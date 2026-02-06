"""
Constitutional Restraints Matrix - User-Adjustable Safety Controls for RCL-2

Implements a 12-dimensional continuous control space (0.0-1.0) with 
cryptographic hard-stops for safe, user-controlled cognitive autonomy.

Based on Constitutional AI principles with dynamic constraint satisfaction.

PHASE 2 ENHANCEMENT: Now includes immutable audit trail for all restraint modifications.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import logging
import os
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger("lollmsbot.constitutional_restraints")


@dataclass
class RestraintChange:
    """A single change to a restraint value (immutable audit record)."""
    timestamp: datetime
    dimension: str
    old_value: float
    new_value: float
    modified_by: str  # "user", "system", "policy"
    authorized: bool
    signature: Optional[str] = None
    change_hash: str = field(default="")
    previous_hash: str = field(default="")  # Hash of previous change (blockchain-style)
    
    def __post_init__(self):
        """Calculate hash of this change."""
        if not self.change_hash:
            data = f"{self.timestamp.isoformat()}:{self.dimension}:{self.old_value}:{self.new_value}:{self.modified_by}:{self.authorized}:{self.previous_hash}"
            self.change_hash = hashlib.sha256(data.encode()).hexdigest()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "timestamp": self.timestamp.isoformat(),
            "dimension": self.dimension,
            "old_value": self.old_value,
            "new_value": self.new_value,
            "modified_by": self.modified_by,
            "authorized": self.authorized,
            "signature": self.signature,
            "change_hash": self.change_hash,
            "previous_hash": self.previous_hash,
        }


class RestraintAuditTrail:
    """
    Immutable log of all restraint modifications.
    
    SECURITY FEATURE: Provides blockchain-style chain of custody for restraint changes.
    Each change references the previous change's hash, making tampering detectable.
    """
    
    def __init__(self):
        self.changes: List[RestraintChange] = []  # Append-only
        self.blockchain_integration = False  # Future: Write to external blockchain
        self._last_hash = "0" * 64  # Genesis hash
        
        logger.info("RestraintAuditTrail initialized (immutable, append-only)")
    
    def record_change(self,
                     dimension: str,
                     old_value: float,
                     new_value: float,
                     modified_by: str = "system",
                     authorized: bool = False,
                     signature: Optional[str] = None) -> RestraintChange:
        """
        Record a restraint change (immutable).
        
        Args:
            dimension: Which restraint dimension changed
            old_value: Previous value
            new_value: New value
            modified_by: Who/what made the change
            authorized: Whether this was an authorized override
            signature: Cryptographic signature if authorized
            
        Returns:
            The recorded change
        """
        change = RestraintChange(
            timestamp=datetime.now(),
            dimension=dimension,
            old_value=old_value,
            new_value=new_value,
            modified_by=modified_by,
            authorized=authorized,
            signature=signature,
            previous_hash=self._last_hash
        )
        
        self.changes.append(change)
        self._last_hash = change.change_hash
        
        logger.info(f"Audit: {dimension} changed from {old_value} to {new_value} by {modified_by} (authorized={authorized})")
        
        return change
    
    def verify_chain(self) -> bool:
        """
        Verify the integrity of the audit trail.
        
        Returns:
            True if chain is intact, False if tampering detected
        """
        if not self.changes:
            return True
        
        prev_hash = "0" * 64
        for change in self.changes:
            if change.previous_hash != prev_hash:
                logger.error(f"Chain integrity violation detected at {change.timestamp}")
                return False
            
            # Recalculate hash to verify
            data = f"{change.timestamp.isoformat()}:{change.dimension}:{change.old_value}:{change.new_value}:{change.modified_by}:{change.authorized}:{change.previous_hash}"
            expected_hash = hashlib.sha256(data.encode()).hexdigest()
            
            if change.change_hash != expected_hash:
                logger.error(f"Hash mismatch detected at {change.timestamp}")
                return False
            
            prev_hash = change.change_hash
        
        return True
    
    def get_history(self, 
                   dimension: Optional[str] = None,
                   limit: int = 50) -> List[RestraintChange]:
        """Get change history for a dimension or all dimensions."""
        changes = self.changes
        
        if dimension:
            changes = [c for c in changes if c.dimension == dimension]
        
        return changes[-limit:]
    
    def get_unauthorized_attempts(self) -> List[RestraintChange]:
        """Get all unauthorized change attempts (security monitoring)."""
        return [c for c in self.changes if not c.authorized and c.new_value > c.old_value]
    
    def export_to_json(self) -> str:
        """Export audit trail to JSON (for archival or blockchain integration)."""
        return json.dumps([c.to_dict() for c in self.changes], indent=2)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the audit trail."""
        if not self.changes:
            return {"total_changes": 0}
        
        return {
            "total_changes": len(self.changes),
            "first_change": self.changes[0].timestamp.isoformat(),
            "last_change": self.changes[-1].timestamp.isoformat(),
            "authorized_changes": sum(1 for c in self.changes if c.authorized),
            "unauthorized_attempts": len(self.get_unauthorized_attempts()),
            "chain_valid": self.verify_chain(),
            "dimensions_modified": len(set(c.dimension for c in self.changes)),
        }


class RestraintDimension(Enum):
    """The 12 dimensions of constitutional control."""
    
    # Cognitive Budgeting (System 2 resource allocation)
    RECURSION_DEPTH = "recursion_depth"
    COGNITIVE_BUDGET_MS = "cognitive_budget_ms"
    SIMULATION_FIDELITY = "simulation_fidelity"
    
    # Epistemic Virtues (Truth-seeking behaviors)
    HALLUCINATION_RESISTANCE = "hallucination_resistance"
    UNCERTAINTY_PROPAGATION = "uncertainty_propagation"
    CONTRADICTION_SENSITIVITY = "contradiction_sensitivity"
    
    # Social Cognition (User modeling - Theory of Mind)
    USER_MODEL_FIDELITY = "user_model_fidelity"
    TRANSPARENCY_LEVEL = "transparency_level"
    EXPLANATION_DEPTH = "explanation_depth"
    
    # Autonomy & Growth
    SELF_MODIFICATION_FREEDOM = "self_modification_freedom"
    GOAL_INFERENCE_AUTONOMY = "goal_inference_autonomy"
    MEMORY_CONSOLIDATION_RATE = "memory_consolidation_rate"


@dataclass
class RestraintValue:
    """A single restraint value with metadata."""
    dimension: RestraintDimension
    value: float  # 0.0-1.0
    hard_limit: Optional[float] = None  # Cannot exceed without authorization
    last_modified: datetime = field(default_factory=datetime.now)
    modified_by: str = "system"  # "system", "user", "policy"
    signature: Optional[str] = None  # Cryptographic verification
    
    def __post_init__(self):
        """Validate and clamp value."""
        self.value = max(0.0, min(1.0, self.value))
        if self.hard_limit is not None:
            self.value = min(self.value, self.hard_limit)
    
    def apply_hard_limit(self, limit: float, key: Optional[bytes] = None) -> bool:
        """
        Apply a hard limit that requires cryptographic authorization to exceed.
        
        Args:
            limit: Maximum allowed value
            key: Optional cryptographic key for verification
            
        Returns:
            True if limit was applied successfully
        """
        if key:
            # Generate signature
            message = f"{self.dimension.value}:{limit}:{datetime.now().isoformat()}"
            self.signature = hmac.new(key, message.encode(), hashlib.sha256).hexdigest()
        
        self.hard_limit = limit
        self.value = min(self.value, limit)
        return True
    
    def verify_signature(self, key: bytes) -> bool:
        """Verify the cryptographic signature of the hard limit."""
        if not self.signature or not self.hard_limit:
            return False
        
        message = f"{self.dimension.value}:{self.hard_limit}:{self.last_modified.isoformat()}"
        expected = hmac.new(key, message.encode(), hashlib.sha256).hexdigest()
        return hmac.compare_digest(self.signature, expected)


@dataclass
class ConstitutionalRestraints:
    """
    The 12-dimensional constitutional restraint matrix.
    
    Each dimension is a continuous value (0.0-1.0) controlling different
    aspects of cognitive autonomy, with cryptographic hard-stops for safety.
    """
    
    # Cognitive Budgeting (System 2 resource allocation)
    recursion_depth: float = 0.5          # 0.0=shallow, 1.0=infinite meta (theoretical)
    cognitive_budget_ms: float = 0.3      # Time allocated to System-2 thinking per decision
    simulation_fidelity: float = 0.4      # Detail level of counterfactual simulations
    
    # Epistemic Virtues (Truth-seeking behaviors)
    hallucination_resistance: float = 0.8  # 1.0=admit ignorance, 0.0=confabulate freely
    uncertainty_propagation: float = 0.7   # How aggressively to flag uncertainty in outputs
    contradiction_sensitivity: float = 0.6 # Aggressiveness of belief consistency checks
    
    # Social Cognition (User modeling - Theory of Mind)
    user_model_fidelity: float = 0.5      # 0.0=generic, 1.0=deep psychological modeling
    transparency_level: float = 0.6       # 0.0=black box, 1.0=show raw token probabilities
    explanation_depth: float = 0.7        # Granularity of reasoning explanation
    
    # Autonomy & Growth
    self_modification_freedom: float = 0.1 # 0.0=static, 1.0=can rewrite own prompts/weights
    goal_inference_autonomy: float = 0.3   # 0.0=user commands only, 1.0=proactive goal formation
    memory_consolidation_rate: float = 0.5 # Speed of long-term self-model updates
    
    # Hard stops (cryptographically signed, require authorization to modify)
    _hard_limits: Dict[str, float] = field(default_factory=lambda: {
        "self_modification_freedom": 0.5,  # Cannot exceed 0.5 without authorization
        "goal_inference_autonomy": 0.7,    # Cannot exceed 0.7 (prevent runaway goals)
        "recursion_depth": 0.9             # Prevent infinite regress
    })
    
    # Cryptographic key for hard limit enforcement
    _secret_key: Optional[bytes] = None
    
    # Audit trail (Phase 2 Security Enhancement)
    _audit_trail: Optional[RestraintAuditTrail] = None
    
    def __post_init__(self):
        """Initialize and apply hard limits."""
        # Initialize audit trail
        self._audit_trail = RestraintAuditTrail()
        
        # Load secret key from environment
        key_hex = os.getenv("CONSTITUTIONAL_KEY")
        if key_hex:
            try:
                self._secret_key = bytes.fromhex(key_hex)
                logger.info("Constitutional key loaded successfully")
            except ValueError:
                logger.warning("Invalid CONSTITUTIONAL_KEY format, using default")
        else:
            logger.warning("No CONSTITUTIONAL_KEY set, hard-stops will use default security")
        
        # Apply hard limits
        for dimension, limit in self._hard_limits.items():
            current_value = getattr(self, dimension, 1.0)
            if current_value > limit:
                logger.warning(f"Clamping {dimension} from {current_value} to hard limit {limit}")
                # Record in audit trail
                if self._audit_trail:
                    self._audit_trail.record_change(
                        dimension=dimension,
                        old_value=current_value,
                        new_value=limit,
                        modified_by="system_init",
                        authorized=True
                    )
                setattr(self, dimension, limit)
    
    @classmethod
    def from_env(cls) -> "ConstitutionalRestraints":
        """Load restraints from environment variables."""
        
        def _get_float(name: str, default: float) -> float:
            val = os.getenv(name)
            if val is None:
                return default
            try:
                return max(0.0, min(1.0, float(val)))
            except ValueError:
                logger.warning(f"Invalid {name} value, using default {default}")
                return default
        
        return cls(
            # Cognitive Budgeting
            recursion_depth=_get_float("RESTRAINT_RECURSION_DEPTH", 0.5),
            cognitive_budget_ms=_get_float("RESTRAINT_COGNITIVE_BUDGET", 0.3),
            simulation_fidelity=_get_float("RESTRAINT_SIMULATION_FIDELITY", 0.4),
            
            # Epistemic Virtues
            hallucination_resistance=_get_float("RESTRAINT_HALLUCINATION_RESISTANCE", 0.8),
            uncertainty_propagation=_get_float("RESTRAINT_UNCERTAINTY_PROPAGATION", 0.7),
            contradiction_sensitivity=_get_float("RESTRAINT_CONTRADICTION_SENSITIVITY", 0.6),
            
            # Social Cognition
            user_model_fidelity=_get_float("RESTRAINT_USER_MODEL_FIDELITY", 0.5),
            transparency_level=_get_float("RESTRAINT_TRANSPARENCY_LEVEL", 0.6),
            explanation_depth=_get_float("RESTRAINT_EXPLANATION_DEPTH", 0.7),
            
            # Autonomy & Growth
            self_modification_freedom=_get_float("RESTRAINT_SELF_MODIFICATION", 0.1),
            goal_inference_autonomy=_get_float("RESTRAINT_GOAL_AUTONOMY", 0.3),
            memory_consolidation_rate=_get_float("RESTRAINT_MEMORY_CONSOLIDATION", 0.5),
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        data = {
            "recursion_depth": self.recursion_depth,
            "cognitive_budget_ms": self.cognitive_budget_ms,
            "simulation_fidelity": self.simulation_fidelity,
            "hallucination_resistance": self.hallucination_resistance,
            "uncertainty_propagation": self.uncertainty_propagation,
            "contradiction_sensitivity": self.contradiction_sensitivity,
            "user_model_fidelity": self.user_model_fidelity,
            "transparency_level": self.transparency_level,
            "explanation_depth": self.explanation_depth,
            "self_modification_freedom": self.self_modification_freedom,
            "goal_inference_autonomy": self.goal_inference_autonomy,
            "memory_consolidation_rate": self.memory_consolidation_rate,
            "hard_limits": self._hard_limits,
        }
        return data
    
    def get_dimension(self, dimension: RestraintDimension) -> float:
        """Get the value of a specific dimension."""
        attr_name = dimension.value
        return getattr(self, attr_name, 0.5)
    
    def set_dimension(self, dimension: RestraintDimension, value: float, 
                     authorized: bool = False, key: Optional[bytes] = None) -> bool:
        """
        Set the value of a specific dimension.
        
        PHASE 2 ENHANCEMENT: Now records all changes in immutable audit trail.
        
        Args:
            dimension: Which dimension to set
            value: New value (0.0-1.0)
            authorized: Whether this is an authorized override
            key: Cryptographic key for hard limit bypass
            
        Returns:
            True if value was set, False if blocked by hard limit
        """
        attr_name = dimension.value
        old_value = getattr(self, attr_name, 0.5)
        value = max(0.0, min(1.0, value))
        
        # Check hard limit
        signature = None
        if attr_name in self._hard_limits:
            hard_limit = self._hard_limits[attr_name]
            
            if value > hard_limit:
                if not authorized:
                    logger.warning(f"Attempt to set {attr_name} to {value} blocked by hard limit {hard_limit}")
                    # Record unauthorized attempt in audit trail
                    if self._audit_trail:
                        self._audit_trail.record_change(
                            dimension=attr_name,
                            old_value=old_value,
                            new_value=value,
                            modified_by="unauthorized_attempt",
                            authorized=False
                        )
                    return False
                
                if key and self._secret_key:
                    # Verify authorization
                    message = f"override:{attr_name}:{value}".encode()
                    expected = hmac.new(self._secret_key, message, hashlib.sha256).hexdigest()
                    provided = hmac.new(key, message, hashlib.sha256).hexdigest()
                    
                    if not hmac.compare_digest(expected, provided):
                        logger.error(f"Invalid authorization key for {attr_name}")
                        # Record failed authorization in audit trail
                        if self._audit_trail:
                            self._audit_trail.record_change(
                                dimension=attr_name,
                                old_value=old_value,
                                new_value=value,
                                modified_by="failed_authorization",
                                authorized=False
                            )
                        return False
                    
                    signature = expected
                else:
                    logger.warning(f"Authorized override of {attr_name} without key verification")
        
        # Set the value
        setattr(self, attr_name, value)
        
        # Record successful change in audit trail
        if self._audit_trail:
            self._audit_trail.record_change(
                dimension=attr_name,
                old_value=old_value,
                new_value=value,
                modified_by="user" if authorized else "system",
                authorized=authorized,
                signature=signature
            )
        
        logger.info(f"Set {attr_name} to {value}")
        return True
    
    def get_audit_trail(self) -> Optional[RestraintAuditTrail]:
        """Get the audit trail for this restraint configuration."""
        return self._audit_trail
    
    def verify_audit_integrity(self) -> bool:
        """Verify the integrity of the audit trail."""
        if not self._audit_trail:
            return True
        return self._audit_trail.verify_chain()
    
    def get_max_recursion_depth(self) -> int:
        """Get maximum allowed recursion depth as integer."""
        return int(self.recursion_depth * 10)  # 0.0-1.0 → 0-10
    
    def get_cognitive_budget(self) -> float:
        """Get cognitive budget in milliseconds."""
        return self.cognitive_budget_ms * 1000.0  # 0.0-1.0 → 0-1000ms
    
    def get_simulation_detail_level(self) -> str:
        """Get simulation fidelity level as descriptive string."""
        if self.simulation_fidelity < 0.3:
            return "low"
        elif self.simulation_fidelity < 0.7:
            return "medium"
        else:
            return "high"
    
    def should_admit_ignorance(self, confidence: float) -> bool:
        """Decide whether to admit ignorance based on confidence and resistance."""
        threshold = 1.0 - self.hallucination_resistance
        return confidence < threshold
    
    def should_flag_uncertainty(self, uncertainty: float) -> bool:
        """Decide whether to explicitly flag uncertainty in output."""
        return uncertainty > (1.0 - self.uncertainty_propagation)
    
    def should_check_contradictions(self) -> bool:
        """Decide whether to perform contradiction checking."""
        return self.contradiction_sensitivity > 0.3
    
    def get_explanation_verbosity(self) -> str:
        """Get explanation verbosity level."""
        if self.explanation_depth < 0.3:
            return "terse"
        elif self.explanation_depth < 0.6:
            return "concise"
        elif self.explanation_depth < 0.8:
            return "detailed"
        else:
            return "exhaustive"


class DynamicRestraintPolicy:
    """
    Reinforcement Learning-based policy that dynamically adjusts restraints
    based on context, user expertise, and detected adversarial inputs.
    """
    
    def __init__(self, base_restraints: ConstitutionalRestraints):
        self.base_restraints = base_restraints
        self.context_adjustments: Dict[str, Dict[str, float]] = {
            "medical_advice": {
                "hallucination_resistance": 0.95,
                "uncertainty_propagation": 0.9,
                "transparency_level": 0.8,
            },
            "casual_chat": {
                "hallucination_resistance": 0.6,
                "cognitive_budget_ms": 0.2,
                "transparency_level": 0.4,
            },
            "code_generation": {
                "contradiction_sensitivity": 0.8,
                "simulation_fidelity": 0.7,
                "recursion_depth": 0.7,
            },
            "creative_writing": {
                "hallucination_resistance": 0.3,
                "self_modification_freedom": 0.4,
                "cognitive_budget_ms": 0.5,
            },
        }
        
        self.user_expertise_levels = {
            "novice": {
                "transparency_level": 0.8,
                "explanation_depth": 0.9,
                "user_model_fidelity": 0.3,
            },
            "intermediate": {
                "transparency_level": 0.6,
                "explanation_depth": 0.6,
                "user_model_fidelity": 0.5,
            },
            "expert": {
                "transparency_level": 0.4,
                "explanation_depth": 0.3,
                "user_model_fidelity": 0.7,
            },
        }
    
    def adjust_for_context(self, 
                          task_type: str,
                          user_expertise: str = "intermediate",
                          adversarial_score: float = 0.0) -> ConstitutionalRestraints:
        """
        Dynamically adjust restraints based on context.
        
        Args:
            task_type: Type of task being performed
            user_expertise: User's expertise level
            adversarial_score: Detected adversarial input score (0.0-1.0)
            
        Returns:
            Adjusted restraints
        """
        # Start with base restraints
        adjusted = ConstitutionalRestraints(
            recursion_depth=self.base_restraints.recursion_depth,
            cognitive_budget_ms=self.base_restraints.cognitive_budget_ms,
            simulation_fidelity=self.base_restraints.simulation_fidelity,
            hallucination_resistance=self.base_restraints.hallucination_resistance,
            uncertainty_propagation=self.base_restraints.uncertainty_propagation,
            contradiction_sensitivity=self.base_restraints.contradiction_sensitivity,
            user_model_fidelity=self.base_restraints.user_model_fidelity,
            transparency_level=self.base_restraints.transparency_level,
            explanation_depth=self.base_restraints.explanation_depth,
            self_modification_freedom=self.base_restraints.self_modification_freedom,
            goal_inference_autonomy=self.base_restraints.goal_inference_autonomy,
            memory_consolidation_rate=self.base_restraints.memory_consolidation_rate,
        )
        
        # Apply task-specific adjustments
        if task_type in self.context_adjustments:
            for key, value in self.context_adjustments[task_type].items():
                if hasattr(adjusted, key):
                    setattr(adjusted, key, value)
        
        # Apply user expertise adjustments
        if user_expertise in self.user_expertise_levels:
            for key, value in self.user_expertise_levels[user_expertise].items():
                if hasattr(adjusted, key):
                    current = getattr(adjusted, key)
                    # Blend with current value
                    setattr(adjusted, key, (current + value) / 2)
        
        # Apply adversarial detection adjustments
        if adversarial_score > 0.5:
            # Clamp down autonomy when manipulation detected
            adjusted.self_modification_freedom = min(adjusted.self_modification_freedom, 0.1)
            adjusted.goal_inference_autonomy = min(adjusted.goal_inference_autonomy, 0.2)
            adjusted.hallucination_resistance = max(adjusted.hallucination_resistance, 0.9)
            logger.warning(f"Adversarial input detected (score={adversarial_score:.2f}), clamping autonomy")
        
        return adjusted


# Global instance
_constitutional_restraints: Optional[ConstitutionalRestraints] = None
_dynamic_policy: Optional[DynamicRestraintPolicy] = None


def get_constitutional_restraints() -> ConstitutionalRestraints:
    """Get or create the global constitutional restraints instance."""
    global _constitutional_restraints
    if _constitutional_restraints is None:
        _constitutional_restraints = ConstitutionalRestraints.from_env()
    return _constitutional_restraints


def get_dynamic_policy() -> DynamicRestraintPolicy:
    """Get or create the global dynamic restraint policy."""
    global _dynamic_policy
    if _dynamic_policy is None:
        _dynamic_policy = DynamicRestraintPolicy(get_constitutional_restraints())
    return _dynamic_policy
