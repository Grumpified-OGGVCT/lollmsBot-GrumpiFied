# lollmsBot 🤖
[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Docker](https://img.shields.io/badge/docker-optional-green.svg)](https://www.docker.com/)

**The Sovereign AI Assistant**
*Agentic • Multi-Backend • Self-Healing • Production-Ready*

## 🎯 What is lollmsBot?

**lollmsBot** is a **sovereign, agentic AI assistant** designed for industrial-grade reliability and total user privacy. 

Unlike standard chatbots, lollmsBot is an **autonomous operator** that lives on your local hardware. It doesn't just talk; it **does**. It can write code, manage your calendar, research the web, and maintain itself—all while adhering to a strict ethical "Soul" that you define.

### The "Hybrid Architecture"

This unique implementation combines:
- **Personality Framework** (lollmsBot): Soul, Guardian, Skills, Memory
- **Reliability Infrastructure** (OpenClaw): Lane Queue, Docker Sandbox, Pearl Logs
- **Performance Research** (MIT): Adaptive Computation, RAG Store, Recursive Summarization

**Result**: A bot that's both charming AND bulletproof—combining a **personality-driven core** with **enterprise reliability infrastructure**, ensuring it never deadlocks, never hallucinates dangerous commands without oversight, and never forgets what matters.

---

## 🌟 Key Capabilities

### 1. 🛡️ Uncompromised Security (The Sandbox)
Most agents are dangerous; they run shell commands directly on your host. 
* **Docker Isolation:** lollmsBot executes all shell commands inside ephemeral **Alpine Linux containers**. Even if the AI tries to run `rm -rf /`, it only destroys a temporary container, not your machine.
* **The Guardian:** A reflexive security layer that scans every prompt for injection attacks and enforces your ethical policy *before* action is taken.

### 2. ⚡ "Lane Queue" Concurrency
Zero race conditions. Zero deadlocks.
* **Prioritized Execution:** The bot uses a 3-tier priority queue. 
    * **User Lane (Priority 0):** Your messages always cut to the front.
    * **System Lane (Priority 1):** Background tasks (like memory compression) automatically pause when you speak.
* **Result:** The bot is always responsive, even when performing heavy maintenance in the background.

### 3. 🧠 Adaptive Intelligence (RAG + Compute)
* **On-Device Learning:** The **RAG Store** allows the bot to learn new facts (e.g., "The project password is `BlueSky`") and recall them via vector search without retraining the model.
* **Adaptive Compute:** The bot analyzes query complexity. It uses cheap, fast settings for "Hello" and maximum power for "Analyze this 50-page PDF," saving you up to 70% on compute/tokens.

### 4. 📜 Immutable Memory (Pearl Logs)
* **Time Travel:** Every thought and action is logged in an append-only JSONL format. You can replay the bot's state from any point in the past.
* **Forgetting Curve:** The bot naturally compresses old memories into "Pearls" (summaries) while keeping relevant details fresh, mimicking human long-term memory.

---

## 🌟 What Makes It Special?

| Feature | Why It Matters |
|--------|---------------|
| **🧬 7-Pillar Architecture** | Soul, Guardian, Heartbeat, Memory, Skills, Tools, Identity — a complete cognitive framework, not just a chatbot script. |
| **🔌 17+ LLM Backends** | Freedom to use OpenAI, Claude, Ollama, vLLM, Groq, Gemini, or *any* OpenAI-compatible API. You are never locked into one provider. |
| **🤖 True Agentic AI** | Plans, executes tools, composes skills, and learns from results. It doesn't just generate text; it performs work. |
| **🛡️ Guardian Security** | Real-time prompt injection detection, quarantine mode, ethics enforcement, and strict audit trails. |
| **🐳 Docker Sandbox** | Commands execute in isolated containers. Prevents `rm -rf /` or malicious scripts from damaging your actual host system. |
| **💓 Self-Healing Heartbeat** | Background tasks (maintenance, healing) automatically pause when you interact—eliminating race conditions and deadlocks. |
| **🎯 Lane Queue Concurrency** | A 3-tier priority system ensures your messages *always* take precedence over background tasks. |
| **📜 Immutable Audit Logs** | "Pearl Logs" enable time travel — you can replay the agent's state from any past checkpoint or fork memory states. |
| **🧠 Adaptive Computation** | Dynamically allocates resources based on complexity — saves 70% compute on simple queries, while using full power for complex ones. |
| **📚 RAG Store** | On-device learning without retraining. You can inject new knowledge (docs, facts) via vector search instantly. |
| **🎨 Skill System** | Capabilities are reusable, versioned, and composable with dependency management (like a package manager for AI skills). |
| **🎮 File Generation** | Can create HTML games, Python scripts, and data exports, delivering them directly to you as downloadable files. |
| **💬 Multi-Channel** | Discord, Telegram, Web UI, HTTP API — it's the same "brain" available across all your different interfaces. |

## 🚀 Quick Start

### Option 1: Docker (Recommended)
The fastest way to get running with full isolation.

```bash
git clone https://github.com/Grumpified-OGGVCT/lollmsBot-GrumpiFied
cd lollmsBot-GrumpiFied
cp .env.example .env

# Edit .env to add your API keys (OpenAI, Anthropic, or Local Ollama URL)
docker-compose up -d

```

* **Web UI:** `http://localhost:8800`

### Option 2: Native Python

For developers who want to modify the source.

```bash
git clone https://github.com/Grumpified-OGGVCT/lollmsBot-GrumpiFied
cd lollmsBot-GrumpiFied

# Install core + sandbox support
pip install -e ".[sandbox]"

# Run the setup wizard
lollmsbot wizard

```

---

## 🎮 Interactive Examples

### Example 1: The Software Engineer
**You:** "Write a Python script to fetch weather data and save it to a CSV."
**lollmsBot:**
1.  **Plan:** Analyzes requirements (API needed? CSV format?).
2.  **Sandbox:** Spins up a Docker container to test the script safely.
3.  **Verify:** Runs the script, checks for errors, fixes them.
4.  **Deliver:** Offers you the final `weather.py` file.

### Example 2: The Researcher
**You:** "Research the latest solid-state battery breakthroughs."
**lollmsBot:**
1.  **Browse:** Uses the **Browser Agent** to scan 10+ sources (filtering out ads/junk).
2.  **Synthesize:** Cross-references claims and resolves conflicts.
3.  **Report:** Generates a Markdown summary with citations.

### Example 3: The Personal Assistant
**You:** "Book a meeting with the dev team every Tuesday at 10 AM."
**lollmsBot:**
1.  **Calendar:** Accesses your local `.ics` or connected calendar.
2.  **Schedule:** Creates the recurring event series.
3.  **Confirm:** "I've added 'Dev Standup' to your calendar for the next year."

### Example 4: Skill Composition (Meta-Capability)
**You:** "Learn how to research topics and create briefing documents"
**lollmsBot:**
1.  **Analyze:** Identifies the workflow pattern (research → structure → document).
2.  **Compose:** Combines existing skills (synthesize_research + prepare_meeting + filesystem).
3.  **Validate:** Tests the new composite skill with examples.
4.  **Confirm:** "New skill 'research_and_brief' created! Use it: 'Create a briefing on quantum computing for executives'"

---

## 🧬 The 7 Pillars Explained

lollmsBot is built on a cognitive framework that mimics organic intelligence:

### 1. 🧬 Soul — Persistent Identity

Your bot has a **configurable personality** stored in `~/.lollmsbot/soul.md`:

```yaml
name: "Claude-Assist"  # Your bot's identity
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

**Docker Sandbox**: Shell commands execute in ephemeral Alpine containers with read-only root filesystem, network isolation, and resource limits (256MB memory, 0.5 CPU, 30s timeout).

### 3. 💓 Heartbeat — Autonomous Self-Care

Every 30 minutes (configurable), the Heartbeat runs maintenance tasks:

- **Diagnostic**: Check LoLLMS connectivity, disk space, Guardian status
- **Memory**: Compress old conversations, apply forgetting curve, consolidate narratives
- **Security**: Review audit logs, check permission drift, verify file integrity
- **Healing**: Detect behavioral drift, re-center Soul traits if needed

**Lane Queue Integration**: Heartbeat tasks run as background priority work. When you send a message, the heartbeat automatically pauses, preventing race conditions and database locks.

### 4. 🧠 Memory — Semantic Compression & Time Travel

Not just "store and retrieve" — **intelligent memory management**:

- **Compression**: Full conversations → "memory pearls" (summaries + key moments)
- **Forgetting Curve**: Ebbinghaus-inspired decay: `R = e^(-t/S)` where S = memory strength
- **Pearl Logs**: Immutable append-only audit trail in JSONL format enables time travel
- **RAG Store**: On-device learning via vector search without retraining the model

### 5. 📚 Skills — Learned Capabilities

Skills are **reusable, versioned, composable workflows** that can be:
- **Learned from description**: "Create a skill that summarizes GitHub repos"
- **Learned from demonstration**: Watch user steps, abstract into reusable workflow
- **Composed together**: `research_and_brief = research_skill + meeting_prep_skill`

### 6. 🔧 Tools — Low-Level Capabilities

| Tool | Capabilities | Safety Features |
|------|-----------| ---------------|
| `filesystem` | Read, write, list, create HTML apps, ZIP archives | Path validation, allowed directories, no traversal |
| `http` | GET/POST/PUT/DELETE, JSON/text auto-parse, retries | URL scheme whitelist, timeout, max size, no local IPs |
| `calendar` | Create events, list by range, export/import ICS | Timezone-aware, validation |
| `shell` | Execute approved commands in Docker sandbox | Docker isolation, explicit allowlist, timeout |

### 7. 🆔 Identity — Multi-Channel Presence

Same **Soul**, different **faces**:

| Channel | Unique Features | Use Case |
|---------|---------------|----------|
| **Web UI** | Real-time tool visualization, file downloads, mobile-responsive | Primary interaction |
| **Discord** | Slash commands, file delivery via DM, server/guild restrictions | Community bots |
| **Telegram** | BotFather integration, user ID allowlisting | Personal assistant |
| **HTTP API** | Webhook support, programmatic access, file download URLs | Integrations |

---

## 🧬 OpenClaw Patterns + MIT Research

lollmsBot has been enhanced with **OpenClaw's industrial-grade reliability patterns** and **MIT's cutting-edge research**, creating a hybrid architecture that combines personality-driven AI with rock-solid infrastructure.

### Lane Queue Concurrency Control

**Problem**: Race conditions between user messages and background tasks (heartbeat) caused database locks.

**Solution**: 3-tier priority queue system:

| Lane | Priority | Purpose | Behavior |
|------|----------|---------|----------|
| **USER_INTERACTION** | 0 (Highest) | User messages, commands | Pauses all lower priority lanes |
| **BACKGROUND** | 1 (Medium) | Heartbeat, memory compression | Yields to user interactions |
| **SYSTEM** | 2 (Lowest) | Tool execution, file I/O | Yields to both above |

**Impact**: No more deadlocks. User interactions are always responsive.

### Docker Sandbox Security

**Problem**: Shell commands on host = one bad prompt away from `rm -rf /`.

**Solution**: Ephemeral Alpine containers for every shell command with read-only root, network isolation, and resource limits.

**Defense in Depth**: Guardian screening → Security policy → Docker isolation = three layers of protection.

### Adaptive Computation (MIT Research)

**Problem**: Wasting full model compute on "Hello" while struggling with complex analysis.

**Solution**: Dynamic resource allocation based on complexity scoring:

- **TRIVIAL**: Greetings, "yes/no" → 70% compute savings via early exit
- **SIMPLE**: Basic Q&A → Reduced token limits
- **MEDIUM**: Multi-step tasks → Balanced parameters
- **COMPLEX**: Planning, analysis → Full model engagement

**Impact**: 70% cost reduction on simple queries, better quality on complex ones.

---

## 📋 Configuration

### AI Backends (17+ Options)

lollmsBot is model-agnostic. It works with:

* **Local:** Ollama, vLLM, Llama.cpp, GPT4All
* **Cloud:** OpenAI, Anthropic (Claude), Google Gemini, Mistral, Groq

Configure via the wizard: `lollmsbot wizard` -> **Select Backend**

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
```

### Security Levels

You control how much autonomy the bot has:

* **Strict:** Ask permission for EVERY file write or shell command
* **Balanced (Default):** Auto-run safe commands; ask for high-risk actions
* **Autonomous:** (Not recommended) Full control within the Sandbox

### Channel Configuration

```bash
# Discord
DISCORD_BOT_TOKEN=MTIz...
DISCORD_ALLOWED_USERS=123456789,987654321  # Optional: restrict users
DISCORD_REQUIRE_MENTION_GUILD=true         # Only respond when @mentioned

# Telegram
TELEGRAM_BOT_TOKEN=123456:ABC-DEF...
TELEGRAM_ALLOWED_USERS=123456789           # Optional: whitelist
```

---

## 🙏 Acknowledgments & Inspiration

* **ParisNeo:** For the original [LoLLMS](https://github.com/ParisNeo/lollms-webui) core.
* **OpenClaw:** For the architectural inspiration regarding "Lane Queues" and reliable agentic patterns.
* **MIT CSAIL:** For research on Adaptive Computation and RAG methodologies.