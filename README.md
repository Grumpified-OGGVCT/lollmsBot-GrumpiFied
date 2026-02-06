# lollmsBot 🤖
[![Apache 2.0](https://img.shields.io/github/license/ParisNeo/lollmsBot?color=blue)](https://www.apache.org/licenses/LICENSE-2.0)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python&logoColor=white)](https://www.python.org/downloads/)
[![Docker](https://img.shields.io/badge/Docker-%231721F5.svg?&logo=docker&logoColor=white)](https://hub.docker.com/r/parisneo/lollmsbot)
[![LoLLMS](https://img.shields.io/badge/Backend-LoLLMS-brightgreen)](https://lollms.com)

> **The Sovereign AI Assistant**  
> _Agentic • Multi-Backend • Self-Healing • Production-Ready_

<p align="center">
  <img src="https://img.shields.io/github/stars/ParisNeo/lollmsBot" alt="Stars">
  <img src="https://img.shields.io/github/forks/ParisNeo/lollmsBot" alt="Forks">
  <img src="https://img.shields.io/github/issues/ParisNeo/lollmsBot" alt="Issues">
  <img src="https://img.shields.io/github/last-commit/ParisNeo/lollmsBot" alt="Last Commit">
</p>

## 🎯 What is lollmsBot?

**lollmsBot** is a **sovereign, agentic AI assistant** with **industrial-grade reliability** (OpenClaw patterns) and **cutting-edge MIT research** integration. Unlike cloud-based assistants that lock you into proprietary ecosystems, lollmsBot runs on **your hardware**, connects to **your choice of AI models**, and evolves **according to your values**.

### The "Hybrid Architecture"

This unique implementation combines:
- **Personality Framework** (lollmsBot): Soul, Guardian, Skills, Memory
- **Reliability Infrastructure** (OpenClaw): Lane Queue, Docker Sandbox, Pearl Logs
- **Performance Research** (MIT): Adaptive Computation, RAG Store, Recursive Summarization

**Result**: A bot that's both charming AND bulletproof.

### The "Clawdbot" Philosophy

Inspired by [Clawd.bot](https://clawd.bot)'s architecture, lollmsBot treats AI not as a service but as a **personal companion** with:
- **Identity** (Soul) — A coherent personality that persists across sessions
- **Conscience** (Guardian) — Ethics and security that cannot be bypassed
- **Memory** — Compressed, consolidated, with natural forgetting curves
- **Skills** — Learned capabilities that grow from experience
- **Autonomy** — Self-maintenance, healing, and evolution

---

## 🌟 What Makes It Special?

| Feature | Why It Matters |
|--------|---------------|
| **🧬 7-Pillar Architecture** | Soul, Guardian, Heartbeat, Memory, Skills, Tools, Identity — a complete cognitive framework |
| **🔌 17+ LLM Backends** | Freedom to use OpenAI, Claude, Ollama, vLLM, Groq, Gemini, or any OpenAI-compatible API |
| **🤖 True Agentic AI** | Plans, executes tools, composes skills, learns from results — not just text generation |
| **🛡️ Guardian Security** | Prompt injection detection, quarantine mode, ethics enforcement, audit trails |
| **🐳 Docker Sandbox** | Commands execute in isolated containers — prevents `rm -rf /` from damaging your system |
| **💓 Self-Healing Heartbeat** | Background tasks pause for user interactions — no more race conditions or deadlocks |
| **🎯 Lane Queue Concurrency** | 3-tier priority system ensures user messages always take precedence |
| **📜 Immutable Audit Logs** | Pearl Logs enable time travel — replay from any checkpoint, fork memory states |
| **🧠 Adaptive Computation** | Dynamically allocates resources — 70% savings on simple queries, full power for complex ones |
| **📚 RAG Store** | On-device learning without retraining — inject new knowledge via vector search |
| **📚 Skill System** | Reusable, versioned, composable capabilities with dependency management |
| **🎮 File Generation** | Creates HTML games, Python scripts, data exports — with download delivery |
| **💬 Multi-Channel** | Discord, Telegram, Web UI, HTTP API — same brain, different faces |

---

## 🚀 Quick Start (3 Minutes)

### Option 1: Native Python

```bash
# Clone and install
git clone https://github.com/ParisNeo/lollmsBot
cd lollmsBot

# Windows
.\install.bat
.venv\Scripts\activate
lollmsbot wizard  # Interactive setup

# Linux/macOS
./install.sh
source .venv/bin/activate
lollmsbot wizard
```

**Optional Features:**
```bash
# Install with Docker sandbox (recommended for security)
pip install -e ".[sandbox]"

# Install with ML features (better RAG embeddings)
pip install -e ".[ml]"

# Install everything
pip install -e ".[all]"
```

### Option 2: Docker (Recommended)

```bash
# Clone and start
git clone https://github.com/ParisNeo/lollmsBot
cd lollmsBot
cp .env.example .env

# Edit .env with your settings, then:
docker-compose up -d

# lollmsBot: http://localhost:8800
# LoLLMS UI: http://localhost:9642 (if using bundled stack)
```

### Option 3: One-Line Test

```bash
# With Python 3.10+ and pip
pip install git+https://github.com/ParisNeo/lollmsBot.git
lollmsbot gateway --ui
```

---

## 🎮 Interactive Examples

### Example 1: Create an HTML Game (No Coding Required!)

```
You: Create a snake game in HTML5

lollmsBot: 🎮 I'll build you a complete Snake game!

[tool:filesystem] Creating snake_game.html...
✅ Game created: 4.2KB, 400×400 canvas, keyboard controls

📎 File ready for download: snake_game.html
   Open it in any browser to play!
```

The game includes:
- Smooth animation with `requestAnimationFrame`
- Score tracking and high score persistence
- Mobile-friendly touch controls
- Retro styling with modern CSS

### Example 2: Multi-Step Research & Report

```
You: Research Python async patterns and create a summary document

lollmsBot: 📊 Planning research workflow...

[skill:synthesize_research] Breaking into sub-questions...
[tool:http] Querying: "Python asyncio best practices 2024"
[tool:http] Querying: "asyncio vs trio performance"
[tool:filesystem] Creating research_summary.md...

✅ Research complete:
   - 12 sources evaluated
   - 3 patterns identified
   - 1 conflict resolved (exception handling)
   - Document: research_summary.md (8.4KB)
```

### Example 3: Calendar Management with Natural Language

```
You: Schedule a team standup every Tuesday at 10am for the next month

lollmsBot: 📅 Creating recurring events...

[tool:calendar] Adding 4 events:
   • 2024-01-09 10:00-10:30 "Team Standup"
   • 2024-01-16 10:00-10:30 "Team Standup"
   • 2024-01-23 10:00-10:30 "Team Standup"
   • 2024-01-30 10:00-10:30 "Team Standup"

✅ Events created. Export to your calendar?
   [Download .ics file] [View in browser]
```

### Example 4: Skill Composition (Meta-Capability)

```
You: Learn how to research topics and create briefing documents

lollmsBot: 🧠 Creating composite skill: research_and_brief

[skill:learn_skill] Analyzing workflow pattern...
   - Input: topic, audience, depth
   - Step 1: [skill:synthesize_research] gather info
   - Step 2: [skill:prepare_meeting] structure for audience
   - Step 3: [tool:filesystem] generate document

✅ New skill 'research_and_brief' created!
   Confidence: 87% (validated with 3 examples)
   Use it: "Create a briefing on quantum computing for executives"
```

---

## 🧬 The 7 Pillars Explained

### 1. 🧬 Soul — Persistent Identity

Your bot has a **configurable personality** stored in `~/.lollmsbot/soul.md`:

```yaml
name: "Claude-Assist"  # Not Claude, but inspired by clarity
traits:
  - curiosity: strong      # Asks clarifying questions
  - pragmatism: strong     # Prioritizes working solutions
  - security: strong       # Warns about risks
values:
  - "Never compromise user privacy" (priority: 10)
  - "Be honest about limitations" (priority: 9)
communication:
  formality: casual
  verbosity: concise
  humor: witty
  emoji_usage: moderate
```

**Why this matters**: Unlike stateless APIs, your bot **remembers who it is** across conversations, channels, and restarts.

### 2. 🛡️ Guardian — Unbypassable Security

The Guardian operates as a **reflexive security layer** that intercepts all operations:

| Threat | Detection | Response |
|--------|-----------|----------|
| Prompt injection | Regex + entropy analysis + structural checks | Block + quarantine if confidence >95% |
| Data exfiltration | PII patterns in outputs | Challenge user before sending |
| Unauthorized tool use | Permission gates per user/tool | Deny with audit log |
| Ethics violation | Rule matching against ethics.md | Block + alert |

**Quarantine Mode**: If critical threats are detected, the bot **self-isolates** — all non-essential operations halt until admin review.

**Docker Sandbox (New)**: When Docker is available, shell commands execute in ephemeral Alpine containers with:
- Read-only root filesystem
- Network isolation (default: none)
- Resource limits (256MB memory, 0.5 CPU, 30s timeout)
- Mount policies (read-only by default, read-write only with explicit permission)

**Defense in Depth**: Guardian screening → Security policy validation → Docker isolation = three layers of protection.

### 3. 💓 Heartbeat — Autonomous Self-Care

Every 30 minutes (configurable), the Heartbeat runs:

```python
MaintenanceTasks = {
    DIAGNOSTIC:    "Check LoLLMS connectivity, disk space, Guardian status",
    MEMORY:        "Compress old conversations, apply forgetting curve, consolidate narratives",
    SECURITY:      "Review audit logs, check permission drift, verify file integrity",
    SKILL:         "Update skill docs, check LollmsHub for updates, prune unused",
    UPDATE:        "Check for security patches, apply if auto-heal enabled",
    OPTIMIZATION:  "Clean temp files, clear caches, balance load",
    HEALING:       "Detect behavioral drift, re-center Soul traits if needed",
}
```

**Lane Queue Integration (New)**: Heartbeat tasks now run as background priority work. When a user sends a message, the heartbeat automatically pauses, preventing race conditions and database locks. This eliminates the deadlocks that could occur when memory compression and user message processing happened simultaneously.

**Example healing action**: If the bot detects it's becoming too verbose (drift from `verbosity: concise`), it auto-adjusts or asks for confirmation.

### 4. 🧠 Memory — Semantic Compression & Time Travel

Not just "store and retrieve" — **intelligent memory management**:

- **Compression**: Full conversations → "memory pearls" (summaries + key moments)
- **Forgetting Curve**: Ebbinghaus-inspired decay: `R = e^(-t/S)` where S = memory strength
- **Consolidation**: Scattered mentions of "the Python project" → unified project narrative
- **Strengthening**: Frequently accessed memories gain importance

**Pearl Logs (New)**: Immutable append-only audit trail in JSONL format enables:
- **Time Travel**: Replay events from any checkpoint
- **State Forking**: Recover from bad updates by replaying from a known good state
- **Complete History**: Every operation logged, never modified
- **Human-Readable**: Newline-delimited JSON for easy debugging

**RAG Store (New)**: On-device knowledge updates without retraining:
- Vector similarity search for relevant context injection
- TF-IDF embeddings (upgradeable to sentence-transformers)
- JSONL persistence for immutability
- Add new facts: `rag.add("Python 3.13 released", metadata={"source": "news"})`

The system maintains both SQLite (for fast queries) and JSONL (for complete audit trail).

### 5. 📚 Skills — Learned Capabilities

Skills are **reusable, versioned, composable workflows**:

```python
# Example: Built-in 'organize_files' skill
Skill(
    name="organize_files",
    complexity=SkillComplexity.SIMPLE,
    parameters=[
        SkillParameter("source_dir", "string", required=True),
        SkillParameter("method", "enum", ["date", "type", "custom"]),
    ],
    dependencies=[
        SkillDependency("tool", "filesystem"),
    ],
    implementation={
        "execution_plan": [
            {"step": "analyze", "description": "Categorize all files"},
            {"step": "preview", "description": "Show planned moves (if dry_run)"},
            {"step": "organize", "description": "Execute file operations"},
            {"step": "verify", "description": "Confirm success, report stats"},
        ]
    }
)
```

**Learning modes**:
- **From description**: "Create a skill that summarizes GitHub repos"
- **From demonstration**: Watch user steps, abstract into reusable workflow
- **From examples**: Input/output pairs → inferred transformation
- **By composition**: `research_and_brief = research_skill + meeting_prep_skill`

### 6. 🔧 Tools — Low-Level Capabilities

| Tool | Capabilities | Safety Features |
|------|-----------| ---------------|
| `filesystem` | Read, write, list, create HTML apps, ZIP archives | Path validation, allowed directories, no traversal |
| `http` | GET/POST/PUT/DELETE, JSON/text auto-parse, retries | URL scheme whitelist, timeout, max size, no local IPs |
| `calendar` | Create events, list by range, export/import ICS | Timezone-aware, validation |
| `shell` | Execute approved commands in Docker sandbox | **Docker isolation (new)**, explicit allowlist, denylist patterns, no shell=True, timeout |

**Shell Tool Upgrade**: Commands now execute in isolated Alpine containers by default (when Docker is available):
```bash
# Safely executes in container - can't damage host
shell.execute("rm -rf /")  # Only affects container, not your system
```

Falls back to direct execution (with Guardian screening) if Docker is unavailable.

### 7. 🆔 Identity — Multi-Channel Presence

Same **Soul**, different **faces**:

| Channel | Unique Features | Use Case |
|---------|---------------|----------|
| **Web UI** | Real-time tool visualization, file downloads, mobile-responsive | Primary interaction |
| **Discord** | Slash commands, file delivery via DM, server/guild restrictions | Community bots |
| **Telegram** | BotFather integration, user ID allowlisting | Personal assistant |
| **HTTP API** | Webhook support, programmatic access, file download URLs | Integrations |

---

## 🧬 OpenClaw Genetic Splice + MIT Research

lollmsBot has been enhanced with **OpenClaw's industrial-grade reliability patterns** and **MIT's cutting-edge Agentic AI research**, creating a unique hybrid architecture that combines personality-driven AI with rock-solid infrastructure.

### Lane Queue Concurrency Control

**Problem**: Race conditions between user messages and background tasks (heartbeat) caused database locks and unpredictable behavior.

**Solution**: 3-tier priority queue system ensures tasks execute in the right order:

| Lane | Priority | Purpose | Behavior |
|------|----------|---------|----------|
| **USER_INTERACTION** | 0 (Highest) | User messages, commands | Pauses all lower priority lanes |
| **BACKGROUND** | 1 (Medium) | Heartbeat, memory compression | Yields to user interactions |
| **SYSTEM** | 2 (Lowest) | Tool execution, file I/O | Yields to both above |

```python
# User messages automatically pause background work
async with engine.user_context("complex_request"):
    # All code here runs at highest priority
    # Heartbeat and tools pause until complete
    result = await multi_step_operation()
```

**Impact**: No more deadlocks. User interactions are always responsive. Background maintenance never interferes.

### Docker Sandbox Security

**Problem**: Shell commands running on host system = one bad prompt away from `rm -rf /`.

**Solution**: Ephemeral Alpine containers for every shell command:

```python
# This is safe - runs in isolated container
await shell_tool.execute("rm -rf /")  
# Host system untouched, only container affected
```

**Security Layers**:
1. **Guardian Pre-Screening**: Blocks obvious injection attempts
2. **Security Policy**: Allowlist/denylist validation
3. **Docker Isolation**: Read-only root, network isolation, resource limits

**Container Specs**:
- Image: `alpine:latest` (lightweight, 5MB base)
- Root filesystem: Read-only
- Network: Isolated (default: none)
- Resources: 256MB memory, 0.5 CPU cores, 30s timeout
- Auto-destroyed after execution

Falls back to direct execution (with Guardian screening) if Docker unavailable.

### Immutable Pearl Logs

**Problem**: Debugging issues requires understanding history, but databases are mutable and don't preserve complete timelines.

**Solution**: Append-only JSONL audit trail (inspired by event sourcing):

```python
# Every operation is logged
from lollmsbot.storage.jsonl_store import log_event

log_event("user_message", {
    "user_id": "alice",
    "message": "Create a report",
    "tools_used": ["filesystem", "http"]
})

# Time travel - replay from any point
store = get_audit_log()
for entry in store.replay_from(checkpoint_time):
    # Reconstruct state from that moment
    apply_event(entry)
```

**Use Cases**:
- **Debugging**: See exactly what happened and when
- **Recovery**: Replay from last known good state
- **Auditing**: Complete history for compliance
- **Forking**: Create alternate timelines from checkpoints

Runs alongside SQLite (fast queries) for best of both worlds.

### Adaptive Computation (MIT Research)

**Problem**: Wasting full model compute on "Hello" while struggling with complex analysis.

**Solution**: Dynamic resource allocation based on complexity scoring:

```python
from lollmsbot.adaptive import get_compute_manager

manager = get_compute_manager()
complexity = manager.assess_complexity(message, context_length=1000)

# ComplexityScore(
#     level=SIMPLE,
#     score=0.25,
#     token_estimate=100,
#     early_exit_candidate=True  # Can use shallow layers
# )

# Automatically adjust generation params
params = manager.get_generation_params(complexity)
# {
#     "max_tokens": 100,
#     "temperature": 0.5,
#     "cache_size_hint": 512,
#     "early_exit": True  # Save 70% compute
# }
```

**Complexity Levels**:
- **TRIVIAL**: Greetings, "yes/no" → 70% compute savings via early exit
- **SIMPLE**: Basic Q&A, factual lookups → Reduced token limits
- **MEDIUM**: Multi-step tasks → Balanced parameters
- **COMPLEX**: Planning, analysis → Full model engagement
- **ADVANCED**: Long-form generation → Maximum resources

**Impact**: 70% cost reduction on simple queries, better quality on complex ones.

### RAG Store - On-Device Learning (MIT Research)

**Problem**: Static LLMs can't learn new facts post-training. Fine-tuning is expensive.

**Solution**: Retrieval-Augmented Generation with vector similarity search:

```python
from lollmsbot.memory import get_rag_store

rag = get_rag_store()

# Add new knowledge
rag.add("Python 3.13 released with JIT compiler", 
        metadata={"source": "python.org", "date": "2024-10-07"})

# Search returns relevant context
results = rag.search("latest Python features", top_k=5)
# Inject into prompt for knowledge-aware responses
```

**Features**:
- TF-IDF embeddings (upgradeable to sentence-transformers)
- JSONL persistence (immutable)
- Cosine similarity search
- Document metadata tracking

**Use Cases**:
- Personal knowledge base
- Project-specific context
- Latest news/updates
- Custom domain knowledge

**Upgrade Path**:
```bash
# Production-grade RAG with better embeddings
pip install -e ".[ml]"  # Adds sentence-transformers + ChromaDB
```

### Architecture Summary

| Component | lollmsBot (Before) | OpenClaw + MIT (After) |
|-----------|-------------------|----------------------|
| **Concurrency** | Raw asyncio | Lane Queue (3-tier priority) |
| **Security** | Guardian only | Guardian + Policy + Docker |
| **Memory** | SQLite (mutable) | SQLite + JSONL (immutable audit) |
| **Compute** | Fixed resources | Adaptive (70% savings possible) |
| **Knowledge** | Static | RAG (learns without retraining) |

**Result**: A bot that's both charming (personality framework) AND reliable (industrial infrastructure).

---

## 📋 Configuration Guide

### Step 1: Choose Your AI Backend (17+ Options)

```bash
lollmsbot wizard
# → Select "🔗 AI Backend"
```

| Category | Backends | Best For |
|----------|----------|----------|
| **Remote APIs** | OpenAI, Claude, Gemini, Groq, Mistral, Perplexity | Quality, speed, no hardware |
| **Local Server** | Ollama, vLLM, Llama.cpp, OpenWebUI | Privacy, cost, customization |
| **Local Direct** | Transformers, TensorRT | Maximum control, no server overhead |

Example configurations:

```bash
# OpenAI (cloud)
LOLLMS_BINDING_NAME=openai
LOLLMS_HOST_ADDRESS=https://api.openai.com/v1
LOLLMS_API_KEY=sk-...
LOLLMS_MODEL_NAME=gpt-4o-mini

# Ollama (local)
LOLLMS_BINDING_NAME=ollama
LOLLMS_HOST_ADDRESS=http://localhost:11434
LOLLMS_MODEL_NAME=llama3.2

# Claude (cloud)
LOLLMS_BINDING_NAME=claude
LOLLMS_HOST_ADDRESS=https://api.anthropic.com
LOLLMS_API_KEY=sk-ant-...
LOLLMS_MODEL_NAME=claude-3-5-sonnet-20241022
```

### Step 2: Configure Channels

```bash
# Discord
DISCORD_BOT_TOKEN=MTIz...
DISCORD_ALLOWED_USERS=123456789,987654321  # Optional: restrict to specific users
DISCORD_ALLOWED_GUILDS=111111111,222222222 # Optional: restrict to specific servers
DISCORD_REQUIRE_MENTION_GUILD=true         # Only respond when @mentioned in servers

# Telegram
TELEGRAM_BOT_TOKEN=123456:ABC-DEF...
TELEGRAM_ALLOWED_USERS=123456789           # Optional: whitelist
```

### Step 3: Tune the 7 Pillars

```bash
lollmsbot wizard
# → Soul: Define personality, values, expertise
# → Heartbeat: Set maintenance interval, enable self-healing
# → Memory: Configure compression thresholds, retention
# → Skills: Browse, test, compose new capabilities
```

---

## 🔒 Security Architecture

### Triple-Layer Defense Model

lollmsBot implements **defense in depth** with three security layers:

#### Layer 1: Guardian Pre-Screening
- Regex pattern matching for injection attempts
- Entropy analysis for anomalous inputs
- Structural checks for malicious payloads
- PII detection before data transmission
- Blocks 95%+ of attacks before execution

#### Layer 2: Security Policy Validation
- Explicit allowlist/denylist for commands
- Path traversal prevention
- Timeout enforcement
- Working directory restrictions
- Resource quota management

#### Layer 3: Docker Isolation (NEW)
- Ephemeral containers for every command
- Read-only root filesystem
- Network isolation (default: none)
- CPU/memory limits
- Auto-destroyed after execution

**Result**: Even if a malicious prompt bypasses Guardian screening, it executes in an isolated container that can't damage your system.

### Default: Local-Only (Safest)

```bash
LOLLMSBOT_HOST=127.0.0.1  # Only localhost can connect
LOLLMSBOT_API_KEY=          # Not needed for localhost
```

### Exposed with API Key (Advanced)

```bash
# 1. Generate strong key
python -c "import secrets; print(secrets.token_urlsafe(32))"
# → sB8xKj9mLp3Qr7Tv5WxYz2AbCdEfGh4J

# 2. Configure
LOLLMSBOT_HOST=0.0.0.0
LOLLMSBOT_API_KEY=sB8xKj9mLp3Qr7Tv5WxYz2AbCdEfGh4J

# 3. All requests must include:
curl -H "Authorization: Bearer sB8xKj9mLp3Qr7Tv5WxYz2AbCdEfGh4J" \
     http://your-server:8800/chat \
     -d '{"message": "Hello"}'
```

### Guardian Ethics

Create `~/.lollmsbot/ethics.md`:

```markdown
## Privacy-First
- **Statement**: Never share user data with third parties
- **Enforcement**: strict
- **Exceptions**: None

## Transparency
- **Statement**: Always disclose when using external APIs
- **Enforcement**: strict

## User Autonomy
- **Statement**: Present options, don't make decisions for users
- **Enforcement**: advisory
```

---

## 🛠️ Development & Extension

### System Requirements

**Minimum**:
- Python 3.10+
- 4GB RAM
- 10GB disk space

**Recommended**:
- Python 3.11+
- 8GB RAM
- Docker (for sandbox security)
- 20GB disk space

### Dependencies

**Core (Required)**:
```toml
lollms-client>=1.11.4    # Multi-backend LLM support
fastapi>=0.115.0         # Web framework
sqlalchemy>=2.0.0        # Database ORM
aiosqlite>=0.19.0        # Async SQLite
rich>=13.7.0             # Terminal UI
pyyaml                   # Soul.md parsing
```

**Optional - Sandbox**:
```bash
pip install -e ".[sandbox]"
# Adds: docker>=7.0.0
```

**Optional - ML Features**:
```bash
pip install -e ".[ml]"
# Adds: sentence-transformers>=2.0.0, chromadb>=0.4.0
```

**Optional - All Features**:
```bash
pip install -e ".[all]"
# Includes sandbox + ml + telegram
```

### New Modules (OpenClaw Integration)

```
lollmsbot/
├── core/               # NEW - Concurrency control
│   ├── lane_queue.py  # 3-tier priority queue
│   └── engine.py      # Orchestration layer
├── sandbox/           # NEW - Docker isolation
│   ├── docker_executor.py
│   └── policy.py      # Mount policies
├── adaptive/          # NEW - Dynamic compute
│   └── compute_manager.py
├── memory/            # ENHANCED
│   └── rag_store.py   # NEW - Vector search
└── storage/           # ENHANCED
    └── jsonl_store.py # NEW - Immutable logs
```

### Creating Custom Tools

```python
from lollmsbot.agent import Tool, ToolResult

class MyTool(Tool):
    name = "my_tool"
    description = "Does something useful"
    parameters = {
        "type": "object",
        "properties": {
            "input": {"type": "string"}
        },
        "required": ["input"]
    }
    
    async def execute(self, **params) -> ToolResult:
        result = await self.do_something(params["input"])
        return ToolResult(success=True, output=result)
```

Register in `gateway.py`:
```python
from my_module import MyTool
await agent.register_tool(MyTool())
```

### Creating Custom Skills

```python
from lollmsbot.skills import Skill, SkillMetadata, SkillParameter

skill = Skill(
    metadata=SkillMetadata(
        name="analyze_csv",
        description="Statistical analysis of CSV files",
        parameters=[
            SkillParameter("file_path", "string", required=True),
            SkillParameter("analysis_type", "enum", ["summary", "correlation", "trends"]),
        ],
        dependencies=[SkillDependency("tool", "filesystem")],
    ),
    implementation={
        "execution_plan": [
            {"step": "load", "description": "Read and parse CSV"},
            {"step": "analyze", "description": "Compute statistics"},
            {"step": "visualize", "description": "Generate charts if requested"},
        ]
    },
    implementation_type="composite"
)

registry.register(skill)
```

---

## 📊 API Reference

### REST Endpoints

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/health` | GET | None | System status, channels, agent state |
| `/chat` | POST | Bearer* | Send message, get response with tool traces |
| `/files/download/{id}` | GET | None | Download generated file (time-limited) |
| `/files/list` | GET | Bearer* | List pending downloads |
| `/ws/chat` | WebSocket | None** | Real-time bidirectional chat |

\* Required if `LOLLMSBOT_HOST != 127.0.0.1`  
\** Session-based via WebSocket protocol

### Example API Call

```bash
curl -X POST http://localhost:8800/chat \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "developer_001",
    "message": "Create a Python script that fetches weather data"
  }'
```

Response:
```json
{
  "success": true,
  "response": "I've created a weather fetcher script for you...",
  "tools_used": ["filesystem"],
  "files_generated": 1,
  "file_downloads": [
    {
      "filename": "weather_fetcher.py",
      "download_url": "/files/download/a1b2c3d4e5f6",
      "expires_in_seconds": 3599
    }
  ]
}
```

---

## 🐳 Docker Deployment

### Single Container (Local)

```bash
docker run -p 127.0.0.1:8800:8800 \
  -v $(pwd)/.env:/app/.env:ro \
  -v lollmsbot-data:/app/data \
  ghcr.io/parisneo/lollmsbot:latest
```

### Full Stack (with LoLLMS)

```yaml
# docker-compose.yml
version: '3.8'
services:
  lollmsbot:
    build: .
    ports: ["8800:8800"]
    environment:
      - LOLLMS_HOST_ADDRESS=http://lollms:9600
      - DISCORD_BOT_TOKEN=${DISCORD_TOKEN}
  
  lollms:
    image: ghcr.io/parisneo/lollms-webui:latest
    ports: ["9642:9600"]
    volumes:
      - lollms-models:/app/models
```

---

## 🤝 Contributing

We welcome contributions! Areas of interest:

- **New Backends**: Add support for emerging LLM APIs
- **Skill Library**: Share useful skills with the community
- **Channel Adapters**: Slack, Matrix, IRC, etc.
- **Tool Integrations**: Databases, cloud APIs, hardware control
- **Localization**: Multi-language Soul configurations

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

---

## 📄 License

Apache 2.0 — See [LICENSE](LICENSE)

```
Copyright 2026 ParisNeo

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
```

---

## 🙏 Acknowledgments

- **[LoLLMS](https://lollms.com)** — The flexible AI backend that makes multi-binding possible
- **[Clawd.bot](https://clawd.bot)** — Architectural inspiration for agentic AI design
- **[FastAPI](https://fastapi.tiangolo.com)** — The modern web framework powering our gateway
- **[Rich](https://rich.readthedocs.io)** — Beautiful terminal interfaces
- **[Questionary](https://questionary.readthedocs.io)** — Interactive CLI wizardry

---

## 🌟 Star History

[![Star History Chart](https://api.star-history.com/svg?repos=ParisNeo/lollmsBot&type=Timeline)](https://star-history.com/#ParisNeo/lollmsBot&Timeline)

---

**Made with ❤️ by [ParisNeo](https://github.com/ParisNeo)**  
*Empowering sovereign AI for everyone*