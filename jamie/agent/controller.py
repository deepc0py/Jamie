"""FastAPI controller for CUA streaming agent."""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import PlainTextResponse
from typing import Dict, Optional
import asyncio

from jamie.shared.models import (
    StreamRequest,
    StreamResponse,
    StopRequest,
    HealthResponse,
    StreamStatus,
)
from jamie.shared.config import (
    AgentConfig,
    ObservabilityConfig,
    get_agent_config,
    get_observability_config,
)
from jamie.shared.logging import get_logger, setup_logging
from jamie.shared.metrics import get_metrics
from jamie.agent.streamer import StreamingAgent, AgentContext

log = get_logger(__name__)

app = FastAPI(title="Jamie CUA Controller", version="0.1.0")

# Store active agents
_agents: Dict[str, StreamingAgent] = {}
_agent_tasks: Dict[str, asyncio.Task] = {}
_config: Optional[AgentConfig] = None
_obs_config: Optional[ObservabilityConfig] = None


def get_config() -> AgentConfig:
    """Get or create the agent configuration."""
    global _config
    if _config is None:
        _config = get_agent_config()
    return _config


def get_obs_config() -> ObservabilityConfig:
    """Get or create the observability configuration."""
    global _obs_config
    if _obs_config is None:
        _obs_config = get_observability_config()
    return _obs_config


@app.on_event("startup")
async def startup():
    """Initialize the controller on startup."""
    obs = get_obs_config()
    setup_logging(level=obs.log_level, json_output=obs.log_json)
    log.info("controller_started", log_level=obs.log_level, metrics_enabled=obs.metrics_enabled)


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint with metrics summary."""
    metrics = get_metrics()
    stats = metrics.get_stats()
    
    return HealthResponse(
        status="healthy",
        version="0.1.0",
        active_sessions=len(_agents),
        uptime_seconds=stats["uptime_seconds"],
        streams_total=stats["streams"]["total"],
        streams_success=stats["streams"]["success"],
        streams_failed=stats["streams"]["failed"],
        success_rate_percent=stats["streams"]["success_rate_percent"],
    )


@app.get("/metrics", response_class=PlainTextResponse)
async def prometheus_metrics():
    """Prometheus-compatible metrics endpoint."""
    obs = get_obs_config()
    if not obs.metrics_endpoint:
        raise HTTPException(status_code=404, detail="Metrics endpoint disabled")
    
    metrics = get_metrics()
    return metrics.to_prometheus()


@app.get("/stats")
async def detailed_stats():
    """Detailed metrics and statistics."""
    metrics = get_metrics()
    return metrics.get_stats()


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
    
    # Track metrics
    metrics = get_metrics()
    metrics.stream_started(request.session_id)
    
    # Start agent in background
    async def run_agent():
        success = False
        error_code = None
        try:
            await agent.start()
            success = True
        except Exception as e:
            log.error("agent_failed", session_id=request.session_id, error=str(e))
            error_code = type(e).__name__
        finally:
            # Record completion metrics
            metrics.stream_completed(request.session_id, success=success, error_code=error_code)
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
    
    # Record metrics - user-initiated stop is considered success
    metrics = get_metrics()
    metrics.stream_completed(session_id, success=True)
    
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
