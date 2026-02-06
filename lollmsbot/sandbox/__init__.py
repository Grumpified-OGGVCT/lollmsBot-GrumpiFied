"""
Sandbox Module - Secure Execution Environment

Implements OpenClaw's "Defense in Depth" security model with Docker-based
sandboxing for tool execution. This prevents malicious commands from
affecting the host system.

Key Features:
- Ephemeral Alpine containers for tool execution
- Read-only and read-write mount policies
- Guardian pre-execution screening
- Automatic cleanup after execution
- Network isolation options
"""

from lollmsbot.sandbox.docker_executor import DockerExecutor, SandboxConfig
from lollmsbot.sandbox.policy import MountPolicy, PermissionMode

__all__ = [
    "DockerExecutor",
    "SandboxConfig",
    "MountPolicy",
    "PermissionMode",
]
