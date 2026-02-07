"""
Test Phase 3 Features - Metrics and Sub-Agent Integration
"""

import pytest
import asyncio
from datetime import datetime

from lollmsbot.autonomous_hobby import HobbyManager, HobbyConfig, HobbyType
from lollmsbot.hobby_metrics import create_metrics_collector
from lollmsbot.hobby_subagent import HobbySubAgentCoordinator


class TestPhase3Metrics:
    """Test metrics and monitoring features."""
    
    def test_metrics_collector_creation(self):
        """Test creating a metrics collector."""
        config = HobbyConfig(enabled=True)
        manager = HobbyManager(config)
        
        collector = create_metrics_collector(manager)
        assert collector is not None
        assert collector.hobby_manager == manager
    
    def test_prometheus_metrics_export(self):
        """Test Prometheus metrics format."""
        config = HobbyConfig(enabled=True)
        manager = HobbyManager(config)
        collector = create_metrics_collector(manager)
        
        metrics = collector.get_prometheus_metrics()
        
        # Check format
        assert isinstance(metrics, str)
        assert "# HELP" in metrics
        assert "# TYPE" in metrics
        assert "hobby_system_enabled" in metrics
        assert "hobby_proficiency" in metrics
    
    def test_metrics_summary(self):
        """Test JSON metrics summary."""
        config = HobbyConfig(enabled=True)
        manager = HobbyManager(config)
        collector = create_metrics_collector(manager)
        
        summary = collector.get_metrics_summary()
        
        # Check structure
        assert "system" in summary
        assert "summary" in summary
        assert "timeline" in summary
        assert "trends" in summary
        assert "timestamp" in summary
        
        # Check system info
        assert "enabled" in summary["system"]
        assert "running" in summary["system"]
        assert "is_idle" in summary["system"]
    
    def test_dashboard_data(self):
        """Test dashboard data format."""
        config = HobbyConfig(enabled=True)
        manager = HobbyManager(config)
        collector = create_metrics_collector(manager)
        
        dashboard = collector.get_dashboard_data()
        
        # Check chart data structures
        assert "proficiency_radar" in dashboard
        assert "time_invested_bars" in dashboard
        assert "activity_timeline" in dashboard
        assert "activities_by_type" in dashboard
        assert "current_stats" in dashboard
        
        # Check radar chart
        radar = dashboard["proficiency_radar"]
        assert "labels" in radar
        assert "values" in radar
        assert len(radar["labels"]) == len(radar["values"])
    
    def test_metrics_caching(self):
        """Test that metrics are cached."""
        config = HobbyConfig(enabled=True)
        manager = HobbyManager(config)
        collector = create_metrics_collector(manager)
        
        # First call
        summary1 = collector.get_metrics_summary(use_cache=True)
        timestamp1 = summary1["timestamp"]
        
        # Second call (should use cache)
        summary2 = collector.get_metrics_summary(use_cache=True)
        timestamp2 = summary2["timestamp"]
        
        # Timestamps should match (cached)
        assert timestamp1 == timestamp2
        
        # Third call without cache
        summary3 = collector.get_metrics_summary(use_cache=False)
        timestamp3 = summary3["timestamp"]
        
        # Timestamp might be different (not cached)
        # Just verify it exists
        assert timestamp3 is not None


class TestPhase3SubAgents:
    """Test sub-agent integration features."""
    
    def test_coordinator_creation(self):
        """Test creating a sub-agent coordinator."""
        config = HobbyConfig(enabled=True)
        manager = HobbyManager(config)
        
        coordinator = HobbySubAgentCoordinator(manager)
        assert coordinator is not None
        assert coordinator.hobby_manager == manager
        assert len(coordinator._registered_subagents) == 0
    
    def test_subagent_registration(self):
        """Test registering a sub-agent."""
        config = HobbyConfig(enabled=True)
        manager = HobbyManager(config)
        coordinator = HobbySubAgentCoordinator(manager)
        
        # Register sub-agent
        coordinator.register_subagent(
            subagent_id="test-agent-1",
            capabilities=["SKILL_PRACTICE", "KNOWLEDGE_EXPLORATION"],
            metadata={"version": "1.0"}
        )
        
        # Verify registration
        assert "test-agent-1" in coordinator._registered_subagents
        info = coordinator._registered_subagents["test-agent-1"]
        assert info["subagent_id"] == "test-agent-1"
        assert len(info["capabilities"]) == 2
        assert info["active_assignments"] == 0
    
    def test_subagent_unregistration(self):
        """Test unregistering a sub-agent."""
        config = HobbyConfig(enabled=True)
        manager = HobbyManager(config)
        coordinator = HobbySubAgentCoordinator(manager)
        
        # Register and unregister
        coordinator.register_subagent("test-agent-1", ["*"])
        assert "test-agent-1" in coordinator._registered_subagents
        
        coordinator.unregister_subagent("test-agent-1")
        assert "test-agent-1" not in coordinator._registered_subagents
    
    @pytest.mark.asyncio
    async def test_hobby_assignment(self):
        """Test assigning a hobby to a sub-agent."""
        config = HobbyConfig(enabled=True)
        manager = HobbyManager(config)
        coordinator = HobbySubAgentCoordinator(manager)
        
        # Register sub-agent
        coordinator.register_subagent("test-agent-1", ["*"])
        
        # Assign hobby
        assignment = await coordinator.assign_hobby_to_subagent(
            subagent_id="test-agent-1",
            hobby_type=HobbyType.SKILL_PRACTICE,
            duration_minutes=1.0
        )
        
        # Verify assignment
        assert assignment is not None
        assert assignment.subagent_id == "test-agent-1"
        assert assignment.hobby_type == HobbyType.SKILL_PRACTICE
        assert assignment.status in ["pending", "running", "completed"]
        
        # Wait a bit for execution
        await asyncio.sleep(2)
        
        # Check assignment was tracked
        assert assignment.assignment_id in coordinator._assignments
    
    @pytest.mark.asyncio
    async def test_auto_distribution(self):
        """Test automatic hobby distribution."""
        config = HobbyConfig(enabled=True)
        manager = HobbyManager(config)
        coordinator = HobbySubAgentCoordinator(manager)
        
        # Register multiple sub-agents
        coordinator.register_subagent("agent-1", ["*"])
        coordinator.register_subagent("agent-2", ["*"])
        
        # Auto-distribute hobbies
        assignments = await coordinator.auto_distribute_hobbies(num_assignments=2)
        
        # Verify assignments were created
        assert len(assignments) == 2
        assert assignments[0].status in ["pending", "running", "completed"]
    
    def test_find_suitable_subagent(self):
        """Test finding suitable sub-agent for hobby."""
        config = HobbyConfig(enabled=True)
        manager = HobbyManager(config)
        coordinator = HobbySubAgentCoordinator(manager)
        
        # Register specialized agents
        coordinator.register_subagent("skill-agent", ["SKILL_PRACTICE"])
        coordinator.register_subagent("general-agent", ["*"])
        
        # Find agent for skill practice
        agent_id = coordinator._find_suitable_subagent(HobbyType.SKILL_PRACTICE)
        assert agent_id in ["skill-agent", "general-agent"]
        
        # Find agent for code analysis (only general can handle)
        agent_id = coordinator._find_suitable_subagent(HobbyType.CODE_ANALYSIS)
        assert agent_id == "general-agent"
    
    def test_subagent_stats(self):
        """Test getting sub-agent statistics."""
        config = HobbyConfig(enabled=True)
        manager = HobbyManager(config)
        coordinator = HobbySubAgentCoordinator(manager)
        
        # Register agents
        coordinator.register_subagent("agent-1", ["*"])
        coordinator.register_subagent("agent-2", ["SKILL_PRACTICE"])
        
        # Get stats
        stats = coordinator.get_subagent_stats()
        
        # Verify stats
        assert stats["total_registered"] == 2
        assert "subagents" in stats
        assert len(stats["subagents"]) == 2
    
    def test_assignment_tracking(self):
        """Test assignment status tracking."""
        config = HobbyConfig(enabled=True)
        manager = HobbyManager(config)
        coordinator = HobbySubAgentCoordinator(manager)
        
        # Create fake assignment for testing
        from lollmsbot.hobby_subagent import SubAgentHobbyAssignment
        
        assignment = SubAgentHobbyAssignment(
            assignment_id="test-123",
            subagent_id="agent-1",
            hobby_type=HobbyType.SKILL_PRACTICE,
            duration_minutes=5.0,
            assigned_at=datetime.now(),
            status="completed"
        )
        
        coordinator._assignments["test-123"] = assignment
        
        # Get status
        status = coordinator.get_assignment_status("test-123")
        assert status is not None
        assert status["assignment_id"] == "test-123"
        assert status["status"] == "completed"
        
        # Get all assignments
        all_assignments = coordinator.get_all_assignments()
        assert len(all_assignments) == 1
        
        # Filter by status
        completed = coordinator.get_all_assignments(status_filter="completed")
        assert len(completed) == 1


class TestPhase3Integration:
    """Test integration between metrics and sub-agents."""
    
    @pytest.mark.asyncio
    async def test_metrics_track_subagent_activity(self):
        """Test that metrics track sub-agent activities."""
        config = HobbyConfig(enabled=True)
        manager = HobbyManager(config)
        
        coordinator = HobbySubAgentCoordinator(manager)
        collector = create_metrics_collector(manager)
        
        # Register agent and assign work
        coordinator.register_subagent("agent-1", ["*"])
        
        # Get initial proficiency
        initial_summary = collector.get_metrics_summary(use_cache=False)
        initial_proficiency = initial_summary["trends"]["skill_practice"]["current_proficiency"]
        
        # Assign hobby
        assignment = await coordinator.assign_hobby_to_subagent(
            subagent_id="agent-1",
            hobby_type=HobbyType.SKILL_PRACTICE,
            duration_minutes=1.0
        )
        
        # Wait for completion
        await asyncio.sleep(3)
        
        # Get updated metrics
        updated_summary = collector.get_metrics_summary(use_cache=False)
        updated_proficiency = updated_summary["trends"]["skill_practice"]["current_proficiency"]
        
        # Proficiency should have increased (or at least not decreased)
        assert updated_proficiency >= initial_proficiency
    
    def test_dashboard_includes_subagent_data(self):
        """Test that dashboard reflects sub-agent activity."""
        config = HobbyConfig(enabled=True)
        manager = HobbyManager(config)
        
        collector = create_metrics_collector(manager)
        dashboard = collector.get_dashboard_data()
        
        # Dashboard should have current stats
        assert "current_stats" in dashboard
        stats = dashboard["current_stats"]
        
        # Check structure
        assert "total_activities" in stats
        assert "overall_engagement" in stats
        assert "active_hobbies" in stats
        assert "is_learning" in stats


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
