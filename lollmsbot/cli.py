#!/usr/bin/env python
"""
lollmsBot CLI - Gateway + Wizard
"""
from __future__ import annotations

import argparse
import sys
from typing import List

try:
    from rich.console import Console
    console = Console()
except ImportError:
    print("Install dev deps: pip install -e .[dev]")
    sys.exit(1)


def main(argv: List[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        prog="lollmsbot",
        description="Agentic LoLLMS Assistant (Clawdbot-style)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  lollmsbot wizard          # Interactive setup
  lollmsbot gateway         # Run server
  lollmsbot gateway --port 8080
        """
    )
    parser.add_argument("--version", action="version", version="lollmsBot 0.1.0")

    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # Gateway command
    gateway_parser = subparsers.add_parser("gateway", help="Run gateway server")
    gateway_parser.add_argument("--host", type=str, default="0.0.0.0")
    gateway_parser.add_argument("--port", type=int, default=8800)

    # Wizard command ✅ FIXED
    wizard_parser = subparsers.add_parser("wizard", help="Interactive setup wizard")
    # wizard_parser.add_argument("--reset", action="store_true", help="Reset config")

    args = parser.parse_args(argv)

    try:
        if args.command == "gateway":
            import uvicorn
            from lollmsbot.config import GatewaySettings
            from lollmsbot import gateway  # Import triggers app
            
            settings = GatewaySettings.from_env()
            host = args.host or settings.host
            port = args.port or settings.port
            
            console.print(f"[green]🚀 Starting gateway on {host}:{port}[/]")
            uvicorn.run(
                "lollmsbot.gateway:app",
                host=host,
                port=port,
                reload=args.host == "127.0.0.1",  # Reload only localhost
                log_level="info",
            )
            
        elif args.command == "wizard":
            from lollmsbot import wizard
            wizard.run_wizard()
            
        else:
            parser.print_help()
            console.print("\n[bold cyan]💡 Try: lollmsbot wizard[/]")
            
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
