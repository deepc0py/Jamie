"""
CUA streaming agent for Discord automation.

This module contains the core automation logic that controls a browser
inside a Docker sandbox to automate Discord streaming operations.

The agent uses Claude's vision capabilities to navigate Discord's UI
and perform actions like logging in, joining voice channels, and
initiating screen shares.

Classes:
    AgentState: Enum of agent lifecycle states
    AgentConfig: Configuration for agent behavior
    StreamingAgent: Main agent class that orchestrates streaming
    AgentError: Exception for agent execution failures
"""

from enum import Enum
from dataclasses import dataclass
from typing import Optional


class AgentState(Enum):
    """Agent lifecycle states during streaming workflow."""
    
    INITIALIZING = "initializing"    # Starting Docker sandbox
    LOGGING_IN = "logging_in"        # Authenticating with Discord
    JOINING_CHANNEL = "joining_channel"  # Connecting to voice channel
    OPENING_URL = "opening_url"      # Loading stream content
    SHARING_SCREEN = "sharing_screen"  # Starting screen share
    STREAMING = "streaming"          # Actively streaming
    STOPPING = "stopping"            # Graceful shutdown
    TERMINATED = "terminated"        # Successfully ended
    ERROR = "error"                  # Failed state


@dataclass
class AgentConfig:
    """
    Configuration for the streaming agent.
    
    Attributes:
        discord_email: Discord account email
        discord_password: Discord account password
        model: Claude model identifier for VLM
        max_budget: Maximum API cost per session in USD
        max_iterations: Maximum agent loop iterations
        screenshot_interval: Seconds between monitoring screenshots
    """
    
    discord_email: str
    discord_password: str
    model: str = "anthropic/claude-sonnet-4-5-20250929"
    max_budget: float = 2.0
    max_iterations: int = 50
    screenshot_interval: float = 2.0


class AgentError(Exception):
    """Exception raised when agent execution fails."""
    pass


class StreamingAgent:
    """
    CUA agent that automates Discord streaming.
    
    Orchestrates the full streaming workflow:
        1. Initialize Docker sandbox with browser
        2. Log into Discord web app
        3. Join the specified voice channel
        4. Open streaming URL in new tab
        5. Share screen via Discord
        6. Monitor stream until stop requested
        7. Clean up resources
    
    Uses Claude's vision capabilities to navigate UI elements
    and handle dynamic page states.
    
    Methods:
        start_stream: Execute full streaming workflow (async generator)
        stop: Request graceful shutdown
    """
    
    def __init__(self, config: AgentConfig):
        """
        Initialize the streaming agent.
        
        Args:
            config: Agent configuration
        """
        self.config = config
        self.state = AgentState.INITIALIZING
        self._stop_requested = False
    
    # TODO: Implement streaming workflow
    pass
