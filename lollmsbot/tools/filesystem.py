"""
Filesystem tool for LollmsBot.

This module provides the FilesystemTool class for safe file and directory
operations within allowed directories. All paths are validated to prevent
directory traversal attacks.
"""

import asyncio
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, List, Set

from lollmsbot.agent import Tool, ToolResult, ToolError


@dataclass
class PathValidationResult:
    """Result of path validation."""
    is_valid: bool
    resolved_path: Path | None
    error_message: str | None


class FilesystemTool(Tool):
    """Tool for safe filesystem operations within allowed directories.
    
    This tool provides read, write, list, and existence check operations
    while enforcing strict path validation to prevent directory traversal
    and unauthorized access outside allowed directories.
    
    Attributes:
        name: Unique identifier for the tool.
        description: Human-readable description of what the tool does.
        parameters: JSON Schema describing expected parameters for each method.
        allowed_directories: Set of allowed base directories for operations.
    """
    
    name: str = "filesystem"
    description: str = (
        "Perform safe filesystem operations including reading files, "
        "writing files, listing directories, and checking file existence. "
        "All operations are restricted to allowed directories."
    )
    
    parameters: dict[str, Any] = {
        "type": "object",
        "properties": {
            "operation": {
                "type": "string",
                "enum": ["read_file", "write_file", "list_dir", "exists"],
                "description": "The filesystem operation to perform",
            },
            "path": {
                "type": "string",
                "description": "Relative path to the file or directory",
            },
            "content": {
                "type": "string",
                "description": "Content to write (required for write_file operation)",
            },
        },
        "required": ["operation", "path"],
    }
    
    def __init__(
        self,
        allowed_directories: List[str] | None = None,
        default_encoding: str = "utf-8",
    ) -> None:
        """Initialize the FilesystemTool.
        
        Args:
            allowed_directories: List of allowed base directories. If None,
                defaults to current working directory.
            default_encoding: Default encoding for file operations.
        """
        self.allowed_directories: Set[Path] = set()
        self.default_encoding: str = default_encoding
        
        if allowed_directories:
            for dir_path in allowed_directories:
                resolved = Path(dir_path).resolve()
                self.allowed_directories.add(resolved)
        else:
            # Default to current working directory
            self.allowed_directories.add(Path.cwd().resolve())
    
    def _validate_path(self, path: str) -> PathValidationResult:
        """Validate that a path is within allowed directories.
        
        Args:
            path: The path to validate (can be relative or absolute).
            
        Returns:
            PathValidationResult indicating if the path is valid and safe.
        """
        try:
            # Resolve to absolute path, handling .. and symlinks
            target_path = Path(path).resolve()
            
            # Check if path is within any allowed directory
            for allowed_dir in self.allowed_directories:
                try:
                    # Check if target_path is within allowed_dir or equals it
                    target_path.relative_to(allowed_dir)
                    return PathValidationResult(
                        is_valid=True,
                        resolved_path=target_path,
                        error_message=None,
                    )
                except ValueError:
                    # target_path is not under allowed_dir, try next
                    continue
            
            # Path is outside all allowed directories
            allowed_strs = [str(d) for d in self.allowed_directories]
            return PathValidationResult(
                is_valid=False,
                resolved_path=None,
                error_message=(
                    f"Path '{path}' is outside allowed directories: "
                    f"{', '.join(allowed_strs)}"
                ),
            )
            
        except (OSError, ValueError) as exc:
            return PathValidationResult(
                is_valid=False,
                resolved_path=None,
                error_message=f"Invalid path '{path}': {str(exc)}",
            )
    
    async def read_file(self, path: str) -> ToolResult:
        """Read contents of a file.
        
        Args:
            path: Path to the file to read.
            
        Returns:
            ToolResult with file content on success, error on failure.
        """
        validation = self._validate_path(path)
        if not validation.is_valid:
            return ToolResult(
                success=False,
                output=None,
                error=validation.error_message,
            )
        
        resolved_path = validation.resolved_path
        
        try:
            if not resolved_path.exists():
                return ToolResult(
                    success=False,
                    output=None,
                    error=f"File not found: {path}",
                )
            
            if not resolved_path.is_file():
                return ToolResult(
                    success=False,
                    output=None,
                    error=f"Path is not a file: {path}",
                )
            
            # Read file asynchronously
            loop = asyncio.get_event_loop()
            content = await loop.run_in_executor(
                None,
                lambda: resolved_path.read_text(encoding=self.default_encoding),
            )
            
            return ToolResult(
                success=True,
                output=content,
                error=None,
            )
            
        except PermissionError as exc:
            return ToolResult(
                success=False,
                output=None,
                error=f"Permission denied reading file '{path}': {str(exc)}",
            )
        except UnicodeDecodeError as exc:
            return ToolResult(
                success=False,
                output=None,
                error=f"File '{path}' is not a valid text file: {str(exc)}",
            )
        except Exception as exc:
            return ToolResult(
                success=False,
                output=None,
                error=f"Error reading file '{path}': {str(exc)}",
            )
    
    async def write_file(self, path: str, content: str) -> ToolResult:
        """Write content to a file.
        
        Args:
            path: Path to the file to write.
            content: Content to write to the file.
            
        Returns:
            ToolResult indicating success or failure.
        """
        validation = self._validate_path(path)
        if not validation.is_valid:
            return ToolResult(
                success=False,
                output=None,
                error=validation.error_message,
            )
        
        resolved_path = validation.resolved_path
        
        try:
            # Ensure parent directory exists
            parent_dir = resolved_path.parent
            if not parent_dir.exists():
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(
                    None,
                    lambda: parent_dir.mkdir(parents=True, exist_ok=True),
                )
            
            # Write file asynchronously
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                lambda: resolved_path.write_text(
                    content,
                    encoding=self.default_encoding,
                ),
            )
            
            return ToolResult(
                success=True,
                output=f"Successfully wrote {len(content)} characters to {path}",
                error=None,
            )
            
        except PermissionError as exc:
            return ToolResult(
                success=False,
                output=None,
                error=f"Permission denied writing file '{path}': {str(exc)}",
            )
        except Exception as exc:
            return ToolResult(
                success=False,
                output=None,
                error=f"Error writing file '{path}': {str(exc)}",
            )
    
    async def list_dir(self, path: str) -> ToolResult:
        """List contents of a directory.
        
        Args:
            path: Path to the directory to list.
            
        Returns:
            ToolResult with list of entries on success.
        """
        validation = self._validate_path(path)
        if not validation.is_valid:
            return ToolResult(
                success=False,
                output=None,
                error=validation.error_message,
            )
        
        resolved_path = validation.resolved_path
        
        try:
            if not resolved_path.exists():
                return ToolResult(
                    success=False,
                    output=None,
                    error=f"Directory not found: {path}",
                )
            
            if not resolved_path.is_dir():
                return ToolResult(
                    success=False,
                    output=None,
                    error=f"Path is not a directory: {path}",
                )
            
            # List directory asynchronously
            loop = asyncio.get_event_loop()
            entries = await loop.run_in_executor(None, lambda: list(resolved_path.iterdir()))
            
            # Format entries with metadata
            result_entries: List[dict[str, Any]] = []
            for entry in entries:
                try:
                    stat = entry.stat()
                    entry_info = {
                        "name": entry.name,
                        "path": str(entry.relative_to(resolved_path)),
                        "type": "directory" if entry.is_dir() else "file",
                        "size": stat.st_size if entry.is_file() else None,
                    }
                    result_entries.append(entry_info)
                except (OSError, PermissionError):
                    # Skip entries we can't stat
                    result_entries.append({
                        "name": entry.name,
                        "path": str(entry.relative_to(resolved_path)),
                        "type": "unknown",
                        "size": None,
                    })
            
            return ToolResult(
                success=True,
                output={
                    "path": str(resolved_path),
                    "entries": result_entries,
                    "count": len(result_entries),
                },
                error=None,
            )
            
        except PermissionError as exc:
            return ToolResult(
                success=False,
                output=None,
                error=f"Permission denied listing directory '{path}': {str(exc)}",
            )
        except Exception as exc:
            return ToolResult(
                success=False,
                output=None,
                error=f"Error listing directory '{path}': {str(exc)}",
            )
    
    async def exists(self, path: str) -> ToolResult:
        """Check if a file or directory exists.
        
        Args:
            path: Path to check.
            
        Returns:
            ToolResult with existence status and type information.
        """
        validation = self._validate_path(path)
        if not validation.is_valid:
            return ToolResult(
                success=False,
                output=None,
                error=validation.error_message,
            )
        
        resolved_path = validation.resolved_path
        
        try:
            loop = asyncio.get_event_loop()
            exists_result = await loop.run_in_executor(None, resolved_path.exists)
            
            if not exists_result:
                return ToolResult(
                    success=True,
                    output={
                        "exists": False,
                        "type": None,
                        "path": str(resolved_path),
                    },
                    error=None,
                )
            
            # Determine type
            is_file = await loop.run_in_executor(None, resolved_path.is_file)
            is_dir = await loop.run_in_executor(None, resolved_path.is_dir)
            
            path_type = "file" if is_file else "directory" if is_dir else "other"
            
            return ToolResult(
                success=True,
                output={
                    "exists": True,
                    "type": path_type,
                    "path": str(resolved_path),
                },
                error=None,
            )
            
        except Exception as exc:
            return ToolResult(
                success=False,
                output=None,
                error=f"Error checking existence of '{path}': {str(exc)}",
            )
    
    async def execute(self, **params: Any) -> ToolResult:
        """Execute a filesystem operation based on parameters.
        
        This is the main entry point for the Tool base class. It dispatches
        to the appropriate method based on the 'operation' parameter.
        
        Args:
            **params: Parameters must include:
                - operation: One of 'read_file', 'write_file', 'list_dir', 'exists'
                - path: Path for the operation
                - content: Required for 'write_file' operation
                
        Returns:
            ToolResult from the executed operation.
            
        Raises:
            ToolError: If the operation is unknown or parameters are invalid.
        """
        operation = params.get("operation")
        path = params.get("path")
        
        if not operation:
            return ToolResult(
                success=False,
                output=None,
                error="Missing required parameter: 'operation'",
            )
        
        if not path:
            return ToolResult(
                success=False,
                output=None,
                error="Missing required parameter: 'path'",
            )
        
        # Dispatch to appropriate method
        if operation == "read_file":
            return await self.read_file(path)
        
        elif operation == "write_file":
            content = params.get("content")
            if content is None:
                return ToolResult(
                    success=False,
                    output=None,
                    error="Missing required parameter 'content' for write_file operation",
                )
            return await self.write_file(path, content)
        
        elif operation == "list_dir":
            return await self.list_dir(path)
        
        elif operation == "exists":
            return await self.exists(path)
        
        else:
            return ToolResult(
                success=False,
                output=None,
                error=f"Unknown operation: '{operation}'. "
                      f"Valid operations are: read_file, write_file, list_dir, exists",
            )