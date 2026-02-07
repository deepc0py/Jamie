"""FastAPI controller for CUA streaming agent."""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from typing import Dict, Optional
import asyncio

from jamie.shared.models import (
    StreamRequest,
    StreamResponse,
    StopRequest,
    HealthResponse,
    StreamStatus,
)
from jamie.shared.config import AgentConfig, get_agent_config
from jamie.shared.logging import get_logger, setup_logging
from jamie.agent.streamer import StreamingAgent, AgentContext

log = get_logger(__name__)

app = FastAPI(title="Jamie CUA Controller", version="0.1.0")

# Store active agents
_agents: Dict[str, StreamingAgent] = {}
_agent_tasks: Dict[str, asyncio.Task] = {}
_config: Optional[AgentConfig] = None


def get_config() -> AgentConfig:
    """Get or create the agent configuration."""
    global _config
    if _config is None:
        _config = get_agent_config()
    return _config


@app.on_event("startup")
async def startup():
    """Initialize the controller on startup."""
    setup_logging(level="INFO")
    log.info("controller_started")


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        version="0.1.0",
        active_sessions=len(_agents),
    )


@app.post("/stream", response_model=StreamResponse)
async def start_stream(request: StreamRequest, background_tasks: BackgroundTasks):
    """Start a new streaming session."""
    
    # Check if session already exists
    if request.session_id in _agents:
        raise HTTPException(status_code=409, detail="Session already exists")
    
    config = get_config()
    
    # Create agent context
    context = AgentContext(
        session_id=request.session_id,
        url=str(request.url),
        guild_id=request.guild_id,
        channel_id=request.channel_id,
        channel_name=request.channel_name,
        discord_email=config.discord_email.get_secret_value(),
        discord_password=config.discord_password.get_secret_value(),
        model=config.model,
        max_budget=config.max_budget_per_session,
        sandbox_image=config.sandbox_image,
        display_resolution=config.display_resolution,
        webhook_url=str(request.webhook_url) if request.webhook_url else None,
    )
    
    # Create and store agent
    agent = StreamingAgent(context)
    _agents[request.session_id] = agent
    
    # Start agent in background
    async def run_agent():
        try:
            await agent.start()
        except Exception as e:
            log.error("agent_failed", session_id=request.session_id, error=str(e))
        finally:
            # Cleanup
            _agents.pop(request.session_id, None)
            _agent_tasks.pop(request.session_id, None)
    
    task = asyncio.create_task(run_agent())
    _agent_tasks[request.session_id] = task
    
    log.info("stream_started", session_id=request.session_id, url=str(request.url))
    
    return StreamResponse(
        session_id=request.session_id,
        status=StreamStatus.PENDING,
        message="Stream request accepted",
    )


@app.post("/stop/{session_id}", response_model=StreamResponse)
async def stop_stream(session_id: str, request: StopRequest):
    """Stop an active streaming session."""
    
    agent = _agents.get(session_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Stop the agent
    await agent.stop()
    
    # Cancel the task
    task = _agent_tasks.get(session_id)
    if task and not task.done():
        task.cancel()
    
    # Cleanup
    _agents.pop(session_id, None)
    _agent_tasks.pop(session_id, None)
    
    log.info("stream_stopped", session_id=session_id)
    
    return StreamResponse(
        session_id=session_id,
        status=StreamStatus.STOPPED,
        message="Stream stopped",
    )


@app.get("/sessions")
async def list_sessions():
    """List active sessions."""
    return {
        "count": len(_agents),
        "sessions": list(_agents.keys()),
    }
