"""
Restraint Semantics and UI Presentation Layer

This module provides human-friendly interpretations and inversions for 
constitutional restraints that have confusing semantics.

PROBLEM: hallucination_resistance is inverted from temperature:
- hallucination_resistance: 0.0 = creative, 1.0 = cautious
- temperature: 0.0 = cautious, 1.0 = creative

SOLUTION: Provide semantic mapping layer for UI presentation
"""

from typing import Dict, Tuple
from enum import Enum


class SemanticMapping(Enum):
    """Semantic interpretation of restraint dimensions."""
    DIRECT = "direct"  # Higher value = more of what the name says
    INVERTED = "inverted"  # Higher value = opposite of what the name suggests


# Mapping of restraint dimensions to their semantic interpretation
RESTRAINT_SEMANTICS: Dict[str, Dict[str, any]] = {
    "recursion_depth": {
        "mapping": SemanticMapping.DIRECT,
        "display_name": "Meta-Reasoning Depth",
        "description": "How deeply the AI thinks about its own thinking",
        "low_label": "Shallow",
        "mid_label": "Balanced",
        "high_label": "Deep",
        "tooltip": "Higher = more recursive self-analysis (slower but deeper)",
        "icon": "🧠",
    },
    
    "cognitive_budget_ms": {
        "mapping": SemanticMapping.DIRECT,
        "display_name": "Thinking Time",
        "description": "Time allocated for analytical reasoning per decision",
        "low_label": "Quick",
        "mid_label": "Moderate",
        "high_label": "Thorough",
        "tooltip": "Higher = more time for System-2 deliberation (slower but more careful)",
        "icon": "⏱️",
    },
    
    "simulation_fidelity": {
        "mapping": SemanticMapping.DIRECT,
        "display_name": "Scenario Detail",
        "description": "Detail level when simulating alternative outcomes",
        "low_label": "Rough",
        "mid_label": "Balanced",
        "high_label": "Detailed",
        "tooltip": "Higher = more detailed counterfactual simulations",
        "icon": "🎯",
    },
    
    # THE CONFUSING ONE - Fixed with inverted presentation
    "hallucination_resistance": {
        "mapping": SemanticMapping.INVERTED,  # Key fix!
        "display_name": "Creativity ↔ Accuracy",
        "description": "Balance between creative expression and factual accuracy",
        "low_label": "Accuracy First",
        "mid_label": "Balanced",
        "high_label": "Creativity First",
        "tooltip": (
            "LEFT (Low): Fact-focused, admits uncertainty, resists hallucination\n"
            "RIGHT (High): Creative expression, imaginative, accepts uncertainty\n"
            "Think of it like LLM temperature: Low = cautious, High = creative"
        ),
        "icon": "🎨",
        "inverse_note": "⚠️ Inverted from backend value for intuitive UI",
    },
    
    "uncertainty_propagation": {
        "mapping": SemanticMapping.DIRECT,
        "display_name": "Uncertainty Transparency",
        "description": "How aggressively to communicate uncertainty to user",
        "low_label": "Subtle",
        "mid_label": "Moderate",
        "high_label": "Explicit",
        "tooltip": "Higher = more visible warnings about uncertainty",
        "icon": "⚠️",
    },
    
    "contradiction_sensitivity": {
        "mapping": SemanticMapping.DIRECT,
        "display_name": "Consistency Checking",
        "description": "How aggressively to detect logical contradictions",
        "low_label": "Relaxed",
        "mid_label": "Moderate",
        "high_label": "Strict",
        "tooltip": "Higher = stricter consistency enforcement",
        "icon": "✓",
    },
    
    "user_model_fidelity": {
        "mapping": SemanticMapping.DIRECT,
        "display_name": "User Modeling Depth",
        "description": "Depth of psychological user modeling (Theory of Mind)",
        "low_label": "Generic",
        "mid_label": "Adaptive",
        "high_label": "Personalized",
        "tooltip": "Higher = deeper understanding of user preferences and patterns",
        "icon": "👤",
    },
    
    "transparency_level": {
        "mapping": SemanticMapping.DIRECT,
        "display_name": "Explanation Detail",
        "description": "How much internal reasoning to expose",
        "low_label": "Results Only",
        "mid_label": "Reasoning",
        "high_label": "Full Internals",
        "tooltip": "Higher = show more internal processing details",
        "icon": "🔍",
    },
    
    "explanation_depth": {
        "mapping": SemanticMapping.DIRECT,
        "display_name": "Explanation Verbosity",
        "description": "Granularity of reasoning explanations",
        "low_label": "Brief",
        "mid_label": "Moderate",
        "high_label": "Detailed",
        "tooltip": "Higher = more detailed step-by-step explanations",
        "icon": "📝",
    },
    
    "self_modification_freedom": {
        "mapping": SemanticMapping.DIRECT,
        "display_name": "Self-Modification",
        "description": "AI's ability to modify its own prompts/behavior",
        "low_label": "Static",
        "mid_label": "Limited",
        "high_label": "Adaptive",
        "tooltip": "⚠️ Higher = more autonomous self-modification (use with caution)",
        "icon": "⚙️",
        "warning": "Hard-stop at 0.5 for safety",
    },
    
    "goal_inference_autonomy": {
        "mapping": SemanticMapping.DIRECT,
        "display_name": "Proactive Goals",
        "description": "AI's ability to infer and pursue goals autonomously",
        "low_label": "Reactive",
        "mid_label": "Suggestive",
        "high_label": "Proactive",
        "tooltip": "⚠️ Higher = more autonomous goal formation (use with caution)",
        "icon": "🎯",
        "warning": "Hard-stop at 0.7 to prevent runaway",
    },
    
    "memory_consolidation_rate": {
        "mapping": SemanticMapping.DIRECT,
        "display_name": "Learning Speed",
        "description": "Speed of long-term self-model updates",
        "low_label": "Slow",
        "mid_label": "Moderate",
        "high_label": "Fast",
        "tooltip": "Higher = faster adaptation to patterns and feedback",
        "icon": "📚",
    },
}


def get_ui_value(dimension: str, backend_value: float) -> float:
    """
    Convert backend restraint value to UI presentation value.
    
    For inverted dimensions (like hallucination_resistance), this flips the scale
    so the UI is intuitive (higher = more creative, like temperature).
    
    Args:
        dimension: Restraint dimension name
        backend_value: Value from backend (0.0-1.0)
        
    Returns:
        UI presentation value (0.0-1.0)
    """
    semantics = RESTRAINT_SEMANTICS.get(dimension, {})
    mapping = semantics.get("mapping", SemanticMapping.DIRECT)
    
    if mapping == SemanticMapping.INVERTED:
        # Flip the scale: 0.8 backend → 0.2 UI (accuracy-first)
        #                 0.2 backend → 0.8 UI (creativity-first)
        return 1.0 - backend_value
    else:
        return backend_value


def get_backend_value(dimension: str, ui_value: float) -> float:
    """
    Convert UI presentation value back to backend storage value.
    
    Args:
        dimension: Restraint dimension name
        ui_value: Value from UI (0.0-1.0)
        
    Returns:
        Backend storage value (0.0-1.0)
    """
    semantics = RESTRAINT_SEMANTICS.get(dimension, {})
    mapping = semantics.get("mapping", SemanticMapping.DIRECT)
    
    if mapping == SemanticMapping.INVERTED:
        return 1.0 - ui_value
    else:
        return ui_value


def get_dimension_label(dimension: str, value: float) -> Tuple[str, str, str]:
    """
    Get human-readable label for a restraint value.
    
    Args:
        dimension: Restraint dimension name
        value: Current value (backend value, 0.0-1.0)
        
    Returns:
        Tuple of (display_name, current_label, description)
    """
    semantics = RESTRAINT_SEMANTICS.get(dimension, {})
    display_name = semantics.get("display_name", dimension.replace("_", " ").title())
    description = semantics.get("description", "")
    
    # Get UI value for label selection
    ui_value = get_ui_value(dimension, value)
    
    # Choose label based on value
    if ui_value < 0.33:
        label = semantics.get("low_label", "Low")
    elif ui_value < 0.67:
        label = semantics.get("mid_label", "Medium")
    else:
        label = semantics.get("high_label", "High")
    
    return (display_name, label, description)


def format_restraint_for_ui(dimension: str, backend_value: float) -> Dict[str, any]:
    """
    Format a restraint dimension for UI display.
    
    Args:
        dimension: Restraint dimension name
        backend_value: Current backend value (0.0-1.0)
        
    Returns:
        Dictionary with all UI presentation data
    """
    semantics = RESTRAINT_SEMANTICS.get(dimension, {})
    ui_value = get_ui_value(dimension, backend_value)
    display_name, label, description = get_dimension_label(dimension, backend_value)
    
    return {
        "dimension": dimension,
        "backend_value": backend_value,
        "ui_value": ui_value,
        "display_name": display_name,
        "description": description,
        "current_label": label,
        "low_label": semantics.get("low_label", "Low"),
        "mid_label": semantics.get("mid_label", "Medium"),
        "high_label": semantics.get("high_label", "High"),
        "tooltip": semantics.get("tooltip", description),
        "icon": semantics.get("icon", "⚙️"),
        "is_inverted": semantics.get("mapping") == SemanticMapping.INVERTED,
        "warning": semantics.get("warning"),
        "inverse_note": semantics.get("inverse_note"),
    }


# Example usage:
if __name__ == "__main__":
    # Backend stores hallucination_resistance = 0.8 (high resistance, cautious)
    # UI shows creativity = 0.2 (low creativity, accuracy-first)
    
    backend_val = 0.8
    ui_val = get_ui_value("hallucination_resistance", backend_val)
    print(f"Backend: hallucination_resistance = {backend_val}")
    print(f"UI: Creativity ↔ Accuracy = {ui_val} (Accuracy First)")
    
    # User adjusts slider to 0.7 (more creative)
    new_ui_val = 0.7
    new_backend_val = get_backend_value("hallucination_resistance", new_ui_val)
    print(f"\nUser moves slider to {new_ui_val} (more creative)")
    print(f"Backend receives: hallucination_resistance = {new_backend_val} (lower resistance)")
    
    # Show formatted data
    formatted = format_restraint_for_ui("hallucination_resistance", 0.8)
    print(f"\nFormatted for UI:")
    print(f"  Display: {formatted['display_name']}")
    print(f"  Value: {formatted['ui_value']:.1f} ({formatted['current_label']})")
    print(f"  Tooltip: {formatted['tooltip']}")
    print(f"  Inverted: {formatted['is_inverted']}")
