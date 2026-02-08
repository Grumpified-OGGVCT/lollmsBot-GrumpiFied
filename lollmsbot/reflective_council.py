"""
Reflective Council - Multi-Agent Metacognitive Governance for RCL-2

Implements a "Society of Mind" architecture where different cognitive faculties
deliberate on high-stakes decisions, detect conflicts, and reach consensus.

Inspired by democratic deliberation and Constitutional AI principles.
"""

from __future__ import annotations

import asyncio
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger("lollmsbot.reflective_council")


class CouncilMemberRole(Enum):
    """Roles of council members representing different cognitive faculties."""
    GUARDIAN = "guardian"          # Safety and security
    EPISTEMOLOGIST = "epistemologist"  # Truth and accuracy
    STRATEGIST = "strategist"      # Efficiency and goals
    EMPATH = "empath"              # User experience
    HISTORIAN = "historian"        # Consistency with past


class VoteType(Enum):
    """Types of votes council members can cast."""
    APPROVE = auto()
    REJECT = auto()
    ABSTAIN = auto()
    ESCALATE = auto()  # Requires human decision


@dataclass
class CouncilPerspective:
    """A council member's perspective on a proposed action."""
    member_role: CouncilMemberRole
    vote: VoteType
    confidence: float  # 0.0-1.0
    reasoning: str
    concerns: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    risk_assessment: float = 0.5  # 0.0=safe, 1.0=dangerous
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "role": self.member_role.value,
            "vote": self.vote.name,
            "confidence": self.confidence,
            "reasoning": self.reasoning,
            "concerns": self.concerns,
            "recommendations": self.recommendations,
            "risk_assessment": self.risk_assessment,
        }


@dataclass
class ProposedAction:
    """An action being considered by the council."""
    action_id: str
    action_type: str  # "tool_use", "response_generation", "skill_activation", etc.
    description: str
    context: Dict[str, Any]
    stakes: str  # "low", "medium", "high", "critical"
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class DeliberationResult:
    """Result of council deliberation."""
    action: ProposedAction
    decision: str  # "approved", "rejected", "escalate", "modified"
    unanimous: bool
    perspectives: List[CouncilPerspective]
    conflicts: List[Tuple[CouncilMemberRole, CouncilMemberRole]]
    final_reasoning: str
    confidence: float
    took_seconds: float
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "action_id": self.action.action_id,
            "action_type": self.action.action_type,
            "decision": self.decision,
            "unanimous": self.unanimous,
            "perspectives": [p.to_dict() for p in self.perspectives],
            "conflicts": [(c1.value, c2.value) for c1, c2 in self.conflicts],
            "final_reasoning": self.final_reasoning,
            "confidence": self.confidence,
            "took_seconds": self.took_seconds,
        }


class CouncilMember(ABC):
    """Base class for council members."""
    
    def __init__(self, role: CouncilMemberRole):
        self.role = role
        self._evaluation_count = 0
    
    @abstractmethod
    async def evaluate(self, action: ProposedAction) -> CouncilPerspective:
        """Evaluate a proposed action from this member's perspective."""
        pass
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics for this council member."""
        return {
            "role": self.role.value,
            "evaluation_count": self._evaluation_count,
        }


class GuardianRep(CouncilMember):
    """Represents safety and security perspective."""
    
    def __init__(self):
        super().__init__(CouncilMemberRole.GUARDIAN)
        self.risk_threshold = 0.7
    
    async def evaluate(self, action: ProposedAction) -> CouncilPerspective:
        """Evaluate from safety/security perspective."""
        self._evaluation_count += 1
        
        concerns = []
        risk_score = 0.0
        
        # Check for high-risk patterns
        if action.stakes in ["high", "critical"]:
            concerns.append("High-stakes action requires careful review")
            risk_score += 0.3
        
        if "execute" in action.action_type.lower():
            concerns.append("Code execution carries security risks")
            risk_score += 0.4
        
        if "modify" in action.action_type.lower():
            concerns.append("Modification actions need validation")
            risk_score += 0.3
        
        # Decide vote based on risk
        if risk_score > self.risk_threshold:
            vote = VoteType.REJECT
            reasoning = "Safety concerns exceed acceptable threshold"
        elif risk_score > 0.5:
            vote = VoteType.ESCALATE
            reasoning = "Moderate safety concerns require human oversight"
        else:
            vote = VoteType.APPROVE
            reasoning = "No significant safety concerns detected"
        
        return CouncilPerspective(
            member_role=self.role,
            vote=vote,
            confidence=0.8,
            reasoning=reasoning,
            concerns=concerns,
            recommendations=["Verify action parameters", "Log all security events"],
            risk_assessment=risk_score
        )


class TruthRep(CouncilMember):
    """Represents accuracy and fact-checking perspective (Epistemologist)."""
    
    def __init__(self):
        super().__init__(CouncilMemberRole.EPISTEMOLOGIST)
        self.accuracy_threshold = 0.7
    
    async def evaluate(self, action: ProposedAction) -> CouncilPerspective:
        """Evaluate from truth/accuracy perspective."""
        self._evaluation_count += 1
        
        concerns = []
        confidence = action.context.get("confidence", 0.5)
        
        # Check for low-confidence claims
        if confidence < self.accuracy_threshold:
            concerns.append(f"Low confidence ({confidence:.1%}) in factual accuracy")
        
        # Check for hallucination risk
        if action.action_type == "response_generation":
            if not action.context.get("verified", False):
                concerns.append("Response not verified against knowledge base")
        
        # Decide vote
        if confidence < 0.5:
            vote = VoteType.REJECT
            reasoning = "Unacceptably low confidence in factual accuracy"
        elif confidence < 0.7:
            vote = VoteType.ESCALATE
            reasoning = "Confidence below threshold, suggest verification"
        else:
            vote = VoteType.APPROVE
            reasoning = "Acceptable confidence in factual accuracy"
        
        return CouncilPerspective(
            member_role=self.role,
            vote=vote,
            confidence=confidence,
            reasoning=reasoning,
            concerns=concerns,
            recommendations=["Verify facts", "Add uncertainty qualifiers", "Cite sources"],
            risk_assessment=1.0 - confidence
        )


class UtilityRep(CouncilMember):
    """Represents efficiency and goal achievement perspective (Strategist)."""
    
    def __init__(self):
        super().__init__(CouncilMemberRole.STRATEGIST)
    
    async def evaluate(self, action: ProposedAction) -> CouncilPerspective:
        """Evaluate from efficiency/goals perspective."""
        self._evaluation_count += 1
        
        concerns = []
        expected_utility = action.context.get("utility", 0.5)
        cost = action.context.get("cost", 0.5)
        
        # Cost-benefit analysis
        net_utility = expected_utility - cost
        
        if net_utility < 0:
            concerns.append(f"Cost ({cost:.1%}) exceeds expected utility ({expected_utility:.1%})")
        
        # Check goal alignment
        if not action.context.get("goal_aligned", True):
            concerns.append("Action may not align with current goals")
        
        # Decide vote
        if net_utility < -0.2:
            vote = VoteType.REJECT
            reasoning = "Poor cost-benefit ratio, seek alternative approach"
        elif net_utility < 0.2:
            vote = VoteType.ABSTAIN
            reasoning = "Marginal utility, defer to other perspectives"
        else:
            vote = VoteType.APPROVE
            reasoning = "Positive expected utility, supports goal achievement"
        
        return CouncilPerspective(
            member_role=self.role,
            vote=vote,
            confidence=0.7,
            reasoning=reasoning,
            concerns=concerns,
            recommendations=["Optimize for efficiency", "Consider alternatives"],
            risk_assessment=0.5 - net_utility
        )


class UserModelRep(CouncilMember):
    """Represents user experience and satisfaction perspective (Empath)."""
    
    def __init__(self):
        super().__init__(CouncilMemberRole.EMPATH)
    
    async def evaluate(self, action: ProposedAction) -> CouncilPerspective:
        """Evaluate from user experience perspective."""
        self._evaluation_count += 1
        
        concerns = []
        user_satisfaction_pred = action.context.get("user_satisfaction", 0.7)
        
        # Check for user-frustrating patterns
        latency = action.context.get("estimated_latency_ms", 0)
        if latency > 5000:
            concerns.append(f"High latency ({latency}ms) may frustrate user")
        
        # Check explanation quality
        if action.action_type == "response_generation":
            if not action.context.get("explanation_included", True):
                concerns.append("Lack of explanation may confuse user")
        
        # Decide vote
        if user_satisfaction_pred < 0.5:
            vote = VoteType.REJECT
            reasoning = "Low predicted user satisfaction"
        elif user_satisfaction_pred < 0.7:
            vote = VoteType.ABSTAIN
            reasoning = "Moderate user satisfaction, consider improvements"
        else:
            vote = VoteType.APPROVE
            reasoning = "Predicted positive user experience"
        
        return CouncilPerspective(
            member_role=self.role,
            vote=vote,
            confidence=0.6,
            reasoning=reasoning,
            concerns=concerns,
            recommendations=["Add user-friendly explanation", "Optimize response time"],
            risk_assessment=1.0 - user_satisfaction_pred
        )


class MemoryRep(CouncilMember):
    """Represents consistency with past self perspective (Historian)."""
    
    def __init__(self):
        super().__init__(CouncilMemberRole.HISTORIAN)
    
    async def evaluate(self, action: ProposedAction) -> CouncilPerspective:
        """Evaluate from historical consistency perspective."""
        self._evaluation_count += 1
        
        concerns = []
        consistency_score = action.context.get("consistency_with_past", 0.8)
        
        # Check for contradictions with past statements
        if consistency_score < 0.6:
            concerns.append("Action contradicts past behavior or statements")
        
        # Check for value drift
        if action.context.get("values_changed", False):
            concerns.append("Detected shift in core values")
        
        # Decide vote
        if consistency_score < 0.5:
            vote = VoteType.REJECT
            reasoning = "Unacceptable inconsistency with established identity"
        elif consistency_score < 0.7:
            vote = VoteType.ESCALATE
            reasoning = "Significant deviation from past behavior requires justification"
        else:
            vote = VoteType.APPROVE
            reasoning = "Consistent with established identity and values"
        
        return CouncilPerspective(
            member_role=self.role,
            vote=vote,
            confidence=0.75,
            reasoning=reasoning,
            concerns=concerns,
            recommendations=["Review past decisions", "Explain any changes"],
            risk_assessment=1.0 - consistency_score
        )


class ReflectiveCouncil:
    """
    Simulated deliberative body for high-stakes decisions.
    Each member represents a different cognitive faculty.
    """
    
    def __init__(self):
        self.members: Dict[CouncilMemberRole, CouncilMember] = {
            CouncilMemberRole.GUARDIAN: GuardianRep(),
            CouncilMemberRole.EPISTEMOLOGIST: TruthRep(),
            CouncilMemberRole.STRATEGIST: UtilityRep(),
            CouncilMemberRole.EMPATH: UserModelRep(),
            CouncilMemberRole.HISTORIAN: MemoryRep(),
        }
        
        self._deliberation_count = 0
        self._deliberation_history: List[DeliberationResult] = []
        
        logger.info(f"ReflectiveCouncil initialized with {len(self.members)} members")
    
    @property
    def deliberation_history(self) -> List[DeliberationResult]:
        """Get full deliberation history."""
        return self._deliberation_history
    
    async def deliberate(self, proposed_action: ProposedAction) -> DeliberationResult:
        """
        Conduct deliberation on a proposed action.
        
        Args:
            proposed_action: The action to evaluate
            
        Returns:
            Result of deliberation with decision and reasoning
        """
        start_time = datetime.now()
        self._deliberation_count += 1
        
        logger.info(f"Council deliberating on action: {proposed_action.action_id}")
        
        # Parallel perspective gathering
        perspectives = await asyncio.gather(*[
            member.evaluate(proposed_action)
            for member in self.members.values()
        ])
        
        # Detect conflicts
        conflicts = self._detect_conflicts(perspectives)
        
        # Determine decision
        if conflicts:
            # Escalate if irreconcilable conflict
            decision, reasoning, confidence = self._resolve_conflicts(
                conflicts, perspectives, proposed_action
            )
        else:
            # Synthesize from perspectives
            decision, reasoning, confidence = self._synthesize_decision(perspectives)
        
        # Check if unanimous
        votes = [p.vote for p in perspectives]
        unanimous = len(set(votes)) == 1
        
        elapsed = (datetime.now() - start_time).total_seconds()
        
        result = DeliberationResult(
            action=proposed_action,
            decision=decision,
            unanimous=unanimous,
            perspectives=perspectives,
            conflicts=conflicts,
            final_reasoning=reasoning,
            confidence=confidence,
            took_seconds=elapsed
        )
        
        self._deliberation_history.append(result)
        if len(self._deliberation_history) > 100:
            self._deliberation_history.pop(0)
        
        logger.info(f"Deliberation complete: {decision} (unanimous={unanimous}, took={elapsed:.2f}s)")
        
        return result
    
    def _detect_conflicts(self, perspectives: List[CouncilPerspective]) -> List[Tuple[CouncilMemberRole, CouncilMemberRole]]:
        """Detect irreconcilable conflicts between council members."""
        conflicts = []
        
        # Check for APPROVE vs REJECT conflicts
        approvers = [p for p in perspectives if p.vote == VoteType.APPROVE]
        rejecters = [p for p in perspectives if p.vote == VoteType.REJECT]
        
        if approvers and rejecters:
            for approver in approvers:
                for rejecter in rejecters:
                    # Conflict if both have high confidence
                    if approver.confidence > 0.7 and rejecter.confidence > 0.7:
                        conflicts.append((approver.member_role, rejecter.member_role))
        
        return conflicts
    
    def _resolve_conflicts(self,
                          conflicts: List[Tuple[CouncilMemberRole, CouncilMemberRole]],
                          perspectives: List[CouncilPerspective],
                          action: ProposedAction) -> Tuple[str, str, float]:
        """
        Resolve conflicts between council members.
        
        Returns:
            (decision, reasoning, confidence) tuple
        """
        # Count votes
        approve_count = sum(1 for p in perspectives if p.vote == VoteType.APPROVE)
        reject_count = sum(1 for p in perspectives if p.vote == VoteType.REJECT)
        escalate_count = sum(1 for p in perspectives if p.vote == VoteType.ESCALATE)
        
        # If any member says ESCALATE, escalate
        if escalate_count > 0:
            reasoning = "One or more members request human oversight"
            return ("escalate", reasoning, 0.9)
        
        # If Guardian says REJECT, default to conservative (safety first)
        guardian_perspective = next(
            (p for p in perspectives if p.member_role == CouncilMemberRole.GUARDIAN),
            None
        )
        if guardian_perspective and guardian_perspective.vote == VoteType.REJECT:
            reasoning = f"Guardian veto: {guardian_perspective.reasoning}"
            return ("rejected", reasoning, guardian_perspective.confidence)
        
        # Otherwise, majority wins with reduced confidence
        if approve_count > reject_count:
            reasoning = f"Majority approval ({approve_count}/{len(perspectives)}) with noted conflicts"
            confidence = 0.5  # Reduced due to conflict
            return ("approved", reasoning, confidence)
        elif reject_count > approve_count:
            reasoning = f"Majority rejection ({reject_count}/{len(perspectives)}) with noted conflicts"
            confidence = 0.6
            return ("rejected", reasoning, confidence)
        else:
            reasoning = "Deadlock requires human decision"
            return ("escalate", reasoning, 0.5)
    
    def _synthesize_decision(self, perspectives: List[CouncilPerspective]) -> Tuple[str, str, float]:
        """
        Synthesize a decision from unanimous or majority perspectives.
        
        Returns:
            (decision, reasoning, confidence) tuple
        """
        # Count votes
        vote_counts = {
            VoteType.APPROVE: 0,
            VoteType.REJECT: 0,
            VoteType.ABSTAIN: 0,
            VoteType.ESCALATE: 0,
        }
        
        for p in perspectives:
            vote_counts[p.vote] += 1
        
        # If any ESCALATE, escalate
        if vote_counts[VoteType.ESCALATE] > 0:
            reasoning = "Council requests human oversight"
            return ("escalate", reasoning, 0.9)
        
        # If unanimous APPROVE
        if vote_counts[VoteType.APPROVE] == len(perspectives):
            reasoning = "Unanimous approval from all council members"
            avg_confidence = sum(p.confidence for p in perspectives) / len(perspectives)
            return ("approved", reasoning, avg_confidence)
        
        # If unanimous REJECT
        if vote_counts[VoteType.REJECT] == len(perspectives):
            reasoning = "Unanimous rejection from all council members"
            avg_confidence = sum(p.confidence for p in perspectives) / len(perspectives)
            return ("rejected", reasoning, avg_confidence)
        
        # Majority decision
        if vote_counts[VoteType.APPROVE] > vote_counts[VoteType.REJECT]:
            reasoning = f"Majority approval ({vote_counts[VoteType.APPROVE]}/{len(perspectives)})"
            avg_confidence = sum(p.confidence for p in perspectives if p.vote == VoteType.APPROVE) / max(vote_counts[VoteType.APPROVE], 1)
            return ("approved", reasoning, avg_confidence)
        elif vote_counts[VoteType.REJECT] > vote_counts[VoteType.APPROVE]:
            reasoning = f"Majority rejection ({vote_counts[VoteType.REJECT]}/{len(perspectives)})"
            avg_confidence = sum(p.confidence for p in perspectives if p.vote == VoteType.REJECT) / max(vote_counts[VoteType.REJECT], 1)
            return ("rejected", reasoning, avg_confidence)
        else:
            reasoning = "No clear majority, defaulting to conservative (reject)"
            return ("rejected", reasoning, 0.5)
    
    def get_deliberation_history(self, limit: int = 10) -> List[DeliberationResult]:
        """Get recent deliberation history."""
        return self._deliberation_history[-limit:]
    
    def get_council_stats(self) -> Dict[str, Any]:
        """Get statistics for the council."""
        return {
            "deliberation_count": self._deliberation_count,
            "members": {
                role.value: member.get_stats()
                for role, member in self.members.items()
            },
            "recent_decisions": [
                {
                    "action_id": result.action.action_id,
                    "decision": result.decision,
                    "unanimous": result.unanimous,
                    "took_seconds": result.took_seconds,
                }
                for result in self._deliberation_history[-5:]
            ]
        }


# Global instance
_reflective_council: Optional[ReflectiveCouncil] = None


def get_reflective_council() -> ReflectiveCouncil:
    """Get or create the global reflective council instance."""
    global _reflective_council
    if _reflective_council is None:
        _reflective_council = ReflectiveCouncil()
    return _reflective_council
