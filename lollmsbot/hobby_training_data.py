"""
Phase 3B: LoRA Training Data Extraction

This module extracts insights from hobby activities and converts them into 
training data suitable for fine-tuning language models via LoRA adapters.
"""

import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum

logger = logging.getLogger(__name__)


class DataQuality(str, Enum):
    """Quality levels for training data"""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    FILTERED = "filtered"


@dataclass
class TrainingExample:
    """Single training example extracted from hobby insights"""
    example_id: str
    hobby_type: str
    instruction: str
    input_context: str
    expected_output: str
    quality_score: float
    metadata: Dict[str, Any]
    created_at: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)
    
    def to_alpaca_format(self) -> Dict[str, str]:
        """Convert to Alpaca instruction format"""
        return {
            "instruction": self.instruction,
            "input": self.input_context,
            "output": self.expected_output
        }
    
    def to_sharegpt_format(self) -> Dict[str, Any]:
        """Convert to ShareGPT format"""
        return {
            "conversations": [
                {"from": "human", "value": self.instruction + "\n\n" + self.input_context},
                {"from": "gpt", "value": self.expected_output}
            ]
        }


class TrainingDataExtractor:
    """Extracts and formats training data from hobby activities"""
    
    def __init__(self, min_quality_score: float = 0.6):
        """
        Initialize extractor
        
        Args:
            min_quality_score: Minimum quality score to include (0.0-1.0)
        """
        self.min_quality_score = min_quality_score
        self.examples: List[TrainingExample] = []
        self._example_counter = 0
        
    def extract_from_activities(self, activities: List[Dict[str, Any]]) -> List[TrainingExample]:
        """
        Extract training examples from hobby activities
        
        Args:
            activities: List of hobby activity dictionaries
            
        Returns:
            List of training examples
        """
        examples = []
        
        for activity in activities:
            try:
                activity_examples = self._extract_from_activity(activity)
                examples.extend(activity_examples)
            except Exception as e:
                logger.warning(f"Failed to extract from activity: {e}")
                continue
        
        # Filter by quality
        filtered = [ex for ex in examples if ex.quality_score >= self.min_quality_score]
        
        logger.info(f"Extracted {len(examples)} examples, {len(filtered)} passed quality filter")
        self.examples.extend(filtered)
        
        return filtered
    
    def _extract_from_activity(self, activity: Dict[str, Any]) -> List[TrainingExample]:
        """Extract examples from a single activity"""
        examples = []
        hobby_type = activity.get("hobby_type", "UNKNOWN")
        insights = activity.get("insights_gained", [])
        patterns = activity.get("patterns_discovered", [])
        goal = activity.get("goal", "")
        approach = activity.get("approach", "")
        
        # Extract from insights
        for insight in insights:
            example = self._create_example_from_insight(
                hobby_type, insight, goal, approach, activity
            )
            if example:
                examples.append(example)
        
        # Extract from patterns
        for pattern in patterns:
            example = self._create_example_from_pattern(
                hobby_type, pattern, goal, approach, activity
            )
            if example:
                examples.append(example)
        
        return examples
    
    def _create_example_from_insight(
        self, 
        hobby_type: str, 
        insight: str, 
        goal: str, 
        approach: str,
        activity: Dict[str, Any]
    ) -> Optional[TrainingExample]:
        """Create training example from an insight"""
        
        # Generate instruction based on hobby type
        instruction = self._generate_instruction(hobby_type, "insight")
        
        # Context includes goal and approach
        input_context = f"Goal: {goal}\nApproach: {approach}"
        
        # Output is the insight
        expected_output = insight
        
        # Quality score based on length and content
        quality_score = self._calculate_quality_score(insight, activity)
        
        self._example_counter += 1
        return TrainingExample(
            example_id=f"insight_{self._example_counter}_{datetime.now().timestamp()}",
            hobby_type=hobby_type,
            instruction=instruction,
            input_context=input_context,
            expected_output=expected_output,
            quality_score=quality_score,
            metadata={
                "source": "insight",
                "activity_started_at": activity.get("started_at"),
                "difficulty": activity.get("difficulty_level", 0.5)
            },
            created_at=datetime.now().isoformat()
        )
    
    def _create_example_from_pattern(
        self,
        hobby_type: str,
        pattern: str,
        goal: str,
        approach: str,
        activity: Dict[str, Any]
    ) -> Optional[TrainingExample]:
        """Create training example from a pattern"""
        
        instruction = self._generate_instruction(hobby_type, "pattern")
        input_context = f"Goal: {goal}\nApproach: {approach}"
        expected_output = pattern
        
        quality_score = self._calculate_quality_score(pattern, activity)
        
        self._example_counter += 1
        return TrainingExample(
            example_id=f"pattern_{self._example_counter}_{datetime.now().timestamp()}",
            hobby_type=hobby_type,
            instruction=instruction,
            input_context=input_context,
            expected_output=expected_output,
            quality_score=quality_score,
            metadata={
                "source": "pattern",
                "activity_started_at": activity.get("started_at"),
                "difficulty": activity.get("difficulty_level", 0.5)
            },
            created_at=datetime.now().isoformat()
        )
    
    def _generate_instruction(self, hobby_type: str, source_type: str) -> str:
        """Generate appropriate instruction for the hobby type"""
        
        instructions = {
            "SKILL_PRACTICE": {
                "insight": "Based on the following coding practice session, what key insight was gained?",
                "pattern": "Based on the following practice, what pattern was discovered?"
            },
            "KNOWLEDGE_EXPLORATION": {
                "insight": "After exploring this knowledge domain, what was the key learning?",
                "pattern": "What conceptual pattern emerged from this exploration?"
            },
            "PATTERN_RECOGNITION": {
                "insight": "What insight was derived from analyzing these patterns?",
                "pattern": "Describe the pattern identified in this analysis."
            },
            "BENCHMARK_PRACTICE": {
                "insight": "What insight was gained from this benchmark practice?",
                "pattern": "What performance pattern was observed?"
            },
            "TOOL_MASTERY": {
                "insight": "What insight was learned about using this tool effectively?",
                "pattern": "What usage pattern was discovered for this tool?"
            },
            "CODE_ANALYSIS": {
                "insight": "What insight was gained from analyzing this code?",
                "pattern": "What code pattern was identified?"
            },
            "RESEARCH_INTEGRATION": {
                "insight": "What key insight was derived from this research?",
                "pattern": "What research pattern or trend was identified?"
            },
            "CREATIVE_PROBLEM_SOLVING": {
                "insight": "What insight emerged from this creative problem-solving session?",
                "pattern": "What problem-solving pattern was discovered?"
            }
        }
        
        return instructions.get(hobby_type, {}).get(
            source_type,
            f"What {source_type} was gained from this learning activity?"
        )
    
    def _calculate_quality_score(self, text: str, activity: Dict[str, Any]) -> float:
        """
        Calculate quality score for a training example
        
        Factors:
        - Text length (prefer substantial content)
        - Activity success
        - Difficulty level
        - Insights count
        """
        score = 0.5  # Base score
        
        # Length factor (10-200 chars is ideal)
        text_len = len(text)
        if 50 <= text_len <= 200:
            score += 0.2
        elif 200 < text_len <= 500:
            score += 0.15
        elif text_len < 20:
            score -= 0.2
        
        # Success factor
        if activity.get("status") == "completed":
            score += 0.15
        
        # Difficulty factor (harder = better training data)
        difficulty = activity.get("difficulty_level", 0.5)
        score += difficulty * 0.1
        
        # Insights count factor
        insights_count = len(activity.get("insights_gained", []))
        if insights_count > 3:
            score += 0.05
        
        return min(1.0, max(0.0, score))
    
    def deduplicate(self, examples: Optional[List[TrainingExample]] = None) -> List[TrainingExample]:
        """
        Remove duplicate examples based on content similarity
        
        Args:
            examples: List to deduplicate, or None to use self.examples
            
        Returns:
            Deduplicated list
        """
        if examples is None:
            examples = self.examples
        
        unique = []
        seen_outputs = set()
        
        for example in examples:
            # Simple deduplication based on exact output match
            output_key = example.expected_output.lower().strip()
            if output_key not in seen_outputs:
                seen_outputs.add(output_key)
                unique.append(example)
        
        logger.info(f"Deduplicated {len(examples)} -> {len(unique)} examples")
        return unique
    
    def split_dataset(
        self, 
        examples: Optional[List[TrainingExample]] = None,
        train_ratio: float = 0.8,
        val_ratio: float = 0.1,
        test_ratio: float = 0.1
    ) -> Tuple[List[TrainingExample], List[TrainingExample], List[TrainingExample]]:
        """
        Split examples into train/validation/test sets
        
        Args:
            examples: Examples to split, or None to use self.examples
            train_ratio: Fraction for training (default 0.8)
            val_ratio: Fraction for validation (default 0.1)
            test_ratio: Fraction for testing (default 0.1)
            
        Returns:
            Tuple of (train, val, test) example lists
        """
        if examples is None:
            examples = self.examples
        
        # Shuffle examples (deterministic based on ID)
        sorted_examples = sorted(examples, key=lambda x: x.example_id)
        
        n = len(sorted_examples)
        train_end = int(n * train_ratio)
        val_end = train_end + int(n * val_ratio)
        
        train = sorted_examples[:train_end]
        val = sorted_examples[train_end:val_end]
        test = sorted_examples[val_end:]
        
        logger.info(f"Split dataset: {len(train)} train, {len(val)} val, {len(test)} test")
        return train, val, test
    
    def export_to_json(
        self, 
        examples: List[TrainingExample],
        output_path: Path,
        format_type: str = "alpaca"
    ) -> None:
        """
        Export examples to JSON file
        
        Args:
            examples: Examples to export
            output_path: Output file path
            format_type: Format ("alpaca", "sharegpt", or "raw")
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        if format_type == "alpaca":
            data = [ex.to_alpaca_format() for ex in examples]
        elif format_type == "sharegpt":
            data = [ex.to_sharegpt_format() for ex in examples]
        else:
            data = [ex.to_dict() for ex in examples]
        
        with open(output_path, 'w') as f:
            json.dump(data, f, indent=2)
        
        logger.info(f"Exported {len(examples)} examples to {output_path} ({format_type} format)")
    
    def get_statistics(self, examples: Optional[List[TrainingExample]] = None) -> Dict[str, Any]:
        """Get statistics about the training data"""
        if examples is None:
            examples = self.examples
        
        if not examples:
            return {"total": 0}
        
        # Count by hobby type
        by_hobby = {}
        quality_scores = []
        
        for ex in examples:
            by_hobby[ex.hobby_type] = by_hobby.get(ex.hobby_type, 0) + 1
            quality_scores.append(ex.quality_score)
        
        return {
            "total": len(examples),
            "by_hobby_type": by_hobby,
            "quality": {
                "mean": sum(quality_scores) / len(quality_scores),
                "min": min(quality_scores),
                "max": max(quality_scores)
            },
            "unique_hobbies": len(by_hobby)
        }


def extract_training_data_from_manager(
    hobby_manager,
    days_back: int = 30,
    min_quality: float = 0.6
) -> Tuple[List[TrainingExample], Dict[str, Any]]:
    """
    Convenience function to extract training data from HobbyManager
    
    Args:
        hobby_manager: HobbyManager instance
        days_back: Number of days of activity history to use
        min_quality: Minimum quality score
        
    Returns:
        Tuple of (examples, statistics)
    """
    extractor = TrainingDataExtractor(min_quality_score=min_quality)
    
    # Get recent activities
    activities = hobby_manager.get_recent_activities(count=1000)
    
    # Filter by date if needed
    cutoff_date = datetime.now() - timedelta(days=days_back)
    recent_activities = [
        act for act in activities
        if datetime.fromisoformat(act.get("started_at", "2000-01-01")) > cutoff_date
    ]
    
    # Extract examples
    examples = extractor.extract_from_activities(recent_activities)
    
    # Deduplicate
    examples = extractor.deduplicate(examples)
    
    # Get stats
    stats = extractor.get_statistics(examples)
    
    return examples, stats
