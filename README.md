# lollmsBot 🤖
[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Docker](https://img.shields.io/badge/docker-optional-green.svg)](https://www.docker.com/)

**The Sovereign AI Assistant**
*Agentic • Multi-Backend • Self-Healing • Production-Ready*

## 🎯 What is lollmsBot?
lollmsBot is a **sovereign, agentic AI assistant** designed for industrial-grade reliability and total user privacy. 

Unlike standard chatbots, lollmsBot is an **autonomous operator** that lives on your local hardware. It doesn't just talk; it **does**. It can write code, manage your calendar, research the web, and maintain itself—all while adhering to a strict ethical "Soul" that you define.

It combines a **personality-driven core** with **enterprise reliability infrastructure**, ensuring it never deadlocks, never hallucinates dangerous commands without oversight, and never forgets what matters.

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
| --- | --- |
| **7-Pillar Architecture** | Soul, Guardian, Heartbeat, Memory, Skills, Tools, Identity — a complete cognitive framework, not just a chatbot script. |
| **17+ LLM Backends** | Freedom to use OpenAI, Claude, Ollama, vLLM, Groq, Gemini, or *any* OpenAI-compatible API. You are never locked into one provider. |
| **True Agentic AI** | Plans, executes tools, composes skills, and learns from results. It doesn't just generate text; it performs work. |
| **Guardian Security** | Real-time prompt injection detection, quarantine mode, ethics enforcement, and strict audit trails. |
| **Docker Sandbox** | Commands execute in isolated containers. Prevents `rm -rf /` or malicious scripts from damaging your actual host system. |
| **Self-Healing Heartbeat** | Background tasks (maintenance, healing) automatically pause when you interact—eliminating race conditions and deadlocks. |
| **Lane Queue Concurrency** | A 3-tier priority system ensures your messages *always* take precedence over background tasks. |
| **Immutable Audit Logs** | "Pearl Logs" enable time travel — you can replay the agent's state from any past checkpoint or fork memory states. |
| **Adaptive Computation** | Dynamically allocates resources based on complexity — saves 70% compute on simple queries, while using full power for complex ones. |
| **RAG Store** | On-device learning without retraining. You can inject new knowledge (docs, facts) via vector search instantly. |
| **Skill System** | Capabilities are reusable, versioned, and composable with dependency management (like a package manager for AI skills). |
| **File Generation** | Can create HTML games, Python scripts, and data exports, delivering them directly to you as downloadable files. |
| **Multi-Channel** | Discord, Telegram, Web UI, HTTP API — it's the same "brain" available across all your different interfaces. |

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

---

## 🧬 The Architecture: 7 Pillars

lollmsBot is built on a cognitive framework that mimics organic intelligence:

1. **Soul:** The persistent personality and values file (`soul.md`). It defines *who* the bot is.
2. **Guardian:** The conscience. A security layer that cannot be bypassed.
3. **Heartbeat:** The autonomic nervous system. Runs background maintenance (healing, updates) without interrupting you.
4. **Memory:** The hippocampus. Manages short-term context and long-term vector storage.
5. **Skills:** The cortex. Learned workflows (e.g., "How to summarize PDFs") that can be composed together.
6. **Tools:** The hands. Interfaces for Filesystem, Shell, HTTP, and Calendar.
7. **Identity:** The voice. Allows the bot to speak on Discord, Telegram, or Web UI simultaneously.

---

## 📋 Configuration

### AI Backends

lollmsBot is model-agnostic. It works with:

* **Local:** Ollama, vLLM, Llama.cpp, GPT4All.
* **Cloud:** OpenAI, Anthropic (Claude), Google Gemini, Mistral, Groq.

Configure this easily via the wizard:
`lollmsbot wizard` -> **Select Backend**

### Security Levels

You control how much autonomy the bot has:

* **Strict:** Ask permission for EVERY file write or shell command.
* **Balanced (Default):** Auto-run safe commands; ask for high-risk actions.
* **Autonomous:** (Not recommended) Full control within the Sandbox.

---

## 🙏 Acknowledgments & Inspiration

* **ParisNeo:** For the original [LoLLMS](https://github.com/ParisNeo/lollms-webui) core.
* **OpenClaw:** For the architectural inspiration regarding "Lane Queues" and reliable agentic patterns.
* **MIT CSAIL:** For research on Adaptive Computation and RAG methodologies.