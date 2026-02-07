"""CUA Streaming Agent for Discord automation."""

from enum import Enum
from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime


class AgentState(str, Enum):
    """State of the CUA streaming agent."""
    IDLE = "idle"
    STARTING_SANDBOX = "starting_sandbox"
    LOGGING_IN = "logging_in"
    JOINING_VOICE = "joining_voice"
    OPENING_URL = "opening_url"
    STARTING_SHARE = "starting_share"
    STREAMING = "streaming"
    STOPPING = "stopping"
    STOPPED = "stopped"
    ERROR = "error"


@dataclass
class AgentContext:
    """Context for a streaming agent run."""
    
    session_id: str
    url: str
    guild_id: str
    channel_id: str
    channel_name: str
    
    # Discord credentials
    discord_email: str
    discord_password: str
    
    # Agent config
    model: str = "anthropic/claude-sonnet-4-5-20250929"
    max_budget: float = 2.0
    sandbox_image: str = "trycua/cua-xfce:latest"
    display_resolution: str = "1024x768"
    
    # Webhook for status updates
    webhook_url: Optional[str] = None


@dataclass 
class AgentRun:
    """Tracks an agent execution run."""
    
    context: AgentContext
    state: AgentState = AgentState.IDLE
    started_at: datetime = field(default_factory=datetime.utcnow)
    last_update: datetime = field(default_factory=datetime.utcnow)
    error_message: Optional[str] = None
    cost_so_far: float = 0.0
    iterations: int = 0
    
    def update_state(self, state: AgentState, error: Optional[str] = None) -> None:
        """Update agent state."""
        self.state = state
        self.last_update = datetime.utcnow()
        if error:
            self.error_message = error


class StreamingAgent:
    """CUA-powered agent that streams content to Discord voice channels."""
    
    def __init__(self, context: AgentContext):
        self.context = context
        self.run: Optional[AgentRun] = None
        self._computer = None  # CUA Computer instance
        self._agent = None  # CUA ComputerAgent instance
    
    async def start(self) -> None:
        """Start the streaming session."""
        ...
    
    async def stop(self) -> None:
        """Stop the streaming session."""
        ...
    
    async def _setup_sandbox(self) -> None:
        """Initialize CUA sandbox."""
        ...
    
    async def _login_discord(self) -> None:
        """Log into Discord web."""
        ...
    
    async def _join_voice_channel(self) -> None:
        """Join the target voice channel."""
        ...
    
    async def _open_url(self) -> None:
        """Open streaming URL in new tab."""
        ...
    
    async def _start_screen_share(self) -> None:
        """Start screen/tab sharing."""
        ...
    
    async def _send_status_update(self, status: str, error: Optional[str] = None) -> None:
        """Send status update via webhook."""
        ...
