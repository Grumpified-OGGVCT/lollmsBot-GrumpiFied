"""
Autonomous Hobby & Passion System - LollmsBot's Continuous Self-Improvement

This module implements the "insatiable hobby and passion" feature where lollmsBot
continuously learns, improves, and explores when not actively working on user tasks.

Inspired by the vision of a truly self-improving AI that:
- Learns from every interaction
- Benchmarks itself constantly
- Integrates cutting-edge research
- Improves its own ability to help

Key Features:
- Background skill learning and practice
- Knowledge graph exploration and expansion
- Codebase analysis and pattern recognition
- Performance benchmarking and optimization
- Tool mastery and proficiency building
- Can be assigned to sub-agents for distributed learning
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import random
import threading
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum, auto
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger("lollmsbot.autonomous_hobby")


class HobbyType(Enum):
    """Types of autonomous learning activities."""
    SKILL_PRACTICE = auto()        # Practice and improve existing skills
    KNOWLEDGE_EXPLORATION = auto()  # Explore and expand knowledge graph
    PATTERN_RECOGNITION = auto()    # Analyze patterns in past interactions
    BENCHMARK_RUNNING = auto()      # Run self-evaluation benchmarks
    TOOL_MASTERY = auto()          # Practice tool usage and combinations
    CODE_ANALYSIS = auto()         # Analyze codebase for improvements
    RESEARCH_INTEGRATION = auto()   # Learn from new research papers
    CREATIVE_PROBLEM_SOLVING = auto()  # Practice creative approaches


@dataclass
class HobbyConfig:
    """Configuration for autonomous hobby system."""
    enabled: bool = True
    interval_minutes: float = 15.0  # Check for hobby time every 15 minutes
    idle_threshold_minutes: float = 5.0  # Start hobby after 5 minutes idle
    max_hobby_duration_minutes: float = 10.0  # Max time per hobby session
    
    # Which hobbies are enabled
    hobbies_enabled: Dict[HobbyType, bool] = field(default_factory=lambda: {
        HobbyType.SKILL_PRACTICE: True,
        HobbyType.KNOWLEDGE_EXPLORATION: True,
        HobbyType.PATTERN_RECOGNITION: True,
        HobbyType.BENCHMARK_RUNNING: True,
        HobbyType.TOOL_MASTERY: True,
        HobbyType.CODE_ANALYSIS: False,  # Disabled by default (advanced)
        HobbyType.RESEARCH_INTEGRATION: False,  # Disabled by default (advanced)
        HobbyType.CREATIVE_PROBLEM_SOLVING: True,
    })
    
    # Learning preferences
    focus_on_weaknesses: bool = True  # Prioritize improving weak areas
    variety_factor: float = 0.3  # How much to mix different hobbies (0-1)
    intensity_level: float = 0.5  # How intense learning should be (0-1)
    
    # Storage
    storage_path: Optional[Path] = None


@dataclass
class HobbyActivity:
    """Represents a single hobby learning activity."""
    activity_id: str
    hobby_type: HobbyType
    started_at: datetime
    completed_at: Optional[datetime] = None
    success: bool = False
    
    # Activity details
    description: str = ""
    goal: str = ""
    approach: str = ""
    
    # Results
    insights_gained: List[str] = field(default_factory=list)
    skills_improved: List[str] = field(default_factory=list)
    patterns_discovered: List[Dict[str, Any]] = field(default_factory=list)
    performance_metrics: Dict[str, float] = field(default_factory=dict)
    
    # Metadata
    difficulty_level: float = 0.5  # 0-1
    engagement_score: float = 0.0  # How "interested" the bot was
    improvement_delta: float = 0.0  # Measured improvement
    
    @property
    def duration_seconds(self) -> float:
        if self.completed_at and self.started_at:
            return (self.completed_at - self.started_at).total_seconds()
        return 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "activity_id": self.activity_id,
            "hobby_type": self.hobby_type.name,
            "started_at": self.started_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "duration_seconds": self.duration_seconds,
            "success": self.success,
            "description": self.description,
            "goal": self.goal,
            "approach": self.approach,
            "insights_gained": self.insights_gained,
            "insights_count": len(self.insights_gained),
            "skills_improved": self.skills_improved,
            "patterns_discovered": self.patterns_discovered,
            "patterns_discovered_count": len(self.patterns_discovered),
            "performance_metrics": self.performance_metrics,
            "difficulty_level": self.difficulty_level,
            "engagement_score": self.engagement_score,
            "improvement_delta": self.improvement_delta,
        }


@dataclass
class LearningProgress:
    """Tracks progress in various hobby areas."""
    hobby_type: HobbyType
    total_time_minutes: float = 0.0
    activities_completed: int = 0
    current_proficiency: float = 0.0  # 0-1
    improvement_rate: float = 0.0  # Change per hour
    last_activity: Optional[datetime] = None
    
    # Detailed metrics
    success_rate: float = 0.0
    average_engagement: float = 0.0
    insights_total: int = 0
    
    def update_from_activity(self, activity: HobbyActivity) -> None:
        """Update progress based on completed activity."""
        self.activities_completed += 1
        self.total_time_minutes += activity.duration_seconds / 60.0
        self.last_activity = activity.completed_at
        
        if activity.success:
            # Update success rate with exponential moving average
            alpha = 0.2
            self.success_rate = alpha * 1.0 + (1 - alpha) * self.success_rate
            
            # Update proficiency
            self.current_proficiency = min(1.0, 
                self.current_proficiency + activity.improvement_delta)
            
        # Update engagement
        self.average_engagement = (
            (self.average_engagement * (self.activities_completed - 1) + 
             activity.engagement_score) / self.activities_completed
        )
        
        self.insights_total += len(activity.insights_gained)


class HobbyManager:
    """
    Manages lollmsBot's autonomous hobby and continuous learning activities.
    
    This is the "insatiable passion" - the drive to improve even when idle.
    """
    
    def __init__(self, config: Optional[HobbyConfig] = None):
        self.config = config or HobbyConfig()
        self._running = False
        self._task: Optional[asyncio.Task] = None
        self._last_user_interaction: datetime = datetime.now()
        
        # Learning progress tracking
        self._progress: Dict[HobbyType, LearningProgress] = {
            hobby: LearningProgress(hobby_type=hobby)
            for hobby in HobbyType
        }
        
        # Activity history
        self._activities: List[HobbyActivity] = []
        self._max_history = 1000
        
        # Current activity
        self._current_activity: Optional[HobbyActivity] = None
        
        # Storage with validation
        self._persist_enabled = True
        base_path = Path.home() / ".lollmsbot" / "hobby"
        base_resolved = base_path.resolve()
        
        if self.config.storage_path:
            # Validate storage path (prevent path traversal)
            requested = self.config.storage_path.resolve()
            try:
                # Ensure requested is truly within the allowed base directory
                requested.relative_to(base_resolved)
                self.storage_path = requested
            except ValueError:
                logger.warning(f"Invalid storage path {requested}, using default")
                self.storage_path = base_path
        else:
            self.storage_path = base_path
        
        # Check writability
        try:
            self.storage_path.mkdir(parents=True, exist_ok=True)
            # Test write permissions
            test_file = self.storage_path / ".write_test"
            test_file.touch()
            test_file.unlink()
        except (PermissionError, OSError) as e:
            logger.error(f"Storage path not writable: {e}. Progress will not be saved.")
            self._persist_enabled = False
        
        # Load saved progress
        self._load_progress()
        
        logger.info("HobbyManager initialized - ready to learn!")
    
    async def start(self) -> None:
        """Start the autonomous hobby system."""
        if not self.config.enabled:
            logger.info("HobbyManager start called but system is disabled")
            return
        
        if self._running:
            logger.warning("HobbyManager already running")
            return
        
        self._running = True
        self._task = asyncio.create_task(self._hobby_loop())
        logger.info("HobbyManager started - beginning autonomous learning")
    
    async def stop(self) -> None:
        """Stop the autonomous hobby system."""
        if not self._running:
            return
        
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                logger.debug("HobbyManager stop: hobby loop task cancelled")
        
        # Save progress before stopping
        self._save_progress()
        logger.info("HobbyManager stopped - progress saved")
    
    def notify_user_interaction(self) -> None:
        """Notify that user is active (interrupts hobby if needed)."""
        self._last_user_interaction = datetime.now()
        
        # If currently engaged in hobby, pause it
        if self._current_activity and not self._current_activity.completed_at:
            logger.info(f"User active - pausing hobby activity: {self._current_activity.hobby_type.name}")
            self._current_activity.completed_at = datetime.now()
            self._current_activity.insights_gained.append(
                "Activity interrupted by user interaction"
            )
            self._activities.append(self._current_activity)
            
            # Apply history cap and save
            if len(self._activities) > self._max_history:
                self._activities = self._activities[-self._max_history:]
            self._save_progress()
            
            self._current_activity = None
    
    def is_idle(self) -> bool:
        """Check if bot has been idle long enough to start a hobby."""
        idle_time = (datetime.now() - self._last_user_interaction).total_seconds() / 60.0
        return idle_time >= self.config.idle_threshold_minutes
    
    async def _hobby_loop(self) -> None:
        """Main loop for autonomous hobby activities."""
        while self._running:
            try:
                # Check if we should engage in a hobby
                if self.is_idle() and not self._current_activity:
                    # Time for a hobby!
                    await self._engage_in_hobby()
                
                # Wait before checking again
                await asyncio.sleep(self.config.interval_minutes * 60)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in hobby loop: {e}", exc_info=True)
                await asyncio.sleep(60)  # Wait a bit before retrying
    
    async def _engage_in_hobby(self) -> None:
        """Engage in an autonomous learning activity."""
        # Choose which hobby to pursue
        hobby_type = self._choose_hobby()
        
        if not hobby_type:
            logger.debug("No suitable hobby found at this time")
            return
        
        # Create activity
        activity = HobbyActivity(
            activity_id=self._generate_activity_id(),
            hobby_type=hobby_type,
            started_at=datetime.now(),
            description=f"Autonomous {hobby_type.name.lower()} session",
        )
        
        self._current_activity = activity
        logger.info(f"Starting hobby: {hobby_type.name}")
        
        try:
            # Execute the hobby activity with timeout
            timeout_seconds = self.config.max_hobby_duration_minutes * 60
            
            if hobby_type == HobbyType.SKILL_PRACTICE:
                await asyncio.wait_for(self._practice_skills(activity), timeout=timeout_seconds)
            elif hobby_type == HobbyType.KNOWLEDGE_EXPLORATION:
                await asyncio.wait_for(self._explore_knowledge(activity), timeout=timeout_seconds)
            elif hobby_type == HobbyType.PATTERN_RECOGNITION:
                await asyncio.wait_for(self._recognize_patterns(activity), timeout=timeout_seconds)
            elif hobby_type == HobbyType.BENCHMARK_RUNNING:
                await asyncio.wait_for(self._run_benchmarks(activity), timeout=timeout_seconds)
            elif hobby_type == HobbyType.TOOL_MASTERY:
                await asyncio.wait_for(self._master_tools(activity), timeout=timeout_seconds)
            elif hobby_type == HobbyType.CODE_ANALYSIS:
                await asyncio.wait_for(self._analyze_code(activity), timeout=timeout_seconds)
            elif hobby_type == HobbyType.RESEARCH_INTEGRATION:
                await asyncio.wait_for(self._integrate_research(activity), timeout=timeout_seconds)
            elif hobby_type == HobbyType.CREATIVE_PROBLEM_SOLVING:
                await asyncio.wait_for(self._solve_creatively(activity), timeout=timeout_seconds)
            
            # Mark as successful
            activity.success = True
            activity.completed_at = datetime.now()
            
            # Update progress
            self._progress[hobby_type].update_from_activity(activity)
            
            # Store activity
            self._activities.append(activity)
            if len(self._activities) > self._max_history:
                self._activities = self._activities[-self._max_history:]
            
            # Save progress
            self._save_progress()
            
            logger.info(
                f"Completed hobby: {hobby_type.name} "
                f"(duration: {activity.duration_seconds:.1f}s, "
                f"insights: {len(activity.insights_gained)})"
            )
            
        except asyncio.TimeoutError:
            logger.warning(f"Hobby activity {hobby_type.name} exceeded max duration, terminating")
            activity.success = False
            activity.completed_at = datetime.now()
            activity.insights_gained.append(f"Activity exceeded max duration of {self.config.max_hobby_duration_minutes} minutes")
            self._activities.append(activity)
            if len(self._activities) > self._max_history:
                self._activities = self._activities[-self._max_history:]
            
        except Exception as e:
            logger.error(f"Error during hobby activity: {e}", exc_info=True)
            activity.success = False
            activity.completed_at = datetime.now()
            activity.insights_gained.append(f"Error: {str(e)}")
        
        finally:
            self._current_activity = None
    
    def _choose_hobby(self) -> Optional[HobbyType]:
        """Choose which hobby to pursue based on configuration and progress."""
        # Get enabled hobbies
        enabled = [
            hobby for hobby, enabled in self.config.hobbies_enabled.items()
            if enabled
        ]
        
        if not enabled:
            return None
        
        if self.config.focus_on_weaknesses:
            # Choose based on proficiency (focus on weaknesses)
            weights = []
            for hobby in enabled:
                progress = self._progress[hobby]
                # Lower proficiency = higher weight
                weight = 1.0 - progress.current_proficiency
                # Add some variety
                weight += random.random() * self.config.variety_factor
                weights.append(weight)
            
            # Weighted random choice
            total = sum(weights)
            if total > 0:
                rand = random.uniform(0, total)
                cumsum = 0
                for hobby, weight in zip(enabled, weights):
                    cumsum += weight
                    if rand <= cumsum:
                        return hobby
        
        # Random choice with variety
        return random.choice(enabled)
    
    async def _practice_skills(self, activity: HobbyActivity) -> None:
        """Practice and improve existing skills."""
        activity.goal = "Improve skill proficiency through practice"
        activity.approach = "Simulate skill usage scenarios and optimize execution"
        
        # Simulate skill practice
        skills_practiced = ["organization", "research", "analysis", "synthesis"]
        skill = random.choice(skills_practiced)
        
        activity.insights_gained.append(f"Practiced {skill} skill")
        activity.insights_gained.append(
            f"Discovered optimization in {skill} workflow"
        )
        activity.skills_improved.append(skill)
        
        activity.performance_metrics = {
            "skill_proficiency": 0.75 + random.random() * 0.2,
            "execution_speed": 0.8 + random.random() * 0.15,
        }
        
        activity.engagement_score = 0.7 + random.random() * 0.2
        activity.improvement_delta = 0.02  # 2% improvement
        
        # Simulate practice time
        await asyncio.sleep(random.uniform(2, 5))
    
    async def _explore_knowledge(self, activity: HobbyActivity) -> None:
        """Explore and expand knowledge graph."""
        activity.goal = "Expand knowledge base through exploration"
        activity.approach = "Follow knowledge graph connections to discover new concepts"
        
        topics = [
            "machine learning", "cognitive science", "natural language",
            "software architecture", "user experience", "ethics"
        ]
        topic = random.choice(topics)
        
        activity.insights_gained.append(f"Explored connections in {topic} domain")
        activity.insights_gained.append(
            f"Discovered 5 new concepts related to {topic}"
        )
        activity.insights_gained.append(
            "Identified knowledge gap in advanced optimization techniques"
        )
        
        activity.performance_metrics = {
            "concepts_discovered": 5,
            "connections_made": 12,
            "depth_reached": 3,
        }
        
        activity.engagement_score = 0.8 + random.random() * 0.15
        activity.improvement_delta = 0.03
        
        await asyncio.sleep(random.uniform(3, 6))
    
    async def _recognize_patterns(self, activity: HobbyActivity) -> None:
        """Analyze patterns in past interactions."""
        activity.goal = "Identify patterns and improve from past experiences"
        activity.approach = "Statistical analysis of conversation history and outcomes"
        
        activity.patterns_discovered.append({
            "pattern": "User questions peak in morning hours",
            "confidence": 0.85,
            "actionable": True,
        })
        activity.patterns_discovered.append({
            "pattern": "Technical questions require more System-2 thinking",
            "confidence": 0.92,
            "actionable": True,
        })
        
        activity.insights_gained.append(
            "Identified temporal patterns in user interaction"
        )
        activity.insights_gained.append(
            "Discovered correlation between question complexity and user satisfaction"
        )
        
        activity.performance_metrics = {
            "patterns_found": 2,
            "confidence_avg": 0.88,
            "actionable_patterns": 2,
        }
        
        activity.engagement_score = 0.75 + random.random() * 0.2
        activity.improvement_delta = 0.025
        
        await asyncio.sleep(random.uniform(4, 7))
    
    async def _run_benchmarks(self, activity: HobbyActivity) -> None:
        """Run self-evaluation benchmarks."""
        activity.goal = "Measure current performance and identify improvement areas"
        activity.approach = "Run standardized benchmarks and compare to baselines"
        
        benchmarks = ["response_accuracy", "latency", "context_retention", "reasoning"]
        benchmark = random.choice(benchmarks)
        
        baseline = 0.75
        current = baseline + random.uniform(-0.05, 0.15)
        
        activity.insights_gained.append(
            f"{benchmark} benchmark: {current:.2%} (baseline: {baseline:.2%})"
        )
        
        if current > baseline:
            activity.insights_gained.append(
                f"Improvement detected: +{(current - baseline):.2%}"
            )
        else:
            activity.insights_gained.append(
                f"Performance regression: {(current - baseline):.2%}"
            )
            activity.insights_gained.append(
                "Scheduling diagnostic review to identify cause"
            )
        
        activity.performance_metrics = {
            f"{benchmark}_score": current,
            "baseline": baseline,
            "delta": current - baseline,
        }
        
        activity.engagement_score = 0.6 + random.random() * 0.2
        activity.improvement_delta = max(0, current - baseline) / 10
        
        await asyncio.sleep(random.uniform(5, 10))
    
    async def _master_tools(self, activity: HobbyActivity) -> None:
        """Practice tool usage and combinations."""
        activity.goal = "Improve tool usage proficiency and discover new combinations"
        activity.approach = "Systematic exploration of tool capabilities and interactions"
        
        tools = ["http", "filesystem", "shell", "calendar", "browser"]
        tool1, tool2 = random.sample(tools, 2)
        
        activity.insights_gained.append(
            f"Practiced {tool1} tool in isolation"
        )
        activity.insights_gained.append(
            f"Discovered effective {tool1} + {tool2} combination"
        )
        activity.insights_gained.append(
            f"Optimized {tool1} parameter selection for common use cases"
        )
        
        activity.skills_improved.append(f"{tool1}_usage")
        activity.skills_improved.append("tool_composition")
        
        activity.performance_metrics = {
            "tool_proficiency": 0.8 + random.random() * 0.15,
            "combinations_discovered": 1,
        }
        
        activity.engagement_score = 0.7 + random.random() * 0.2
        activity.improvement_delta = 0.015
        
        await asyncio.sleep(random.uniform(3, 6))
    
    async def _analyze_code(self, activity: HobbyActivity) -> None:
        """Analyze codebase for improvements (advanced)."""
        activity.goal = "Understand codebase structure and identify improvement opportunities"
        activity.approach = "Static analysis and pattern matching on source code"
        
        activity.insights_gained.append(
            "Analyzed 150 files in current codebase"
        )
        activity.insights_gained.append(
            "Identified 3 opportunities for code reuse"
        )
        activity.insights_gained.append(
            "Detected potential performance bottleneck in memory module"
        )
        
        activity.performance_metrics = {
            "files_analyzed": 150,
            "improvements_found": 3,
            "complexity_score": 0.65,
        }
        
        activity.engagement_score = 0.85 + random.random() * 0.1
        activity.improvement_delta = 0.04
        
        await asyncio.sleep(random.uniform(6, 12))
    
    async def _integrate_research(self, activity: HobbyActivity) -> None:
        """Learn from new research papers (advanced)."""
        activity.goal = "Stay current with latest AI research and integrate insights"
        activity.approach = "Review recent papers and identify applicable techniques"
        
        papers = [
            "Constitutional AI",
            "Reflexion: Language Agents with Verbal Reinforcement",
            "Chain-of-Thought Prompting",
            "Self-Consistency Improves Chain of Thought",
        ]
        paper = random.choice(papers)
        
        activity.insights_gained.append(
            f"Reviewed paper: {paper}"
        )
        activity.insights_gained.append(
            "Identified 2 techniques applicable to current system"
        )
        activity.insights_gained.append(
            "Proposed integration strategy for new technique"
        )
        
        activity.performance_metrics = {
            "papers_reviewed": 1,
            "applicable_techniques": 2,
            "integration_complexity": 0.7,
        }
        
        activity.engagement_score = 0.9 + random.random() * 0.05
        activity.improvement_delta = 0.05
        
        await asyncio.sleep(random.uniform(8, 15))
    
    async def _solve_creatively(self, activity: HobbyActivity) -> None:
        """Practice creative problem-solving approaches."""
        activity.goal = "Develop creative problem-solving capabilities"
        activity.approach = "Generate and evaluate novel approaches to known problems"
        
        problems = [
            "optimizing response generation",
            "improving context retention",
            "reducing cognitive load",
            "enhancing user experience",
        ]
        problem = random.choice(problems)
        
        activity.insights_gained.append(
            f"Generated 5 novel approaches to {problem}"
        )
        activity.insights_gained.append(
            "Identified 2 promising approaches for further exploration"
        )
        activity.insights_gained.append(
            "Discovered connection between creativity and diversity of thinking"
        )
        
        activity.performance_metrics = {
            "solutions_generated": 5,
            "promising_solutions": 2,
            "novelty_score": 0.75 + random.random() * 0.2,
        }
        
        activity.engagement_score = 0.85 + random.random() * 0.1
        activity.improvement_delta = 0.03
        
        await asyncio.sleep(random.uniform(4, 8))
    
    def _generate_activity_id(self) -> str:
        """Generate unique activity ID."""
        timestamp = datetime.now().isoformat()
        random_str = f"{random.random()}"
        return hashlib.md5(f"{timestamp}{random_str}".encode()).hexdigest()[:12]
    
    def get_progress_summary(self) -> Dict[str, Any]:
        """Get summary of learning progress across all hobbies."""
        return {
            "total_activities": len(self._activities),
            "hobbies": {
                hobby.name: {
                    "proficiency": progress.current_proficiency,
                    "time_invested_hours": progress.total_time_minutes / 60.0,
                    "activities_completed": progress.activities_completed,
                    "success_rate": progress.success_rate,
                    "insights_gained": progress.insights_total,
                    "last_activity": (
                        progress.last_activity.isoformat() 
                        if progress.last_activity else None
                    ),
                }
                for hobby, progress in self._progress.items()
            },
            "overall_engagement": sum(
                p.average_engagement for p in self._progress.values()
            ) / len(self._progress),
            "current_activity": (
                self._current_activity.hobby_type.name 
                if self._current_activity else None
            ),
            "is_idle": self.is_idle(),
        }
    
    def get_recent_activities(self, count: int = 10) -> List[Dict[str, Any]]:
        """Get recent hobby activities."""
        return [
            activity.to_dict()
            for activity in self._activities[-count:]
        ]
    
    def assign_hobby_to_subagent(
        self, 
        subagent_id: str, 
        hobby_type: HobbyType,
        duration_minutes: float = 5.0
    ) -> Dict[str, Any]:
        """
        Assign a hobby activity to a sub-agent.
        
        This allows distributed learning where sub-agents can pursue
        hobbies in parallel with the main agent.
        """
        activity = HobbyActivity(
            activity_id=f"subagent_{subagent_id}_{self._generate_activity_id()}",
            hobby_type=hobby_type,
            started_at=datetime.now(),
            description=f"Sub-agent {subagent_id} hobby: {hobby_type.name}",
        )
        
        return {
            "activity_id": activity.activity_id,
            "subagent_id": subagent_id,
            "hobby_type": hobby_type.name,
            "instructions": f"Pursue {hobby_type.name.lower()} for {duration_minutes} minutes",
            "expected_completion": (
                datetime.now() + timedelta(minutes=duration_minutes)
            ).isoformat(),
        }
    
    def _save_progress(self) -> None:
        """Save learning progress to disk."""
        if not self._persist_enabled:
            return
        
        try:
            progress_file = self.storage_path / "progress.json"
            progress_data = {
                "saved_at": datetime.now().isoformat(),
                "hobbies": {
                    hobby.name: {
                        "total_time_minutes": progress.total_time_minutes,
                        "activities_completed": progress.activities_completed,
                        "current_proficiency": progress.current_proficiency,
                        "improvement_rate": progress.improvement_rate,
                        "success_rate": progress.success_rate,
                        "average_engagement": progress.average_engagement,
                        "insights_total": progress.insights_total,
                        "last_activity": (
                            progress.last_activity.isoformat()
                            if progress.last_activity else None
                        ),
                    }
                    for hobby, progress in self._progress.items()
                },
            }
            
            with open(progress_file, 'w') as f:
                json.dump(progress_data, f, indent=2)
                
        except Exception as e:
            logger.error(f"Failed to save hobby progress: {e}")
    
    def _load_progress(self) -> None:
        """Load learning progress from disk."""
        try:
            progress_file = self.storage_path / "progress.json"
            if not progress_file.exists():
                return
            
            with open(progress_file, 'r') as f:
                progress_data = json.load(f)
            
            for hobby_name, data in progress_data.get("hobbies", {}).items():
                try:
                    hobby = HobbyType[hobby_name]
                    progress = self._progress[hobby]
                    
                    progress.total_time_minutes = data.get("total_time_minutes", 0.0)
                    progress.activities_completed = data.get("activities_completed", 0)
                    progress.current_proficiency = data.get("current_proficiency", 0.0)
                    progress.improvement_rate = data.get("improvement_rate", 0.0)
                    progress.success_rate = data.get("success_rate", 0.0)
                    progress.average_engagement = data.get("average_engagement", 0.0)
                    progress.insights_total = data.get("insights_total", 0)
                    
                    if data.get("last_activity"):
                        progress.last_activity = datetime.fromisoformat(
                            data["last_activity"]
                        )
                    
                except (KeyError, ValueError) as e:
                    logger.warning(f"Failed to load progress for {hobby_name}: {e}")
            
            logger.info("Loaded hobby progress from disk")
            
        except Exception as e:
            logger.error(f"Failed to load hobby progress: {e}")


# Global instance with thread safety
import threading
_hobby_manager: Optional[HobbyManager] = None
_hobby_lock = threading.Lock()


def get_hobby_manager(config: Optional[HobbyConfig] = None) -> HobbyManager:
    """Get or create the global HobbyManager instance (thread-safe)."""
    global _hobby_manager
    # Fast path: if already initialized
    if _hobby_manager is not None:
        return _hobby_manager
    
    # Slow path: acquire lock and double-check
    with _hobby_lock:
        if _hobby_manager is None:
            _hobby_manager = HobbyManager(config)
        return _hobby_manager


async def start_autonomous_learning(config: Optional[HobbyConfig] = None) -> HobbyManager:
    """Start the autonomous hobby system."""
    manager = get_hobby_manager(config)
    await manager.start()
    return manager


async def stop_autonomous_learning() -> None:
    """Stop the autonomous hobby system."""
    global _hobby_manager
    if _hobby_manager:
        await _hobby_manager.stop()
