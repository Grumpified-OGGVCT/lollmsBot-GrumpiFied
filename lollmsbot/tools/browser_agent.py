"""
Browser Agent - Web Browsing with Semantic DOM Snapshots

Implements OpenClaw's "semantic snapshot" approach: parse the accessibility tree (ARIA)
instead of taking expensive screenshots. Falls back to vision model only when needed.

Key Features:
- ARIA/accessibility tree parsing for interactive elements
- JSON representation of DOM structure (500 tokens vs 5000 for screenshot)
- Intelligent decision: text extraction vs visual analysis
- Fallback to screenshot for layout-heavy tasks
- Cost-effective web browsing

Requires: playwright (optional dependency)
"""

from __future__ import annotations

import asyncio
import json
import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger("lollmsbot.tools.browser_agent")

# Check if playwright is available
try:
    from playwright.async_api import async_playwright, Browser, Page
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    async_playwright = None
    Browser = None
    Page = None
    logger.warning("Playwright not available - browser agent will be disabled")


class SnapshotMode(Enum):
    """Mode for capturing page content."""
    SEMANTIC = "semantic"  # ARIA tree (cheap, text-focused)
    VISUAL = "visual"      # Screenshot (expensive, layout-focused)
    HYBRID = "hybrid"      # Both semantic + screenshot


@dataclass
class InteractiveElement:
    """An interactive element from the accessibility tree.
    
    Attributes:
        role: ARIA role (button, link, textbox, etc.)
        name: Accessible name/label
        value: Current value (for inputs)
        tag: HTML tag name
        selector: CSS selector to find this element
        children: Nested interactive elements
    """
    role: str
    name: str
    value: str = ""
    tag: str = ""
    selector: str = ""
    children: List[InteractiveElement] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "role": self.role,
            "name": self.name,
            "value": self.value,
            "tag": self.tag,
            "selector": self.selector,
            "children": [c.to_dict() for c in self.children],
        }


@dataclass
class SemanticSnapshot:
    """Semantic representation of a web page.
    
    Attributes:
        url: Page URL
        title: Page title
        interactive_elements: Parsed accessibility tree
        text_content: Extracted visible text
        metadata: Page metadata (description, etc.)
        estimated_tokens: Token count for this snapshot
    """
    url: str
    title: str
    interactive_elements: List[InteractiveElement]
    text_content: str
    metadata: Dict[str, str] = field(default_factory=dict)
    estimated_tokens: int = 0
    
    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps({
            "url": self.url,
            "title": self.title,
            "interactive_elements": [e.to_dict() for e in self.interactive_elements],
            "text_content": self.text_content[:1000],  # Truncate for brevity
            "metadata": self.metadata,
        }, indent=2)


class BrowserAgent:
    """Browser agent with semantic DOM snapshot capability.
    
    Usage:
        agent = BrowserAgent()
        await agent.start()
        
        # Semantic snapshot (cheap, ~500 tokens)
        snapshot = await agent.get_semantic_snapshot("https://example.com")
        print(snapshot.to_json())
        
        # Or screenshot if needed (expensive, ~5000 tokens)
        screenshot_path = await agent.take_screenshot("https://example.com")
        
        await agent.close()
    """
    
    def __init__(self):
        """Initialize browser agent."""
        if not PLAYWRIGHT_AVAILABLE:
            raise RuntimeError("Playwright not available. Install with: pip install playwright && playwright install")
        
        self.playwright = None
        self.browser: Optional[Browser] = None
        self.context = None
        self._started = False
    
    async def start(self, headless: bool = True):
        """Start the browser.
        
        Args:
            headless: Whether to run in headless mode
        """
        if self._started:
            return
        
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(headless=headless)
        self.context = await self.browser.new_context(
            viewport={"width": 1280, "height": 720},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        )
        self._started = True
        logger.info("Browser agent started")
    
    async def close(self):
        """Close the browser."""
        if not self._started:
            return
        
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
        
        self._started = False
        logger.info("Browser agent closed")
    
    async def _navigate(self, url: str) -> Page:
        """Navigate to URL and return page.
        
        Args:
            url: URL to navigate to
            
        Returns:
            Playwright Page object
        """
        if not self._started:
            await self.start()
        
        page = await self.context.new_page()
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=30000)
            # Wait a bit for dynamic content
            await page.wait_for_timeout(1000)
        except Exception as e:
            logger.error(f"Navigation failed: {e}")
            await page.close()
            raise
        
        return page
    
    async def get_semantic_snapshot(self, url: str) -> SemanticSnapshot:
        """Get semantic snapshot of a page (ARIA tree + text).
        
        This is the cost-effective approach: ~500 tokens vs ~5000 for screenshot.
        
        Args:
            url: URL to snapshot
            
        Returns:
            SemanticSnapshot with parsed interactive elements
        """
        page = await self._navigate(url)
        
        try:
            # Get page title and metadata
            title = await page.title()
            metadata = {}
            
            # Try to get meta description
            try:
                description = await page.locator('meta[name="description"]').get_attribute("content")
                if description:
                    metadata["description"] = description
            except:
                pass
            
            # Parse accessibility tree for interactive elements
            interactive_elements = await self._parse_accessibility_tree(page)
            
            # Extract visible text content
            text_content = await page.evaluate("""
                () => {
                    const walker = document.createTreeWalker(
                        document.body,
                        NodeFilter.SHOW_TEXT,
                        null
                    );
                    let text = '';
                    let node;
                    while (node = walker.nextNode()) {
                        const parent = node.parentElement;
                        // Skip hidden elements
                        if (parent && window.getComputedStyle(parent).display !== 'none') {
                            text += node.textContent.trim() + ' ';
                        }
                    }
                    return text.trim();
                }
            """)
            
            snapshot = SemanticSnapshot(
                url=url,
                title=title,
                interactive_elements=interactive_elements,
                text_content=text_content[:5000],  # Limit text
                metadata=metadata,
            )
            
            # Estimate tokens (rough: 4 chars per token)
            snapshot.estimated_tokens = len(snapshot.to_json()) // 4
            
            logger.info(f"Semantic snapshot: {snapshot.estimated_tokens} tokens")
            
            return snapshot
            
        finally:
            await page.close()
    
    async def _parse_accessibility_tree(self, page: Page) -> List[InteractiveElement]:
        """Parse accessibility tree to extract interactive elements.
        
        Args:
            page: Playwright page
            
        Returns:
            List of InteractiveElement objects
        """
        # Extract interactive elements using ARIA roles
        elements = await page.evaluate("""
            () => {
                const interactiveRoles = [
                    'button', 'link', 'textbox', 'searchbox', 'checkbox',
                    'radio', 'menuitem', 'tab', 'option', 'slider'
                ];
                
                function extractElement(el, depth = 0) {
                    if (depth > 3) return null;  // Limit depth
                    
                    const role = el.getAttribute('role') || el.tagName.toLowerCase();
                    const name = el.getAttribute('aria-label') || 
                                el.getAttribute('aria-labelledby') ||
                                el.textContent.substring(0, 50).trim();
                    const value = el.value || el.getAttribute('aria-valuenow') || '';
                    
                    // Get a selector
                    const id = el.id;
                    const selector = id ? `#${id}` : el.tagName.toLowerCase();
                    
                    return {
                        role: role,
                        name: name,
                        value: value,
                        tag: el.tagName.toLowerCase(),
                        selector: selector,
                    };
                }
                
                // Find all interactive elements
                const results = [];
                const selectors = [
                    'button', 'a', 'input', 'select', 'textarea',
                    '[role="button"]', '[role="link"]', '[role="textbox"]'
                ];
                
                selectors.forEach(sel => {
                    document.querySelectorAll(sel).forEach(el => {
                        // Skip hidden elements
                        if (window.getComputedStyle(el).display === 'none') return;
                        
                        const extracted = extractElement(el);
                        if (extracted && extracted.name) {
                            results.push(extracted);
                        }
                    });
                });
                
                // Limit to first 50 interactive elements
                return results.slice(0, 50);
            }
        """)
        
        # Convert to InteractiveElement objects
        return [
            InteractiveElement(
                role=el.get("role", ""),
                name=el.get("name", ""),
                value=el.get("value", ""),
                tag=el.get("tag", ""),
                selector=el.get("selector", ""),
            )
            for el in elements
        ]
    
    async def take_screenshot(
        self,
        url: str,
        output_path: str = "screenshot.png",
        full_page: bool = False,
    ) -> str:
        """Take a screenshot (fallback for layout-heavy tasks).
        
        Args:
            url: URL to screenshot
            output_path: Where to save the screenshot
            full_page: Whether to capture full scrollable page
            
        Returns:
            Path to saved screenshot
        """
        page = await self._navigate(url)
        
        try:
            await page.screenshot(path=output_path, full_page=full_page)
            logger.info(f"Screenshot saved: {output_path}")
            return output_path
        finally:
            await page.close()
    
    async def decide_snapshot_mode(
        self,
        url: str,
        task_description: str,
    ) -> SnapshotMode:
        """Decide whether to use semantic or visual snapshot based on task.
        
        Args:
            url: Target URL
            task_description: What the user wants to do
            
        Returns:
            Recommended SnapshotMode
        """
        # Keywords that suggest layout/visual analysis needed
        visual_keywords = [
            "layout", "design", "color", "appearance", "look",
            "visual", "image", "screenshot", "how it looks"
        ]
        
        # Keywords that suggest text extraction is sufficient
        semantic_keywords = [
            "read", "text", "content", "find", "search", "click",
            "button", "link", "form", "fill", "submit"
        ]
        
        task_lower = task_description.lower()
        
        has_visual = any(kw in task_lower for kw in visual_keywords)
        has_semantic = any(kw in task_lower for kw in semantic_keywords)
        
        if has_visual and not has_semantic:
            return SnapshotMode.VISUAL
        elif has_semantic and not has_visual:
            return SnapshotMode.SEMANTIC
        else:
            # Default to semantic (cheaper)
            return SnapshotMode.SEMANTIC


# Global instance
_browser_agent: Optional[BrowserAgent] = None


async def get_browser_agent() -> BrowserAgent:
    """Get or create global browser agent instance."""
    global _browser_agent
    if _browser_agent is None:
        _browser_agent = BrowserAgent()
        await _browser_agent.start()
    return _browser_agent


def is_browser_available() -> bool:
    """Check if browser agent is available."""
    return PLAYWRIGHT_AVAILABLE
