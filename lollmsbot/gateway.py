#!/usr/bin/env python
"""
lollmsBot Gateway - .env Source of Truth
"""
import asyncio
import json
import os
from typing import AsyncGenerator, Dict, List, Optional, Any
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from rich.console import Console

console = Console()
app = FastAPI(title="lollmsBot API")

# === LOAD WIZARD CONFIG FIRST, THEN FALLBACK TO .env ===
def _load_wizard_config() -> Dict[str, Any]:
    """Load config from wizard's config.json if it exists."""
    wizard_path = Path.home() / ".lollmsbot" / "config.json"
    if wizard_path.exists():
        try:
            return json.loads(wizard_path.read_text())
        except (json.JSONDecodeError, IOError):
            pass
    return {}

_WIZARD_CONFIG = _load_wizard_config()

def _get_config(service: str, key: str, env_name: str, default: Any = None) -> Any:
    """Get config value: wizard config > env var > default."""
    # Check wizard config first
    if service in _WIZARD_CONFIG and key in _WIZARD_CONFIG[service]:
        return _WIZARD_CONFIG[service][key]
    # Fall back to environment
    return os.getenv(env_name, default)

# === CONFIG CONSTANTS ===
HOST = _get_config("lollmsbot", "host", "LOLLMSBOT_HOST", "0.0.0.0")
PORT = int(_get_config("lollmsbot", "port", "LOLLMSBOT_PORT", "8800"))
# Use localhost for internal gateway URL (Discord needs to reach the gateway)
GATEWAY_URL = f"http://127.0.0.1:{PORT}"
DISCORD_TOKEN = _get_config("discord", "bot_token", "DISCORD_BOT_TOKEN", None)
TELEGRAM_TOKEN = _get_config("telegram", "bot_token", "TELEGRAM_BOT_TOKEN", None)

# Track active channels for status reporting
_active_channels: Dict[str, Any] = {}
_channel_tasks: List[asyncio.Task] = []

# === MODELS ===
class Health(BaseModel):
    status: str = "ok"
    url: str = f"http://{HOST}:{PORT}"
    discord: str = "active" if DISCORD_TOKEN else "disabled"
    telegram: str = "active" if TELEGRAM_TOKEN else "disabled"

class ChannelInfo(BaseModel):
    name: str
    type: str
    status: str
    details: Dict[str, Any] = {}

class ChannelsResponse(BaseModel):
    channels: List[ChannelInfo]
    count: int

class ChatReq(BaseModel):
    message: str

class ChatResp(BaseModel):
    reply: str

# === ROUTES ===
@app.get("/")
async def root():
    return {
        "api": f"http://{HOST}:{PORT}",
        "docs": "/docs",
        "health": "/health",
        "channels": "/channels",
    }

@app.get("/health", response_model=Health)
async def health():
    from .config import LollmsSettings
    settings = LollmsSettings.from_env()
    
    lollms_ok = True
    try:
        from .lollms_client import build_lollms_client
        client = build_lollms_client(settings)
        getattr(client, "list_models", lambda: None)()
    except:
        lollms_ok = False
    
    # Check Discord status
    discord_status = "disabled"
    if DISCORD_TOKEN:
        discord_ch = _active_channels.get("discord")
        if discord_ch and getattr(discord_ch, "is_running", False):
            discord_status = "connected" if discord_ch.is_running else "connecting"
        else:
            discord_status = "error"
    
    # Check Telegram status
    telegram_status = "disabled"
    if TELEGRAM_TOKEN:
        telegram_ch = _active_channels.get("telegram")
        if telegram_ch and getattr(telegram_ch, "_is_running", False):
            telegram_status = "active"
        else:
            telegram_status = "error"
    
    return {
        "status": "ok",
        "url": f"http://{HOST}:{PORT}",
        "discord": discord_status,
        "telegram": telegram_status,
        "lollms": lollms_ok,
    }

@app.get("/channels", response_model=ChannelsResponse)
async def list_channels():
    """List all active channels and their status."""
    channels = []
    
    for name, channel in _active_channels.items():
        info = ChannelInfo(
            name=name,
            type=channel.__class__.__name__,
            status="running" if getattr(channel, "_is_running", False) else "stopped",
            details={
                "repr": repr(channel),
            }
        )
        
        # Add channel-specific details
        if hasattr(channel, "bot") and hasattr(channel.bot, "user"):
            if channel.bot.user:
                info.details["bot_name"] = str(channel.bot.user)
                info.details["bot_id"] = channel.bot.user.id
                info.details["guilds"] = len(channel.bot.guilds)
        
        channels.append(info)
    
    return ChannelsResponse(channels=channels, count=len(channels))

@app.post("/chat", response_model=ChatResp)
async def chat(req: ChatReq):
    from .config import LollmsSettings
    from .lollms_client import build_lollms_client
    
    settings = LollmsSettings.from_env()
    lc = build_lollms_client(settings)
    reply = lc.generate_text(req.message)
    
    return ChatResp(reply=str(reply))

# === LIFESPAN ===
@asynccontextmanager
async def lifespan(app_: FastAPI) -> AsyncGenerator[None, None]:
    # Show which config sources are being used
    wizard_loaded = bool(_WIZARD_CONFIG)
    if wizard_loaded:
        console.print(f"[dim]📄 Loaded wizard config from ~/.lollmsbot/config.json[/]")
    
    console.print(f"[green]🚀 Gateway starting on http://{HOST}:{PORT}[/]")
    
    # Track active channels
    global _active_channels, _channel_tasks
    
    # Discord (from wizard or .env)
    if DISCORD_TOKEN:
        try:
            from .channels.discord import DiscordChannel
            console.print("[cyan]🤖 Initializing Discord channel...[/]")
            
            channel = DiscordChannel(
                bot_token=DISCORD_TOKEN,
                gateway_url=GATEWAY_URL,  # Use localhost URL for internal access
            )
            _active_channels["discord"] = channel
            
            # Start in background task
            task = asyncio.create_task(channel.start())
            _channel_tasks.append(task)
            
            # Wait a bit for connection (non-blocking for other channels)
            async def wait_discord():
                ready = await channel.wait_for_ready(timeout=10.0)
                if ready:
                    console.print("[green]✅ Discord connected and ready[/]")
                else:
                    console.print("[yellow]⚠️  Discord still connecting (may need more time)[/]")
            
            asyncio.create_task(wait_discord())
            
        except Exception as e:
            console.print(f"[red]❌ Discord failed: {e}[/]")
            import traceback
            traceback.print_exc()
    else:
        console.print("[dim]ℹ️  Discord disabled (set DISCORD_BOT_TOKEN in wizard or .env)[/]")
    
    # Telegram (from wizard or .env)
    if TELEGRAM_TOKEN:
        try:
            from .channels.telegram import TelegramChannel
            console.print("[cyan]📱 Initializing Telegram channel...[/]")
            
            channel = TelegramChannel(bot_token=TELEGRAM_TOKEN)
            _active_channels["telegram"] = channel
            
            task = asyncio.create_task(channel.start())
            _channel_tasks.append(task)
            console.print("[green]✅ Telegram started[/]")
            
        except Exception as e:
            console.print(f"[red]❌ Telegram failed: {e}[/]")
            import traceback
            traceback.print_exc()
    else:
        console.print("[dim]ℹ️  Telegram disabled (set TELEGRAM_BOT_TOKEN in wizard or .env)[/]")
    
    # HTTP API channel (always enabled for gateway communication)
    try:
        from .channels.http_api import HttpApiChannel
        console.print("[cyan]🌐 HTTP API channel available at /webhook[/]")
    except ImportError:
        pass  # Optional dependency
    
    # Summary
    active_count = len([c for c in _active_channels.values() if getattr(c, "_is_running", False)])
    console.print(f"[bold green]📊 Active channels: {len(_active_channels)} initialized ({active_count} running)[/]")
    
    yield
    
    # Cleanup
    console.print("[yellow]🛑 Shutting down channels...[/]")
    
    for name, channel in _active_channels.items():
        try:
            await channel.stop()
            console.print(f"[dim]  • {name} stopped[/]")
        except Exception as e:
            console.print(f"[red]  • {name} error: {e}[/]")
    
    _active_channels.clear()
    
    # Cancel any pending tasks
    for task in _channel_tasks:
        if not task.done():
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
    
    _channel_tasks.clear()
    console.print("[green]👋 Gateway shutdown complete[/]")

app.router.lifespan_context = lifespan

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("lollmsbot.gateway:app", host=HOST, port=PORT)
