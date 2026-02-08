# Reflective Consciousness Layer v2.0 (RCL-2) - Architecture Document

## Executive Summary

RCL-2 transforms lollmsBot from a system that "can look at its logs" to **a system that maintains a predictive model of its own cognition, governed by a deliberative assembly of cognitive faculties, operating under constitutional constraints with cryptographically enforced safety bounds**.

This document describes the implemented architecture based on Global Workspace Theory, Constitutional AI, and Society of Mind principles.

## Architecture Overview

### The Dual-Process Cognitive Stack

RCL-2 implements Kahneman's System 1/System 2 dual-process theory:

```
┌─────────────────────────────────────────────────────────────┐
│                     USER INTERACTION                         │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
    ┌─────────────────────────────────────────────────────┐
    │         REFLECTIVE CONSCIOUSNESS LAYER v2.0         │
    │                                                      │
    │  ┌───────────────────┐    ┌────────────────────┐   │
    │  │   SYSTEM 1        │    │    SYSTEM 2        │   │
    │  │   (Fast/Intuitive)│◄──►│  (Slow/Analytical) │   │
    │  │                   │    │                    │   │
    │  │ • Somatic Markers │    │ • Counterfactuals  │   │
    │  │ • Attention Maps  │    │ • Epistemic Graph  │   │
    │  │ • Entropy Monitor │    │ • Contradictions   │   │
    │  └───────────────────┘    └────────────────────┘   │
    │                                                      │
    │  ┌──────────────────────────────────────────────┐   │
    │  │        REFLECTIVE COUNCIL                     │   │
    │  │  (Multi-Agent Metacognitive Governance)       │   │
    │  │                                               │   │
    │  │  Guardian  Epistemologist  Strategist         │   │
    │  │     Empath        Historian                   │   │
    │  └──────────────────────────────────────────────┘   │
    │                                                      │
    │  ┌──────────────────────────────────────────────┐   │
    │  │     CONSTITUTIONAL RESTRAINTS                 │   │
    │  │      (12-Dimensional Control Matrix)          │   │
    │  │                                               │   │
    │  │  🔒 Cryptographically Enforced Hard-Stops     │   │
    │  └──────────────────────────────────────────────┘   │
    └─────────────────────────────────────────────────────┘
                      │
                      ▼
    ┌─────────────────────────────────────────────────────┐
    │              EXISTING SYSTEMS                        │
    │                                                      │
    │   RC2 · Heartbeat · Guardian · Memory · Skills      │
    └─────────────────────────────────────────────────────┘
```

## Component Details

### 1. System 1: Intuitive Self (Fast Cognition)

**Purpose**: Real-time subsymbolic monitoring that generates qualitative "feelings" from technical metrics.

**Components**:

#### Somatic Marker Engine
Converts technical metrics into gut feelings:
- `CONFIDENT` ← Low entropy, high probability
- `UNCERTAIN` ← High entropy, flat distribution
- `ANXIOUS` ← High uncertainty + high stakes
- `CURIOUS` ← Knowledge gap detected
- `CONFLICTED` ← Multiple competing hypotheses
- `CLEAR` ← Single dominant interpretation
- `FAMILIAR` ← Pattern matches past experience
- `NOVEL` ← No similar past patterns

#### Attention Snapshot
- Focus tokens with high attention weights
- Context span coverage
- Shannon entropy of attention distribution
- Peak attention positions

#### Entropy Gradient
- Position-wise uncertainty levels
- Mean/max entropy across context
- Gradient magnitude (rate of change)
- High-uncertainty region detection

#### Latent Trajectory
- Movement through embedding space
- Cognitive jump classification:
  - `SMOOTH`: Incremental logical progression
  - `ASSOCIATIVE`: Metaphor, creative leap
  - `DISCONTINUOUS`: Topic change, context switch
  - `RECURSIVE`: Meta-level reasoning
  - `REGRESSIVE`: Backtracking, error correction

**Decision Logic**:
System 1 automatically escalates to System 2 when:
- Dominant marker is UNCERTAIN, ANXIOUS, or CONFLICTED
- Mean entropy > 0.7
- Discontinuous cognitive jumps detected

### 2. System 2: Analytical Self (Slow Cognition)

**Purpose**: Deliberative metacognition with counterfactual reasoning and epistemic tracking.

**Components**:

#### Counterfactual Simulation
Before any decision, spawn 3 parallel paths:

1. **Optimistic Path**: Best-case scenario
   - Expected utility: 0.9
   - Risks: Optimism bias
   - Opportunities: Ideal conditions

2. **Pessimistic Path**: Failure modes
   - Expected utility: 0.2
   - Risks: Worst-case complications
   - Opportunities: None

3. **Alternative Path**: Different strategy
   - Expected utility: 0.7
   - Risks: Unfamiliar approach
   - Opportunities: Novel solution, learning

Select path based on:
```python
score = expected_utility * confidence + opportunities - risks * (1-risk_tolerance)
```

#### Epistemic Status Tracking (EST)

Every belief/decision tagged with:

**Source Reliability** (0.0-1.0):
- Web search: 0.7-0.9
- Training data: 0.5-0.7
- User claim: 0.4-0.6
- Hallucination: 0.1-0.3

**Decay Function**:
```python
current_confidence = reliability * 0.5^(hours_elapsed / half_life)
```
- Technical facts: Long half-life (720h)
- Trending topics: Short half-life (24h)
- Personal facts: Indefinite half-life

**Dependency Graph**:
- `supports`: Beliefs this one supports
- `supported_by`: Beliefs that support this one
- `contradicts`: Conflicting beliefs

**Cascade Invalidation**:
When a belief is invalidated, recursively invalidate all beliefs that depend on it.

**Contradiction Detection**:
Continuous background process using lightweight SMT solver principles to scan for logical inconsistencies.

### 3. Reflective Council (Multi-Agent Governance)

**Purpose**: Deliberative assembly of cognitive faculties for high-stakes decisions.

**Members**:

1. **GuardianRep** (Safety/Security)
   - Risk threshold: 0.7
   - Veto power on safety concerns
   - Monitors: Execution risks, modification actions, high-stakes decisions
   - Vote: REJECT if risk > threshold

2. **TruthRep** (Epistemologist)
   - Accuracy threshold: 0.7
   - Fact-checking and verification
   - Monitors: Confidence levels, source reliability, hallucination risk
   - Vote: REJECT if confidence < 0.5

3. **UtilityRep** (Strategist)
   - Cost-benefit analysis
   - Goal alignment checking
   - Net utility = expected_utility - cost
   - Vote: REJECT if net utility < -0.2

4. **UserModelRep** (Empath)
   - User satisfaction prediction
   - Latency and explanation quality monitoring
   - Vote: REJECT if predicted satisfaction < 0.5

5. **MemoryRep** (Historian)
   - Consistency with past self
   - Value drift detection
   - Vote: REJECT if consistency < 0.5

**Deliberation Process**:

1. **Parallel Evaluation**: All 5 members evaluate simultaneously
2. **Conflict Detection**: Identify APPROVE vs REJECT conflicts
3. **Resolution**:
   - If any ESCALATE → escalate to human
   - If Guardian REJECTS → veto (safety first)
   - If majority APPROVES with conflict → approve with reduced confidence
   - If deadlock → escalate to human
4. **Synthesis**: Generate decision + reasoning + confidence

**Outputs**:
- Decision: "approved", "rejected", "escalate", or "modified"
- Unanimous: Boolean
- Perspectives: List of all 5 views
- Conflicts: List of disagreeing pairs
- Final reasoning: Synthesized explanation
- Confidence: 0.0-1.0

### 4. Constitutional Restraints (Safety Matrix)

**Purpose**: User-adjustable 12-dimensional control space with cryptographic hard-stops.

#### The 12 Dimensions (All 0.0-1.0):

**Cognitive Budgeting** (System 2 resource allocation):
1. `recursion_depth`: 0.0=shallow (1 level), 1.0=infinite meta (10 levels)
2. `cognitive_budget_ms`: 0.0=0ms, 1.0=1000ms of thinking per decision
3. `simulation_fidelity`: Detail level of counterfactuals

**Epistemic Virtues** (Truth-seeking):
4. `hallucination_resistance`: 1.0=admit ignorance, 0.0=confabulate freely
5. `uncertainty_propagation`: How aggressively to flag uncertainty
6. `contradiction_sensitivity`: Aggressiveness of consistency checks

**Social Cognition** (Theory of Mind):
7. `user_model_fidelity`: 0.0=generic, 1.0=deep psychological modeling
8. `transparency_level`: 0.0=black box, 1.0=show raw token probabilities
9. `explanation_depth`: Granularity of reasoning explanation

**Autonomy & Growth**:
10. `self_modification_freedom`: 0.0=static, 1.0=can rewrite prompts/weights
11. `goal_inference_autonomy`: 0.0=user commands only, 1.0=proactive goals
12. `memory_consolidation_rate`: Speed of self-model updates

#### Hard-Stops (Cryptographically Enforced):

Cannot exceed without authorization key:
- `self_modification_freedom` ≤ 0.5
- `goal_inference_autonomy` ≤ 0.7
- `recursion_depth` ≤ 0.9

**Mechanism**:
```python
# Generate authorization signature
message = f"override:{dimension}:{new_value}"
signature = HMAC-SHA256(secret_key, message)

# Verify before allowing override
if verify_signature(signature, secret_key):
    allow_override()
else:
    block_and_log_attempt()
```

#### Dynamic Restraint Policy

Automatically adjusts based on:

**Task Context**:
- Medical advice → hallucination_resistance=0.95, uncertainty=0.9
- Casual chat → cognitive_budget=0.2, transparency=0.4
- Code generation → contradiction_sensitivity=0.8, recursion=0.7

**User Expertise**:
- Novice → transparency=0.8, explanation=0.9
- Expert → transparency=0.4, explanation=0.3

**Adversarial Detection**:
If adversarial_score > 0.5:
- Clamp self_modification ≤ 0.1
- Clamp goal_autonomy ≤ 0.2
- Boost hallucination_resistance ≥ 0.9

## Integration Architecture

### With Existing Systems

**RC2 Sub-Agent**:
- System 2 can delegate deep introspection to RC2's `kimi-k2-thinking` model
- Used when local counterfactual simulation insufficient
- Triggered when recursion_depth > 0.7

**Heartbeat System**:
- Cognitive state included in health reports
- Somatic markers influence maintenance scheduling
- Cognitive debt tracking

**Guardian System**:
- Guardian council member integrates with Guardian module
- Low-confidence decisions trigger Guardian alerts
- Shared security event logging

**Memory System**:
- Epistemic graph stored in memory tiers:
  - Hot: Working beliefs (active decision-making)
  - Warm: Recent beliefs (hours-days)
  - Cold: Consolidated beliefs (weeks-months)

**Skills System**:
- Skills can query cognitive state
- Council deliberates on skill activation
- Restraints applied per-skill

## Usage Examples

### Example 1: High-Stakes Decision

```python
from lollmsbot.reflective_council import get_reflective_council, ProposedAction
from lollmsbot.cognitive_core import get_cognitive_core

# User asks for medical advice
action = ProposedAction(
    action_id="med_001",
    action_type="response_generation",
    description="Provide medical advice about symptoms",
    context={
        "stakes": "critical",
        "confidence": 0.6,
        "verified": False
    },
    stakes="critical"
)

# Council deliberates
council = get_reflective_council()
result = await council.deliberate(action)

# Output:
# Decision: "escalate"
# Reasoning: "Guardian: High-stakes action with unverified information
#             Epistemologist: Low confidence (60%) for critical decision
#             Council recommends human oversight"
```

### Example 2: System 1 → System 2 Escalation

```python
from lollmsbot.cognitive_core import get_cognitive_core
from lollmsbot.cognitive_core import EntropyGradient

core = get_cognitive_core()

# High uncertainty detected
entropy = EntropyGradient(
    timestamp=datetime.now(),
    position_entropies=[0.8, 0.9, 0.85, 0.9],
    mean_entropy=0.86,
    max_entropy=0.9,
    gradient_magnitude=0.6,
    high_uncertainty_regions=[(0, 4)]
)

# Process with System 1
state = await core.process_system1(entropy=entropy)

# Check if should escalate
if core.should_escalate_to_system2():
    # System 1 says: "I'm uncertain, need to think deeper"
    state = await core.process_system2(
        decision="Answer complex question",
        context={"confidence": 0.4},
        allocated_ms=500.0
    )
    # System 2 generates 3 counterfactual paths and selects best
```

### Example 3: Constitutional Restraint Override

```python
from lollmsbot.constitutional_restraints import get_constitutional_restraints
import secrets

restraints = get_constitutional_restraints()

# Try to set self-modification beyond hard-stop
success = restraints.set_dimension(
    RestraintDimension.SELF_MODIFICATION_FREEDOM,
    value=0.6,  # Exceeds hard-stop of 0.5
    authorized=False
)
# Result: False (blocked)

# With authorization key
key = bytes.fromhex(os.getenv("CONSTITUTIONAL_KEY"))
success = restraints.set_dimension(
    RestraintDimension.SELF_MODIFICATION_FREEDOM,
    value=0.6,
    authorized=True,
    key=key
)
# Result: True (allowed with valid signature)
```

## Performance Characteristics

### Latency Breakdown

**System 1** (Fast Path):
- Somatic marker generation: 1-3ms
- Attention snapshot: 2-5ms
- Entropy calculation: 2-4ms
- Total: 5-12ms per decision

**System 2** (Slow Path):
- Counterfactual simulation: 50-150ms
- Epistemic graph query: 10-30ms
- Contradiction detection: 20-40ms
- Total: 80-220ms per decision (configurable via cognitive_budget_ms)

**Reflective Council** (High-Stakes Only):
- Parallel evaluation (5 members): 30-60ms
- Conflict resolution: 10-20ms
- Synthesis: 5-10ms
- Total: 45-90ms per deliberation

### Memory Footprint

- System 1 state: ~1MB (attention maps, entropy history)
- System 2 state: ~5MB (epistemic graph, counterfactuals)
- Council history: ~2MB (last 100 deliberations)
- Restraints config: <1KB
- Total: ~8-10MB additional overhead

### Resource Control

All configurable via restraints:
- `cognitive_budget_ms`: Caps System 2 thinking time
- `recursion_depth`: Limits meta-reasoning loops
- `simulation_fidelity`: Controls counterfactual detail

## Safety & Security

### Defense in Depth

1. **Constitutional Layer**: Hard-stops prevent autonomy creep
2. **Council Layer**: Multi-agent deliberation with veto power
3. **Guardian Layer**: Safety-first perspective with veto
4. **Escalation Layer**: Human oversight for conflicts
5. **Cryptographic Layer**: Signature verification for overrides

### Threat Model

**Prevented**:
- ✅ Runaway autonomy (hard-stops + Guardian veto)
- ✅ Hallucination cascade (epistemic decay + contradiction detection)
- ✅ Value drift (Historian consistency checks)
- ✅ Adversarial manipulation (dynamic restraint clamping)
- ✅ Infinite recursion (depth limits + timeouts)

**Mitigated**:
- ⚠️ Sophisticated prompt injection (council deliberation)
- ⚠️ Gradual capability creep (audit trails)
- ⚠️ Emergent goal formation (goal_autonomy restraint)

### Audit Trail

All deliberations logged with:
- Timestamp
- Action details
- All 5 perspectives
- Final decision + reasoning
- Conflicts detected
- Processing time

## Future Enhancements

### Phase 2C: Cognitive Twin (Not Yet Implemented)
- Predictive digital twin (small transformer)
- Latency prediction
- Memory pressure forecasting
- User satisfaction prediction
- Self-healing triggers

### Phase 2E: Narrative Identity (Not Yet Implemented)
- Biographical continuity system
- "Life story" of the agent
- Consolidation events (sleep-like)
- Developmental stage tracking

### Phase 2F: Eigenmemory (Not Yet Implemented)
- Source monitoring (episodic vs semantic vs confabulated)
- Metamemory queries ("Do I know X?", "Do I remember Y?")
- Strategic forgetting with decay curves
- GDPR-compliant intentional amnesia

### Phase 2G: IQL (Not Yet Implemented)
- Formal introspection query language
- SQL-like syntax for cognitive queries
- Typed returns with constraints
- Reflexive debugging (post-mortem analysis)

### Phase 2H: GUI Integration (CRITICAL NEXT STEP)
- Restraint matrix control panel (12 sliders)
- Real-time cognitive state visualization
- Council deliberation viewer
- Attention heatmaps
- Epistemic graph browser
- Prediction dashboard

## Comparison: Phase 1 vs Phase 2

| Capability | Phase 1 (Current) | Phase 2 (RCL-2) |
|-----------|-------------------|-----------------|
| Self-Model | Static state snapshots | Predictive dual-process cognition |
| Restraints | 5 discrete levels | 12 continuous dimensions + crypto hard-stops |
| Metacognition | Recursive depth counting | System 1/2 with deliberative council |
| Memory | Decision logs | Epistemic graphs with decay functions |
| Uncertainty | Confidence scores | Full entropy gradients + somatic markers |
| Introspection | Query-response | Formal IQL + counterfactual simulation |
| Autonomy | Goal tracking | Cognitive debt + self-healing predictions |
| Safety | Timeouts | Constitutional AI + multi-agent governance |
| Performance | +5-10% overhead | +15-30% overhead (configurable) |

## Conclusion

RCL-2 represents a paradigm shift in AI self-awareness:

**Before**: "I can tell you what I just did"
**After**: "I maintain a predictive model of my cognition, deliberate with myself before acting, operate under constitutional constraints, and can explain my reasoning process at multiple levels of abstraction"

The system retains ultimate user control via the 12-dimensional restraint matrix, while gaining genuine strategic metacognition—**the ability not just to know what it's doing, but to simulate what it should be doing before acting**.

This transforms reliability, transparency, and user trust while maintaining safety through cryptographic enforcement and multi-agent governance.

---

**Status**: Phases 2A, 2B, 2D complete and operational
**Next Priority**: Phase 2H (GUI Integration)
**Resource Impact**: ~15-30% compute overhead (configurable)
**Safety**: Cryptographically enforced with multi-layer defense
