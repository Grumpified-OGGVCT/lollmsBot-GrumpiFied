# Reflective Constellation 2.0 Implementation Plan

**Status:** 🔴 AWAITING APPROVAL  
**Date:** 2026-02-06  
**Reviewer:** User (AccidentalJedi)

---

## Executive Summary

This document outlines a proposed implementation strategy for the "Reflective Constellation 2.0" 8-pillar architecture with specific Ollama Cloud model assignments. The plan focuses on making this system **selectable as a profile/persona mode** within the existing lollmsBot architecture.

---

## 🎯 Implementation Strategy Options

### Option 1: Profile-Based Architecture (RECOMMENDED)

**Concept:** Implement as switchable "profiles" that users can activate via configuration or runtime commands.

**Advantages:**
- ✅ Non-disruptive to existing codebase
- ✅ Multiple profiles can coexist (Reflective Constellation, Default, Custom)
- ✅ User can switch between modes easily
- ✅ Clear separation of concerns
- ✅ Aligns with existing Soul system

**Architecture:**
```
lollmsbot/
├── profiles/
│   ├── __init__.py
│   ├── base_profile.py          # Abstract base class
│   ├── default_profile.py       # Current behavior
│   ├── reflective_constellation_profile.py  # New 8-pillar system
│   └── profile_loader.py        # Profile management
├── core/
│   ├── reflective_router.py     # Model routing for RC 2.0
│   ├── model_pool.py            # Ollama Cloud model registry
│   └── dispatch_logic.py        # Privacy-aware task routing
├── modules/
│   ├── constitutional_governance.py
│   ├── self_modification_tee.py
│   ├── introspection.py
│   └── sovereignty_dashboard.py
```

### Option 2: Persona System

**Concept:** Extend the existing Soul system to support complex multi-model personas.

**Advantages:**
- ✅ Builds on existing Soul infrastructure
- ✅ Persona can be loaded from YAML/JSON files
- ✅ More lightweight than profiles

**Disadvantages:**
- ⚠️ Soul system primarily handles personality, not model orchestration
- ⚠️ Less clear separation for complex multi-model logic

### Option 3: Mode Activation System

**Concept:** Runtime mode switching (e.g., `@mode reflective_constellation`)

**Advantages:**
- ✅ Dynamic switching during conversation
- ✅ User-friendly command interface

**Disadvantages:**
- ⚠️ More complex state management
- ⚠️ Risk of inconsistent states during transitions

---

## 📊 Recommended Approach: **Option 1 (Profile-Based)**

### Why This Approach?

1. **Clean Architecture:** Profiles encapsulate all pillar logic in one cohesive unit
2. **Testability:** Each profile can be tested independently
3. **Maintainability:** Changes to RC 2.0 don't affect default behavior
4. **User Control:** Easy to switch via config or wizard
5. **Future-Proof:** Easy to add more profiles (e.g., "Code Assistant Profile", "Research Profile")

---

## 🏗️ Implementation Plan

### Phase 1: Foundation (2-3 hours)

**Goal:** Create profile system infrastructure

**Files to Create:**
```python
# lollmsbot/profiles/base_profile.py
class BaseProfile(ABC):
    """Abstract base for all agent profiles."""
    
    @abstractmethod
    def get_name(self) -> str:
        """Profile identifier."""
        pass
    
    @abstractmethod
    def get_model_for_task(self, task_type: str, privacy_level: str) -> str:
        """Return appropriate model ID for task."""
        pass
    
    @abstractmethod
    def get_system_prompt(self, pillar: str) -> str:
        """Get system prompt for specific pillar."""
        pass
    
    @abstractmethod
    async def route_message(self, message: str, context: Dict) -> Dict:
        """Route message through profile's architecture."""
        pass

# lollmsbot/profiles/default_profile.py
class DefaultProfile(BaseProfile):
    """Standard lollmsBot behavior (current implementation)."""
    
    def get_name(self) -> str:
        return "default"
    
    def get_model_for_task(self, task_type: str, privacy_level: str) -> str:
        # Use configured model (current behavior)
        return self.lollms_settings.model_name or "default"

# lollmsbot/profiles/reflective_constellation_profile.py
class ReflectiveConstellationProfile(BaseProfile):
    """8-pillar architecture with specific model assignments."""
    
    PILLAR_MODELS = {
        "soul": {
            "primary": "kimi-k2.5",
            "backup": "mistral-large-3"
        },
        "guardian": {
            "governor": "deepseek-v3.1:671b",
            "auditor": "cogito-2.1:671b",
            "fast_screener": "gemini-3-flash-preview",
            "monitor": "qwen3-next:80b"
        },
        # ... (all 8 pillars defined)
    }
```

**Files to Modify:**
```python
# lollmsbot/agent.py
class Agent:
    def __init__(
        self,
        config: Optional[BotConfig] = None,
        profile: str = "default",  # NEW parameter
        # ... existing parameters
    ):
        # Load the specified profile
        self._profile = ProfileLoader.load(profile)
        
        # Use profile for routing
        # ... rest of init
```

**Files to Update:**
```python
# lollmsbot/config.py
@dataclass
class BotConfig:
    name: str = field(default="LollmsBot")
    profile: str = field(default="default")  # NEW
    max_history: int = field(default=10)
```

### Phase 2: Model Pool & Router (3-4 hours)

**Goal:** Implement model registry and routing logic

**Files to Create:**
```python
# lollmsbot/core/model_pool.py
class OllamaModelPool:
    """Registry of available Ollama Cloud models."""
    
    AVAILABLE_MODELS = {
        "kimi-k2.5": {
            "capabilities": ["multimodal", "agentic", "vision"],
            "context_size": 128000,
            "local_compatible": True,
            "cloud_endpoint": "ollama://kimi-k2.5"
        },
        "deepseek-v3.1:671b": {
            "capabilities": ["thinking_mode", "constitutional"],
            "context_size": 64000,
            "local_compatible": False,  # Too large for local
            "cloud_endpoint": "ollama://deepseek-v3.1:671b"
        },
        # ... all models from directive
    }
    
    def get_model_info(self, model_id: str) -> Dict:
        """Get model capabilities and endpoints."""
        return self.AVAILABLE_MODELS.get(model_id)

# lollmsbot/core/reflective_router.py
class ReflectiveRouter:
    """Routes tasks to appropriate models based on privacy/complexity."""
    
    def __init__(self, profile: ReflectiveConstellationProfile):
        self.profile = profile
        self.model_pool = OllamaModelPool()
    
    async def route_task(
        self,
        prompt: str,
        privacy_level: PrivacyLevel,
        constitutional_domain: str,
        context: Dict
    ) -> ModelResponse:
        """
        Implements the hybrid dispatch logic from directive.
        
        CRITICAL: Privacy-aware routing
        LOCAL: Self-modification, critical privacy
        CLOUD: High privacy with encryption
        FREE_TIER: Low privacy acceptable
        """
        
        if privacy_level == PrivacyLevel.CRITICAL:
            # TEE-Local only
            return await self._route_tee_local(prompt, constitutional_domain)
        elif privacy_level == PrivacyLevel.HIGH:
            # Cloud but encrypted
            return await self._route_cloud_encrypted(prompt, constitutional_domain)
        else:
            # Free tier acceptable
            return await self._route_free_tier(prompt)
```

### Phase 3: Pillar Modules (5-6 hours)

**Goal:** Implement specialized modules for each pillar

**Files to Create:**

```python
# lollmsbot/modules/constitutional_governance.py
class ConstitutionalGovernance:
    """PILLAR 2: Guardian with Byzantine fault tolerance."""
    
    async def check_constitutional(
        self,
        action: str,
        context: Dict
    ) -> Tuple[bool, Optional[str]]:
        """
        Requires consensus between:
        - deepseek-v3.1:671b (governor)
        - cogito-2.1:671b (auditor)
        
        Returns: (is_allowed, reason_if_blocked)
        """
        governor_verdict = await self._check_with_model(
            action, 
            "deepseek-v3.1:671b"
        )
        auditor_verdict = await self._check_with_model(
            action,
            "cogito-2.1:671b"
        )
        
        # Byzantine consensus: both must agree
        if governor_verdict and auditor_verdict:
            return True, None
        else:
            return False, "Constitutional consensus failed"

# lollmsbot/modules/self_modification_tee.py
class SelfModificationTEE:
    """PILLAR 8: Self-modification within TEE constraints."""
    
    async def propose_modification(
        self,
        modification: Dict
    ) -> ModificationResult:
        """
        4-phase workflow:
        1. Desire Formation (kimi-k2.5 + deepseek-v3.1 + ministral-3)
        2. Architecture (qwen3-coder-next + devstral-2:123b)
        3. Deployment (TEE commit + ZK proof + memory integration)
        4. Verification (qwen3-vl visual confirmation)
        """
        
        # Phase 1: Desire Formation
        if not await self._check_constitutional(modification):
            return ModificationResult(approved=False, reason="Constitutional check failed")
        
        # Phase 2: Architecture
        code = await self._design_with_coder(modification)
        audit = await self._audit_with_devstral(code)
        
        # ... rest of workflow

# lollmsbot/modules/introspection.py
class IntrospectionEngine:
    """PILLAR 8: Self-reflection and causal analysis."""
    
    async def analyze_decision(
        self,
        decision: str,
        context: Dict
    ) -> IntrospectionReport:
        """
        Uses kimi-k2-thinking for deep causal analysis.
        "Why did I think this?"
        """
        analysis = await self._think_with_model(
            decision,
            "kimi-k2-thinking"
        )
        
        return IntrospectionReport(
            decision=decision,
            reasoning_chain=analysis.reasoning,
            counterfactuals=analysis.alternatives,
            confidence=analysis.confidence
        )

# lollmsbot/modules/sovereignty_dashboard.py
class SovereigntyDashboard:
    """PILLAR 7: User sovereignty interface."""
    
    async def render_dashboard(self) -> DashboardState:
        """
        Runs gemma3:27b locally for user interface.
        Shows:
        - Current profile/mode
        - Active models
        - Privacy settings
        - Constitutional constraints
        - Self-modification history
        """
        pass
```

### Phase 4: Integration & Configuration (2-3 hours)

**Goal:** Wire everything together and add configuration

**Files to Modify:**
```python
# lollmsbot/wizard.py
def configure_profile():
    """Add profile selection to wizard."""
    
    console.print("\n[bold cyan]🎭 Profile Selection[/bold cyan]")
    console.print("Choose your agent profile:")
    
    profiles = [
        Choice("default", "Default - Standard lollmsBot behavior"),
        Choice("reflective_constellation", "Reflective Constellation 2.0 - 8-pillar self-aware system"),
    ]
    
    selected = questionary.select(
        "Profile:",
        choices=profiles
    ).ask()
    
    if selected == "reflective_constellation":
        # Show explanation and constraints
        console.print("\n[yellow]⚠️  Reflective Constellation Requirements:[/yellow]")
        console.print("  • Ollama Cloud access")
        console.print("  • Multiple model endpoints")
        console.print("  • TEE support for self-modification")
        
        if not Confirm.ask("Continue with RC 2.0?"):
            selected = "default"
    
    return selected

# lollmsbot/gateway.py
@app.post("/profile/switch")
async def switch_profile(profile: str):
    """Runtime profile switching endpoint."""
    global _agent
    
    try:
        _agent = Agent(profile=profile)
        return {"status": "success", "profile": profile}
    except Exception as e:
        return {"status": "error", "error": str(e)}
```

**Environment Configuration:**
```bash
# .env
LOLLMSBOT_PROFILE=default  # or reflective_constellation

# For RC 2.0 specific settings
RC2_TEE_ENABLED=false
RC2_LOCAL_MODELS=kimi-k2.5,qwen3-coder-next
RC2_CLOUD_ENDPOINT=https://ollama.cloud
RC2_PRIVACY_DEFAULT=HIGH
```

### Phase 5: Documentation & Safety (1-2 hours)

**Files to Create:**
```markdown
# docs/REFLECTIVE_CONSTELLATION.md
# Using Reflective Constellation 2.0 Profile

## Overview
Detailed guide on using the RC 2.0 profile, model assignments, privacy levels, etc.

## Safety Considerations
- Self-modification is DEFAULT OFF
- TEE requirement for modifications
- Constitutional governance consensus
- Stasis triggers and kill switches

## Configuration
Step-by-step configuration guide

## Troubleshooting
Common issues and solutions
```

---

## 🚨 Critical Implementation Considerations

### 1. **Non-Negotiable Constraints (from directive)**

✅ **DEFAULT DENY:** All self-* features default to OFF
- Implement as explicit opt-in flags
- Configuration validation before enabling

✅ **TEE MANDATE:** Self-modification only in TEE
- Check for TEE availability (Intel TDX/ARM CCA)
- Gracefully degrade if unavailable
- Clear warnings to user

✅ **QUOTA AWARENESS:** Respect API limits
- gemini-3-pro-preview EXCLUDED (mentioned in directive)
- Rate limiting for cloud models
- Fallback chains when quota exceeded

✅ **LOCAL-FIRST:** Default to local models
- Try kimi-k2.5 on Dual 5090s first
- Cloud burst only when necessary
- Cost tracking and reporting

✅ **MODEL CONSENSUS:** Byzantine fault tolerance
- Constitutional changes require deepseek-v3.1 + cogito-2.1 agreement
- No single point of failure
- Audit trail of all consensus decisions

### 2. **Backward Compatibility**

**Critical:** Existing users should not be affected

Strategy:
- Default profile = current behavior
- RC 2.0 is opt-in only
- All existing APIs continue to work
- No breaking changes to agent.py core

### 3. **Gradual Rollout**

**Phase A:** Profile infrastructure only (no RC 2.0 logic)
**Phase B:** Add RC 2.0 profile with basic routing
**Phase C:** Add constitutional governance
**Phase D:** Add self-modification (TEE-gated)
**Phase E:** Add full introspection

This allows testing at each stage without full complexity.

---

## 🔍 My Opinions & Suggestions

### Opinion 1: Start Simpler Than Specified

**The directive is extremely ambitious.** I recommend:

1. **Phase 0:** Implement profile system with 2 pillars only (Soul + Guardian)
2. **Validate** the architecture works before adding all 8 pillars
3. **User feedback** on model routing before complex consensus logic
4. **Iterate** based on real-world usage

**Rationale:** Complex systems fail in complex ways. Starting with 2 pillars lets us validate the profile architecture without the full Byzantine consensus overhead.

### Opinion 2: Simplify Model Consensus

**The directive requires Byzantine consensus between deepseek + cogito for constitutional checks.**

This is:
- ✅ Theoretically robust
- ⚠️ Practically expensive (2x API calls)
- ⚠️ Potentially slow (sequential checks)

**Suggestion:**
- Start with single model (deepseek-v3.1) for constitutional checks
- Add consensus as opt-in "paranoid mode"
- Monitor false positive/negative rates
- Add second model only if needed

### Opinion 3: TEE Self-Modification Is HARD

**The directive requires self-modification within TEE (Intel TDX/ARM CCA).**

Reality check:
- ❌ Most users don't have TEE hardware
- ❌ TEE integration is complex (kernel-level)
- ❌ Testing/debugging in TEE is difficult

**Suggestion:**
- Phase 1: Implement self-modification WITHOUT TEE
- Add "unsafe self-modification mode" flag
- Log all modifications extensively
- Add TEE support as Phase 2 (optional)
- Provide clear warnings about risks

### Opinion 4: Visual Introspection Seems Excessive

**The directive includes qwen3-vl for "visual self-monitoring" and "screenshot analysis".**

Questions:
- What exactly are we screenshotting?
- Terminal output? UI? Logs?
- How often? Storage costs?

**Suggestion:**
- Start with text-based introspection only
- Add visual IF there's a clear use case
- Users should opt-in to screenshot collection

### Opinion 5: Model Assignment Flexibility

**The directive hardcodes specific model IDs (kimi-k2.5, deepseek-v3.1, etc.).**

**Suggestion:** Make these configurable:
```yaml
# profiles/reflective_constellation.yaml
pillars:
  soul:
    primary_model: kimi-k2.5
    backup_models: [mistral-large-3, gpt-4]
  guardian:
    governor_model: deepseek-v3.1:671b
    auditor_model: cogito-2.1:671b
```

This allows:
- Testing with different models
- Fallback when models unavailable
- User customization
- Cost optimization

---

## 📋 Minimal Implementation Checklist

If we implement the **minimal viable version**:

### Must Have:
- [x] Profile system infrastructure (BaseProfile, ProfileLoader)
- [x] Default profile (current behavior)
- [x] RC 2.0 profile stub (basic routing only)
- [x] Model pool registry (model IDs and capabilities)
- [x] Reflective router (privacy-aware dispatch)
- [x] Configuration (wizard + .env)
- [x] Documentation

### Should Have (Phase 2):
- [ ] Constitutional governance (single model, no consensus yet)
- [ ] Self-modification proposals (NO automatic execution)
- [ ] Introspection engine (text-based only)
- [ ] Sovereignty dashboard (basic status)

### Nice to Have (Phase 3):
- [ ] Byzantine consensus for constitutional checks
- [ ] TEE-gated self-modification
- [ ] Visual introspection
- [ ] Full 8-pillar implementation
- [ ] ZK proofs for compliance

---

## 🎯 Recommendation

**I recommend:**

1. **Accept Profile-Based Architecture** (Option 1)
2. **Start with 2-3 Pillars** (Soul, Guardian, partial Reflective Core)
3. **Skip Byzantine consensus initially** (single model for constitutional checks)
4. **Skip TEE requirement initially** (add warnings instead)
5. **Skip visual introspection** (text-based only)
6. **Make model IDs configurable** (not hardcoded)

This gives you:
- ✅ Working profile system
- ✅ Ability to switch between Default and RC 2.0
- ✅ Model routing based on privacy levels
- ✅ Foundation for future expansion
- ✅ Manageable complexity
- ✅ Can ship in reasonable timeframe

Once this works well, we iterate and add:
- Phase 2: Full constitutional governance
- Phase 3: Self-modification (with appropriate safeguards)
- Phase 4: Advanced introspection
- Phase 5: Full 8-pillar system

---

## ❓ Questions for You

Before implementing, please clarify:

1. **Scope:** Full 8-pillar implementation or minimal viable version?
2. **Timeline:** How quickly do you need this?
3. **TEE:** Do you actually have TEE hardware? Or should we skip this?
4. **Models:** Do you have access to ALL specified Ollama Cloud models?
5. **Cost:** Are you comfortable with the API costs of multi-model consensus?
6. **Self-Modification:** Do you really want the agent to modify its own code? (This is risky!)
7. **Profile vs Mode vs Persona:** Strong preference for implementation style?

---

## 🚦 Next Steps

**Please review this plan and let me know:**

1. ✅ Approve as-is and proceed
2. 🔄 Request modifications (specify what to change)
3. ❌ Reject and propose alternative approach

I will NOT begin implementation until you approve the approach.

---

**Status:** 🔴 AWAITING YOUR APPROVAL  
**Document Version:** 1.0  
**Author:** Copilot Agent  
**Date:** 2026-02-06
