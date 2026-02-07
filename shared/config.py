"""
Configuration management for Jamie.

This module handles loading and validating configuration from
environment variables and configuration files.

Classes:
    BotConfig: Configuration for Jamie Discord bot
    AgentConfig: Configuration for CUA Controller and agent
    Settings: Combined settings with validation

Functions:
    load_config: Load configuration from environment
"""

from typing import Optional
from dataclasses import dataclass


@dataclass
class BotConfig:
    """
    Configuration for the Jamie Discord bot.
    
    Attributes:
        discord_token: Discord bot authentication token
        cua_controller_url: URL of the CUA Controller HTTP API
        webhook_host: Host for receiving status webhooks
        webhook_port: Port for webhook server
    """
    
    discord_token: str
    cua_controller_url: str
    webhook_host: str = "0.0.0.0"
    webhook_port: int = 8080


@dataclass
class ControllerConfig:
    """
    Configuration for the CUA Controller.
    
    Attributes:
        discord_email: Discord account email for automation
        discord_password: Discord account password
        anthropic_api_key: API key for Claude model access
        host: Server bind host
        port: Server bind port
        max_budget_per_session: Maximum API cost per session in USD
    """
    
    discord_email: str
    discord_password: str
    anthropic_api_key: str
    host: str = "0.0.0.0"
    port: int = 8000
    max_budget_per_session: float = 2.0


def load_config() -> tuple[Optional[BotConfig], Optional[ControllerConfig]]:
    """
    Load configuration from environment variables.
    
    Returns:
        Tuple of (BotConfig, ControllerConfig), either may be None
        if required environment variables are missing.
    
    Environment Variables:
        Bot:
            DISCORD_BOT_TOKEN
            CUA_CONTROLLER_URL
            WEBHOOK_HOST (optional)
            WEBHOOK_PORT (optional)
        
        Controller:
            DISCORD_EMAIL
            DISCORD_PASSWORD
            ANTHROPIC_API_KEY
            CONTROLLER_HOST (optional)
            CONTROLLER_PORT (optional)
            MAX_BUDGET_PER_SESSION (optional)
    """
    # TODO: Implement configuration loading from os.environ
    raise NotImplementedError("Configuration loading not yet implemented")
