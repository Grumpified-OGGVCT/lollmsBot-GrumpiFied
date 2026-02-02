"""
Configuration management for LollmsBot using Pydantic BaseSettings.

This module provides type-safe configuration classes with environment variable
support for all LollmsBot components.
"""

from pathlib import Path
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class LollmsConfig(BaseSettings):
    """Configuration for LoLLMs server connection."""
    
    model_config = SettingsConfigDict(
        env_prefix="LOLLMSBOT_LLM_",
        frozen=True,
        extra="ignore",
    )
    
    host: str = Field(
        default="localhost",
        description="LoLLMs server hostname",
    )
    port: int = Field(
        default=9600,
        ge=1,
        le=65535,
        description="LoLLMs server port",
    )
    api_key: Optional[str] = Field(
        default=None,
        description="API key for LoLLMs authentication",
    )
    timeout: float = Field(
        default=30.0,
        gt=0.0,
        description="Request timeout in seconds",
    )
    
    @property
    def base_url(self) -> str:
        """Construct base URL for LoLLMs API."""
        return f"http://{self.host}:{self.port}"


class DatabaseConfig(BaseSettings):
    """Configuration for local SQLite database."""
    
    model_config = SettingsConfigDict(
        env_prefix="LOLLMSBOT_DB_",
        frozen=True,
        extra="ignore",
    )
    
    path: Path = Field(
        default=Path("./data/lollmsbot.db"),
        description="Path to SQLite database file",
    )
    
    @property
    def connection_string(self) -> str:
        """Generate SQLite connection string."""
        return f"sqlite:///{self.path.resolve()}"


class BotConfig(BaseSettings):
    """Configuration for bot identity and behavior."""
    
    model_config = SettingsConfigDict(
        env_prefix="LOLLMSBOT_BOT_",
        frozen=True,
        extra="ignore",
    )
    
    name: str = Field(
        default="LollmsBot",
        min_length=1,
        max_length=64,
        description="Bot display name",
    )
    description: str = Field(
        default="An AI assistant powered by LoLLMs",
        max_length=256,
        description="Bot description for help text",
    )
    max_history: int = Field(
        default=10,
        ge=1,
        le=100,
        description="Maximum conversation history length",
    )
    response_timeout: float = Field(
        default=60.0,
        gt=0.0,
        description="Maximum time to wait for response generation",
    )


class Settings(BaseSettings):
    """Main application settings combining all configuration sections."""
    
    model_config = SettingsConfigDict(
        env_prefix="LOLLMSBOT_",
        frozen=True,
        extra="ignore",
    )
    
    llm: LollmsConfig = Field(default_factory=LollmsConfig)
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    bot: BotConfig = Field(default_factory=BotConfig)
    
    debug: bool = Field(
        default=False,
        description="Enable debug logging",
    )
    log_level: str = Field(
        default="INFO",
        pattern=r"^(DEBUG|INFO|WARNING|ERROR|CRITICAL)$",
        description="Logging level",
    )


def load_settings(env_file: Optional[Path] = None) -> Settings:
    """
    Load settings from environment and optional .env file.
    
    Args:
        env_file: Optional path to .env file to load
        
    Returns:
        Configured Settings instance
    """
    if env_file is not None:
        return Settings(_env_file=env_file)
    return Settings()