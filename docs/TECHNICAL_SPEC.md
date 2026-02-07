# Jamie Technical Specification

> **Version:** 1.0  
> **Last Updated:** 2026-02-07  
> **Status:** Implementation-Ready  
> **Authors:** Technical Writing Team

---

## Table of Contents

1. [System Architecture](#1-system-architecture)
2. [Component Specifications](#2-component-specifications)
3. [Data Models](#3-data-models)
4. [API Specifications](#4-api-specifications)
5. [Infrastructure](#5-infrastructure)
6. [Security Design](#6-security-design)
7. [Error Handling](#7-error-handling)
8. [Testing Strategy](#8-testing-strategy)
9. [Performance Considerations](#9-performance-considerations)
10. [Implementation Notes](#10-implementation-notes)

---

## 1. System Architecture

### 1.1 Component Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              JAMIE SYSTEM                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌──────────────────┐         ┌──────────────────────────────────────────┐  │
│  │   Discord API    │◄───────►│              JAMIE BOT                   │  │
│  │   (Gateway)      │         │            (discord.py)                  │  │
│  │                  │         │                                          │  │
│  │  • DM Events     │         │  ┌─────────────────┐  ┌──────────────┐  │  │
│  │  • Voice States  │         │  │  Message        │  │  Voice       │  │  │
│  │  • Guild Data    │         │  │  Handler        │  │  Detector    │  │  │
│  └──────────────────┘         │  └────────┬────────┘  └──────┬───────┘  │  │
│                               │           │                  │          │  │
│                               │           ▼                  ▼          │  │
│                               │  ┌─────────────────────────────────┐    │  │
│                               │  │      Session Manager            │    │  │
│                               │  └─────────────┬───────────────────┘    │  │
│                               │                │                        │  │
│                               │                ▼                        │  │
│                               │  ┌─────────────────────────────────┐    │  │
│                               │  │      CUA Client (HTTP)          │    │  │
│                               │  └─────────────┬───────────────────┘    │  │
│                               └────────────────┼────────────────────────┘  │
│                                                │                            │
│                                                │ HTTP/JSON                  │
│                                                ▼                            │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                        CUA CONTROLLER                                │   │
│  │                      (FastAPI HTTP Server)                           │   │
│  │                                                                      │   │
│  │  ┌─────────────────┐  ┌─────────────────┐  ┌────────────────────┐   │   │
│  │  │  Task Queue     │  │  Agent Manager  │  │  Status Reporter   │   │   │
│  │  └────────┬────────┘  └────────┬────────┘  └────────┬───────────┘   │   │
│  │           │                    │                    │               │   │
│  └───────────┼────────────────────┼────────────────────┼───────────────┘   │
│              │                    │                    │                    │
│              ▼                    ▼                    ▼                    │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                       DOCKER SANDBOX                                 │   │
│  │                    (trycua/cua-xfce:latest)                          │   │
│  │                                                                      │   │
│  │  ┌─────────────────────────────────────────────────────────────┐    │   │
│  │  │                    CUA AGENT                                 │    │   │
│  │  │              (ComputerAgent + Computer)                      │    │   │
│  │  │                                                              │    │   │
│  │  │  ┌───────────────┐  ┌───────────────┐  ┌────────────────┐   │    │   │
│  │  │  │ Discord       │  │ Browser       │  │ Stream         │   │    │   │
│  │  │  │ Automator     │  │ Controller    │  │ Manager        │   │    │   │
│  │  │  └───────────────┘  └───────────────┘  └────────────────┘   │    │   │
│  │  └──────────────────────────────────────────────────────────────┘    │   │
│  │                                                                      │   │
│  │  ┌────────────────┐  ┌────────────────┐  ┌────────────────────┐     │   │
│  │  │  Firefox       │  │  XFCE Desktop  │  │  X11 Display       │     │   │
│  │  │  (Browser)     │  │  (GUI)         │  │  (1024x768)        │     │   │
│  │  └────────────────┘  └────────────────┘  └────────────────────┘     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      │ HTTPS
                                      ▼
                    ┌──────────────────────────────────┐
                    │        ANTHROPIC API             │
                    │   (Claude Sonnet 4.5 VLM)        │
                    └──────────────────────────────────┘
```

### 1.2 Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           STREAM REQUEST FLOW                                │
└─────────────────────────────────────────────────────────────────────────────┘

     USER                JAMIE BOT           CUA CONTROLLER        CUA AGENT
       │                     │                     │                    │
       │  1. DM with URL     │                     │                    │
       │────────────────────►│                     │                    │
       │                     │                     │                    │
       │                     │ 2. Detect voice     │                    │
       │                     │    channel          │                    │
       │                     │◄────────────────────┤                    │
       │                     │                     │                    │
       │  3. "Got it!"       │                     │                    │
       │◄────────────────────│                     │                    │
       │                     │                     │                    │
       │                     │ 4. POST /stream     │                    │
       │                     │────────────────────►│                    │
       │                     │                     │                    │
       │                     │ 5. {session_id}     │                    │
       │                     │◄────────────────────│                    │
       │                     │                     │                    │
       │                     │                     │ 6. Spawn agent     │
       │                     │                     │───────────────────►│
       │                     │                     │                    │
       │                     │                     │    7. Agent loop:  │
       │                     │                     │    - Screenshot    │
       │                     │                     │    - VLM decision  │
       │                     │                     │    - Action        │
       │                     │                     │◄──────────────────►│
       │                     │                     │                    │
       │                     │ 8. Webhook:         │                    │
       │                     │    status=streaming │                    │
       │                     │◄────────────────────│                    │
       │                     │                     │                    │
       │  9. "Now streaming!"│                     │                    │
       │◄────────────────────│                     │                    │
       │                     │                     │                    │
       ├─────────────────────┼─────────────────────┼────────────────────┤
       │                     │    STREAMING...     │                    │
       ├─────────────────────┼─────────────────────┼────────────────────┤
       │                     │                     │                    │
       │  10. DM "stop"      │                     │                    │
       │────────────────────►│                     │                    │
       │                     │                     │                    │
       │                     │ 11. POST /stop      │                    │
       │                     │────────────────────►│                    │
       │                     │                     │                    │
       │                     │                     │ 12. Terminate      │
       │                     │                     │───────────────────►│
       │                     │                     │                    │
       │                     │ 13. {status: ended} │                    │
       │                     │◄────────────────────│                    │
       │                     │                     │                    │
       │  14. "Stream ended" │                     │                    │
       │◄────────────────────│                     │                    │
       │                     │                     │                    │
```

### 1.3 Technology Stack

| Layer | Technology | Version | Purpose |
|-------|------------|---------|---------|
| **Discord Bot** | Python | 3.12+ | Runtime |
| | discord.py | 2.4+ | Discord API client |
| | aiohttp | 3.9+ | Async HTTP client for CUA |
| | pydantic | 2.5+ | Data validation |
| **CUA Controller** | Python | 3.12/3.13 | Runtime (CUA requirement) |
| | FastAPI | 0.110+ | HTTP API framework |
| | uvicorn | 0.27+ | ASGI server |
| | cua-computer | latest | Sandbox SDK |
| | cua-agent | latest | Agent framework |
| **CUA Agent** | Claude Sonnet 4.5 | 20250929 | Vision-Language Model |
| | Firefox | ESR | Browser in sandbox |
| **Infrastructure** | Docker | 24.0+ | Container runtime |
| | trycua/cua-xfce | latest | Lightweight Linux desktop |
| **Observability** | structlog | 24.1+ | Structured logging |
| | prometheus-client | 0.20+ | Metrics export |

---

## 2. Component Specifications

### 2.1 Jamie Bot (discord.py)

#### 2.1.1 Class Structure

```python
# jamie/bot/main.py

from __future__ import annotations
import asyncio
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional
import discord
from discord.ext import commands

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
    """Represents an active streaming session."""
    session_id: str
    requester_id: int              # Discord user ID
    guild_id: int                  # Discord server ID
    channel_id: int                # Voice channel ID
    channel_name: str              # Voice channel name
    guild_name: str                # Server name
    url: str                       # Streaming URL
    status: StreamStatus = StreamStatus.PENDING
    created_at: float = field(default_factory=lambda: asyncio.get_event_loop().time())
    error_message: Optional[str] = None


class SessionManager:
    """Manages streaming sessions (single-session for MVP)."""
    
    def __init__(self):
        self._current_session: Optional[StreamSession] = None
        self._lock = asyncio.Lock()
    
    @property
    def is_busy(self) -> bool:
        """Check if a session is currently active."""
        return self._current_session is not None and \
               self._current_session.status not in (StreamStatus.ENDED, StreamStatus.FAILED)
    
    @property
    def current_session(self) -> Optional[StreamSession]:
        return self._current_session
    
    async def create_session(self, session: StreamSession) -> bool:
        """Create a new session. Returns False if already busy."""
        async with self._lock:
            if self.is_busy:
                return False
            self._current_session = session
            return True
    
    async def update_status(self, session_id: str, status: StreamStatus, 
                           error: Optional[str] = None) -> bool:
        """Update session status. Returns False if session not found."""
        async with self._lock:
            if self._current_session and self._current_session.session_id == session_id:
                self._current_session.status = status
                if error:
                    self._current_session.error_message = error
                return True
            return False
    
    async def end_session(self, session_id: str) -> None:
        """Mark session as ended and clear it."""
        async with self._lock:
            if self._current_session and self._current_session.session_id == session_id:
                self._current_session.status = StreamStatus.ENDED
                self._current_session = None


class CUAClient:
    """HTTP client for communicating with CUA Controller."""
    
    def __init__(self, base_url: str, timeout: float = 30.0):
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self._session: Optional[aiohttp.ClientSession] = None
    
    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=self.timeout)
            )
        return self._session
    
    async def start_stream(self, request: StreamRequest) -> StreamResponse:
        """Send stream request to CUA Controller."""
        session = await self._get_session()
        async with session.post(
            f"{self.base_url}/stream",
            json=request.model_dump()
        ) as resp:
            data = await resp.json()
            if resp.status != 200:
                raise CUAError(data.get("error", "Unknown error"))
            return StreamResponse(**data)
    
    async def stop_stream(self, session_id: str) -> None:
        """Request stream termination."""
        session = await self._get_session()
        async with session.post(f"{self.base_url}/stop/{session_id}") as resp:
            if resp.status not in (200, 204):
                data = await resp.json()
                raise CUAError(data.get("error", "Failed to stop"))
    
    async def health_check(self) -> bool:
        """Check if CUA Controller is responsive."""
        try:
            session = await self._get_session()
            async with session.get(f"{self.base_url}/health") as resp:
                return resp.status == 200
        except Exception:
            return False
    
    async def close(self) -> None:
        if self._session and not self._session.closed:
            await self._session.close()


class JamieBot(commands.Bot):
    """Discord bot that receives URLs via DM and streams to voice channels."""
    
    # URL patterns for supported platforms
    URL_PATTERNS = [
        # YouTube
        re.compile(r'https?://(?:www\.)?youtube\.com/watch\?v=[\w\-]+'),
        re.compile(r'https?://youtu\.be/[\w\-]+'),
        # Twitch
        re.compile(r'https?://(?:www\.)?twitch\.tv/\w+'),
        # Vimeo
        re.compile(r'https?://(?:www\.)?vimeo\.com/\d+'),
        # General URLs (fallback)
        re.compile(r'https?://\S+'),
    ]
    
    def __init__(self, cua_endpoint: str):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.dm_messages = True
        intents.guilds = True
        intents.voice_states = True
        intents.members = True
        
        super().__init__(command_prefix='!', intents=intents)
        
        self.session_manager = SessionManager()
        self.cua_client = CUAClient(cua_endpoint)
    
    async def setup_hook(self) -> None:
        """Called when bot is ready to start."""
        # Verify CUA Controller is reachable
        if not await self.cua_client.health_check():
            raise RuntimeError("CUA Controller not reachable")
    
    async def close(self) -> None:
        await self.cua_client.close()
        await super().close()
```

#### 2.1.2 Event Handlers

```python
# jamie/bot/handlers.py

import uuid
from typing import Optional
import discord
from .main import JamieBot, StreamSession, StreamStatus

class MessageHandler:
    """Handles incoming DM messages."""
    
    def __init__(self, bot: JamieBot):
        self.bot = bot
        self._setup_handlers()
    
    def _setup_handlers(self) -> None:
        @self.bot.event
        async def on_message(message: discord.Message):
            # Ignore self
            if message.author == self.bot.user:
                return
            
            # Only process DMs
            if not isinstance(message.channel, discord.DMChannel):
                return
            
            await self._handle_dm(message)
    
    async def _handle_dm(self, message: discord.Message) -> None:
        """Route DM to appropriate handler."""
        content = message.content.strip().lower()
        
        # Stop command
        if content == "stop":
            await self._handle_stop(message)
            return
        
        # Status command (future)
        if content == "status":
            await self._handle_status(message)
            return
        
        # Help command
        if content == "help":
            await self._handle_help(message)
            return
        
        # Try to extract URL
        url = self._extract_url(message.content)
        if url:
            await self._handle_stream_request(message, url)
        else:
            await message.channel.send(
                "👋 Send me a YouTube, Twitch, or Vimeo URL and I'll stream it to your voice channel!\n"
                "Commands: `stop`, `status`, `help`"
            )
    
    def _extract_url(self, content: str) -> Optional[str]:
        """Extract first matching URL from message content."""
        for pattern in JamieBot.URL_PATTERNS:
            match = pattern.search(content)
            if match:
                return match.group(0)
        return None
    
    async def _handle_stream_request(self, message: discord.Message, url: str) -> None:
        """Process a stream request."""
        user = message.author
        
        # Check if already streaming
        if self.bot.session_manager.is_busy:
            session = self.bot.session_manager.current_session
            await message.channel.send(
                f"⏳ I'm already streaming to **{session.channel_name}** on **{session.guild_name}**.\n"
                "DM `stop` to end that stream first."
            )
            return
        
        # Find user's voice channel
        voice_channel = await self._find_user_voice_channel(user)
        if not voice_channel:
            await message.channel.send(
                "❌ You're not in any voice channel I can see.\n"
                "Join a voice channel in a server we share, then try again."
            )
            return
        
        # Create session
        session_id = str(uuid.uuid4())
        session = StreamSession(
            session_id=session_id,
            requester_id=user.id,
            guild_id=voice_channel.guild.id,
            channel_id=voice_channel.id,
            channel_name=voice_channel.name,
            guild_name=voice_channel.guild.name,
            url=url
        )
        
        if not await self.bot.session_manager.create_session(session):
            await message.channel.send("❌ Failed to create session. Please try again.")
            return
        
        # Acknowledge request
        await message.channel.send(
            f"🎬 Got it! Streaming to **{voice_channel.name}** on **{voice_channel.guild.name}**...\n"
            "This usually takes 30-60 seconds to set up."
        )
        
        # Send to CUA Controller
        try:
            await self.bot.cua_client.start_stream(StreamRequest(
                session_id=session_id,
                url=url,
                guild_id=voice_channel.guild.id,
                channel_id=voice_channel.id,
                channel_name=voice_channel.name,
                webhook_url=f"{JAMIE_WEBHOOK_BASE}/status"
            ))
        except CUAError as e:
            await self.bot.session_manager.update_status(
                session_id, StreamStatus.FAILED, str(e)
            )
            await message.channel.send(f"❌ Failed to start stream: {e}")
    
    async def _find_user_voice_channel(
        self, 
        user: discord.User
    ) -> Optional[discord.VoiceChannel]:
        """Find user's current voice channel across all shared guilds."""
        for guild in self.bot.guilds:
            member = guild.get_member(user.id)
            if member and member.voice and member.voice.channel:
                return member.voice.channel
        return None
    
    async def _handle_stop(self, message: discord.Message) -> None:
        """Handle stop command."""
        session = self.bot.session_manager.current_session
        
        if not session:
            await message.channel.send("ℹ️ Nothing is streaming right now.")
            return
        
        # Only requester can stop (for MVP)
        if session.requester_id != message.author.id:
            await message.channel.send(
                f"❌ Only the person who started the stream can stop it."
            )
            return
        
        await self.bot.session_manager.update_status(session.session_id, StreamStatus.STOPPING)
        
        try:
            await self.bot.cua_client.stop_stream(session.session_id)
            await message.channel.send("⏹️ Stream ended. Thanks for watching!")
        except CUAError as e:
            await message.channel.send(f"❌ Failed to stop stream: {e}")
    
    async def _handle_status(self, message: discord.Message) -> None:
        """Handle status command."""
        session = self.bot.session_manager.current_session
        
        if not session:
            await message.channel.send("ℹ️ Nothing is streaming right now.")
            return
        
        status_emoji = {
            StreamStatus.PENDING: "⏳",
            StreamStatus.STARTING: "🔄",
            StreamStatus.STREAMING: "▶️",
            StreamStatus.STOPPING: "⏹️",
            StreamStatus.ENDED: "✅",
            StreamStatus.FAILED: "❌"
        }
        
        await message.channel.send(
            f"{status_emoji.get(session.status, '❓')} **{session.status.value}**\n"
            f"Channel: {session.channel_name}\n"
            f"Server: {session.guild_name}\n"
            f"URL: {session.url}"
        )
    
    async def _handle_help(self, message: discord.Message) -> None:
        """Handle help command."""
        await message.channel.send(
            "**Jamie - URL Streamer**\n\n"
            "Send me a URL and I'll stream it to your voice channel!\n\n"
            "**Supported:**\n"
            "• YouTube videos and streams\n"
            "• Twitch channels and VODs\n"
            "• Vimeo videos\n"
            "• Any web page\n\n"
            "**Commands:**\n"
            "• `stop` - End the current stream\n"
            "• `status` - Check streaming status\n"
            "• `help` - Show this message\n\n"
            "**How it works:**\n"
            "1. Join a voice channel\n"
            "2. DM me a URL\n"
            "3. Wait ~30-60 seconds\n"
            "4. Watch together!"
        )
```

#### 2.1.3 State Management

The bot uses an in-memory `SessionManager` for MVP. State transitions:

```
                                    ┌──────────────────────┐
                                    │                      │
                         ┌──────────│      FAILED          │
                         │          │                      │
                         │          └──────────────────────┘
                         │                    ▲
                         │                    │ error
                         │                    │
┌──────────────┐    ┌────▼─────┐    ┌─────────┴──────────┐    ┌──────────────┐
│              │    │          │    │                    │    │              │
│   PENDING    │───►│ STARTING │───►│     STREAMING      │───►│   STOPPING   │
│              │    │          │    │                    │    │              │
└──────────────┘    └──────────┘    └────────────────────┘    └──────┬───────┘
                                                                     │
                                                                     ▼
                                                              ┌──────────────┐
                                                              │              │
                                                              │    ENDED     │
                                                              │              │
                                                              └──────────────┘
```

---

### 2.2 CUA Agent

#### 2.2.1 Sandbox Configuration

```python
# jamie/agent/sandbox.py

from computer import Computer

def create_sandbox() -> Computer:
    """Create a configured Docker sandbox for Discord streaming."""
    return Computer(
        os_type="linux",
        provider_type="docker",
        image="trycua/cua-xfce:latest",
        display="1024x768",  # XGA for optimal VLM accuracy
        memory="4GB",
        cpu="2",
        timeout=300,  # 5 minute timeout
        ephemeral=False,  # Persist browser profile
    )


# Sandbox environment setup script (run once after container start)
SETUP_SCRIPT = """
#!/bin/bash
set -e

# Ensure Firefox is installed
which firefox || apt-get update && apt-get install -y firefox-esr

# Create profile directory for Discord login persistence
mkdir -p /home/user/.mozilla/firefox/jamie.default

# Configure Firefox for streaming
cat > /home/user/.mozilla/firefox/jamie.default/user.js << 'EOF'
user_pref("media.autoplay.default", 0);
user_pref("media.autoplay.blocking_policy", 0);
user_pref("permissions.default.microphone", 1);
user_pref("permissions.default.camera", 1);
user_pref("media.navigator.permission.disabled", true);
user_pref("media.getusermedia.screensharing.enabled", true);
EOF

echo "Setup complete"
"""
```

#### 2.2.2 Agent Loop Design

```python
# jamie/agent/streamer.py

import asyncio
from typing import AsyncGenerator, Optional
from dataclasses import dataclass
from enum import Enum

from computer import Computer
from agent import ComputerAgent
from agent.callbacks import LoggingCallback, BudgetManagerCallback

from .actions import DiscordAutomator


class AgentState(Enum):
    """Agent lifecycle states."""
    INITIALIZING = "initializing"
    LOGGING_IN = "logging_in"
    JOINING_CHANNEL = "joining_channel"
    OPENING_URL = "opening_url"
    SHARING_SCREEN = "sharing_screen"
    STREAMING = "streaming"
    STOPPING = "stopping"
    TERMINATED = "terminated"
    ERROR = "error"


@dataclass
class AgentConfig:
    """Configuration for the streaming agent."""
    discord_email: str
    discord_password: str
    model: str = "anthropic/claude-sonnet-4-5-20250929"
    max_budget: float = 2.0  # Max cost per session
    max_iterations: int = 50  # Prevent runaway loops
    screenshot_interval: float = 2.0  # Seconds between screenshots during monitoring


class StreamingAgent:
    """CUA agent that automates Discord streaming."""
    
    def __init__(self, config: AgentConfig):
        self.config = config
        self.state = AgentState.INITIALIZING
        self.computer: Optional[Computer] = None
        self.agent: Optional[ComputerAgent] = None
        self._stop_requested = False
    
    async def start_stream(
        self, 
        url: str, 
        channel_name: str,
        guild_id: int
    ) -> AsyncGenerator[dict, None]:
        """
        Execute the full streaming workflow.
        
        Yields status updates as the agent progresses through steps.
        """
        try:
            # Initialize sandbox
            self.state = AgentState.INITIALIZING
            yield {"state": self.state.value, "message": "Starting sandbox..."}
            
            self.computer = await self._create_computer()
            await self.computer.run()
            
            # Create agent with budget control
            self.agent = ComputerAgent(
                model=self.config.model,
                tools=[self.computer],
                max_trajectory_budget=self.config.max_budget,
                callbacks=[
                    LoggingCallback(),
                    BudgetManagerCallback(
                        max_budget=self.config.max_budget,
                        reset_after_each_run=False
                    )
                ]
            )
            
            # Step 1: Login to Discord
            self.state = AgentState.LOGGING_IN
            yield {"state": self.state.value, "message": "Logging into Discord..."}
            
            login_result = await self._execute_task(
                f"Open Firefox and navigate to discord.com/login. "
                f"Log in with email '{self.config.discord_email}' and password. "
                f"Wait for the Discord app to fully load (you should see the server list)."
            )
            if not login_result["success"]:
                raise AgentError(f"Login failed: {login_result.get('error')}")
            
            # Step 2: Join voice channel
            self.state = AgentState.JOINING_CHANNEL
            yield {"state": self.state.value, "message": f"Joining {channel_name}..."}
            
            join_result = await self._execute_task(
                f"Find and click on the voice channel named '{channel_name}'. "
                f"You should join the voice channel and see yourself connected."
            )
            if not join_result["success"]:
                raise AgentError(f"Failed to join channel: {join_result.get('error')}")
            
            # Step 3: Open streaming URL in new tab
            self.state = AgentState.OPENING_URL
            yield {"state": self.state.value, "message": "Opening URL..."}
            
            open_result = await self._execute_task(
                f"Open a new browser tab (Ctrl+T) and navigate to: {url}. "
                f"Wait for the page to fully load. If it's a video, let it start playing."
            )
            if not open_result["success"]:
                raise AgentError(f"Failed to open URL: {open_result.get('error')}")
            
            # Step 4: Share screen via Discord
            self.state = AgentState.SHARING_SCREEN
            yield {"state": self.state.value, "message": "Starting screen share..."}
            
            share_result = await self._execute_task(
                f"Switch back to the Discord tab. "
                f"Click the 'Share Your Screen' button (monitor icon in the voice controls). "
                f"In the sharing picker, select the tab with the streaming content. "
                f"Click 'Share' or 'Go Live' to start streaming."
            )
            if not share_result["success"]:
                raise AgentError(f"Failed to share screen: {share_result.get('error')}")
            
            # Step 5: Streaming - monitor for issues
            self.state = AgentState.STREAMING
            yield {"state": self.state.value, "message": "Streaming!"}
            
            # Monitor loop - check periodically that stream is still active
            while not self._stop_requested:
                await asyncio.sleep(self.config.screenshot_interval)
                
                # Take screenshot to verify stream is active
                screenshot = await self.computer.interface.screenshot()
                # TODO: Verify stream is still running (check for disconnect dialogs, etc.)
                
                yield {"state": self.state.value, "message": "Streaming...", "active": True}
            
            # Step 6: Stop streaming
            self.state = AgentState.STOPPING
            yield {"state": self.state.value, "message": "Stopping stream..."}
            
            await self._execute_task(
                "Stop screen sharing by clicking the 'Stop Sharing' button. "
                "Then leave the voice channel by clicking the disconnect button."
            )
            
            self.state = AgentState.TERMINATED
            yield {"state": self.state.value, "message": "Stream ended"}
            
        except Exception as e:
            self.state = AgentState.ERROR
            yield {"state": self.state.value, "error": str(e)}
            raise
        
        finally:
            await self._cleanup()
    
    async def stop(self) -> None:
        """Request graceful shutdown of the stream."""
        self._stop_requested = True
    
    async def _create_computer(self) -> Computer:
        """Create and configure the sandbox computer."""
        return Computer(
            os_type="linux",
            provider_type="docker",
            image="trycua/cua-xfce:latest",
            display="1024x768",
            memory="4GB",
            cpu="2",
            timeout=300,
            ephemeral=False,
        )
    
    async def _execute_task(self, task: str) -> dict:
        """Execute a task using the CUA agent."""
        iteration = 0
        success = False
        error = None
        
        try:
            async for result in self.agent.run(task):
                iteration += 1
                
                if iteration > self.config.max_iterations:
                    error = "Max iterations exceeded"
                    break
                
                # Check for completion signals in agent output
                for item in result.get("output", []):
                    if item.get("type") == "message":
                        content = item.get("content", [{}])[0].get("text", "")
                        if "complete" in content.lower() or "done" in content.lower():
                            success = True
                            break
                
                if success:
                    break
            
            if not error:
                success = True
                
        except Exception as e:
            error = str(e)
        
        return {"success": success, "error": error, "iterations": iteration}
    
    async def _cleanup(self) -> None:
        """Clean up resources."""
        if self.computer:
            try:
                await self.computer.stop()
            except Exception:
                pass  # Best effort cleanup


class AgentError(Exception):
    """Error during agent execution."""
    pass
```

#### 2.2.3 Action Sequences for Discord Automation

```python
# jamie/agent/actions.py

"""
Pre-defined action sequences for common Discord operations.
These provide structured prompts for the CUA agent.
"""

DISCORD_LOGIN_PROMPT = """
Navigate to Discord Web and log in:

1. Open Firefox browser
2. Go to https://discord.com/login
3. Enter email: {email}
4. Click "Continue" or press Enter
5. Enter password: {password}
6. Click "Log In" or press Enter
7. If 2FA appears, STOP and report "2FA_REQUIRED"
8. Wait for the Discord app to fully load (server list visible)
9. Report "LOGIN_COMPLETE" when done

IMPORTANT:
- Do NOT click any "Download" buttons
- Do NOT accept any browser notifications
- If you see a captcha, report "CAPTCHA_REQUIRED"
"""

JOIN_VOICE_CHANNEL_PROMPT = """
Join a voice channel in Discord:

1. Look for the server with guild ID {guild_id} in the left sidebar
   OR find a server containing a voice channel named "{channel_name}"
2. Click on the server to open it
3. Find the voice channel named "{channel_name}" (has a speaker icon)
4. Click the voice channel to join
5. You should see yourself connected (your name appears in the channel)
6. If prompted about microphone permissions, click Allow
7. Report "JOINED_CHANNEL" when connected

If the channel is not found, report "CHANNEL_NOT_FOUND".
"""

OPEN_URL_PROMPT = """
Open a URL in a new browser tab:

1. Press Ctrl+T to open a new tab
2. Type the URL: {url}
3. Press Enter to navigate
4. Wait for the page to fully load
5. If it's a video (YouTube, Twitch, Vimeo):
   - Wait for the video player to load
   - Click play if video doesn't auto-play
   - Optionally, click fullscreen
6. Report "URL_LOADED" when the content is ready

If the URL fails to load, report "URL_FAILED" with the error.
"""

START_SCREEN_SHARE_PROMPT = """
Start sharing the browser tab via Discord:

1. Switch to the Discord tab (Ctrl+Tab or click Discord tab)
2. Look for the voice channel controls at the bottom of the screen
3. Find the "Share Your Screen" button (looks like a monitor with an arrow)
4. Click "Share Your Screen"
5. A picker dialog will appear with tabs/windows to share
6. Find and select the tab showing the streaming content (YouTube/Twitch/etc)
7. Make sure "Share audio" or "Also share tab audio" is checked if available
8. Click "Share" or "Go Live"
9. Verify you see a preview of your stream in Discord
10. Report "SHARING_STARTED" when complete

If screen sharing fails or the dialog doesn't appear, report "SHARE_FAILED".
"""

STOP_SCREEN_SHARE_PROMPT = """
Stop screen sharing and leave voice:

1. Look for the "Stop Sharing" button in Discord (usually red or in the preview area)
2. Click "Stop Sharing" to end the screen share
3. Verify the stream preview disappears
4. Find the "Disconnect" button (phone icon with X, usually red)
5. Click "Disconnect" to leave the voice channel
6. Verify you're no longer in the voice channel
7. Report "STOPPED" when complete
"""

# Error recovery prompts
HANDLE_DISCONNECT_PROMPT = """
Handle an unexpected disconnect:

1. Check if you're still connected to voice
2. If disconnected, try rejoining: click the voice channel again
3. If screen share stopped, restart it using the "Share Your Screen" button
4. Report current status: RECONNECTED, FAILED_TO_RECONNECT, or STREAMING
"""
```

---

### 2.3 Communication Layer

#### 2.3.1 API Contracts

```python
# jamie/shared/models.py

from pydantic import BaseModel, Field, HttpUrl
from typing import Optional, Literal
from datetime import datetime
from enum import Enum


class StreamRequestStatus(str, Enum):
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    IN_PROGRESS = "in_progress"


class StreamRequest(BaseModel):
    """Request to start a stream (Jamie Bot → CUA Controller)."""
    
    session_id: str = Field(..., description="Unique session identifier")
    url: str = Field(..., description="URL to stream")
    guild_id: int = Field(..., description="Discord server ID")
    channel_id: int = Field(..., description="Voice channel ID")
    channel_name: str = Field(..., description="Voice channel name")
    webhook_url: Optional[str] = Field(None, description="URL for status callbacks")
    
    class Config:
        json_schema_extra = {
            "example": {
                "session_id": "550e8400-e29b-41d4-a716-446655440000",
                "url": "https://youtube.com/watch?v=dQw4w9WgXcQ",
                "guild_id": 123456789012345678,
                "channel_id": 987654321098765432,
                "channel_name": "Movie Night",
                "webhook_url": "http://jamie-bot:8080/status"
            }
        }


class StreamResponse(BaseModel):
    """Response to stream request (CUA Controller → Jamie Bot)."""
    
    session_id: str
    status: StreamRequestStatus
    message: Optional[str] = None
    estimated_start_time: Optional[float] = Field(
        None, 
        description="Estimated seconds until stream starts"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "session_id": "550e8400-e29b-41d4-a716-446655440000",
                "status": "accepted",
                "message": "Stream starting",
                "estimated_start_time": 45.0
            }
        }


class StatusUpdate(BaseModel):
    """Webhook payload for status updates (CUA Controller → Jamie Bot)."""
    
    session_id: str
    status: str = Field(..., description="Current status: starting, streaming, error, ended")
    message: Optional[str] = None
    error_code: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_schema_extra = {
            "example": {
                "session_id": "550e8400-e29b-41d4-a716-446655440000",
                "status": "streaming",
                "message": "Screen share active",
                "timestamp": "2026-02-07T12:34:56Z"
            }
        }


class StopRequest(BaseModel):
    """Request to stop a stream (Jamie Bot → CUA Controller)."""
    
    session_id: str
    reason: Optional[str] = Field("user_requested", description="Reason for stop")


class HealthResponse(BaseModel):
    """Health check response."""
    
    status: Literal["healthy", "degraded", "unhealthy"]
    sandbox_ready: bool
    active_sessions: int
    version: str
```

#### 2.3.2 Message Formats

**HTTP Request/Response Examples:**

```http
# Start stream
POST /stream HTTP/1.1
Host: cua-controller:8000
Content-Type: application/json

{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "url": "https://youtube.com/watch?v=dQw4w9WgXcQ",
  "guild_id": 123456789012345678,
  "channel_id": 987654321098765432,
  "channel_name": "Movie Night",
  "webhook_url": "http://jamie-bot:8080/status"
}

---

HTTP/1.1 200 OK
Content-Type: application/json

{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "accepted",
  "message": "Stream starting",
  "estimated_start_time": 45.0
}
```

```http
# Stop stream
POST /stop/550e8400-e29b-41d4-a716-446655440000 HTTP/1.1
Host: cua-controller:8000
Content-Type: application/json

{
  "reason": "user_requested"
}

---

HTTP/1.1 204 No Content
```

```http
# Status webhook (CUA → Jamie)
POST /status HTTP/1.1
Host: jamie-bot:8080
Content-Type: application/json

{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "streaming",
  "message": "Screen share active",
  "timestamp": "2026-02-07T12:34:56Z"
}
```

#### 2.3.3 Error Codes

| Code | HTTP Status | Description | Recovery |
|------|-------------|-------------|----------|
| `ERR_BUSY` | 409 | Another stream is active | Wait or stop existing stream |
| `ERR_INVALID_URL` | 400 | URL not parseable or blocked | User provides different URL |
| `ERR_SANDBOX_FAILED` | 503 | Docker sandbox won't start | Retry or escalate |
| `ERR_LOGIN_FAILED` | 401 | Discord login failed | Check credentials |
| `ERR_2FA_REQUIRED` | 401 | Account requires 2FA | Use non-2FA account |
| `ERR_CAPTCHA` | 401 | CAPTCHA required | Manual intervention |
| `ERR_CHANNEL_NOT_FOUND` | 404 | Voice channel not accessible | Verify permissions |
| `ERR_SHARE_FAILED` | 500 | Screen share didn't work | Retry stream |
| `ERR_TIMEOUT` | 504 | Operation timed out | Retry |
| `ERR_BUDGET_EXCEEDED` | 402 | API cost limit reached | End session |
| `ERR_MAX_ITERATIONS` | 500 | Agent loop exceeded limit | End session |
| `ERR_UNKNOWN` | 500 | Unexpected error | Log and investigate |

---

## 3. Data Models

### 3.1 Session State Schema

```python
# jamie/shared/schemas.py

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List
from enum import Enum


class SessionState(str, Enum):
    PENDING = "pending"
    STARTING = "starting"
    STREAMING = "streaming"
    STOPPING = "stopping"
    ENDED = "ended"
    FAILED = "failed"


@dataclass
class Session:
    """Complete session state model."""
    
    # Identity
    session_id: str
    
    # Discord context
    requester_id: int  # User who requested
    guild_id: int
    channel_id: int
    channel_name: str
    guild_name: str
    
    # Stream details
    url: str
    
    # State
    state: SessionState = SessionState.PENDING
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    
    # Timing
    created_at: datetime = field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    
    # Agent tracking
    agent_iterations: int = 0
    agent_cost_usd: float = 0.0
    
    # Metrics
    viewer_count: int = 0  # Future: track viewers


@dataclass
class SessionMetrics:
    """Aggregated session metrics."""
    
    total_sessions: int = 0
    successful_sessions: int = 0
    failed_sessions: int = 0
    total_streaming_seconds: float = 0.0
    total_cost_usd: float = 0.0
    avg_start_time_seconds: float = 0.0
```

### 3.2 Stream Request Schema

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "StreamRequest",
  "type": "object",
  "required": ["session_id", "url", "guild_id", "channel_id", "channel_name"],
  "properties": {
    "session_id": {
      "type": "string",
      "format": "uuid",
      "description": "Unique identifier for this streaming session"
    },
    "url": {
      "type": "string",
      "format": "uri",
      "pattern": "^https?://",
      "description": "URL to stream"
    },
    "guild_id": {
      "type": "integer",
      "minimum": 0,
      "description": "Discord server snowflake ID"
    },
    "channel_id": {
      "type": "integer", 
      "minimum": 0,
      "description": "Voice channel snowflake ID"
    },
    "channel_name": {
      "type": "string",
      "minLength": 1,
      "maxLength": 100,
      "description": "Voice channel display name"
    },
    "webhook_url": {
      "type": "string",
      "format": "uri",
      "description": "URL for status update callbacks"
    }
  }
}
```

### 3.3 Configuration Schema

```python
# jamie/config/settings.py

from pydantic_settings import BaseSettings
from pydantic import Field, SecretStr
from typing import Optional


class DiscordSettings(BaseSettings):
    """Discord bot configuration."""
    
    bot_token: SecretStr = Field(..., env="DISCORD_BOT_TOKEN")
    streaming_email: SecretStr = Field(..., env="DISCORD_EMAIL")
    streaming_password: SecretStr = Field(..., env="DISCORD_PASSWORD")
    
    class Config:
        env_prefix = ""


class CUASettings(BaseSettings):
    """CUA agent configuration."""
    
    anthropic_api_key: SecretStr = Field(..., env="ANTHROPIC_API_KEY")
    model: str = Field(
        "anthropic/claude-sonnet-4-5-20250929", 
        env="CUA_MODEL"
    )
    max_budget_usd: float = Field(2.0, env="CUA_MAX_BUDGET")
    max_iterations: int = Field(50, env="CUA_MAX_ITERATIONS")
    screenshot_interval: float = Field(2.0, env="CUA_SCREENSHOT_INTERVAL")
    
    class Config:
        env_prefix = ""


class SandboxSettings(BaseSettings):
    """Docker sandbox configuration."""
    
    image: str = Field("trycua/cua-xfce:latest", env="SANDBOX_IMAGE")
    display_resolution: str = Field("1024x768", env="SANDBOX_RESOLUTION")
    memory: str = Field("4GB", env="SANDBOX_MEMORY")
    cpu: str = Field("2", env="SANDBOX_CPU")
    timeout_seconds: int = Field(300, env="SANDBOX_TIMEOUT")
    
    class Config:
        env_prefix = ""


class ServerSettings(BaseSettings):
    """HTTP server configuration."""
    
    host: str = Field("0.0.0.0", env="SERVER_HOST")
    port: int = Field(8000, env="SERVER_PORT")
    webhook_base_url: Optional[str] = Field(None, env="WEBHOOK_BASE_URL")
    
    class Config:
        env_prefix = ""


class Settings(BaseSettings):
    """Root configuration container."""
    
    discord: DiscordSettings = DiscordSettings()
    cua: CUASettings = CUASettings()
    sandbox: SandboxSettings = SandboxSettings()
    server: ServerSettings = ServerSettings()
    
    # Logging
    log_level: str = Field("INFO", env="LOG_LEVEL")
    log_format: str = Field("json", env="LOG_FORMAT")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


def get_settings() -> Settings:
    """Load and validate settings."""
    return Settings()
```

---

## 4. API Specifications

### 4.1 Internal APIs (Jamie ↔ CUA)

#### 4.1.1 CUA Controller API

```python
# jamie/agent/controller.py

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
import asyncio
from typing import Dict

from ..shared.models import (
    StreamRequest, StreamResponse, StatusUpdate, 
    StopRequest, HealthResponse, StreamRequestStatus
)
from .streamer import StreamingAgent, AgentConfig


app = FastAPI(title="Jamie CUA Controller", version="1.0.0")

# In-memory state (single session for MVP)
active_session: Dict = {}
agent: StreamingAgent = None


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Check controller health status."""
    return HealthResponse(
        status="healthy",
        sandbox_ready=True,  # TODO: Actually check Docker
        active_sessions=1 if active_session else 0,
        version="1.0.0"
    )


@app.post("/stream", response_model=StreamResponse)
async def start_stream(request: StreamRequest, background_tasks: BackgroundTasks):
    """
    Start a new streaming session.
    
    Returns immediately with session_id. Stream status updates sent via webhook.
    """
    global active_session, agent
    
    # Check if already busy
    if active_session:
        raise HTTPException(
            status_code=409,
            detail={"error": "ERR_BUSY", "message": "Another stream is active"}
        )
    
    # Validate URL
    if not _validate_url(request.url):
        raise HTTPException(
            status_code=400,
            detail={"error": "ERR_INVALID_URL", "message": "URL not supported"}
        )
    
    # Create session
    active_session = {
        "session_id": request.session_id,
        "url": request.url,
        "channel_name": request.channel_name,
        "webhook_url": request.webhook_url,
        "status": "starting"
    }
    
    # Start agent in background
    background_tasks.add_task(
        _run_stream,
        request.session_id,
        request.url,
        request.channel_name,
        request.guild_id,
        request.webhook_url
    )
    
    return StreamResponse(
        session_id=request.session_id,
        status=StreamRequestStatus.ACCEPTED,
        message="Stream starting",
        estimated_start_time=45.0
    )


@app.post("/stop/{session_id}")
async def stop_stream(session_id: str):
    """Stop an active stream."""
    global active_session, agent
    
    if not active_session or active_session.get("session_id") != session_id:
        raise HTTPException(
            status_code=404,
            detail={"error": "ERR_NOT_FOUND", "message": "Session not found"}
        )
    
    if agent:
        await agent.stop()
    
    active_session = {}
    return JSONResponse(status_code=204, content=None)


@app.get("/session/{session_id}")
async def get_session(session_id: str):
    """Get current session status."""
    if not active_session or active_session.get("session_id") != session_id:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return active_session


async def _run_stream(
    session_id: str, 
    url: str, 
    channel_name: str, 
    guild_id: int,
    webhook_url: str
):
    """Background task to run the streaming agent."""
    global active_session, agent
    
    config = AgentConfig(
        discord_email=settings.discord.streaming_email.get_secret_value(),
        discord_password=settings.discord.streaming_password.get_secret_value(),
        model=settings.cua.model,
        max_budget=settings.cua.max_budget_usd,
        max_iterations=settings.cua.max_iterations
    )
    
    agent = StreamingAgent(config)
    
    try:
        async for update in agent.start_stream(url, channel_name, guild_id):
            active_session["status"] = update.get("state", "unknown")
            
            # Send webhook update
            if webhook_url:
                await _send_webhook(webhook_url, StatusUpdate(
                    session_id=session_id,
                    status=update.get("state"),
                    message=update.get("message"),
                    error_code=update.get("error_code")
                ))
    
    except Exception as e:
        active_session["status"] = "error"
        active_session["error"] = str(e)
        
        if webhook_url:
            await _send_webhook(webhook_url, StatusUpdate(
                session_id=session_id,
                status="error",
                error_code="ERR_UNKNOWN",
                message=str(e)
            ))
    
    finally:
        active_session = {}
        agent = None


def _validate_url(url: str) -> bool:
    """Validate URL is supported."""
    import re
    patterns = [
        r'https?://(?:www\.)?youtube\.com/watch\?v=',
        r'https?://youtu\.be/',
        r'https?://(?:www\.)?twitch\.tv/',
        r'https?://(?:www\.)?vimeo\.com/',
        r'https?://\S+',  # General fallback
    ]
    return any(re.match(p, url) for p in patterns)


async def _send_webhook(url: str, update: StatusUpdate):
    """Send status update via webhook."""
    import aiohttp
    async with aiohttp.ClientSession() as session:
        try:
            await session.post(url, json=update.model_dump())
        except Exception:
            pass  # Best effort
```

#### 4.1.2 Jamie Bot Webhook Receiver

```python
# jamie/bot/webhook.py

from fastapi import FastAPI, Request
from ..shared.models import StatusUpdate

app = FastAPI(title="Jamie Bot Webhook Receiver")


@app.post("/status")
async def receive_status(update: StatusUpdate):
    """
    Receive status updates from CUA Controller.
    
    Updates session state and notifies user via DM.
    """
    session = bot.session_manager.current_session
    
    if not session or session.session_id != update.session_id:
        return {"status": "ignored", "reason": "session_not_found"}
    
    # Map status to StreamStatus
    status_map = {
        "starting": StreamStatus.STARTING,
        "streaming": StreamStatus.STREAMING,
        "stopping": StreamStatus.STOPPING,
        "ended": StreamStatus.ENDED,
        "error": StreamStatus.FAILED
    }
    
    new_status = status_map.get(update.status, StreamStatus.PENDING)
    await bot.session_manager.update_status(
        update.session_id, 
        new_status, 
        update.message
    )
    
    # Notify user
    user = await bot.fetch_user(session.requester_id)
    
    if new_status == StreamStatus.STREAMING:
        await user.send(
            f"✅ Now streaming! Everyone in **{session.channel_name}** should see it.\n"
            "DM me `stop` when you're done."
        )
    elif new_status == StreamStatus.FAILED:
        await user.send(
            f"❌ Something went wrong: {update.message or 'Unknown error'}\n"
            "Try again, or try a different URL."
        )
    elif new_status == StreamStatus.ENDED:
        await user.send("⏹️ Stream ended. Thanks for watching!")
    
    return {"status": "processed"}
```

### 4.2 External Integrations

#### 4.2.1 Discord API Usage

```python
# Required Discord API permissions and intents

REQUIRED_BOT_PERMISSIONS = [
    "VIEW_CHANNEL",      # See channels in servers
    "SEND_MESSAGES",     # Reply to DMs
    "READ_MESSAGE_HISTORY",  # Access DM history
]

REQUIRED_INTENTS = {
    "guilds": True,           # Access server information
    "guild_members": True,    # See member voice states (privileged)
    "voice_states": True,     # Detect voice channel presence
    "dm_messages": True,      # Receive DMs
    "message_content": True,  # Read DM content (privileged)
}

# Bot invite URL generator
def generate_invite_url(client_id: str) -> str:
    permissions = 2048  # Send messages + View channels
    return (
        f"https://discord.com/api/oauth2/authorize"
        f"?client_id={client_id}"
        f"&permissions={permissions}"
        f"&scope=bot"
    )
```

#### 4.2.2 Anthropic API Usage

```python
# CUA uses Anthropic API via the cua-agent framework

# Model configuration
MODEL = "anthropic/claude-sonnet-4-5-20250929"

# Tool definition (handled by CUA framework)
COMPUTER_TOOL = {
    "type": "computer_20250124",
    "name": "computer",
    "display_width_px": 1024,
    "display_height_px": 768,
}

# Budget tracking
# CUA framework automatically tracks:
# - Input tokens (screenshots, context)
# - Output tokens (actions, reasoning)
# - Cost per action

# Approximate costs (Sonnet 4.5):
# - Input: $3 / 1M tokens
# - Output: $15 / 1M tokens
# - Per screenshot: ~1000 tokens (768p JPEG)
# - Per action cycle: ~500 tokens output
```

---

## 5. Infrastructure

### 5.1 Docker Configuration

```yaml
# docker-compose.yml

version: "3.8"

services:
  jamie-bot:
    build:
      context: .
      dockerfile: Dockerfile.bot
    container_name: jamie-bot
    restart: unless-stopped
    environment:
      - DISCORD_BOT_TOKEN=${DISCORD_BOT_TOKEN}
      - CUA_ENDPOINT=http://cua-controller:8000
      - WEBHOOK_BASE_URL=http://jamie-bot:8080
      - LOG_LEVEL=INFO
    ports:
      - "8080:8080"  # Webhook receiver
    networks:
      - jamie-network
    depends_on:
      - cua-controller

  cua-controller:
    build:
      context: .
      dockerfile: Dockerfile.agent
    container_name: cua-controller
    restart: unless-stopped
    environment:
      - DISCORD_EMAIL=${DISCORD_EMAIL}
      - DISCORD_PASSWORD=${DISCORD_PASSWORD}
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
      - CUA_MODEL=anthropic/claude-sonnet-4-5-20250929
      - CUA_MAX_BUDGET=2.0
      - LOG_LEVEL=INFO
    ports:
      - "8000:8000"
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock  # Docker-in-Docker
      - cua-profiles:/home/user/.mozilla  # Persist Firefox profile
    networks:
      - jamie-network
    privileged: true  # Required for Docker-in-Docker

networks:
  jamie-network:
    driver: bridge

volumes:
  cua-profiles:
```

```dockerfile
# Dockerfile.bot

FROM python:3.12-slim

WORKDIR /app

# Install dependencies
COPY requirements-bot.txt .
RUN pip install --no-cache-dir -r requirements-bot.txt

# Copy source
COPY jamie/bot ./jamie/bot
COPY jamie/shared ./jamie/shared
COPY jamie/config ./jamie/config

# Run
CMD ["python", "-m", "jamie.bot.main"]
```

```dockerfile
# Dockerfile.agent

FROM python:3.12-slim

# Install Docker CLI for Docker-in-Docker
RUN apt-get update && apt-get install -y \
    docker.io \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install dependencies
COPY requirements-agent.txt .
RUN pip install --no-cache-dir -r requirements-agent.txt

# Pull CUA sandbox image at build time (optional, speeds up first run)
# RUN docker pull --platform=linux/amd64 trycua/cua-xfce:latest

# Copy source
COPY jamie/agent ./jamie/agent
COPY jamie/shared ./jamie/shared
COPY jamie/config ./jamie/config

# Run
CMD ["uvicorn", "jamie.agent.controller:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 5.2 Environment Variables

```bash
# .env.example

# =============================================================================
# DISCORD CONFIGURATION
# =============================================================================

# Bot token from Discord Developer Portal
DISCORD_BOT_TOKEN=your_bot_token_here

# Streaming account credentials (separate from bot account)
DISCORD_EMAIL=streaming-account@example.com
DISCORD_PASSWORD=secure_password_here

# =============================================================================
# ANTHROPIC CONFIGURATION  
# =============================================================================

# API key for Claude access
ANTHROPIC_API_KEY=sk-ant-api03-xxxx

# =============================================================================
# CUA CONFIGURATION
# =============================================================================

# VLM model to use (cost vs accuracy tradeoff)
CUA_MODEL=anthropic/claude-sonnet-4-5-20250929

# Maximum cost per streaming session (USD)
CUA_MAX_BUDGET=2.0

# Maximum agent iterations before giving up
CUA_MAX_ITERATIONS=50

# Seconds between screenshots during streaming
CUA_SCREENSHOT_INTERVAL=2.0

# =============================================================================
# SANDBOX CONFIGURATION
# =============================================================================

# Docker image for CUA sandbox
SANDBOX_IMAGE=trycua/cua-xfce:latest

# Display resolution (XGA recommended for accuracy)
SANDBOX_RESOLUTION=1024x768

# Container resource limits
SANDBOX_MEMORY=4GB
SANDBOX_CPU=2

# Timeout for sandbox operations (seconds)
SANDBOX_TIMEOUT=300

# =============================================================================
# SERVER CONFIGURATION
# =============================================================================

# CUA Controller address (for Jamie Bot to connect to)
CUA_ENDPOINT=http://localhost:8000

# Webhook base URL (for CUA Controller to callback)
WEBHOOK_BASE_URL=http://localhost:8080

# =============================================================================
# LOGGING
# =============================================================================

# Log level: DEBUG, INFO, WARNING, ERROR
LOG_LEVEL=INFO

# Log format: json, text
LOG_FORMAT=json
```

### 5.3 Deployment Topology

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          DEPLOYMENT TOPOLOGY                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                         HOST MACHINE                                   │  │
│  │                   (Linux VPS / Home Server)                           │  │
│  │                                                                        │  │
│  │  ┌─────────────────────────────────────────────────────────────────┐  │  │
│  │  │                    DOCKER ENGINE                                 │  │  │
│  │  │                                                                  │  │  │
│  │  │  ┌─────────────────┐     ┌─────────────────────────────────┐   │  │  │
│  │  │  │                 │     │                                  │   │  │  │
│  │  │  │   jamie-bot     │     │      cua-controller              │   │  │  │
│  │  │  │                 │     │                                  │   │  │  │
│  │  │  │  Port 8080      │◄───►│  Port 8000                       │   │  │  │
│  │  │  │  (webhook)      │     │  (API)                           │   │  │  │
│  │  │  │                 │     │                                  │   │  │  │
│  │  │  └─────────────────┘     │  ┌───────────────────────────┐  │   │  │  │
│  │  │          │               │  │  cua-xfce (sandbox)       │  │   │  │  │
│  │  │          │               │  │                           │  │   │  │  │
│  │  │          │               │  │  • Firefox                │  │   │  │  │
│  │  │          │               │  │  • XFCE Desktop           │  │   │  │  │
│  │  │          │               │  │  • X11 @ 1024x768         │  │   │  │  │
│  │  │          │               │  │                           │  │   │  │  │
│  │  │          │               │  └───────────────────────────┘  │   │  │  │
│  │  │          │               │             ▲                   │   │  │  │
│  │  │          │               └─────────────┼───────────────────┘   │  │  │
│  │  │          │                             │                       │  │  │
│  │  └──────────┼─────────────────────────────┼───────────────────────┘  │  │
│  │             │                             │                          │  │
│  └─────────────┼─────────────────────────────┼──────────────────────────┘  │
│                │                             │                              │
│                ▼                             ▼                              │
│  ┌─────────────────────────┐   ┌─────────────────────────────────────────┐  │
│  │     Discord Gateway     │   │           Anthropic API                 │  │
│  │   (wss://gateway...)    │   │   (api.anthropic.com)                   │  │
│  └─────────────────────────┘   └─────────────────────────────────────────┘  │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘

NETWORK:
├── jamie-network (bridge)
│   ├── jamie-bot ──────────► cua-controller:8000 (HTTP)
│   └── cua-controller ─────► jamie-bot:8080 (webhook)
│
└── External
    ├── jamie-bot ──────────► Discord Gateway (WSS)
    └── cua-controller ─────► Anthropic API (HTTPS)

VOLUMES:
├── cua-profiles ────────────► /home/user/.mozilla (Firefox profile)
└── /var/run/docker.sock ───► Docker-in-Docker access
```

---

## 6. Security Design

### 6.1 Authentication Flows

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        AUTHENTICATION FLOWS                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  [1] DISCORD BOT AUTHENTICATION                                              │
│  ───────────────────────────────                                             │
│                                                                              │
│  Jamie Bot                         Discord Gateway                           │
│      │                                   │                                   │
│      │  1. IDENTIFY (bot token)          │                                   │
│      │──────────────────────────────────►│                                   │
│      │                                   │                                   │
│      │  2. READY (session)               │                                   │
│      │◄──────────────────────────────────│                                   │
│      │                                   │                                   │
│      │  3. HEARTBEAT (interval)          │                                   │
│      │◄─────────────────────────────────►│                                   │
│                                                                              │
│  Token is loaded from DISCORD_BOT_TOKEN env var.                             │
│  Never logged, never transmitted except to Discord.                          │
│                                                                              │
│  ─────────────────────────────────────────────────────────────────────────   │
│                                                                              │
│  [2] DISCORD WEB AUTHENTICATION (CUA Agent)                                  │
│  ──────────────────────────────────────────                                  │
│                                                                              │
│  CUA Agent (Firefox)              Discord Web                                │
│      │                                   │                                   │
│      │  1. Navigate to /login            │                                   │
│      │──────────────────────────────────►│                                   │
│      │                                   │                                   │
│      │  2. Type email                    │                                   │
│      │──────────────────────────────────►│                                   │
│      │                                   │                                   │
│      │  3. Type password                 │                                   │
│      │──────────────────────────────────►│                                   │
│      │                                   │                                   │
│      │  4. Session cookie stored         │                                   │
│      │◄──────────────────────────────────│                                   │
│      │                                   │                                   │
│      │  5. (Profile persisted)           │                                   │
│      │                                   │                                   │
│                                                                              │
│  Credentials from DISCORD_EMAIL / DISCORD_PASSWORD env vars.                 │
│  Firefox profile persisted to avoid re-login each session.                   │
│  ⚠️ 2FA must be disabled on streaming account.                               │
│                                                                              │
│  ─────────────────────────────────────────────────────────────────────────   │
│                                                                              │
│  [3] ANTHROPIC API AUTHENTICATION                                            │
│  ────────────────────────────────                                            │
│                                                                              │
│  CUA Framework                    Anthropic API                              │
│      │                                   │                                   │
│      │  Authorization: Bearer {key}      │                                   │
│      │──────────────────────────────────►│                                   │
│      │                                   │                                   │
│                                                                              │
│  API key from ANTHROPIC_API_KEY env var.                                     │
│  Managed by CUA framework, not exposed to agent prompts.                     │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

### 6.2 Credential Management

```python
# jamie/config/credentials.py

"""
Credential management utilities.

All credentials are:
- Loaded from environment variables only
- Wrapped in SecretStr to prevent accidental logging
- Never passed through agent prompts in plaintext
"""

from pydantic import SecretStr
import os


class CredentialError(Exception):
    """Raised when required credentials are missing."""
    pass


def load_secret(env_var: str, required: bool = True) -> SecretStr:
    """
    Load a secret from environment variable.
    
    Args:
        env_var: Name of environment variable
        required: If True, raise error when missing
        
    Returns:
        SecretStr containing the value
        
    Raises:
        CredentialError if required and missing
    """
    value = os.environ.get(env_var)
    
    if not value and required:
        raise CredentialError(
            f"Required environment variable {env_var} is not set. "
            f"See .env.example for required variables."
        )
    
    return SecretStr(value or "")


def validate_credentials() -> dict:
    """
    Validate all required credentials are present.
    
    Returns dict of credential names → masked values for logging.
    """
    creds = {
        "DISCORD_BOT_TOKEN": load_secret("DISCORD_BOT_TOKEN"),
        "DISCORD_EMAIL": load_secret("DISCORD_EMAIL"),
        "DISCORD_PASSWORD": load_secret("DISCORD_PASSWORD"),
        "ANTHROPIC_API_KEY": load_secret("ANTHROPIC_API_KEY"),
    }
    
    # Return masked versions for logging
    return {
        name: f"{value.get_secret_value()[:4]}...{value.get_secret_value()[-4:]}"
        if len(value.get_secret_value()) > 8 else "***"
        for name, value in creds.items()
    }


# Logging filter to redact secrets
class SecretFilter:
    """Log filter that redacts known secret patterns."""
    
    PATTERNS = [
        (r'sk-ant-api03-[\w-]+', '[ANTHROPIC_KEY]'),
        (r'[\w-]{24}\.[\w-]{6}\.[\w-]{27}', '[DISCORD_TOKEN]'),
        (r'password["\']?\s*[:=]\s*["\']?[\w@#$%^&*]+', 'password=[REDACTED]'),
    ]
    
    @classmethod
    def filter(cls, record: str) -> str:
        import re
        result = record
        for pattern, replacement in cls.PATTERNS:
            result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)
        return result
```

### 6.3 Sandbox Isolation

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         SANDBOX ISOLATION MODEL                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                          HOST SYSTEM                                   │  │
│  │                                                                        │  │
│  │   ┌─────────────────────────────────────────────────────────────────┐ │  │
│  │   │                    DOCKER CONTAINER                              │ │  │
│  │   │                    (cua-controller)                              │ │  │
│  │   │                                                                  │ │  │
│  │   │   ┌───────────────────────────────────────────────────────────┐ │ │  │
│  │   │   │                 CUA SANDBOX                                │ │ │  │
│  │   │   │              (trycua/cua-xfce)                             │ │ │  │
│  │   │   │                                                            │ │ │  │
│  │   │   │  ┌──────────────────────────────────────────────────────┐ │ │ │  │
│  │   │   │  │              AGENT EXECUTION                          │ │ │ │  │
│  │   │   │  │                                                       │ │ │ │  │
│  │   │   │  │  • Firefox (browsing Discord, YouTube)                │ │ │ │  │
│  │   │   │  │  • Agent prompts (Claude reasoning)                   │ │ │ │  │
│  │   │   │  │  • Screenshots (screen capture)                       │ │ │ │  │
│  │   │   │  │                                                       │ │ │ │  │
│  │   │   │  └──────────────────────────────────────────────────────┘ │ │ │  │
│  │   │   │                                                            │ │ │  │
│  │   │   │  ISOLATION BOUNDARIES:                                     │ │ │  │
│  │   │   │  ✗ No access to host filesystem                           │ │ │  │
│  │   │   │  ✗ No access to host network (except allowed egress)      │ │ │  │
│  │   │   │  ✗ No access to other containers                          │ │ │  │
│  │   │   │  ✗ No privilege escalation                                │ │ │  │
│  │   │   │  ✓ Allowed egress: discord.com, youtube.com, etc.         │ │ │  │
│  │   │   │  ✓ Allowed egress: api.anthropic.com                      │ │ │  │
│  │   │   │                                                            │ │ │  │
│  │   │   └───────────────────────────────────────────────────────────┘ │ │  │
│  │   │                                                                  │ │  │
│  │   └─────────────────────────────────────────────────────────────────┘ │  │
│  │                                                                        │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘

PROMPT INJECTION MITIGATIONS:

1. Agent ONLY executes pre-defined task prompts
   - Login prompt
   - Join channel prompt
   - Open URL prompt
   - Share screen prompt
   
2. Agent does NOT:
   - Read text from streamed content
   - Follow instructions visible on screen
   - Execute arbitrary user-provided commands
   
3. URL validation:
   - Only http/https schemes
   - Blocklist for known malicious domains
   - No file:// or javascript: URLs
```

---

## 7. Error Handling

### 7.1 Error Taxonomy

```python
# jamie/shared/errors.py

from enum import Enum
from typing import Optional
from dataclasses import dataclass


class ErrorCategory(Enum):
    """Top-level error categories."""
    USER_ERROR = "user"           # User-caused, recoverable by user
    TRANSIENT = "transient"       # Temporary, retry may help
    CONFIGURATION = "config"      # Misconfiguration, admin intervention
    EXTERNAL = "external"         # Third-party service failure
    INTERNAL = "internal"         # Bug or unexpected state


class ErrorCode(Enum):
    """Specific error codes with metadata."""
    
    # User errors (4xx equivalent)
    ERR_NOT_IN_VOICE = ("E4001", ErrorCategory.USER_ERROR, "User not in a voice channel")
    ERR_INVALID_URL = ("E4002", ErrorCategory.USER_ERROR, "URL format not recognized")
    ERR_BUSY = ("E4003", ErrorCategory.USER_ERROR, "Stream already in progress")
    ERR_NOT_REQUESTER = ("E4004", ErrorCategory.USER_ERROR, "Only requester can stop")
    
    # Transient errors (retry may help)
    ERR_SANDBOX_TIMEOUT = ("E5001", ErrorCategory.TRANSIENT, "Sandbox operation timed out")
    ERR_DISCORD_RATE_LIMIT = ("E5002", ErrorCategory.TRANSIENT, "Discord rate limited")
    ERR_STREAM_DROPPED = ("E5003", ErrorCategory.TRANSIENT, "Stream unexpectedly ended")
    ERR_AGENT_STUCK = ("E5004", ErrorCategory.TRANSIENT, "Agent loop not progressing")
    
    # Configuration errors
    ERR_NO_BOT_TOKEN = ("E6001", ErrorCategory.CONFIGURATION, "Bot token not configured")
    ERR_INVALID_CREDS = ("E6002", ErrorCategory.CONFIGURATION, "Discord credentials invalid")
    ERR_2FA_REQUIRED = ("E6003", ErrorCategory.CONFIGURATION, "Account requires 2FA")
    ERR_NO_API_KEY = ("E6004", ErrorCategory.CONFIGURATION, "Anthropic API key missing")
    
    # External service errors
    ERR_DISCORD_DOWN = ("E7001", ErrorCategory.EXTERNAL, "Discord services unavailable")
    ERR_ANTHROPIC_DOWN = ("E7002", ErrorCategory.EXTERNAL, "Anthropic API unavailable")
    ERR_URL_UNREACHABLE = ("E7003", ErrorCategory.EXTERNAL, "Streaming URL not accessible")
    ERR_CAPTCHA = ("E7004", ErrorCategory.EXTERNAL, "CAPTCHA challenge required")
    
    # Internal errors
    ERR_BUDGET_EXCEEDED = ("E8001", ErrorCategory.INTERNAL, "Cost budget exceeded")
    ERR_MAX_ITERATIONS = ("E8002", ErrorCategory.INTERNAL, "Max iterations exceeded")
    ERR_UNKNOWN = ("E9999", ErrorCategory.INTERNAL, "Unexpected error")
    
    def __init__(self, code: str, category: ErrorCategory, message: str):
        self._code = code
        self._category = category
        self._message = message
    
    @property
    def code(self) -> str:
        return self._code
    
    @property
    def category(self) -> ErrorCategory:
        return self._category
    
    @property
    def default_message(self) -> str:
        return self._message


@dataclass
class JamieError(Exception):
    """Structured error for Jamie system."""
    
    error_code: ErrorCode
    message: Optional[str] = None
    details: Optional[dict] = None
    
    def __str__(self) -> str:
        msg = self.message or self.error_code.default_message
        return f"[{self.error_code.code}] {msg}"
    
    @property
    def is_retryable(self) -> bool:
        return self.error_code.category == ErrorCategory.TRANSIENT
    
    @property
    def user_message(self) -> str:
        """User-friendly error message."""
        messages = {
            ErrorCode.ERR_NOT_IN_VOICE: (
                "❌ You're not in any voice channel I can see.\n"
                "Join a voice channel in a server we share, then try again."
            ),
            ErrorCode.ERR_INVALID_URL: (
                "❌ I couldn't find a valid URL in your message.\n"
                "Send me a YouTube, Twitch, or Vimeo link to stream!"
            ),
            ErrorCode.ERR_BUSY: (
                "⏳ I'm already streaming somewhere else.\n"
                "DM `stop` to end that stream first."
            ),
            ErrorCode.ERR_SANDBOX_TIMEOUT: (
                "❌ Stream setup timed out.\n"
                "Please try again."
            ),
            ErrorCode.ERR_URL_UNREACHABLE: (
                "❌ I couldn't load that URL.\n"
                "It might be geoblocked or require a login."
            ),
            ErrorCode.ERR_BUDGET_EXCEEDED: (
                "❌ This session got too expensive.\n"
                "Try again with a simpler request."
            ),
        }
        return messages.get(
            self.error_code,
            f"❌ Something went wrong: {self.message or self.error_code.default_message}"
        )
```

### 7.2 Recovery Strategies

| Error Code | Category | Strategy | Max Retries | Backoff |
|------------|----------|----------|-------------|---------|
| `ERR_SANDBOX_TIMEOUT` | Transient | Auto-retry with fresh sandbox | 2 | Exponential (5s, 15s) |
| `ERR_DISCORD_RATE_LIMIT` | Transient | Wait and retry | 3 | Use `Retry-After` header |
| `ERR_STREAM_DROPPED` | Transient | Attempt reconnection | 3 | Fixed (5s) |
| `ERR_AGENT_STUCK` | Transient | Reset agent, retry | 1 | None |
| `ERR_CAPTCHA` | External | Alert user, wait | 0 | N/A (manual) |
| `ERR_2FA_REQUIRED` | Config | Fail permanently | 0 | N/A |
| `ERR_BUDGET_EXCEEDED` | Internal | Terminate session | 0 | N/A |

```python
# jamie/shared/recovery.py

import asyncio
from typing import Callable, TypeVar, Awaitable
from .errors import JamieError, ErrorCategory

T = TypeVar('T')


async def with_retry(
    operation: Callable[[], Awaitable[T]],
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 30.0,
    exponential: bool = True
) -> T:
    """
    Execute async operation with retry logic.
    
    Only retries on transient errors.
    """
    last_error = None
    delay = base_delay
    
    for attempt in range(max_retries + 1):
        try:
            return await operation()
        
        except JamieError as e:
            last_error = e
            
            # Don't retry non-transient errors
            if e.error_code.category != ErrorCategory.TRANSIENT:
                raise
            
            if attempt < max_retries:
                await asyncio.sleep(delay)
                if exponential:
                    delay = min(delay * 2, max_delay)
        
        except Exception as e:
            # Wrap unexpected errors
            raise JamieError(
                error_code=ErrorCode.ERR_UNKNOWN,
                message=str(e)
            ) from e
    
    raise last_error
```

### 7.3 Logging Requirements

```python
# jamie/shared/logging.py

import structlog
from datetime import datetime
from typing import Any

# Configure structlog
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    wrapper_class=structlog.stdlib.BoundLogger,
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)


def get_logger(name: str) -> structlog.BoundLogger:
    """Get a configured logger instance."""
    return structlog.get_logger(name)


# Required log events and their fields:

LOG_EVENTS = {
    # Session lifecycle
    "session.created": ["session_id", "user_id", "guild_id", "channel_id", "url"],
    "session.started": ["session_id", "startup_time_ms"],
    "session.streaming": ["session_id"],
    "session.ended": ["session_id", "duration_seconds", "cost_usd"],
    "session.failed": ["session_id", "error_code", "error_message"],
    
    # Agent events
    "agent.iteration": ["session_id", "iteration", "action_type"],
    "agent.screenshot": ["session_id", "size_bytes"],
    "agent.action": ["session_id", "action", "success"],
    "agent.budget_warning": ["session_id", "spent_usd", "limit_usd"],
    
    # HTTP events
    "http.request": ["method", "path", "status_code", "duration_ms"],
    "webhook.sent": ["session_id", "status", "success"],
    
    # Discord events
    "discord.dm_received": ["user_id", "content_length"],
    "discord.voice_detected": ["user_id", "guild_id", "channel_id"],
}


# Example log output (JSON format):
"""
{
  "timestamp": "2026-02-07T12:34:56.789Z",
  "level": "info",
  "logger": "jamie.bot.handlers",
  "event": "session.created",
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "user_id": 123456789,
  "guild_id": 987654321,
  "channel_id": 111222333,
  "url": "https://youtube.com/watch?v=dQw4w9WgXcQ"
}
"""
```

---

## 8. Testing Strategy

### 8.1 Unit Test Coverage

```python
# tests/unit/test_session_manager.py

import pytest
import asyncio
from jamie.bot.main import SessionManager, StreamSession, StreamStatus


class TestSessionManager:
    """Unit tests for SessionManager."""
    
    @pytest.fixture
    def manager(self):
        return SessionManager()
    
    @pytest.fixture
    def sample_session(self):
        return StreamSession(
            session_id="test-123",
            requester_id=1,
            guild_id=2,
            channel_id=3,
            channel_name="test-channel",
            guild_name="test-server",
            url="https://youtube.com/watch?v=test"
        )
    
    @pytest.mark.asyncio
    async def test_create_session_when_idle(self, manager, sample_session):
        """Should allow creating session when no session exists."""
        result = await manager.create_session(sample_session)
        assert result is True
        assert manager.current_session == sample_session
    
    @pytest.mark.asyncio
    async def test_create_session_when_busy(self, manager, sample_session):
        """Should reject new session when one is active."""
        await manager.create_session(sample_session)
        
        other_session = StreamSession(
            session_id="other-456",
            requester_id=9,
            guild_id=8,
            channel_id=7,
            channel_name="other-channel",
            guild_name="other-server",
            url="https://youtube.com/watch?v=other"
        )
        
        result = await manager.create_session(other_session)
        assert result is False
        assert manager.current_session.session_id == "test-123"
    
    @pytest.mark.asyncio
    async def test_is_busy_reflects_state(self, manager, sample_session):
        """is_busy should reflect session state."""
        assert manager.is_busy is False
        
        await manager.create_session(sample_session)
        assert manager.is_busy is True
        
        await manager.update_status(sample_session.session_id, StreamStatus.ENDED)
        assert manager.is_busy is False
    
    @pytest.mark.asyncio
    async def test_update_nonexistent_session(self, manager):
        """Updating nonexistent session should return False."""
        result = await manager.update_status("fake-id", StreamStatus.STREAMING)
        assert result is False


# tests/unit/test_url_extraction.py

import pytest
from jamie.bot.handlers import MessageHandler


class TestURLExtraction:
    """Unit tests for URL extraction logic."""
    
    @pytest.fixture
    def handler(self, mocker):
        mock_bot = mocker.Mock()
        return MessageHandler(mock_bot)
    
    @pytest.mark.parametrize("content,expected", [
        ("https://youtube.com/watch?v=dQw4w9WgXcQ", "https://youtube.com/watch?v=dQw4w9WgXcQ"),
        ("check this out https://youtu.be/dQw4w9WgXcQ please", "https://youtu.be/dQw4w9WgXcQ"),
        ("https://twitch.tv/shroud", "https://twitch.tv/shroud"),
        ("https://www.twitch.tv/shroud", "https://www.twitch.tv/shroud"),
        ("https://vimeo.com/123456789", "https://vimeo.com/123456789"),
        ("no url here", None),
        ("", None),
    ])
    def test_extract_url(self, handler, content, expected):
        """Should extract URL correctly from various message formats."""
        result = handler._extract_url(content)
        assert result == expected


# Target coverage: 90%+ for bot/ and shared/ modules
```

### 8.2 Integration Test Plan

```python
# tests/integration/test_jamie_cua_integration.py

import pytest
import asyncio
import aiohttp
from unittest.mock import AsyncMock, patch


class TestJamieCUAIntegration:
    """Integration tests for Jamie Bot ↔ CUA Controller communication."""
    
    @pytest.fixture
    async def mock_cua_server(self, aiohttp_server):
        """Start a mock CUA Controller server."""
        from aiohttp import web
        
        app = web.Application()
        
        async def handle_stream(request):
            data = await request.json()
            return web.json_response({
                "session_id": data["session_id"],
                "status": "accepted",
                "estimated_start_time": 30.0
            })
        
        async def handle_stop(request):
            return web.Response(status=204)
        
        async def handle_health(request):
            return web.json_response({
                "status": "healthy",
                "sandbox_ready": True,
                "active_sessions": 0,
                "version": "1.0.0"
            })
        
        app.router.add_post("/stream", handle_stream)
        app.router.add_post("/stop/{session_id}", handle_stop)
        app.router.add_get("/health", handle_health)
        
        return await aiohttp_server(app)
    
    @pytest.mark.asyncio
    async def test_start_stream_flow(self, mock_cua_server):
        """Test full start stream request/response cycle."""
        from jamie.bot.main import CUAClient
        
        client = CUAClient(f"http://localhost:{mock_cua_server.port}")
        
        response = await client.start_stream(StreamRequest(
            session_id="test-123",
            url="https://youtube.com/watch?v=test",
            guild_id=1,
            channel_id=2,
            channel_name="test"
        ))
        
        assert response.status == StreamRequestStatus.ACCEPTED
        assert response.session_id == "test-123"
        
        await client.close()
    
    @pytest.mark.asyncio
    async def test_webhook_delivery(self, mock_cua_server, mocker):
        """Test status update webhook is received and processed."""
        # Setup webhook receiver
        received_updates = []
        
        async def webhook_handler(request):
            data = await request.json()
            received_updates.append(data)
            return web.Response(status=200)
        
        # ... (webhook server setup)
        
        # Trigger stream that sends webhook
        # ...
        
        # Assert webhook received
        assert len(received_updates) == 1
        assert received_updates[0]["status"] == "streaming"
```

### 8.3 E2E Test Scenarios

```yaml
# tests/e2e/scenarios.yaml

# These scenarios require a running instance with real Discord/Anthropic access
# Run manually or in a dedicated E2E pipeline

scenarios:
  - name: "Happy Path: Stream YouTube Video"
    preconditions:
      - User is in voice channel "Test Channel"
      - Jamie bot is online
      - CUA sandbox is ready
    steps:
      - action: "DM Jamie: 'https://youtube.com/watch?v=dQw4w9WgXcQ'"
        expect:
          - message_contains: "Got it! Streaming to **Test Channel**"
      - wait: 60s
      - action: "Check voice channel"
        expect:
          - jamie_in_channel: true
          - stream_visible: true
      - action: "DM Jamie: 'stop'"
        expect:
          - message_contains: "Stream ended"
          - jamie_in_channel: false

  - name: "Error: User Not in Voice"
    preconditions:
      - User is NOT in any voice channel
    steps:
      - action: "DM Jamie: 'https://youtube.com/watch?v=test'"
        expect:
          - message_contains: "not in any voice channel"

  - name: "Error: Already Streaming"
    preconditions:
      - Jamie is already streaming in another channel
    steps:
      - action: "DM Jamie: 'https://youtube.com/watch?v=test'"
        expect:
          - message_contains: "already streaming"

  - name: "Error: Invalid URL"
    preconditions:
      - User is in voice channel
    steps:
      - action: "DM Jamie: 'this is not a url'"
        expect:
          - message_contains: "Send me a YouTube"

  - name: "Resilience: Agent Timeout Recovery"
    preconditions:
      - User is in voice channel
      - CUA configured with 30s timeout (artificially low)
    steps:
      - action: "DM Jamie: 'https://youtube.com/watch?v=test'"
      - wait: 45s  # Exceed timeout
      - action: "Check response"
        expect:
          - message_contains: "timed out" OR message_contains: "went wrong"
      - action: "DM Jamie: status"
        expect:
          - is_busy: false  # System recovered
```

---

## 9. Performance Considerations

### 9.1 Latency Targets

| Operation | Target | Maximum | Measurement Point |
|-----------|--------|---------|-------------------|
| **DM Acknowledgment** | < 2s | 5s | User sends DM → "Got it!" reply |
| **Stream Start** | < 45s | 60s | Request accepted → stream visible |
| **Stop Command** | < 5s | 10s | User sends "stop" → stream ends |
| **Health Check** | < 100ms | 500ms | HTTP request → response |
| **Webhook Delivery** | < 1s | 5s | Status change → callback received |

### 9.2 Resource Limits

```yaml
# Resource limits for containers

jamie-bot:
  cpu: "0.5"       # Half a CPU core
  memory: "256Mi"  # 256 MB RAM
  # Lightweight: just handles Discord gateway + HTTP

cua-controller:
  cpu: "1.0"       # One CPU core
  memory: "512Mi"  # 512 MB RAM
  # Manages sandbox lifecycle, HTTP API

cua-sandbox (per instance):
  cpu: "2.0"       # Two CPU cores
  memory: "4Gi"    # 4 GB RAM
  # Runs Firefox, XFCE, streaming workload
  # This is the heavy component

# Anthropic API budget per session
anthropic:
  max_tokens_input: 50000   # ~50k tokens per session
  max_tokens_output: 10000  # ~10k tokens per session
  max_cost_usd: 2.00        # Hard limit per session
  max_iterations: 50        # Agent loop limit
```

### 9.3 Scaling Approach

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           SCALING STRATEGY                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  MVP: Single-Session Architecture                                            │
│  ─────────────────────────────────                                           │
│                                                                              │
│  ┌─────────────┐     ┌────────────────┐     ┌─────────────────┐             │
│  │  jamie-bot  │────►│ cua-controller │────►│  cua-sandbox    │             │
│  └─────────────┘     └────────────────┘     └─────────────────┘             │
│                                                                              │
│  • One stream at a time                                                      │
│  • Reject concurrent requests with ERR_BUSY                                  │
│  • Simple, predictable resource usage                                        │
│                                                                              │
│  ─────────────────────────────────────────────────────────────────────────   │
│                                                                              │
│  v1.1: Queue-Based Multi-Session                                             │
│  ────────────────────────────────                                            │
│                                                                              │
│  ┌─────────────┐     ┌────────────────┐                                     │
│  │  jamie-bot  │────►│   Task Queue   │                                     │
│  └─────────────┘     │   (Redis)      │                                     │
│                      └───────┬────────┘                                     │
│                              │                                               │
│            ┌─────────────────┼─────────────────┐                            │
│            ▼                 ▼                 ▼                            │
│  ┌────────────────┐ ┌────────────────┐ ┌────────────────┐                   │
│  │ cua-controller │ │ cua-controller │ │ cua-controller │                   │
│  │    (worker)    │ │    (worker)    │ │    (worker)    │                   │
│  └───────┬────────┘ └───────┬────────┘ └───────┬────────┘                   │
│          │                  │                  │                            │
│          ▼                  ▼                  ▼                            │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐                      │
│  │ cua-sandbox │    │ cua-sandbox │    │ cua-sandbox │                      │
│  └─────────────┘    └─────────────┘    └─────────────┘                      │
│                                                                              │
│  • Multiple concurrent streams (N workers)                                   │
│  • Each worker handles one stream                                            │
│  • Requires N Discord streaming accounts                                     │
│  • Horizontal scaling: add more workers                                      │
│                                                                              │
│  ─────────────────────────────────────────────────────────────────────────   │
│                                                                              │
│  Resource Calculation (per stream):                                          │
│  ──────────────────────────────────                                          │
│                                                                              │
│  • CPU: 2 cores (sandbox) + 0.5 cores (controller) = 2.5 cores               │
│  • RAM: 4 GB (sandbox) + 0.5 GB (controller) = 4.5 GB                        │
│  • Anthropic cost: ~$0.10-0.50 per stream (setup)                            │
│                                                                              │
│  For 3 concurrent streams:                                                   │
│  • 8+ CPU cores                                                              │
│  • 16+ GB RAM                                                                │
│  • 3 Discord accounts                                                        │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## 10. Implementation Notes

### 10.1 Critical Code Patterns

#### 10.1.1 Async Context Management

```python
# Always use async context managers for Computer instances
async with Computer(...) as computer:
    # Computer is running and connected
    agent = ComputerAgent(model="...", tools=[computer])
    # Use agent...
# Computer automatically cleaned up

# DON'T do this:
computer = Computer(...)
await computer.run()
# ... if exception happens, computer may not be cleaned up!
```

#### 10.1.2 Discord Intents Setup

```python
# Intents MUST be set before client initialization
intents = discord.Intents.default()
intents.message_content = True  # PRIVILEGED - enable in Developer Portal!
intents.dm_messages = True
intents.guilds = True
intents.voice_states = True
intents.members = True  # PRIVILEGED - enable in Developer Portal!

# Create client WITH intents
client = discord.Client(intents=intents)

# NOT like this (too late):
client = discord.Client()
client.intents.message_content = True  # Won't work!
```

#### 10.1.3 Agent Task Execution

```python
# Use task-specific prompts, not open-ended instructions
# GOOD:
await agent.run(
    "Click the button labeled 'Share Your Screen' in the voice controls area. "
    "Wait for the sharing picker to appear."
)

# BAD:
await agent.run("Share your screen with Discord")
# Too vague - agent may try multiple approaches

# Always set iteration limits
async for result in agent.run(task):
    iteration += 1
    if iteration > MAX_ITERATIONS:
        raise AgentError("Max iterations exceeded")
```

#### 10.1.4 Webhook Reliability

```python
# Webhooks should be fire-and-forget with retry
async def send_webhook(url: str, payload: dict, max_retries: int = 3):
    """Send webhook with exponential backoff."""
    for attempt in range(max_retries):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, timeout=5) as resp:
                    if resp.status < 400:
                        return True
        except Exception:
            pass
        
        if attempt < max_retries - 1:
            await asyncio.sleep(2 ** attempt)
    
    return False  # Don't raise - webhook failure shouldn't crash stream
```

### 10.2 Known Gotchas

| Issue | Description | Mitigation |
|-------|-------------|------------|
| **Discord 2FA** | CUA can't handle 2FA prompts | Use account without 2FA |
| **CAPTCHA** | Discord may show CAPTCHA after multiple logins | Use persistent Firefox profile |
| **Screen Picker** | Browser's tab picker UI varies by browser | Use Firefox, test specific version |
| **Audio Routing** | Tab share audio requires specific Discord settings | Verify "Also share tab audio" is checked |
| **High Resolution** | Resolutions > 1024x768 reduce VLM accuracy | Stick with XGA resolution |
| **Rate Limits** | Discord gateway rate limits at 120 req/min | Implement backoff in bot |
| **Profile Corruption** | Firefox profile can become corrupted | Add profile reset mechanism |
| **Docker Socket** | Docker-in-Docker requires socket mount | Use `--privileged` or socket access |
| **Timezone** | Agent may click wrong time-based elements | Set consistent TZ in container |

### 10.3 Library Recommendations

| Purpose | Library | Version | Notes |
|---------|---------|---------|-------|
| **Discord Bot** | discord.py | 2.4+ | Use `py-cord` as alternative |
| **HTTP Client** | aiohttp | 3.9+ | Async, connection pooling |
| **HTTP Server** | FastAPI | 0.110+ | Pydantic v2 compatible |
| **ASGI Server** | uvicorn | 0.27+ | With `--workers` for prod |
| **Data Validation** | pydantic | 2.5+ | Type-safe models |
| **Settings** | pydantic-settings | 2.1+ | Env var loading |
| **Logging** | structlog | 24.1+ | JSON structured logs |
| **CUA SDK** | cua-computer | latest | Pin version after testing |
| **CUA Agent** | cua-agent | latest | Pin version after testing |
| **Testing** | pytest | 8.0+ | With `pytest-asyncio` |
| **Test HTTP** | aiohttp-pytest | 1.0+ | Mock HTTP servers |
| **Mocking** | pytest-mock | 3.12+ | Fixture-based mocking |

---

## Appendix A: File Structure

```
jamie/
├── bot/
│   ├── __init__.py
│   ├── main.py              # JamieBot class, SessionManager, CUAClient
│   ├── handlers.py          # MessageHandler, event handling
│   └── webhook.py           # FastAPI webhook receiver
│
├── agent/
│   ├── __init__.py
│   ├── controller.py        # FastAPI CUA Controller API
│   ├── streamer.py          # StreamingAgent class
│   ├── actions.py           # Discord automation prompts
│   └── sandbox.py           # Computer configuration
│
├── shared/
│   ├── __init__.py
│   ├── models.py            # Pydantic models (request/response)
│   ├── schemas.py           # Data schemas (Session, etc.)
│   ├── errors.py            # Error taxonomy
│   ├── recovery.py          # Retry logic
│   └── logging.py           # Logging configuration
│
├── config/
│   ├── __init__.py
│   ├── settings.py          # Pydantic settings
│   └── credentials.py       # Credential management
│
├── tests/
│   ├── unit/
│   │   ├── test_session_manager.py
│   │   ├── test_url_extraction.py
│   │   └── test_error_handling.py
│   ├── integration/
│   │   └── test_jamie_cua_integration.py
│   └── e2e/
│       └── scenarios.yaml
│
├── docker/
│   ├── docker-compose.yml
│   ├── Dockerfile.bot
│   └── Dockerfile.agent
│
├── docs/
│   ├── PRODUCT_SPEC.md
│   ├── ARCHITECTURE.md
│   ├── TECHNICAL_SPEC.md    # This document
│   ├── discord-py-api.md
│   ├── cua-framework.md
│   └── anthropic-computer-use.md
│
├── requirements-bot.txt
├── requirements-agent.txt
├── .env.example
├── pyproject.toml
└── README.md
```

---

## Appendix B: Quick Start Commands

```bash
# Development setup
git clone <repo>
cd jamie
python -m venv venv
source venv/bin/activate
pip install -r requirements-bot.txt
pip install -r requirements-agent.txt

# Copy and configure environment
cp .env.example .env
# Edit .env with your credentials

# Pull CUA sandbox image
docker pull --platform=linux/amd64 trycua/cua-xfce:latest

# Run locally (separate terminals)
# Terminal 1: CUA Controller
uvicorn jamie.agent.controller:app --host 0.0.0.0 --port 8000

# Terminal 2: Jamie Bot
python -m jamie.bot.main

# Production: Docker Compose
docker-compose up -d
docker-compose logs -f

# Testing
pytest tests/unit -v
pytest tests/integration -v
```

---

## Document History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-02-07 | Technical Writing Team | Initial specification |

---

*This document is the technical source of truth for Jamie implementation. Engineers should use this document to begin implementation. Update this document as the system evolves.*
