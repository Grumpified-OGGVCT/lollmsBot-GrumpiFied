"""
Hobby Metrics - Prometheus metrics exporter for autonomous learning system

This module exports metrics about the autonomous hobby system for monitoring
and visualization in Prometheus/Grafana dashboards.
"""

from typing import Dict, Any, List
from datetime import datetime, timedelta
from collections import defaultdict
import logging

from lollmsbot.autonomous_hobby import HobbyType, HobbyManager

logger = logging.getLogger(__name__)


class HobbyMetricsCollector:
    """Collects and exports metrics about hobby learning activities."""
    
    def __init__(self, hobby_manager: HobbyManager):
        """Initialize metrics collector.
        
        Args:
            hobby_manager: The HobbyManager instance to collect metrics from
        """
        self.hobby_manager = hobby_manager
        self._metrics_cache = {}
        self._cache_timestamp = None
        self._cache_ttl_seconds = 10  # Cache metrics for 10 seconds
    
    def get_prometheus_metrics(self) -> str:
        """Export metrics in Prometheus text format.
        
        Returns:
            Prometheus-formatted metrics string
        """
        lines = []
        
        # System-level metrics
        lines.append("# HELP hobby_system_enabled Whether the hobby system is enabled")
        lines.append("# TYPE hobby_system_enabled gauge")
        lines.append(f"hobby_system_enabled {int(self.hobby_manager.config.enabled)}")
        
        lines.append("# HELP hobby_system_running Whether the hobby system is currently running")
        lines.append("# TYPE hobby_system_running gauge")
        lines.append(f"hobby_system_running {int(self.hobby_manager._running)}")
        
        lines.append("# HELP hobby_system_is_idle Whether the system is currently idle")
        lines.append("# TYPE hobby_system_is_idle gauge")
        lines.append(f"hobby_system_is_idle {int(self.hobby_manager.is_idle())}")
        
        # Activity metrics
        lines.append("# HELP hobby_activities_total Total number of hobby activities completed")
        lines.append("# TYPE hobby_activities_total counter")
        total_activities = len(self.hobby_manager._activities)
        lines.append(f"hobby_activities_total {total_activities}")
        
        # Per-hobby-type metrics
        lines.append("# HELP hobby_proficiency Current proficiency level per hobby type (0-1)")
        lines.append("# TYPE hobby_proficiency gauge")
        
        lines.append("# HELP hobby_time_invested_minutes Total time invested per hobby type in minutes")
        lines.append("# TYPE hobby_time_invested_minutes counter")
        
        lines.append("# HELP hobby_activities_completed Total activities completed per hobby type")
        lines.append("# TYPE hobby_activities_completed counter")
        
        lines.append("# HELP hobby_success_rate Success rate per hobby type (0-1)")
        lines.append("# TYPE hobby_success_rate gauge")
        
        lines.append("# HELP hobby_insights_total Total insights gained per hobby type")
        lines.append("# TYPE hobby_insights_total counter")
        
        for hobby_type, progress in self.hobby_manager._progress.items():
            hobby_name = hobby_type.name.lower()
            
            lines.append(f'hobby_proficiency{{type="{hobby_name}"}} {progress.current_proficiency}')
            lines.append(f'hobby_time_invested_minutes{{type="{hobby_name}"}} {progress.total_time_minutes}')
            lines.append(f'hobby_activities_completed{{type="{hobby_name}"}} {progress.activities_completed}')
            lines.append(f'hobby_success_rate{{type="{hobby_name}"}} {progress.success_rate}')
            lines.append(f'hobby_insights_total{{type="{hobby_name}"}} {progress.insights_total}')
        
        # Current activity
        lines.append("# HELP hobby_current_activity_active Whether there is a current activity running")
        lines.append("# TYPE hobby_current_activity_active gauge")
        has_current = int(self.hobby_manager._current_activity is not None)
        lines.append(f"hobby_current_activity_active {has_current}")
        
        if self.hobby_manager._current_activity:
            current = self.hobby_manager._current_activity
            duration = (datetime.now() - current.started_at).total_seconds()
            lines.append("# HELP hobby_current_activity_duration_seconds Duration of current activity")
            lines.append("# TYPE hobby_current_activity_duration_seconds gauge")
            lines.append(f'hobby_current_activity_duration_seconds{{type="{current.hobby_type.name.lower()}"}} {duration}')
        
        return "\n".join(lines) + "\n"
    
    def get_metrics_summary(self, use_cache: bool = True) -> Dict[str, Any]:
        """Get a JSON summary of all metrics.
        
        Args:
            use_cache: Whether to use cached metrics
            
        Returns:
            Dictionary with metrics summary
        """
        # Check cache
        now = datetime.now()
        if use_cache and self._cache_timestamp:
            age = (now - self._cache_timestamp).total_seconds()
            if age < self._cache_ttl_seconds:
                return self._metrics_cache
        
        summary = self.hobby_manager.get_progress_summary()
        
        # Add time-series data for recent activities
        recent_activities = self.hobby_manager.get_recent_activities(100)
        
        # Calculate activity frequency over time
        activity_timeline = self._calculate_activity_timeline(recent_activities)
        
        # Calculate proficiency trends
        proficiency_trends = self._calculate_proficiency_trends()
        
        metrics = {
            "system": {
                "enabled": self.hobby_manager.config.enabled,
                "running": self.hobby_manager._running,
                "is_idle": self.hobby_manager.is_idle(),
                "total_activities": len(self.hobby_manager._activities),
                "current_activity": self._get_current_activity_info(),
            },
            "summary": summary,
            "timeline": activity_timeline,
            "trends": proficiency_trends,
            "timestamp": now.isoformat(),
        }
        
        # Update cache
        self._metrics_cache = metrics
        self._cache_timestamp = now
        
        return metrics
    
    def _get_current_activity_info(self) -> Dict[str, Any]:
        """Get information about current activity if any."""
        if not self.hobby_manager._current_activity:
            return None
        
        current = self.hobby_manager._current_activity
        duration = (datetime.now() - current.started_at).total_seconds()
        
        return {
            "activity_id": current.activity_id,
            "hobby_type": current.hobby_type.name,
            "started_at": current.started_at.isoformat(),
            "duration_seconds": duration,
            "description": current.description,
        }
    
    def _calculate_activity_timeline(self, activities: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate activity frequency timeline.
        
        Args:
            activities: List of recent activities
            
        Returns:
            Timeline data with activity counts per hour/day
        """
        # Group by hour for last 24 hours
        hourly_counts = defaultdict(int)
        daily_counts = defaultdict(int)
        
        now = datetime.now()
        
        for activity in activities:
            try:
                started_at = datetime.fromisoformat(activity.get("started_at", ""))
                age_hours = (now - started_at).total_seconds() / 3600
                
                if age_hours <= 24:
                    hour_key = started_at.strftime("%Y-%m-%d %H:00")
                    hourly_counts[hour_key] += 1
                
                day_key = started_at.strftime("%Y-%m-%d")
                daily_counts[day_key] += 1
                
            except (ValueError, TypeError):
                continue
        
        return {
            "hourly": dict(sorted(hourly_counts.items())),
            "daily": dict(sorted(daily_counts.items())),
        }
    
    def _calculate_proficiency_trends(self) -> Dict[str, Any]:
        """Calculate proficiency change trends.
        
        Returns:
            Trend data showing proficiency changes
        """
        trends = {}
        
        for hobby_type, progress in self.hobby_manager._progress.items():
            trends[hobby_type.name.lower()] = {
                "current_proficiency": progress.current_proficiency,
                "improvement_rate": progress.improvement_rate,
                "activities_completed": progress.activities_completed,
                "time_invested_hours": progress.total_time_minutes / 60.0,
                "success_rate": progress.success_rate,
                "average_engagement": progress.average_engagement,
            }
        
        return trends
    
    def get_dashboard_data(self) -> Dict[str, Any]:
        """Get data formatted for dashboard visualization.
        
        Returns:
            Dashboard-ready data structure
        """
        metrics = self.get_metrics_summary(use_cache=True)
        
        # Format data for common chart types
        dashboard = {
            # Radar chart data (proficiency by hobby type)
            "proficiency_radar": {
                "labels": [],
                "values": [],
            },
            # Bar chart data (time invested by hobby type)
            "time_invested_bars": {
                "labels": [],
                "values": [],
            },
            # Line chart data (activity timeline)
            "activity_timeline": {
                "labels": list(metrics["timeline"]["hourly"].keys()),
                "values": list(metrics["timeline"]["hourly"].values()),
            },
            # Pie chart data (activities by type)
            "activities_by_type": {
                "labels": [],
                "values": [],
            },
            # Current stats
            "current_stats": {
                "total_activities": metrics["system"]["total_activities"],
                "overall_engagement": metrics["summary"].get("overall_engagement", 0),
                "active_hobbies": sum(1 for h in metrics["summary"]["hobbies"].values() 
                                     if h["activities_completed"] > 0),
                "is_learning": metrics["system"]["current_activity"] is not None,
            },
        }
        
        # Populate hobby-specific data
        for hobby_name, data in metrics["trends"].items():
            dashboard["proficiency_radar"]["labels"].append(hobby_name)
            dashboard["proficiency_radar"]["values"].append(data["current_proficiency"])
            
            dashboard["time_invested_bars"]["labels"].append(hobby_name)
            dashboard["time_invested_bars"]["values"].append(data["time_invested_hours"])
            
            dashboard["activities_by_type"]["labels"].append(hobby_name)
            dashboard["activities_by_type"]["values"].append(data["activities_completed"])
        
        return dashboard


def create_metrics_collector(hobby_manager: HobbyManager) -> HobbyMetricsCollector:
    """Factory function to create a metrics collector.
    
    Args:
        hobby_manager: The HobbyManager instance
        
    Returns:
        Initialized HobbyMetricsCollector
    """
    return HobbyMetricsCollector(hobby_manager)
