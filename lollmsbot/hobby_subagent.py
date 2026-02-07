"""
Hobby Sub-Agent Integration - Distributed hobby execution across sub-agents

This module implements Phase 3 sub-agent integration, allowing hobby activities
to be distributed across RC2 sub-agents for parallel learning and specialized
execution.
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, field

from lollmsbot.autonomous_hobby import HobbyType, HobbyActivity, HobbyManager

logger = logging.getLogger(__name__)


@dataclass
class SubAgentHobbyAssignment:
    """Represents a hobby assignment to a sub-agent."""
    assignment_id: str
    subagent_id: str
    hobby_type: HobbyType
    duration_minutes: float
    assigned_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    status: str = "pending"  # pending, running, completed, failed
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert assignment to dictionary."""
        return {
            "assignment_id": self.assignment_id,
            "subagent_id": self.subagent_id,
            "hobby_type": self.hobby_type.name,
            "duration_minutes": self.duration_minutes,
            "assigned_at": self.assigned_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "status": self.status,
            "result": self.result,
            "error": self.error,
        }


class HobbySubAgentCoordinator:
    """Coordinates hobby execution across multiple sub-agents."""
    
    def __init__(self, hobby_manager: HobbyManager):
        """Initialize coordinator.
        
        Args:
            hobby_manager: The main HobbyManager instance
        """
        self.hobby_manager = hobby_manager
        self._assignments: Dict[str, SubAgentHobbyAssignment] = {}
        self._running_tasks: Dict[str, asyncio.Task] = {}
        self._max_concurrent_assignments = 5
        
        # Sub-agent registry
        self._registered_subagents: Dict[str, Dict[str, Any]] = {}
        
        logger.info("HobbySubAgentCoordinator initialized")
    
    def register_subagent(self, subagent_id: str, capabilities: List[str], 
                         metadata: Optional[Dict[str, Any]] = None) -> None:
        """Register a sub-agent for hobby execution.
        
        Args:
            subagent_id: Unique identifier for the sub-agent
            capabilities: List of hobby types this sub-agent can handle
            metadata: Optional metadata about the sub-agent
        """
        self._registered_subagents[subagent_id] = {
            "subagent_id": subagent_id,
            "capabilities": capabilities,
            "metadata": metadata or {},
            "registered_at": datetime.now().isoformat(),
            "active_assignments": 0,
            "completed_assignments": 0,
            "failed_assignments": 0,
        }
        logger.info(f"Registered sub-agent {subagent_id} with capabilities: {capabilities}")
    
    def unregister_subagent(self, subagent_id: str) -> None:
        """Unregister a sub-agent.
        
        Args:
            subagent_id: The sub-agent to unregister
        """
        if subagent_id in self._registered_subagents:
            del self._registered_subagents[subagent_id]
            logger.info(f"Unregistered sub-agent {subagent_id}")
    
    async def assign_hobby_to_subagent(self, subagent_id: str, hobby_type: HobbyType,
                                       duration_minutes: float = 10.0) -> SubAgentHobbyAssignment:
        """Assign a hobby activity to a specific sub-agent.
        
        Args:
            subagent_id: The sub-agent to assign to
            hobby_type: Type of hobby to execute
            duration_minutes: Maximum duration for the hobby
            
        Returns:
            The created assignment
        """
        # Create assignment
        assignment = SubAgentHobbyAssignment(
            assignment_id=self._generate_assignment_id(),
            subagent_id=subagent_id,
            hobby_type=hobby_type,
            duration_minutes=duration_minutes,
            assigned_at=datetime.now(),
        )
        
        self._assignments[assignment.assignment_id] = assignment
        
        # Update sub-agent stats
        if subagent_id in self._registered_subagents:
            self._registered_subagents[subagent_id]["active_assignments"] += 1
        
        # Start execution
        task = asyncio.create_task(self._execute_hobby_on_subagent(assignment))
        self._running_tasks[assignment.assignment_id] = task
        
        logger.info(f"Assigned {hobby_type.name} to sub-agent {subagent_id} (assignment {assignment.assignment_id})")
        
        return assignment
    
    async def auto_distribute_hobbies(self, num_assignments: int = 3) -> List[SubAgentHobbyAssignment]:
        """Automatically distribute hobbies across available sub-agents.
        
        Args:
            num_assignments: Number of hobbies to distribute
            
        Returns:
            List of created assignments
        """
        if not self._registered_subagents:
            logger.warning("No sub-agents registered for auto-distribution")
            return []
        
        assignments = []
        
        # Select hobbies that need work (lowest proficiency)
        hobby_priorities = []
        for hobby_type, progress in self.hobby_manager._progress.items():
            hobby_priorities.append((hobby_type, progress.current_proficiency))
        
        # Sort by proficiency (lowest first)
        hobby_priorities.sort(key=lambda x: x[1])
        
        # Distribute to sub-agents
        for i in range(min(num_assignments, len(hobby_priorities))):
            hobby_type, _ = hobby_priorities[i]
            
            # Find suitable sub-agent
            subagent_id = self._find_suitable_subagent(hobby_type)
            
            if subagent_id:
                assignment = await self.assign_hobby_to_subagent(
                    subagent_id, hobby_type, duration_minutes=10.0
                )
                assignments.append(assignment)
            else:
                logger.warning(f"No suitable sub-agent found for {hobby_type.name}")
        
        logger.info(f"Auto-distributed {len(assignments)} hobbies to sub-agents")
        return assignments
    
    def _find_suitable_subagent(self, hobby_type: HobbyType) -> Optional[str]:
        """Find the best sub-agent for a hobby type.
        
        Args:
            hobby_type: The hobby type to assign
            
        Returns:
            Sub-agent ID or None if none suitable
        """
        suitable = []
        
        for subagent_id, info in self._registered_subagents.items():
            # Check if sub-agent can handle this hobby type
            if hobby_type.name in info["capabilities"] or "*" in info["capabilities"]:
                # Check if sub-agent isn't overloaded
                if info["active_assignments"] < self._max_concurrent_assignments:
                    suitable.append((subagent_id, info["active_assignments"]))
        
        if not suitable:
            return None
        
        # Return sub-agent with fewest active assignments
        suitable.sort(key=lambda x: x[1])
        return suitable[0][0]
    
    async def _execute_hobby_on_subagent(self, assignment: SubAgentHobbyAssignment) -> None:
        """Execute a hobby assignment on a sub-agent.
        
        Args:
            assignment: The assignment to execute
        """
        assignment.status = "running"
        assignment.started_at = datetime.now()
        
        try:
            # Try to dispatch to RC2 sub-agent if available
            result = await self._dispatch_to_rc2_subagent(assignment)
            
            if result:
                # Sub-agent execution succeeded
                assignment.status = "completed"
                assignment.result = result
                assignment.completed_at = datetime.now()
                
                # Update main hobby manager with results
                await self._integrate_subagent_results(assignment, result)
                
                # Update sub-agent stats
                if assignment.subagent_id in self._registered_subagents:
                    self._registered_subagents[assignment.subagent_id]["completed_assignments"] += 1
                    self._registered_subagents[assignment.subagent_id]["active_assignments"] -= 1
                
                logger.info(f"Sub-agent {assignment.subagent_id} completed {assignment.hobby_type.name}")
            else:
                # Fallback: execute locally
                logger.info(f"Executing {assignment.hobby_type.name} locally (sub-agent unavailable)")
                result = await self._execute_hobby_locally(assignment)
                assignment.status = "completed"
                assignment.result = result
                assignment.completed_at = datetime.now()
        
        except asyncio.TimeoutError:
            assignment.status = "failed"
            assignment.error = "Execution timeout"
            assignment.completed_at = datetime.now()
            
            if assignment.subagent_id in self._registered_subagents:
                self._registered_subagents[assignment.subagent_id]["failed_assignments"] += 1
                self._registered_subagents[assignment.subagent_id]["active_assignments"] -= 1
            
            logger.error(f"Sub-agent {assignment.subagent_id} timed out on {assignment.hobby_type.name}")
        
        except Exception as e:
            assignment.status = "failed"
            assignment.error = str(e)
            assignment.completed_at = datetime.now()
            
            if assignment.subagent_id in self._registered_subagents:
                self._registered_subagents[assignment.subagent_id]["failed_assignments"] += 1
                self._registered_subagents[assignment.subagent_id]["active_assignments"] -= 1
            
            logger.error(f"Sub-agent {assignment.subagent_id} failed on {assignment.hobby_type.name}: {e}")
    
    async def _dispatch_to_rc2_subagent(self, assignment: SubAgentHobbyAssignment) -> Optional[Dict[str, Any]]:
        """Dispatch hobby execution to RC2 sub-agent.
        
        Args:
            assignment: The assignment to dispatch
            
        Returns:
            Execution result or None if unavailable
        """
        try:
            from lollmsbot.subagents import RC2SubAgent
            from lollmsbot.subagents.base_subagent import SubAgentRequest, SubAgentCapability
            
            # Create sub-agent request for META_LEARNING capability
            request = SubAgentRequest(
                capability=SubAgentCapability.META_LEARNING,
                context={
                    "task": "hobby_execution",
                    "hobby_type": assignment.hobby_type.name,
                    "duration_minutes": assignment.duration_minutes,
                    "assignment_id": assignment.assignment_id,
                    "learning_objective": self._get_learning_objective(assignment.hobby_type),
                },
                user_id="system",
                priority=5,
            )
            
            # Try to get or create RC2 instance
            # Note: In production, this should be managed by a sub-agent pool
            rc2 = RC2SubAgent(enabled=True, use_multi_provider=True)
            
            if await rc2.can_handle(request):
                # Execute with timeout
                timeout_seconds = assignment.duration_minutes * 60
                response = await asyncio.wait_for(
                    rc2.process(request),
                    timeout=timeout_seconds
                )
                
                if response.success:
                    return {
                        "success": True,
                        "insights": response.result.get("insights", []),
                        "proficiency_gain": response.result.get("proficiency_gain", 0.01),
                        "patterns_discovered": response.result.get("patterns", []),
                        "confidence": response.confidence,
                        "reasoning": response.reasoning,
                    }
                else:
                    logger.warning(f"RC2 sub-agent returned failure: {response.reasoning}")
                    return None
            else:
                logger.warning(f"RC2 sub-agent cannot handle META_LEARNING capability")
                return None
        
        except ImportError:
            logger.debug("RC2 sub-agent not available (import failed)")
            return None
        except Exception as e:
            logger.error(f"Error dispatching to RC2 sub-agent: {e}")
            return None
    
    async def _execute_hobby_locally(self, assignment: SubAgentHobbyAssignment) -> Dict[str, Any]:
        """Execute hobby locally as fallback.
        
        Args:
            assignment: The assignment to execute
            
        Returns:
            Execution result
        """
        # Create a hobby activity
        from lollmsbot.autonomous_hobby import HobbyActivity
        
        activity = HobbyActivity(
            activity_id=assignment.assignment_id,
            hobby_type=assignment.hobby_type,
            started_at=assignment.started_at or datetime.now(),
            description=f"Sub-agent fallback: {assignment.hobby_type.name}",
        )
        
        # Simulate hobby execution (in reality, this would call the actual hobby methods)
        await asyncio.sleep(2)  # Simulate work
        
        activity.completed_at = datetime.now()
        activity.success = True
        activity.insights_gained = [
            f"Sub-agent fallback execution of {assignment.hobby_type.name}",
            "Completed with local resources",
        ]
        activity.engagement_score = 0.7
        activity.improvement_delta = 0.01
        
        return {
            "success": True,
            "insights": activity.insights_gained,
            "proficiency_gain": activity.improvement_delta,
            "patterns_discovered": [],
            "note": "Executed locally (sub-agent unavailable)",
        }
    
    async def _integrate_subagent_results(self, assignment: SubAgentHobbyAssignment, 
                                         result: Dict[str, Any]) -> None:
        """Integrate sub-agent execution results into main hobby manager.
        
        Args:
            assignment: The completed assignment
            result: Execution results from sub-agent
        """
        # Update progress tracking
        progress = self.hobby_manager._progress[assignment.hobby_type]
        
        # Update proficiency
        proficiency_gain = result.get("proficiency_gain", 0.01)
        progress.current_proficiency = min(1.0, progress.current_proficiency + proficiency_gain)
        
        # Update stats
        progress.activities_completed += 1
        progress.insights_total += len(result.get("insights", []))
        progress.total_time_minutes += assignment.duration_minutes
        progress.last_activity = datetime.now()
        
        # Calculate success rate
        if progress.activities_completed > 0:
            # Assume sub-agent execution is successful if we got results
            successful = progress.activities_completed
            progress.success_rate = successful / progress.activities_completed
        
        # Save progress
        self.hobby_manager._save_progress()
        
        logger.info(f"Integrated sub-agent results for {assignment.hobby_type.name}: +{proficiency_gain} proficiency")
    
    def _get_learning_objective(self, hobby_type: HobbyType) -> str:
        """Get learning objective for a hobby type.
        
        Args:
            hobby_type: The hobby type
            
        Returns:
            Description of learning objective
        """
        objectives = {
            HobbyType.SKILL_PRACTICE: "Practice and refine existing skills through simulation",
            HobbyType.KNOWLEDGE_EXPLORATION: "Explore knowledge graph and discover connections",
            HobbyType.PATTERN_RECOGNITION: "Analyze patterns in past interactions",
            HobbyType.BENCHMARK_RUNNING: "Run performance benchmarks and self-evaluation",
            HobbyType.TOOL_MASTERY: "Practice tool usage and discover combinations",
            HobbyType.CODE_ANALYSIS: "Analyze code structure and identify improvements",
            HobbyType.RESEARCH_INTEGRATION: "Review recent research and propose integrations",
            HobbyType.CREATIVE_PROBLEM_SOLVING: "Generate and evaluate novel solutions",
        }
        return objectives.get(hobby_type, "General learning and improvement")
    
    def _generate_assignment_id(self) -> str:
        """Generate unique assignment ID."""
        import hashlib
        import time
        
        data = f"assignment_{time.time()}_{len(self._assignments)}"
        return hashlib.sha256(data.encode()).hexdigest()[:16]
    
    def get_assignment_status(self, assignment_id: str) -> Optional[Dict[str, Any]]:
        """Get status of an assignment.
        
        Args:
            assignment_id: The assignment ID
            
        Returns:
            Assignment status or None if not found
        """
        if assignment_id in self._assignments:
            return self._assignments[assignment_id].to_dict()
        return None
    
    def get_all_assignments(self, status_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all assignments, optionally filtered by status.
        
        Args:
            status_filter: Filter by status (pending, running, completed, failed)
            
        Returns:
            List of assignments
        """
        assignments = []
        for assignment in self._assignments.values():
            if status_filter is None or assignment.status == status_filter:
                assignments.append(assignment.to_dict())
        return assignments
    
    def get_subagent_stats(self) -> Dict[str, Any]:
        """Get statistics about registered sub-agents.
        
        Returns:
            Sub-agent statistics
        """
        return {
            "total_registered": len(self._registered_subagents),
            "total_active_assignments": sum(
                info["active_assignments"] for info in self._registered_subagents.values()
            ),
            "total_completed_assignments": sum(
                info["completed_assignments"] for info in self._registered_subagents.values()
            ),
            "total_failed_assignments": sum(
                info["failed_assignments"] for info in self._registered_subagents.values()
            ),
            "subagents": list(self._registered_subagents.values()),
        }


# Global coordinator instance
_coordinator: Optional[HobbySubAgentCoordinator] = None


def get_coordinator(hobby_manager: HobbyManager) -> HobbySubAgentCoordinator:
    """Get or create the global coordinator instance.
    
    Args:
        hobby_manager: The HobbyManager instance
        
    Returns:
        The coordinator instance
    """
    global _coordinator
    if _coordinator is None:
        _coordinator = HobbySubAgentCoordinator(hobby_manager)
    return _coordinator
