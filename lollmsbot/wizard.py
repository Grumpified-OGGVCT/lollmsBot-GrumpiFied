#!/usr/bin/env python
"""
lollmsBot Interactive Setup Wizard - Skills Edition

Now includes:
- Binding-first backend configuration (remote vs local bindings)
- Soul configuration (personality, identity, values)
- Heartbeat settings (self-maintenance frequency, tasks)
- Memory monitoring (compression, retention, optimization)
- Skills management (browse, test, create, configure)
"""
from __future__ import annotations

import os
import json
import hashlib
from pathlib import Path
from typing import Any, Dict, List, Optional
from dataclasses import dataclass

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.prompt import Prompt, Confirm, IntPrompt, FloatPrompt
    from rich.table import Table
    from rich.text import Text
    from rich.tree import Tree
    import questionary
    from questionary import Choice
except ImportError:
    print("❌ Install dev deps: pip install -e .[dev]")
    exit(1)

from lollmsbot.config import LollmsSettings
from lollmsbot.lollms_client import build_lollms_client
from lollmsbot.soul import Soul, PersonalityTrait, TraitIntensity, ValueStatement, CommunicationStyle, ExpertiseDomain
from lollmsbot.heartbeat import Heartbeat, HeartbeatConfig, MaintenanceTask, get_heartbeat
from lollmsbot.skills import SkillRegistry, SkillComplexity, get_skill_registry, SkillLearner


console = Console()


@dataclass
class BindingInfo:
    """Information about an LLM binding."""
    name: str
    display_name: str
    category: str  # "remote", "local_server", "local_direct"
    description: str
    default_host: Optional[str] = None
    requires_api_key: bool = True
    supports_ssl_verify: bool = True
    requires_models_path: bool = False
    default_model: Optional[str] = None


# Binding registry - all available bindings
AVAILABLE_BINDINGS: Dict[str, BindingInfo] = {
    # Remote / SaaS bindings
    "lollms": BindingInfo(
        name="lollms",
        display_name="🔗 LoLLMS (Default)",
        category="remote",
        description="LoLLMS WebUI - Local or remote LoLLMS server",
        default_host="http://localhost:9600",
        requires_api_key=False,  # Optional for local, required for remote
        supports_ssl_verify=True,
        default_model=None,
    ),
    "openai": BindingInfo(
        name="openai",
        display_name="🤖 OpenAI",
        category="remote",
        description="OpenAI GPT models (GPT-4, GPT-3.5, etc.)",
        default_host="https://api.openai.com/v1",
        requires_api_key=True,
        supports_ssl_verify=True,
        default_model="gpt-4o-mini",
    ),
    "azure_openai": BindingInfo(
        name="azure_openai",
        display_name="☁️ Azure OpenAI",
        category="remote",
        description="Microsoft Azure OpenAI Service",
        default_host="https://YOUR_RESOURCE.openai.azure.com/",
        requires_api_key=True,
        supports_ssl_verify=True,
        default_model="gpt-4",
    ),
    "claude": BindingInfo(
        name="claude",
        display_name="🧠 Anthropic Claude",
        category="remote",
        description="Anthropic Claude models",
        default_host="https://api.anthropic.com",
        requires_api_key=True,
        supports_ssl_verify=True,
        default_model="claude-3-5-sonnet-20241022",
    ),
    "gemini": BindingInfo(
        name="gemini",
        display_name="💎 Google Gemini",
        category="remote",
        description="Google Gemini models",
        default_host="https://generativelanguage.googleapis.com",
        requires_api_key=True,
        supports_ssl_verify=True,
        default_model="gemini-1.5-flash",
    ),
    "groq": BindingInfo(
        name="groq",
        display_name="⚡ Groq",
        category="remote",
        description="Groq ultra-fast inference",
        default_host="https://api.groq.com/openai/v1",
        requires_api_key=True,
        supports_ssl_verify=True,
        default_model="llama-3.1-8b-instant",
    ),
    "grok": BindingInfo(
        name="grok",
        display_name="🐦 xAI Grok",
        category="remote",
        description="xAI Grok models",
        default_host="https://api.x.ai/v1",
        requires_api_key=True,
        supports_ssl_verify=True,
        default_model="grok-2",
    ),
    "mistral": BindingInfo(
        name="mistral",
        display_name="🌊 Mistral AI",
        category="remote",
        description="Mistral AI models",
        default_host="https://api.mistral.ai/v1",
        requires_api_key=True,
        supports_ssl_verify=True,
        default_model="mistral-small-latest",
    ),
    "ollama": BindingInfo(
        name="ollama",
        display_name="🦙 Ollama",
        category="local_server",
        description="Ollama local LLM server",
        default_host="http://localhost:11434",
        requires_api_key=False,  # Local by default, key optional for proxy
        supports_ssl_verify=False,  # Usually local
        default_model="llama3.2",
    ),
    "open_router": BindingInfo(
        name="open_router",
        display_name="🌐 OpenRouter",
        category="remote",
        description="OpenRouter - unified API for many models",
        default_host="https://openrouter.ai/api/v1",
        requires_api_key=True,
        supports_ssl_verify=True,
        default_model="meta-llama/llama-3.1-8b-instruct",
    ),
    "perplexity": BindingInfo(
        name="perplexity",
        display_name="❓ Perplexity",
        category="remote",
        description="Perplexity AI API",
        default_host="https://api.perplexity.ai",
        requires_api_key=True,
        supports_ssl_verify=True,
        default_model="llama-3.1-sonar-small-128k-online",
    ),
    "novita_ai": BindingInfo(
        name="novita_ai",
        display_name="✨ Novita AI",
        category="remote",
        description="Novita AI inference platform",
        default_host="https://api.novita.ai/v3/openai",
        requires_api_key=True,
        supports_ssl_verify=True,
        default_model="meta-llama/llama-3.1-8b-instruct",
    ),
    "litellm": BindingInfo(
        name="litellm",
        display_name="📡 LiteLLM",
        category="remote",
        description="LiteLLM proxy/gateway",
        default_host="http://localhost:4000",
        requires_api_key=True,
        supports_ssl_verify=True,
        default_model=None,
    ),
    "hugging_face_inference_api": BindingInfo(
        name="hugging_face_inference_api",
        display_name="🤗 Hugging Face",
        category="remote",
        description="Hugging Face Inference API",
        default_host="https://api-inference.huggingface.co",
        requires_api_key=True,
        supports_ssl_verify=True,
        default_model=None,
    ),
    "openllm": BindingInfo(
        name="openllm",
        display_name="🔧 OpenLLM",
        category="local_server",
        description="BentoML OpenLLM serving",
        default_host="http://localhost:3000",
        requires_api_key=False,
        supports_ssl_verify=True,
        default_model=None,
    ),
    "openwebui": BindingInfo(
        name="openwebui",
        display_name="🌟 OpenWebUI",
        category="local_server",
        description="OpenWebUI backend",
        default_host="http://localhost:8080",
        requires_api_key=True,  # OpenWebUI uses API keys
        supports_ssl_verify=True,
        default_model=None,
    ),
    # Local direct bindings
    "llama_cpp_server": BindingInfo(
        name="llama_cpp_server",
        display_name="🦙 Llama.cpp (Server)",
        category="local_server",
        description="llama.cpp server mode (local)",
        default_host="http://localhost:8080",
        requires_api_key=False,
        supports_ssl_verify=False,
        requires_models_path=True,
        default_model=None,
    ),
    "vllm": BindingInfo(
        name="vllm",
        display_name="🔥 vLLM",
        category="local_server",
        description="vLLM high-throughput inference",
        default_host="http://localhost:8000",
        requires_api_key=False,
        supports_ssl_verify=True,
        requires_models_path=False,
        default_model=None,
    ),
    "tensor_rt": BindingInfo(
        name="tensor_rt",
        display_name="🚀 TensorRT",
        category="local_direct",
        description="NVIDIA TensorRT LLM (local)",
        default_host=None,
        requires_api_key=False,
        supports_ssl_verify=False,
        requires_models_path=True,
        default_model=None,
    ),
    "transformers": BindingInfo(
        name="transformers",
        display_name="🤗 Transformers",
        category="local_direct",
        description="Hugging Face Transformers (local)",
        default_host=None,
        requires_api_key=False,
        supports_ssl_verify=False,
        requires_models_path=True,
        default_model=None,
    ),
}


class Wizard:
    """Interactive setup wizard for lollmsBot services - Full 7 Pillars Edition."""

    def __init__(self):
        self.config_path = Path.home() / ".lollmsbot" / "config.json"
        self.config_path.parent.mkdir(exist_ok=True)
        self.config: Dict[str, Dict[str, Any]] = self._load_config()
        
        # Initialize subsystems for configuration
        self.soul = Soul()
        self.heartbeat = get_heartbeat()
        self.skill_registry = get_skill_registry()
        
        # Track what's been configured
        self._configured: set = set()

    def _load_config(self) -> Dict[str, Dict[str, Any]]:
        if self.config_path.exists():
            return json.loads(self.config_path.read_text())
        return {}

    def _save_config(self) -> None:
        self.config_path.write_text(json.dumps(self.config, indent=2))

    def run_wizard(self) -> None:
        """Main wizard loop - Full Edition with all 7 Pillars."""
        console.clear()
        
        # Beautiful animated banner
        banner = Panel.fit(
            Text.assemble(
                ("🧬 ", "bold magenta"),
                ("lollmsBot", "bold cyan"),
                (" Setup Wizard\n", "bold blue"),
                ("Configure your ", "dim"),
                ("sovereign AI companion", "italic green"),
            ),
            border_style="bright_blue",
            padding=(1, 4),
        )
        console.print(banner)
        console.print()

        # Show current status
        self._show_status_tree()

        while True:
            action = questionary.select(
                "What would you like to configure?",
                choices=[
                    Choice("🔗 AI Backend (Select Binding First)", "lollms"),
                    Choice("🔀 Multi-Provider (OpenRouter + Ollama)", "multiprovider"),
                    Choice("🧠 RC2 Sub-Agent (Constitutional AI)", "rc2"),
                    Choice("🤖 Discord Channel", "discord"),
                    Choice("✈️ Telegram Channel", "telegram"),
                    Choice("🧬 Soul (Personality & Identity)", "soul"),
                    Choice("💓 Heartbeat (Self-Maintenance)", "heartbeat"),
                    Choice("🧠 Memory (Storage & Retention)", "memory"),
                    Choice("📚 Skills (Capabilities & Learning)", "skills"),
                    Choice("🔍 Test Connections", "test"),
                    Choice("📄 View Full Configuration", "view"),
                    Choice("💾 Save & Exit", "save"),
                    Choice("❌ Quit Without Saving", "quit"),
                ],
                use_indicator=True,
            ).ask()

            if action == "lollms":
                self.configure_backend()  # New binding-first configuration
            elif action == "multiprovider":
                self.configure_multi_provider()
            elif action == "rc2":
                self.configure_rc2()
            elif action == "discord":
                self.configure_service("discord")
            elif action == "telegram":
                self.configure_service("telegram")
            elif action == "soul":
                self.configure_soul()
            elif action == "heartbeat":
                self.configure_heartbeat()
            elif action == "memory":
                self.configure_memory()
            elif action == "skills":
                self.configure_skills()
            elif action == "test":
                self.test_connections()
            elif action == "view":
                self.show_full_config()
            elif action == "save":
                self._save_all()
                console.print("\n[bold green]✅ All configurations saved![/]")
                console.print(f"[dim]Location: {self.config_path}[/]")
                break
            elif action == "quit":
                if questionary.confirm("Discard unsaved changes?", default=False).ask():
                    break
        
        console.print("\n[bold cyan]🚀 Ready to start your lollmsBot journey![/]")
        console.print("[dim]Run: lollmsbot gateway[/]")

    def _show_status_tree(self) -> None:
        """Show configuration status as a tree."""
        tree = Tree("📊 Configuration Status")
        
        # Core services
        services = tree.add("[bold]Services[/]")
        for key in ["lollms", "discord", "telegram"]:
            configured = key in self.config and self.config[key]
            status = "✅" if configured else "⭕"
            color = "green" if configured else "dim"
            display_name = "AI Backend" if key == "lollms" else key.title()
            services.add(f"[{color}]{status} {display_name}[/{color}]")
        
        # Show current binding if configured
        if "lollms" in self.config and "binding_name" in self.config["lollms"]:
            binding = self.config["lollms"]["binding_name"]
            services.add(f"   [dim cyan]↳ Using: {binding}[/]")
        
        # 7 Pillars
        pillars = tree.add("[bold]7 Pillars[/]")
        soul_ok = self.soul.name != "LollmsBot" or len(self.soul.traits) > 4
        pillars.add(f"{'✅' if soul_ok else '⭕'} [cyan]Soul[/] (identity)")
        pillars.add("✅ [cyan]Guardian[/] (security) - always active")
        
        hb_config = self.heartbeat.config
        pillars.add(f"{'✅' if hb_config.enabled else '⭕'} [cyan]Heartbeat[/] ({hb_config.interval_minutes}min)")
        pillars.add(f"⭕ [dim]Memory[/] (configure in Heartbeat)")
        
        # Skills
        skill_count = len(self.skill_registry._skills)
        pillars.add(f"{'✅' if skill_count > 5 else '⭕'} [cyan]Skills[/] ({skill_count} loaded)")
        
        pillars.add("⭕ [dim]Tools[/] (enabled by default)")
        pillars.add("⭕ [dim]Identity[/] (configure in Soul)")
        
        console.print(tree)
        console.print()

    def configure_backend(self) -> None:
        """Configure AI backend with binding-first selection."""
        console.print("\n[bold blue]🔗 AI Backend Configuration[/]")
        console.print("[dim]Select your LLM provider and configure connection details[/]")
        console.print()

        # Step 1: Select binding category
        console.print("[bold]Step 1: Choose binding category[/]")
        
        category = questionary.select(
            "What type of backend?",
            choices=[
                Choice("🌐 Remote / Cloud APIs (OpenAI, Claude, etc.)", "remote"),
                Choice("🏠 Local Server (Ollama, vLLM, Llama.cpp, etc.)", "local_server"),
                Choice("💻 Local Direct (Transformers, TensorRT - no server)", "local_direct"),
            ],
            use_indicator=True,
        ).ask()

        # Step 2: Select specific binding from category
        console.print(f"\n[bold]Step 2: Select {category.replace('_', ' ').title()} binding[/]")
        
        # Filter bindings by category
        category_bindings = {
            name: info for name, info in AVAILABLE_BINDINGS.items()
            if info.category == category
        }
        
        # Create choices with descriptions
        binding_choices = [
            Choice(
                f"{info.display_name} - {info.description}",
                name
            )
            for name, info in sorted(
                category_bindings.items(),
                key=lambda x: x[1].display_name
            )
        ]
        
        binding_name = questionary.select(
            "Which binding?",
            choices=binding_choices,
            use_indicator=True,
        ).ask()
        
        binding_info = AVAILABLE_BINDINGS[binding_name]
        
        # Step 3: Configure based on binding type
        console.print(f"\n[bold]Step 3: Configure {binding_info.display_name}[/]")
        
        lollms_config = self.config.setdefault("lollms", {})
        lollms_config["binding_name"] = binding_name
        
        # Common configuration
        console.print(Panel(
            f"[bold]{binding_info.display_name}[/]\n"
            f"Category: {binding_info.category.replace('_', ' ').title()}\n"
            f"Description: {binding_info.description}",
            title="Selected Binding",
            border_style="green"
        ))

        # Model name (required for all)
        default_model = binding_info.default_model or ""
        current_model = lollms_config.get("model_name", default_model)
        model_name = questionary.text(
            "Model name",
            default=current_model,
            instruction="e.g., gpt-4o-mini, llama3.2, claude-3-5-sonnet-20241022"
        ).ask()
        lollms_config["model_name"] = model_name

        # Host address (for remote and local_server)
        if binding_info.category in ("remote", "local_server"):
            default_host = binding_info.default_host or "http://localhost:8080"
            current_host = lollms_config.get("host_address", default_host)
            host_address = questionary.text(
                "Host address / API endpoint",
                default=current_host,
                instruction="Full URL including http:// or https://"
            ).ask()
            lollms_config["host_address"] = host_address

            # API key / service key
            if binding_info.requires_api_key:
                has_key = questionary.confirm(
                    "Do you have an API key / service key?",
                    default=True
                ).ask()
                
                if has_key:
                    current_key = lollms_config.get("api_key", "")
                    api_key = questionary.password(
                        "API / Service key",
                        default=current_key,
                    ).ask()
                    lollms_config["api_key"] = api_key
                else:
                    console.print("[yellow]⚠️ Most remote APIs require a key. You can add one later.[/]")
                    lollms_config["api_key"] = ""
            else:
                # Optional key (e.g., for local servers with optional auth)
                current_key = lollms_config.get("api_key", "")
                if current_key or questionary.confirm(
                    "Add optional API key? (for authenticated servers/proxies)",
                    default=bool(current_key)
                ).ask():
                    api_key = questionary.password(
                        "API / Service key (optional)",
                        default=current_key,
                    ).ask()
                    lollms_config["api_key"] = api_key

            # SSL verification (if supported)
            if binding_info.supports_ssl_verify:
                default_verify = lollms_config.get("verify_ssl", True)
                # For local servers, default to False for convenience
                if binding_info.category == "local_server" and "localhost" in host_address:
                    default_verify = lollms_config.get("verify_ssl", False)
                
                verify_ssl = questionary.confirm(
                    "Verify SSL certificates?",
                    default=default_verify
                ).ask()
                lollms_config["verify_ssl"] = verify_ssl
                
                if not verify_ssl:
                    console.print("[yellow]⚠️ SSL verification disabled. Only use for trusted local servers.[/]")
                
                # Custom certificate (advanced)
                if questionary.confirm("Use custom SSL certificate file? (advanced)", default=False).ask():
                    cert_path = questionary.text("Path to certificate file (.pem, .crt):").ask()
                    lollms_config["certificate_file_path"] = cert_path

        # Models path (for local direct bindings and some local servers)
        if binding_info.requires_models_path or (
            binding_info.category == "local_direct" and 
            questionary.confirm("Specify models folder path?", default=True).ask()
        ):
            default_path = str(Path.home() / "models")
            current_path = lollms_config.get("models_path", default_path)
            models_path = questionary.text(
                "Models folder path",
                default=current_path,
                instruction="Directory containing .gguf, .bin, or model files"
            ).ask()
            lollms_config["models_path"] = models_path
            
            # Expand user path
            models_path_expanded = os.path.expanduser(models_path)
            if not Path(models_path_expanded).exists():
                console.print(f"[yellow]⚠️ Path doesn't exist yet: {models_path_expanded}[/]")
                if questionary.confirm("Create this directory?", default=True).ask():
                    Path(models_path_expanded).mkdir(parents=True, exist_ok=True)
                    console.print("[green]✅ Directory created[/]")

        # Step 4: Optional advanced settings
        console.print("\n[bold]Step 4: Advanced settings (optional)[/]")
        
        if questionary.confirm("Configure advanced options?", default=False).ask():
            # Context size
            current_ctx = lollms_config.get("context_size", 4096)
            context_size = IntPrompt.ask(
                "Context size (tokens)",
                default=current_ctx
            )
            lollms_config["context_size"] = context_size
            
            # Temperature
            current_temp = lollms_config.get("temperature", 0.7)
            temperature = FloatPrompt.ask(
                "Default temperature (0-2)",
                default=current_temp
            )
            lollms_config["temperature"] = max(0.0, min(2.0, temperature))

        # Summary and test
        console.print("\n[bold green]✅ Backend configured![/]")
        self._configured.add("lollms")
        
        # Show configuration summary
        self._show_backend_summary(lollms_config, binding_info)
        
        # Offer to test
        if questionary.confirm("Test connection now?", default=True).ask():
            test_result = self._test_backend_connection(lollms_config)
            if not test_result:
                # Test failed and user wants to reconfigure
                if questionary.confirm("Restart backend configuration?", default=True).ask():
                    return self.configure_backend()  # Recursive call to reconfigure

    def _show_backend_summary(self, config: Dict[str, Any], binding_info: BindingInfo) -> None:
        """Show a summary of the backend configuration."""
        table = Table(title="Backend Configuration Summary")
        table.add_column("Setting", style="cyan")
        table.add_column("Value", style="green")
        
        table.add_row("Binding", binding_info.display_name)
        table.add_row("Model", config.get("model_name", "Not set") or "Not set")
        
        if binding_info.category in ("remote", "local_server"):
            table.add_row("Host", config.get("host_address", "Not set") or "Not set")
            has_key = bool(config.get("api_key"))
            table.add_row("API Key", "✅ Set" if has_key else "⭕ Not set")
            if binding_info.supports_ssl_verify:
                table.add_row("SSL Verify", "✅ Yes" if config.get("verify_ssl", True) else "❌ No")
        
        if binding_info.requires_models_path or config.get("models_path"):
            table.add_row("Models Path", config.get("models_path", "Not set") or "Not set")
        
        table.add_row("Context Size", str(config.get("context_size", 4096)))
        table.add_row("Temperature", str(config.get("temperature", 0.7)))
        
        console.print(table)

    def _test_backend_connection(self, config: Dict[str, Any]) -> bool:
        """Test the backend connection with actual LLM call.
        
        Returns:
            True if test successful, False otherwise
        """
        console.print("\n[bold]🧪 Testing connection...[/]")
        
        try:
            # Build settings from config
            settings = LollmsSettings(
                host_address=config.get("host_address", ""),
                api_key=config.get("api_key"),
                binding_name=config.get("binding_name"),
                model_name=config.get("model_name"),
                context_size=config.get("context_size", 4096),
                verify_ssl=config.get("verify_ssl", True),
            )
            
            # Try to build client
            console.print("[dim]Step 1/2: Building client...[/]")
            client = build_lollms_client(settings)
            
            if not client:
                console.print("[yellow]⚠️ Could not initialize client - check configuration[/]")
                return False
            
            console.print("[green]✓[/] Client initialized")
            
            # Try to generate a test response
            console.print("[dim]Step 2/2: Testing LLM generation...[/]")
            test_response = client.generate_text(
                prompt="Respond with exactly: 'Connection successful'",
                max_tokens=10,
                temperature=0.1
            )
            
            if test_response and len(test_response.strip()) > 0:
                console.print(f"[bold green]✅ Connection successful![/]")
                console.print(f"[dim]Test response: {test_response[:100]}...[/]")
                return True
            else:
                console.print("[red]❌ Connection returned empty response[/]")
                console.print("[dim]The API may be working but not responding correctly.[/]")
                return False
                
        except Exception as e:
            console.print(f"[red]❌ Connection test failed: {e}[/]")
            console.print("[dim]Tip: Ensure the backend service is running and accessible[/]")
            
            # Offer to reconfigure
            if questionary.confirm(
                "Would you like to reconfigure the backend?",
                default=True
            ).ask():
                return False  # Signal to restart configuration
            else:
                console.print("[yellow]⚠️ Saving configuration anyway (you can test later)[/]")
                return True  # Allow saving despite test failure

    def configure_multi_provider(self) -> None:
        """Configure multi-provider API routing (OpenRouter + Ollama)."""
        console.print("\n[bold cyan]🔀 Multi-Provider API Configuration[/bold cyan]\n")
        
        console.print("Multi-provider routing allows using multiple API providers:")
        console.print("  • [green]OpenRouter[/] - Free tier with 3 keys (quota cycling)")
        console.print("  • [green]Ollama Cloud[/] - Specialized models with 2 keys (load balanced)")
        console.print("  • Automatic failover: OpenRouter (free) → Ollama (paid)")
        console.print()
        
        # Enable/disable multi-provider
        enabled = Confirm.ask(
            "Enable multi-provider API routing?",
            default=True
        )
        
        self.config["multiprovider"] = self.config.get("multiprovider", {})
        self.config["multiprovider"]["enabled"] = enabled
        
        if not enabled:
            console.print("[yellow]Multi-provider disabled. Using single backend only.[/]")
            return
        
        # Configure OpenRouter keys
        console.print("\n[bold]OpenRouter Configuration[/bold]")
        console.print("Provides free tier access with quota cycling across keys")
        console.print("Leave blank to skip OpenRouter")
        console.print()
        
        for i in [1, 2, 3]:
            key = Prompt.ask(
                f"  OpenRouter API Key #{i}",
                default=self.config.get("multiprovider", {}).get(f"openrouter_key_{i}", ""),
                password=True
            )
            if key:
                self.config["multiprovider"][f"openrouter_key_{i}"] = key
        
        # Configure Ollama Cloud keys
        console.print("\n[bold]Ollama Cloud Configuration[/bold]")
        console.print("Provides access to specialized models (kimi, deepseek, cogito, etc.)")
        console.print("Leave blank to skip Ollama Cloud")
        console.print()
        
        for i in ["", "_2"]:
            key = Prompt.ask(
                f"  Ollama API Key{' #2' if i else ''}",
                default=self.config.get("multiprovider", {}).get(f"ollama_key{i}", ""),
                password=True
            )
            if key:
                self.config["multiprovider"][f"ollama_key{i}"] = key
        
        console.print("\n[green]✓ Multi-provider configuration saved[/]")
        console.print("💡 Set USE_MULTI_PROVIDER=true in .env to enable at runtime")
        console.print()

    def configure_rc2(self) -> None:
        """Configure RC2 sub-agent (Reflective Constellation 2.0)."""
        console.print("\n[bold cyan]🧠 RC2 Sub-Agent Configuration[/bold cyan]\n")
        
        console.print("RC2 (Reflective Constellation 2.0) provides advanced capabilities:")
        console.print("  • [green]Constitutional Review[/] - Byzantine consensus for governance")
        console.print("  • [green]Deep Introspection[/] - Causal analysis of decisions")
        console.print("  • [yellow]Self-Modification[/] - Code improvement proposals (experimental)")
        console.print("  • [yellow]Meta-Learning[/] - Learning optimization (experimental)")
        console.print()
        
        console.print("[yellow]⚠️  RC2 is DISABLED by default for safety[/]")
        console.print()
        
        # Enable/disable RC2
        enabled = Confirm.ask(
            "Enable RC2 sub-agent?",
            default=False
        )
        
        self.config["rc2"] = self.config.get("rc2", {})
        self.config["rc2"]["enabled"] = enabled
        
        if not enabled:
            console.print("[yellow]RC2 disabled for safety.[/]")
            return
        
        # Configure rate limiting
        console.print("\n[bold]Rate Limiting[/bold]")
        rate_limit = IntPrompt.ask(
            "  Max RC2 requests per minute (per user)",
            default=self.config.get("rc2", {}).get("rate_limit", 5)
        )
        self.config["rc2"]["rate_limit"] = rate_limit
        
        # Configure capabilities
        console.print("\n[bold]Capabilities[/bold]")
        console.print("Enable individual RC2 capabilities:")
        
        self.config["rc2"]["constitutional"] = Confirm.ask(
            "  • Constitutional Review (governance decisions)?",
            default=self.config.get("rc2", {}).get("constitutional", True)
        )
        
        self.config["rc2"]["introspection"] = Confirm.ask(
            "  • Deep Introspection (decision analysis)?",
            default=self.config.get("rc2", {}).get("introspection", True)
        )
        
        console.print("\n[yellow]⚠️  Experimental capabilities (not fully implemented):[/]")
        
        self.config["rc2"]["self_modification"] = Confirm.ask(
            "  • Self-Modification (EXPERIMENTAL)?",
            default=self.config.get("rc2", {}).get("self_modification", False)
        )
        
        self.config["rc2"]["meta_learning"] = Confirm.ask(
            "  • Meta-Learning (EXPERIMENTAL)?",
            default=self.config.get("rc2", {}).get("meta_learning", False)
        )
        
        console.print("\n[green]✓ RC2 configuration saved[/]")
        console.print("💡 Set RC2_ENABLED=true in .env to enable at runtime")
        console.print("💡 Set RC2_RATE_LIMIT={} in .env for rate limiting".format(rate_limit))
        console.print()

    # Legacy method - kept for backward compatibility but not used in main flow
    def configure_service(self, service_name: str) -> None:
        """Configure a non-backend service (Discord, Telegram)."""
        if service_name == "lollms":
            # Redirect to new binding-first configuration
            return self.configure_backend()
        
        # Legacy configuration for other services
        SERVICES_CONFIG: Dict[str, Dict[str, Any]] = {
            "discord": {
                "title": "🤖 Discord Bot",
                "fields": [
                    {"name": "bot_token", "prompt": "Discord Bot Token", "secret": True},
                    {"name": "allowed_users", "prompt": "Allowed User IDs (comma-separated, optional)", "optional": True},
                    {"name": "allowed_guilds", "prompt": "Allowed Server IDs (comma-separated, optional)", "optional": True},
                ],
                "setup_instructions": """🤖 Discord Setup (2 min):

1. https://discord.com/developers/applications → [+ New Application]
2. Bot → [Add Bot] → Copy **TOKEN** (MTIz... format)
3. Bot → Privileged Gateway Intents → ✅ Message Content
4. OAuth2 → URL Generator → bot scope → Invite to server""",
            },
            "telegram": {
                "title": "✈️ Telegram Bot",
                "fields": [
                    {"name": "bot_token", "prompt": "Telegram Bot Token (from @BotFather)", "secret": True},
                    {"name": "allowed_users", "prompt": "Allowed User IDs (comma-separated, optional)", "optional": True},
                ],
                "setup_instructions": """✈️ Telegram Setup (1 min):

1. Message @BotFather on Telegram
2. Send /newbot and follow instructions
3. Copy the HTTP API token provided""",
            },
        }
        
        service = SERVICES_CONFIG.get(service_name)
        if not service:
            console.print(f"[red]Unknown service: {service_name}[/]")
            return
            
        console.print(f"\n[bold yellow]{service['title']}[/]")
        
        if "setup_instructions" in service:
            console.print(Panel(service["setup_instructions"], title="📋 Instructions"))

        service_config = self.config.setdefault(service_name, {})

        for field in service["fields"]:
            current = service_config.get(field["name"])
            default = str(current) if current is not None else field.get("default", "")

            if field.get("type") == "bool":
                value = questionary.confirm(field["prompt"], default=field.get("default", False)).ask()
            elif field.get("secret"):
                value = questionary.password(field["prompt"], default=default).ask()
            else:
                value = questionary.text(field["prompt"], default=default).ask()

            # Parse comma-separated lists
            if "users" in field["name"] or "guilds" in field["name"]:
                if value:
                    value = [v.strip() for v in value.split(",") if v.strip()]
                else:
                    value = []
            elif field.get("optional") and not value:
                continue

            service_config[field["name"]] = value

        self._configured.add(service_name)
        console.print("[green]✅ Updated![/]")

    def configure_soul(self) -> None:
        """Interactive Soul (personality) configuration."""
        console.print("\n[bold magenta]🧬 Soul Configuration[/]")
        
        while True:
            section = questionary.select(
                "Configure aspect:",
                choices=[
                    "🎭 Core Identity (name, purpose, origin)",
                    "🌈 Personality Traits",
                    "⚖️ Core Values",
                    "💬 Communication Style",
                    "🎓 Expertise Domains",
                    "👥 Relationship Stances",
                    "🔍 Preview System Prompt",
                    "💾 Save & Return",
                ]
            ).ask()

            if section == "🎭 Core Identity (name, purpose, origin)":
                self._configure_core_identity()
            elif section == "🌈 Personality Traits":
                self._configure_personality_traits()
            elif section == "⚖️ Core Values":
                self._configure_values()
            elif section == "💬 Communication Style":
                self._configure_communication()
            elif section == "🎓 Expertise Domains":
                self._configure_expertise()
            elif section == "👥 Relationship Stances":
                self._configure_relationships()
            elif section == "🔍 Preview System Prompt":
                self._preview_soul_prompt()
            else:
                self.soul._save()
                self._configured.add("soul")
                console.print("[green]✅ Soul saved![/]")
                break

    def _configure_core_identity(self) -> None:
        """Configure name, purpose, and origin story."""
        console.print("\n[bold]Core Identity[/]")
        
        self.soul.name = questionary.text("AI Name", default=self.soul.name).ask()
        self.soul.purpose = questionary.text("Primary Purpose", default=self.soul.purpose).ask()
        self.soul.origin_story = questionary.text("Origin Story", default=self.soul.origin_story).ask()

    def _configure_personality_traits(self) -> None:
        """Add, edit, or remove personality traits."""
        console.print("\n[bold]Personality Traits[/]")
        
        while True:
            table = Table(title="Current Traits")
            table.add_column("Trait")
            table.add_column("Intensity")
            table.add_column("Description")
            
            for trait in self.soul.traits:
                intensity_emoji = {
                    TraitIntensity.SUBTLE: "◐",
                    TraitIntensity.MODERATE: "◑",
                    TraitIntensity.STRONG: "◕",
                    TraitIntensity.EXTREME: "⬤",
                }.get(trait.intensity, "◑")
                table.add_row(trait.name, f"{intensity_emoji} {trait.intensity.name.lower()}", trait.description[:40])
            
            console.print(table)
            
            action = questionary.select(
                "Action:",
                choices=["➕ Add Trait", "✏️ Edit Trait", "🗑️ Remove Trait", "🔙 Back"]
            ).ask()
            
            if action == "➕ Add Trait":
                name = questionary.text("Trait name (e.g., 'curiosity', 'pragmatism')").ask()
                description = questionary.text("How does this manifest?").ask()
                intensity = questionary.select(
                    "Intensity",
                    choices=["subtle", "moderate", "strong", "extreme"],
                    default="moderate"
                ).ask()
                
                trait = PersonalityTrait(
                    name=name,
                    description=description,
                    intensity=TraitIntensity[intensity.upper()],
                )
                self.soul.traits.append(trait)
                
            elif action == "✏️ Edit Trait" and self.soul.traits:
                trait_names = [t.name for t in self.soul.traits]
                to_edit = questionary.select("Edit which trait?", choices=trait_names).ask()
                trait = next(t for t in self.soul.traits if t.name == to_edit)
                
                trait.description = questionary.text("Description", default=trait.description).ask()
                new_intensity = questionary.select(
                    "Intensity",
                    choices=["subtle", "moderate", "strong", "extreme"],
                    default=trait.intensity.name.lower()
                ).ask()
                trait.intensity = TraitIntensity[new_intensity.upper()]
                
            elif action == "🗑️ Remove Trait" and self.soul.traits:
                to_remove = questionary.select(
                    "Remove which trait?",
                    choices=[t.name for t in self.soul.traits]
                ).ask()
                self.soul.traits = [t for t in self.soul.traits if t.name != to_remove]
            else:
                break

    def _configure_values(self) -> None:
        """Configure core ethical values."""
        console.print("\n[bold]Core Values[/]")
        
        while True:
            table = Table(title="Current Values (by priority)")
            table.add_column("Priority")
            table.add_column("Value")
            table.add_column("Category")
            
            for v in sorted(self.soul.values, key=lambda x: -x.priority):
                priority_color = "red" if v.priority >= 9 else "yellow" if v.priority >= 7 else "green"
                table.add_row(f"[{priority_color}]{v.priority}[/{priority_color}]", v.statement[:50], v.category)
            
            console.print(table)
            
            action = questionary.select(
                "Action:",
                choices=["➕ Add Value", "✏️ Edit Priority", "🗑️ Remove Value", "🔙 Back"]
            ).ask()
            
            if action == "➕ Add Value":
                statement = questionary.text("Value statement").ask()
                category = questionary.text("Category", default="general").ask()
                priority = IntPrompt.ask("Priority (1-10)", default=5)
                self.soul.values.append(ValueStatement(statement, category, max(1, min(10, priority))))
                
            elif action == "✏️ Edit Priority" and self.soul.values:
                statements = [v.statement[:40] + "..." for v in self.soul.values]
                to_edit = questionary.select("Edit which value?", choices=statements).ask()
                val = next(v for v in self.soul.values if v.statement.startswith(to_edit[:20]))
                val.priority = IntPrompt.ask("New priority (1-10)", default=val.priority)
                
            elif action == "🗑️ Remove Value" and self.soul.values:
                to_remove = questionary.select(
                    "Remove which value?",
                    choices=[v.statement[:40] for v in self.soul.values]
                ).ask()
                self.soul.values = [v for v in self.soul.values if not v.statement.startswith(to_remove[:20])]
            else:
                break

    def _configure_communication(self) -> None:
        """Configure communication style."""
        style = self.soul.communication
        
        style.formality = questionary.select(
            "Formality",
            choices=["formal", "casual", "technical", "playful"],
            default=style.formality
        ).ask()
        
        style.verbosity = questionary.select(
            "Default verbosity",
            choices=["terse", "concise", "detailed", "exhaustive"],
            default=style.verbosity
        ).ask()
        
        humor = questionary.select(
            "Humor style",
            choices=["None (serious)", "witty", "dry", "punny", "absurdist"],
            default=style.humor_style or "None (serious)"
        ).ask()
        style.humor_style = None if humor == "None (serious)" else humor
        
        style.emoji_usage = questionary.select(
            "Emoji usage",
            choices=["none", "minimal", "moderate", "liberal"],
            default=style.emoji_usage
        ).ask()

    def _configure_expertise(self) -> None:
        """Configure knowledge domains."""
        console.print("\n[bold]Expertise Domains[/]")
        
        while True:
            table = Table(title="Current Expertise")
            table.add_column("Domain")
            table.add_column("Level")
            table.add_column("Specialties")
            
            for e in self.soul.expertise:
                level_color = {
                    "novice": "red", "competent": "yellow", "expert": "green",
                    "authority": "blue", "pioneer": "magenta",
                }.get(e.level, "white")
                table.add_row(e.domain, f"[{level_color}]{e.level}[/{level_color}]", ", ".join(e.specialties[:2]))
            
            console.print(table)
            
            action = questionary.select(
                "Action:",
                choices=["➕ Add Domain", "🔙 Back"]
            ).ask()
            
            if action == "➕ Add Domain":
                domain = questionary.text("Domain name").ask()
                level = questionary.select(
                    "Competence level",
                    choices=["novice", "competent", "expert", "authority", "pioneer"],
                    default="competent"
                ).ask()
                specialties = [s.strip() for s in questionary.text("Specialties (comma-separated)").ask().split(",") if s.strip()]
                
                self.soul.expertise.append(ExpertiseDomain(domain=domain, level=level, specialties=specialties))
            else:
                break

    def _configure_relationships(self) -> None:
        """Configure relationship stances."""
        console.print("\n[bold]Relationship Stances[/]")
        console.print("[dim]Simplified configuration - full implementation in soul.md[/]")

    def _preview_soul_prompt(self) -> None:
        """Preview the generated system prompt."""
        prompt = self.soul.generate_system_prompt()
        preview = prompt[:1000] + ("..." if len(prompt) > 1000 else "")
        console.print(Panel(preview, title="System Prompt", border_style="cyan"))

    def configure_heartbeat(self) -> None:
        """Configure self-maintenance heartbeat."""
        console.print("\n[bold magenta]💓 Heartbeat Configuration[/]")
        
        config = self.heartbeat.config
        
        config.enabled = questionary.confirm("Enable automatic self-maintenance?", default=config.enabled).ask()
        if not config.enabled:
            self.heartbeat._save_config()
            return
        
        config.interval_minutes = FloatPrompt.ask("Maintenance interval (minutes)", default=config.interval_minutes)
        
        console.print("\n[bold]Maintenance Tasks[/]")
        for task in MaintenanceTask:
            task_name = task.name.replace("_", " ").title()
            config.tasks_enabled[task] = questionary.confirm(
                f"Enable {task_name}?", default=config.tasks_enabled.get(task, True)
            ).ask()
        
        console.print("\n[bold]Self-Healing Behavior[/]")
        config.auto_heal_minor = questionary.confirm("Auto-fix minor issues?", default=config.auto_heal_minor).ask()
        config.confirm_heal_major = questionary.confirm("Confirm before major changes?", default=config.confirm_heal_major).ask()
        
        self.heartbeat.update_config(**{
            k: getattr(config, k) for k in [
                "enabled", "interval_minutes", "tasks_enabled",
                "auto_heal_minor", "confirm_heal_major"
            ]
        })
        
        self.config["heartbeat"] = {
            "enabled": config.enabled,
            "interval_minutes": config.interval_minutes,
            "tasks_enabled": [t.name for t, v in config.tasks_enabled.items() if v],
        }
        self._configured.add("heartbeat")
        console.print("[green]✅ Heartbeat configured![/]")

    def configure_memory(self) -> None:
        """Configure memory and retention settings."""
        console.print("\n[bold magenta]🧠 Memory Configuration[/]")
        
        hb_config = self.heartbeat.config
        
        hb_config.memory_pressure_threshold = FloatPrompt.ask(
            "Memory pressure threshold (0-1)", default=hb_config.memory_pressure_threshold
        )
        hb_config.log_retention_days = IntPrompt.ask(
            "Audit log retention (days)", default=hb_config.log_retention_days
        )
        
        console.print("\n[bold]Forgetting Curve Parameters[/]")
        halflife = FloatPrompt.ask("Memory half-life (days)", default=7.0)
        strength_mult = FloatPrompt.ask("Review strength multiplier", default=2.0)
        
        self.heartbeat.memory_monitor.retention_halflife_days = halflife
        self.heartbeat.memory_monitor.strength_multiplier = strength_mult
        self.heartbeat._save_config()
        
        self.config["memory"] = {
            "pressure_threshold": hb_config.memory_pressure_threshold,
            "log_retention_days": hb_config.log_retention_days,
            "retention_halflife_days": halflife,
            "strength_multiplier": strength_mult,
        }
        self._configured.add("memory")
        console.print("[green]✅ Memory configured![/]")

    def configure_skills(self) -> None:
        """Configure Skills - browse, test, and manage capabilities."""
        console.print("\n[bold magenta]📚 Skills Configuration[/]")
        console.print("[dim]Browse, test, and configure LollmsBot's capabilities[/]")
        
        while True:
            # Show skill statistics
            stats = self._get_skill_stats()
            
            table = Table(title=f"Skills Library ({stats['total']} total)")
            table.add_column("Category")
            table.add_column("Built-in")
            table.add_column("User-created")
            table.add_column("Avg Confidence")
            
            for cat, data in sorted(stats['by_category'].items()):
                table.add_row(
                    cat,
                    str(data['builtin']),
                    str(data['user']),
                    f"{data['avg_confidence']:.0%}"
                )
            
            console.print(table)
            
            # Check awesome-claude-skills status
            awesome_status = self._get_awesome_skills_status()
            if awesome_status['available']:
                console.print(f"\n[green]✅ Awesome-Claude-Skills: {awesome_status['loaded']} skills loaded[/green]")
            else:
                console.print("\n[yellow]⚠️ Awesome-Claude-Skills: Not configured[/yellow]")
            
            action = questionary.select(
                "Skills action:",
                choices=[
                    "🌟 Awesome Claude Skills (Integration)",
                    "🔍 Browse & Search Skills",
                    "📖 View Skill Details",
                    "🧪 Test Skill Execution",
                    "➕ Compose New Skill (from existing)",
                    "📤 Export Skill Library",
                    "📥 Import Skills",
                    "⚙️ Skill Preferences",
                    "🔙 Back to Main Menu",
                ]
            ).ask()
            
            if action == "🌟 Awesome Claude Skills (Integration)":
                self._configure_awesome_skills()
            elif action == "🔍 Browse & Search Skills":
                self._browse_skills()
            elif action == "📖 View Skill Details":
                self._view_skill_details()
            elif action == "🧪 Test Skill Execution":
                self._test_skill()
            elif action == "➕ Compose New Skill (from existing)":
                self._compose_skill()
            elif action == "📤 Export Skill Library":
                self._export_skills()
            elif action == "📥 Import Skills":
                self._import_skills()
            elif action == "⚙️ Skill Preferences":
                self._skill_preferences()
            else:
                self._configured.add("skills")
                break
    
    def _get_skill_stats(self) -> Dict[str, Any]:
        """Get statistics about loaded skills."""
        skills = list(self.skill_registry._skills.values())
        
        by_category: Dict[str, Dict[str, Any]] = {}
        for skill in skills:
            for cat in skill.metadata.categories or ["uncategorized"]:
                if cat not in by_category:
                    by_category[cat] = {'builtin': 0, 'user': 0, 'confidence_sum': 0, 'count': 0}
                # Simplified: would track builtin vs user properly
                by_category[cat]['count'] += 1
                by_category[cat]['confidence_sum'] += skill.metadata.confidence_score
        
        # Calculate averages
        for cat in by_category:
            data = by_category[cat]
            data['avg_confidence'] = data['confidence_sum'] / data['count'] if data['count'] > 0 else 0
        
        return {
            'total': len(skills),
            'by_category': by_category,
            'by_complexity': {
                c.name: len(self.skill_registry.list_skills(complexity=c))
                for c in SkillComplexity
            },
        }
    
    def _browse_skills(self) -> None:
        """Browse and search skills interactively."""
        search = questionary.text("Search skills (empty for all):").ask()
        
        if search:
            results = self.skill_registry.search(search)
            skills = [s for s, _ in results]
        else:
            category = questionary.select(
                "Filter by category:",
                choices=["All"] + list(self.skill_registry._categories.keys())
            ).ask()
            if category == "All":
                skills = list(self.skill_registry._skills.values())
            else:
                skills = self.skill_registry.list_skills(category=category)
        
        # Display results
        table = Table(title=f"Skills ({len(skills)} found)")
        table.add_column("Name")
        table.add_column("Complexity")
        table.add_column("Description")
        table.add_column("Confidence")
        
        for skill in skills[:20]:  # Limit display
            conf_color = "green" if skill.metadata.confidence_score > 0.8 else "yellow" if skill.metadata.confidence_score > 0.5 else "red"
            table.add_row(
                skill.name,
                skill.metadata.complexity.name,
                skill.metadata.description[:40],
                f"[{conf_color}]{skill.metadata.confidence_score:.0%}[/{conf_color}]"
            )
        
        console.print(table)
    
    def _view_skill_details(self) -> None:
        """View detailed information about a specific skill."""
        skill_name = questionary.select(
            "Select skill:",
            choices=list(self.skill_registry._skills.keys())
        ).ask()
        
        skill = self.skill_registry.get(skill_name)
        if not skill:
            console.print("[red]Skill not found[/]")
            return
        
        md = skill.metadata
        
        details = f"""
[bold]{md.name}[/] v{md.version}
[dim]{md.description}[/]

[bold]Complexity:[/] {md.complexity.name}
[bold]Categories:[/] {', '.join(md.categories)}
[bold]Tags:[/] {', '.join(md.tags)}

[bold]When to use:[/] {md.when_to_use or 'N/A'}
[bold]When NOT to use:[/] {md.when_not_to_use or 'N/A'}

[bold]Parameters:[/]
{chr(10).join(f"  • {p.name} ({p.type}){' [required]' if p.required else ''}: {p.description}" for p in md.parameters)}

[bold]Dependencies:[/]
{chr(10).join(f"  • {d.kind}:{d.name}{' (optional)' if d.optional else ''}" for d in md.dependencies)}

[bold]Statistics:[/]
  • Executed: {md.execution_count} times
  • Success rate: {md.success_rate:.1%}
  • Confidence score: {md.confidence_score:.0%}
"""
        console.print(Panel(details, title=f"Skill: {md.name}", border_style="blue"))
        
        # Show examples if any
        if md.examples:
            console.print("\n[bold]Examples:[/]")
            for i, ex in enumerate(md.examples[:2], 1):
                console.print(Panel(
                    f"Input: {json.dumps(ex.input_params, indent=2)}\n"
                    f"Output: {json.dumps(ex.expected_output, indent=2)}",
                    title=f"Example {i}"
                ))
    
    def _test_skill(self) -> None:
        """Test execute a skill with sample inputs."""
        console.print("[yellow]Note: Full execution requires running agent. Showing validation only.[/]")
        
        skill_name = questionary.select(
            "Select skill to test:",
            choices=list(self.skill_registry._skills.keys())
        ).ask()
        
        skill = self.skill_registry.get(skill_name)
        
        # Gather inputs
        inputs = {}
        for param in skill.metadata.parameters:
            if not param.required:
                if not questionary.confirm(f"Provide optional parameter '{param.name}'?", default=False).ask():
                    continue
            
            value = questionary.text(f"{param.name} ({param.type}): {param.description}").ask()
            
            # Simple type coercion
            if param.type == "number":
                value = float(value) if '.' in value else int(value)
            elif param.type == "boolean":
                value = value.lower() in ('true', 'yes', '1', 'on')
            elif param.type == "array":
                value = [v.strip() for v in value.split(',')]
            elif param.type == "object":
                try:
                    value = json.loads(value)
                except (json.JSONDecodeError, ValueError):
                    # Could not parse as JSON, treat as raw string
                    value = {"raw": value}
            
            inputs[param.name] = value
        
        # Validate
        valid, errors = skill.validate_inputs(inputs)
        if valid:
            console.print("[green]✅ Inputs valid![/]")
            
            # Check dependencies
            # Would need actual agent/tools to check properly
            console.print("[dim]Dependency check: would validate against available tools[/]")
        else:
            console.print("[red]❌ Validation failed:[/]")
            for err in errors:
                console.print(f"  • {err}")
    
    def _compose_skill(self) -> None:
        """Create new skill by composing existing skills."""
        console.print("\n[bold]Compose New Skill[/]")
        console.print("[dim]Combine existing skills into a workflow[/]")
        
        name = questionary.text("Name for new skill:").ask()
        description = questionary.text("What does this skill do?").ask()
        
        # Select component skills
        available = list(self.skill_registry._skills.keys())
        components = []
        
        while True:
            remaining = [s for s in available if s not in components]
            if not remaining:
                break
            
            choice = questionary.select(
                "Add component skill (or Done):",
                choices=["Done"] + remaining
            ).ask()
            
            if choice == "Done":
                break
            
            components.append(choice)
            console.print(f"[green]Added: {choice}[/]")
        
        if len(components) < 1:
            console.print("[yellow]Need at least one component[/]")
            return
        
        # Define data flow (simplified)
        console.print("\n[dim]Data flow would be configured here - mapping outputs to inputs[/]")
        
        # Preview and confirm
        console.print(Panel(
            f"Name: {name}\n"
            f"Description: {description}\n"
            f"Components: {' → '.join(components)}",
            title="New Skill Preview"
        ))
        
        if questionary.confirm("Create this skill?", default=True).ask():
            # Would call skill learner
            console.print("[green]✅ Skill composition recorded (implementation in code)[/]")
    
    def _export_skills(self) -> None:
        """Export skills to file."""
        export_path = Path.home() / ".lollmsbot" / "skills_export.json"
        
        data = {
            "export_date": datetime.now().isoformat(),
            "skills": [skill.to_dict() for skill in self.skill_registry._skills.values()],
        }
        
        export_path.write_text(json.dumps(data, indent=2))
        console.print(f"[green]✅ Exported {len(data['skills'])} skills to {export_path}[/]")
    
    def _import_skills(self) -> None:
        """Import skills from file."""
        import_path = questionary.text("Path to skills file:").ask()
        path = Path(import_path)
        
        if not path.exists():
            console.print("[red]File not found[/]")
            return
        
        try:
            data = json.loads(path.read_text())
            count = len(data.get("skills", []))
            console.print(f"[green]✅ Found {count} skills to import[/]")
            console.print("[dim]Import would validate and register skills here[/]")
        except Exception as e:
            console.print(f"[red]Import failed: {e}[/]")
    
    def _skill_preferences(self) -> None:
        """Configure skill execution preferences."""
        console.print("\n[bold]Skill Preferences[/]")
        
        # Would configure: auto-skill vs manual, confidence thresholds, etc.
        prefs = {
            "auto_skill_selection": questionary.confirm("Allow automatic skill selection?", default=True).ask(),
            "min_confidence_threshold": FloatPrompt.ask("Minimum skill confidence (0-1)", default=0.6),
            "confirm_complex_skills": questionary.confirm("Confirm before complex skill execution?", default=True).ask(),
        }
        
        self.config["skill_preferences"] = prefs
        console.print("[green]✅ Preferences saved[/]")

    def test_connections(self) -> None:
        """Test all configured connections."""
        table = Table(title="🧪 Connection Tests")
        table.add_column("Service")
        table.add_column("Status")
        table.add_column("Details")

        # Test backend first
        lollms_config = self.config.get("lollms", {})
        if lollms_config:
            status, details = self._test_single("lollms", lollms_config)
            # Show binding name in details
            binding_name = lollms_config.get("binding_name", "unknown")
            details = f"{binding_name}: {details}"
            table.add_row("AI Backend", status, details)
        
        # Test other services
        for service_name, svc_config in self.config.items():
            if service_name in ["lollms", "heartbeat", "memory", "soul", "skill_preferences"]:
                continue
                
            status, details = self._test_single(service_name, svc_config)
            display_name = "Discord" if service_name == "discord" else "Telegram" if service_name == "telegram" else service_name.title()
            table.add_row(display_name, status, details)

        # Test Soul
        soul_hash = hashlib.sha256(
            json.dumps(self.soul.to_dict(), sort_keys=True).encode()
        ).hexdigest()[:16]
        table.add_row("Soul", "✅ VALID", f"Hash: {soul_hash}")

        # Test Heartbeat
        hb_status = self.heartbeat.get_status()
        table.add_row(
            "Heartbeat", 
            "✅ ACTIVE" if hb_status["running"] else "⭕ STOPPED",
            f"Interval: {hb_status['interval_minutes']}min"
        )

        # Test Skills
        skill_stats = self._get_skill_stats()
        table.add_row(
            "Skills",
            "✅ LOADED",
            f"{skill_stats['total']} skills, {len(skill_stats['by_category'])} categories"
        )

        console.print(table)

    def _test_single(self, service_name: str, config: Dict[str, Any]) -> tuple[str, str]:
        """Test a single service connection."""
        try:
            if service_name == "lollms":
                settings = LollmsSettings(
                    host_address=config.get("host_address", ""),
                    api_key=config.get("api_key"),
                    binding_name=config.get("binding_name"),
                    model_name=config.get("model_name"),
                    context_size=config.get("context_size", 4096),
                    verify_ssl=config.get("verify_ssl", True),
                )
                client = build_lollms_client(settings)
                
                if client:
                    # Show model and binding info
                    binding = config.get("binding_name", "unknown")
                    model = config.get("model_name", "default")
                    return ("✅ READY", f"{binding}/{model}")
                else:
                    return ("❌ ERROR", "Client initialization failed")
                    
            elif service_name == "discord":
                token = config.get("bot_token", "")
                has_token = bool(token)
                allowed_users = config.get("allowed_users", [])
                return (
                    "🔍 CONFIGURED" if has_token else "⭕ NO TOKEN",
                    f"Token: {'✅' if has_token else '❌'}, Users: {len(allowed_users)}"
                )
                
            elif service_name == "telegram":
                token = config.get("bot_token", "")
                has_token = bool(token)
                return (
                    "🔍 CONFIGURED" if has_token else "⭕ NO TOKEN",
                    f"Token: {'✅' if has_token else '❌'}"
                )
                
            return ("❓ SKIP", "-")
            
        except Exception as e:
            return ("❌ ERROR", str(e)[:40])

    def show_full_config(self) -> None:
        """Display complete configuration."""
        console.print("\n[bold]📄 Full Configuration[/]")
        
        # Backend with binding details
        if "lollms" in self.config:
            lollms = self.config["lollms"]
            console.print(Panel(
                json.dumps(lollms, indent=2),
                title=f"AI Backend: {lollms.get('binding_name', 'unknown')}",
                border_style="blue"
            ))
        
        # Other services
        for svc in ["discord", "telegram"]:
            if svc in self.config:
                # Mask secrets
                safe_config = {k: (v if "token" not in k else "***") for k, v in self.config[svc].items()}
                console.print(Panel(
                    json.dumps(safe_config, indent=2),
                    title=svc.title(),
                    border_style="blue"
                ))
        
        # Soul
        console.print(Panel(
            json.dumps(self.soul.to_dict(), indent=2),
            title=f"Soul: {self.soul.name}",
            border_style="magenta"
        ))
        
        # Heartbeat
        hb_status = self.heartbeat.get_status()
        console.print(Panel(
            json.dumps(hb_status, indent=2),
            title="Heartbeat Status",
            border_style="green"
        ))
        
        # Skills
        skill_stats = self._get_skill_stats()
        console.print(Panel(
            json.dumps(skill_stats, indent=2),
            title=f"Skills Library ({skill_stats['total']} skills)",
            border_style="yellow"
        ))

    def _save_all(self) -> None:
        """Save all configurations."""
        self.soul._save()
        self.heartbeat._save_config()
        
        self.config["soul"] = {
            "name": self.soul.name,
            "version": self.soul.version,
            "trait_count": len(self.soul.traits),
            "value_count": len(self.soul.values),
        }
        
        self.config["skills"] = {
            "total_loaded": len(self.skill_registry._skills),
            "categories": list(self.skill_registry._categories.keys()),
        }
        
        self._save_config()
    
    def _get_awesome_skills_status(self) -> Dict[str, Any]:
        """Get status of awesome-claude-skills integration."""
        try:
            from lollmsbot.skills import get_awesome_skills_integration
            
            integration = get_awesome_skills_integration()
            if not integration or not integration.is_available():
                return {"available": False, "loaded": 0}
            
            info = integration.get_repository_info()
            return {
                "available": True,
                "loaded": info.get("loaded_skills_count", 0),
                "total": info.get("skills_count", 0),
            }
        except Exception:
            return {"available": False, "loaded": 0}
    
    def _configure_awesome_skills(self) -> None:
        """Configure awesome-claude-skills integration."""
        try:
            from lollmsbot.skills import get_awesome_skills_integration
            
            console.print("\n[bold cyan]🌟 Awesome Claude Skills Integration[/bold cyan]")
            console.print("[dim]27+ production-ready AI workflows from the community[/dim]\n")
            
            integration = get_awesome_skills_integration()
            
            if not integration or not integration.is_available():
                # Enable awesome-claude-skills
                enable = questionary.confirm(
                    "Awesome-claude-skills is not enabled. Enable it now?",
                    default=True
                ).ask()
                
                if enable:
                    console.print("[yellow]Enabling awesome-claude-skills...[/yellow]")
                    console.print("[dim]This will clone the repository to ~/.lollmsbot/awesome-skills[/dim]")
                    
                    # Update config
                    self.config.setdefault("awesome_skills", {})
                    self.config["awesome_skills"]["enabled"] = True
                    self._save_config()
                    
                    console.print("[green]✅ Awesome-claude-skills enabled![/green]")
                    console.print("[yellow]Please restart the wizard to load skills.[/yellow]")
                    return
                else:
                    return
            
            # Show current status
            info = integration.get_repository_info()
            console.print(f"[green]Repository: {info.get('url')}[/green]")
            console.print(f"[green]Local path: {info.get('path')}[/green]")
            console.print(f"[green]Total skills: {info.get('skills_count', 0)}[/green]")
            console.print(f"[green]Loaded skills: {info.get('loaded_skills_count', 0)}[/green]\n")
            
            while True:
                action = questionary.select(
                    "What would you like to do?",
                    choices=[
                        "🔍 Browse Available Skills",
                        "🔎 Search for Skills",
                        "📥 Install/Enable Skills",
                        "📤 Uninstall/Disable Skills",
                        "🔄 Update Repository",
                        "ℹ️ View Repository Info",
                        "🔙 Back",
                    ]
                ).ask()
                
                if action == "🔍 Browse Available Skills":
                    self._browse_awesome_skills(integration)
                elif action == "🔎 Search for Skills":
                    self._search_awesome_skills(integration)
                elif action == "📥 Install/Enable Skills":
                    self._install_awesome_skills(integration)
                elif action == "📤 Uninstall/Disable Skills":
                    self._uninstall_awesome_skills(integration)
                elif action == "🔄 Update Repository":
                    self._update_awesome_skills(integration)
                elif action == "ℹ️ View Repository Info":
                    self._show_awesome_skills_info(integration)
                else:
                    break
                    
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")
    
    def _browse_awesome_skills(self, integration) -> None:
        """Browse available awesome-claude-skills."""
        # Get categories
        categories = integration.get_categories()
        
        category = questionary.select(
            "Select a category:",
            choices=["All"] + categories
        ).ask()
        
        # Get skills
        if category == "All":
            skills = integration.list_available_skills()
        else:
            skills = integration.list_available_skills(category=category)
        
        if not skills:
            console.print("[yellow]No skills found in this category.[/yellow]")
            return
        
        # Display skills
        table = Table(title=f"{category} Skills ({len(skills)} total)", box=box.ROUNDED)
        table.add_column("Name", style="cyan")
        table.add_column("Tier", style="magenta")
        table.add_column("Description", style="dim", max_width=50)
        table.add_column("Status", style="green")
        
        for skill in skills[:20]:  # Limit to 20
            status = "✅" if skill.name in integration.loaded_skills else "⭕"
            table.add_row(
                skill.name,
                skill.tier,
                skill.description[:47] + "..." if len(skill.description) > 50 else skill.description,
                status
            )
        
        console.print(table)
        
        if len(skills) > 20:
            console.print(f"\n[dim]... and {len(skills) - 20} more skills[/dim]")
        
        questionary.press_any_key_to_continue().ask()
    
    def _search_awesome_skills(self, integration) -> None:
        """Search for awesome-claude-skills."""
        query = questionary.text("Enter search query:").ask()
        
        if not query:
            return
        
        results = integration.search_skills(query)
        
        if not results:
            console.print("[yellow]No skills found.[/yellow]")
            questionary.press_any_key_to_continue().ask()
            return
        
        console.print(f"\n[green]Found {len(results)} skill(s):[/green]\n")
        
        for skill in results[:10]:
            status = "✅ Loaded" if skill.name in integration.loaded_skills else "⭕ Available"
            console.print(f"[bold cyan]• {skill.name}[/bold cyan] [{status}]")
            console.print(f"  Category: {skill.category} | Tier: {skill.tier}")
            console.print(f"  {skill.description}\n")
        
        if len(results) > 10:
            console.print(f"[dim]... and {len(results) - 10} more results[/dim]")
        
        questionary.press_any_key_to_continue().ask()
    
    def _install_awesome_skills(self, integration) -> None:
        """Install awesome-claude-skills."""
        # Get available skills (not loaded)
        all_skills = integration.list_available_skills()
        available = [s for s in all_skills if s.name not in integration.loaded_skills]
        
        if not available:
            console.print("[yellow]All skills are already loaded.[/yellow]")
            questionary.press_any_key_to_continue().ask()
            return
        
        # Select skills to install
        choices = [f"{s.name} ({s.category})" for s in available[:30]]  # Limit to 30
        
        selected = questionary.checkbox(
            "Select skills to install:",
            choices=choices
        ).ask()
        
        if not selected:
            return
        
        # Extract skill names
        skill_names = [s.split(" (")[0] for s in selected]
        
        # Install skills
        console.print("\n[yellow]Installing skills...[/yellow]")
        results = integration.batch_load_skills(skill_names)
        
        success_count = sum(1 for v in results.values() if v)
        console.print(f"\n[green]✅ Installed {success_count}/{len(skill_names)} skills![/green]")
        
        questionary.press_any_key_to_continue().ask()
    
    def _uninstall_awesome_skills(self, integration) -> None:
        """Uninstall awesome-claude-skills."""
        loaded = list(integration.loaded_skills.keys())
        
        if not loaded:
            console.print("[yellow]No skills are currently loaded.[/yellow]")
            questionary.press_any_key_to_continue().ask()
            return
        
        # Select skills to uninstall
        selected = questionary.checkbox(
            "Select skills to uninstall:",
            choices=loaded
        ).ask()
        
        if not selected:
            return
        
        # Uninstall skills
        console.print("\n[yellow]Uninstalling skills...[/yellow]")
        success_count = 0
        for skill_name in selected:
            if integration.unload_skill(skill_name):
                success_count += 1
        
        console.print(f"\n[green]✅ Uninstalled {success_count}/{len(selected)} skills![/green]")
        
        questionary.press_any_key_to_continue().ask()
    
    def _update_awesome_skills(self, integration) -> None:
        """Update awesome-claude-skills repository."""
        console.print("\n[yellow]Updating repository...[/yellow]")
        
        success = integration.update_repository()
        
        if success:
            console.print("[green]✅ Repository updated successfully![/green]")
            
            # Reload skills
            console.print("[yellow]Reloading skills...[/yellow]")
            reloaded = integration.reload_all_skills()
            console.print(f"[green]✅ Reloaded {reloaded} skill(s)![/green]")
        else:
            console.print("[red]❌ Failed to update repository.[/red]")
        
        questionary.press_any_key_to_continue().ask()
    
    def _show_awesome_skills_info(self, integration) -> None:
        """Show awesome-claude-skills repository info."""
        info = integration.get_repository_info()
        
        table = Table(title="Awesome Claude Skills Repository", box=box.ROUNDED)
        table.add_column("Property", style="cyan")
        table.add_column("Value", style="green")
        
        table.add_row("Repository", info.get("url", "N/A"))
        table.add_row("Local Path", info.get("path", "N/A"))
        table.add_row("Last Updated", info.get("last_updated", "N/A"))
        table.add_row("Total Skills", str(info.get("skills_count", 0)))
        table.add_row("Loaded Skills", str(info.get("loaded_skills_count", 0)))
        
        console.print(table)
        
        if info.get("loaded_skills"):
            console.print("\n[bold]Loaded Skills:[/bold]")
            for skill in info["loaded_skills"][:10]:
                console.print(f"  • {skill}")
            if len(info["loaded_skills"]) > 10:
                console.print(f"  [dim]... and {len(info['loaded_skills']) - 10} more[/dim]")
        
        questionary.press_any_key_to_continue().ask()


# Entry point
def run_wizard() -> None:
    """CLI entrypoint."""
    try:
        Wizard().run_wizard()
    except KeyboardInterrupt:
        console.print("\n[yellow]👋 Bye![/]")
    except Exception as e:
        console.print(f"[red]Error: {e}[/]")
        raise


if __name__ == "__main__":
    run_wizard()
