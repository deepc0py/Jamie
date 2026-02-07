"""
Shared Pydantic models for Jamie API contracts.

This module defines the data models used for communication between
the Jamie Bot and CUA Controller via HTTP.

Classes:
    StreamRequest: Request to start a stream (Bot → Controller)
    StreamResponse: Response to stream request (Controller → Bot)
    StatusUpdate: Webhook payload for status updates (Controller → Bot)
    StopRequest: Request to stop a stream (Bot → Controller)
    HealthResponse: Health check response
"""

from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import datetime
from enum import Enum


class StreamRequestStatus(str, Enum):
    """Status of a stream request."""
    
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    IN_PROGRESS = "in_progress"


class StreamRequest(BaseModel):
    """
    Request to start a streaming session.
    
    Sent from Jamie Bot to CUA Controller when a user requests a stream.
    """
    
    session_id: str = Field(..., description="Unique session identifier")
    url: str = Field(..., description="URL to stream")
    guild_id: int = Field(..., description="Discord server ID")
    channel_id: int = Field(..., description="Voice channel ID")
    channel_name: str = Field(..., description="Voice channel name")
    webhook_url: Optional[str] = Field(None, description="URL for status callbacks")


class StreamResponse(BaseModel):
    """
    Response to a stream request.
    
    Returned from CUA Controller to Jamie Bot after receiving a stream request.
    """
    
    session_id: str
    status: StreamRequestStatus
    message: Optional[str] = None
    estimated_start_time: Optional[float] = Field(
        None,
        description="Estimated seconds until stream starts"
    )


class StatusUpdate(BaseModel):
    """
    Webhook payload for status updates.
    
    Sent from CUA Controller to Jamie Bot as stream status changes.
    """
    
    session_id: str
    status: str = Field(..., description="Current status: starting, streaming, error, ended")
    message: Optional[str] = None
    error_code: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class StopRequest(BaseModel):
    """
    Request to stop an active stream.
    
    Sent from Jamie Bot to CUA Controller when user requests stop.
    """
    
    session_id: str
    reason: Optional[str] = Field("user_requested", description="Reason for stop")


class HealthResponse(BaseModel):
    """Health check response from CUA Controller."""
    
    status: Literal["healthy", "degraded", "unhealthy"]
    sandbox_ready: bool
    active_sessions: int
    version: str
