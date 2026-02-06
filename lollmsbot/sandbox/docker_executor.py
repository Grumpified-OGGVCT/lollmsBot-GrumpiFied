"""
Docker Executor - Sandboxed Command Execution

Implements OpenClaw's secure execution model using ephemeral Docker containers.
Commands are executed in lightweight Alpine Linux containers with controlled
filesystem access and network isolation.

Security Features:
1. Ephemeral containers - spun up for each command, destroyed after
2. Read-only root filesystem
3. Controlled mounts via MountPolicy
4. Network isolation (optional)
5. Resource limits (CPU, memory, timeout)
6. Guardian pre-screening of commands

This prevents scenarios like:
- `rm -rf /` affecting the host system
- Privilege escalation attacks
- Data exfiltration through network
- Resource exhaustion attacks
"""

from __future__ import annotations

import asyncio
import logging
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from lollmsbot.sandbox.policy import MountPolicy, PermissionMode

logger = logging.getLogger("lollmsbot.sandbox.docker_executor")

# Check if docker is available
try:
    import docker
    from docker.errors import DockerException, ImageNotFound, ContainerError
    DOCKER_AVAILABLE = True
except ImportError:
    DOCKER_AVAILABLE = False
    docker = None
    DockerException = Exception
    ImageNotFound = Exception
    ContainerError = Exception
    logger.warning("Docker not available - sandbox execution will be disabled")


@dataclass
class SandboxConfig:
    """Configuration for sandbox execution.
    
    Attributes:
        image: Docker image to use (default: alpine:latest)
        network_mode: Network mode ('none', 'bridge', 'host')
        memory_limit: Memory limit (e.g., '256m', '1g')
        cpu_quota: CPU quota (100000 = 1 core)
        timeout: Execution timeout in seconds
        auto_remove: Whether to auto-remove containers
        mount_policy: Policy for directory mounting
        read_only_root: Whether root filesystem is read-only
    """
    image: str = "alpine:latest"
    network_mode: str = "none"  # Isolated by default
    memory_limit: str = "256m"
    cpu_quota: int = 50000  # 0.5 CPU cores
    timeout: float = 30.0
    auto_remove: bool = True
    mount_policy: MountPolicy = field(default_factory=MountPolicy.default_policy)
    read_only_root: bool = True


@dataclass
class SandboxResult:
    """Result from sandbox execution.
    
    Attributes:
        success: Whether execution succeeded
        stdout: Standard output
        stderr: Standard error
        exit_code: Container exit code
        execution_time: Time taken in seconds
        container_id: Container ID (if not auto-removed)
        error: Error message if failed
    """
    success: bool
    stdout: str
    stderr: str
    exit_code: int
    execution_time: float
    container_id: Optional[str] = None
    error: Optional[str] = None


class DockerExecutor:
    """Executes commands in isolated Docker containers.
    
    Usage:
        config = SandboxConfig()
        executor = DockerExecutor(config)
        
        # Execute a command
        result = await executor.execute("ls -la /workspace")
        
        # Execute with specific mounts
        result = await executor.execute_with_mounts(
            command="python script.py",
            mounts={Path("/home/user/workspace"): Path("/workspace")}
        )
    """
    
    def __init__(self, config: Optional[SandboxConfig] = None):
        """Initialize Docker executor.
        
        Args:
            config: Sandbox configuration
        """
        if not DOCKER_AVAILABLE:
            raise RuntimeError("Docker is not available. Install with: pip install docker")
        
        self.config = config or SandboxConfig()
        self.client: Optional[docker.DockerClient] = None
        
        try:
            self.client = docker.from_env()
            logger.info(f"Docker client initialized: {self.client.version()}")
        except DockerException as e:
            logger.error(f"Failed to initialize Docker client: {e}")
            raise RuntimeError(f"Docker daemon not accessible: {e}")
    
    async def execute(
        self,
        command: str,
        working_dir: str = "/workspace",
        env_vars: Optional[Dict[str, str]] = None,
    ) -> SandboxResult:
        """Execute a command in a sandbox container.
        
        Args:
            command: Command to execute
            working_dir: Working directory in container
            env_vars: Environment variables
            
        Returns:
            SandboxResult with execution details
        """
        return await self.execute_with_mounts(
            command=command,
            mounts={},
            working_dir=working_dir,
            env_vars=env_vars,
        )
    
    async def execute_with_mounts(
        self,
        command: str,
        mounts: Dict[Path, Path],
        working_dir: str = "/workspace",
        env_vars: Optional[Dict[str, str]] = None,
    ) -> SandboxResult:
        """Execute a command with specific directory mounts.
        
        Args:
            command: Command to execute
            mounts: Dict mapping host paths to container paths
            working_dir: Working directory in container
            env_vars: Environment variables
            
        Returns:
            SandboxResult with execution details
        """
        import time
        start_time = time.time()
        
        # Ensure image is available
        await self._ensure_image()
        
        # Prepare mounts with permission checking
        volume_mounts = {}
        for host_path, container_path in mounts.items():
            if not self.config.mount_policy.can_mount(host_path):
                return SandboxResult(
                    success=False,
                    stdout="",
                    stderr=f"Mount denied by policy: {host_path}",
                    exit_code=-1,
                    execution_time=0.0,
                    error=f"Path {host_path} is not allowed to be mounted"
                )
            
            mode = self.config.mount_policy.get_mode(host_path)
            if mode == PermissionMode.NO_ACCESS:
                continue
            
            # Create host path if it doesn't exist
            host_path.mkdir(parents=True, exist_ok=True)
            
            volume_mounts[str(host_path)] = {
                'bind': str(container_path),
                'mode': mode.value
            }
        
        # Generate unique container name
        container_name = f"lollmsbot-sandbox-{uuid.uuid4().hex[:8]}"
        
        try:
            # Run container
            container = self.client.containers.run(
                image=self.config.image,
                command=command,
                name=container_name,
                working_dir=working_dir,
                environment=env_vars or {},
                volumes=volume_mounts,
                network_mode=self.config.network_mode,
                mem_limit=self.config.memory_limit,
                cpu_quota=self.config.cpu_quota,
                read_only=self.config.read_only_root,
                detach=True,
                remove=False,  # Manual removal for error handling
            )
            
            # Wait for completion with timeout
            try:
                exit_code = container.wait(timeout=self.config.timeout)
                
                # Get output
                stdout = container.logs(stdout=True, stderr=False).decode('utf-8', errors='replace')
                stderr = container.logs(stdout=False, stderr=True).decode('utf-8', errors='replace')
                
                execution_time = time.time() - start_time
                
                # Clean up
                if self.config.auto_remove:
                    container.remove()
                    container_id = None
                else:
                    container_id = container.id
                
                return SandboxResult(
                    success=(exit_code['StatusCode'] == 0),
                    stdout=stdout,
                    stderr=stderr,
                    exit_code=exit_code['StatusCode'],
                    execution_time=execution_time,
                    container_id=container_id,
                )
                
            except Exception as e:
                # Timeout or other error - kill container
                try:
                    container.kill()
                    container.remove()
                except Exception:
                    pass
                
                return SandboxResult(
                    success=False,
                    stdout="",
                    stderr=f"Execution timeout or error: {str(e)}",
                    exit_code=-1,
                    execution_time=time.time() - start_time,
                    error=str(e)
                )
                
        except ContainerError as e:
            return SandboxResult(
                success=False,
                stdout=e.stdout.decode('utf-8', errors='replace') if e.stdout else "",
                stderr=e.stderr.decode('utf-8', errors='replace') if e.stderr else str(e),
                exit_code=e.exit_status,
                execution_time=time.time() - start_time,
                error=str(e)
            )
        except Exception as e:
            logger.error(f"Sandbox execution error: {e}", exc_info=True)
            return SandboxResult(
                success=False,
                stdout="",
                stderr=str(e),
                exit_code=-1,
                execution_time=time.time() - start_time,
                error=str(e)
            )
    
    async def _ensure_image(self):
        """Ensure the sandbox image is available, pull if necessary."""
        try:
            self.client.images.get(self.config.image)
            logger.debug(f"Image {self.config.image} already available")
        except ImageNotFound:
            logger.info(f"Pulling image {self.config.image}...")
            try:
                self.client.images.pull(self.config.image)
                logger.info(f"Successfully pulled {self.config.image}")
            except Exception as e:
                logger.error(f"Failed to pull image {self.config.image}: {e}")
                raise RuntimeError(f"Cannot pull required image: {e}")
    
    def cleanup_old_containers(self, max_age_hours: int = 24):
        """Clean up old sandbox containers that weren't auto-removed.
        
        Args:
            max_age_hours: Remove containers older than this many hours
        """
        try:
            containers = self.client.containers.list(
                all=True,
                filters={'name': 'lollmsbot-sandbox-'}
            )
            
            import datetime
            now = datetime.datetime.now(datetime.timezone.utc)
            removed = 0
            
            for container in containers:
                created = datetime.datetime.fromisoformat(
                    container.attrs['Created'].replace('Z', '+00:00')
                )
                age_hours = (now - created).total_seconds() / 3600
                
                if age_hours > max_age_hours:
                    container.remove(force=True)
                    removed += 1
            
            if removed > 0:
                logger.info(f"Cleaned up {removed} old sandbox containers")
                
        except Exception as e:
            logger.error(f"Failed to cleanup old containers: {e}")


# Global instance
_executor: Optional[DockerExecutor] = None


def get_docker_executor(config: Optional[SandboxConfig] = None) -> Optional[DockerExecutor]:
    """Get or create the global Docker executor instance.
    
    Returns:
        DockerExecutor if Docker is available, None otherwise
    """
    global _executor
    if not DOCKER_AVAILABLE:
        return None
    
    if _executor is None:
        try:
            _executor = DockerExecutor(config)
        except RuntimeError as e:
            logger.warning(f"Docker executor unavailable: {e}")
            return None
    
    return _executor


def is_docker_available() -> bool:
    """Check if Docker is available for sandbox execution.
    
    Returns:
        True if Docker is available and accessible
    """
    if not DOCKER_AVAILABLE:
        return False
    
    try:
        executor = get_docker_executor()
        return executor is not None
    except Exception:
        return False
