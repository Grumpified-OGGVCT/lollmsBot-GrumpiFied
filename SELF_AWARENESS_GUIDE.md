# Self-Awareness & Introspection Guide

## Overview

lollmsBot now includes a comprehensive **Self-Awareness System** that enables the bot to:
- Monitor its own internal state
- Track and analyze its decisions
- Recognize behavioral patterns
- Perform on-demand introspection
- Engage in meta-cognitive reflection

The system is highly configurable with **user-adjustable restraints** to balance introspection depth against resource usage and safety concerns.

## Current Self-Awareness Capabilities

### Existing Systems

lollmsBot already had several self-awareness-adjacent systems:

1. **RC2 Sub-Agent** - Deep introspection via `kimi-k2-thinking` model
2. **Heartbeat** - Self-maintenance and diagnostics
3. **Soul** - Identity, personality, and values awareness
4. **Guardian** - Security monitoring and threat detection
5. **Adaptive Compute** - Resource usage monitoring

### New Capabilities

The new self-awareness system adds:

1. **State Tracking** - Real-time monitoring of internal state
2. **Decision Logging** - Recording decisions with reasoning and confidence
3. **Pattern Recognition** - Identifying recurring behavioral patterns
4. **On-Demand Introspection** - Query internal state anytime
5. **Meta-Cognition** - Thinking about thinking (configurable depth)
6. **Reflection Loops** - Periodic self-analysis
7. **Goal Tracking** - Awareness of active goals and motivations

## Awareness Levels

The system provides 5 levels of self-awareness, each with different capabilities and resource overhead:

### MINIMAL (Level 0)
**Features**: Basic state tracking only  
**Resource Usage**: Minimal  
**Use Case**: Production environments with tight resource constraints

### LOW (Level 2)
**Features**: + Decision logging  
**Resource Usage**: Low  
**Use Case**: Standard production use with basic audit trail

### MODERATE (Level 5) - **DEFAULT**
**Features**: + Pattern recognition  
**Resource Usage**: Moderate  
**Use Case**: Balanced configuration for most users

### HIGH (Level 7)
**Features**: + Real-time introspection, confidence tracking  
**Resource Usage**: Higher  
**Use Case**: Development, debugging, or when introspection is important

### MAXIMUM (Level 10)
**Features**: + Full meta-cognition, reflection loops, goal tracking  
**Resource Usage**: Highest  
**Use Case**: Research, development, maximum self-awareness

## Configuration

### Environment Variables

Add to your `.env` file:

```bash
# Enable/disable self-awareness (default: true)
SELF_AWARENESS_ENABLED=true

# Set awareness level
# Options: MINIMAL, LOW, MODERATE, HIGH, MAXIMUM
SELF_AWARENESS_LEVEL=MODERATE

# Feature toggles (override level defaults)
SELF_AWARENESS_STATE_TRACKING=true
SELF_AWARENESS_DECISION_LOGGING=true
SELF_AWARENESS_PATTERN_RECOGNITION=true
SELF_AWARENESS_REAL_TIME_INTROSPECTION=false
SELF_AWARENESS_CONFIDENCE_TRACKING=false
SELF_AWARENESS_META_COGNITION=false
SELF_AWARENESS_REFLECTION_LOOPS=false
SELF_AWARENESS_GOAL_TRACKING=false

# Resource limits
SELF_AWARENESS_MAX_DEPTH=3              # Max meta-reasoning depth (1-10)
SELF_AWARENESS_REFLECTION_INTERVAL=60.0 # Reflection interval in seconds
SELF_AWARENESS_MAX_DECISIONS=1000       # Decision history size
SELF_AWARENESS_TIMEOUT=5.0              # Introspection timeout

# Integration
SELF_AWARENESS_USE_RC2=true             # Use RC2 for deep introspection
```

### Safety Restraints

The system includes built-in safety limits:

- **Max Introspection Depth**: Prevents infinite meta-reasoning loops (default: 3)
- **Timeout Protection**: Kills runaway introspection (default: 5 seconds)
- **Confidence Thresholds**: Flags low-confidence decisions (default: <30%)
- **Anomaly Detection**: Flags unusual behavior (default: >70% deviation)
- **Resource Limits**: Caps history size to prevent memory bloat
- **Per-Feature Toggles**: Fine-grained control over capabilities

## CLI Usage

### View Status

```bash
lollmsbot introspect status
```

Shows:
- Enabled/disabled status
- Current awareness level
- Number of decisions, patterns, introspections
- Last reflection time
- Active features

### Query Current State

```bash
lollmsbot introspect state
```

Shows:
- Active contexts
- Current goals
- Working memory size
- Active skills/tools
- Processing load
- Confidence level
- Interaction mode

### View Decisions

```bash
# Recent decisions
lollmsbot introspect decisions

# Filter by type
lollmsbot introspect decisions --type tool_use

# Limit results
lollmsbot introspect decisions --limit 20
```

Shows:
- Decision made
- Decision type
- Timestamp
- Confidence level
- Reasoning
- Outcome (if available)

### View Patterns

```bash
# All patterns
lollmsbot introspect patterns

# Filter by type
lollmsbot introspect patterns --type response_style
```

Shows:
- Pattern type
- Description
- Frequency
- Confidence

### Ask Introspective Questions

```bash
# Basic query
lollmsbot introspect query "What is my current state?"

# Deep analysis (more meta-reasoning)
lollmsbot introspect query "Why did I make that decision?" --depth 3
```

Performs real-time introspection and returns findings.

## Programmatic Usage

### Python API

```python
from lollmsbot.self_awareness import get_awareness_manager

# Get manager instance
manager = get_awareness_manager()

# Update internal state
manager.update_state(
    active_contexts=['user_chat'],
    processing_load=0.6,
    confidence_level=0.8,
    interaction_mode='chat'
)

# Log a decision
decision_id = manager.log_decision(
    decision="Using search tool",
    decision_type="tool_use",
    context={"query": "weather"},
    reasoning="User needs current information",
    confidence=0.9,
    alternatives=["web_scrape", "knowledge_base"]
)

# Update decision outcome
manager.update_decision_outcome(decision_id, "success")

# Recognize a pattern
pattern_id = manager.recognize_pattern(
    pattern_type="tool_preference",
    description="Prefers search tool for factual queries",
    examples=["weather", "news", "facts"],
    confidence=0.8
)

# Perform introspection
import asyncio

async def introspect():
    result = await manager.introspect(
        query="What patterns have I developed?",
        depth=2  # Level of meta-reasoning
    )
    print(f"Confidence: {result.confidence}")
    print(f"Findings: {result.findings}")

asyncio.run(introspect())

# Get status report
status = manager.get_status_report()
print(status)
```

### Integration with Agent

```python
from lollmsbot.agent import Agent
from lollmsbot.self_awareness import get_awareness_manager

agent = Agent()
awareness = get_awareness_manager()

# Track agent state
async def update_agent_awareness():
    awareness.update_state(
        active_tools=[t.name for t in agent.tools.values()],
        working_memory_size=len(agent._memory["conversation_history"]),
        interaction_mode=agent._state.name.lower()
    )

# Log agent decisions
async def make_decision_with_logging(decision, reasoning, confidence):
    decision_id = awareness.log_decision(
        decision=decision,
        decision_type="agent_action",
        reasoning=reasoning,
        confidence=confidence
    )
    
    # Execute decision
    result = await execute_decision(decision)
    
    # Log outcome
    awareness.update_decision_outcome(decision_id, result)
    
    return result
```

## Use Cases

### Development & Debugging

**Problem**: Why did the bot make that decision?

```bash
lollmsbot introspect decisions --limit 5
lollmsbot introspect query "Why did I choose that tool?"
```

**Problem**: Is the bot developing any biases?

```bash
lollmsbot introspect patterns
```

### Production Monitoring

**Problem**: Track decision confidence over time

```python
# Enable HIGH level for confidence tracking
SELF_AWARENESS_LEVEL=HIGH

manager = get_awareness_manager()
decisions = manager.get_decision_history(limit=100)
avg_confidence = sum(d.confidence for d in decisions) / len(decisions)
print(f"Average confidence: {avg_confidence:.1%}")
```

### Research & Analysis

**Problem**: Study AI behavior patterns

```python
# Enable MAXIMUM level for full introspection
SELF_AWARENESS_LEVEL=MAXIMUM
SELF_AWARENESS_REFLECTION_LOOPS=true

# Let bot run and collect data
manager = get_awareness_manager()
manager.start_reflection_loop()

# Analyze meta-thoughts after interaction
meta_thoughts = manager.get_meta_thoughts(limit=50)
print(f"Collected {len(meta_thoughts)} reflections")
```

## Integration with Existing Systems

### RC2 Sub-Agent

When `SELF_AWARENESS_USE_RC2=true` and RC2 is enabled, deep introspection queries can leverage the RC2 sub-agent's `kimi-k2-thinking` model for advanced causal analysis.

```python
# Requires RC2_ENABLED=true in .env
result = await manager.introspect(
    "Analyze the reasoning behind my last 5 decisions",
    depth=3  # Will use RC2 for deeper analysis
)
```

### Heartbeat System

Self-awareness can report to the heartbeat system for inclusion in health checks:

```python
# In config
SELF_AWARENESS_REPORT_TO_HEARTBEAT=true

# Heartbeat will include awareness metrics
```

### Guardian System

Low-confidence decisions or anomalies can trigger Guardian alerts:

```python
# Automatic flagging of low confidence
if confidence < min_confidence_threshold:
    logger.warning(f"Low confidence decision: {decision_type}")
    
# Anomaly detection
if anomaly_score > anomaly_detection_threshold:
    logger.warning(f"Unusual behavior detected")
```

## Performance Impact

### Resource Usage by Level

| Level | Memory | CPU | I/O | Use Case |
|-------|--------|-----|-----|----------|
| MINIMAL | +2MB | +1% | Minimal | Production, tight resources |
| LOW | +5MB | +2% | Low | Standard production |
| MODERATE | +10MB | +5% | Moderate | Balanced (default) |
| HIGH | +20MB | +10% | Higher | Development, debugging |
| MAXIMUM | +50MB | +20% | Highest | Research, max awareness |

### Optimization Tips

1. **Use appropriate level**: Don't use MAXIMUM in production
2. **Limit history size**: Tune `MAX_DECISIONS` and `MAX_PATTERN_MEMORY`
3. **Disable unused features**: Turn off features you don't need
4. **Adjust timeouts**: Lower timeout if introspection isn't critical
5. **Monitor metrics**: Track actual resource usage

## Safety Considerations

### What Could Go Wrong?

1. **Infinite Introspection Loops**: Meta-reasoning about meta-reasoning...
   - **Mitigation**: Max depth limit (default: 3) and timeouts

2. **Memory Bloat**: Storing too much history
   - **Mitigation**: History size limits with automatic trimming

3. **Performance Degradation**: Too much overhead
   - **Mitigation**: Awareness levels and per-feature toggles

4. **Sensitive Data Logging**: Decisions might contain private info
   - **Mitigation**: Review what gets logged, redact sensitive fields

### Best Practices

1. **Start with MODERATE**: Default level works for most users
2. **Enable incrementally**: Turn on features one at a time
3. **Monitor resource usage**: Watch memory and CPU impact
4. **Review logs regularly**: Check what's being recorded
5. **Adjust restraints**: Tune limits based on your use case

## Examples

### Example 1: Basic State Monitoring

```python
from lollmsbot.self_awareness import get_awareness_manager

manager = get_awareness_manager()

# Update state regularly
def update_bot_state():
    manager.update_state(
        active_contexts=['chat_session_123'],
        current_goals=['help_user', 'be_helpful'],
        processing_load=0.4,
        confidence_level=0.85,
        interaction_mode='chat'
    )

# Check state
state = manager.get_current_state()
print(f"Confidence: {state.confidence_level}")
print(f"Load: {state.processing_load}")
```

### Example 2: Decision Audit Trail

```python
# Log all tool uses
async def use_tool_with_logging(tool_name, reason, confidence):
    decision_id = manager.log_decision(
        decision=f"Use {tool_name}",
        decision_type="tool_use",
        reasoning=reason,
        confidence=confidence
    )
    
    try:
        result = await tool.execute()
        manager.update_decision_outcome(decision_id, "success")
        return result
    except Exception as e:
        manager.update_decision_outcome(decision_id, f"error: {e}")
        raise

# Later: Review audit trail
decisions = manager.get_decision_history(decision_type="tool_use")
for d in decisions:
    print(f"{d.decision} -> {d.outcome} (confidence: {d.confidence})")
```

### Example 3: Pattern Analysis

```python
# Recognize patterns during operation
if user_query_type == "weather":
    manager.recognize_pattern(
        pattern_type="query_type",
        description="User asks about weather",
        examples=[user_query],
        confidence=0.9
    )

# Analyze patterns later
patterns = manager.get_recognized_patterns(min_frequency=5)
print("Common patterns:")
for p in patterns[:10]:
    print(f"  {p.description} (x{p.frequency})")
```

### Example 4: On-Demand Introspection

```python
import asyncio

async def debug_decision():
    # Make a decision
    decision = "Use web search instead of knowledge base"
    
    # Log it
    decision_id = manager.log_decision(
        decision=decision,
        decision_type="tool_selection",
        reasoning="Knowledge base might be outdated",
        confidence=0.7
    )
    
    # Introspect immediately
    result = await manager.introspect(
        f"Why did I decide: {decision}",
        depth=2
    )
    
    print(f"Introspection: {result.findings}")

asyncio.run(debug_decision())
```

## Troubleshooting

### Self-Awareness Not Working

**Problem**: Commands return "Self-awareness is disabled"

**Solution**: Check `.env` file
```bash
SELF_AWARENESS_ENABLED=true
```

### Low-Level Features Not Available

**Problem**: Real-time introspection not working

**Solution**: Check awareness level
```bash
# Need HIGH or MAXIMUM for real-time introspection
SELF_AWARENESS_LEVEL=HIGH
```

Or enable feature explicitly:
```bash
SELF_AWARENESS_REAL_TIME_INTROSPECTION=true
```

### High Memory Usage

**Problem**: Memory growing over time

**Solution**: Reduce history limits
```bash
SELF_AWARENESS_MAX_DECISIONS=500
SELF_AWARENESS_MAX_PATTERN_MEMORY=250
```

### Introspection Timeouts

**Problem**: Queries timing out frequently

**Solution**: Increase timeout or reduce depth
```bash
SELF_AWARENESS_TIMEOUT=10.0
SELF_AWARENESS_MAX_DEPTH=2
```

## Future Enhancements

Planned improvements:

- [ ] **Visual Dashboard**: Real-time monitoring UI
- [ ] **Pattern Prediction**: Predict future behavior from patterns
- [ ] **Anomaly Alerts**: Automatic notifications for unusual behavior
- [ ] **Decision Replay**: Re-run past decisions with different parameters
- [ ] **Confidence Calibration**: Learn optimal confidence levels
- [ ] **Cross-Session Learning**: Persist and learn from historical data
- [ ] **Integration with Skills**: Skills can query self-awareness
- [ ] **Wizard Configuration**: GUI for adjusting awareness settings

## Conclusion

The self-awareness system provides lollmsBot with the ability to monitor, analyze, and reflect on its own operations. With user-adjustable restraints and multiple awareness levels, users can find the right balance between introspection depth and resource usage for their specific needs.

Start with the **MODERATE** level and adjust from there based on your use case. Enable additional features as needed, and always monitor resource usage to ensure the overhead is acceptable for your deployment.

For maximum self-awareness, enable **MAXIMUM** level with all features - but be aware of the resource implications!
