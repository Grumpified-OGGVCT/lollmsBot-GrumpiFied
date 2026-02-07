"""
FastAPI router for the LollmsBot Web UI.

Provides API routes for the web interface, including health checks,
settings management, conversation endpoints, and security status.
"""

from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import JSONResponse
from datetime import datetime, timedelta

ui_router = APIRouter(
    prefix="/ui-api",
    tags=["ui"],
    responses={404: {"description": "Not found"}},
)


@ui_router.get("/health")
async def ui_health() -> dict:
    """Health check endpoint for the UI."""
    return {
        "status": "ok",
        "service": "lollmsbot-ui",
        "version": "0.1.0",
    }


@ui_router.get("/config")
async def ui_config(request: Request) -> dict:
    """Get current UI configuration (safe values only)."""
    # Return non-sensitive configuration for the frontend
    return {
        "max_history": 10,
        "features": {
            "tools": True,
            "settings": True,
            "streaming": True,
            "security": True,
        },
    }


@ui_router.get("/security/status")
async def security_status() -> dict:
    """Get Guardian security status."""
    try:
        from lollmsbot.guardian import get_guardian
        from lollmsbot.security_monitoring import get_security_monitor
        
        guardian = get_guardian()
        monitor = get_security_monitor()
        
        # Get audit report for last 24 hours
        since = datetime.now() - timedelta(hours=24)
        audit = guardian.get_audit_report(since=since)
        
        # Get monitoring stats
        monitoring_stats = monitor.get_monitoring_stats()
        
        # Get adaptive learning stats
        adaptive_stats = guardian.get_adaptive_stats()
        
        return {
            "status": "active",
            "quarantine_active": guardian.is_quarantined,
            "events_24h": audit.get("total_events", 0),
            "events_by_level": audit.get("events_by_level", {}),
            "api_key_protection": True,
            "skill_scanning": True,
            "container_protection": True,
            "monitoring": monitoring_stats,
            "adaptive_learning": adaptive_stats,
            "resource_usage": {
                "event_history_size": len(guardian._event_history),
                "max_events": guardian._max_history,
                "api_keys_tracked": len(guardian.threat_detector._detected_keys),
                "max_keys": guardian._max_api_key_hashes,
            }
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "quarantine_active": False,
            "events_24h": 0,
        }


@ui_router.get("/security/audit")
async def security_audit(limit: int = 50) -> dict:
    """Get recent security audit events."""
    try:
        from lollmsbot.guardian import get_guardian
        
        guardian = get_guardian()
        
        # Get recent events
        events = guardian._event_history[-limit:]
        
        return {
            "events": [e.to_dict() for e in events],
            "total": len(guardian._event_history),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@ui_router.get("/security/skills")
async def security_skills() -> dict:
    """Get skill security scan results."""
    try:
        from lollmsbot.skills import get_awesome_skills_integration
        
        integration = get_awesome_skills_integration()
        
        if not integration or not integration.is_available():
            return {
                "available": False,
                "scanned": [],
            }
        
        scan_results = integration.get_scan_results()
        
        return {
            "available": True,
            "scanned": [
                {
                    "name": name,
                    "is_safe": result.get("is_safe", False),
                    "threats": result.get("threats", []),
                }
                for name, result in scan_results.items()
            ],
            "total": len(scan_results),
        }
    except Exception as e:
        return {
            "available": False,
            "error": str(e),
            "scanned": [],
        }
