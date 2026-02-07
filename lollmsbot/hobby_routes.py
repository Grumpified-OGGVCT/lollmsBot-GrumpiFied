"""
Autonomous Hobby API Routes - FastAPI endpoints for hobby system monitoring and control
"""

from fastapi import APIRouter, HTTPException, Depends, Query, Request
from pydantic import BaseModel, Field
from typing import Dict, Any, List
import time
from collections import defaultdict
import threading

from lollmsbot.autonomous_hobby import (
    get_hobby_manager,
    HobbyType,
    start_autonomous_learning,
    stop_autonomous_learning,
)

router = APIRouter(prefix="/hobby", tags=["Autonomous Learning"])


# Simple rate limiting (in-memory)
_rate_limit_data = defaultdict(list)
_rate_limit_lock = threading.Lock()


def check_rate_limit(identifier: str, max_requests: int = 100, window_seconds: int = 60) -> bool:
    """Check if request is within rate limit.
    
    Args:
        identifier: Unique identifier (IP, user_id, etc.)
        max_requests: Maximum requests allowed in window
        window_seconds: Time window in seconds
        
    Returns:
        True if within limit, False if exceeded
    """
    now = time.time()
    cutoff = now - window_seconds
    
    with _rate_limit_lock:
        # Clean old entries
        _rate_limit_data[identifier] = [
            ts for ts in _rate_limit_data[identifier] if ts > cutoff
        ]
        
        # Check limit
        if len(_rate_limit_data[identifier]) >= max_requests:
            return False
        
        # Add current request
        _rate_limit_data[identifier].append(now)
        return True


async def rate_limit_dependency(request: Request) -> None:
    """FastAPI dependency for rate limiting."""
    # Use client IP and path for rate limiting
    client_host = request.client.host if request.client else "unknown"
    path = request.url.path
    identifier = f"{client_host}:{path}"
    
    if not check_rate_limit(identifier, max_requests=100, window_seconds=60):
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded. Maximum 100 requests per minute."
        )


class HobbyAssignment(BaseModel):
    """Request model for assigning hobby to sub-agent."""
    subagent_id: str = Field(min_length=1, max_length=100, description="Sub-agent identifier")
    hobby_type: str = Field(description="Type of hobby to assign")
    duration_minutes: float = Field(ge=0.1, le=60.0, description="Duration in minutes (0.1-60.0)")


@router.get(
    "/status",
    summary="Get Hobby System Status",
    description="""
    **What's in it for you:** See exactly what your AI is learning when idle.
    
    **User Value:**
    - Monitor autonomous learning progress
    - See which skills are being practiced
    - Track proficiency improvements over time
    - Understand what your AI is passionate about
    
    **Returns:**
    - Current activity (if any)
    - Overall learning progress by hobby type
    - Recent activities and insights gained
    - Whether the system is currently idle
    
    **Example Use Cases:**
    - Check what your AI learned overnight
    - See if it's improving in weak areas
    - Monitor engagement with different learning activities
    """,
    dependencies=[Depends(rate_limit_dependency)]
)
async def get_hobby_status() -> Dict[str, Any]:
    """Get current status of the autonomous hobby system."""
    try:
        manager = get_hobby_manager()
        return {
            "enabled": manager.config.enabled,
            "progress": manager.get_progress_summary(),
            "recent_activities": manager.get_recent_activities(10),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to get hobby status")


@router.get(
    "/progress",
    summary="Get Learning Progress",
    description="""
    **What's in it for you:** Detailed view of continuous self-improvement progress.
    
    **User Value:**
    - Track proficiency across all hobby types
    - See time invested in each area
    - Monitor success rates and engagement
    - Identify areas of strength and weakness
    
    **Why This Matters:**
    This shows that your AI is genuinely improving over time, not just
    generating static responses. You can see measurable progress in:
    - Skill execution speed and accuracy
    - Knowledge depth and breadth
    - Pattern recognition abilities
    - Tool mastery
    """,
    dependencies=[Depends(rate_limit_dependency)]
)
async def get_learning_progress() -> Dict[str, Any]:
    """Get detailed learning progress across all hobby types."""
    try:
        manager = get_hobby_manager()
        return manager.get_progress_summary()
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to get progress")


@router.get(
    "/activities",
    summary="Get Recent Activities",
    description="""
    **What's in it for you:** See what your AI has been learning recently.
    
    **Returns:** List of recent hobby activities with:
    - Type of activity (skill practice, knowledge exploration, etc.)
    - Duration and success status
    - Insights gained during the activity
    - Performance metrics
    - Engagement score (how "interested" the AI was)
    """,
    dependencies=[Depends(rate_limit_dependency)]
)
async def get_recent_activities(count: int = Query(default=20, ge=1, le=100)) -> List[Dict[str, Any]]:
    """Get recent hobby activities (max 100)."""
    try:
        manager = get_hobby_manager()
        return manager.get_recent_activities(min(count, 100))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to get activities")


@router.post(
    "/start",
    summary="Start Autonomous Learning",
    description="""
    **What's in it for you:** Enable continuous self-improvement.
    
    **User Value:**
    - Your AI learns and improves even when idle
    - Skills get sharper over time
    - Knowledge base expands automatically
    - Performance benchmarks run in the background
    
    **This implements the vision:**
    "An AI that genuinely gets better at coding every single day through
    transparent, governed, measurable self-improvement."
    """,
    dependencies=[Depends(rate_limit_dependency)]
)
async def start_hobby_system() -> Dict[str, str]:
    """Start the autonomous hobby system."""
    try:
        await start_autonomous_learning()
        return {
            "status": "started",
            "message": "Autonomous learning system activated",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to start hobby system")


@router.post(
    "/stop",
    summary="Stop Autonomous Learning",
    description="""
    **What's in it for you:** Disable background learning activities.
    
    **Use Cases:**
    - Conserve system resources
    - Temporarily pause learning
    - Prepare for system shutdown
    
    **Note:** Progress is automatically saved before stopping.
    """,
    dependencies=[Depends(rate_limit_dependency)]
)
async def stop_hobby_system() -> Dict[str, str]:
    """Stop the autonomous hobby system."""
    try:
        await stop_autonomous_learning()
        return {
            "status": "stopped",
            "message": "Autonomous learning system deactivated, progress saved",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to stop hobby system")


@router.get(
    "/config",
    summary="Get Hobby Configuration",
    description="""
    **What's in it for you:** See how autonomous learning is configured.
    
    **Returns:**
    - Which hobbies are enabled
    - Learning parameters (intensity, variety, focus)
    - Timing settings (intervals, idle thresholds)
    """,
    dependencies=[Depends(rate_limit_dependency)]
)
async def get_hobby_config() -> Dict[str, Any]:
    """Get current hobby system configuration."""
    try:
        manager = get_hobby_manager()
        return {
            "enabled": manager.config.enabled,
            "interval_minutes": manager.config.interval_minutes,
            "idle_threshold_minutes": manager.config.idle_threshold_minutes,
            "max_hobby_duration_minutes": manager.config.max_hobby_duration_minutes,
            "hobbies_enabled": {
                hobby.name: enabled
                for hobby, enabled in manager.config.hobbies_enabled.items()
            },
            "focus_on_weaknesses": manager.config.focus_on_weaknesses,
            "variety_factor": manager.config.variety_factor,
            "intensity_level": manager.config.intensity_level,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to get config")


@router.post(
    "/assign-to-subagent",
    summary="Assign Hobby to Sub-Agent",
    description="""
    **What's in it for you:** Queue learning tasks for sub-agent execution.
    
    **Current Status:** Creates assignment metadata. Sub-agent dispatch requires
    RC2 META_LEARNING capability integration (Phase 3).
    
    **How It Works:**
    Creates an assignment record that can be used by external sub-agent
    orchestration systems or future integrated dispatch.
    """,
    dependencies=[Depends(rate_limit_dependency)]
)
async def assign_hobby_to_subagent(assignment: HobbyAssignment) -> Dict[str, Any]:
    """Assign a hobby activity to a sub-agent (queues assignment metadata)."""
    try:
        # Validate hobby type
        try:
            hobby_enum = HobbyType[assignment.hobby_type.upper()]
        except KeyError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid hobby type: {assignment.hobby_type}. "
                       f"Valid types: {[h.name for h in HobbyType]}",
            )
        
        manager = get_hobby_manager()
        result = manager.assign_hobby_to_subagent(
            subagent_id=assignment.subagent_id,
            hobby_type=hobby_enum,
            duration_minutes=assignment.duration_minutes,
        )
        
        return {
            "status": "queued",
            "assignment": result,
            "note": "Assignment metadata created. Requires external dispatch or Phase 3 RC2 integration."
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to assign hobby")


@router.get(
    "/hobby-types",
    summary="List Available Hobby Types",
    description="""
    **What's in it for you:** Discover all the ways your AI can improve itself.
    
    **Hobby Types:**
    - **SKILL_PRACTICE**: Practice and improve existing skills
    - **KNOWLEDGE_EXPLORATION**: Explore and expand knowledge graph
    - **PATTERN_RECOGNITION**: Analyze patterns in past interactions
    - **BENCHMARK_RUNNING**: Run self-evaluation benchmarks
    - **TOOL_MASTERY**: Practice tool usage and combinations
    - **CODE_ANALYSIS**: Analyze codebase for improvements (advanced)
    - **RESEARCH_INTEGRATION**: Learn from new research papers (advanced)
    - **CREATIVE_PROBLEM_SOLVING**: Practice creative approaches
    
    Each hobby type contributes to the AI's continuous self-improvement
    in different ways, implementing the vision of an AI that "genuinely
    gets better every single day."
    """,
    dependencies=[Depends(rate_limit_dependency)]
)
async def list_hobby_types() -> Dict[str, List[Dict[str, str]]]:
    """List all available hobby types with descriptions."""
    hobby_descriptions = {
        HobbyType.SKILL_PRACTICE: "Practice and improve existing skills through simulated scenarios",
        HobbyType.KNOWLEDGE_EXPLORATION: "Explore knowledge graph to discover new concepts and connections",
        HobbyType.PATTERN_RECOGNITION: "Analyze patterns in past interactions to improve future performance",
        HobbyType.BENCHMARK_RUNNING: "Run self-evaluation benchmarks to measure and track improvement",
        HobbyType.TOOL_MASTERY: "Practice tool usage and discover effective tool combinations",
        HobbyType.CODE_ANALYSIS: "Analyze codebase structure to identify improvement opportunities (advanced)",
        HobbyType.RESEARCH_INTEGRATION: "Review research papers and integrate new techniques (advanced)",
        HobbyType.CREATIVE_PROBLEM_SOLVING: "Generate and evaluate novel approaches to known problems",
    }
    
    return {
        "hobby_types": [
            {
                "name": hobby.name,
                "description": hobby_descriptions.get(hobby, "No description available"),
            }
            for hobby in HobbyType
        ]
    }


@router.get(
    "/insights",
    summary="Get Recent Insights",
    description="""
    **What's in it for you:** See what your AI has learned recently.
    
    **User Value:**
    - Discover new patterns the AI has identified
    - See which skills have improved
    - Understand performance gains
    - Track knowledge expansion
    
    **Returns:**
    A feed of recent insights gained during hobby activities, showing
    the continuous learning process in action.
    """,
    dependencies=[Depends(rate_limit_dependency)]
)
async def get_recent_insights(count: int = Query(default=50, ge=1, le=500)) -> Dict[str, List[Dict[str, Any]]]:
    """Get recent insights from hobby activities (max 500)."""
    try:
        manager = get_hobby_manager()
        activities = manager.get_recent_activities(min(count, 500))
        
        insights: List[Dict[str, Any]] = []
        for activity in activities:
            # Get insights from the activity dict
            activity_insights = activity.get("insights_gained", [])
            for insight in activity_insights:
                insights.append({
                    "timestamp": activity.get("started_at", ""),
                    "hobby_type": activity.get("hobby_type", ""),
                    "insight": insight,
                })
        
        return {"insights": insights}
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to get insights")
