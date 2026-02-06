# Reflective Constellation 2.0: Sub-Agent Enhancement System

**Status:** 🟡 REVISED PLAN - AWAITING APPROVAL  
**Date:** 2026-02-06  
**Approach:** Sub-Agent Architecture (Enhancement, Not Replacement)

---

## 🎯 Core Philosophy: "Super Powers on Demand"

### Key Insight from User Feedback

> "The current bot is the BASE. This new stuff is ADDED as optional capabilities - like a sub-agent the main agent calls upon as needed."

**Translation:**
- ✅ **Main Agent:** Current lollmsBot (works as-is, unchanged)
- ✅ **RC 2.0 Sub-Agent:** Optional specialist that gets called for advanced tasks
- ✅ **Delegation Pattern:** Main agent decides WHEN to use superpowers
- ✅ **Not Everything:** RC 2.0 doesn't handle normal chat - only special operations

---

## 🏗️ Revised Architecture: Sub-Agent as "Specialist Consultant"

### Mental Model

Think of RC 2.0 like **calling in a specialist:**

```
User: "Can you help me plan my week?"
Main Agent: "Sure!" [handles directly - normal chat]

User: "Should this code modification be allowed?"
Main Agent: "Let me consult Constitutional Governance..." [delegates to RC 2.0]
└─> RC 2.0 Sub-Agent: [deepseek + cogito consensus check]
└─> Main Agent: [receives verdict, continues]

User: "Analyze why you made that decision"
Main Agent: "Let me run deep introspection..." [delegates to RC 2.0]
└─> RC 2.0 Sub-Agent: [kimi-k2-thinking causal analysis]
└─> Main Agent: [receives report, explains to user]
```

### What Stays in Main Agent
- Normal conversation
- Tool usage (filesystem, http, calendar, etc.)
- Skills execution
- Guardian security screening (current)
- Memory/RAG retrieval
- User permissions

### What RC 2.0 Sub-Agent Handles
- **Constitutional Review:** Deep governance checks
- **Self-Modification Proposals:** Architecture and safety review
- **Deep Introspection:** "Why did I decide X?" causal analysis
- **Meta-Learning:** Optimize learning algorithms
- **Visual Self-Monitoring:** Analyze logs/screenshots for issues
- **Consensus Building:** Byzantine fault-tolerant decisions
- **Healing Chains:** Auto-fix when main agent detects issues

---

## 📊 New Architecture

```
lollmsbot/
├── agent.py                    # MAIN AGENT (unchanged core logic)
│   ├── chat()                  # Normal conversation
│   ├── execute_tool()          # Standard tools
│   ├── execute_skill()         # Standard skills
│   └── delegate_to_rc2()       # NEW: Delegate to sub-agent when needed
│
├── subagents/                  # NEW: Sub-agent system
│   ├── __init__.py
│   ├── base_subagent.py        # Abstract base for all sub-agents
│   ├── rc2_subagent.py         # Reflective Constellation 2.0
│   └── subagent_manager.py     # Manages sub-agent lifecycle
│
├── rc2/                        # NEW: RC 2.0 specific modules
│   ├── __init__.py
│   ├── model_pool.py           # Ollama Cloud model registry
│   ├── constitutional.py       # Constitutional governance
│   ├── introspection.py        # Deep analysis engine
│   ├── self_modification.py    # Proposal and review system
│   ├── meta_learning.py        # Learning optimization
│   └── privacy_router.py       # Privacy-aware model routing
│
├── core/
│   ├── engine.py               # Lane Queue (existing)
│   └── delegation.py           # NEW: Delegation decision logic
│
└── config.py
    └── RC2Settings              # NEW: RC 2.0 configuration
```

---

## 🔧 Implementation Design

### 1. Sub-Agent Manager

```python
# lollmsbot/subagents/subagent_manager.py

class SubAgentManager:
    """Manages optional sub-agents for specialized tasks."""
    
    def __init__(self):
        self._subagents: Dict[str, BaseSubAgent] = {}
        self._enabled: Dict[str, bool] = {}
    
    def register_subagent(
        self,
        name: str,
        subagent: BaseSubAgent,
        enabled: bool = False
    ):
        """Register a sub-agent (disabled by default)."""
        self._subagents[name] = subagent
        self._enabled[name] = enabled
    
    def enable_subagent(self, name: str):
        """Enable a sub-agent (opt-in)."""
        if name in self._subagents:
            self._enabled[name] = True
            logger.info(f"Enabled sub-agent: {name}")
    
    def disable_subagent(self, name: str):
        """Disable a sub-agent."""
        if name in self._subagents:
            self._enabled[name] = False
    
    async def delegate(
        self,
        task_type: str,
        context: Dict[str, Any]
    ) -> Optional[SubAgentResult]:
        """
        Delegate a task to appropriate sub-agent.
        Returns None if no sub-agent handles this task type.
        """
        for name, subagent in self._subagents.items():
            if not self._enabled[name]:
                continue  # Skip disabled sub-agents
            
            if subagent.can_handle(task_type):
                return await subagent.execute(task_type, context)
        
        return None  # No sub-agent available
```

### 2. RC 2.0 Sub-Agent

```python
# lollmsbot/subagents/rc2_subagent.py

class RC2SubAgent(BaseSubAgent):
    """
    Reflective Constellation 2.0 Sub-Agent
    
    Provides advanced capabilities:
    - Constitutional governance (Byzantine consensus)
    - Deep introspection (causal analysis)
    - Self-modification proposals
    - Meta-learning optimization
    """
    
    HANDLED_TASKS = [
        "constitutional_check",
        "deep_introspection", 
        "self_modification_proposal",
        "meta_learning",
        "healing_chain",
        "visual_monitoring"
    ]
    
    def __init__(self, config: RC2Settings):
        self.config = config
        self.model_pool = OllamaModelPool()
        self.privacy_router = PrivacyRouter()
        
        # Initialize specialized modules
        self.constitutional = ConstitutionalGovernance(config)
        self.introspection = IntrospectionEngine(config)
        self.self_mod = SelfModificationEngine(config)
        self.meta_learning = MetaLearningEngine(config)
    
    def can_handle(self, task_type: str) -> bool:
        """Check if this sub-agent handles this task."""
        return task_type in self.HANDLED_TASKS
    
    async def execute(
        self,
        task_type: str,
        context: Dict[str, Any]
    ) -> SubAgentResult:
        """Execute specialized task."""
        
        if task_type == "constitutional_check":
            return await self._check_constitutional(context)
        elif task_type == "deep_introspection":
            return await self._deep_introspect(context)
        elif task_type == "self_modification_proposal":
            return await self._propose_modification(context)
        # ... other task types
    
    async def _check_constitutional(
        self,
        context: Dict[str, Any]
    ) -> SubAgentResult:
        """
        Run constitutional check with Byzantine consensus.
        Uses deepseek-v3.1 + cogito-2.1 consensus.
        """
        action = context.get("action")
        
        # Get verdicts from both models
        governor = await self._query_model(
            "deepseek-v3.1:671b",
            f"Constitutional check: {action}"
        )
        auditor = await self._query_model(
            "cogito-2.1:671b",
            f"Constitutional audit: {action}"
        )
        
        # Byzantine consensus: both must agree
        approved = governor.approved and auditor.approved
        
        return SubAgentResult(
            success=True,
            data={
                "approved": approved,
                "governor_verdict": governor.reasoning,
                "auditor_verdict": auditor.reasoning,
                "consensus": approved
            }
        )
    
    async def _deep_introspect(
        self,
        context: Dict[str, Any]
    ) -> SubAgentResult:
        """
        Deep introspection using kimi-k2-thinking.
        Answers "Why did I think X?"
        """
        decision = context.get("decision")
        
        analysis = await self._query_model(
            "kimi-k2-thinking",
            f"Analyze decision causally: {decision}"
        )
        
        return SubAgentResult(
            success=True,
            data={
                "reasoning_chain": analysis.reasoning,
                "counterfactuals": analysis.alternatives,
                "confidence": analysis.confidence,
                "causal_factors": analysis.factors
            }
        )
```

### 3. Main Agent Integration

```python
# lollmsbot/agent.py (modifications)

class Agent:
    def __init__(
        self,
        config: Optional[BotConfig] = None,
        enable_rc2: bool = False,  # NEW: opt-in RC 2.0
        # ... existing parameters
    ):
        # ... existing init code ...
        
        # NEW: Sub-agent manager
        self._subagent_manager = SubAgentManager()
        
        # NEW: Optionally enable RC 2.0 sub-agent
        if enable_rc2:
            rc2_config = RC2Settings.from_env()
            rc2_agent = RC2SubAgent(rc2_config)
            self._subagent_manager.register_subagent(
                "rc2",
                rc2_agent,
                enabled=True
            )
            logger.info("✨ RC 2.0 Sub-Agent enabled")
    
    async def chat(
        self,
        user_id: str,
        message: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Main chat method (mostly unchanged)."""
        
        # ... existing chat logic ...
        
        # NEW: Check if we should delegate to sub-agent
        delegation_needed = self._should_delegate(message, context)
        
        if delegation_needed:
            task_type = delegation_needed["task_type"]
            result = await self._subagent_manager.delegate(
                task_type,
                context
            )
            
            if result:
                # Sub-agent handled it
                return self._format_subagent_response(result)
        
        # Normal flow continues
        # ... rest of existing chat logic ...
    
    def _should_delegate(
        self,
        message: str,
        context: Optional[Dict[str, Any]]
    ) -> Optional[Dict[str, str]]:
        """
        Decide if message needs sub-agent delegation.
        
        Triggers for RC 2.0:
        - User asks "why did you..." (introspection)
        - Message contains "constitutional check"
        - Self-modification request detected
        - Meta-learning optimization needed
        """
        msg_lower = message.lower()
        
        # Introspection triggers
        if any(phrase in msg_lower for phrase in [
            "why did you",
            "explain your reasoning",
            "analyze your decision",
            "what made you think"
        ]):
            return {"task_type": "deep_introspection"}
        
        # Constitutional review triggers
        if any(phrase in msg_lower for phrase in [
            "is this allowed",
            "constitutional check",
            "should i be able to",
            "policy violation"
        ]):
            return {"task_type": "constitutional_check"}
        
        # Self-modification triggers
        if any(phrase in msg_lower for phrase in [
            "modify yourself",
            "improve your code",
            "self-modification",
            "upgrade capability"
        ]):
            return {"task_type": "self_modification_proposal"}
        
        return None  # No delegation needed
```

### 4. Configuration

```python
# lollmsbot/config.py (additions)

@dataclass
class RC2Settings:
    """Reflective Constellation 2.0 configuration."""
    
    enabled: bool = field(default=False)  # OFF by default
    
    # Privacy levels
    default_privacy_level: str = field(default="HIGH")
    allow_cloud_models: bool = field(default=True)
    
    # Model endpoints
    ollama_cloud_endpoint: str = field(default="https://ollama.cloud")
    local_models: List[str] = field(default_factory=lambda: [
        "kimi-k2.5",
        "qwen3-coder-next"
    ])
    
    # Feature flags (all default OFF per directive)
    enable_constitutional_consensus: bool = field(default=False)
    enable_self_modification: bool = field(default=False)
    enable_visual_monitoring: bool = field(default=False)
    enable_meta_learning: bool = field(default=False)
    
    # TEE settings
    tee_available: bool = field(default=False)
    tee_provider: Optional[str] = field(default=None)  # "intel_tdx" or "arm_cca"
    
    # Model assignments (8 pillars)
    pillar_models: Dict[str, Dict[str, str]] = field(default_factory=lambda: {
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
        "heartbeat": {
            "primary": "ministral-3:8b",
            "healer": "qwen3-coder-next",
            "validator": "devstral-small-2:24b"
        },
        # ... rest of 8 pillars
    })
    
    @classmethod
    def from_env(cls) -> "RC2Settings":
        """Load RC 2.0 settings from environment."""
        return cls(
            enabled=_get_bool("RC2_ENABLED", False),
            default_privacy_level=os.getenv("RC2_PRIVACY_LEVEL", "HIGH"),
            allow_cloud_models=_get_bool("RC2_ALLOW_CLOUD", True),
            enable_constitutional_consensus=_get_bool("RC2_CONSTITUTIONAL", False),
            enable_self_modification=_get_bool("RC2_SELF_MOD", False),
            tee_available=_get_bool("RC2_TEE_AVAILABLE", False),
        )
```

### 5. Wizard Integration

```python
# lollmsbot/wizard.py (additions)

def configure_rc2():
    """Optional RC 2.0 configuration in wizard."""
    
    console.print("\n[bold cyan]✨ Reflective Constellation 2.0 (Optional)[/bold cyan]")
    console.print("RC 2.0 adds advanced capabilities as a sub-agent:")
    console.print("  • Constitutional governance (Byzantine consensus)")
    console.print("  • Deep introspection (causal analysis)")
    console.print("  • Self-modification proposals (TEE-gated)")
    console.print("  • Meta-learning optimization")
    
    if not Confirm.ask("\nEnable RC 2.0 sub-agent?", default=False):
        console.print("[dim]Skipping RC 2.0 configuration[/dim]")
        return None
    
    # Show requirements
    console.print("\n[yellow]⚠️  RC 2.0 Requirements:[/yellow]")
    console.print("  • Ollama Cloud access")
    console.print("  • API keys for specified models")
    console.print("  • (Optional) TEE hardware for self-modification")
    
    rc2_settings = {
        "enabled": True,
        "privacy_level": questionary.select(
            "Default privacy level:",
            choices=["LOW", "HIGH", "CRITICAL"]
        ).ask(),
    }
    
    # Feature opt-ins
    console.print("\n[bold]Feature Configuration:[/bold]")
    
    rc2_settings["constitutional_consensus"] = Confirm.ask(
        "Enable constitutional consensus? (requires 2x API calls)",
        default=False
    )
    
    rc2_settings["self_modification"] = False  # Always default OFF
    if Confirm.ask("Enable self-modification proposals?", default=False):
        console.print("[red]⚠️  WARNING: This allows agent to propose code changes![/red]")
        if Confirm.ask("Really enable? (requires TEE for safety)", default=False):
            rc2_settings["self_modification"] = True
    
    return rc2_settings
```

---

## 🎯 Delegation Decision Logic

### When Main Agent Calls RC 2.0

```python
# lollmsbot/core/delegation.py

class DelegationDecider:
    """Decides when to delegate to RC 2.0 sub-agent."""
    
    @staticmethod
    def should_delegate(
        message: str,
        context: Dict[str, Any],
        agent_state: AgentState
    ) -> Optional[str]:
        """
        Returns task_type if delegation needed, None otherwise.
        
        Delegation triggers:
        1. User explicitly requests (e.g., "analyze your reasoning")
        2. Agent detects need (e.g., self-healing required)
        3. Guardian escalation (e.g., constitutional question)
        4. System event (e.g., meta-learning schedule)
        """
        
        # User-initiated requests
        if user_wants_introspection(message):
            return "deep_introspection"
        
        if user_requests_constitutional_check(message):
            return "constitutional_check"
        
        if user_proposes_self_modification(message):
            return "self_modification_proposal"
        
        # Agent-initiated needs
        if agent_state == AgentState.ERROR:
            return "healing_chain"
        
        if should_run_meta_learning(context):
            return "meta_learning"
        
        return None  # No delegation needed
```

### Example Flows

**Example 1: Normal Chat (No Delegation)**
```
User: "What's the weather today?"
Main Agent: [handles directly with tools]
└─> Response: "The weather is sunny, 72°F"
```

**Example 2: Introspection Request (Delegates)**
```
User: "Why did you recommend Python over JavaScript?"
Main Agent: [detects introspection request]
├─> Delegates to RC 2.0 Sub-Agent
│   └─> RC 2.0: [kimi-k2-thinking deep analysis]
│       └─> Returns: causal reasoning chain
├─> Main Agent: [formats response]
└─> Response: "I recommended Python because: [reasoning chain]..."
```

**Example 3: Self-Healing (Auto-Delegates)**
```
Main Agent: [tool execution fails repeatedly]
├─> Detects: ERROR state
├─> Delegates to RC 2.0 Sub-Agent
│   └─> RC 2.0: [healing chain]
│       ├─> qwen3-coder-next: generates fix
│       ├─> devstral-small-2: validates
│       └─> Returns: proposed fix
├─> Main Agent: [applies fix]
└─> Continues operation
```

---

## 📋 Implementation Phases (Revised)

### Phase 0: Sub-Agent Infrastructure (2-3h)

**Goal:** Create sub-agent system without RC 2.0 logic yet

**Files to Create:**
```
lollmsbot/subagents/
├── __init__.py
├── base_subagent.py        # Abstract base class
├── subagent_manager.py     # Manager for all sub-agents
└── demo_subagent.py        # Simple demo for testing
```

**Files to Modify:**
```
lollmsbot/agent.py          # Add subagent_manager
lollmsbot/config.py         # Add SubAgentSettings
```

**Validation:**
- Create a simple "echo" sub-agent
- Main agent successfully delegates to it
- Main agent works normally when sub-agent disabled

### Phase 1: RC 2.0 Foundation (3-4h)

**Goal:** Add RC 2.0 sub-agent with basic structure

**Files to Create:**
```
lollmsbot/subagents/rc2_subagent.py
lollmsbot/rc2/
├── __init__.py
├── model_pool.py           # Ollama model registry
├── privacy_router.py       # Privacy-aware routing
└── base_module.py          # Base for pillar modules
```

**Files to Modify:**
```
lollmsbot/config.py         # Add RC2Settings
lollmsbot/wizard.py         # Add RC 2.0 configuration
```

**Validation:**
- RC 2.0 sub-agent can be enabled/disabled
- Model pool correctly lists all Ollama models
- Privacy router routes based on privacy level

### Phase 2: Core Capabilities (4-5h)

**Goal:** Implement 2-3 key RC 2.0 capabilities

**Files to Create:**
```
lollmsbot/rc2/
├── constitutional.py       # Constitutional governance
├── introspection.py        # Deep analysis
└── self_modification.py    # Proposal system (no auto-execute)
```

**Capabilities to Implement:**
1. **Constitutional Check** (deepseek + cogito consensus)
2. **Deep Introspection** (kimi-k2-thinking)
3. **Self-Modification Proposal** (proposal only, requires approval)

**Validation:**
- User asks "Is this allowed?" → Constitutional check runs
- User asks "Why did you do X?" → Introspection runs
- User requests modification → Proposal generated (not auto-executed)

### Phase 3: Delegation Logic (2-3h)

**Goal:** Smart delegation decisions

**Files to Create:**
```
lollmsbot/core/delegation.py
```

**Files to Modify:**
```
lollmsbot/agent.py          # Enhanced delegation logic
```

**Features:**
- Pattern matching for user requests
- Agent state monitoring
- Guardian escalation hooks
- Scheduled tasks (meta-learning)

**Validation:**
- Right tasks delegated to RC 2.0
- Wrong tasks stay in main agent
- Graceful fallback if RC 2.0 unavailable

### Phase 4: Advanced Features (3-4h)

**Goal:** Add remaining capabilities

**Files to Create:**
```
lollmsbot/rc2/
├── meta_learning.py        # Learning optimization
├── healing_chain.py        # Auto-healing
└── visual_monitoring.py    # Screenshot analysis (optional)
```

**Validation:**
- Meta-learning runs on schedule
- Healing chain fixes simple errors
- Visual monitoring can be enabled/disabled

### Phase 5: Documentation & Safety (2-3h)

**Files to Create:**
```
docs/RC2_USER_GUIDE.md
docs/RC2_SAFETY.md
docs/RC2_API.md
```

**Files to Modify:**
```
README.md                   # Add RC 2.0 section
.env.example                # Add RC 2.0 variables
```

---

## 🔐 Safety & Constraints

### Non-Negotiable Safety Features

1. **DEFAULT OFF:**
   ```python
   RC2Settings(
       enabled=False,  # Must explicitly enable
       enable_self_modification=False,  # Extra protection
       enable_constitutional_consensus=False,  # Opt-in
       # ... all features default OFF
   )
   ```

2. **User Approval Required:**
   ```python
   # Self-modification proposals NEVER auto-execute
   proposal = await rc2.propose_modification(...)
   
   # User must explicitly approve
   if not user_approved(proposal):
       logger.info("Modification rejected by user")
       return
   
   # Only then apply
   apply_modification(proposal)
   ```

3. **Audit Trail:**
   ```python
   # Every RC 2.0 operation logged
   logger.info(f"RC2 Delegation: {task_type}")
   logger.info(f"RC2 Models Used: {models}")
   logger.info(f"RC2 Privacy Level: {privacy}")
   logger.info(f"RC2 Result: {result}")
   ```

4. **Graceful Degradation:**
   ```python
   # If RC 2.0 fails, main agent continues
   try:
       result = await subagent_manager.delegate(...)
   except Exception as e:
       logger.warning(f"RC 2.0 failed: {e}")
       # Fall back to main agent logic
       result = main_agent_fallback(...)
   ```

5. **Cost Awareness:**
   ```python
   # Track API usage
   rc2_usage = {
       "api_calls": 0,
       "estimated_cost": 0.0,
       "models_used": []
   }
   
   # Warn on high usage
   if rc2_usage["estimated_cost"] > WARNING_THRESHOLD:
       logger.warning("RC 2.0 API costs high!")
   ```

---

## 🎨 User Experience

### Enabling RC 2.0

**Option 1: Wizard**
```bash
$ lollmsbot wizard

# ... standard configuration ...

✨ Reflective Constellation 2.0 (Optional)
RC 2.0 adds advanced capabilities as a sub-agent.

? Enable RC 2.0 sub-agent? (y/N): y

⚠️  RC 2.0 Requirements:
  • Ollama Cloud access
  • API keys for specified models

? Default privacy level: (HIGH)
? Enable constitutional consensus? (y/N): n
? Enable self-modification proposals? (y/N): n

✅ RC 2.0 configured (basic features only)
```

**Option 2: Environment Variables**
```bash
# .env
RC2_ENABLED=true
RC2_PRIVACY_LEVEL=HIGH
RC2_ALLOW_CLOUD=true
RC2_CONSTITUTIONAL=false
RC2_SELF_MOD=false
```

**Option 3: Runtime**
```python
agent = Agent(
    config=BotConfig(),
    enable_rc2=True  # Enable RC 2.0
)
```

### Using RC 2.0 Features

**Constitutional Check:**
```
User: Is it okay if I access the production database directly?
Bot: Let me run a constitutional check... [delegates to RC 2.0]
     
     Constitutional Review Complete:
     ❌ NOT ALLOWED
     
     Governor (DeepSeek): Direct production access violates safety protocols
     Auditor (Cogito): Confirmed - requires proper access control
     
     Recommendation: Use staging environment or request admin approval
```

**Deep Introspection:**
```
User: Why did you recommend using Redis instead of PostgreSQL?
Bot: Let me analyze my reasoning... [delegates to RC 2.0]
     
     Deep Introspection Analysis:
     
     Primary Factors:
     1. You mentioned "real-time caching" (90% weight)
     2. Dataset size < 10GB (80% weight)
     3. Read-heavy workload (70% weight)
     
     Counterfactuals:
     - If dataset were >50GB, I would have recommended PostgreSQL
     - If you needed complex queries, PostgreSQL would be better
     
     Confidence: 85%
```

**Self-Modification Proposal:**
```
User: Can you improve your file organization logic?
Bot: Let me draft a self-modification proposal... [delegates to RC 2.0]
     
     Self-Modification Proposal:
     
     Proposed Change: Enhance FileSystemTool.organize()
     - Add ML-based categorization
     - Improve duplicate detection
     
     Safety Review:
     ✅ No security risks detected
     ✅ No privacy violations
     ✅ Code validated by devstral-2
     
     ⚠️  This change requires your approval.
     
     [View Full Proposal] [Approve] [Reject]
```

---

## 📊 Comparison: Before vs After

### Before (Current)
```
User Message
    ↓
Main Agent
    ├─> Guardian (security check)
    ├─> Tools (filesystem, http, etc.)
    ├─> Skills (organize, research, etc.)
    └─> LLM (generate response)
    ↓
Response
```

### After (With RC 2.0)
```
User Message
    ↓
Main Agent
    ├─> Should delegate? 
    │   ├─> No: Normal flow (same as before)
    │   └─> Yes: Delegate to RC 2.0 Sub-Agent
    │           ├─> Constitutional check
    │           ├─> Deep introspection
    │           ├─> Self-mod proposal
    │           └─> Meta-learning
    │       
    ├─> Guardian (security check)
    ├─> Tools (filesystem, http, etc.)
    ├─> Skills (organize, research, etc.)
    └─> LLM (generate response)
    ↓
Response
```

**Key Points:**
- ✅ Main agent logic UNCHANGED for normal operations
- ✅ RC 2.0 is OPTIONAL enhancement
- ✅ Delegation is INTELLIGENT (only when needed)
- ✅ Gracefully degrades if RC 2.0 unavailable

---

## 💡 Benefits of This Approach

### For Users
1. **No Learning Curve:** Bot works same as before
2. **Opt-In Superpowers:** Enable advanced features when ready
3. **Clear Costs:** Know when using expensive models
4. **Safety:** RC 2.0 can't take control (delegation only)

### For Developers
1. **Modular:** RC 2.0 completely separate from main agent
2. **Testable:** Each component tested independently
3. **Maintainable:** Changes to RC 2.0 don't affect main logic
4. **Extensible:** Easy to add more sub-agents later

### For Architecture
1. **Clean Separation:** Main agent vs specialist sub-agents
2. **No Breaking Changes:** Existing code continues to work
3. **Future-Proof:** Can add more sub-agents (e.g., "ResearchAgent", "CodeReviewAgent")
4. **Performance:** Only use RC 2.0 when needed (no overhead)

---

## 🚀 Migration Path

### Step 1: Users Do Nothing
- Default behavior unchanged
- No configuration required
- Bot works exactly as before

### Step 2: Optional Enablement
- Run `lollmsbot wizard`
- Choose to enable RC 2.0
- Select which features to activate

### Step 3: Use Superpowers
- Ask "Why did you decide X?" → Get deep analysis
- Request constitutional checks → Get consensus
- Propose modifications → Get safety review

### Step 4: Tune Over Time
- Adjust privacy levels
- Enable more features
- Add custom delegation rules

---

## 📝 Minimal Implementation Checklist

### Phase 0: Sub-Agent Infrastructure ✅
- [ ] Create `base_subagent.py`
- [ ] Create `subagent_manager.py`
- [ ] Integrate into `agent.py`
- [ ] Add configuration to `config.py`
- [ ] Test with demo sub-agent

### Phase 1: RC 2.0 Foundation ✅
- [ ] Create `rc2_subagent.py`
- [ ] Create `model_pool.py`
- [ ] Create `privacy_router.py`
- [ ] Add `RC2Settings` to config
- [ ] Add RC 2.0 to wizard

### Phase 2: Core Capabilities ✅
- [ ] Implement constitutional governance
- [ ] Implement deep introspection
- [ ] Implement self-mod proposals (no auto-exec)
- [ ] Test each capability independently

### Phase 3: Delegation Logic ✅
- [ ] Create `delegation.py`
- [ ] Add delegation decision logic
- [ ] Test pattern matching
- [ ] Verify fallback behavior

### Phase 4: Documentation ✅
- [ ] User guide
- [ ] Safety documentation
- [ ] API reference
- [ ] Update README

---

## ❓ Clarification Questions

Before implementing, I need to confirm:

1. **Scope for MVP:**
   - Start with Phase 0-3 (infrastructure + 3 core capabilities)?
   - Or full implementation including advanced features?

2. **Model Access:**
   - Do you have Ollama Cloud access?
   - Which models from the list are actually available?
   - Should I provide fallbacks for unavailable models?

3. **TEE Requirement:**
   - Should I implement TEE checking, or skip for now?
   - If skipping TEE, what safeguards for self-modification?

4. **Cost Controls:**
   - Should I implement usage tracking?
   - Daily/monthly limits?
   - Warnings at certain thresholds?

5. **Delegation Triggers:**
   - Any specific keywords you want to trigger RC 2.0?
   - Should agent autonomously delegate (e.g., auto-healing)?
   - Or always require user initiation?

---

## 🎯 Recommended Approach

**I recommend starting with Phases 0-3:**

✅ **Phase 0:** Sub-agent infrastructure (2-3h)
✅ **Phase 1:** RC 2.0 foundation (3-4h)
✅ **Phase 2:** Core capabilities (4-5h)
  - Constitutional governance
  - Deep introspection
  - Self-mod proposals
✅ **Phase 3:** Delegation logic (2-3h)

**Total: ~12-15 hours**

This gives you:
- Working sub-agent system
- 3 powerful RC 2.0 capabilities
- Intelligent delegation
- Safe, tested foundation

Then add Phases 4-5 based on feedback:
- Advanced features (healing, meta-learning)
- Additional pillars
- Visual monitoring
- Complete documentation

---

## 🚦 What I Need From You

Please review and tell me:

1. ✅ **Approve MVP** (Phases 0-3) - Start implementation
2. 🔄 **Modify** - Tell me what to change
3. 🎯 **Full Implementation** - Do all phases now
4. ❓ **Answer Questions** - Clarify the questions above

**I will NOT start coding until you approve.**

---

**Status:** 🟡 REVISED PLAN AWAITING APPROVAL  
**Architecture:** Sub-Agent Enhancement System  
**Approach:** Non-disruptive, opt-in, delegation-based  
**Next:** Awaiting your feedback to proceed
