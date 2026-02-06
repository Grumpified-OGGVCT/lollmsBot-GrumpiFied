"""
Permission Policy - Mount and Execution Policies for Sandboxed Operations

Defines what directories can be mounted and with what permissions (R/O vs R/W).
Integrates with the Guardian security layer for defense in depth.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Set


class PermissionMode(Enum):
    """Permission modes for directory mounts."""
    READ_ONLY = "ro"
    READ_WRITE = "rw"
    NO_ACCESS = "none"


def _default_denied_paths():
    """Factory function for default denied paths."""
    return {
        Path("/etc"),
        Path("/sys"),
        Path("/proc"),
        Path("/dev"),
        Path("/boot"),
        Path("/root"),
    }


@dataclass
class MountPolicy:
    """Policy for mounting directories in sandbox.
    
    Attributes:
        allowed_paths: Paths that can be mounted
        default_mode: Default permission mode
        path_modes: Specific modes for specific paths
        denied_paths: Paths that can never be mounted
    """
    allowed_paths: Set[Path] = field(default_factory=set)
    default_mode: PermissionMode = PermissionMode.READ_ONLY
    path_modes: Dict[Path, PermissionMode] = field(default_factory=dict)
    denied_paths: Set[Path] = field(default_factory=_default_denied_paths)
    
    def can_mount(self, path: Path) -> bool:
        """Check if a path can be mounted.
        
        Args:
            path: Path to check
            
        Returns:
            True if mountable, False otherwise
        """
        path = path.resolve()
        
        # Check denied paths
        for denied in self.denied_paths:
            try:
                path.relative_to(denied)
                return False
            except ValueError:
                continue
        
        # Check allowed paths
        if not self.allowed_paths:
            return True  # No restrictions
        
        for allowed in self.allowed_paths:
            try:
                path.relative_to(allowed)
                return True
            except ValueError:
                continue
        
        return False
    
    def get_mode(self, path: Path) -> PermissionMode:
        """Get permission mode for a path.
        
        Args:
            path: Path to check
            
        Returns:
            PermissionMode for this path
        """
        path = path.resolve()
        
        # Check for explicit mode
        if path in self.path_modes:
            return self.path_modes[path]
        
        # Check parent directories
        for parent in path.parents:
            if parent in self.path_modes:
                return self.path_modes[parent]
        
        return self.default_mode
    
    def grant_write_access(self, path: Path, session_id: Optional[str] = None):
        """Grant temporary write access to a path.
        
        This is called when a user explicitly grants destructive_action permission
        for a specific session.
        
        Args:
            path: Path to grant write access to
            session_id: Optional session ID for tracking
        """
        path = path.resolve()
        if self.can_mount(path):
            self.path_modes[path] = PermissionMode.READ_WRITE
    
    def revoke_write_access(self, path: Path):
        """Revoke write access from a path.
        
        Args:
            path: Path to revoke write access from
        """
        path = path.resolve()
        if path in self.path_modes:
            self.path_modes[path] = PermissionMode.READ_ONLY
    
    @classmethod
    def default_policy(cls) -> MountPolicy:
        """Create a default restrictive policy.
        
        Returns:
            MountPolicy with safe defaults
        """
        return cls(
            allowed_paths={
                Path.home() / ".lollmsbot" / "workspace",
                Path("/tmp") / "lollmsbot",
            },
            default_mode=PermissionMode.READ_ONLY,
        )
    
    @classmethod
    def permissive_policy(cls) -> MountPolicy:
        """Create a more permissive policy (use with caution).
        
        Returns:
            MountPolicy that allows more paths
        """
        return cls(
            allowed_paths={
                Path.home(),
                Path("/tmp"),
            },
            default_mode=PermissionMode.READ_ONLY,
        )
