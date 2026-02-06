#!/usr/bin/env python
"""
lollmsBot CLI - Gateway + Wizard + UI
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import List

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich.text import Text
    from rich import box
    console = Console()
except ImportError:
    print("Install dev deps: pip install -e .[dev]")
    sys.exit(1)


def print_ui_banner() -> None:
    """Print beautiful UI launch banner."""
    console.print()
    
    # Create ASCII art style banner
    banner = Text()
    banner.append("╭─────────╮\n", style="blue")
    banner.append("│  🤖     │  ", style="blue")
    banner.append("LollmsBot", style="bold cyan")
    banner.append(" Web UI\n", style="bold blue")
    banner.append("╰─────────╯\n", style="blue")
    
    panel = Panel(
        banner,
        box=box.DOUBLE_EDGE,
        border_style="bright_cyan",
        title="[bold]Starting Interface[/bold]",
        subtitle="[dim]Real-time AI Chat[/dim]"
    )
    console.print(panel)


def print_gateway_banner(host: str, port: int, ui_enabled: bool) -> None:
    """Print gateway startup banner with status."""
    
    # For display purposes, use localhost if host is 0.0.0.0 or empty
    # Browsers can't connect to 0.0.0.0, they need localhost/127.0.0.1
    display_host = "localhost" if host in ("0.0.0.0", "") else host
    
    # Status indicators
    status_table = Table(
        show_header=False,
        box=box.SIMPLE,
        border_style="blue",
        padding=(0, 2)
    )
    status_table.add_column("Service", style="cyan")
    status_table.add_column("Status", style="green")
    status_table.add_column("URL", style="dim")
    
    status_table.add_row(
        "🔌 Gateway API",
        "✅ Active",
        f"http://{display_host}:{port}"
    )
    status_table.add_row(
        "📚 API Docs",
        "✅ Available",
        f"http://{display_host}:{port}/docs"
    )
    
    if ui_enabled:
        status_table.add_row(
            "🌐 Web UI",
            "✅ Mounted",
            f"http://{display_host}:{port}/ui"
        )
    else:
        status_table.add_row(
            "🌐 Web UI",
            "⭕ Disabled",
            "Use --ui to enable"
        )
    
    panel = Panel(
        status_table,
        box=box.ROUNDED,
        border_style="bright_green" if ui_enabled else "yellow",
        title="[bold bright_green]🚀 Gateway Starting[/bold bright_green]",
        subtitle=f"[dim]LoLLMS Agentic Bot | Host: {host}[/dim]"
    )
    console.print()
    console.print(panel)
    console.print()


def print_skills_info() -> None:
    """Print awesome-claude-skills repository info."""
    try:
        from lollmsbot.skills import get_awesome_skills_integration
        
        console.print("\n[bold cyan]📚 Awesome Claude Skills Integration[/bold cyan]\n")
        
        integration = get_awesome_skills_integration()
        if not integration:
            console.print("[yellow]⚠️ Awesome-claude-skills integration not available[/yellow]")
            console.print("[dim]Enable in .env: AWESOME_SKILLS_ENABLED_FLAG=true[/dim]")
            return
        
        info = integration.get_repository_info()
        
        if not info.get("available"):
            console.print(f"[red]❌ {info.get('reason', 'Not available')}[/red]")
            return
        
        # Create info table
        info_table = Table(box=box.ROUNDED, border_style="cyan")
        info_table.add_column("Property", style="cyan")
        info_table.add_column("Value", style="green")
        
        info_table.add_row("Repository", info.get("url", "N/A"))
        info_table.add_row("Local Path", info.get("path", "N/A"))
        info_table.add_row("Cloned", "✅ Yes" if info.get("cloned") else "❌ No")
        info_table.add_row("Last Updated", info.get("last_updated", "N/A"))
        info_table.add_row("Total Skills", str(info.get("skills_count", 0)))
        info_table.add_row("Loaded Skills", str(info.get("loaded_skills_count", 0)))
        
        console.print(info_table)
        
        if info.get("loaded_skills"):
            console.print("\n[bold]Loaded Skills:[/bold]")
            for skill in info["loaded_skills"]:
                console.print(f"  • {skill}", style="dim")
        
        console.print()
        
    except Exception as e:
        console.print(f"[red]❌ Error: {e}[/red]")
        console.print_exception(show_locals=True)


def handle_skills_command(args) -> None:
    """Handle skills subcommands."""
    try:
        from lollmsbot.skills import get_awesome_skills_integration
        from rich.table import Table
        
        integration = get_awesome_skills_integration()
        if not integration or not integration.is_available():
            console.print("[red]❌ Awesome-claude-skills not available[/red]")
            console.print("[dim]Run: lollmsbot wizard to configure[/dim]")
            return
        
        if args.skills_command == "list":
            # List skills
            console.print("\n[bold cyan]📚 Available Skills[/bold cyan]\n")
            
            if args.loaded:
                skills = [integration.manager.get_skill(name) for name in integration.loaded_skills.keys()]
                skills = [s for s in skills if s]  # Filter None
                console.print(f"[dim]Showing {len(skills)} loaded skills[/dim]\n")
            else:
                skills = integration.list_available_skills(category=args.category)
                if args.category:
                    console.print(f"[dim]Category: {args.category}[/dim]\n")
            
            if not skills:
                console.print("[yellow]No skills found[/yellow]")
                return
            
            # Create table
            table = Table(box=box.ROUNDED, border_style="cyan")
            table.add_column("Name", style="cyan")
            table.add_column("Category", style="yellow")
            table.add_column("Tier", style="magenta")
            table.add_column("Description", style="dim", max_width=50)
            table.add_column("Status", style="green")
            
            for skill in skills[:20]:  # Limit to 20 for display
                status = "✅ Loaded" if skill.name in integration.loaded_skills else "⭕ Available"
                table.add_row(
                    skill.name,
                    skill.category,
                    skill.tier,
                    skill.description[:47] + "..." if len(skill.description) > 50 else skill.description,
                    status
                )
            
            console.print(table)
            
            if len(skills) > 20:
                console.print(f"\n[dim]... and {len(skills) - 20} more skills[/dim]")
            
            console.print()
        
        elif args.skills_command == "search":
            # Search skills
            console.print(f"\n[bold cyan]🔍 Searching for: {args.query}[/bold cyan]\n")
            
            results = integration.search_skills(args.query)
            
            if not results:
                console.print("[yellow]No skills found[/yellow]")
                return
            
            console.print(f"[green]Found {len(results)} skill(s):[/green]\n")
            
            for skill in results[:10]:  # Limit to 10
                console.print(f"[bold cyan]• {skill.name}[/bold cyan]")
                console.print(f"  Category: {skill.category} | Tier: {skill.tier}")
                console.print(f"  {skill.description}\n")
            
            if len(results) > 10:
                console.print(f"[dim]... and {len(results) - 10} more results[/dim]")
            
            console.print()
        
        elif args.skills_command == "install":
            # Install skill
            console.print(f"\n[bold cyan]📥 Installing skill: {args.skill_name}[/bold cyan]\n")
            
            success = integration.load_skill(args.skill_name)
            
            if success:
                console.print(f"[green]✅ Skill '{args.skill_name}' installed successfully![/green]")
            else:
                console.print(f"[red]❌ Failed to install skill '{args.skill_name}'[/red]")
                console.print("[dim]Check logs for details[/dim]")
            
            console.print()
        
        elif args.skills_command == "uninstall":
            # Uninstall skill
            console.print(f"\n[bold cyan]📤 Uninstalling skill: {args.skill_name}[/bold cyan]\n")
            
            success = integration.unload_skill(args.skill_name)
            
            if success:
                console.print(f"[green]✅ Skill '{args.skill_name}' uninstalled successfully![/green]")
            else:
                console.print(f"[red]❌ Failed to uninstall skill '{args.skill_name}'[/red]")
                console.print("[dim]Skill may not be loaded[/dim]")
            
            console.print()
        
        elif args.skills_command == "update":
            # Update repository
            console.print("\n[bold cyan]🔄 Updating skills repository...[/bold cyan]\n")
            
            success = integration.update_repository()
            
            if success:
                console.print("[green]✅ Repository updated successfully![/green]")
                console.print("\n[dim]Reloading skills...[/dim]")
                reloaded = integration.reload_all_skills()
                console.print(f"[green]✅ Reloaded {reloaded} skill(s)[/green]")
            else:
                console.print("[red]❌ Failed to update repository[/red]")
            
            console.print()
        
        elif args.skills_command == "info":
            # Show repository info
            print_skills_info()
        
        else:
            console.print("[yellow]Please specify a skills command: list, search, install, uninstall, update, or info[/yellow]")
    
    except Exception as e:
        console.print(f"[red]❌ Error: {e}[/red]")
        console.print_exception(show_locals=True)


def print_status() -> None:
    """Print comprehensive system status."""
    from pathlib import Path
    import json
    
    console.print()
    console.print(Panel(
        "[bold cyan]LollmsBot System Status[/bold cyan]",
        border_style="bright_cyan"
    ))
    console.print()
    
    # Check configuration
    config_table = Table(title="📋 Configuration", box=box.ROUNDED)
    config_table.add_column("Setting", style="cyan")
    config_table.add_column("Value", style="green")
    config_table.add_column("Status", style="yellow")
    
    config_dir = Path.home() / ".lollmsbot"
    config_file = config_dir / "config.json"
    
    if config_file.exists():
        try:
            with open(config_file) as f:
                config = json.load(f)
            
            # LLM Backend
            lollms_config = config.get("lollms", {})
            backend = lollms_config.get("binding_name", "Not configured")
            model = lollms_config.get("model_name", "Default")
            host = lollms_config.get("host_address", "Not set")
            
            config_table.add_row("Backend", backend, "✅" if backend != "Not configured" else "⚠️")
            config_table.add_row("Model", model, "✅" if model else "⚠️")
            config_table.add_row("Host", host[:50] if host else "Not set", "✅" if host else "⚠️")
            
            # Check for API key
            has_api_key = bool(lollms_config.get("api_key"))
            config_table.add_row("API Key", "Set" if has_api_key else "Not set", "✅" if has_api_key else "⭕")
            
        except Exception as e:
            config_table.add_row("Error", str(e), "❌")
    else:
        config_table.add_row("Configuration", "Not found", "⚠️")
        config_table.add_row("Action", "Run 'lollmsbot wizard'", "💡")
    
    console.print(config_table)
    console.print()
    
    # Check components
    components_table = Table(title="🔧 Components", box=box.ROUNDED)
    components_table.add_column("Component", style="cyan")
    components_table.add_column("Status", style="green")
    components_table.add_column("Details", style="dim")
    
    # Check if agent can be imported
    try:
        from lollmsbot.agent import Agent
        components_table.add_row("Agent", "✅ Available", "Core AI agent module loaded")
    except Exception as e:
        components_table.add_row("Agent", "❌ Error", str(e)[:50])
    
    # Check Guardian
    try:
        from lollmsbot.guardian import Guardian
        components_table.add_row("Guardian", "✅ Available", "Security & ethics layer loaded")
    except Exception as e:
        components_table.add_row("Guardian", "❌ Error", str(e)[:50])
    
    # Check Skills
    try:
        from lollmsbot.skills import get_skill_registry
        registry = get_skill_registry()
        skill_count = len(registry._skills) if hasattr(registry, '_skills') else 0
        components_table.add_row("Skills", "✅ Available", f"{skill_count} skills loaded")
    except Exception as e:
        components_table.add_row("Skills", "❌ Error", str(e)[:50])
    
    # Check Heartbeat
    try:
        from lollmsbot.heartbeat import get_heartbeat
        components_table.add_row("Heartbeat", "✅ Available", "Self-maintenance system ready")
    except Exception as e:
        components_table.add_row("Heartbeat", "❌ Error", str(e)[:50])
    
    # Check Lane Queue
    try:
        from lollmsbot.core.engine import get_engine
        components_table.add_row("Lane Queue", "✅ Available", "Priority-based task execution")
    except Exception as e:
        components_table.add_row("Lane Queue", "⚠️ Optional", "Not available (optional feature)")
    
    # Check RAG Store
    try:
        from lollmsbot.memory.rag_store import get_rag_store
        components_table.add_row("RAG Store", "✅ Available", "Knowledge base ready")
    except Exception as e:
        components_table.add_row("RAG Store", "⚠️ Optional", "Not available (optional feature)")
    
    # Check Multi-Provider
    try:
        from lollmsbot.providers import MultiProviderRouter
        use_multi = os.getenv("USE_MULTI_PROVIDER", "true").lower() == "true"
        if use_multi:
            # Count available keys
            openrouter_keys = sum(1 for i in [1,2,3] if os.getenv(f"OPENROUTER_API_KEY_{i}"))
            ollama_keys = sum(1 for i in ["", "_2"] if os.getenv(f"OLLAMA_API_KEY{i}"))
            components_table.add_row(
                "Multi-Provider", 
                "✅ Enabled", 
                f"OpenRouter: {openrouter_keys} keys, Ollama: {ollama_keys} keys"
            )
        else:
            components_table.add_row("Multi-Provider", "⚪ Disabled", "Set USE_MULTI_PROVIDER=true to enable")
    except Exception as e:
        components_table.add_row("Multi-Provider", "❌ Error", str(e)[:50])
    
    # Check RC2 Sub-Agent
    try:
        from lollmsbot.subagents import RC2SubAgent
        rc2_enabled = os.getenv("RC2_ENABLED", "false").lower() == "true"
        if rc2_enabled:
            components_table.add_row("RC2 Sub-Agent", "✅ Enabled", "Constitutional review & introspection")
        else:
            components_table.add_row("RC2 Sub-Agent", "⚪ Disabled", "Set RC2_ENABLED=true to enable")
    except Exception as e:
        components_table.add_row("RC2 Sub-Agent", "❌ Error", str(e)[:50])
    
    console.print(components_table)
    console.print()
    
    # Quick start guide
    guide_table = Table(title="🚀 Quick Start", box=box.ROUNDED, show_header=False)
    guide_table.add_column("Command", style="cyan")
    guide_table.add_column("Description", style="dim")
    
    if not config_file.exists():
        guide_table.add_row("lollmsbot wizard", "Run interactive setup wizard")
        guide_table.add_row("", "[yellow]⚠️ Configuration needed before starting gateway[/yellow]")
    else:
        guide_table.add_row("lollmsbot gateway", "Start API gateway server")
        guide_table.add_row("lollmsbot gateway --ui", "Start gateway with web UI")
        guide_table.add_row("lollmsbot wizard", "Reconfigure settings")
    
    console.print(guide_table)
    console.print()


def main(argv: List[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        prog="lollmsbot",
        description="Agentic LoLLMS Assistant (Clawdbot-style)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
┌─────────────────────────────────────────────────────────────┐
│  Examples:                                                  │
│    lollmsbot wizard          # Interactive setup            │
│    lollmsbot gateway         # Run API server               │
│    lollmsbot gateway --ui    # API + Web UI together        │
│    lollmsbot ui              # Web UI only (standalone)     │
│    lollmsbot ui --port 3000  # UI on custom port            │
└─────────────────────────────────────────────────────────────┘
        """
    )
    parser.add_argument("--version", action="version", version="lollmsBot 0.1.0")

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Gateway command
    gateway_parser = subparsers.add_parser(
        "gateway", 
        help="Run API gateway server",
        description="Start the main API gateway with optional channels and UI"
    )
    gateway_parser.add_argument("--host", type=str, default="0.0.0.0", help="Bind address (default: 0.0.0.0)")
    gateway_parser.add_argument("--port", type=int, default=8800, help="Port number (default: 8800)")
    gateway_parser.add_argument("--ui", action="store_true", help="Also start web UI at /ui")

    # UI command (standalone)
    ui_parser = subparsers.add_parser(
        "ui", 
        help="Run web UI only (standalone mode)",
        description="Start just the web interface without the full gateway"
    )
    ui_parser.add_argument("--host", type=str, default="127.0.0.1", help="Bind address (default: 127.0.0.1)")
    ui_parser.add_argument("--port", type=int, default=8080, help="Port number (default: 8080)")
    ui_parser.add_argument("--quiet", "-q", action="store_true", help="Minimal console output")

    # Wizard command
    wizard_parser = subparsers.add_parser(
        "wizard", 
        help="Interactive setup wizard",
        description="Configure LoLLMS connection and bot settings interactively"
    )
    
    # Status command
    status_parser = subparsers.add_parser(
        "status",
        help="Show LollmsBot system status",
        description="Display operational status, loaded components, and metrics"
    )
    
    # Skills command
    skills_parser = subparsers.add_parser(
        "skills",
        help="Manage awesome-claude-skills",
        description="Search, install, and manage awesome-claude-skills integration"
    )
    skills_subparsers = skills_parser.add_subparsers(dest="skills_command", help="Skills operations")
    
    # skills list
    list_parser = skills_subparsers.add_parser("list", help="List available skills")
    list_parser.add_argument("--category", type=str, help="Filter by category")
    list_parser.add_argument("--loaded", action="store_true", help="Show only loaded skills")
    
    # skills search
    search_parser = skills_subparsers.add_parser("search", help="Search for skills")
    search_parser.add_argument("query", type=str, help="Search query")
    
    # skills install
    install_parser = skills_subparsers.add_parser("install", help="Install/enable a skill")
    install_parser.add_argument("skill_name", type=str, help="Name of skill to install")
    
    # skills uninstall
    uninstall_parser = skills_subparsers.add_parser("uninstall", help="Uninstall/disable a skill")
    uninstall_parser.add_argument("skill_name", type=str, help="Name of skill to uninstall")
    
    # skills update
    update_parser = skills_subparsers.add_parser("update", help="Update skills repository")
    
    # skills info
    info_parser = skills_subparsers.add_parser("info", help="Show skills repository info")

    args = parser.parse_args(argv)

    try:
        if args.command == "gateway":
            import uvicorn
            from lollmsbot.config import GatewaySettings
            from lollmsbot import gateway
            
            settings = GatewaySettings.from_env()
            host = args.host or settings.host
            port = args.port or settings.port
            
            # Print startup banner
            print_gateway_banner(host, port, args.ui)
            
            # Enable UI if requested
            if args.ui:
                # Use localhost for UI server internally, gateway will mount it
                gateway.enable_ui(host="127.0.0.1", port=8080)
            
            # Run server
            uvicorn.run(
                "lollmsbot.gateway:app",
                host=host,
                port=port,
                reload=args.host == "127.0.0.1" and not args.ui,
                log_level="info",
            )
            
        elif args.command == "ui":
            # Run standalone UI with full rich output
            from lollmsbot.ui.app import WebUI
            import uvicorn
            
            print_ui_banner()
            
            ui = WebUI(verbose=not args.quiet)
            ui.print_server_ready(args.host, args.port)
            
            try:
                uvicorn.run(
                    ui.app,
                    host=args.host,
                    port=args.port,
                    log_level="warning" if args.quiet else "info",
                )
            except KeyboardInterrupt:
                ui._print_shutdown_message()
            
        elif args.command == "wizard":
            from lollmsbot import wizard
            wizard.run_wizard()
        
        elif args.command == "status":
            print_status()
        
        elif args.command == "skills":
            handle_skills_command(args)
            
        else:
            parser.print_help()
            console.print("\n[bold cyan]💡 Need help? Try: lollmsbot wizard[/]")
            
    except KeyboardInterrupt:
        console.print("\n[yellow]👋 Goodbye![/]")
        sys.exit(130)
    except ImportError as e:
        console.print(f"[red]❌ Missing dependency: {e}[/]")
        console.print("[cyan]💡 Run: pip install -e .[dev][/]")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]💥 Error: {e}[/]")
        console.print_exception(show_locals=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
