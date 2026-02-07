"""Shared API models for Jamie bot and agent communication."""

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, HttpUrl


class StreamStatus(str, Enum):
    """Status of a streaming session."""

    PENDING = "pending"
    STARTING = "starting"
    LOGGING_IN = "logging_in"
    JOINING_VOICE = "joining_voice"
    OPENING_URL = "opening_url"
    SHARING_SCREEN = "sharing_screen"
    STREAMING = "streaming"
    STOPPING = "stopping"
    STOPPED = "stopped"
    FAILED = "failed"


class StreamRequest(BaseModel):
    """Request to start a stream."""

    session_id: str = Field(..., description="Unique session identifier")
    url: HttpUrl = Field(..., description="URL to stream")
    guild_id: str = Field(..., description="Discord guild ID")
    channel_id: str = Field(..., description="Discord voice channel ID")
    channel_name: str = Field(..., description="Voice channel name for display")
    requester_id: str = Field(..., description="Discord user ID who requested")
    webhook_url: Optional[HttpUrl] = Field(
        None, description="Webhook for status updates"
    )


class StreamResponse(BaseModel):
    """Response to stream request."""

    session_id: str
    status: StreamStatus
    message: str


class StatusUpdate(BaseModel):
    """Status update sent via webhook."""

    session_id: str
    status: StreamStatus
    message: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    error_code: Optional[str] = None
    details: Optional[dict] = None


class StopRequest(BaseModel):
    """Request to stop a stream."""

    session_id: str
    requester_id: str


class HealthResponse(BaseModel):
    """Health check response with metrics summary."""

    status: str = "healthy"
    version: str = "0.1.0"
    active_sessions: int = 0
    uptime_seconds: Optional[float] = None
    streams_total: Optional[int] = None
    streams_success: Optional[int] = None
    streams_failed: Optional[int] = None
    success_rate_percent: Optional[float] = None
