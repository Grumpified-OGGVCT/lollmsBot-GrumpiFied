"""
Lane Queue - Serial-by-Default Concurrency Control

The Lane Queue implements OpenClaw's priority-based execution model to prevent
race conditions and database locks. Tasks are organized into lanes with strict
priority ordering:

- Lane 0 (High Priority): User Interaction (Discord/Telegram/WebUI)
  When this lane is active, all other lanes pause.
  
- Lane 1 (Background): Heartbeat tasks (Memory pruning, summary generation)
  These must be interruptible by Lane 0.
  
- Lane 2 (System): Tool execution (File I/O, Shell)
  Lowest priority, yields to both Lane 0 and Lane 1.

Key Design Principles:
1. Serial-by-Default: Within a lane, tasks execute sequentially
2. Priority Preemption: Higher priority lanes pause lower priority lanes
3. Atomic Completion: Tasks cannot be interrupted mid-execution (but can be paused)
4. No Deadlocks: No circular dependencies between lanes
"""

from __future__ import annotations

import asyncio
import logging
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import IntEnum
from typing import Any, Callable, Coroutine, Dict, List, Optional, Set

logger = logging.getLogger("lollmsbot.core.lane_queue")


class LanePriority(IntEnum):
    """Priority levels for task lanes (lower number = higher priority)."""
    USER_INTERACTION = 0  # Highest priority - user messages, commands
    BACKGROUND = 1        # Background tasks - heartbeat, memory maintenance
    SYSTEM = 2            # System tasks - tool execution, file I/O


@dataclass
class LaneTask:
    """A task to be executed in a specific lane.
    
    Attributes:
        task_id: Unique identifier for this task
        lane: Priority lane for execution
        coro: Async coroutine to execute
        name: Human-readable task name for debugging
        created_at: When the task was created
        started_at: When execution started
        completed_at: When execution completed
        cancelled: Whether this task was cancelled
        result: Result from the coroutine (if completed successfully)
        error: Exception if the task failed
    """
    task_id: str
    lane: LanePriority
    coro: Coroutine[Any, Any, Any]
    name: str
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    cancelled: bool = False
    result: Any = None
    error: Optional[Exception] = None
    
    def __post_init__(self):
        """Generate task_id if not provided."""
        if not self.task_id:
            self.task_id = str(uuid.uuid4())


class Lane:
    """A single execution lane with its own queue and state.
    
    Each lane maintains a queue of tasks and tracks whether it's currently
    executing. Lanes can be paused by higher-priority lanes.
    """
    
    def __init__(self, priority: LanePriority):
        """Initialize a lane with the given priority.
        
        Args:
            priority: The priority level for this lane
        """
        self.priority = priority
        self.queue: asyncio.Queue[LaneTask] = asyncio.Queue()
        self.current_task: Optional[LaneTask] = None
        self.is_executing = False
        self.is_paused = False
        self.tasks_completed = 0
        self.tasks_failed = 0
        self.tasks_cancelled = 0
        
    def __repr__(self) -> str:
        return (
            f"Lane(priority={self.priority.name}, "
            f"queued={self.queue.qsize()}, "
            f"executing={self.is_executing}, "
            f"paused={self.is_paused})"
        )


class LaneQueue:
    """Serial-by-Default Lane Queue for controlled concurrency.
    
    This implements the OpenClaw pattern where tasks are organized into
    priority lanes, with higher-priority lanes able to pause lower-priority
    lanes to prevent race conditions and resource conflicts.
    
    Usage:
        queue = LaneQueue()
        await queue.start()
        
        # Submit a user interaction task (highest priority)
        task_id = await queue.submit(
            user_interaction_coroutine(),
            lane=LanePriority.USER_INTERACTION,
            name="process_user_message"
        )
        
        # Submit a background task (can be paused by user interactions)
        await queue.submit(
            heartbeat_task(),
            lane=LanePriority.BACKGROUND,
            name="memory_compression"
        )
        
        await queue.stop()
    """
    
    def __init__(self):
        """Initialize the Lane Queue with all lanes."""
        self.lanes: Dict[LanePriority, Lane] = {
            priority: Lane(priority) for priority in LanePriority
        }
        self._executor_tasks: Dict[LanePriority, asyncio.Task] = {}
        self._stop_event = asyncio.Event()
        self._started = False
        self._lock = asyncio.Lock()
        
        # Statistics
        self.total_tasks_submitted = 0
        self.total_tasks_completed = 0
        self.total_tasks_failed = 0
        
    async def start(self) -> None:
        """Start the lane queue executors.
        
        This spawns an async task for each lane that processes tasks
        from that lane's queue.
        """
        if self._started:
            logger.warning("LaneQueue already started")
            return
            
        logger.info("Starting LaneQueue with %d lanes", len(self.lanes))
        self._started = True
        self._stop_event.clear()
        
        # Start an executor task for each lane
        for priority, lane in self.lanes.items():
            task = asyncio.create_task(
                self._lane_executor(priority),
                name=f"lane_executor_{priority.name}"
            )
            self._executor_tasks[priority] = task
            
        logger.info("LaneQueue started successfully")
        
    async def stop(self, timeout: float = 10.0) -> None:
        """Stop the lane queue and wait for tasks to complete.
        
        Args:
            timeout: How long to wait for tasks to complete before cancelling
        """
        if not self._started:
            return
            
        logger.info("Stopping LaneQueue...")
        self._stop_event.set()
        
        # Wait for executor tasks to finish with timeout
        if self._executor_tasks:
            try:
                await asyncio.wait_for(
                    asyncio.gather(*self._executor_tasks.values(), return_exceptions=True),
                    timeout=timeout
                )
            except asyncio.TimeoutError:
                logger.warning("LaneQueue stop timeout, cancelling tasks")
                for task in self._executor_tasks.values():
                    if not task.done():
                        task.cancel()
                        
        self._started = False
        logger.info("LaneQueue stopped")
        
    async def submit(
        self,
        coro: Coroutine[Any, Any, Any],
        lane: LanePriority = LanePriority.SYSTEM,
        name: str = "unnamed_task"
    ) -> str:
        """Submit a task to be executed in the specified lane.
        
        Args:
            coro: Async coroutine to execute
            lane: Priority lane for this task
            name: Human-readable name for debugging
            
        Returns:
            task_id: Unique identifier for tracking this task
        """
        if not self._started:
            raise RuntimeError("LaneQueue not started. Call start() first.")
            
        task = LaneTask(
            task_id=str(uuid.uuid4()),
            lane=lane,
            coro=coro,
            name=name
        )
        
        await self.lanes[lane].queue.put(task)
        self.total_tasks_submitted += 1
        
        logger.debug(
            "Task submitted: %s (lane=%s, queue_size=%d)",
            task.name,
            lane.name,
            self.lanes[lane].queue.qsize()
        )
        
        return task.task_id
        
    async def _lane_executor(self, priority: LanePriority) -> None:
        """Execute tasks from a specific lane's queue.
        
        This runs in a loop, pulling tasks from the lane's queue and
        executing them. It handles pausing when higher-priority lanes
        are active.
        
        Args:
            priority: The lane to execute tasks from
        """
        lane = self.lanes[priority]
        logger.info("Lane executor started: %s", priority.name)
        
        while not self._stop_event.is_set():
            try:
                # Check if we should pause for higher-priority lanes
                should_pause = await self._should_pause(priority)
                if should_pause:
                    lane.is_paused = True
                    await asyncio.sleep(0.1)  # Brief pause before checking again
                    continue
                    
                lane.is_paused = False
                
                # Try to get a task with timeout so we can check stop event
                try:
                    task = await asyncio.wait_for(
                        lane.queue.get(),
                        timeout=0.5
                    )
                except asyncio.TimeoutError:
                    continue
                    
                # Execute the task
                await self._execute_task(lane, task)
                
            except asyncio.CancelledError:
                logger.info("Lane executor cancelled: %s", priority.name)
                break
            except Exception as e:
                logger.error("Lane executor error (%s): %s", priority.name, e, exc_info=True)
                await asyncio.sleep(0.1)
                
        logger.info("Lane executor stopped: %s", priority.name)
        
    async def _should_pause(self, priority: LanePriority) -> bool:
        """Check if this lane should pause due to higher-priority activity.
        
        Args:
            priority: The lane to check
            
        Returns:
            True if this lane should pause, False otherwise
        """
        # Check all higher-priority lanes
        for p in LanePriority:
            if p < priority:  # Lower value = higher priority
                lane = self.lanes[p]
                # Pause if higher-priority lane has tasks queued or is executing
                if not lane.queue.empty() or lane.is_executing:
                    return True
        return False
        
    async def _execute_task(self, lane: Lane, task: LaneTask) -> None:
        """Execute a single task from a lane.
        
        Args:
            lane: The lane this task belongs to
            task: The task to execute
        """
        lane.is_executing = True
        lane.current_task = task
        task.started_at = datetime.now()
        
        logger.debug(
            "Executing task: %s (lane=%s, queued_for=%.2fs)",
            task.name,
            lane.priority.name,
            (task.started_at - task.created_at).total_seconds()
        )
        
        try:
            # Execute the coroutine
            task.result = await task.coro
            task.completed_at = datetime.now()
            
            lane.tasks_completed += 1
            self.total_tasks_completed += 1
            
            execution_time = (task.completed_at - task.started_at).total_seconds()
            logger.debug(
                "Task completed: %s (lane=%s, time=%.2fs)",
                task.name,
                lane.priority.name,
                execution_time
            )
            
        except asyncio.CancelledError:
            task.cancelled = True
            task.completed_at = datetime.now()
            lane.tasks_cancelled += 1
            
            logger.warning("Task cancelled: %s (lane=%s)", task.name, lane.priority.name)
            raise
            
        except Exception as e:
            task.error = e
            task.completed_at = datetime.now()
            lane.tasks_failed += 1
            self.total_tasks_failed += 1
            
            logger.error(
                "Task failed: %s (lane=%s): %s",
                task.name,
                lane.priority.name,
                str(e),
                exc_info=True
            )
            
        finally:
            lane.is_executing = False
            lane.current_task = None
            
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about lane queue operation.
        
        Returns:
            Dictionary with queue stats including per-lane metrics
        """
        return {
            "started": self._started,
            "total_submitted": self.total_tasks_submitted,
            "total_completed": self.total_tasks_completed,
            "total_failed": self.total_tasks_failed,
            "lanes": {
                priority.name: {
                    "queued": lane.queue.qsize(),
                    "executing": lane.is_executing,
                    "paused": lane.is_paused,
                    "current_task": lane.current_task.name if lane.current_task else None,
                    "completed": lane.tasks_completed,
                    "failed": lane.tasks_failed,
                    "cancelled": lane.tasks_cancelled,
                }
                for priority, lane in self.lanes.items()
            }
        }
        
    def __repr__(self) -> str:
        stats = self.get_stats()
        return (
            f"LaneQueue(started={stats['started']}, "
            f"submitted={stats['total_submitted']}, "
            f"completed={stats['total_completed']}, "
            f"failed={stats['total_failed']})"
        )
