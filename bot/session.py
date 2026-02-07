"""
Session management for Jamie streaming sessions.

This module provides state management for active streaming sessions,
including lifecycle tracking and status updates.

Classes:
    StreamStatus: Enum of session lifecycle states
    StreamSession: Data class representing a streaming session
    SessionManager: Thread-safe session state management
"""

from enum import Enum
from dataclasses import dataclass
from typing import Optional


class StreamStatus(Enum):
    """Lifecycle states for a streaming session."""
    
    PENDING = "pending"       # Request received, not yet started
    STARTING = "starting"     # CUA agent spinning up
    STREAMING = "streaming"   # Actively streaming
    STOPPING = "stopping"     # Stop requested, winding down
    ENDED = "ended"           # Session complete
    FAILED = "failed"         # Error occurred


@dataclass
class StreamSession:
    """
    Represents an active streaming session.
    
    Attributes:
        session_id: Unique identifier for this session
        requester_id: Discord user ID who initiated the stream
        guild_id: Discord server ID
        channel_id: Voice channel ID
        channel_name: Voice channel display name
        guild_name: Server display name
        url: The URL being streamed
        status: Current lifecycle state
        error_message: Error details if status is FAILED
    """
    
    session_id: str
    requester_id: int
    guild_id: int
    channel_id: int
    channel_name: str
    guild_name: str
    url: str
    status: StreamStatus = StreamStatus.PENDING
    error_message: Optional[str] = None


class SessionManager:
    """
    Manages streaming sessions with thread-safe state transitions.
    
    For MVP, supports only a single active session at a time.
    Future versions may support concurrent sessions.
    
    Methods:
        is_busy: Check if a session is currently active
        create_session: Start tracking a new session
        update_status: Transition session to new state
        end_session: Mark session complete and clear state
    """
    
    # TODO: Implement session management with asyncio.Lock
    pass
