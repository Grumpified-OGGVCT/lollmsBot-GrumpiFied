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
    summary="Assign Hobby to Sub-Agent (Phase 3 - ACTIVE)",
    description="""
    **Phase 3 Feature: Sub-Agent Integration** ✅ NOW ACTIVE
    
    Assigns a hobby activity to a specific sub-agent for distributed execution.
    The sub-agent will execute the hobby independently using its specialized
    capabilities, then report results back for integration.
    
    **How It Works:**
    1. Assignment created and queued
    2. Dispatched to RC2 sub-agent with META_LEARNING capability
    3. Sub-agent executes hobby with specified duration
    4. Results integrated into main proficiency tracking
    5. Progress automatically saved
    
    **Benefits:**
    - Parallel learning across multiple agents
    - Specialized execution for different hobby types
    - Faster overall improvement
    - Distributed workload
    
    **Sub-Agent Requirements:**
    - Must support META_LEARNING capability (RC2 does)
    - Registered with coordinator (auto-registration available)
    - Has capacity for additional work
    """,
    dependencies=[Depends(rate_limit_dependency)]
)
async def assign_hobby_to_subagent(assignment: HobbyAssignment) -> Dict[str, Any]:
    """Assign a hobby activity to a sub-agent (Phase 3 - FULLY FUNCTIONAL)."""
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
        
        # Get coordinator
        from lollmsbot.hobby_subagent import get_coordinator
        
        manager = get_hobby_manager()
        coordinator = get_coordinator(manager)
        
        # Assign to sub-agent
        assignment_obj = await coordinator.assign_hobby_to_subagent(
            subagent_id=assignment.subagent_id,
            hobby_type=hobby_enum,
            duration_minutes=assignment.duration_minutes,
        )
        
        return {
            "status": "assigned",
            "assignment": assignment_obj.to_dict(),
            "message": "Hobby assigned to sub-agent. Execution started.",
            "phase": "Phase 3 - Sub-Agent Integration Active",
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


@router.get(
    "/metrics/prometheus",
    summary="Prometheus Metrics Export",
    description="""
    **Phase 3A Feature: Metrics Dashboard**
    
    Exports hobby system metrics in Prometheus text format for monitoring
    and alerting. Use this endpoint as a scrape target in your Prometheus
    configuration.
    
    **Metrics Included:**
    - System status (enabled, running, idle)
    - Per-hobby proficiency levels
    - Time invested per hobby type
    - Success rates and insights gained
    - Current activity information
    
    **Integration:**
    Add to prometheus.yml:
    ```yaml
    scrape_configs:
      - job_name: 'lollmsbot-hobbies'
        static_configs:
          - targets: ['localhost:8800']
        metrics_path: '/hobby/metrics/prometheus'
    ```
    """,
    dependencies=[Depends(rate_limit_dependency)]
)
async def get_prometheus_metrics() -> str:
    """Export metrics in Prometheus format."""
    try:
        from lollmsbot.hobby_metrics import create_metrics_collector
        
        manager = get_hobby_manager()
        collector = create_metrics_collector(manager)
        return collector.get_prometheus_metrics()
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to generate metrics")


@router.get(
    "/metrics/summary",
    summary="Metrics Summary (JSON)",
    description="""
    **Phase 3A Feature: Metrics Dashboard**
    
    Returns comprehensive metrics in JSON format, optimized for
    visualization dashboards and monitoring tools.
    
    **Includes:**
    - Real-time system status
    - Progress summary by hobby type
    - Activity timeline (hourly/daily)
    - Proficiency trends
    - Dashboard-ready chart data
    
    **Use Cases:**
    - Custom dashboards
    - Mobile apps
    - Real-time monitoring
    - Performance analysis
    """,
    dependencies=[Depends(rate_limit_dependency)]
)
async def get_metrics_summary() -> Dict[str, Any]:
    """Get comprehensive metrics summary."""
    try:
        from lollmsbot.hobby_metrics import create_metrics_collector
        
        manager = get_hobby_manager()
        collector = create_metrics_collector(manager)
        return collector.get_metrics_summary()
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to get metrics summary")


@router.get(
    "/dashboard",
    summary="Dashboard Visualization Data",
    description="""
    **Phase 3A Feature: Metrics Dashboard**
    
    Returns data pre-formatted for common visualization charts:
    - Radar chart (proficiency by hobby type)
    - Bar chart (time invested)
    - Line chart (activity timeline)
    - Pie chart (activities by type)
    - Current statistics
    
    **Perfect for:**
    - Web dashboards (Chart.js, D3.js, Recharts)
    - Mobile visualizations
    - Quick overview displays
    - Executive summaries
    """,
    dependencies=[Depends(rate_limit_dependency)]
)
async def get_dashboard_data() -> Dict[str, Any]:
    """Get dashboard-ready visualization data."""
    try:
        from lollmsbot.hobby_metrics import create_metrics_collector
        
        manager = get_hobby_manager()
        collector = create_metrics_collector(manager)
        return collector.get_dashboard_data()
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to get dashboard data")


@router.post(
    "/subagents/register",
    summary="Register Sub-Agent for Hobby Execution",
    description="""
    **Phase 3 Feature: Sub-Agent Registration**
    
    Register a sub-agent to participate in distributed hobby execution.
    Sub-agents can be specialized for specific hobby types or support all types.
    
    **Parameters:**
    - subagent_id: Unique identifier
    - capabilities: List of hobby types (or ["*"] for all)
    - metadata: Optional info (version, specialization, etc.)
    
    **Example:**
    ```json
    {
      "subagent_id": "rc2-instance-1",
      "capabilities": ["SKILL_PRACTICE", "KNOWLEDGE_EXPLORATION"],
      "metadata": {"version": "1.0", "specialization": "coding"}
    }
    ```
    """,
    dependencies=[Depends(rate_limit_dependency)]
)
async def register_subagent(
    subagent_id: str,
    capabilities: List[str],
    metadata: Dict[str, Any] = {}
) -> Dict[str, str]:
    """Register a sub-agent for hobby execution."""
    try:
        from lollmsbot.hobby_subagent import get_coordinator
        
        manager = get_hobby_manager()
        coordinator = get_coordinator(manager)
        
        coordinator.register_subagent(subagent_id, capabilities, metadata)
        
        return {
            "status": "registered",
            "subagent_id": subagent_id,
            "message": f"Sub-agent registered with {len(capabilities)} capabilities",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to register sub-agent")


@router.delete(
    "/subagents/{subagent_id}",
    summary="Unregister Sub-Agent",
    description="""
    **Phase 3 Feature: Sub-Agent Management**
    
    Unregister a sub-agent from hobby execution pool.
    Active assignments will complete, but no new work will be assigned.
    """,
    dependencies=[Depends(rate_limit_dependency)]
)
async def unregister_subagent(subagent_id: str) -> Dict[str, str]:
    """Unregister a sub-agent."""
    try:
        from lollmsbot.hobby_subagent import get_coordinator
        
        manager = get_hobby_manager()
        coordinator = get_coordinator(manager)
        
        coordinator.unregister_subagent(subagent_id)
        
        return {
            "status": "unregistered",
            "subagent_id": subagent_id,
            "message": "Sub-agent unregistered successfully",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to unregister sub-agent")


@router.get(
    "/subagents/stats",
    summary="Get Sub-Agent Statistics",
    description="""
    **Phase 3 Feature: Sub-Agent Monitoring**
    
    Get comprehensive statistics about all registered sub-agents:
    - Total registered sub-agents
    - Active/completed/failed assignments
    - Per-agent performance metrics
    - Capability distribution
    """,
    dependencies=[Depends(rate_limit_dependency)]
)
async def get_subagent_stats() -> Dict[str, Any]:
    """Get sub-agent statistics."""
    try:
        from lollmsbot.hobby_subagent import get_coordinator
        
        manager = get_hobby_manager()
        coordinator = get_coordinator(manager)
        
        return coordinator.get_subagent_stats()
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to get sub-agent stats")


@router.get(
    "/assignments/{assignment_id}",
    summary="Get Assignment Status",
    description="""
    **Phase 3 Feature: Assignment Tracking**
    
    Get detailed status of a specific hobby assignment including:
    - Current status (pending, running, completed, failed)
    - Execution timeline
    - Results and insights gained
    - Error information if failed
    """,
    dependencies=[Depends(rate_limit_dependency)]
)
async def get_assignment_status(assignment_id: str) -> Dict[str, Any]:
    """Get status of a specific assignment."""
    try:
        from lollmsbot.hobby_subagent import get_coordinator
        
        manager = get_hobby_manager()
        coordinator = get_coordinator(manager)
        
        status = coordinator.get_assignment_status(assignment_id)
        
        if status is None:
            raise HTTPException(status_code=404, detail="Assignment not found")
        
        return status
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to get assignment status")


@router.get(
    "/assignments",
    summary="List All Assignments",
    description="""
    **Phase 3 Feature: Assignment Management**
    
    List all hobby assignments, optionally filtered by status.
    
    **Query Parameters:**
    - status: Filter by status (pending, running, completed, failed)
    
    **Use Cases:**
    - Monitor active assignments
    - Review completed work
    - Debug failures
    - Track distribution efficiency
    """,
    dependencies=[Depends(rate_limit_dependency)]
)
async def list_assignments(status: Optional[str] = Query(None)) -> Dict[str, List[Dict[str, Any]]]:
    """List all assignments with optional status filter."""
    try:
        from lollmsbot.hobby_subagent import get_coordinator
        
        manager = get_hobby_manager()
        coordinator = get_coordinator(manager)
        
        assignments = coordinator.get_all_assignments(status_filter=status)
        
        return {
            "assignments": assignments,
            "count": len(assignments),
            "filter": status or "all",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to list assignments")


@router.post(
    "/distribute",
    summary="Auto-Distribute Hobbies to Sub-Agents",
    description="""
    **Phase 3 Feature: Intelligent Distribution**
    
    Automatically distribute hobby activities to available sub-agents based on:
    - Current proficiency levels (prioritize weak areas)
    - Sub-agent capabilities and availability
    - Load balancing across agents
    
    **Parameters:**
    - num_assignments: Number of hobbies to distribute (default: 3)
    
    **Returns:**
    List of created assignments with their status.
    
    **Example Use Case:**
    Run this periodically to keep sub-agents busy with improvement work.
    """,
    dependencies=[Depends(rate_limit_dependency)]
)
async def auto_distribute_hobbies(num_assignments: int = Query(default=3, ge=1, le=10)) -> Dict[str, Any]:
    """Automatically distribute hobbies to sub-agents."""
    try:
        from lollmsbot.hobby_subagent import get_coordinator
        
        manager = get_hobby_manager()
        coordinator = get_coordinator(manager)
        
        assignments = await coordinator.auto_distribute_hobbies(num_assignments=num_assignments)
        
        return {
            "status": "distributed",
            "assignments": [a.to_dict() for a in assignments],
            "count": len(assignments),
            "message": f"Distributed {len(assignments)} hobbies to sub-agents",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to distribute hobbies")


# ========================================================================
# Phase 3B: LoRA Training Pipeline Endpoints
# ========================================================================

class TrainingJobRequest(BaseModel):
    """Request to create a training job"""
    days_back: int = Field(default=30, ge=1, le=365, description="Days of activity history to use")
    min_quality: float = Field(default=0.6, ge=0.0, le=1.0, description="Minimum quality score")
    model_name: str = Field(default="base_model", description="Base model name")
    num_epochs: int = Field(default=3, ge=1, le=10, description="Number of training epochs")
    learning_rate: float = Field(default=3e-4, ge=1e-6, le=1e-2, description="Learning rate")


@router.post(
    "/lora/train",
    summary="Start LoRA Training",
    description="""
    Create and start a LoRA training job using insights from hobby activities.
    
    This extracts training data from recent hobby activities and fine-tunes
    a LoRA adapter to improve the model's performance on learned patterns.
    """,
    dependencies=[Depends(rate_limit_dependency)]
)
async def start_lora_training(request: TrainingJobRequest) -> Dict[str, Any]:
    """Start a new LoRA training job."""
    try:
        from lollmsbot.hobby_training_data import extract_training_data_from_manager
        from lollmsbot.hobby_lora import get_lora_manager, TrainingConfig
        from pathlib import Path
        
        manager = get_hobby_manager()
        lora_manager = get_lora_manager()
        
        # Extract training data
        examples, stats = extract_training_data_from_manager(
            manager,
            days_back=request.days_back,
            min_quality=request.min_quality
        )
        
        if len(examples) < 10:
            raise HTTPException(
                status_code=400,
                detail=f"Insufficient training data: only {len(examples)} examples found (minimum 10 required)"
            )
        
        # Export to JSON
        data_path = lora_manager.storage_path / "training_data" / f"data_{int(time.time())}.json"
        data_path.parent.mkdir(parents=True, exist_ok=True)
        
        from lollmsbot.hobby_training_data import TrainingDataExtractor
        extractor = TrainingDataExtractor()
        extractor.export_to_json(examples, data_path, format_type="alpaca")
        
        # Create training config
        config = TrainingConfig(
            model_name=request.model_name,
            num_epochs=request.num_epochs,
            learning_rate=request.learning_rate
        )
        
        # Create training job
        job = lora_manager.create_training_job(
            data_path=data_path,
            num_examples=len(examples),
            config=config,
            metadata={
                "days_back": request.days_back,
                "min_quality": request.min_quality,
                "data_stats": stats
            }
        )
        
        # Start training asynchronously
        import asyncio
        asyncio.create_task(lora_manager.start_training(job.job_id))
        
        return {
            "status": "started",
            "job": job.to_dict(),
            "data_stats": stats,
            "message": f"Started training job {job.job_id} with {len(examples)} examples"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to start training")


@router.get(
    "/lora/jobs/{job_id}",
    summary="Get Training Job Status",
    description="Get detailed status and metrics for a training job.",
    dependencies=[Depends(rate_limit_dependency)]
)
async def get_training_job_status(job_id: str) -> Dict[str, Any]:
    """Get training job status."""
    try:
        from lollmsbot.hobby_lora import get_lora_manager
        
        lora_manager = get_lora_manager()
        job = lora_manager.get_training_job(job_id)
        
        if not job:
            raise HTTPException(status_code=404, detail=f"Training job {job_id} not found")
        
        return job.to_dict()
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to get training job")


@router.get(
    "/lora/jobs",
    summary="List Training Jobs",
    description="List all training jobs with optional status filter.",
    dependencies=[Depends(rate_limit_dependency)]
)
async def list_training_jobs(
    status: str = Query(default=None, description="Filter by status"),
    limit: int = Query(default=50, ge=1, le=100)
) -> Dict[str, Any]:
    """List training jobs."""
    try:
        from lollmsbot.hobby_lora import get_lora_manager, TrainingStatus
        
        lora_manager = get_lora_manager()
        
        filter_status = None
        if status:
            try:
                filter_status = TrainingStatus(status)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid status: {status}")
        
        jobs = lora_manager.list_training_jobs(status=filter_status, limit=limit)
        
        return {
            "jobs": [job.to_dict() for job in jobs],
            "count": len(jobs)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to list training jobs")


@router.get(
    "/lora/adapters",
    summary="List LoRA Adapters",
    description="List all trained LoRA adapters with optional status filter.",
    dependencies=[Depends(rate_limit_dependency)]
)
async def list_lora_adapters(
    status: str = Query(default=None, description="Filter by status"),
    limit: int = Query(default=50, ge=1, le=100)
) -> Dict[str, Any]:
    """List LoRA adapters."""
    try:
        from lollmsbot.hobby_lora import get_lora_manager, AdapterStatus
        
        lora_manager = get_lora_manager()
        
        filter_status = None
        if status:
            try:
                filter_status = AdapterStatus(status)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid status: {status}")
        
        adapters = lora_manager.list_adapters(status=filter_status, limit=limit)
        
        return {
            "adapters": [adapter.to_dict() for adapter in adapters],
            "count": len(adapters),
            "active_adapter_id": lora_manager.active_adapter_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to list adapters")


@router.post(
    "/lora/adapters/{adapter_id}/activate",
    summary="Activate LoRA Adapter",
    description="Set a LoRA adapter as the active adapter for inference.",
    dependencies=[Depends(rate_limit_dependency)]
)
async def activate_lora_adapter(adapter_id: str) -> Dict[str, Any]:
    """Activate a LoRA adapter."""
    try:
        from lollmsbot.hobby_lora import get_lora_manager
        
        lora_manager = get_lora_manager()
        lora_manager.set_active_adapter(adapter_id)
        
        return {
            "status": "activated",
            "adapter_id": adapter_id,
            "message": f"Activated adapter {adapter_id}"
        }
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to activate adapter")


@router.post(
    "/lora/adapters/{adapter_id}/archive",
    summary="Archive LoRA Adapter",
    description="Archive a LoRA adapter (removes it from active use).",
    dependencies=[Depends(rate_limit_dependency)]
)
async def archive_lora_adapter(adapter_id: str) -> Dict[str, Any]:
    """Archive a LoRA adapter."""
    try:
        from lollmsbot.hobby_lora import get_lora_manager
        
        lora_manager = get_lora_manager()
        lora_manager.archive_adapter(adapter_id)
        
        return {
            "status": "archived",
            "adapter_id": adapter_id,
            "message": f"Archived adapter {adapter_id}"
        }
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to archive adapter")


@router.get(
    "/lora/compare",
    summary="Compare LoRA Adapters",
    description="""
    Compare two LoRA adapters for A/B testing.
    
    Returns metrics comparison and recommendation on which adapter to use.
    """,
    dependencies=[Depends(rate_limit_dependency)]
)
async def compare_lora_adapters(
    adapter1: str = Query(..., description="First adapter ID"),
    adapter2: str = Query(..., description="Second adapter ID")
) -> Dict[str, Any]:
    """Compare two LoRA adapters."""
    try:
        from lollmsbot.hobby_lora import get_lora_manager
        
        lora_manager = get_lora_manager()
        comparison = lora_manager.compare_adapters(adapter1, adapter2)
        
        return comparison
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to compare adapters")


@router.get(
    "/lora/stats",
    summary="Get LoRA Training Statistics",
    description="Get overall statistics for LoRA training system.",
    dependencies=[Depends(rate_limit_dependency)]
)
async def get_lora_stats() -> Dict[str, Any]:
    """Get LoRA training statistics."""
    try:
        from lollmsbot.hobby_lora import get_lora_manager
        
        lora_manager = get_lora_manager()
        stats = lora_manager.get_statistics()
        
        return stats
        
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to get LoRA statistics")


# ========================================================================
# Phase 3C: Knowledge Graph Integration Endpoints
# ========================================================================

class BuildGraphRequest(BaseModel):
    """Request to build knowledge graph from activities"""
    days_back: int = Field(default=30, ge=1, le=365, description="Days of activity history")


@router.post(
    "/graph/build",
    summary="Build Knowledge Graph",
    description="""
    Build or update the knowledge graph from hobby activity insights.
    
    Extracts concepts, insights, patterns, and skills from activities
    and creates nodes and relationships in the knowledge graph.
    """,
    dependencies=[Depends(rate_limit_dependency)]
)
async def build_knowledge_graph(request: BuildGraphRequest) -> Dict[str, Any]:
    """Build knowledge graph from activities."""
    try:
        from lollmsbot.hobby_knowledge_graph import get_knowledge_graph, build_graph_from_activities
        from datetime import timedelta
        
        manager = get_hobby_manager()
        graph = get_knowledge_graph()
        
        # Get recent activities
        activities = manager.get_recent_activities(count=1000)
        
        # Filter by date
        cutoff_date = datetime.now() - timedelta(days=request.days_back)
        recent_activities = [
            act for act in activities
            if datetime.fromisoformat(act.get("started_at", "2000-01-01")) > cutoff_date
        ]
        
        # Build graph
        stats = build_graph_from_activities(graph, recent_activities)
        
        return {
            "status": "success",
            "stats": stats,
            "graph_stats": graph.get_statistics(),
            "message": f"Built graph from {len(recent_activities)} activities"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to build knowledge graph")


@router.get(
    "/graph/stats",
    summary="Get Knowledge Graph Statistics",
    description="Get overall statistics about the knowledge graph.",
    dependencies=[Depends(rate_limit_dependency)]
)
async def get_graph_stats() -> Dict[str, Any]:
    """Get knowledge graph statistics."""
    try:
        from lollmsbot.hobby_knowledge_graph import get_knowledge_graph
        
        graph = get_knowledge_graph()
        stats = graph.get_statistics()
        
        return stats
        
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to get graph statistics")


@router.get(
    "/graph/nodes/{node_id}",
    summary="Get Knowledge Node",
    description="Get a specific node from the knowledge graph.",
    dependencies=[Depends(rate_limit_dependency)]
)
async def get_knowledge_node(node_id: str) -> Dict[str, Any]:
    """Get knowledge node by ID."""
    try:
        from lollmsbot.hobby_knowledge_graph import get_knowledge_graph
        
        graph = get_knowledge_graph()
        node = graph.get_node(node_id)
        
        if not node:
            raise HTTPException(status_code=404, detail=f"Node {node_id} not found")
        
        # Get neighbors
        neighbors = graph.get_neighbors(node_id)
        
        return {
            "node": node.to_dict(),
            "neighbors": [
                {
                    "node": n.to_dict(),
                    "edge": e.to_dict()
                }
                for n, e in neighbors
            ]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to get knowledge node")


@router.get(
    "/graph/search",
    summary="Search Knowledge Graph",
    description="Search for nodes in the knowledge graph by query string.",
    dependencies=[Depends(rate_limit_dependency)]
)
async def search_knowledge_graph(
    query: str = Query(..., description="Search query"),
    node_type: str = Query(default=None, description="Filter by node type"),
    limit: int = Query(default=50, ge=1, le=100)
) -> Dict[str, Any]:
    """Search knowledge graph."""
    try:
        from lollmsbot.hobby_knowledge_graph import get_knowledge_graph, NodeType
        
        graph = get_knowledge_graph()
        
        filter_type = None
        if node_type:
            try:
                filter_type = NodeType(node_type)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid node type: {node_type}")
        
        nodes = graph.search_nodes(query, node_type=filter_type, limit=limit)
        
        return {
            "nodes": [node.to_dict() for node in nodes],
            "count": len(nodes)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to search knowledge graph")


@router.get(
    "/graph/path",
    summary="Find Path Between Concepts",
    description="""
    Find the shortest path between two concepts in the knowledge graph.
    
    This reveals how different learnings and insights are connected.
    """,
    dependencies=[Depends(rate_limit_dependency)]
)
async def find_knowledge_path(
    start_id: str = Query(..., description="Start node ID"),
    end_id: str = Query(..., description="End node ID"),
    max_depth: int = Query(default=5, ge=1, le=10)
) -> Dict[str, Any]:
    """Find path between two nodes."""
    try:
        from lollmsbot.hobby_knowledge_graph import get_knowledge_graph
        
        graph = get_knowledge_graph()
        path = graph.find_path(start_id, end_id, max_depth=max_depth)
        
        if not path:
            return {
                "found": False,
                "message": f"No path found between {start_id} and {end_id} within depth {max_depth}"
            }
        
        # Get node details for path
        path_nodes = []
        for node_id in path:
            node = graph.get_node(node_id)
            if node:
                path_nodes.append(node.to_dict())
        
        return {
            "found": True,
            "path": path,
            "path_nodes": path_nodes,
            "length": len(path) - 1
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to find path")


@router.get(
    "/graph/subgraph/{node_id}",
    summary="Get Subgraph",
    description="""
    Get a subgraph centered on a specific node.
    
    Returns all nodes and edges within the specified depth.
    """,
    dependencies=[Depends(rate_limit_dependency)]
)
async def get_subgraph(
    node_id: str,
    depth: int = Query(default=2, ge=1, le=5)
) -> Dict[str, Any]:
    """Get subgraph around a node."""
    try:
        from lollmsbot.hobby_knowledge_graph import get_knowledge_graph
        
        graph = get_knowledge_graph()
        
        if node_id not in graph.nodes:
            raise HTTPException(status_code=404, detail=f"Node {node_id} not found")
        
        subgraph = graph.get_subgraph(node_id, depth=depth)
        
        return {
            "center_node_id": node_id,
            "depth": depth,
            "subgraph": subgraph,
            "node_count": len(subgraph["nodes"]),
            "edge_count": len(subgraph["edges"])
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to get subgraph")
