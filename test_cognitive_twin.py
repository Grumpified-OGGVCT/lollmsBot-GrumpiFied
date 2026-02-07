#!/usr/bin/env python3
"""
Test suite for Cognitive Digital Twin (Phase 2C).

Validates all predictors and integration points.
"""

import time
import sys
from pathlib import Path

# Add lollmsbot to path
sys.path.insert(0, str(Path(__file__).parent))

from lollmsbot.cognitive_twin import (
    get_cognitive_twin,
    LatencyPredictor,
    MemoryPressureForecaster,
    SkillPreLoader,
    EngagementPredictor,
    SelfHealingPredictor,
    AnomalyDetection,
    PredictionType
)


def test_latency_predictor():
    """Test latency prediction with exponential smoothing."""
    print("\n=== Testing LatencyPredictor ===")
    
    predictor = LatencyPredictor(history_size=10)
    
    # Record some latencies
    for i in range(10):
        latency = 100 + i * 10  # Increasing latency
        predictor.record_latency("api_call", latency)
    
    # Predict
    predicted, confidence = predictor.predict("api_call")
    print(f"Predicted latency: {predicted:.2f}ms (confidence: {confidence:.2f})")
    
    # Test unknown operation
    unknown_pred, unknown_conf = predictor.predict("unknown_op")
    print(f"Unknown operation: {unknown_pred:.2f}ms (confidence: {unknown_conf:.2f})")
    
    assert predicted > 100, "Prediction should reflect increasing trend"
    assert 0 <= confidence <= 1, "Confidence should be in [0, 1]"
    assert unknown_conf < 0.5, "Unknown operation should have low confidence"
    
    print("✓ LatencyPredictor passed")


def test_memory_forecaster():
    """Test memory pressure forecasting with linear extrapolation."""
    print("\n=== Testing MemoryPressureForecaster ===")
    
    forecaster = MemoryPressureForecaster(history_size=20)
    
    # Simulate increasing memory usage
    base_memory = 100 * 1024 * 1024  # 100 MB
    for i in range(15):
        memory = base_memory + (i * 10 * 1024 * 1024)  # +10 MB each time
        forecaster.record_memory_usage(memory)
        time.sleep(0.01)  # Small delay to simulate time progression
    
    # Predict 30 minutes ahead
    pressure, confidence = forecaster.predict(horizon_minutes=30)
    print(f"Predicted pressure (30 min): {pressure:.3f} (confidence: {confidence:.2f})")
    
    assert 0 <= pressure <= 1, "Pressure should be in [0, 1]"
    assert 0 <= confidence <= 1, "Confidence should be in [0, 1]"
    
    print("✓ MemoryPressureForecaster passed")


def test_skill_preloader():
    """Test skill usage prediction with recency weighting."""
    print("\n=== Testing SkillPreLoader ===")
    
    preloader = SkillPreLoader(history_size=50)
    
    # Record skill usage with patterns
    skills = ["skill_a", "skill_b", "skill_c", "skill_a", "skill_a"]
    for skill in skills:
        preloader.record_skill_usage(skill)
        time.sleep(0.01)
    
    # Predict next skills
    predictions = preloader.predict_next_skills(count=3)
    print(f"Predicted next skills: {predictions}")
    
    assert len(predictions) <= 3, "Should return at most 3 predictions"
    if predictions:
        top_skill, top_prob = predictions[0]
        assert top_skill == "skill_a", "Most frequent recent skill should be first"
        assert 0 <= top_prob <= 1, "Probability should be in [0, 1]"
    
    print("✓ SkillPreLoader passed")


def test_engagement_predictor():
    """Test engagement prediction with weighted moving average."""
    print("\n=== Testing EngagementPredictor ===")
    
    predictor = EngagementPredictor(history_size=20)
    
    # Record engagement scores
    scores = [0.8, 0.7, 0.75, 0.85, 0.9, 0.8]
    for score in scores:
        predictor.record_engagement(score, context={"test": True})
        time.sleep(0.01)
    
    # Predict
    predicted, confidence = predictor.predict()
    print(f"Predicted engagement: {predicted:.2f} (confidence: {confidence:.2f})")
    
    assert 0 <= predicted <= 1, "Engagement should be in [0, 1]"
    assert 0 <= confidence <= 1, "Confidence should be in [0, 1]"
    assert predicted > 0.7, "Should reflect high engagement pattern"
    
    print("✓ EngagementPredictor passed")


def test_healing_predictor():
    """Test self-healing trigger detection."""
    print("\n=== Testing SelfHealingPredictor ===")
    
    predictor = SelfHealingPredictor(anomaly_threshold=3.0)
    
    # Record normal metrics
    for _ in range(20):
        predictor.update_health_metric("latency", 100.0)
    
    # Check normal state
    should_heal, reason = predictor.should_trigger_healing(
        latency_ms=100.0,
        memory_pressure=0.5,
        engagement=0.8
    )
    print(f"Normal state - Heal: {should_heal}, Reason: {reason}")
    assert not should_heal, "Should not trigger healing in normal state"
    
    # Test anomaly detection
    anomaly = predictor.detect_anomaly("latency", 500.0)  # Spike
    print(f"Anomaly detection - Is anomaly: {anomaly.is_anomaly}, Z-score: {anomaly.z_score:.2f}")
    
    # Test high latency trigger
    should_heal, reason = predictor.should_trigger_healing(
        latency_ms=6000.0,  # > 5 seconds
        memory_pressure=0.5,
        engagement=0.8
    )
    print(f"High latency - Heal: {should_heal}, Reason: {reason}")
    assert should_heal, "Should trigger healing for high latency"
    
    # Test high memory pressure
    should_heal, reason = predictor.should_trigger_healing(
        latency_ms=100.0,
        memory_pressure=0.9,  # > 0.8
        engagement=0.8
    )
    print(f"High memory - Heal: {should_heal}, Reason: {reason}")
    assert should_heal, "Should trigger healing for high memory pressure"
    
    # Test low engagement
    should_heal, reason = predictor.should_trigger_healing(
        latency_ms=100.0,
        memory_pressure=0.5,
        engagement=0.2  # < 0.3
    )
    print(f"Low engagement - Heal: {should_heal}, Reason: {reason}")
    assert should_heal, "Should trigger healing for low engagement"
    
    print("✓ SelfHealingPredictor passed")


def test_cognitive_twin_integration():
    """Test full CognitiveTwin integration."""
    print("\n=== Testing CognitiveTwin Integration ===")
    
    twin = get_cognitive_twin()
    
    # Record various metrics
    print("Recording metrics...")
    for i in range(10):
        twin.record_latency("inference", 150 + i * 10)
        twin.record_memory_usage(200 * 1024 * 1024 + i * 10 * 1024 * 1024)
        twin.record_skill_usage("text_generation")
        twin.record_engagement(0.7 + i * 0.02)
        time.sleep(0.01)
    
    # Test predictions
    print("\nTesting predictions...")
    
    latency, lat_conf = twin.predict_latency("inference")
    print(f"Latency prediction: {latency:.2f}ms (confidence: {lat_conf:.2f})")
    assert latency > 0, "Should predict positive latency"
    
    pressure, press_conf = twin.predict_memory_pressure(horizon_minutes=15)
    print(f"Memory pressure: {pressure:.3f} (confidence: {press_conf:.2f})")
    assert 0 <= pressure <= 1, "Pressure should be in [0, 1]"
    
    skills = twin.predict_next_skills(count=3)
    print(f"Next skills: {skills}")
    assert "text_generation" in [s[0] for s in skills], "Should predict recent skill"
    
    engagement, eng_conf = twin.predict_engagement()
    print(f"Engagement: {engagement:.2f} (confidence: {eng_conf:.2f})")
    assert engagement > 0.5, "Should predict high engagement"
    
    should_heal, heal_reason = twin.should_trigger_healing()
    print(f"Should heal: {should_heal}, Reason: {heal_reason}")
    
    # Get health summary
    summary = twin.get_health_summary()
    print(f"\nHealth Summary:")
    print(f"  Uptime: {summary['uptime_seconds']:.2f}s")
    print(f"  Predictions: {summary['predictions']}")
    print(f"  Next skills: {summary['next_skills']}")
    print(f"  Self-healing: {summary['self_healing']}")
    
    assert summary["enabled"], "Twin should be enabled"
    assert "predictions" in summary, "Should have predictions"
    
    print("✓ CognitiveTwin integration passed")


def test_singleton_pattern():
    """Test that get_cognitive_twin returns the same instance."""
    print("\n=== Testing Singleton Pattern ===")
    
    twin1 = get_cognitive_twin()
    twin2 = get_cognitive_twin()
    
    assert twin1 is twin2, "Should return same instance"
    print("✓ Singleton pattern works correctly")


def test_thread_safety():
    """Basic thread safety test."""
    print("\n=== Testing Thread Safety ===")
    
    import threading
    
    twin = get_cognitive_twin()
    errors = []
    
    def record_data():
        try:
            for i in range(50):
                twin.record_latency("test_op", 100 + i)
                twin.record_memory_usage(100 * 1024 * 1024 + i * 1024)
                twin.record_skill_usage(f"skill_{i % 3}")
                twin.record_engagement(0.5 + (i % 10) * 0.05)
        except Exception as e:
            errors.append(e)
    
    # Run 5 threads concurrently
    threads = [threading.Thread(target=record_data) for _ in range(5)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    
    assert len(errors) == 0, f"Thread safety errors: {errors}"
    print("✓ Thread safety test passed")


def main():
    """Run all tests."""
    print("=" * 60)
    print("Cognitive Digital Twin Test Suite")
    print("=" * 60)
    
    try:
        test_latency_predictor()
        test_memory_forecaster()
        test_skill_preloader()
        test_engagement_predictor()
        test_healing_predictor()
        test_cognitive_twin_integration()
        test_singleton_pattern()
        test_thread_safety()
        
        print("\n" + "=" * 60)
        print("✓ ALL TESTS PASSED!")
        print("=" * 60)
        return 0
        
    except AssertionError as e:
        print(f"\n✗ Test failed: {e}")
        return 1
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
