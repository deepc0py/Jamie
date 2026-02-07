"""CUA Streaming Agent for Discord automation."""

import asyncio
import aiohttp
from enum import Enum
from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime

# CUA imports
from computer import Computer
from agent import ComputerAgent

from jamie.agent.sandbox import SandboxManager, SandboxConfig
from jamie.agent.prompts import (
    DISCORD_LOGIN_PROMPT,
    JOIN_VOICE_CHANNEL_PROMPT,
    OPEN_URL_IN_NEW_TAB_PROMPT,
    START_SCREEN_SHARE_PROMPT,
    STOP_SCREEN_SHARE_PROMPT,
    LEAVE_VOICE_CHANNEL_PROMPT,
)


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
    
    # Server name for finding the server in Discord
    guild_name: str = ""
    
    # Discord credentials
    discord_email: str = ""
    discord_password: str = ""
    
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
        self._sandbox: Optional[SandboxManager] = None
        self._computer: Optional[Computer] = None
        self._agent: Optional[ComputerAgent] = None
        self._http_session: Optional[aiohttp.ClientSession] = None
    
    async def start(self) -> None:
        """Start the streaming session."""
        self.run = AgentRun(context=self.context)
        
        try:
            await self._setup_sandbox()
            await self._login_discord()
            await self._join_voice_channel()
            await self._open_url()
            await self._start_screen_share()
            
            self.run.update_state(AgentState.STREAMING)
            await self._send_status_update("streaming")
            
            # Keep running until stopped
            while self.run.state == AgentState.STREAMING:
                await asyncio.sleep(5)
                # Health check: verify we're still connected
                # Could take periodic screenshots and verify stream is active
                
        except Exception as e:
            self.run.update_state(AgentState.ERROR, str(e))
            await self._send_status_update("error", str(e))
            raise
        finally:
            # Ensure cleanup happens even on error
            await self._cleanup()
    
    async def stop(self) -> None:
        """Stop the streaming session."""
        if self.run and self.run.state == AgentState.STREAMING:
            self.run.update_state(AgentState.STOPPING)
            await self._send_status_update("stopping")
            
            try:
                # Stop screen share and leave voice channel
                await self._stop_screen_share()
                await self._leave_voice_channel()
            except Exception as e:
                # Log but don't fail on cleanup errors
                self.run.error_message = f"Cleanup warning: {e}"
            
            # Cleanup sandbox
            await self._cleanup()
            
            self.run.update_state(AgentState.STOPPED)
            await self._send_status_update("stopped")
        elif self.run:
            # Force stop if in other states
            self.run.update_state(AgentState.STOPPED)
            await self._cleanup()
    
    async def _setup_sandbox(self) -> None:
        """Initialize CUA sandbox."""
        self.run.update_state(AgentState.STARTING_SANDBOX)
        await self._send_status_update("starting_sandbox")
        
        config = SandboxConfig(
            image=self.context.sandbox_image,
            display=self.context.display_resolution,
        )
        self._sandbox = SandboxManager(config)
        self._computer = await self._sandbox.start()
        
        self._agent = ComputerAgent(
            model=self.context.model,
            tools=[self._computer],
            max_trajectory_budget=self.context.max_budget,
        )
    
    async def _login_discord(self) -> None:
        """Log into Discord web."""
        self.run.update_state(AgentState.LOGGING_IN)
        await self._send_status_update("logging_in")
        
        prompt = DISCORD_LOGIN_PROMPT.format(
            email=self.context.discord_email,
            password=self.context.discord_password,
        )
        
        await self._run_agent_task(prompt)
    
    async def _join_voice_channel(self) -> None:
        """Join the target voice channel."""
        self.run.update_state(AgentState.JOINING_VOICE)
        await self._send_status_update("joining_voice")
        
        # Use guild_name if available, otherwise leave it for the agent to figure out
        server_name = self.context.guild_name or f"Server ID: {self.context.guild_id}"
        
        prompt = JOIN_VOICE_CHANNEL_PROMPT.format(
            server_name=server_name,
            channel_name=self.context.channel_name,
        )
        
        await self._run_agent_task(prompt)
    
    async def _open_url(self) -> None:
        """Open streaming URL in new tab."""
        self.run.update_state(AgentState.OPENING_URL)
        await self._send_status_update("opening_url")
        
        prompt = OPEN_URL_IN_NEW_TAB_PROMPT.format(
            url=self.context.url,
        )
        
        await self._run_agent_task(prompt)
    
    async def _start_screen_share(self) -> None:
        """Start screen/tab sharing."""
        self.run.update_state(AgentState.STARTING_SHARE)
        await self._send_status_update("starting_share")
        
        prompt = START_SCREEN_SHARE_PROMPT.format(
            url=self.context.url,
        )
        
        await self._run_agent_task(prompt)
    
    async def _stop_screen_share(self) -> None:
        """Stop screen sharing."""
        prompt = STOP_SCREEN_SHARE_PROMPT
        await self._run_agent_task(prompt)
    
    async def _leave_voice_channel(self) -> None:
        """Leave the voice channel."""
        prompt = LEAVE_VOICE_CHANNEL_PROMPT
        await self._run_agent_task(prompt)
    
    async def _run_agent_task(self, prompt: str) -> None:
        """Run a task through the CUA agent and track usage."""
        if not self._agent:
            raise RuntimeError("Agent not initialized")
        
        async for result in self._agent.run(prompt):
            self.run.iterations += 1
            
            # Track cost from usage data
            if "usage" in result:
                usage = result["usage"]
                if "response_cost" in usage:
                    self.run.cost_so_far += usage["response_cost"]
            
            # Check for error states in output
            for item in result.get("output", []):
                if item.get("type") == "message":
                    content = item.get("content", [{}])
                    if content and isinstance(content, list):
                        text = content[0].get("text", "")
                        # Check for failure indicators
                        if any(err in text.upper() for err in [
                            "LOGIN_FAILED", "CAPTCHA", "2FA_REQUIRED",
                            "CHANNEL_NOT_FOUND", "SERVER_NOT_FOUND",
                            "SHARE_FAILED", "PERMISSION_DENIED"
                        ]):
                            raise AgentTaskError(f"Agent reported error: {text}")
    
    async def _send_status_update(self, status: str, error: Optional[str] = None) -> None:
        """Send status update via webhook."""
        if not self.context.webhook_url:
            return
        
        try:
            if not self._http_session:
                self._http_session = aiohttp.ClientSession()
            
            payload = {
                "session_id": self.context.session_id,
                "status": status,
                "message": error if error else f"State: {status}",
                "timestamp": datetime.utcnow().isoformat(),
                "cost_so_far": self.run.cost_so_far if self.run else 0.0,
                "iterations": self.run.iterations if self.run else 0,
            }
            
            if error:
                payload["error"] = error
            
            async with self._http_session.post(
                self.context.webhook_url,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=10)
            ) as resp:
                if resp.status >= 400:
                    # Log but don't fail on webhook errors
                    pass
                    
        except Exception:
            # Webhook failures shouldn't stop the streaming process
            pass
    
    async def _cleanup(self) -> None:
        """Clean up all resources."""
        # Close HTTP session
        if self._http_session:
            try:
                await self._http_session.close()
            except Exception:
                pass
            self._http_session = None
        
        # Stop sandbox
        if self._sandbox:
            try:
                await self._sandbox.stop()
            except Exception:
                pass
            self._sandbox = None
        
        self._computer = None
        self._agent = None


class AgentTaskError(Exception):
    """Error during agent task execution."""
    pass
