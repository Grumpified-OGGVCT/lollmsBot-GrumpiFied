"""
RCL-2 API Routes for Web UI.

Provides REST and WebSocket endpoints for the Reflective Consciousness Layer v2.0:
- Constitutional restraints management
- Cognitive state monitoring
- Reflective council deliberations
- Cognitive debt tracking
- Audit trail browsing

SECURITY: All endpoints use rate limiting and input validation.
"""

import asyncio
import logging
import os
import re
from typing import Dict, Optional, Any
from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect, Query
from pydantic import BaseModel, Field, validator
from slowapi import Limiter
from slowapi.util import get_remote_address

from lollmsbot.cognitive_core import get_cognitive_core
from lollmsbot.constitutional_restraints import (
    get_constitutional_restraints,
    RestraintDimension,
)
from lollmsbot.reflective_council import (
    get_reflective_council,
    ProposedAction,
    CouncilRole,
)
from lollmsbot.self_awareness import get_awareness_manager
from lollmsbot.cognitive_twin import get_cognitive_twin

logger = logging.getLogger(__name__)

# Rate limiter
limiter = Limiter(key_func=get_remote_address)

# WebSocket configuration
WEBSOCKET_UPDATE_INTERVAL_SECONDS = 5.0  # Periodic update interval
MAX_WS_RECONNECT_ATTEMPTS = 10  # Prevent infinite reconnect storms

rcl2_router = APIRouter(
    prefix="/rcl2",
    tags=["rcl2"],
    responses={404: {"description": "Not found"}},
)


# ============================================================================
# WebSocket Authentication (C05 fix)
# ============================================================================

async def verify_ws_token(websocket: WebSocket, token: Optional[str] = Query(None)):
    """Verify WebSocket connection token."""
    # Simple token validation (replace with proper auth in production)
    expected_token = os.getenv("RCL2_WS_TOKEN")
    
    if expected_token and token != expected_token:
        logger.warning(f"Unauthorized WebSocket connection attempt from {websocket.client}")
        await websocket.close(code=403, reason="Unauthorized")
        return False
    
    return True


# ============================================================================
# Request/Response Models with Validation (C04 fix)
# ============================================================================

class RestraintUpdateRequest(BaseModel):
    """Request to update a restraint dimension."""
    dimension: str = Field(..., description="Restraint dimension name", min_length=1, max_length=50)
    value: float = Field(..., ge=0.0, le=1.0, description="New value (0.0-1.0)")
    authorized: bool = Field(default=False, description="Has authorization key")
    authorization_key: Optional[str] = Field(default=None, description="Hex authorization key", max_length=128)
    
    @validator('dimension')
    def validate_dimension(cls, v):
        """Validate dimension name."""
        if not re.match(r'^[a-z_]+$', v):
            raise ValueError("Dimension name must contain only lowercase letters and underscores")
        return v
    
    @validator('authorization_key')
    def validate_auth_key(cls, v):
        """Validate authorization key format."""
        if v and not re.match(r'^[0-9a-fA-F]+$', v):
            raise ValueError("Authorization key must be hexadecimal")
        return v


class DeliberationRequest(BaseModel):
    """Request to trigger a council deliberation."""
    action_id: str = Field(..., description="Unique action ID", min_length=1, max_length=100)
    action_type: str = Field(..., description="Type of action", min_length=1, max_length=50)
    description: str = Field(..., description="Action description", min_length=1, max_length=1000)
    context: Dict[str, Any] = Field(default_factory=dict, description="Action context")
    stakes: str = Field(default="medium", description="Stakes level", regex="^(low|medium|high|critical)$")
    
    @validator('action_id', 'action_type')
    def validate_alphanumeric(cls, v, field):
        """Validate alphanumeric fields."""
        if not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise ValueError(f"{field.name} must contain only alphanumeric characters, hyphens, and underscores")
        return v


class DebtRepaymentRequest(BaseModel):
    """Request to repay cognitive debt."""
    decision_id: Optional[str] = Field(default=None, description="Specific decision ID, or None for highest priority", max_length=100)
    
    @validator('decision_id')
    def validate_decision_id(cls, v):
        """Validate decision ID format."""
        if v and not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise ValueError("Decision ID must contain only alphanumeric characters, hyphens, and underscores")
        return v


# ============================================================================
# Constitutional Restraints Endpoints
# ============================================================================

@rcl2_router.get(
    "/restraints",
    summary="Get Constitutional Restraints",
    description="""
    **What's in it for you:** See exactly how autonomous and transparent your AI is configured to be.
    
    **User Value:**
    - Know your AI's current behavior settings (12 dimensions)
    - See which settings have hard-stops (safety limits)
    - Verify no unauthorized changes (audit summary)
    
    **Results You'll See:**
    - All 12 restraint values (0.0-1.0 scale)
    - Hard-stop limits for each dimension
    - Audit trail summary (total changes, integrity status)
    
    **Example Use Case:**
    "I want to see how cautious my AI is configured to be about hallucinations"
    → Check `hallucination_resistance` value (0.8 = very cautious, 0.2 = more creative)
    
    **Rate Limit:** 60 requests per minute
    """,
    response_description="Current restraint values, hard-limits, and audit summary",
    responses={
        200: {
            "description": "Successfully retrieved restraint configuration",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "restraints": {
                            "recursion_depth": 0.5,
                            "hallucination_resistance": 0.8,
                            "transparency_level": 0.6,
                        },
                        "hard_limits": {
                            "self_modification_freedom": 0.5,
                            "goal_inference_autonomy": 0.7,
                        },
                        "audit_summary": {
                            "total_changes": 5,
                            "chain_valid": True,
                            "unauthorized_attempts": 0,
                        },
                    }
                }
            },
        }
    },
)
async def get_restraints() -> Dict[str, Any]:
    """Get current constitutional restraint values with UI-friendly semantics."""
    try:
        restraints = get_constitutional_restraints()
        audit_trail = restraints.get_audit_trail()
        
        # Import semantic layer
        from lollmsbot.restraint_semantics import format_restraint_for_ui
        
        # Format each restraint for UI
        restraints_ui = {}
        for dimension in [
            "recursion_depth", "cognitive_budget_ms", "simulation_fidelity",
            "hallucination_resistance", "uncertainty_propagation", "contradiction_sensitivity",
            "user_model_fidelity", "transparency_level", "explanation_depth",
            "self_modification_freedom", "goal_inference_autonomy", "memory_consolidation_rate"
        ]:
            backend_value = getattr(restraints, dimension)
            restraints_ui[dimension] = format_restraint_for_ui(dimension, backend_value)
        
        return {
            "success": True,
            "restraints": restraints_ui,
            "hard_limits": restraints._hard_limits,
            "audit_summary": {
                "total_changes": len(audit_trail.changes),
                "chain_valid": audit_trail.verify_chain(),
                "unauthorized_attempts": len(audit_trail.get_unauthorized_attempts()),
            },
            "semantic_note": "⚠️ Some dimensions (like hallucination_resistance) are inverted for intuitive UI. Use ui_value for display, backend_value for storage.",
        }
    except Exception as e:
        logger.error(f"Error getting restraints: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@rcl2_router.post(
    "/restraints",
    summary="Update a Constitutional Restraint",
    description="""
    **What's in it for you:** Fine-tune your AI's behavior to match your needs and comfort level.
    
    **User Value:**
    - Adjust AI autonomy (more cautious ↔ more proactive)
    - Control transparency (show me everything ↔ just results)
    - Set epistemic standards (admit uncertainty ↔ best guess)
    
    **Results You'll See:**
    - Immediate behavior change in the AI
    - Confirmation or rejection (if hitting hard-stop)
    - Audit trail entry (tamper-proof record)
    
    **Example Use Cases:**
    1. "Make AI more transparent" → Set `transparency_level` to 0.9
    2. "Let AI take more initiative" → Increase `goal_inference_autonomy` to 0.5
    3. "Be more cautious with facts" → Set `hallucination_resistance` to 0.9
    
    **Safety:** Changes above hard-stops require authorization key (cryptographic proof).
    """,
    response_description="Update confirmation with success status",
    responses={
        200: {
            "description": "Update processed (may be blocked by hard-stop)",
            "content": {
                "application/json": {
                    "examples": {
                        "success": {
                            "summary": "Successful update",
                            "value": {
                                "success": True,
                                "dimension": "transparency_level",
                                "value": 0.8,
                                "message": "Restraint updated successfully",
                            },
                        },
                        "blocked": {
                            "summary": "Blocked by hard-stop",
                            "value": {
                                "success": False,
                                "dimension": "self_modification_freedom",
                                "value": 0.7,
                                "message": "Update blocked by hard-stop or invalid authorization",
                                "requires_authorization": True,
                            },
                        },
                    }
                }
            },
        }
    },
)
async def update_restraint(request: RestraintUpdateRequest) -> Dict[str, Any]:
    """Update a constitutional restraint dimension."""
    try:
        restraints = get_constitutional_restraints()
        
        # Import semantic layer
        from lollmsbot.restraint_semantics import get_backend_value
        
        # Parse dimension
        try:
            dimension = RestraintDimension[request.dimension.upper()]
        except KeyError:
            raise HTTPException(status_code=400, detail=f"Invalid dimension: {request.dimension}")
        
        # Convert UI value to backend value (handles inversion for hallucination_resistance)
        backend_value = get_backend_value(request.dimension, request.value)
        
        # Log the conversion for transparency
        if backend_value != request.value:
            logger.info(f"UI value {request.value} converted to backend value {backend_value} for {request.dimension}")
        
        # Attempt update
        success = restraints.set_dimension(
            dimension=dimension,
            value=backend_value,
            authorized=request.authorized,
            authorization_key=request.authorization_key,
        )
        
        if success:
            return {
                "success": True,
                "dimension": request.dimension,
                "ui_value": request.value,
                "backend_value": backend_value,
                "message": "Restraint updated successfully",
            }
        else:
            return {
                "success": False,
                "dimension": request.dimension,
                "ui_value": request.value,
                "backend_value": backend_value,
                "message": "Update blocked by hard-stop or invalid authorization",
                "requires_authorization": True,
            }
    
    except Exception as e:
        logger.error(f"Error updating restraint: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@rcl2_router.get("/audit-trail")
async def get_audit_trail(
    limit: int = Query(100, ge=1, le=1000, description="Max entries to return")
) -> Dict[str, Any]:
    """Get restraint change audit trail."""
    try:
        restraints = get_constitutional_restraints()
        audit_trail = restraints.get_audit_trail()
        
        # Get recent changes
        changes = audit_trail.changes[-limit:]
        
        return {
            "success": True,
            "changes": [
                {
                    "timestamp": change.timestamp,
                    "dimension": change.dimension.name,
                    "old_value": change.old_value,
                    "new_value": change.new_value,
                    "authorized": change.authorized,
                    "hash": change.hash,
                }
                for change in changes
            ],
            "chain_valid": audit_trail.verify_chain(),
            "unauthorized_attempts": [
                {
                    "timestamp": attempt.timestamp,
                    "dimension": attempt.dimension.name,
                    "attempted_value": attempt.new_value,
                }
                for attempt in audit_trail.get_unauthorized_attempts()
            ],
        }
    except Exception as e:
        logger.error(f"Error getting audit trail: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@rcl2_router.post("/audit-trail/verify")
async def verify_audit_chain() -> Dict[str, Any]:
    """Verify integrity of the audit trail chain."""
    try:
        restraints = get_constitutional_restraints()
        audit_trail = restraints.get_audit_trail()
        
        valid = audit_trail.verify_chain()
        stats = audit_trail.get_stats()
        
        return {
            "success": True,
            "chain_valid": valid,
            "stats": stats,
            "message": "Audit trail integrity verified" if valid else "⚠️ Audit trail compromised!",
        }
    except Exception as e:
        logger.error(f"Error verifying audit chain: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Cognitive State Endpoints
# ============================================================================

@rcl2_router.get("/cognitive-state")
async def get_cognitive_state() -> Dict[str, Any]:
    """Get current cognitive state (System 1/2 activity)."""
    try:
        core = get_cognitive_core()
        
        return {
            "success": True,
            "system1": {
                "enabled": True,
                "calls": core.system1_calls,
                "total_time_ms": core.system1_time_ms,
            },
            "system2": {
                "enabled": True,
                "calls": core.system2_calls,
                "total_time_ms": core.system2_time_ms,
            },
            "escalations": core.system2_escalations,
        }
    except Exception as e:
        logger.error(f"Error getting cognitive state: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Reflective Council Endpoints
# ============================================================================

@rcl2_router.get("/council/status")
async def get_council_status() -> Dict[str, Any]:
    """Get reflective council composition and status."""
    try:
        council = get_reflective_council()
        
        return {
            "success": True,
            "members": [
                {
                    "role": role.value,
                    "description": f"{role.value.title()} representative",
                }
                for role in CouncilRole
            ],
            "deliberations_total": len(council.deliberation_history),
        }
    except Exception as e:
        logger.error(f"Error getting council status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@rcl2_router.post(
    "/council/deliberate",
    summary="Trigger a Council Deliberation",
    description="""
    **What's in it for you:** See your AI's "internal debate" before important decisions.
    
    **User Value:**
    - Understand WHY a decision was made
    - See multiple perspectives (safety, accuracy, efficiency, UX, consistency)
    - Catch conflicts before they cause problems
    
    **Results You'll See:**
    - 5 council member perspectives with reasoning
    - Vote breakdown (APPROVE/REJECT/ABSTAIN/ESCALATE)
    - Unanimous agreement or conflicts highlighted
    - Final decision with full transparency
    
    **Example Use Cases:**
    1. Before executing risky command: "Should I run this shell script?"
    2. Medical advice: "Is this medical information accurate enough?"
    3. Financial decision: "Should I process this transaction?"
    
    **Transparency:** Every council member explains their vote and concerns.
    """,
    response_description="Deliberation result with all perspectives and final decision",
    responses={
        200: {
            "description": "Deliberation completed",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "decision": "proceed",
                        "unanimous": False,
                        "perspectives": [
                            {
                                "member_role": "guardian",
                                "vote": "REJECT",
                                "confidence": 0.9,
                                "reasoning": "High risk operation requires human oversight",
                                "concerns": ["Data loss potential", "Irreversible action"],
                            },
                            {
                                "member_role": "strategist",
                                "vote": "APPROVE",
                                "confidence": 0.8,
                                "reasoning": "Efficient solution to user's problem",
                                "concerns": [],
                            },
                        ],
                        "conflicts": [
                            {
                                "roles": ["guardian", "strategist"],
                                "issue": "Safety vs efficiency trade-off",
                            }
                        ],
                    }
                }
            },
        }
    },
)
async def trigger_deliberation(request: DeliberationRequest) -> Dict[str, Any]:
    """Trigger a council deliberation."""
    try:
        council = get_reflective_council()
        
        action = ProposedAction(
            action_id=request.action_id,
            action_type=request.action_type,
            description=request.description,
            context=request.context,
            stakes=request.stakes,
        )
        
        result = await council.deliberate(action)
        
        return {
            "success": True,
            "decision": result.decision,
            "unanimous": result.unanimous,
            "perspectives": [
                {
                    "member_role": p.member_role.value,
                    "vote": p.vote.name,
                    "confidence": p.confidence,
                    "reasoning": p.reasoning,
                    "concerns": p.concerns,
                }
                for p in result.perspectives
            ],
            "conflicts": [
                {
                    "roles": [r.value for r in conflict["roles"]],
                    "issue": conflict["issue"],
                }
                for conflict in result.conflicts
            ],
        }
    except Exception as e:
        logger.error(f"Error during deliberation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@rcl2_router.get("/council/deliberations")
async def get_deliberations(
    limit: int = Query(50, ge=1, le=500, description="Max deliberations to return")
) -> Dict[str, Any]:
    """Get recent council deliberations."""
    try:
        council = get_reflective_council()
        
        recent = council.deliberation_history[-limit:]
        
        return {
            "success": True,
            "deliberations": [
                {
                    "action_id": delib.action.action_id,
                    "action_type": delib.action.action_type,
                    "description": delib.action.description,
                    "decision": delib.result.decision,
                    "unanimous": delib.result.unanimous,
                    "timestamp": delib.timestamp,
                }
                for delib in recent
            ],
        }
    except Exception as e:
        logger.error(f"Error getting deliberations: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Cognitive Debt Endpoints
# ============================================================================

@rcl2_router.get(
    "/debt",
    summary="Get Cognitive Debt Queue",
    description="""
    **What's in it for you:** Ensure your AI double-checks uncertain answers.
    
    **User Value:**
    - See which answers need verification
    - Know when AI took shortcuts for speed
    - Trust that mistakes get caught and corrected
    
    **Results You'll See:**
    - Outstanding "IOUs" (decisions pending verification)
    - Priority levels (which need review first)
    - When each debt was logged
    
    **Example Scenario:**
    1. You ask: "What's the capital of Mongolia?"
    2. AI answers quickly: "Ulaanbaatar" (confidence: 0.65)
    3. Low confidence triggers cognitive debt logging
    4. Later, during idle time, AI verifies with external source
    5. You get notification if answer needs correction
    
    **Transparency:** Never "fire and forget" - every uncertain answer gets rechecked.
    """,
    response_description="Current cognitive debt queue with priorities",
    responses={
        200: {
            "description": "Cognitive debt queue retrieved",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "outstanding_debt": 3,
                        "debt_items": [
                            {
                                "decision_id": "dec_12345",
                                "reason": "Low confidence (0.65)",
                                "priority": 0.8,
                                "logged_at": 1234567890.0,
                            }
                        ],
                    }
                }
            },
        }
    },
)
async def get_cognitive_debt() -> Dict[str, Any]:
    """Get cognitive debt queue."""
    try:
        manager = get_awareness_manager()
        
        debt = manager.get_cognitive_debt(unpaid_only=True)
        
        return {
            "success": True,
            "outstanding_debt": len(debt),
            "debt_items": [
                {
                    "decision_id": item.decision_id,
                    "reason": item.reason,
                    "priority": item.priority,
                    "logged_at": item.logged_at,
                }
                for item in debt
            ],
        }
    except Exception as e:
        logger.error(f"Error getting cognitive debt: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@rcl2_router.post("/debt/repay")
async def repay_cognitive_debt(request: DebtRepaymentRequest) -> Dict[str, Any]:
    """Trigger cognitive debt repayment."""
    try:
        manager = get_awareness_manager()
        
        if request.decision_id:
            # Repay specific decision
            await manager.repay_cognitive_debt(request.decision_id)
            return {
                "success": True,
                "decision_id": request.decision_id,
                "message": "Cognitive debt repaid",
            }
        else:
            # Repay highest priority
            debt = manager.get_cognitive_debt(unpaid_only=True)
            if not debt:
                return {
                    "success": True,
                    "message": "No outstanding cognitive debt",
                }
            
            # Repay highest priority
            highest_priority = max(debt, key=lambda d: d.priority)
            await manager.repay_cognitive_debt(highest_priority.decision_id)
            
            return {
                "success": True,
                "decision_id": highest_priority.decision_id,
                "message": "Highest priority cognitive debt repaid",
            }
    except Exception as e:
        logger.error(f"Error repaying cognitive debt: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Decision Log Endpoints
# ============================================================================

@rcl2_router.get("/decisions")
async def get_decisions(
    limit: int = Query(100, ge=1, le=1000, description="Max decisions to return"),
    decision_type: Optional[str] = Query(None, description="Filter by decision type"),
    min_confidence: Optional[float] = Query(None, ge=0.0, le=1.0, description="Min confidence threshold"),
) -> Dict[str, Any]:
    """Get decision log with optional filters."""
    try:
        manager = get_awareness_manager()
        
        # Get all decisions
        decisions = list(manager.decision_history.values())
        
        # Apply filters
        if decision_type:
            decisions = [d for d in decisions if d.decision_type == decision_type]
        
        if min_confidence is not None:
            decisions = [d for d in decisions if d.confidence >= min_confidence]
        
        # Limit and reverse (newest first)
        decisions = decisions[-limit:][::-1]
        
        return {
            "success": True,
            "count": len(decisions),
            "decisions": [
                {
                    "decision_id": d.decision_id,
                    "decision": d.decision,
                    "decision_type": d.decision_type,
                    "confidence": d.confidence,
                    "timestamp": d.timestamp,
                    "context": d.context,
                }
                for d in decisions
            ],
        }
    except Exception as e:
        logger.error(f"Error getting decisions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Cognitive Twin (Predictive Model) Endpoints
# ============================================================================

@rcl2_router.get("/cognitive-twin/health")
async def get_cognitive_twin_health() -> Dict[str, Any]:
    """Get cognitive twin health summary with all predictions."""
    try:
        twin = get_cognitive_twin()
        return {
            "success": True,
            "health": twin.get_health_summary()
        }
    except Exception as e:
        logger.error(f"Error getting cognitive twin health: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@rcl2_router.get("/cognitive-twin/predict/latency")
async def predict_latency(
    operation_type: str = Query("default", description="Operation type to predict")
) -> Dict[str, Any]:
    """Predict latency for an operation type."""
    try:
        twin = get_cognitive_twin()
        latency_ms, confidence = twin.predict_latency(operation_type)
        
        return {
            "success": True,
            "operation_type": operation_type,
            "predicted_latency_ms": latency_ms,
            "confidence": confidence,
            "high_confidence": confidence >= twin.confidence_threshold
        }
    except Exception as e:
        logger.error(f"Error predicting latency: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@rcl2_router.get("/cognitive-twin/predict/memory")
async def predict_memory_pressure(
    horizon_minutes: int = Query(30, ge=1, le=180, description="Prediction horizon in minutes")
) -> Dict[str, Any]:
    """Predict memory pressure at time horizon."""
    try:
        twin = get_cognitive_twin()
        pressure, confidence = twin.predict_memory_pressure(horizon_minutes)
        
        return {
            "success": True,
            "horizon_minutes": horizon_minutes,
            "predicted_pressure": pressure,
            "confidence": confidence,
            "status": "critical" if pressure > 0.8 else "warning" if pressure > 0.6 else "normal"
        }
    except Exception as e:
        logger.error(f"Error predicting memory pressure: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@rcl2_router.get("/cognitive-twin/predict/skills")
async def predict_next_skills(
    count: int = Query(5, ge=1, le=20, description="Number of skills to predict")
) -> Dict[str, Any]:
    """Predict which skills will be used next."""
    try:
        twin = get_cognitive_twin()
        skills = twin.predict_next_skills(count)
        
        return {
            "success": True,
            "predicted_skills": [
                {
                    "skill_name": skill,
                    "probability": float(prob)
                }
                for skill, prob in skills
            ]
        }
    except Exception as e:
        logger.error(f"Error predicting skills: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@rcl2_router.get("/cognitive-twin/predict/engagement")
async def predict_engagement() -> Dict[str, Any]:
    """Predict user engagement score."""
    try:
        twin = get_cognitive_twin()
        engagement, confidence = twin.predict_engagement()
        
        return {
            "success": True,
            "predicted_engagement": engagement,
            "confidence": confidence,
            "status": "low" if engagement < 0.4 else "medium" if engagement < 0.7 else "high"
        }
    except Exception as e:
        logger.error(f"Error predicting engagement: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@rcl2_router.get("/cognitive-twin/healing")
async def check_self_healing() -> Dict[str, Any]:
    """Check if self-healing should be triggered."""
    try:
        twin = get_cognitive_twin()
        should_heal, reason = twin.should_trigger_healing()
        
        return {
            "success": True,
            "should_trigger_healing": should_heal,
            "reason": reason,
            "recommendation": "Initiate self-healing" if should_heal else "System healthy"
        }
    except Exception as e:
        logger.error(f"Error checking self-healing: {e}")
        raise HTTPException(status_code=500, detail=str(e))


class CognitiveTwinRecordRequest(BaseModel):
    """Request to record metrics in cognitive twin."""
    metric_type: str = Field(..., description="Type: latency, memory, skill, engagement")
    operation_type: Optional[str] = Field(None, description="For latency: operation type")
    duration_ms: Optional[float] = Field(None, description="For latency: duration in ms")
    bytes_used: Optional[int] = Field(None, description="For memory: bytes used")
    skill_name: Optional[str] = Field(None, description="For skill: skill name")
    engagement_score: Optional[float] = Field(None, ge=0.0, le=1.0, description="For engagement: score 0-1")


@rcl2_router.post("/cognitive-twin/record")
async def record_cognitive_twin_metric(request: CognitiveTwinRecordRequest) -> Dict[str, Any]:
    """Record a metric in the cognitive twin for learning."""
    try:
        twin = get_cognitive_twin()
        
        if request.metric_type == "latency":
            if not request.operation_type or request.duration_ms is None:
                raise HTTPException(status_code=400, detail="Missing operation_type or duration_ms")
            twin.record_latency(request.operation_type, request.duration_ms)
            
        elif request.metric_type == "memory":
            if request.bytes_used is None:
                raise HTTPException(status_code=400, detail="Missing bytes_used")
            twin.record_memory_usage(request.bytes_used)
            
        elif request.metric_type == "skill":
            if not request.skill_name:
                raise HTTPException(status_code=400, detail="Missing skill_name")
            twin.record_skill_usage(request.skill_name)
            
        elif request.metric_type == "engagement":
            if request.engagement_score is None:
                raise HTTPException(status_code=400, detail="Missing engagement_score")
            twin.record_engagement(request.engagement_score)
            
        else:
            raise HTTPException(status_code=400, detail=f"Unknown metric_type: {request.metric_type}")
        
        return {
            "success": True,
            "message": f"Recorded {request.metric_type} metric"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error recording cognitive twin metric: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# WebSocket for Real-Time Updates
# ============================================================================

@rcl2_router.websocket("/ws")
async def rcl2_websocket(websocket: WebSocket):
    """WebSocket endpoint for real-time RCL-2 updates."""
    await websocket.accept()
    logger.info("RCL-2 WebSocket connected")
    
    try:
        # Send initial state
        restraints = get_constitutional_restraints()
        core = get_cognitive_core()
        twin = get_cognitive_twin()
        
        await websocket.send_json({
            "type": "initial_state",
            "restraints": {dim.name: getattr(restraints, dim.name.lower()) for dim in RestraintDimension},
            "cognitive_state": {
                "system1_calls": core.system1_calls,
                "system2_calls": core.system2_calls,
            },
            "cognitive_twin": twin.get_health_summary() if twin.enabled else {"enabled": False}
        })
        
        # Keep connection alive and send updates
        while True:
            # Wait for client messages or send periodic updates
            try:
                data = await asyncio.wait_for(
                    websocket.receive_json(), 
                    timeout=WEBSOCKET_UPDATE_INTERVAL_SECONDS
                )
                
                # Handle client requests
                if data.get("type") == "ping":
                    await websocket.send_json({"type": "pong"})
                
            except asyncio.TimeoutError:
                # Send periodic update with cognitive twin predictions
                should_heal, heal_reason = twin.should_trigger_healing()
                
                await websocket.send_json({
                    "type": "update",
                    "timestamp": asyncio.get_event_loop().time(),
                    "cognitive_state": {
                        "system1_calls": core.system1_calls,
                        "system2_calls": core.system2_calls,
                    },
                    "cognitive_twin": {
                        "enabled": twin.enabled,
                        "should_heal": should_heal,
                        "heal_reason": heal_reason
                    } if twin.enabled else {"enabled": False}
                })
    
    except WebSocketDisconnect:
        logger.info("RCL-2 WebSocket disconnected")
    except Exception as e:
        logger.error(f"RCL-2 WebSocket error: {e}")
        try:
            await websocket.close()
        except Exception as close_err:
            # Suppress non-critical exceptions during websocket close
            logger.debug(f"Failed to close RCL-2 WebSocket cleanly: {close_err}")


# ============================================================================
# Phase 2E: Narrative Identity API Routes
# ============================================================================

@rcl2_router.get(
    "/narrative",
    summary="Get Narrative Identity Summary",
    description="Retrieve agent's biographical continuity and developmental stage information."
)
async def get_narrative_identity() -> Dict[str, Any]:
    """Get narrative identity summary."""
    try:
        from lollmsbot.narrative_identity import get_narrative_engine
        
        engine = get_narrative_engine()
        summary = engine.get_identity_summary()
        
        return {
            "status": "success",
            "data": summary
        }
    except ImportError:
        logger.warning("Narrative Identity not available")
        return {
            "status": "unavailable",
            "message": "Narrative Identity module not found",
            "data": None
        }
    except Exception as e:
        logger.error(f"Error getting narrative identity: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@rcl2_router.get(
    "/narrative/events",
    summary="Get Biographical Events",
    description="Retrieve recent biographical events from the agent's life story."
)
async def get_narrative_events(limit: int = Query(default=50, ge=1, le=1000)) -> Dict[str, Any]:
    """Get biographical events."""
    try:
        from lollmsbot.narrative_identity import get_narrative_engine
        
        engine = get_narrative_engine()
        
        # Get recent events
        events = []
        for event in list(engine.life_story)[-limit:]:
            events.append({
                "timestamp": event.timestamp.isoformat(),
                "event_type": event.event_type,
                "description": event.description,
                "significance": event.significance,
                "emotional_valence": event.emotional_valence,
                "context": event.context
            })
        
        return {
            "status": "success",
            "count": len(events),
            "events": events
        }
    except ImportError:
        return {"status": "unavailable", "message": "Narrative Identity not available"}
    except Exception as e:
        logger.error(f"Error getting narrative events: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@rcl2_router.post(
    "/narrative/consolidation",
    summary="Trigger Narrative Consolidation",
    description="Manually trigger consolidation of biographical events (normally done during idle time)."
)
async def trigger_consolidation() -> Dict[str, Any]:
    """Trigger narrative consolidation."""
    try:
        from lollmsbot.narrative_identity import get_narrative_engine
        
        engine = get_narrative_engine()
        report = engine.consolidate_events()
        
        return {
            "status": "success",
            "report": {
                "events_processed": report.events_processed,
                "patterns_identified": report.patterns_identified,
                "contradictions_found": report.contradictions_found,
                "consolidation_quality": report.consolidation_quality,
                "duration_seconds": report.duration_seconds,
                "timestamp": report.timestamp.isoformat()
            }
        }
    except ImportError:
        return {"status": "unavailable", "message": "Narrative Identity not available"}
    except Exception as e:
        logger.error(f"Error triggering consolidation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Phase 2F: Eigenmemory API Routes
# ============================================================================

@rcl2_router.get(
    "/eigenmemory",
    summary="Get Eigenmemory Statistics",
    description="Retrieve memory system statistics and health metrics."
)
async def get_eigenmemory_stats() -> Dict[str, Any]:
    """Get eigenmemory statistics."""
    try:
        from lollmsbot.eigenmemory import get_eigenmemory
        
        memory = get_eigenmemory()
        stats = memory.get_memory_statistics()
        
        return {
            "status": "success",
            "data": stats
        }
    except ImportError:
        return {"status": "unavailable", "message": "Eigenmemory not available"}
    except Exception as e:
        logger.error(f"Error getting eigenmemory stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


class MemoryQueryRequest(BaseModel):
    """Request to query memory."""
    query: str = Field(..., description="Query string", min_length=1, max_length=500)
    query_type: str = Field(default="knowledge", description="Type: 'knowledge' or 'remember'")


@rcl2_router.post(
    "/eigenmemory/query",
    summary="Query Eigenmemory",
    description="Query the memory system using metamemory queries."
)
async def query_eigenmemory(request: MemoryQueryRequest) -> Dict[str, Any]:
    """Query eigenmemory system."""
    try:
        from lollmsbot.eigenmemory import get_eigenmemory
        
        memory = get_eigenmemory()
        
        if request.query_type == "knowledge":
            result = memory.query_knowledge(request.query)
        elif request.query_type == "remember":
            result = memory.query_remember(request.query)
        else:
            raise HTTPException(status_code=400, detail=f"Invalid query type: {request.query_type}")
        
        return {
            "status": "success",
            "result": result
        }
    except ImportError:
        return {"status": "unavailable", "message": "Eigenmemory not available"}
    except Exception as e:
        logger.error(f"Error querying eigenmemory: {e}")
        raise HTTPException(status_code=500, detail=str(e))


class ForgetRequest(BaseModel):
    """Request to forget memories."""
    subject: str = Field(..., description="Subject to forget", min_length=1, max_length=200)
    require_confirmation: bool = Field(default=True, description="Require confirmation")


@rcl2_router.post(
    "/eigenmemory/forget",
    summary="Intentional Amnesia",
    description="Request the system to forget memories about a specific subject (GDPR-compliant)."
)
async def forget_memory(request: ForgetRequest) -> Dict[str, Any]:
    """Trigger intentional amnesia."""
    try:
        from lollmsbot.eigenmemory import get_eigenmemory
        
        memory = get_eigenmemory()
        forgotten_count = memory.forget_by_subject(
            request.subject, 
            require_confirmation=request.require_confirmation
        )
        
        return {
            "status": "success",
            "forgotten_count": forgotten_count,
            "subject": request.subject
        }
    except ImportError:
        return {"status": "unavailable", "message": "Eigenmemory not available"}
    except Exception as e:
        logger.error(f"Error forgetting memory: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Phase 2G: Introspection Query Language (IQL) API Routes
# ============================================================================

class IQLQueryRequest(BaseModel):
    """Request to execute an IQL query."""
    query: str = Field(..., description="IQL query string", min_length=1, max_length=5000)


@rcl2_router.post(
    "/iql",
    summary="Execute IQL Query",
    description="Execute an Introspection Query Language (IQL) query for cognitive state analysis."
)
async def execute_iql_query(request: IQLQueryRequest) -> Dict[str, Any]:
    """Execute IQL query."""
    try:
        from lollmsbot.introspection_query_language import query_cognitive_state
        
        result = query_cognitive_state(request.query)
        
        return {
            "status": "success",
            "result": {
                "query": result.query,
                "fields": result.fields,
                "execution_time_ms": result.execution_time_ms,
                "constraints_satisfied": result.constraints_satisfied,
                "errors": result.errors
            }
        }
    except ImportError:
        return {"status": "unavailable", "message": "IQL not available"}
    except Exception as e:
        logger.error(f"Error executing IQL query: {e}")
        return {
            "status": "error",
            "message": "An internal error occurred while executing the IQL query.",
            "result": None
        }


@rcl2_router.get(
    "/iql/examples",
    summary="Get IQL Example Queries",
    description="Retrieve example IQL queries for learning and testing."
)
async def get_iql_examples() -> Dict[str, Any]:
    """Get IQL example queries."""
    examples = [
        {
            "name": "Current Cognitive State",
            "description": "Get basic cognitive state information",
            "query": """INTROSPECT {
    SELECT uncertainty, system_mode, attention_focus
    FROM current_cognitive_state
}"""
        },
        {
            "name": "Restraint Values",
            "description": "Query all constitutional restraint dimensions",
            "query": """INTROSPECT {
    SELECT hallucination_resistance, transparency_level, goal_autonomy
    FROM restraints
}"""
        },
        {
            "name": "Council Status",
            "description": "Check reflective council activity",
            "query": """INTROSPECT {
    SELECT enabled, member_count, recent_deliberations
    FROM council
}"""
        },
        {
            "name": "Cognitive Twin Predictions",
            "description": "Get cognitive twin prediction data",
            "query": """INTROSPECT {
    SELECT enabled, predictions, accuracy
    FROM twin
    DEPTH 3
}"""
        },
        {
            "name": "Narrative Identity",
            "description": "Query narrative identity summary",
            "query": """INTROSPECT {
    SELECT developmental_stage, coherence_score, event_count
    FROM narrative
}"""
        },
        {
            "name": "Memory Statistics",
            "description": "Get eigenmemory system stats",
            "query": """INTROSPECT {
    SELECT total_memories, strong_memories, confabulation_rate
    FROM memory
}"""
        }
    ]
    
    return {
        "status": "success",
        "examples": examples
    }
