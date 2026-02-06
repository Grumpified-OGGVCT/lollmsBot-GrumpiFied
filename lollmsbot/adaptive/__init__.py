"""
Adaptive Computation Module

Implements MIT's research on dynamic resource allocation based on task complexity.
"""

from lollmsbot.adaptive.compute_manager import (
    ComputeManager,
    ComplexityLevel,
    ComplexityScore,
    get_compute_manager,
)

__all__ = [
    "ComputeManager",
    "ComplexityLevel",
    "ComplexityScore",
    "get_compute_manager",
]
