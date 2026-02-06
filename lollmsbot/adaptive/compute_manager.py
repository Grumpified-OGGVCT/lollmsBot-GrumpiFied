"""
Compute Manager - Adaptive Computation for Efficient LLM Usage

Implements MIT's research on dynamic resource allocation based on task complexity.
This module analyzes incoming requests and allocates computational resources
accordingly, using early-exit strategies for simple tasks and full model power
for complex ones.

Key Features:
- Complexity scoring for prompts
- Early-exit detection
- Dynamic KV-cache sizing hints
- Token efficiency optimization
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger("lollmsbot.adaptive.compute_manager")


class ComplexityLevel(Enum):
    """Task complexity levels for adaptive computation."""
    TRIVIAL = 1      # Simple queries, greetings (< 50 tokens, no reasoning)
    SIMPLE = 2       # Basic Q&A, factual lookups (50-200 tokens, minimal reasoning)
    MEDIUM = 3       # Multi-step tasks, some analysis (200-500 tokens, moderate reasoning)
    COMPLEX = 4      # Multi-turn reasoning, planning (500-1500 tokens, complex reasoning)
    ADVANCED = 5     # Long-form generation, deep analysis (1500+ tokens, advanced reasoning)


@dataclass
class ComplexityScore:
    """Complexity assessment for a task.
    
    Attributes:
        level: The complexity level
        score: Numeric score (0.0-1.0)
        reasoning: Why this complexity was assigned
        token_estimate: Estimated tokens needed
        cache_size_hint: Suggested KV-cache size (None = use full)
        early_exit_candidate: Whether this can use early exit layers
    """
    level: ComplexityLevel
    score: float
    reasoning: List[str]
    token_estimate: int
    cache_size_hint: Optional[int] = None
    early_exit_candidate: bool = False


class ComputeManager:
    """Manages adaptive computation based on task complexity.
    
    This implements the MIT research on adaptive computation by analyzing
    incoming prompts and providing hints for resource allocation.
    """
    
    # Patterns for complexity detection
    GREETING_PATTERNS = [
        r"^(hi|hello|hey|greetings|good\s+(morning|afternoon|evening))",
        r"^(what'?s up|how are you|how's it going)",
    ]
    
    SIMPLE_QUERY_PATTERNS = [
        r"^(what is|who is|when did|where is)",
        r"(yes|no|ok|okay|thanks|thank you)$",
        r"^(list|show me|tell me about)\s+\w+$",
    ]
    
    COMPLEX_INDICATORS = [
        "analyze", "compare", "evaluate", "synthesize",
        "create", "build", "design", "implement",
        "explain why", "break down", "step by step",
        "multiple", "several", "various", "comprehensive",
    ]
    
    ADVANCED_INDICATORS = [
        "research", "investigate", "comprehensive analysis",
        "pros and cons", "trade-offs", "implications",
        "long-term", "strategic", "architectural",
    ]
    
    def __init__(self):
        """Initialize the compute manager."""
        self._greeting_regex = [re.compile(p, re.IGNORECASE) for p in self.GREETING_PATTERNS]
        self._simple_regex = [re.compile(p, re.IGNORECASE) for p in self.SIMPLE_QUERY_PATTERNS]
    
    def assess_complexity(
        self,
        message: str,
        context_length: int = 0,
        has_history: bool = False,
    ) -> ComplexityScore:
        """Assess the complexity of a user message.
        
        Args:
            message: The user's message
            context_length: Length of conversation history (in tokens)
            has_history: Whether there's relevant conversation history
            
        Returns:
            ComplexityScore with recommendations
        """
        msg_lower = message.lower().strip()
        msg_words = len(message.split())
        reasoning = []
        
        # Check for greetings/trivial (early exit candidate)
        if any(pattern.match(msg_lower) for pattern in self._greeting_regex):
            reasoning.append("Greeting detected - trivial response")
            return ComplexityScore(
                level=ComplexityLevel.TRIVIAL,
                score=0.1,
                reasoning=reasoning,
                token_estimate=20,
                cache_size_hint=128,  # Minimal cache
                early_exit_candidate=True
            )
        
        # Check for simple queries (early exit candidate)
        if any(pattern.match(msg_lower) for pattern in self._simple_regex):
            reasoning.append("Simple query pattern matched")
            return ComplexityScore(
                level=ComplexityLevel.SIMPLE,
                score=0.25,
                reasoning=reasoning,
                token_estimate=100,
                cache_size_hint=512,
                early_exit_candidate=True
            )
        
        # Count complexity indicators
        complex_count = sum(1 for ind in self.COMPLEX_INDICATORS if ind in msg_lower)
        advanced_count = sum(1 for ind in self.ADVANCED_INDICATORS if ind in msg_lower)
        
        # Base scoring
        word_score = min(msg_words / 100, 0.5)  # Cap at 0.5
        context_score = min(context_length / 2000, 0.3)  # Cap at 0.3
        indicator_score = min((complex_count * 0.1 + advanced_count * 0.2), 0.4)
        
        total_score = word_score + context_score + indicator_score
        
        # Determine level
        if total_score < 0.3:
            level = ComplexityLevel.SIMPLE
            token_est = 150
            cache_hint = 1024
            early_exit = True
            reasoning.append(f"Low complexity score: {total_score:.2f}")
        elif total_score < 0.5:
            level = ComplexityLevel.MEDIUM
            token_est = 350
            cache_hint = 2048
            early_exit = False
            reasoning.append(f"Medium complexity score: {total_score:.2f}")
        elif total_score < 0.7:
            level = ComplexityLevel.COMPLEX
            token_est = 800
            cache_hint = 4096
            early_exit = False
            reasoning.append(f"Complex task score: {total_score:.2f}")
        else:
            level = ComplexityLevel.ADVANCED
            token_est = 2000
            cache_hint = None  # Use full cache
            early_exit = False
            reasoning.append(f"Advanced task score: {total_score:.2f}")
        
        # Add context-specific reasoning
        if complex_count > 0:
            reasoning.append(f"Found {complex_count} complexity indicators")
        if advanced_count > 0:
            reasoning.append(f"Found {advanced_count} advanced indicators")
        if has_history:
            reasoning.append("Multi-turn conversation context")
        
        return ComplexityScore(
            level=level,
            score=total_score,
            reasoning=reasoning,
            token_estimate=token_est,
            cache_size_hint=cache_hint,
            early_exit_candidate=early_exit
        )
    
    def get_generation_params(self, complexity: ComplexityScore) -> Dict[str, any]:
        """Get recommended generation parameters based on complexity.
        
        Args:
            complexity: The complexity assessment
            
        Returns:
            Dict of parameters for LLM generation
        """
        params = {
            "max_tokens": complexity.token_estimate,
        }
        
        # Adjust temperature based on complexity
        if complexity.level == ComplexityLevel.TRIVIAL:
            params["temperature"] = 0.3  # Low variance for greetings
        elif complexity.level == ComplexityLevel.SIMPLE:
            params["temperature"] = 0.5  # Factual responses
        elif complexity.level in (ComplexityLevel.MEDIUM, ComplexityLevel.COMPLEX):
            params["temperature"] = 0.7  # Balanced creativity
        else:  # ADVANCED
            params["temperature"] = 0.8  # Higher creativity for complex tasks
        
        # Cache hints (if supported by backend)
        if complexity.cache_size_hint:
            params["cache_size_hint"] = complexity.cache_size_hint
        
        # Early exit hint (if supported)
        if complexity.early_exit_candidate:
            params["early_exit"] = True
        
        return params
    
    def should_use_full_model(self, complexity: ComplexityScore) -> bool:
        """Determine if the full model is needed or if a smaller model/early exit suffices.
        
        Args:
            complexity: The complexity assessment
            
        Returns:
            True if full model is recommended, False if early exit is acceptable
        """
        return complexity.level.value >= ComplexityLevel.MEDIUM.value
    
    def estimate_cost_savings(self, complexity: ComplexityScore) -> Tuple[float, str]:
        """Estimate cost savings from adaptive computation.
        
        Args:
            complexity: The complexity assessment
            
        Returns:
            Tuple of (savings_ratio, description)
            savings_ratio: 0.0 (no savings) to 1.0 (maximum savings)
        """
        if complexity.early_exit_candidate:
            return (0.7, "Early exit can save ~70% compute by using shallow layers")
        elif complexity.cache_size_hint and complexity.cache_size_hint < 2048:
            return (0.3, "Reduced cache size saves ~30% memory/compute")
        elif complexity.level == ComplexityLevel.MEDIUM:
            return (0.1, "Minor optimization via token limit")
        else:
            return (0.0, "Full model required for complex task")


# Global instance
_compute_manager: Optional[ComputeManager] = None


def get_compute_manager() -> ComputeManager:
    """Get or create the global ComputeManager instance."""
    global _compute_manager
    if _compute_manager is None:
        _compute_manager = ComputeManager()
    return _compute_manager
