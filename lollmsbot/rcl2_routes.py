"""
RCL-2 API Routes for Web UI.

Provides REST and WebSocket endpoints for the Reflective Consciousness Layer v2.0:
- Constitutional restraints management
- Cognitive state monitoring
- Reflective council deliberations
- Cognitive debt tracking
- Audit trail browsing
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect, Query, Body
from pydantic import BaseModel, Field

from lollmsbot.cognitive_core import get_cognitive_core, CognitiveState
from lollmsbot.constitutional_restraints import (
    get_constitutional_restraints,
    RestraintDimension,
    ConstitutionalRestraints,
)
from lollmsbot.reflective_council import (
    get_reflective_council,
    ProposedAction,
    CouncilRole,
)
from lollmsbot.self_awareness import get_awareness_manager
from lollmsbot.cognitive_twin import get_cognitive_twin

logger = logging.getLogger(__name__)

rcl2_router = APIRouter(
    prefix="/rcl2",
    tags=["rcl2"],
    responses={404: {"description": "Not found"}},
)


# ============================================================================
# Request/Response Models
# ============================================================================

class RestraintUpdateRequest(BaseModel):
    """Request to update a restraint dimension."""
    dimension: str = Field(..., description="Restraint dimension name")
    value: float = Field(..., ge=0.0, le=1.0, description="New value (0.0-1.0)")
    authorized: bool = Field(default=False, description="Has authorization key")
    authorization_key: Optional[str] = Field(default=None, description="Hex authorization key")


class DeliberationRequest(BaseModel):
    """Request to trigger a council deliberation."""
    action_id: str = Field(..., description="Unique action ID")
    action_type: str = Field(..., description="Type of action")
    description: str = Field(..., description="Action description")
    context: Dict[str, Any] = Field(default_factory=dict, description="Action context")
    stakes: str = Field(default="medium", description="Stakes level")


class DebtRepaymentRequest(BaseModel):
    """Request to repay cognitive debt."""
    decision_id: Optional[str] = Field(default=None, description="Specific decision ID, or None for highest priority")


# ============================================================================
# Constitutional Restraints Endpoints
# ============================================================================

@rcl2_router.get("/restraints")
async def get_restraints() -> Dict[str, Any]:
    """Get current constitutional restraint values and metadata."""
    try:
        restraints = get_constitutional_restraints()
        audit_trail = restraints.get_audit_trail()
        
        return {
            "success": True,
            "restraints": {
                # Cognitive Budgeting
                "recursion_depth": restraints.recursion_depth,
                "cognitive_budget_ms": restraints.cognitive_budget_ms,
                "simulation_fidelity": restraints.simulation_fidelity,
                # Epistemic Virtues
                "hallucination_resistance": restraints.hallucination_resistance,
                "uncertainty_propagation": restraints.uncertainty_propagation,
                "contradiction_sensitivity": restraints.contradiction_sensitivity,
                # Social Cognition
                "user_model_fidelity": restraints.user_model_fidelity,
                "transparency_level": restraints.transparency_level,
                "explanation_depth": restraints.explanation_depth,
                # Autonomy & Growth
                "self_modification_freedom": restraints.self_modification_freedom,
                "goal_inference_autonomy": restraints.goal_inference_autonomy,
                "memory_consolidation_rate": restraints.memory_consolidation_rate,
            },
            "hard_limits": restraints._hard_limits,
            "audit_summary": {
                "total_changes": len(audit_trail.changes),
                "chain_valid": audit_trail.verify_chain(),
                "unauthorized_attempts": len(audit_trail.get_unauthorized_attempts()),
            },
        }
    except Exception as e:
        logger.error(f"Error getting restraints: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@rcl2_router.post("/restraints")
async def update_restraint(request: RestraintUpdateRequest) -> Dict[str, Any]:
    """Update a constitutional restraint dimension."""
    try:
        restraints = get_constitutional_restraints()
        
        # Parse dimension
        try:
            dimension = RestraintDimension[request.dimension.upper()]
        except KeyError:
            raise HTTPException(status_code=400, detail=f"Invalid dimension: {request.dimension}")
        
        # Attempt update
        success = restraints.set_dimension(
            dimension=dimension,
            value=request.value,
            authorized=request.authorized,
            authorization_key=request.authorization_key,
        )
        
        if success:
            return {
                "success": True,
                "dimension": request.dimension,
                "value": request.value,
                "message": "Restraint updated successfully",
            }
        else:
            return {
                "success": False,
                "dimension": request.dimension,
                "value": request.value,
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


@rcl2_router.post("/council/deliberate")
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

@rcl2_router.get("/debt")
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
                data = await asyncio.wait_for(websocket.receive_json(), timeout=5.0)
                
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
        except:
            pass
