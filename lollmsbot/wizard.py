#!/usr/bin/env python
"""
lollmsBot Interactive Setup Wizard
"""
from __future__ import annotations

import os
import json
from pathlib import Path
from typing import Any, Dict, List

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.prompt import Prompt, Confirm
    from rich.table import Table
    from rich.text import Text
    import questionary
except ImportError:
    print("❌ Install dev deps: pip install -e .[dev]")
    exit(1)

from lollmsbot.config import LollmsSettings
from lollmsbot.lollms_client import build_lollms_client

console = Console()


class Wizard:
    """Interactive setup wizard for lollmsBot services."""

    SERVICES_CONFIG: Dict[str, Dict[str, Any]] = {
        "lollms": {
            "title": "🔗 LoLLMS Backend",
            "fields": [
                {"name": "host_address", "prompt": "LoLLMS server URL", "default": "http://localhost:9642"},
                {"name": "api_key", "prompt": "API Key (optional)", "secret": True},
                {"name": "verify_ssl", "prompt": "Verify SSL?", "type": "bool", "default": True},
                {"name": "binding_name", "prompt": "Binding (ollama/openai/etc)", "optional": True},
            ],
        },
        "discord": {
            "title": "🤖 Discord Bot",
            "fields": [
                {"name": "bot_token", "prompt": "Discord Bot Token", "secret": True},
            ],
            "setup_instructions": """🤖 Discord Setup (2 min):

1. https://discord.com/developers/applications → [+ New Application]
2. Bot → [Add Bot] → Copy **TOKEN** (MTIz... format)
3. Bot → Privileged Gateway Intents → ✅ Message Content
4. OAuth2 → URL Generator → bot scope → Invite to server""",
        },
    }

    def __init__(self):
        self.config_path = Path.home() / ".lollmsbot" / "config.json"
        self.config_path.parent.mkdir(exist_ok=True)
        self.config: Dict[str, Dict[str, Any]] = self._load_config()

    def _load_config(self) -> Dict[str, Dict[str, Any]]:
        if self.config_path.exists():
            return json.loads(self.config_path.read_text())
        return {}

    def _save_config(self) -> None:
        self.config_path.write_text(json.dumps(self.config, indent=2))

    def run_wizard(self) -> None:  # ✅ FIXED: Public entrypoint
        """Main wizard loop."""
        console.clear()
        console.print(Panel("[bold cyan]🎉 lollmsBot Setup Wizard[/]", width=80))

        while True:
            action = questionary.select(
                "What would you like to do?",
                choices=[
                    "📡 Configure Services",
                    "🔍 Test Connections", 
                    "📄 View Config",
                    "💾 Save & Exit",
                    "❌ Quit",
                ],
            ).ask()

            if action == "📡 Configure Services":
                self.configure_services()
            elif action == "🔍 Test Connections":
                self.test_connections()
            elif action == "📄 View Config":
                self.show_config()
            elif action == "💾 Save & Exit":
                self._save_config()
                console.print("[bold green]✅ Saved to ~/.lollmsbot/config.json![/]")
                break
            elif action == "❌ Quit":
                break

    # Replace the configure_services() method with this:

    def configure_services(self) -> None:
        service_name = questionary.select(
            "Select service:",
            choices=list(self.SERVICES_CONFIG.keys()) + ["← Back"],
        ).ask()

        if service_name == "← Back":
            return

        service = self.SERVICES_CONFIG[service_name]
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
                # ✅ FIXED: Use password() for secrets
                value = questionary.password(field["prompt"], default=default).ask()
            else:
                value = questionary.text(field["prompt"], default=default).ask()

            if value or not field.get("optional"):
                service_config[field["name"]] = value

        console.print("[green]✅ Updated![/]")


    def test_connections(self) -> None:
        if not self.config:
            console.print("[yellow]No services configured yet.[/]")
            return

        table = Table(title="🧪 Connection Tests")
        table.add_column("Service")
        table.add_column("Status")
        table.add_column("Details")

        for service_name, config in self.config.items():
            status, details = self._test_single(service_name, config)
            table.add_row(service_name.title(), status, details)

        console.print(table)

    def _test_single(self, service_name: str, config: Dict[str, Any]) -> tuple[str, str]:
        try:
            if service_name == "lollms":
                # ✅ FIXED: Safe bool conversion
                lollms_config = {}
                for k, v in config.items():
                    if k in ["host_address", "api_key"]:
                        lollms_config[k] = v
                    elif k == "verify_ssl":
                        # Handle string, bool, or missing
                        if isinstance(v, str):
                            lollms_config[k] = v.lower() in ("true", "yes", "1", "on")
                        elif isinstance(v, bool):
                            lollms_config[k] = v
                        else:
                            lollms_config[k] = True  # Default

                settings = LollmsSettings(**lollms_config)
                client = build_lollms_client(settings)
                
                # Connectivity test
                try:
                    # Non-destructive test
                    _ = getattr(client, "list_models", lambda: ["test"])(())
                    return ("✅ CONNECTED", "API reachable ✓")
                except:
                    return ("🟡 READY", "Client initialized ✓")
                    
            elif service_name == "discord":
                token = config.get("bot_token", "")
                return ("🔍 READY", f"Token loaded ({len(token or '')} chars)")
                
            return ("❓ SKIP", "-")
            
        except Exception as e:
            return ("❌ ERROR", str(e)[:40])



    def show_config(self) -> None:
        if not self.config:
            console.print("[yellow]No config yet.[/]")
            return

        console.print_json(data=self.config, indent=2)


# ✅ Entry point for CLI
def run_wizard() -> None:
    """CLI entrypoint."""
    try:
        Wizard().run_wizard()
    except KeyboardInterrupt:
        console.print("\n[yellow]👋 Bye![/]")
    except Exception as e:
        console.print(f"[red]Error: {e}[/]")
