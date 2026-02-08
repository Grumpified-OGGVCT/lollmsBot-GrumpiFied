#!/usr/bin/env python
from __future__ import annotations
import os
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from dotenv import load_dotenv
import json

load_dotenv()

console = None  # Forward ref

def _get_bool(name: str, default: bool = False) -> bool:
    val = os.getenv(name)
    if val is None:
        return default
    return val.lower() in ("1", "true", "yes", "on")

def _get_float(name: str, default: float, min_val: float = None, max_val: float = None) -> float:
    """Get float from environment with validation."""
    try:
        val = float(os.getenv(name, str(default)))
        if min_val is not None and val < min_val:
            return default
        if max_val is not None and val > max_val:
            return default
        return val
    except (ValueError, TypeError):
        return default

@dataclass
class BotConfig:
    """Bot behavior configuration settings."""
    name: str = field(default="LollmsBot")
    max_history: int = field(default=10)
    
    @classmethod
    def from_env(cls) -> "BotConfig":
        """Load from environment variables."""
        return cls(
            name=os.getenv("LOLLMSBOT_NAME", "LollmsBot"),
            max_history=int(os.getenv("LOLLMSBOT_MAX_HISTORY", "10")),
        )


@dataclass
class RC2Config:
    """RC2 sub-agent configuration settings."""
    enabled: bool = field(default=False)  # Default disabled for safety
    rate_limit_per_minute: int = field(default=5)  # Max RC2 calls per user per minute
    use_multi_provider: bool = field(default=True)  # Use multi-provider by default
    enable_constitutional: bool = field(default=True)  # Constitutional review
    enable_introspection: bool = field(default=True)  # Deep introspection
    enable_self_mod: bool = field(default=False)  # Self-modification (proposals only)
    enable_meta_learning: bool = field(default=False)  # Meta-learning
    enable_healing: bool = field(default=False)  # Error healing
    enable_visual: bool = field(default=False)  # Visual monitoring
    
    @classmethod
    def from_env(cls) -> "RC2Config":
        """Load from environment variables."""
        return cls(
            enabled=_get_bool("RC2_ENABLED", False),
            rate_limit_per_minute=int(os.getenv("RC2_RATE_LIMIT", "5")),
            use_multi_provider=_get_bool("RC2_USE_MULTI_PROVIDER", True),
            enable_constitutional=_get_bool("RC2_CONSTITUTIONAL", True),
            enable_introspection=_get_bool("RC2_INTROSPECTION", True),
            enable_self_mod=_get_bool("RC2_SELF_MODIFICATION", False),
            enable_meta_learning=_get_bool("RC2_META_LEARNING", False),
            enable_healing=_get_bool("RC2_HEALING", False),
            enable_visual=_get_bool("RC2_VISUAL", False),
        )
    
    def validate(self) -> None:
        """Validate configuration values.
        
        Raises:
            ValueError: If configuration is invalid
        """
        if self.rate_limit_per_minute < 1:
            raise ValueError("RC2 rate_limit_per_minute must be at least 1")
        if self.rate_limit_per_minute > 100:
            raise ValueError("RC2 rate_limit_per_minute should not exceed 100")


@dataclass
class MultiProviderConfig:
    """Multi-provider API system configuration."""
    enabled: bool = field(default=True)  # Enable multi-provider by default
    prefer_free_tier: bool = field(default=True)  # Try OpenRouter free first
    openrouter_enabled: bool = field(default=True)
    ollama_enabled: bool = field(default=True)
    
    @classmethod
    def from_env(cls) -> "MultiProviderConfig":
        """Load from environment variables."""
        return cls(
            enabled=_get_bool("USE_MULTI_PROVIDER", True),
            prefer_free_tier=_get_bool("PREFER_FREE_TIER", True),
            openrouter_enabled=_get_bool("OPENROUTER_ENABLED", True),
            ollama_enabled=_get_bool("OLLAMA_ENABLED", True),
        )


@dataclass
class AutonomousHobbyConfig:
    """Autonomous hobby and continuous learning configuration."""
    enabled: bool = field(default=True)  # Enable autonomous learning by default
    interval_minutes: float = field(default=15.0)  # Check for hobby time every 15 minutes
    idle_threshold_minutes: float = field(default=5.0)  # Start hobby after 5 minutes idle
    max_hobby_duration_minutes: float = field(default=10.0)  # Max time per hobby session
    focus_on_weaknesses: bool = field(default=True)  # Prioritize improving weak areas
    variety_factor: float = field(default=0.3)  # How much to mix different hobbies
    intensity_level: float = field(default=0.5)  # Learning intensity (0-1)
    
    @classmethod
    def from_env(cls) -> "AutonomousHobbyConfig":
        """Load from environment variables with validation."""
        return cls(
            enabled=_get_bool("AUTONOMOUS_HOBBY_ENABLED", True),
            interval_minutes=_get_float("HOBBY_INTERVAL_MINUTES", 15.0, min_val=1.0, max_val=1440.0),
            idle_threshold_minutes=_get_float("HOBBY_IDLE_THRESHOLD_MINUTES", 5.0, min_val=0.1, max_val=120.0),
            max_hobby_duration_minutes=_get_float("HOBBY_MAX_DURATION_MINUTES", 10.0, min_val=1.0, max_val=60.0),
            focus_on_weaknesses=_get_bool("HOBBY_FOCUS_WEAKNESSES", True),
            variety_factor=_get_float("HOBBY_VARIETY_FACTOR", 0.3, min_val=0.0, max_val=1.0),
            intensity_level=_get_float("HOBBY_INTENSITY_LEVEL", 0.5, min_val=0.0, max_val=1.0),
        )

@dataclass
class LollmsSettings:
    """LoLLMS connection settings."""
    host_address: str = field(default="http://localhost:9600")
    api_key: Optional[str] = field(default=None)
    verify_ssl: bool = field(default=True)
    binding_name: Optional[str] = field(default=None)
    model_name: Optional[str] = field(default=None)
    context_size: Optional[int] = field(default=None)

    @classmethod
    def from_env(cls) -> "LollmsSettings":
        """Load from environment variables."""
        global console
        return cls(
            host_address=os.getenv("LOLLMS_HOST_ADDRESS", "http://localhost:9600"),
            api_key=os.getenv("LOLLMS_API_KEY"),
            verify_ssl=_get_bool("LOLLMS_VERIFY_SSL", True),
            binding_name=os.getenv("LOLLMS_BINDING_NAME"),
            model_name=os.getenv("LOLLMS_MODEL_NAME"),
            context_size=int(os.getenv("LOLLMS_CONTEXT_SIZE", "32000")) or None,
        )

    @classmethod
    def from_wizard(cls) -> "LollmsSettings":
        """Load from wizard config."""
        wizard_path = Path.home() / ".lollmsbot" / "config.json"
        if not wizard_path.exists():
            return cls.from_env()
        
        try:
            wizard_data = json.loads(wizard_path.read_text())
            lollms_data = wizard_data.get("lollms", {})
            if lollms_data.get("host_address"):
                console.print("[green]📡 Using wizard config![/]" if console else "Using wizard config")
                return cls(
                    host_address=lollms_data.get("host_address", "http://localhost:9600"),
                    api_key=lollms_data.get("api_key"),
                    verify_ssl=_get_bool(str(lollms_data.get("verify_ssl", True))),
                    binding_name=lollms_data.get("binding_name"),
                )
        except (FileNotFoundError, json.JSONDecodeError, KeyError) as e:
            # Wizard config not found or invalid, fall back to environment variables
            logger.debug(f"Could not load wizard config: {e}")
            pass
        return cls.from_env()

@dataclass
class GatewaySettings:
    """Gateway server settings."""
    host: str = field(default="localhost")
    port: int = field(default=8800)
    cors_origins: List[str] = field(default_factory=lambda: ["http://localhost", "http://127.0.0.1"])

    @classmethod
    def from_env(cls) -> "GatewaySettings":
        # Parse CORS origins from environment variable (comma-separated)
        cors_env = os.getenv("LOLLMSBOT_CORS_ORIGINS", "")
        cors_origins = [origin.strip() for origin in cors_env.split(",") if origin.strip()] if cors_env else ["http://localhost", "http://127.0.0.1"]
        
        return cls(
            host=os.getenv("LOLLMSBOT_HOST", "localhost"),
            port=int(os.getenv("LOLLMSBOT_PORT", "8800")),
            cors_origins=cors_origins,
        )


@dataclass
class AwesomeSkillsConfig:
    """Awesome Claude Skills integration configuration."""
    enabled: bool = field(default=True)  # Enable awesome-claude-skills integration
    auto_update: bool = field(default=True)  # Auto-update repository on startup
    repo_url: str = field(default="https://github.com/Grumpified-OGGVCT/awesome-claude-skills.git")
    skills_dir: Optional[Path] = field(default=None)  # Directory for skills (default: ~/.lollmsbot/awesome-skills)
    enabled_skills: List[str] = field(default_factory=list)  # List of enabled skill names
    auto_load: bool = field(default=True)  # Auto-load enabled skills on startup
    
    @classmethod
    def from_env(cls) -> "AwesomeSkillsConfig":
        """Load from environment variables."""
        # Parse enabled skills from comma-separated list
        enabled_skills_env = os.getenv("AWESOME_SKILLS_ENABLED", "")
        enabled_skills = [s.strip() for s in enabled_skills_env.split(",") if s.strip()]
        
        # Parse skills directory
        skills_dir_env = os.getenv("AWESOME_SKILLS_DIR")
        skills_dir = Path(skills_dir_env) if skills_dir_env else None
        
        return cls(
            enabled=_get_bool("AWESOME_SKILLS_ENABLED_FLAG", True),
            auto_update=_get_bool("AWESOME_SKILLS_AUTO_UPDATE", True),
            repo_url=os.getenv("AWESOME_SKILLS_REPO_URL", "https://github.com/Grumpified-OGGVCT/awesome-claude-skills.git"),
            skills_dir=skills_dir,
            enabled_skills=enabled_skills,
            auto_load=_get_bool("AWESOME_SKILLS_AUTO_LOAD", True),
        )
