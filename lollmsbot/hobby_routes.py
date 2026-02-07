"""
Autonomous Hobby API Routes - FastAPI endpoints for hobby system monitoring and control
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any, List, Optional
from datetime import datetime

from lollmsbot.autonomous_hobby import (
    get_hobby_manager,
    HobbyType,
    HobbyConfig,
    start_autonomous_learning,
    stop_autonomous_learning,
)

router = APIRouter(prefix="/hobby", tags=["Autonomous Learning"])


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
        raise HTTPException(status_code=500, detail=f"Failed to get hobby status: {str(e)}")


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
)
async def get_learning_progress() -> Dict[str, Any]:
    """Get detailed learning progress across all hobby types."""
    try:
        manager = get_hobby_manager()
        return manager.get_progress_summary()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get progress: {str(e)}")


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
)
async def get_recent_activities(count: int = 20) -> List[Dict[str, Any]]:
    """Get recent hobby activities."""
    try:
        manager = get_hobby_manager()
        return manager.get_recent_activities(count)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get activities: {str(e)}")


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
)
async def start_hobby_system() -> Dict[str, str]:
    """Start the autonomous hobby system."""
    try:
        manager = await start_autonomous_learning()
        return {
            "status": "started",
            "message": "Autonomous learning system activated",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start hobby system: {str(e)}")


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
        raise HTTPException(status_code=500, detail=f"Failed to stop hobby system: {str(e)}")


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
        raise HTTPException(status_code=500, detail=f"Failed to get config: {str(e)}")


@router.post(
    "/assign-to-subagent",
    summary="Assign Hobby to Sub-Agent",
    description="""
    **What's in it for you:** Distributed learning across multiple agents.
    
    **User Value:**
    - Parallel learning activities
    - Faster overall improvement
    - Specialized sub-agents for different areas
    
    **How It Works:**
    Assign a specific hobby (skill practice, knowledge exploration, etc.)
    to a sub-agent for a specified duration. The sub-agent will pursue
    that hobby independently and report back results.
    
    **This enables the vision:**
    "Hobbies can also be assigned to sub-agents" - allowing truly
    distributed continuous learning.
    """,
)
async def assign_hobby_to_subagent(
    subagent_id: str,
    hobby_type: str,
    duration_minutes: float = 5.0,
) -> Dict[str, Any]:
    """Assign a hobby activity to a sub-agent."""
    try:
        # Parse hobby type
        try:
            hobby_enum = HobbyType[hobby_type.upper()]
        except KeyError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid hobby type: {hobby_type}. "
                       f"Valid types: {[h.name for h in HobbyType]}",
            )
        
        manager = get_hobby_manager()
        assignment = manager.assign_hobby_to_subagent(
            subagent_id=subagent_id,
            hobby_type=hobby_enum,
            duration_minutes=duration_minutes,
        )
        
        return {
            "status": "assigned",
            "assignment": assignment,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to assign hobby: {str(e)}",
        )


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
)
async def get_recent_insights(count: int = 50) -> Dict[str, List[str]]:
    """Get recent insights from hobby activities."""
    try:
        manager = get_hobby_manager()
        activities = manager.get_recent_activities(count)
        
        insights = []
        for activity in activities:
            for insight in activity.get("insights_gained", []):
                insights.append({
                    "timestamp": activity.get("started_at", ""),
                    "hobby_type": activity.get("hobby_type", ""),
                    "insight": insight,
                })
        
        return {"insights": insights}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get insights: {str(e)}")
