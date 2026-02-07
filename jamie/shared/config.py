"""Configuration management for Jamie using pydantic-settings."""

from pydantic import SecretStr, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class BotConfig(BaseSettings):
    """Configuration for Jamie Discord bot."""
    
    model_config = SettingsConfigDict(
        env_prefix="JAMIE_BOT_",
        env_file=".env",
        extra="ignore",
    )
    
    # Discord
    discord_token: SecretStr = Field(..., description="Discord bot token")
    
    # CUA Agent
    cua_endpoint: str = Field(
        default="http://localhost:8000",
        description="CUA controller HTTP endpoint"
    )
    cua_timeout: int = Field(default=30, description="CUA request timeout in seconds")
    
    # Webhook
    webhook_host: str = Field(default="0.0.0.0", description="Webhook listener host")
    webhook_port: int = Field(default=8080, description="Webhook listener port")


class AgentConfig(BaseSettings):
    """Configuration for CUA streaming agent."""
    
    model_config = SettingsConfigDict(
        env_prefix="JAMIE_AGENT_",
        env_file=".env",
        extra="ignore",
    )
    
    # Discord credentials for web login
    discord_email: SecretStr = Field(..., description="Discord email for web login")
    discord_password: SecretStr = Field(..., description="Discord password")
    
    # Anthropic
    anthropic_api_key: SecretStr = Field(..., description="Anthropic API key")
    model: str = Field(
        default="anthropic/claude-sonnet-4-5-20250929",
        description="VLM model for CUA agent"
    )
    
    # Budget
    max_budget_per_session: float = Field(
        default=2.0,
        description="Maximum cost in dollars per streaming session"
    )
    
    # Sandbox
    sandbox_image: str = Field(
        default="trycua/cua-xfce:latest",
        description="Docker image for CUA sandbox"
    )
    display_resolution: str = Field(default="1024x768", description="Sandbox display resolution")
    
    # HTTP
    host: str = Field(default="0.0.0.0", description="Controller HTTP host")
    port: int = Field(default=8000, description="Controller HTTP port")


def get_bot_config() -> BotConfig:
    """Get bot configuration from environment."""
    return BotConfig()


def get_agent_config() -> AgentConfig:
    """Get agent configuration from environment."""
    return AgentConfig()
