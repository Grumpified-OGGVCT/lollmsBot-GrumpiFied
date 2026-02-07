"""
Test suite for autonomous hobby and continuous learning system.
"""

import asyncio
import pytest
from datetime import datetime, timedelta

from lollmsbot.autonomous_hobby import (
    HobbyManager,
    HobbyConfig,
    HobbyType,
    HobbyActivity,
    get_hobby_manager,
    start_autonomous_learning,
    stop_autonomous_learning,
)


@pytest.fixture
def hobby_config():
    """Create a test hobby configuration."""
    return HobbyConfig(
        enabled=True,
        interval_minutes=0.1,  # Check every 6 seconds for testing
        idle_threshold_minutes=0.05,  # Start after 3 seconds idle
        max_hobby_duration_minutes=0.1,  # Max 6 seconds per hobby
        focus_on_weaknesses=True,
        variety_factor=0.3,
        intensity_level=0.5,
    )


@pytest.fixture
def hobby_manager(hobby_config):
    """Create a hobby manager for testing."""
    manager = HobbyManager(hobby_config)
    yield manager
    # Cleanup
    import asyncio
    asyncio.run(manager.stop())


class TestHobbyConfiguration:
    """Test hobby configuration."""
    
    def test_config_defaults(self):
        """Test default configuration values."""
        config = HobbyConfig()
        assert config.enabled == True
        assert config.interval_minutes == 15.0
        assert config.idle_threshold_minutes == 5.0
        assert config.max_hobby_duration_minutes == 10.0
        assert len(config.hobbies_enabled) == len(HobbyType)
    
    def test_config_customization(self):
        """Test custom configuration."""
        config = HobbyConfig(
            enabled=False,
            interval_minutes=30.0,
            hobbies_enabled={
                HobbyType.SKILL_PRACTICE: True,
                HobbyType.KNOWLEDGE_EXPLORATION: False,
            }
        )
        assert config.enabled == False
        assert config.interval_minutes == 30.0
        assert config.hobbies_enabled[HobbyType.SKILL_PRACTICE] == True
        assert config.hobbies_enabled[HobbyType.KNOWLEDGE_EXPLORATION] == False


class TestHobbyManager:
    """Test hobby manager functionality."""
    
    @pytest.mark.asyncio
    async def test_manager_initialization(self, hobby_manager):
        """Test manager initializes correctly."""
        assert hobby_manager.config.enabled == True
        assert len(hobby_manager._progress) == len(HobbyType)
        assert hobby_manager._running == False
        assert hobby_manager._current_activity is None
    
    @pytest.mark.asyncio
    async def test_manager_start_stop(self, hobby_manager):
        """Test starting and stopping the manager."""
        # Start
        await hobby_manager.start()
        assert hobby_manager._running == True
        assert hobby_manager._task is not None
        
        # Stop
        await hobby_manager.stop()
        assert hobby_manager._running == False
    
    @pytest.mark.asyncio
    async def test_idle_detection(self, hobby_manager):
        """Test idle time detection."""
        # Initially should be idle after exceeding idle threshold
        await asyncio.sleep(3.2)  # Wait longer than idle threshold (0.05 minutes ≈ 3 seconds)
        assert hobby_manager.is_idle() == True
        
        # After user interaction, should not be idle
        hobby_manager.notify_user_interaction()
        assert hobby_manager.is_idle() == False
    
    @pytest.mark.asyncio
    async def test_user_interaction_notification(self, hobby_manager):
        """Test that user interaction pauses hobbies."""
        # Create a mock current activity
        activity = HobbyActivity(
            activity_id="test_001",
            hobby_type=HobbyType.SKILL_PRACTICE,
            started_at=datetime.now(),
        )
        hobby_manager._current_activity = activity
        
        # Notify user interaction
        hobby_manager.notify_user_interaction()
        
        # Activity should be completed
        assert activity.completed_at is not None
        assert hobby_manager._current_activity is None
    
    @pytest.mark.asyncio
    async def test_hobby_selection(self, hobby_manager):
        """Test hobby selection algorithm."""
        # Enable only one hobby for deterministic selection
        hobby_manager.config.hobbies_enabled = {
            hobby: (hobby == HobbyType.SKILL_PRACTICE)
            for hobby in HobbyType
        }
        
        selected = hobby_manager._choose_hobby()
        assert selected == HobbyType.SKILL_PRACTICE
    
    @pytest.mark.asyncio
    async def test_progress_tracking(self, hobby_manager):
        """Test learning progress tracking."""
        # Create and complete an activity
        activity = HobbyActivity(
            activity_id="test_001",
            hobby_type=HobbyType.SKILL_PRACTICE,
            started_at=datetime.now() - timedelta(seconds=30),
            completed_at=datetime.now(),
            success=True,
            insights_gained=["Improved skill proficiency"],
            skills_improved=["organization"],
            engagement_score=0.8,
            improvement_delta=0.02,
        )
        
        # Update progress
        progress = hobby_manager._progress[HobbyType.SKILL_PRACTICE]
        progress.update_from_activity(activity)
        
        # Check progress updated
        assert progress.activities_completed == 1
        assert progress.success_rate > 0
        assert progress.average_engagement > 0
        assert progress.insights_total == 1
    
    @pytest.mark.asyncio
    async def test_progress_summary(self, hobby_manager):
        """Test getting progress summary."""
        summary = hobby_manager.get_progress_summary()
        
        assert "total_activities" in summary
        assert "hobbies" in summary
        assert "overall_engagement" in summary
        assert "is_idle" in summary
        
        # Check hobby details
        for hobby_name, details in summary["hobbies"].items():
            assert "proficiency" in details
            assert "time_invested_hours" in details
            assert "activities_completed" in details
            assert "success_rate" in details
    
    @pytest.mark.asyncio
    async def test_subagent_assignment(self, hobby_manager):
        """Test assigning hobbies to sub-agents."""
        assignment = hobby_manager.assign_hobby_to_subagent(
            subagent_id="test_subagent_1",
            hobby_type=HobbyType.KNOWLEDGE_EXPLORATION,
            duration_minutes=5.0,
        )
        
        assert "activity_id" in assignment
        assert "subagent_id" in assignment
        assert assignment["subagent_id"] == "test_subagent_1"
        assert assignment["hobby_type"] == "KNOWLEDGE_EXPLORATION"
        assert "instructions" in assignment
        assert "expected_completion" in assignment


class TestHobbyActivities:
    """Test individual hobby activity implementations."""
    
    @pytest.mark.asyncio
    async def test_skill_practice(self, hobby_manager):
        """Test skill practice activity."""
        activity = HobbyActivity(
            activity_id="test_skill_001",
            hobby_type=HobbyType.SKILL_PRACTICE,
            started_at=datetime.now(),
        )
        
        await hobby_manager._practice_skills(activity)
        
        assert activity.success == False  # Not marked successful yet
        assert len(activity.insights_gained) > 0
        assert len(activity.skills_improved) > 0
        assert activity.engagement_score > 0
        assert activity.improvement_delta > 0
    
    @pytest.mark.asyncio
    async def test_knowledge_exploration(self, hobby_manager):
        """Test knowledge exploration activity."""
        activity = HobbyActivity(
            activity_id="test_knowledge_001",
            hobby_type=HobbyType.KNOWLEDGE_EXPLORATION,
            started_at=datetime.now(),
        )
        
        await hobby_manager._explore_knowledge(activity)
        
        assert len(activity.insights_gained) > 0
        assert "performance_metrics" in activity.performance_metrics
        assert activity.engagement_score > 0
    
    @pytest.mark.asyncio
    async def test_pattern_recognition(self, hobby_manager):
        """Test pattern recognition activity."""
        activity = HobbyActivity(
            activity_id="test_pattern_001",
            hobby_type=HobbyType.PATTERN_RECOGNITION,
            started_at=datetime.now(),
        )
        
        await hobby_manager._recognize_patterns(activity)
        
        assert len(activity.patterns_discovered) > 0
        assert len(activity.insights_gained) > 0
        # Check pattern structure
        if activity.patterns_discovered:
            pattern = activity.patterns_discovered[0]
            assert "pattern" in pattern
            assert "confidence" in pattern
            assert "actionable" in pattern
    
    @pytest.mark.asyncio
    async def test_benchmark_running(self, hobby_manager):
        """Test benchmark running activity."""
        activity = HobbyActivity(
            activity_id="test_benchmark_001",
            hobby_type=HobbyType.BENCHMARK_RUNNING,
            started_at=datetime.now(),
        )
        
        await hobby_manager._run_benchmarks(activity)
        
        assert len(activity.insights_gained) > 0
        assert len(activity.performance_metrics) > 0
    
    @pytest.mark.asyncio
    async def test_tool_mastery(self, hobby_manager):
        """Test tool mastery activity."""
        activity = HobbyActivity(
            activity_id="test_tool_001",
            hobby_type=HobbyType.TOOL_MASTERY,
            started_at=datetime.now(),
        )
        
        await hobby_manager._master_tools(activity)
        
        assert len(activity.insights_gained) > 0
        assert len(activity.skills_improved) > 0
        assert activity.engagement_score > 0


class TestPersistence:
    """Test persistence of hobby progress."""
    
    @pytest.mark.asyncio
    async def test_save_progress(self, tmp_path):
        """Test saving progress to disk."""
        # Create manager with test storage path
        config = HobbyConfig(storage_path=tmp_path / "hobby")
        hobby_manager = HobbyManager(config)
        
        # Update some progress
        progress = hobby_manager._progress[HobbyType.SKILL_PRACTICE]
        progress.activities_completed = 5
        progress.current_proficiency = 0.75
        
        # Save
        hobby_manager._save_progress()
        
        # Check file was created
        progress_file = hobby_manager.storage_path / "progress.json"
        assert progress_file.exists()
    
    @pytest.mark.asyncio
    async def test_load_progress(self, tmp_path):
        """Test loading progress from disk."""
        # Create first manager with test storage path
        config = HobbyConfig(storage_path=tmp_path / "hobby")
        hobby_manager = HobbyManager(config)
        
        # Set some progress
        progress = hobby_manager._progress[HobbyType.SKILL_PRACTICE]
        progress.activities_completed = 10
        progress.current_proficiency = 0.85
        
        # Save
        hobby_manager._save_progress()
        
        # Create new manager with same storage (will load saved progress)
        new_config = HobbyConfig(storage_path=tmp_path / "hobby")
        new_manager = HobbyManager(new_config)
        
        # Check progress was loaded
        loaded_progress = new_manager._progress[HobbyType.SKILL_PRACTICE]
        assert loaded_progress.activities_completed == 10
        assert loaded_progress.current_proficiency == 0.85


class TestGlobalInstance:
    """Test global hobby manager instance."""
    
    def test_get_hobby_manager(self):
        """Test getting global instance."""
        manager1 = get_hobby_manager()
        manager2 = get_hobby_manager()
        
        # Should return same instance
        assert manager1 is manager2
    
    @pytest.mark.asyncio
    async def test_start_stop_global(self):
        """Test starting and stopping global instance."""
        manager = await start_autonomous_learning()
        assert manager._running == True
        
        await stop_autonomous_learning()
        assert manager._running == False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
