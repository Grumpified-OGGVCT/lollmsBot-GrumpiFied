"""
Recursive Summarizer - Hierarchical Context Compression for 100K+ Tokens

Implements MIT research on recursive context expansion through hierarchical summarization.
This enables handling of arbitrarily large contexts by breaking them into chunks,
summarizing each chunk, then recursively summarizing the summaries.

Key Features:
- Handles 100K+ token contexts
- Hierarchical chunking strategy
- Recursive summarization
- Preserves key information at each level
- Configurable chunk sizes and overlap
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger("lollmsbot.memory.recursive_summarizer")


@dataclass
class SummaryNode:
    """A node in the hierarchical summary tree.
    
    Attributes:
        level: Depth in tree (0 = original chunks, 1+ = summaries)
        content: The text content at this level
        children: Child nodes (original chunks or lower-level summaries)
        token_count: Estimated token count
        key_points: Extracted key points
    """
    level: int
    content: str
    children: List[SummaryNode] = field(default_factory=list)
    token_count: int = 0
    key_points: List[str] = field(default_factory=list)


class RecursiveSummarizer:
    """Hierarchical summarizer for arbitrarily large contexts.
    
    Usage:
        summarizer = RecursiveSummarizer(chunk_size=2000, target_summary_ratio=0.3)
        
        # Handle 100K token document
        large_text = load_100k_token_document()
        summary = await summarizer.summarize(large_text, max_tokens=4000)
        
        # Or get hierarchical structure
        tree = await summarizer.build_hierarchy(large_text)
        summary = tree.content  # Top-level summary
        details = tree.children  # Access different granularities
    """
    
    def __init__(
        self,
        chunk_size: int = 2000,
        chunk_overlap: int = 200,
        target_summary_ratio: float = 0.3,
        max_recursion_depth: int = 10,
    ):
        """Initialize recursive summarizer.
        
        Args:
            chunk_size: Target tokens per chunk
            chunk_overlap: Overlap between chunks for context preservation
            target_summary_ratio: Target summary length as ratio of input (0.3 = 30%)
            max_recursion_depth: Maximum tree depth to prevent infinite recursion
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.target_summary_ratio = target_summary_ratio
        self.max_recursion_depth = max_recursion_depth
    
    def _estimate_tokens(self, text: str) -> int:
        """Rough token count estimation (4 chars per token average)."""
        return len(text) // 4
    
    def _chunk_text(self, text: str) -> List[str]:
        """Split text into overlapping chunks.
        
        Args:
            text: Input text
            
        Returns:
            List of text chunks with overlap
        """
        # Simple word-based chunking with overlap
        words = text.split()
        chunks = []
        
        chunk_word_size = self.chunk_size // 4  # Rough words per chunk
        overlap_words = self.chunk_overlap // 4
        
        i = 0
        while i < len(words):
            chunk_end = min(i + chunk_word_size, len(words))
            chunk = " ".join(words[i:chunk_end])
            chunks.append(chunk)
            
            # Move forward with overlap
            i += chunk_word_size - overlap_words
            if i >= len(words):
                break
        
        return chunks
    
    async def _summarize_chunk(
        self,
        chunk: str,
        target_length: int,
        lollms_client: Optional[Any] = None,
    ) -> str:
        """Summarize a single chunk.
        
        Args:
            chunk: Text to summarize
            target_length: Target summary length in tokens
            lollms_client: Optional LLM client for actual summarization
            
        Returns:
            Summary text
        """
        if lollms_client:
            # Use LLM for intelligent summarization
            prompt = f"""### System:
You are a precise summarizer. Create a concise summary that preserves key information, facts, and context.

### User:
Summarize the following text in approximately {target_length} tokens. Focus on the most important points:

{chunk}

### Assistant:
Summary:"""
            
            try:
                summary = lollms_client.generate_text(
                    prompt=prompt,
                    max_tokens=target_length,
                    temperature=0.3,  # Low temperature for factual summary
                )
                return summary.strip()
            except Exception as e:
                logger.error(f"LLM summarization failed: {e}")
                # Fall back to extraction
        
        # Fallback: Extract key sentences (simple heuristic)
        sentences = chunk.split(". ")
        # Take first and last sentences, plus some middle ones
        target_sentences = max(3, target_length // 30)
        if len(sentences) <= target_sentences:
            return chunk
        
        # Take beginning, middle, and end
        step = len(sentences) // target_sentences
        selected = [sentences[i] for i in range(0, len(sentences), step)][:target_sentences]
        return ". ".join(selected) + "."
    
    async def build_hierarchy(
        self,
        text: str,
        lollms_client: Optional[Any] = None,
        current_level: int = 0,
    ) -> SummaryNode:
        """Build hierarchical summary tree.
        
        Args:
            text: Input text
            lollms_client: Optional LLM client
            current_level: Current recursion level
            
        Returns:
            Root SummaryNode of the tree
        """
        token_count = self._estimate_tokens(text)
        
        # Base case: text is small enough
        if token_count <= self.chunk_size or current_level >= self.max_recursion_depth:
            return SummaryNode(
                level=current_level,
                content=text,
                token_count=token_count,
            )
        
        # Recursive case: chunk and summarize
        chunks = self._chunk_text(text)
        logger.info(f"Level {current_level}: Split {token_count} tokens into {len(chunks)} chunks")
        
        # Summarize each chunk
        child_nodes = []
        summaries = []
        
        for i, chunk in enumerate(chunks):
            target_length = int(self._estimate_tokens(chunk) * self.target_summary_ratio)
            summary = await self._summarize_chunk(chunk, target_length, lollms_client)
            summaries.append(summary)
            
            child_nodes.append(SummaryNode(
                level=current_level,
                content=chunk,
                token_count=self._estimate_tokens(chunk),
            ))
        
        # Combine summaries and recurse if needed
        combined_summary = "\n\n".join(summaries)
        combined_tokens = self._estimate_tokens(combined_summary)
        
        # If combined summaries are still too large, recurse
        if combined_tokens > self.chunk_size:
            logger.info(f"Level {current_level}: Recursing on {combined_tokens} token summary")
            parent_node = await self.build_hierarchy(
                combined_summary,
                lollms_client,
                current_level + 1
            )
            parent_node.children = child_nodes
            return parent_node
        else:
            # This is the top level
            return SummaryNode(
                level=current_level + 1,
                content=combined_summary,
                children=child_nodes,
                token_count=combined_tokens,
            )
    
    async def summarize(
        self,
        text: str,
        max_tokens: int = 4000,
        lollms_client: Optional[Any] = None,
    ) -> str:
        """Summarize arbitrarily large text to fit within max_tokens.
        
        Args:
            text: Input text (can be 100K+ tokens)
            max_tokens: Maximum tokens for output summary
            lollms_client: Optional LLM client for intelligent summarization
            
        Returns:
            Condensed summary fitting within max_tokens
        """
        input_tokens = self._estimate_tokens(text)
        logger.info(f"Summarizing {input_tokens} tokens -> {max_tokens} tokens")
        
        # If already small enough, return as-is
        if input_tokens <= max_tokens:
            return text
        
        # Build hierarchical summary tree
        tree = await self.build_hierarchy(text, lollms_client)
        
        # Return top-level summary
        summary = tree.content
        summary_tokens = self._estimate_tokens(summary)
        
        logger.info(f"Generated summary: {summary_tokens} tokens (target: {max_tokens})")
        
        # If still too large, truncate (shouldn't happen with proper ratio)
        if summary_tokens > max_tokens:
            # Truncate to max_tokens
            char_limit = max_tokens * 4  # Rough estimate
            summary = summary[:char_limit] + "..."
        
        return summary
    
    async def get_multi_granularity_summaries(
        self,
        text: str,
        lollms_client: Optional[Any] = None,
    ) -> Dict[str, str]:
        """Get summaries at multiple levels of detail.
        
        Useful for providing different context depths based on need.
        
        Args:
            text: Input text
            lollms_client: Optional LLM client
            
        Returns:
            Dict with keys: 'brief' (100 tokens), 'medium' (500 tokens), 
            'detailed' (2000 tokens), 'full' (original)
        """
        tree = await self.build_hierarchy(text, lollms_client)
        
        return {
            "brief": await self.summarize(text, max_tokens=100, lollms_client=lollms_client),
            "medium": await self.summarize(text, max_tokens=500, lollms_client=lollms_client),
            "detailed": await self.summarize(text, max_tokens=2000, lollms_client=lollms_client),
            "full": text,
        }


# Global instance
_summarizer: Optional[RecursiveSummarizer] = None


def get_recursive_summarizer() -> RecursiveSummarizer:
    """Get or create global recursive summarizer instance."""
    global _summarizer
    if _summarizer is None:
        _summarizer = RecursiveSummarizer()
    return _summarizer
