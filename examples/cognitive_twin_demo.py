#!/usr/bin/env python3
"""
Example demonstrating Cognitive Digital Twin integration with RCL-2.

Shows how the predictive model works with cognitive core and self-awareness.
"""

import time
import psutil
from lollmsbot.cognitive_twin import get_cognitive_twin


def simulate_system_operations():
    """Simulate system operations and predictions."""
    print("=" * 70)
    print("Cognitive Digital Twin - Integration Demo")
    print("=" * 70)
    
    twin = get_cognitive_twin()
    print(f"\n✓ Cognitive Twin initialized: enabled={twin.enabled}")
    
    # Simulate 20 operations with varying characteristics
    print("\n📊 Simulating 20 operations...")
    
    for i in range(20):
        # Simulate different operation types
        if i % 3 == 0:
            op_type = "inference"
            latency = 100 + i * 5 + (i % 7) * 10  # Increasing with noise
        elif i % 3 == 1:
            op_type = "skill_execution"
            latency = 150 + i * 3
        else:
            op_type = "memory_retrieval"
            latency = 50 + i * 2
        
        # Record latency
        twin.record_latency(op_type, latency)
        
        # Simulate memory usage
        process = psutil.Process()
        memory_bytes = process.memory_info().rss + i * 1024 * 1024  # Simulate growth
        twin.record_memory_usage(memory_bytes)
        
        # Simulate skill usage
        skills = ["text_gen", "code_gen", "search", "summarize"]
        skill = skills[i % len(skills)]
        twin.record_skill_usage(skill)
        
        # Simulate engagement (slightly decreasing over time)
        engagement = 0.9 - (i * 0.02) + ((i % 5) * 0.05)
        engagement = max(0.1, min(1.0, engagement))
        twin.record_engagement(engagement, context={"iteration": i})
        
        time.sleep(0.01)  # Small delay
    
    print("✓ Recorded 20 operations\n")
    
    # Make predictions
    print("🔮 Making Predictions...")
    print("-" * 70)
    
    # 1. Latency predictions
    print("\n1. LATENCY PREDICTIONS:")
    for op_type in ["inference", "skill_execution", "memory_retrieval"]:
        latency, conf = twin.predict_latency(op_type)
        status = "✅ High" if conf >= 0.7 else "⚠️  Low"
        print(f"   {op_type:20s}: {latency:6.2f}ms  (confidence: {conf:.2f} {status})")
    
    # 2. Memory pressure forecast
    print("\n2. MEMORY PRESSURE FORECAST:")
    for horizon in [15, 30, 60]:
        pressure, conf = twin.predict_memory_pressure(horizon)
        if pressure > 0.8:
            status = "🔴 Critical"
        elif pressure > 0.6:
            status = "🟡 Warning"
        else:
            status = "🟢 Normal"
        print(f"   {horizon:3d} minutes: {pressure:5.3f}  (confidence: {conf:.2f}) {status}")
    
    # 3. Skill predictions
    print("\n3. SKILL PRELOADING RECOMMENDATIONS:")
    skills = twin.predict_next_skills(5)
    for i, (skill, prob) in enumerate(skills, 1):
        bar_length = int(prob * 30)
        bar = "█" * bar_length + "░" * (30 - bar_length)
        print(f"   {i}. {skill:15s} {bar} {prob:.1%}")
    
    # 4. Engagement prediction
    print("\n4. USER ENGAGEMENT PREDICTION:")
    engagement, conf = twin.predict_engagement()
    if engagement < 0.4:
        status = "🔴 Low - Action Needed"
    elif engagement < 0.7:
        status = "🟡 Medium"
    else:
        status = "🟢 High"
    print(f"   Score: {engagement:.2f}  (confidence: {conf:.2f}) {status}")
    
    # 5. Self-healing check
    print("\n5. SELF-HEALING STATUS:")
    should_heal, reason = twin.should_trigger_healing()
    if should_heal:
        print(f"   🚨 HEALING RECOMMENDED")
        print(f"   Reason: {reason}")
    else:
        print(f"   ✅ System Healthy")
        print(f"   Status: {reason}")
    
    # 6. Comprehensive health summary
    print("\n6. SYSTEM HEALTH SUMMARY:")
    print("-" * 70)
    health = twin.get_health_summary()
    
    print(f"   Uptime: {health['uptime_seconds']:.1f}s")
    print(f"   Predictions:")
    for key, value in health['predictions'].items():
        if isinstance(value, float):
            print(f"     • {key:25s}: {value:8.3f}")
    
    print(f"\n   Next Skills:")
    for skill_info in health['next_skills'][:3]:
        print(f"     • {skill_info['skill']:15s}: {skill_info['probability']:.1%}")
    
    print(f"\n   Self-Healing:")
    print(f"     • Should Trigger: {health['self_healing']['should_trigger']}")
    print(f"     • Reason: {health['self_healing']['reason']}")
    
    print("\n" + "=" * 70)
    print("✓ Demo Complete - Cognitive Twin is fully operational!")
    print("=" * 70)


def demonstrate_anomaly_detection():
    """Demonstrate anomaly detection capabilities."""
    print("\n\n" + "=" * 70)
    print("Anomaly Detection Demo")
    print("=" * 70)
    
    twin = get_cognitive_twin()
    
    # Establish baseline
    print("\n📈 Establishing baseline (20 normal operations)...")
    for i in range(20):
        twin.record_latency("test_op", 100.0 + (i % 5) * 2)
        time.sleep(0.01)
    
    latency, conf = twin.predict_latency("test_op")
    print(f"✓ Baseline: {latency:.2f}ms (confidence: {conf:.2f})")
    
    # Introduce anomaly
    print("\n⚠️  Introducing anomaly (latency spike to 500ms)...")
    twin.record_latency("test_op", 500.0)
    
    # Check for healing trigger
    should_heal, reason = twin.should_trigger_healing()
    if should_heal:
        print(f"✅ Anomaly detected! Self-healing triggered:")
        print(f"   Reason: {reason}")
    else:
        print(f"ℹ️  No trigger (reason: {reason})")
    
    print("\n" + "=" * 70)


if __name__ == "__main__":
    try:
        # Main demo
        simulate_system_operations()
        
        # Anomaly detection demo
        demonstrate_anomaly_detection()
        
        print("\n✨ All demos completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
