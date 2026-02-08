"""
Cognitive Digital Twin - Predictive Modeling Backend for RCL-2

Implements a digital twin that predicts cognitive system behavior:
- Response latency forecasting
- Memory pressure prediction
- Skill preloading optimization
- User engagement prediction
- Self-healing trigger detection

Uses simple statistical models (moving averages, exponential smoothing) with
confidence scoring and anomaly detection for production reliability.
"""

from __future__ import annotations

import logging
import os
import threading
import time
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple, Deque
from enum import Enum, auto

import numpy as np

logger = logging.getLogger("lollmsbot.cognitive_twin")


class PredictionType(Enum):
    """Types of predictions the cognitive twin can make."""
    LATENCY = auto()
    MEMORY_PRESSURE = auto()
    SKILL_USAGE = auto()
    ENGAGEMENT = auto()
    HEALING = auto()


@dataclass
class TimeSeriesData:
    """Time series data point with timestamp."""
    timestamp: float
    value: float
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PredictionResult:
    """Result of a prediction with confidence score."""
    prediction_type: PredictionType
    value: float
    confidence: float
    timestamp: float
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AnomalyDetection:
    """Anomaly detection result."""
    is_anomaly: bool
    z_score: float
    threshold: float
    value: float
    mean: float
    std: float


class LatencyPredictor:
    """Predicts response time for different operation types using exponential smoothing."""
    
    def __init__(self, history_size: int = 100, alpha: float = 0.3):
        self.history_size = history_size
        self.alpha = alpha  # Smoothing factor for exponential weighted average
        self.operation_history: Dict[str, Deque[TimeSeriesData]] = {}
        self.smoothed_values: Dict[str, float] = {}
        self.lock = threading.Lock()
    
    def record_latency(self, operation_type: str, duration_ms: float) -> None:
        """Record observed latency for an operation type."""
        with self.lock:
            if operation_type not in self.operation_history:
                self.operation_history[operation_type] = deque(maxlen=self.history_size)
                self.smoothed_values[operation_type] = duration_ms
            
            data = TimeSeriesData(timestamp=time.time(), value=duration_ms)
            self.operation_history[operation_type].append(data)
            
            # Update exponential moving average
            self.smoothed_values[operation_type] = (
                self.alpha * duration_ms + 
                (1 - self.alpha) * self.smoothed_values[operation_type]
            )
    
    def predict(self, operation_type: str) -> Tuple[float, float]:
        """
        Predict latency for an operation type.
        
        Returns:
            (predicted_latency_ms, confidence_score)
        """
        with self.lock:
            if operation_type not in self.operation_history:
                return (1000.0, 0.1)  # Default: 1 second, low confidence
            
            history = self.operation_history[operation_type]
            if len(history) < 3:
                return (self.smoothed_values[operation_type], 0.3)
            
            # Use exponential moving average as prediction
            prediction = self.smoothed_values[operation_type]
            
            # Calculate confidence based on stability (inverse of coefficient of variation)
            values = [d.value for d in history]
            mean = np.mean(values)
            std = np.std(values)
            
            if mean > 0:
                cv = std / mean  # Coefficient of variation
                confidence = max(0.0, min(1.0, 1.0 - cv))  # Lower CV = higher confidence
            else:
                confidence = 0.1
            
            return (prediction, confidence)


class MemoryPressureForecaster:
    """Forecasts when memory will be saturated using linear extrapolation."""
    
    def __init__(self, history_size: int = 100):
        self.history_size = history_size
        self.memory_history: Deque[TimeSeriesData] = deque(maxlen=history_size)
        self.lock = threading.Lock()
    
    def record_memory_usage(self, bytes_used: int) -> None:
        """Record current memory usage."""
        with self.lock:
            data = TimeSeriesData(
                timestamp=time.time(),
                value=float(bytes_used),
                metadata={"bytes": bytes_used}
            )
            self.memory_history.append(data)
    
    def predict(self, horizon_minutes: int = 30) -> Tuple[float, float]:
        """
        Predict memory pressure (0.0-1.0) at horizon.
        
        Args:
            horizon_minutes: How far into the future to predict
            
        Returns:
            (pressure_score_0_1, confidence_score)
        """
        with self.lock:
            if len(self.memory_history) < 5:
                return (0.2, 0.1)  # Default: low pressure, low confidence
            
            # Get recent trend using linear regression
            recent_data = list(self.memory_history)[-20:]  # Last 20 points
            times = np.array([d.timestamp for d in recent_data])
            values = np.array([d.value for d in recent_data])
            
            # Normalize time to start at 0
            times = times - times[0]
            
            # Simple linear regression
            if len(times) > 1:
                coeffs = np.polyfit(times, values, 1)
                slope, intercept = coeffs[0], coeffs[1]
                
                # Project into future
                future_time = times[-1] + (horizon_minutes * 60)
                predicted_bytes = slope * future_time + intercept
                
                # Convert to pressure score (0-1)
                # Assume 1GB is high pressure threshold
                max_bytes = 1024 * 1024 * 1024
                pressure = min(1.0, max(0.0, predicted_bytes / max_bytes))
                
                # Confidence based on R-squared
                y_mean = np.mean(values)
                ss_tot = np.sum((values - y_mean) ** 2)
                predictions = slope * times + intercept
                ss_res = np.sum((values - predictions) ** 2)
                
                r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0
                confidence = max(0.1, min(1.0, r_squared))
                
                return (pressure, confidence)
            
            # Fallback: use current level
            current_bytes = recent_data[-1].value
            pressure = min(1.0, max(0.0, current_bytes / (1024 * 1024 * 1024)))
            return (pressure, 0.3)


class SkillPreLoader:
    """Predicts which skills will be needed next using frequency and recency."""
    
    def __init__(self, history_size: int = 100):
        self.history_size = history_size
        self.skill_history: Deque[TimeSeriesData] = deque(maxlen=history_size)
        self.skill_frequencies: Dict[str, int] = {}
        self.lock = threading.Lock()
    
    def record_skill_usage(self, skill_name: str) -> None:
        """Record usage of a skill."""
        with self.lock:
            data = TimeSeriesData(
                timestamp=time.time(),
                value=1.0,
                metadata={"skill": skill_name}
            )
            self.skill_history.append(data)
            self.skill_frequencies[skill_name] = self.skill_frequencies.get(skill_name, 0) + 1
    
    def predict_next_skills(self, count: int = 5) -> List[Tuple[str, float]]:
        """
        Predict which skills will be used next.
        
        Args:
            count: Number of skills to predict
            
        Returns:
            List of (skill_name, probability) tuples
        """
        with self.lock:
            if not self.skill_history:
                return []
            
            # Score skills by recency-weighted frequency
            skill_scores: Dict[str, float] = {}
            current_time = time.time()
            
            for data in self.skill_history:
                skill = data.metadata.get("skill")
                if not skill:
                    continue
                
                # Exponential decay based on time
                age_seconds = current_time - data.timestamp
                recency_weight = np.exp(-age_seconds / 3600)  # Decay over 1 hour
                
                skill_scores[skill] = skill_scores.get(skill, 0.0) + recency_weight
            
            # Normalize to probabilities
            total_score = sum(skill_scores.values())
            if total_score > 0:
                skill_probs = {
                    skill: score / total_score 
                    for skill, score in skill_scores.items()
                }
            else:
                skill_probs = {}
            
            # Sort by probability and return top N
            sorted_skills = sorted(
                skill_probs.items(), 
                key=lambda x: x[1], 
                reverse=True
            )
            
            return sorted_skills[:count]


class EngagementPredictor:
    """Predicts user engagement/satisfaction using moving average."""
    
    def __init__(self, history_size: int = 100):
        self.history_size = history_size
        self.engagement_history: Deque[TimeSeriesData] = deque(maxlen=history_size)
        self.lock = threading.Lock()
    
    def record_engagement(self, engagement_score: float, context: Optional[Dict] = None) -> None:
        """Record user engagement score (0.0-1.0)."""
        with self.lock:
            data = TimeSeriesData(
                timestamp=time.time(),
                value=engagement_score,
                metadata=context or {}
            )
            self.engagement_history.append(data)
    
    def predict(self, context: Optional[Dict] = None) -> Tuple[float, float]:
        """
        Predict engagement score for given context.
        
        Returns:
            (engagement_score_0_1, confidence)
        """
        with self.lock:
            if len(self.engagement_history) < 3:
                return (0.5, 0.1)  # Default: neutral engagement, low confidence
            
            # Use weighted moving average with exponential decay
            recent_data = list(self.engagement_history)[-20:]
            weights = np.exp(np.linspace(-2, 0, len(recent_data)))
            values = np.array([d.value for d in recent_data])
            
            weighted_avg = np.average(values, weights=weights)
            
            # Confidence based on consistency
            std = np.std(values)
            confidence = max(0.1, min(1.0, 1.0 - std))
            
            return (weighted_avg, confidence)


class SelfHealingPredictor:
    """Predicts when self-healing should be triggered based on system health."""
    
    def __init__(self, anomaly_threshold: float = 3.0):
        self.anomaly_threshold = anomaly_threshold
        self.health_metrics: Dict[str, Deque[float]] = {
            "latency": deque(maxlen=50),
            "memory": deque(maxlen=50),
            "engagement": deque(maxlen=50),
            "error_rate": deque(maxlen=50)
        }
        self.lock = threading.Lock()
    
    def update_health_metric(self, metric_name: str, value: float) -> None:
        """Update a health metric."""
        with self.lock:
            if metric_name in self.health_metrics:
                self.health_metrics[metric_name].append(value)
    
    def detect_anomaly(self, metric_name: str, value: float) -> AnomalyDetection:
        """Detect if a value is anomalous using z-score."""
        with self.lock:
            history = self.health_metrics.get(metric_name, deque())
            
            if len(history) < 10:
                return AnomalyDetection(
                    is_anomaly=False,
                    z_score=0.0,
                    threshold=self.anomaly_threshold,
                    value=value,
                    mean=value,
                    std=0.0
                )
            
            values = np.array(list(history))
            mean = np.mean(values)
            std = np.std(values)
            
            if std > 0:
                z_score = abs((value - mean) / std)
            else:
                z_score = 0.0
            
            is_anomaly = z_score > self.anomaly_threshold
            
            return AnomalyDetection(
                is_anomaly=is_anomaly,
                z_score=z_score,
                threshold=self.anomaly_threshold,
                value=value,
                mean=mean,
                std=std
            )
    
    def should_trigger_healing(
        self, 
        latency_ms: float,
        memory_pressure: float,
        engagement: float
    ) -> Tuple[bool, str]:
        """
        Determine if self-healing should be triggered.
        
        Returns:
            (should_heal, reason)
        """
        reasons = []
        
        # Check latency
        if latency_ms > 5000:  # > 5 seconds
            reasons.append(f"High latency: {latency_ms:.0f}ms")
        
        latency_anomaly = self.detect_anomaly("latency", latency_ms)
        if latency_anomaly.is_anomaly:
            reasons.append(f"Latency anomaly detected (z={latency_anomaly.z_score:.2f})")
        
        # Check memory pressure
        if memory_pressure > 0.8:
            reasons.append(f"High memory pressure: {memory_pressure:.2f}")
        
        memory_anomaly = self.detect_anomaly("memory", memory_pressure)
        if memory_anomaly.is_anomaly:
            reasons.append(f"Memory anomaly detected (z={memory_anomaly.z_score:.2f})")
        
        # Check engagement
        if engagement < 0.3:
            reasons.append(f"Low engagement: {engagement:.2f}")
        
        engagement_anomaly = self.detect_anomaly("engagement", engagement)
        if engagement_anomaly.is_anomaly and engagement < 0.5:
            reasons.append(f"Engagement drop detected (z={engagement_anomaly.z_score:.2f})")
        
        should_heal = len(reasons) > 0
        reason_str = "; ".join(reasons) if reasons else "System healthy"
        
        return (should_heal, reason_str)


class CognitiveTwin:
    """
    Main cognitive digital twin for predictive modeling.
    
    Integrates all predictors and provides unified prediction interface.
    Thread-safe singleton accessible via get_cognitive_twin().
    """
    
    def __init__(
        self,
        enabled: bool = True,
        history_size: int = 100,
        confidence_threshold: float = 0.7,
        anomaly_threshold: float = 3.0
    ):
        self.enabled = enabled
        self.history_size = history_size
        self.confidence_threshold = confidence_threshold
        
        # Initialize predictors
        self.latency_predictor = LatencyPredictor(history_size)
        self.memory_forecaster = MemoryPressureForecaster(history_size)
        self.skill_preloader = SkillPreLoader(history_size)
        self.engagement_predictor = EngagementPredictor(history_size)
        self.healing_predictor = SelfHealingPredictor(anomaly_threshold)
        
        self.lock = threading.Lock()
        self.start_time = time.time()
        
        logger.info(
            f"CognitiveTwin initialized: enabled={enabled}, "
            f"history_size={history_size}, confidence_threshold={confidence_threshold}"
        )
    
    # === Recording Methods ===
    
    def record_latency(self, operation_type: str, duration_ms: float) -> None:
        """Record observed latency for an operation."""
        if not self.enabled:
            return
        self.latency_predictor.record_latency(operation_type, duration_ms)
        self.healing_predictor.update_health_metric("latency", duration_ms)
    
    def record_memory_usage(self, bytes_used: int) -> None:
        """Record current memory usage."""
        if not self.enabled:
            return
        self.memory_forecaster.record_memory_usage(bytes_used)
        pressure = bytes_used / (1024 * 1024 * 1024)  # Normalize to GB
        self.healing_predictor.update_health_metric("memory", pressure)
    
    def record_skill_usage(self, skill_name: str) -> None:
        """Record usage of a skill."""
        if not self.enabled:
            return
        self.skill_preloader.record_skill_usage(skill_name)
    
    def record_engagement(self, engagement_score: float, context: Optional[Dict] = None) -> None:
        """Record user engagement score."""
        if not self.enabled:
            return
        self.engagement_predictor.record_engagement(engagement_score, context)
        self.healing_predictor.update_health_metric("engagement", engagement_score)
    
    # === Prediction Methods ===
    
    def predict_latency(self, operation_type: str) -> Tuple[float, float]:
        """
        Predict latency for an operation type.
        
        Returns:
            (predicted_latency_ms, confidence_score)
        """
        if not self.enabled:
            return (1000.0, 0.0)
        return self.latency_predictor.predict(operation_type)
    
    def predict_memory_pressure(self, horizon_minutes: int = 30) -> Tuple[float, float]:
        """
        Predict memory pressure at time horizon.
        
        Returns:
            (pressure_0_1, confidence_score)
        """
        if not self.enabled:
            return (0.2, 0.0)
        return self.memory_forecaster.predict(horizon_minutes)
    
    def predict_next_skills(self, count: int = 5) -> List[Tuple[str, float]]:
        """
        Predict which skills will be used next.
        
        Returns:
            List of (skill_name, probability) tuples
        """
        if not self.enabled:
            return []
        return self.skill_preloader.predict_next_skills(count)
    
    def predict_engagement(self, context: Optional[Dict] = None) -> Tuple[float, float]:
        """
        Predict user engagement score.
        
        Returns:
            (engagement_0_1, confidence_score)
        """
        if not self.enabled:
            return (0.5, 0.0)
        return self.engagement_predictor.predict(context)
    
    def should_trigger_healing(self) -> Tuple[bool, str]:
        """
        Determine if self-healing should be triggered.
        
        Returns:
            (should_heal, reason)
        """
        if not self.enabled:
            return (False, "Cognitive twin disabled")
        
        # Get current predictions
        latency, _ = self.predict_latency("default")
        memory_pressure, _ = self.predict_memory_pressure()
        engagement, _ = self.predict_engagement()
        
        return self.healing_predictor.should_trigger_healing(
            latency, memory_pressure, engagement
        )
    
    # === Utility Methods ===
    
    def get_health_summary(self) -> Dict[str, Any]:
        """Get overall system health summary."""
        if not self.enabled:
            return {"enabled": False}
        
        latency, latency_conf = self.predict_latency("default")
        memory, memory_conf = self.predict_memory_pressure()
        engagement, engagement_conf = self.predict_engagement()
        should_heal, heal_reason = self.should_trigger_healing()
        next_skills = self.predict_next_skills(3)
        
        return {
            "enabled": True,
            "uptime_seconds": time.time() - self.start_time,
            "predictions": {
                "latency_ms": latency,
                "latency_confidence": latency_conf,
                "memory_pressure": memory,
                "memory_confidence": memory_conf,
                "engagement": engagement,
                "engagement_confidence": engagement_conf,
            },
            "next_skills": [
                {"skill": skill, "probability": prob}
                for skill, prob in next_skills
            ],
            "self_healing": {
                "should_trigger": should_heal,
                "reason": heal_reason
            }
        }


# === Singleton Pattern ===

_cognitive_twin_instance: Optional[CognitiveTwin] = None
_cognitive_twin_lock = threading.Lock()


def get_cognitive_twin() -> CognitiveTwin:
    """
    Get singleton instance of CognitiveTwin.
    
    Configuration from environment variables:
    - COGNITIVE_TWIN_ENABLED (default: true)
    - COGNITIVE_TWIN_HISTORY_SIZE (default: 100)
    - COGNITIVE_TWIN_CONFIDENCE_THRESHOLD (default: 0.7)
    - COGNITIVE_TWIN_ANOMALY_THRESHOLD (default: 3.0)
    """
    global _cognitive_twin_instance
    
    if _cognitive_twin_instance is None:
        with _cognitive_twin_lock:
            if _cognitive_twin_instance is None:
                # Load configuration from environment
                enabled = os.getenv("COGNITIVE_TWIN_ENABLED", "true").lower() == "true"
                history_size = int(os.getenv("COGNITIVE_TWIN_HISTORY_SIZE", "100"))
                confidence_threshold = float(os.getenv("COGNITIVE_TWIN_CONFIDENCE_THRESHOLD", "0.7"))
                anomaly_threshold = float(os.getenv("COGNITIVE_TWIN_ANOMALY_THRESHOLD", "3.0"))
                
                _cognitive_twin_instance = CognitiveTwin(
                    enabled=enabled,
                    history_size=history_size,
                    confidence_threshold=confidence_threshold,
                    anomaly_threshold=anomaly_threshold
                )
    
    return _cognitive_twin_instance
