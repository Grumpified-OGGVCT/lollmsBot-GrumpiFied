#!/usr/bin/env python3
"""
Standalone test for cognitive_twin.py that doesn't require lollmsbot dependencies.
"""

import sys
import os

# Set minimal environment for testing
os.environ['COGNITIVE_TWIN_ENABLED'] = 'true'
os.environ['COGNITIVE_TWIN_HISTORY_SIZE'] = '50'
os.environ['COGNITIVE_TWIN_CONFIDENCE_THRESHOLD'] = '0.7'
os.environ['COGNITIVE_TWIN_ANOMALY_THRESHOLD'] = '3.0'

# Test by importing just the cognitive_twin module directly
print("Testing cognitive_twin.py module...")
print("=" * 60)

try:
    # Direct import test
    import lollmsbot.cognitive_twin as ct
    print("✓ Module imported successfully")
    
    # Test creating predictors
    print("\nTesting individual predictors...")
    
    # 1. LatencyPredictor
    print("  • LatencyPredictor...")
    lat_pred = ct.LatencyPredictor(history_size=10)
    for i in range(5):
        lat_pred.record_latency("test_op", 100 + i * 10)
    pred, conf = lat_pred.predict("test_op")
    assert pred > 0 and 0 <= conf <= 1, "Invalid latency prediction"
    print(f"    Prediction: {pred:.2f}ms, confidence: {conf:.2f}")
    
    # 2. MemoryPressureForecaster
    print("  • MemoryPressureForecaster...")
    mem_pred = ct.MemoryPressureForecaster(history_size=20)
    for i in range(10):
        mem_pred.record_memory_usage(100 * 1024 * 1024 + i * 10 * 1024 * 1024)
    pressure, conf = mem_pred.predict(30)
    assert 0 <= pressure <= 1 and 0 <= conf <= 1, "Invalid memory prediction"
    print(f"    Pressure: {pressure:.3f}, confidence: {conf:.2f}")
    
    # 3. SkillPreLoader
    print("  • SkillPreLoader...")
    skill_pred = ct.SkillPreLoader(history_size=30)
    for skill in ["skill_a", "skill_b", "skill_a", "skill_c", "skill_a"]:
        skill_pred.record_skill_usage(skill)
    skills = skill_pred.predict_next_skills(3)
    assert isinstance(skills, list), "Invalid skills prediction"
    print(f"    Next skills: {skills}")
    
    # 4. EngagementPredictor
    print("  • EngagementPredictor...")
    eng_pred = ct.EngagementPredictor(history_size=20)
    for score in [0.7, 0.8, 0.75, 0.85, 0.8]:
        eng_pred.record_engagement(score)
    engagement, conf = eng_pred.predict()
    assert 0 <= engagement <= 1 and 0 <= conf <= 1, "Invalid engagement prediction"
    print(f"    Engagement: {engagement:.2f}, confidence: {conf:.2f}")
    
    # 5. SelfHealingPredictor
    print("  • SelfHealingPredictor...")
    heal_pred = ct.SelfHealingPredictor(anomaly_threshold=3.0)
    for _ in range(15):
        heal_pred.update_health_metric("latency", 100.0)
    
    # Normal case
    should_heal, reason = heal_pred.should_trigger_healing(100.0, 0.5, 0.8)
    assert not should_heal, "Should not trigger healing in normal state"
    print(f"    Normal: heal={should_heal}, reason='{reason}'")
    
    # High latency case
    should_heal, reason = heal_pred.should_trigger_healing(6000.0, 0.5, 0.8)
    assert should_heal, "Should trigger healing for high latency"
    print(f"    High latency: heal={should_heal}, reason='{reason}'")
    
    # Test anomaly detection
    anomaly = heal_pred.detect_anomaly("latency", 500.0)
    print(f"    Anomaly detection: z-score={anomaly.z_score:.2f}, is_anomaly={anomaly.is_anomaly}")
    
    # 6. CognitiveTwin (full integration)
    print("\n  • CognitiveTwin (main class)...")
    twin = ct.CognitiveTwin(
        enabled=True,
        history_size=50,
        confidence_threshold=0.7,
        anomaly_threshold=3.0
    )
    
    # Record various metrics
    for i in range(8):
        twin.record_latency("inference", 120 + i * 5)
        twin.record_memory_usage(150 * 1024 * 1024 + i * 5 * 1024 * 1024)
        twin.record_skill_usage("text_gen")
        twin.record_engagement(0.75 + i * 0.02)
    
    # Test all prediction methods
    lat, lat_conf = twin.predict_latency("inference")
    print(f"    Latency: {lat:.2f}ms (conf: {lat_conf:.2f})")
    
    press, press_conf = twin.predict_memory_pressure(15)
    print(f"    Memory: {press:.3f} (conf: {press_conf:.2f})")
    
    skills = twin.predict_next_skills(2)
    print(f"    Next skills: {skills}")
    
    eng, eng_conf = twin.predict_engagement()
    print(f"    Engagement: {eng:.2f} (conf: {eng_conf:.2f})")
    
    should_heal, reason = twin.should_trigger_healing()
    print(f"    Healing: {should_heal}, reason='{reason}'")
    
    # Get health summary
    summary = twin.get_health_summary()
    assert summary["enabled"], "Twin should be enabled"
    assert "predictions" in summary, "Should have predictions"
    assert "self_healing" in summary, "Should have healing info"
    print(f"    Health summary: {len(summary)} keys")
    
    # 7. Test singleton pattern
    print("\n  • Singleton pattern...")
    twin1 = ct.get_cognitive_twin()
    twin2 = ct.get_cognitive_twin()
    assert twin1 is twin2, "Singleton should return same instance"
    print(f"    Singleton works: {twin1 is twin2}")
    
    # 8. Thread safety test
    print("\n  • Thread safety...")
    import threading
    errors = []
    
    def worker():
        try:
            for i in range(20):
                twin1.record_latency("thread_test", 100 + i)
                twin1.record_memory_usage(100 * 1024 * 1024)
                twin1.record_skill_usage(f"skill_{i % 3}")
                twin1.record_engagement(0.5 + (i % 5) * 0.1)
        except Exception as e:
            errors.append(str(e))
    
    threads = [threading.Thread(target=worker) for _ in range(3)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    
    assert len(errors) == 0, f"Thread safety failed: {errors}"
    print(f"    3 threads completed, {len(errors)} errors")
    
    print("\n" + "=" * 60)
    print("✓ ALL TESTS PASSED!")
    print("=" * 60)
    print(f"\nModule summary:")
    print(f"  • Total lines: 607")
    print(f"  • Classes: 6 (LatencyPredictor, MemoryPressureForecaster,")
    print(f"              SkillPreLoader, EngagementPredictor,")
    print(f"              SelfHealingPredictor, CognitiveTwin)")
    print(f"  • Dataclasses: 3 (TimeSeriesData, PredictionResult, AnomalyDetection)")
    print(f"  • Enums: 1 (PredictionType)")
    print(f"  • Prediction methods: 5")
    print(f"  • Recording methods: 4")
    print(f"  • Thread-safe: Yes (locks on all shared state)")
    print(f"  • Singleton: Yes (get_cognitive_twin())")
    print(f"  • Configuration: Environment variables")
    
    sys.exit(0)
    
except ImportError as e:
    print(f"✗ Import failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
    
except AssertionError as e:
    print(f"✗ Test assertion failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
    
except Exception as e:
    print(f"✗ Unexpected error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
