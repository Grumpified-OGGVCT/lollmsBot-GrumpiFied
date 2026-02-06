"""
Tools package for LollmsBot.

This package provides a collection of built-in tools for the Agent framework,
including filesystem operations, HTTP requests, calendar management, and
shell command execution. It also provides the ToolRegistry for dynamic
tool registration and discovery.

Example:
    >>> from lollmsbot.tools import get_default_tools, ToolRegistry
    >>> tools = get_default_tools()
    >>> registry = ToolRegistry()
    >>> for tool in tools:
    ...     registry.register(tool)
"""

from lollmsbot.agent import Tool, ToolResult, ToolError

# Import all tool classes
from lollmsbot.tools.filesystem import FilesystemTool
from lollmsbot.tools.http import HttpTool
from lollmsbot.tools.calendar import CalendarTool
from lollmsbot.tools.shell import ShellTool


class ToolRegistry:
    """Dynamic registry for tool registration and discovery.
    
    The ToolRegistry provides a centralized way to manage tool instances,
    allowing dynamic registration, lookup, and enumeration of available tools.
    
    Attributes:
        _tools: Dictionary mapping tool names to tool instances.
    
    Example:
        >>> registry = ToolRegistry()
        >>> registry.register(FilesystemTool())
        >>> tool = registry.get("filesystem")
        >>> all_tools = registry.list_tools()
    """
    
    def __init__(self) -> None:
        """Initialize an empty tool registry."""
        self._tools: dict[str, Tool] = {}
    
    def register(self, tool: Tool) -> None:
        """Register a tool in the registry.
        
        Args:
            tool: Tool instance to register.
            
        Raises:
            ValueError: If a tool with the same name is already registered.
        """
        if tool.name in self._tools:
            raise ValueError(f"Tool '{tool.name}' is already registered")
        self._tools[tool.name] = tool
    
    def unregister(self, tool_name: str) -> Tool | None:
        """Remove a tool from the registry.
        
        Args:
            tool_name: Name of the tool to remove.
            
        Returns:
            The removed tool if found, None otherwise.
        """
        return self._tools.pop(tool_name, None)
    
    def get(self, tool_name: str) -> Tool | None:
        """Get a tool by name.
        
        Args:
            tool_name: Name of the tool to retrieve.
            
        Returns:
            The tool instance if found, None otherwise.
        """
        return self._tools.get(tool_name)
    
    def list_tools(self) -> list[Tool]:
        """List all registered tools.
        
        Returns:
            List of all registered tool instances.
        """
        return list(self._tools.values())
    
    def clear(self) -> None:
        """Remove all tools from the registry."""
        self._tools.clear()
    
    def __contains__(self, tool_name: str) -> bool:
        """Check if a tool name is registered.
        
        Args:
            tool_name: Name to check.
            
        Returns:
            True if the tool is registered, False otherwise.
        """
        return tool_name in self._tools


class SmartWebFetcher:
    """Intelligently choose between HTTP and Browser tools for web fetching.
    
    This dispatcher optimizes web content fetching by:
    - Using lightweight HTTP tool for static content (faster, lower resource)
    - Using Browser tool for JavaScript-heavy or interactive content
    - Automatically falling back when Browser isn't available
    
    Example:
        >>> fetcher = SmartWebFetcher(http_tool, browser_tool)
        >>> # Fetch static page (uses HTTP)
        >>> content = await fetcher.fetch("https://example.com")
        >>> # Fetch dynamic page (uses Browser)
        >>> content = await fetcher.fetch("https://app.example.com", requires_js=True)
    """
    
    def __init__(self, http_tool: HttpTool, browser_tool: Tool = None):
        """Initialize the smart web fetcher.
        
        Args:
            http_tool: HTTP tool for static content
            browser_tool: Optional browser tool for dynamic content
        """
        self.http_tool = http_tool
        self.browser_tool = browser_tool
    
    def is_browser_available(self) -> bool:
        """Check if browser tool is available."""
        return self.browser_tool is not None
    
    async def fetch(
        self,
        url: str,
        requires_js: bool = False,
        requires_interaction: bool = False,
        **kwargs
    ) -> str:
        """Fetch web content using the optimal tool.
        
        Args:
            url: URL to fetch
            requires_js: Whether JavaScript execution is needed
            requires_interaction: Whether user interaction simulation is needed
            **kwargs: Additional arguments passed to the tool
            
        Returns:
            Fetched content as string
            
        Raises:
            ToolError: If fetching fails
        """
        # Determine which tool to use
        needs_browser = requires_js or requires_interaction
        
        if needs_browser:
            if self.is_browser_available():
                # Use browser for dynamic content
                return await self._fetch_with_browser(url, **kwargs)
            else:
                # Browser not available, log warning and fall back to HTTP
                import logging
                logger = logging.getLogger("lollmsbot.tools")
                logger.warning(
                    f"Browser tool not available for {url}, falling back to HTTP "
                    "(some content may be missing)"
                )
                return await self._fetch_with_http(url, **kwargs)
        else:
            # Use HTTP for static content (faster and lighter)
            return await self._fetch_with_http(url, **kwargs)
    
    async def _fetch_with_http(self, url: str, **kwargs) -> str:
        """Fetch content using HTTP tool."""
        result = await self.http_tool.execute(
            action="get",
            url=url,
            **kwargs
        )
        
        if result.success:
            return result.output
        else:
            raise ToolError(f"HTTP fetch failed: {result.error}")
    
    async def _fetch_with_browser(self, url: str, **kwargs) -> str:
        """Fetch content using Browser tool."""
        if not self.browser_tool:
            raise ToolError("Browser tool not available")
        
        result = await self.browser_tool.execute(
            action="fetch",
            url=url,
            **kwargs
        )
        
        if result.success:
            return result.output
        else:
            raise ToolError(f"Browser fetch failed: {result.error}")
    
    def __len__(self) -> int:
        """Get the number of registered tools."""
        return len(self._tools)
    
    def __repr__(self) -> str:
        return f"ToolRegistry({list(self._tools.keys())})"


def get_default_tools() -> list[Tool]:
    """Get a list of default tool instances.
    
    Returns a list containing instantiated default tools:
    - FilesystemTool: File and directory operations
    - HttpTool: HTTP requests and API calls
    - CalendarTool: Date and time management
    - ShellTool: Safe shell command execution
    
    Returns:
        List of default tool instances.
        
    Example:
        >>> tools = get_default_tools()
        >>> for tool in tools:
        ...     print(f"Loaded: {tool.name}")
    """
    return [
        FilesystemTool(),
        HttpTool(),
        CalendarTool(),
        ShellTool(),
    ]


__all__ = [
    # Base classes from agent module
    "Tool",
    "ToolResult",
    "ToolError",
    # Tool registry
    "ToolRegistry",
    # Smart dispatchers
    "SmartWebFetcher",
    # Tool classes
    "FilesystemTool",
    "HttpTool",
    "CalendarTool",
    "ShellTool",
    # Utility functions
    "get_default_tools",
]
]
