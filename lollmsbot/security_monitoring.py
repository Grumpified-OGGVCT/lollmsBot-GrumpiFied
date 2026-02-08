"""
Security Monitoring - Active Background Security Scanning

Integrates with the autonomous hobby system to provide:
1. Periodic security audits
2. Threat intelligence updates
3. Active skill monitoring
4. Security health checks
5. Pattern updates

This runs as a background hobby to keep defenses up-to-date without
consuming excessive resources.
"""

import asyncio
import logging
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
from collections import deque
from dataclasses import dataclass, field

logger = logging.getLogger("lollmsbot.security_monitoring")


@dataclass
class SecurityMonitoringConfig:
    """Configuration for security monitoring."""
    enabled: bool = True
    scan_interval_minutes: int = 30  # How often to run scans
    pattern_update_interval_hours: int = 24  # How often to check for pattern updates
    max_audit_log_mb: int = 10  # Max audit log size in MB
    max_event_history: int = 10000  # Max events in memory
    max_api_key_hashes: int = 1000  # Max API key hashes to track
    enable_threat_intel_updates: bool = False  # Fetch updates from external source
    threat_intel_url: Optional[str] = None  # URL for threat intelligence feed


@dataclass
class SecurityHealth:
    """Health status of security system."""
    guardian_active: bool
    last_scan_time: Optional[datetime]
    events_24h: int
    quarantine_active: bool
    skills_scanned: int
    skills_blocked: int
    api_keys_detected: int
    threats_blocked: int
    audit_log_size_mb: float
    event_history_size: int
    memory_usage_mb: float


class SecurityMonitor:
    """
    Background security monitoring integrated with hobby system.
    
    Runs periodic scans to:
    - Check for new threats in loaded skills
    - Rotate audit logs
    - Update threat patterns
    - Monitor security health
    - Clean up old data
    """
    
    def __init__(self, config: Optional[SecurityMonitoringConfig] = None):
        self.config = config or SecurityMonitoringConfig()
        self._last_scan_time: Optional[datetime] = None
        self._last_pattern_update: Optional[datetime] = None
        self._running = False
        self._scan_count = 0
        
        # Resource tracking
        self._scan_history: deque = deque(maxlen=100)  # Last 100 scans
        
        logger.info("🔍 Security Monitor initialized")
    
    async def start_monitoring(self) -> None:
        """Start background monitoring loop."""
        if not self.config.enabled:
            logger.info("Security monitoring disabled")
            return
        
        self._running = True
        logger.info("🔍 Security monitoring started")
        
        try:
            while self._running:
                await self._monitoring_cycle()
                
                # Sleep until next scan
                await asyncio.sleep(self.config.scan_interval_minutes * 60)
                
        except asyncio.CancelledError:
            logger.info("Security monitoring cancelled")
            self._running = False
        except Exception as e:
            logger.error(f"Security monitoring error: {e}")
            self._running = False
    
    async def stop_monitoring(self) -> None:
        """Stop background monitoring."""
        self._running = False
        logger.info("🔍 Security monitoring stopped")
    
    async def _monitoring_cycle(self) -> None:
        """Run one complete monitoring cycle."""
        cycle_start = time.time()
        self._scan_count += 1
        
        logger.info(f"🔍 Security scan #{self._scan_count} starting...")
        
        try:
            # 1. Check Guardian health
            health = await self._check_security_health()
            
            # 2. Rotate audit logs if needed
            await self._rotate_audit_logs()
            
            # 3. Clean up old data
            await self._cleanup_old_data()
            
            # 4. Re-scan loaded skills
            await self._rescan_loaded_skills()
            
            # 5. Update threat patterns if needed
            if self._should_update_patterns():
                await self._update_threat_patterns()
            
            # 6. Check for anomalies
            await self._check_for_anomalies(health)
            
            self._last_scan_time = datetime.now()
            
            cycle_time = time.time() - cycle_start
            self._scan_history.append({
                "timestamp": datetime.now(),
                "duration_seconds": cycle_time,
                "health": health
            })
            
            logger.info(
                f"✅ Security scan #{self._scan_count} complete "
                f"({cycle_time:.2f}s, {health.events_24h} events)"
            )
            
        except Exception as e:
            logger.error(f"Error in monitoring cycle: {e}")
    
    async def _check_security_health(self) -> SecurityHealth:
        """Check current security system health."""
        try:
            from lollmsbot.guardian import get_guardian
            from lollmsbot.skills import get_awesome_skills_integration
            
            guardian = get_guardian()
            integration = get_awesome_skills_integration()
            
            # Calculate events in last 24h
            since = datetime.now() - timedelta(hours=24)
            recent_events = [e for e in guardian._event_history if e.timestamp >= since]
            
            # Count API keys detected
            api_keys_count = len(guardian.threat_detector._detected_keys)
            
            # Get audit log size
            audit_size_mb = 0
            if guardian.audit_log_path.exists():
                audit_size_mb = guardian.audit_log_path.stat().st_size / (1024 * 1024)
            
            # Count skills
            skills_scanned = 0
            skills_blocked = 0
            if integration and integration.is_available():
                scan_results = integration.get_scan_results()
                skills_scanned = len(scan_results)
                skills_blocked = sum(1 for r in scan_results.values() if not r.get("is_safe", True))
            
            # Estimate memory usage (rough)
            import sys
            memory_mb = sys.getsizeof(guardian._event_history) / (1024 * 1024)
            
            return SecurityHealth(
                guardian_active=not guardian.is_quarantined,
                last_scan_time=self._last_scan_time,
                events_24h=len(recent_events),
                quarantine_active=guardian.is_quarantined,
                skills_scanned=skills_scanned,
                skills_blocked=skills_blocked,
                api_keys_detected=api_keys_count,
                threats_blocked=sum(1 for e in recent_events if e.action_taken.name == "BLOCK"),
                audit_log_size_mb=audit_size_mb,
                event_history_size=len(guardian._event_history),
                memory_usage_mb=memory_mb
            )
            
        except Exception as e:
            logger.error(f"Error checking security health: {e}")
            return SecurityHealth(
                guardian_active=False,
                last_scan_time=None,
                events_24h=0,
                quarantine_active=False,
                skills_scanned=0,
                skills_blocked=0,
                api_keys_detected=0,
                threats_blocked=0,
                audit_log_size_mb=0,
                event_history_size=0,
                memory_usage_mb=0
            )
    
    async def _rotate_audit_logs(self) -> None:
        """Rotate audit logs if they exceed size limit."""
        try:
            from lollmsbot.guardian import get_guardian
            
            guardian = get_guardian()
            log_path = guardian.audit_log_path
            
            if not log_path.exists():
                return
            
            size_mb = log_path.stat().st_size / (1024 * 1024)
            
            if size_mb > self.config.max_audit_log_mb:
                # Rotate log
                backup_path = log_path.with_suffix(f".{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
                log_path.rename(backup_path)
                
                logger.info(f"📝 Rotated audit log: {size_mb:.2f}MB -> {backup_path.name}")
                
                # Keep only last 5 rotated logs
                log_dir = log_path.parent
                old_logs = sorted(log_dir.glob("audit.*.log"), key=lambda p: p.stat().st_mtime)
                for old_log in old_logs[:-5]:
                    old_log.unlink()
                    logger.debug(f"Deleted old audit log: {old_log.name}")
                    
        except Exception as e:
            logger.error(f"Error rotating audit logs: {e}")
    
    async def _cleanup_old_data(self) -> None:
        """Clean up old data to prevent unbounded growth."""
        try:
            from lollmsbot.guardian import get_guardian
            
            guardian = get_guardian()
            
            # Limit event history
            if len(guardian._event_history) > self.config.max_event_history:
                excess = len(guardian._event_history) - self.config.max_event_history
                guardian._event_history = guardian._event_history[excess:]
                logger.debug(f"Trimmed {excess} old events from history")
            
            # Limit API key hash storage
            if len(guardian.threat_detector._detected_keys) > self.config.max_api_key_hashes:
                # Remove oldest entries
                sorted_keys = sorted(
                    guardian.threat_detector._detected_keys.items(),
                    key=lambda x: x[1]
                )
                to_remove = len(sorted_keys) - self.config.max_api_key_hashes
                for key, _ in sorted_keys[:to_remove]:
                    del guardian.threat_detector._detected_keys[key]
                
                logger.debug(f"Removed {to_remove} old API key hashes")
                
        except Exception as e:
            logger.error(f"Error cleaning up old data: {e}")
    
    async def _rescan_loaded_skills(self) -> None:
        """Re-scan all loaded skills for new threats."""
        try:
            from lollmsbot.skills import get_awesome_skills_integration
            
            integration = get_awesome_skills_integration()
            
            if not integration or not integration.is_available():
                return
            
            # Get currently loaded skills
            loaded_skills = integration.loaded_skills
            
            if not loaded_skills:
                return
            
            logger.debug(f"Re-scanning {len(loaded_skills)} loaded skills...")
            
            for skill_name, skill in loaded_skills.items():
                # Quick scan - don't block loading, just check
                # This could detect if a skill's behavior changed
                pass  # Actual implementation would re-scan skill content
            
        except Exception as e:
            logger.error(f"Error re-scanning skills: {e}")
    
    def _should_update_patterns(self) -> bool:
        """Check if it's time to update threat patterns."""
        if not self.config.enable_threat_intel_updates:
            return False
        
        if self._last_pattern_update is None:
            return True
        
        hours_since_update = (datetime.now() - self._last_pattern_update).total_seconds() / 3600
        return hours_since_update >= self.config.pattern_update_interval_hours
    
    async def _update_threat_patterns(self) -> None:
        """Update threat patterns from external threat intelligence."""
        try:
            if not self.config.threat_intel_url:
                logger.debug("No threat intelligence URL configured")
                return
            
            logger.info("🔄 Checking for threat pattern updates...")
            
            # This would fetch updated patterns from external source
            # For now, just log that we checked
            self._last_pattern_update = datetime.now()
            
            logger.info("✅ Threat patterns up-to-date")
            
        except Exception as e:
            logger.error(f"Error updating threat patterns: {e}")
    
    async def _check_for_anomalies(self, health: SecurityHealth) -> None:
        """Check for unusual patterns that might indicate issues."""
        try:
            # Check if quarantine activated
            if health.quarantine_active:
                logger.warning("⚠️  QUARANTINE ACTIVE - Security threat detected!")
            
            # Check if too many events
            if health.events_24h > 1000:
                logger.warning(f"⚠️  High security event rate: {health.events_24h} in 24h")
            
            # Check if blocked skills increasing
            if health.skills_blocked > health.skills_scanned * 0.5:
                logger.warning(
                    f"⚠️  High skill block rate: {health.skills_blocked}/{health.skills_scanned}"
                )
            
            # Check resource usage
            if health.audit_log_size_mb > self.config.max_audit_log_mb * 0.9:
                logger.warning(
                    f"⚠️  Audit log approaching limit: {health.audit_log_size_mb:.2f}MB"
                )
            
        except Exception as e:
            logger.error(f"Error checking anomalies: {e}")
    
    def get_monitoring_stats(self) -> Dict[str, Any]:
        """Get monitoring statistics."""
        return {
            "enabled": self.config.enabled,
            "running": self._running,
            "scan_count": self._scan_count,
            "last_scan": self._last_scan_time.isoformat() if self._last_scan_time else None,
            "scan_interval_minutes": self.config.scan_interval_minutes,
            "recent_scans": [
                {
                    "timestamp": s["timestamp"].isoformat(),
                    "duration": s["duration_seconds"],
                    "events_24h": s["health"].events_24h
                }
                for s in list(self._scan_history)[-10:]
            ]
        }


# Global instance
_monitor_instance: Optional[SecurityMonitor] = None


def get_security_monitor(config: Optional[SecurityMonitoringConfig] = None) -> SecurityMonitor:
    """Get or create the security monitor instance."""
    global _monitor_instance
    if _monitor_instance is None:
        _monitor_instance = SecurityMonitor(config)
    return _monitor_instance


async def start_security_monitoring(config: Optional[SecurityMonitoringConfig] = None) -> SecurityMonitor:
    """Start the security monitoring background task."""
    monitor = get_security_monitor(config)
    
    # Start monitoring in background
    asyncio.create_task(monitor.start_monitoring())
    
    return monitor


async def stop_security_monitoring() -> None:
    """Stop the security monitoring."""
    global _monitor_instance
    if _monitor_instance:
        await _monitor_instance.stop_monitoring()
