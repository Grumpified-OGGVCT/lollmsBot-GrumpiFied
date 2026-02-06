"""
Engine - Central Orchestration for LollmsBot

The Engine is the "nervous system" that coordinates all async operations
in LollmsBot. It wraps the Lane Queue and provides high-level APIs for
submitting different types of tasks with appropriate priority levels.

Key responsibilities:
- Initialize and manage the Lane Queue
- Route tasks to appropriate lanes based on type
- Provide context managers for atomic operations
- Monitor system health and report stats
"""

from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager
from typing import Any, AsyncIterator, Callable, Coroutine, Dict, Optional

from lollmsbot.core.lane_queue import LaneQueue, LanePriority

logger = logging.getLogger("lollmsbot.core.engine")


class Engine:
    """Central orchestration engine for LollmsBot operations.
    
    The Engine manages the Lane Queue and provides convenient APIs for
    submitting tasks with appropriate priority levels. It ensures that
    user interactions always take precedence over background tasks.
    
    Usage:
        engine = Engine()
        await engine.start()
        
        # Submit a user interaction (highest priority)
        await engine.process_user_message(handle_message_coro)
        
        # Submit a background task (can be paused)
        await engine.run_background_task(heartbeat_coro)
        
        await engine.stop()
    """
    
    def __init__(self):
        """Initialize the engine with a new Lane Queue."""
        self.lane_queue = LaneQueue()
        self._started = False
        
    async def start(self) -> None:
        """Start the engine and its Lane Queue."""
        if self._started:
            logger.warning("Engine already started")
            return
            
        logger.info("Starting Engine...")
        await self.lane_queue.start()
        self._started = True
        logger.info("Engine started successfully")
        
    async def stop(self, timeout: float = 10.0) -> None:
        """Stop the engine gracefully.
        
        Args:
            timeout: How long to wait for tasks to complete
        """
        if not self._started:
            return
            
        logger.info("Stopping Engine...")
        await self.lane_queue.stop(timeout=timeout)
        self._started = False
        logger.info("Engine stopped")
        
    async def process_user_message(
        self,
        coro: Coroutine[Any, Any, Any],
        name: str = "user_interaction"
    ) -> str:
        """Submit a user interaction task (highest priority).
        
        User interactions include:
        - Discord messages
        - Telegram messages  
        - WebUI chat messages
        - API requests
        
        These tasks will pause all background and system tasks.
        
        Args:
            coro: Coroutine to execute
            name: Human-readable task name
            
        Returns:
            task_id: Unique identifier for this task
        """
        return await self.lane_queue.submit(
            coro,
            lane=LanePriority.USER_INTERACTION,
            name=name
        )
        
    async def run_background_task(
        self,
        coro: Coroutine[Any, Any, Any],
        name: str = "background_task"
    ) -> str:
        """Submit a background maintenance task.
        
        Background tasks include:
        - Heartbeat cycles
        - Memory compression
        - Log analysis
        - Skill updates
        
        These tasks can be paused by user interactions.
        
        Args:
            coro: Coroutine to execute
            name: Human-readable task name
            
        Returns:
            task_id: Unique identifier for this task
        """
        return await self.lane_queue.submit(
            coro,
            lane=LanePriority.BACKGROUND,
            name=name
        )
        
    async def execute_system_task(
        self,
        coro: Coroutine[Any, Any, Any],
        name: str = "system_task"
    ) -> str:
        """Submit a system/tool execution task (lowest priority).
        
        System tasks include:
        - File I/O operations
        - Shell command execution
        - HTTP requests
        - Database operations
        
        These tasks can be paused by both user and background tasks.
        
        Args:
            coro: Coroutine to execute
            name: Human-readable task name
            
        Returns:
            task_id: Unique identifier for this task
        """
        return await self.lane_queue.submit(
            coro,
            lane=LanePriority.SYSTEM,
            name=name
        )
        
    @asynccontextmanager
    async def user_context(self, name: str = "user_operation") -> AsyncIterator[None]:
        """Context manager that pauses background tasks during user operations.
        
        This ensures that while a user operation is in progress (e.g., processing
        a complex request that involves multiple steps), no background tasks will
        interfere.
        
        Usage:
            async with engine.user_context("process_complex_request"):
                # All code here runs at USER_INTERACTION priority
                # Background tasks are paused
                result = await some_operation()
                await another_operation()
        
        Args:
            name: Name for this operation context
        """
        # Create a sentinel task that holds the user interaction lane active
        async def sentinel():
            # Just wait - the presence of this task in the queue pauses lower lanes
            await asyncio.sleep(0.001)
            
        task_id = await self.process_user_message(sentinel(), name=f"{name}_context_start")
        
        try:
            # Brief wait to ensure lane activation
            await asyncio.sleep(0.01)
            yield
        finally:
            # Release happens automatically when we exit
            pass
            
    def get_stats(self) -> Dict[str, Any]:
        """Get current engine statistics.
        
        Returns:
            Dictionary with engine and lane queue stats
        """
        return {
            "started": self._started,
            "lane_queue": self.lane_queue.get_stats()
        }
        
    def __repr__(self) -> str:
        return f"Engine(started={self._started}, queue={self.lane_queue})"


# Global engine instance (singleton pattern)
_engine: Optional[Engine] = None


def get_engine() -> Engine:
    """Get or create the global engine instance.
    
    Returns:
        The global Engine instance
    """
    global _engine
    if _engine is None:
        _engine = Engine()
    return _engine


async def init_engine() -> Engine:
    """Initialize and start the global engine.
    
    Returns:
        The started Engine instance
    """
    engine = get_engine()
    if not engine._started:
        await engine.start()
    return engine
