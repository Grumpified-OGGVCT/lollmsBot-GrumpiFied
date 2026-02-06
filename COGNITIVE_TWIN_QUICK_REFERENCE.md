# Cognitive Digital Twin - Quick Reference

## Import and Initialize

```python
from lollmsbot.cognitive_twin import get_cognitive_twin

# Get singleton instance (auto-configured from environment)
twin = get_cognitive_twin()
```

## Recording Metrics

```python
# Record operation latency
twin.record_latency("operation_type", duration_ms=145.5)

# Record memory usage
twin.record_memory_usage(bytes_used=250 * 1024 * 1024)

# Record skill usage
twin.record_skill_usage(skill_name="text_generation")

# Record user engagement
twin.record_engagement(engagement_score=0.85, context={"page": "home"})
```

## Making Predictions

```python
# Predict latency (returns: latency_ms, confidence)
latency, conf = twin.predict_latency("operation_type")

# Predict memory pressure (returns: pressure_0_1, confidence)
pressure, conf = twin.predict_memory_pressure(horizon_minutes=30)

# Predict next skills (returns: [(skill, probability), ...])
skills = twin.predict_next_skills(count=5)

# Predict engagement (returns: engagement_0_1, confidence)
engagement, conf = twin.predict_engagement()

# Check self-healing (returns: should_heal, reason)
should_heal, reason = twin.should_trigger_healing()
```

## Health Summary

```python
# Get comprehensive health report
health = twin.get_health_summary()

print(f"Uptime: {health['uptime_seconds']}s")
print(f"Predictions: {health['predictions']}")
print(f"Next skills: {health['next_skills']}")
print(f"Should heal: {health['self_healing']['should_trigger']}")
```

## REST API Endpoints

```bash
# Get health summary
GET /rcl2/cognitive-twin/health

# Predict latency
GET /rcl2/cognitive-twin/predict/latency?operation_type=inference

# Predict memory pressure
GET /rcl2/cognitive-twin/predict/memory?horizon_minutes=30

# Predict next skills
GET /rcl2/cognitive-twin/predict/skills?count=5

# Predict engagement
GET /rcl2/cognitive-twin/predict/engagement

# Check self-healing
GET /rcl2/cognitive-twin/healing

# Record metric
POST /rcl2/cognitive-twin/record
{
  "metric_type": "latency",
  "operation_type": "api_call",
  "duration_ms": 145.5
}
```

## Configuration

```bash
# .env file
COGNITIVE_TWIN_ENABLED=true
COGNITIVE_TWIN_HISTORY_SIZE=100
COGNITIVE_TWIN_CONFIDENCE_THRESHOLD=0.7
COGNITIVE_TWIN_ANOMALY_THRESHOLD=3.0
```

## Self-Healing Triggers

The system automatically triggers healing when:
- Predicted latency > 5000ms
- Memory pressure > 0.8
- Engagement < 0.3
- Anomalies detected (z-score > threshold)

## Confidence Scores

- **< 0.3:** Low confidence (insufficient data)
- **0.3 - 0.7:** Medium confidence
- **> 0.7:** High confidence (reliable prediction)

## Thread Safety

All operations are thread-safe. Call from multiple threads without external locking.

## Error Handling

All methods gracefully degrade if predictions fail:
- Return sensible defaults
- Log errors for debugging
- Never crash or throw unhandled exceptions
