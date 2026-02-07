"""CUA agent components for Discord automation."""

from .prompts import (
    DISCORD_LOGIN_PROMPT,
    JOIN_VOICE_CHANNEL_PROMPT,
    OPEN_URL_IN_NEW_TAB_PROMPT,
    START_SCREEN_SHARE_PROMPT,
    STOP_SCREEN_SHARE_PROMPT,
    LEAVE_VOICE_CHANNEL_PROMPT,
    TAKE_SCREENSHOT_PROMPT,
    HANDLE_ERROR_PROMPT,
)
from .sandbox import SandboxConfig, SandboxManager, create_sandbox
from .streamer import StreamingAgent, AgentContext, AgentState, AgentRun
from .controller import app

__all__ = [
    # Prompts
    "DISCORD_LOGIN_PROMPT",
    "JOIN_VOICE_CHANNEL_PROMPT",
    "OPEN_URL_IN_NEW_TAB_PROMPT",
    "START_SCREEN_SHARE_PROMPT",
    "STOP_SCREEN_SHARE_PROMPT",
    "LEAVE_VOICE_CHANNEL_PROMPT",
    "TAKE_SCREENSHOT_PROMPT",
    "HANDLE_ERROR_PROMPT",
    # Sandbox
    "SandboxConfig",
    "SandboxManager",
    "create_sandbox",
    # Streamer
    "StreamingAgent",
    "AgentContext",
    "AgentState",
    "AgentRun",
    # Controller
    "app",
]
