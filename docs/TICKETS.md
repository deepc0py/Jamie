# Jamie Implementation Tickets

> **Generated:** 2026-02-07  
> **Source:** TECHNICAL_SPEC.md, PRODUCT_SPEC.md, ARCHITECTURE.md  
> **Status:** Ready for Implementation

---

## Table of Contents

1. [Epic Overview](#epic-overview)
2. [E1: Project Setup & Infrastructure](#e1-project-setup--infrastructure)
3. [E2: Jamie Bot (discord.py)](#e2-jamie-bot-discordpy)
4. [E3: CUA Agent](#e3-cua-agent)
5. [E4: Communication Layer](#e4-communication-layer)
6. [E5: Integration & Testing](#e5-integration--testing)
7. [E6: Documentation & Polish](#e6-documentation--polish)
8. [Dependency Graph](#dependency-graph)
9. [MVP Milestone](#mvp-milestone)

---

## Epic Overview

| Epic | Description | Tickets | MVP? |
|------|-------------|---------|------|
| **E1** | Project Setup & Infrastructure | 6 tasks | ✅ |
| **E2** | Jamie Bot (discord.py) | 8 tasks | ✅ |
| **E3** | CUA Agent | 7 tasks | ✅ |
| **E4** | Communication Layer | 5 tasks | ✅ |
| **E5** | Integration & Testing | 6 tasks | ✅ |
| **E6** | Documentation & Polish | 4 tasks | Partial |

---

## E1: Project Setup & Infrastructure

### [E1-T1] Initialize Project Repository Structure

**Priority:** P0  
**Type:** task  
**Estimate:** S (1 hour)  
**Dependencies:** None

#### Description
Create the base project structure following the architecture doc. Set up Python packaging, directory layout, and initial configuration files.

#### Acceptance Criteria
- [ ] Directory structure matches architecture: `jamie/{bot,agent,shared,config}/`
- [ ] `pyproject.toml` configured with project metadata
- [ ] `.gitignore` includes Python, Docker, and IDE patterns
- [ ] Empty `__init__.py` files in all packages
- [ ] README.md with basic project description

#### Technical Context
From ARCHITECTURE.md file structure:
```
jamie/
├── bot/
├── agent/
├── shared/
├── config/
├── docker/
└── docs/
```

#### Files to Create/Modify
- `jamie/pyproject.toml` — Project metadata and dependencies
- `jamie/.gitignore` — Git ignore patterns
- `jamie/README.md` — Project README
- `jamie/bot/__init__.py` — Bot package init
- `jamie/agent/__init__.py` — Agent package init
- `jamie/shared/__init__.py` — Shared models package init
- `jamie/config/__init__.py` — Config package init

#### Testing Requirements
- `cd jamie && python -c "import bot; import agent; import shared; import config"` succeeds

---

### [E1-T2] Configure Bot Dependencies

**Priority:** P0  
**Type:** task  
**Estimate:** XS (30 min)  
**Dependencies:** E1-T1

#### Description
Set up the Jamie Bot's Python dependencies. Create virtual environment configuration and requirements.

#### Acceptance Criteria
- [ ] `requirements-bot.txt` with pinned versions
- [ ] discord.py >= 2.4 specified
- [ ] aiohttp >= 3.9 for HTTP client
- [ ] pydantic >= 2.5 for data validation
- [ ] structlog >= 24.1 for logging
- [ ] python-dotenv for environment variables

#### Technical Context
From Technical Spec Section 1.3 Technology Stack:
- Python 3.12+
- discord.py 2.4+
- aiohttp 3.9+
- pydantic 2.5+
- structlog 24.1+

#### Files to Create/Modify
- `jamie/requirements-bot.txt` — Bot dependencies
- `jamie/pyproject.toml` — Add optional [bot] dependencies group

#### Testing Requirements
- `pip install -r requirements-bot.txt` succeeds
- `python -c "import discord; import aiohttp; import pydantic"` succeeds

---

### [E1-T3] Configure Agent Dependencies

**Priority:** P0  
**Type:** task  
**Estimate:** XS (30 min)  
**Dependencies:** E1-T1

#### Description
Set up the CUA Agent's Python dependencies. Note: CUA requires Python 3.12 or 3.13.

#### Acceptance Criteria
- [ ] `requirements-agent.txt` with pinned versions
- [ ] cua-computer (latest) specified
- [ ] cua-agent (latest) specified
- [ ] fastapi >= 0.110 for HTTP API
- [ ] uvicorn >= 0.27 for ASGI server
- [ ] pydantic >= 2.5 for data validation
- [ ] structlog >= 24.1 for logging

#### Technical Context
From Technical Spec Section 1.3:
- Python 3.12/3.13 (CUA requirement)
- FastAPI 0.110+
- uvicorn 0.27+
- cua-computer, cua-agent (latest)

#### Files to Create/Modify
- `jamie/requirements-agent.txt` — Agent dependencies
- `jamie/pyproject.toml` — Add optional [agent] dependencies group

#### Testing Requirements
- `pip install -r requirements-agent.txt` succeeds
- `python -c "from computer import Computer; from agent import ComputerAgent"` succeeds

---

### [E1-T4] Create Docker Compose Configuration

**Priority:** P0  
**Type:** task  
**Estimate:** S (1 hour)  
**Dependencies:** E1-T1

#### Description
Create Docker Compose configuration for the CUA sandbox environment. The sandbox uses `trycua/cua-xfce:latest` for the Linux desktop.

#### Acceptance Criteria
- [ ] `docker-compose.yml` defines cua-sandbox service
- [ ] Uses `trycua/cua-xfce:latest` image (linux/amd64)
- [ ] Display set to 1024x768 (XGA for VLM accuracy)
- [ ] Memory limit 4GB, CPU limit 2 cores
- [ ] Exposes necessary ports for VNC (optional) and API
- [ ] Volume mount for browser profile persistence
- [ ] Environment variables for credentials passed through

#### Technical Context
From Technical Spec Section 2.2.1:
```python
Computer(
    os_type="linux",
    provider_type="docker",
    image="trycua/cua-xfce:latest",
    display="1024x768",
    memory="4GB",
    cpu="2",
    timeout=300,
    ephemeral=False,  # Persist browser profile
)
```

#### Files to Create/Modify
- `jamie/docker/docker-compose.yml` — Docker Compose configuration
- `jamie/docker/.env.example` — Example environment variables

#### Testing Requirements
- `docker compose config` validates successfully
- `docker compose pull` downloads the image

---

### [E1-T5] Create Environment Configuration Module

**Priority:** P0  
**Type:** task  
**Estimate:** S (1 hour)  
**Dependencies:** E1-T1, E1-T2, E1-T3

#### Description
Create configuration management module for loading settings from environment variables. Handle both bot and agent configurations.

#### Acceptance Criteria
- [ ] `config/settings.py` with Pydantic Settings classes
- [ ] `BotSettings` class for Discord bot configuration
- [ ] `AgentSettings` class for CUA agent configuration
- [ ] `CUAEndpointSettings` for HTTP API configuration
- [ ] `.env.example` with all required variables documented
- [ ] Validation for required fields (fail fast if missing)
- [ ] Sensible defaults for optional fields

#### Technical Context
Required environment variables from ARCHITECTURE.md:
```bash
DISCORD_BOT_TOKEN=
DISCORD_EMAIL=
DISCORD_PASSWORD=
ANTHROPIC_API_KEY=
JAMIE_CUA_ENDPOINT=http://localhost:8000
```

#### Files to Create/Modify
- `jamie/config/settings.py` — Settings management
- `jamie/.env.example` — Environment template

#### Testing Requirements
- Settings load from `.env` file
- Missing required field raises clear error
- `python -c "from config.settings import BotSettings"` succeeds

---

### [E1-T6] Set Up Structured Logging

**Priority:** P1  
**Type:** task  
**Estimate:** S (1 hour)  
**Dependencies:** E1-T2, E1-T3

#### Description
Configure structlog for consistent JSON logging across both bot and agent components. Include correlation IDs for tracing requests.

#### Acceptance Criteria
- [ ] `shared/logging.py` with logging configuration
- [ ] JSON output format for production
- [ ] Console-friendly format for development
- [ ] Request correlation ID support (session_id)
- [ ] Log level configurable via environment
- [ ] Timestamp in ISO8601 format

#### Technical Context
From Technical Spec NFR-15: "All components must log to stdout with structured JSON"

Example log structure:
```json
{
  "timestamp": "2026-02-07T12:34:56Z",
  "level": "info",
  "event": "stream_started",
  "session_id": "550e8400-...",
  "channel_name": "Movie Night"
}
```

#### Files to Create/Modify
- `jamie/shared/logging.py` — Logging configuration
- `jamie/shared/__init__.py` — Export logging setup

#### Testing Requirements
- Logs output as valid JSON
- session_id appears in all related log entries

---

## E2: Jamie Bot (discord.py)

### [E2-T1] Create Stream Status Enum and Session Model

**Priority:** P0  
**Type:** task  
**Estimate:** S (1 hour)  
**Dependencies:** E1-T1, E1-T2

#### Description
Define the core data models for streaming sessions. These models track the lifecycle of a stream request.

#### Acceptance Criteria
- [ ] `StreamStatus` enum with states: PENDING, STARTING, STREAMING, STOPPING, ENDED, FAILED
- [ ] `StreamSession` dataclass with all required fields
- [ ] Fields include: session_id, requester_id, guild_id, channel_id, channel_name, guild_name, url, status, created_at, error_message
- [ ] Type hints for all fields
- [ ] Default values for optional fields

#### Technical Context
From Technical Spec Section 2.1.1:
```python
class StreamStatus(Enum):
    PENDING = "pending"
    STARTING = "starting"
    STREAMING = "streaming"
    STOPPING = "stopping"
    ENDED = "ended"
    FAILED = "failed"

@dataclass
class StreamSession:
    session_id: str
    requester_id: int
    guild_id: int
    channel_id: int
    channel_name: str
    guild_name: str
    url: str
    status: StreamStatus = StreamStatus.PENDING
    created_at: float = field(default_factory=...)
    error_message: Optional[str] = None
```

#### Files to Create/Modify
- `jamie/bot/models.py` — Session models and enums

#### Testing Requirements
- Can instantiate StreamSession with required fields
- Status transitions work correctly
- JSON serialization works for logging

---

### [E2-T2] Implement Session Manager

**Priority:** P0  
**Type:** task  
**Estimate:** M (2 hours)  
**Dependencies:** E2-T1

#### Description
Create the SessionManager class that tracks active streaming sessions. For MVP, this supports a single concurrent session (in-memory).

#### Acceptance Criteria
- [ ] `SessionManager` class with async-safe operations
- [ ] `is_busy` property returns True if session active
- [ ] `current_session` property returns active session or None
- [ ] `create_session()` method with mutex lock
- [ ] `update_status()` method for state transitions
- [ ] `end_session()` method to clear session
- [ ] Returns False if trying to create session when busy

#### Technical Context
From Technical Spec Section 2.1.1:
```python
class SessionManager:
    def __init__(self):
        self._current_session: Optional[StreamSession] = None
        self._lock = asyncio.Lock()
    
    @property
    def is_busy(self) -> bool: ...
    async def create_session(self, session: StreamSession) -> bool: ...
    async def update_status(self, session_id: str, status: StreamStatus, error: Optional[str] = None) -> bool: ...
    async def end_session(self, session_id: str) -> None: ...
```

State transition diagram:
```
PENDING → STARTING → STREAMING → STOPPING → ENDED
    ↓         ↓           ↓
  FAILED    FAILED      FAILED
```

#### Files to Create/Modify
- `jamie/bot/session.py` — SessionManager implementation

#### Testing Requirements
- Cannot create session when already busy
- Status transitions are atomic (thread-safe)
- end_session clears the session correctly

---

### [E2-T3] Implement CUA HTTP Client

**Priority:** P0  
**Type:** task  
**Estimate:** M (2 hours)  
**Dependencies:** E1-T5, E4-T1

#### Description
Create the HTTP client for communicating with the CUA Controller. Handles starting streams, stopping streams, and health checks.

#### Acceptance Criteria
- [ ] `CUAClient` class with configurable base URL and timeout
- [ ] `start_stream()` method sends POST /stream
- [ ] `stop_stream()` method sends POST /stop/{session_id}
- [ ] `health_check()` method sends GET /health
- [ ] Proper error handling with `CUAError` exception
- [ ] Connection pooling with aiohttp.ClientSession
- [ ] Graceful cleanup in `close()` method

#### Technical Context
From Technical Spec Section 2.1.1:
```python
class CUAClient:
    def __init__(self, base_url: str, timeout: float = 30.0): ...
    async def start_stream(self, request: StreamRequest) -> StreamResponse: ...
    async def stop_stream(self, session_id: str) -> None: ...
    async def health_check(self) -> bool: ...
    async def close(self) -> None: ...
```

API endpoints:
- POST /stream — Start a stream
- POST /stop/{session_id} — Stop a stream
- GET /health — Health check

#### Files to Create/Modify
- `jamie/bot/cua_client.py` — CUA HTTP client

#### Testing Requirements
- Mock server tests for each endpoint
- Timeout handling works correctly
- Connection reuse (session not recreated each call)

---

### [E2-T4] Implement URL Pattern Matching

**Priority:** P0  
**Type:** task  
**Estimate:** S (1 hour)  
**Dependencies:** E1-T1

#### Description
Create URL extraction logic that identifies supported streaming URLs from message content. Support YouTube, Twitch, Vimeo, and general HTTP(S) URLs.

#### Acceptance Criteria
- [ ] Regex patterns for YouTube (youtube.com, youtu.be)
- [ ] Regex patterns for Twitch (twitch.tv)
- [ ] Regex patterns for Vimeo (vimeo.com)
- [ ] Fallback pattern for general HTTP/HTTPS URLs
- [ ] `extract_url()` function returns first match or None
- [ ] Patterns compiled once for performance
- [ ] Unit tests for each platform

#### Technical Context
From Technical Spec Section 2.1.1:
```python
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
```

#### Files to Create/Modify
- `jamie/bot/url_parser.py` — URL pattern matching

#### Testing Requirements
- YouTube URLs: `youtube.com/watch?v=abc`, `youtu.be/abc`
- Twitch URLs: `twitch.tv/streamer`
- Vimeo URLs: `vimeo.com/123456`
- General URLs: `https://example.com/page`
- Non-URL text returns None

---

### [E2-T5] Implement Voice Channel Detection

**Priority:** P0  
**Type:** task  
**Estimate:** M (2 hours)  
**Dependencies:** E2-T6

#### Description
Create logic to find a user's current voice channel across all guilds the bot shares with them. This is critical for auto-detecting where to stream.

#### Acceptance Criteria
- [ ] `find_user_voice_channel()` function
- [ ] Iterates through all guilds bot is in
- [ ] Gets member object for user in each guild
- [ ] Checks member.voice.channel for voice state
- [ ] Returns first voice channel found, or None
- [ ] Handles case where user is in multiple channels (returns first)
- [ ] Logs which guild/channel found for debugging

#### Technical Context
From ARCHITECTURE.md:
```python
async def find_user_voice_channel(user: discord.User) -> Optional[discord.VoiceChannel]:
    """Find user's current voice channel across shared guilds."""
    for guild in client.guilds:
        member = guild.get_member(user.id)
        if member and member.voice and member.voice.channel:
            return member.voice.channel
    return None
```

Required intents:
- `intents.guilds = True`
- `intents.voice_states = True`
- `intents.members = True`

#### Files to Create/Modify
- `jamie/bot/voice.py` — Voice channel detection

#### Testing Requirements
- Returns channel when user is in voice
- Returns None when user is not in voice
- Works across multiple guilds

---

### [E2-T6] Create JamieBot Class

**Priority:** P0  
**Type:** task  
**Estimate:** M (2 hours)  
**Dependencies:** E2-T1, E2-T2, E2-T3

#### Description
Create the main JamieBot class that extends discord.py's Bot. Configure intents and set up component initialization.

#### Acceptance Criteria
- [ ] `JamieBot` class extends `commands.Bot`
- [ ] Required intents configured (message_content, dm_messages, guilds, voice_states, members)
- [ ] SessionManager initialized on bot creation
- [ ] CUAClient initialized with endpoint from config
- [ ] `setup_hook()` verifies CUA Controller is reachable
- [ ] `close()` cleans up CUA client
- [ ] Command prefix set (not used for DM but required by discord.py)

#### Technical Context
From Technical Spec Section 2.1.1:
```python
class JamieBot(commands.Bot):
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
        if not await self.cua_client.health_check():
            raise RuntimeError("CUA Controller not reachable")
```

#### Files to Create/Modify
- `jamie/bot/main.py` — JamieBot class
- `jamie/bot/__init__.py` — Export JamieBot

#### Testing Requirements
- Bot initializes with correct intents
- setup_hook fails if CUA Controller unreachable
- Cleanup runs on close

---

### [E2-T7] Implement DM Message Handler

**Priority:** P0  
**Type:** task  
**Estimate:** L (3 hours)  
**Dependencies:** E2-T4, E2-T5, E2-T6

#### Description
Create the message handler for DM interactions. Route messages to appropriate handlers (URL, stop, status, help).

#### Acceptance Criteria
- [ ] `MessageHandler` class registered with bot
- [ ] Ignores messages from self
- [ ] Only processes DM messages (not guild messages)
- [ ] Routes "stop" to stop handler
- [ ] Routes "status" to status handler
- [ ] Routes "help" to help handler
- [ ] Attempts URL extraction for other messages
- [ ] Sends help message if no URL found
- [ ] `_handle_stream_request()` for URL messages

#### Technical Context
From Technical Spec Section 2.1.2:
```python
async def _handle_dm(self, message: discord.Message) -> None:
    content = message.content.strip().lower()
    
    if content == "stop":
        await self._handle_stop(message)
        return
    
    if content == "status":
        await self._handle_status(message)
        return
    
    if content == "help":
        await self._handle_help(message)
        return
    
    url = self._extract_url(message.content)
    if url:
        await self._handle_stream_request(message, url)
    else:
        await message.channel.send("👋 Send me a YouTube, Twitch, or Vimeo URL...")
```

#### Files to Create/Modify
- `jamie/bot/handlers.py` — Message handlers

#### Testing Requirements
- DM with URL triggers stream request
- DM "stop" triggers stop handler
- DM "help" shows help message
- Non-DM messages ignored

---

### [E2-T8] Implement Stream Request Handler

**Priority:** P0  
**Type:** task  
**Estimate:** L (3 hours)  
**Dependencies:** E2-T7

#### Description
Implement the core stream request flow: check busy status, find voice channel, create session, send to CUA, handle response.

#### Acceptance Criteria
- [ ] Check if already streaming → reply with busy message
- [ ] Find user's voice channel → reply if not found
- [ ] Generate UUID session ID
- [ ] Create StreamSession object
- [ ] Register session with SessionManager
- [ ] Send acknowledgment message to user
- [ ] Call CUA client to start stream
- [ ] Handle CUA errors gracefully
- [ ] Update session status based on response

#### Technical Context
From Technical Spec Section 2.1.2:
```python
async def _handle_stream_request(self, message: discord.Message, url: str) -> None:
    user = message.author
    
    if self.bot.session_manager.is_busy:
        await message.channel.send(f"⏳ I'm already streaming...")
        return
    
    voice_channel = await self._find_user_voice_channel(user)
    if not voice_channel:
        await message.channel.send("❌ You're not in any voice channel...")
        return
    
    session_id = str(uuid.uuid4())
    session = StreamSession(...)
    
    await self.bot.session_manager.create_session(session)
    
    await message.channel.send(f"🎬 Got it! Streaming to **{voice_channel.name}**...")
    
    try:
        await self.bot.cua_client.start_stream(StreamRequest(...))
    except CUAError as e:
        await self.bot.session_manager.update_status(session_id, StreamStatus.FAILED, str(e))
        await message.channel.send(f"❌ Failed to start stream: {e}")
```

Bot response messages:
- Busy: "⏳ I'm already streaming to **{channel}** on **{server}**..."
- Not in voice: "❌ You're not in any voice channel I can see..."
- Acknowledged: "🎬 Got it! Streaming to **{channel}** on **{server}**..."
- Error: "❌ Failed to start stream: {error}"

#### Files to Create/Modify
- `jamie/bot/handlers.py` — Add stream request handler

#### Testing Requirements
- Cannot start stream when busy
- Cannot start stream when not in voice
- Successful request sends acknowledgment
- CUA errors handled gracefully

---

## E3: CUA Agent

### [E3-T1] Create Shared API Models

**Priority:** P0  
**Type:** task  
**Estimate:** M (2 hours)  
**Dependencies:** E1-T1

#### Description
Define Pydantic models for API communication between Jamie Bot and CUA Controller. These are shared contracts.

#### Acceptance Criteria
- [ ] `StreamRequest` model with all fields
- [ ] `StreamResponse` model with status enum
- [ ] `StatusUpdate` model for webhooks
- [ ] `StopRequest` model
- [ ] `HealthResponse` model
- [ ] All models have JSON schema examples
- [ ] Proper validation (HttpUrl, positive integers, etc.)

#### Technical Context
From Technical Spec Section 2.3.1:
```python
class StreamRequest(BaseModel):
    session_id: str
    url: str
    guild_id: int
    channel_id: int
    channel_name: str
    webhook_url: Optional[str] = None

class StreamResponse(BaseModel):
    session_id: str
    status: StreamRequestStatus  # accepted, rejected, in_progress
    message: Optional[str] = None
    estimated_start_time: Optional[float] = None

class StatusUpdate(BaseModel):
    session_id: str
    status: str  # starting, streaming, error, ended
    message: Optional[str] = None
    error_code: Optional[str] = None
    timestamp: datetime
```

#### Files to Create/Modify
- `jamie/shared/models.py` — API models

#### Testing Requirements
- Models serialize to JSON correctly
- Validation rejects invalid data
- Optional fields work as expected

---

### [E3-T2] Create Agent State Enum and Config

**Priority:** P0  
**Type:** task  
**Estimate:** S (1 hour)  
**Dependencies:** E1-T3

#### Description
Define agent lifecycle states and configuration dataclass for the streaming agent.

#### Acceptance Criteria
- [ ] `AgentState` enum with states: INITIALIZING, LOGGING_IN, JOINING_CHANNEL, OPENING_URL, SHARING_SCREEN, STREAMING, STOPPING, TERMINATED, ERROR
- [ ] `AgentConfig` dataclass with all config options
- [ ] Fields: discord_email, discord_password, model, max_budget, max_iterations, screenshot_interval
- [ ] Sensible defaults (model=sonnet-4-5, budget=$2, iterations=50)

#### Technical Context
From Technical Spec Section 2.2.2:
```python
class AgentState(Enum):
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
    discord_email: str
    discord_password: str
    model: str = "anthropic/claude-sonnet-4-5-20250929"
    max_budget: float = 2.0
    max_iterations: int = 50
    screenshot_interval: float = 2.0
```

#### Files to Create/Modify
- `jamie/agent/models.py` — Agent state and config

#### Testing Requirements
- AgentConfig validates required fields
- Defaults are applied correctly

---

### [E3-T3] Implement Sandbox Creation

**Priority:** P0  
**Type:** task  
**Estimate:** M (2 hours)  
**Dependencies:** E1-T3, E1-T4

#### Description
Create function to instantiate and configure the CUA Docker sandbox with proper settings for Discord streaming.

#### Acceptance Criteria
- [ ] `create_sandbox()` function returns configured Computer
- [ ] Uses trycua/cua-xfce:latest image
- [ ] Display set to 1024x768 (XGA)
- [ ] Memory 4GB, CPU 2 cores
- [ ] Timeout 300 seconds (5 minutes)
- [ ] ephemeral=False for browser profile persistence
- [ ] Firefox setup script for streaming permissions

#### Technical Context
From Technical Spec Section 2.2.1:
```python
def create_sandbox() -> Computer:
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

SETUP_SCRIPT = """
#!/bin/bash
set -e
# Firefox config for auto-play and permissions
cat > /home/user/.mozilla/firefox/jamie.default/user.js << 'EOF'
user_pref("media.autoplay.default", 0);
user_pref("permissions.default.microphone", 1);
...
EOF
"""
```

#### Files to Create/Modify
- `jamie/agent/sandbox.py` — Sandbox creation

#### Testing Requirements
- Computer object created with correct settings
- Setup script is syntactically valid bash

---

### [E3-T4] Define Discord Automation Prompts

**Priority:** P0  
**Type:** task  
**Estimate:** M (2 hours)  
**Dependencies:** None

#### Description
Create the structured prompts for Discord automation tasks. These are templates the agent uses to perform specific actions.

#### Acceptance Criteria
- [ ] `DISCORD_LOGIN_PROMPT` template
- [ ] `JOIN_VOICE_CHANNEL_PROMPT` template
- [ ] `OPEN_URL_PROMPT` template
- [ ] `START_SCREEN_SHARE_PROMPT` template
- [ ] `STOP_SCREEN_SHARE_PROMPT` template
- [ ] `HANDLE_DISCONNECT_PROMPT` for error recovery
- [ ] All prompts use clear, numbered steps
- [ ] Prompts include success/failure signal words

#### Technical Context
From Technical Spec Section 2.2.3:
```python
DISCORD_LOGIN_PROMPT = """
Navigate to Discord Web and log in:

1. Open Firefox browser
2. Go to https://discord.com/login
3. Enter email: {email}
...
8. Report "LOGIN_COMPLETE" when done

IMPORTANT:
- Do NOT click any "Download" buttons
- If you see a captcha, report "CAPTCHA_REQUIRED"
"""

JOIN_VOICE_CHANNEL_PROMPT = """
Join a voice channel in Discord:

1. Look for the server with guild ID {guild_id}...
...
7. Report "JOINED_CHANNEL" when connected
"""
```

#### Files to Create/Modify
- `jamie/agent/prompts.py` — Automation prompts

#### Testing Requirements
- Prompts have all required placeholders
- Format strings work with .format()

---

### [E3-T5] Implement Streaming Agent Class

**Priority:** P0  
**Type:** task  
**Estimate:** XL (4 hours)  
**Dependencies:** E3-T2, E3-T3, E3-T4

#### Description
Create the main StreamingAgent class that orchestrates the full streaming workflow using CUA's ComputerAgent.

#### Acceptance Criteria
- [ ] `StreamingAgent` class with AgentConfig
- [ ] `start_stream()` async generator yields status updates
- [ ] `stop()` method for graceful shutdown
- [ ] Implements full workflow: init → login → join → open → share → monitor
- [ ] Uses CUA's BudgetManagerCallback for cost control
- [ ] Handles agent loop iteration limits
- [ ] Detects completion signals in agent output
- [ ] `_cleanup()` method stops computer on exit

#### Technical Context
From Technical Spec Section 2.2.2:
```python
class StreamingAgent:
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
        # Yields {"state": "...", "message": "..."} at each step
        ...
    
    async def stop(self) -> None:
        self._stop_requested = True
    
    async def _execute_task(self, task: str) -> dict:
        # Run a single task through the agent
        ...
```

#### Files to Create/Modify
- `jamie/agent/streamer.py` — StreamingAgent implementation

#### Testing Requirements
- State transitions in correct order
- Budget limit triggers termination
- Iteration limit triggers termination
- Stop request is honored

---

### [E3-T6] Implement CUA Controller HTTP API

**Priority:** P0  
**Type:** task  
**Estimate:** L (3 hours)  
**Dependencies:** E3-T1, E3-T5

#### Description
Create FastAPI HTTP server that receives streaming tasks from Jamie Bot and manages agent lifecycle.

#### Acceptance Criteria
- [ ] FastAPI app with uvicorn runner
- [ ] `POST /stream` endpoint accepts StreamRequest
- [ ] `POST /stop/{session_id}` endpoint stops stream
- [ ] `GET /health` endpoint returns HealthResponse
- [ ] Spawns StreamingAgent as background task
- [ ] Tracks active session (single session for MVP)
- [ ] Returns 409 Conflict if already streaming
- [ ] Sends webhook callbacks for status updates

#### Technical Context
From Technical Spec Section 2.3:
```http
POST /stream
Content-Type: application/json

{
  "session_id": "...",
  "url": "https://youtube.com/...",
  "guild_id": 123,
  "channel_id": 456,
  "channel_name": "Movie Night",
  "webhook_url": "http://jamie-bot:8080/status"
}

---

200 OK
{
  "session_id": "...",
  "status": "accepted",
  "estimated_start_time": 45.0
}
```

#### Files to Create/Modify
- `jamie/agent/controller.py` — FastAPI controller

#### Testing Requirements
- Health check returns 200 when healthy
- Stream request returns 409 when busy
- Stream request spawns agent task
- Stop request terminates agent

---

### [E3-T7] Implement Webhook Status Reporting

**Priority:** P0  
**Type:** task  
**Estimate:** M (2 hours)  
**Dependencies:** E3-T6

#### Description
Implement webhook callbacks from CUA Controller to Jamie Bot for status updates. The agent emits events, controller sends to webhook.

#### Acceptance Criteria
- [ ] `StatusReporter` class with webhook URL
- [ ] `report()` method sends POST to webhook
- [ ] StatusUpdate model used for payload
- [ ] Retry logic for transient failures (3 retries)
- [ ] Timeout handling (5 second timeout)
- [ ] Non-blocking (fire and forget with logging)
- [ ] Called at each agent state transition

#### Technical Context
From Technical Spec Section 2.3.2:
```http
POST /status HTTP/1.1
Host: jamie-bot:8080
Content-Type: application/json

{
  "session_id": "...",
  "status": "streaming",
  "message": "Screen share active",
  "timestamp": "2026-02-07T12:34:56Z"
}
```

Status values: starting, streaming, error, ended

#### Files to Create/Modify
- `jamie/agent/reporter.py` — Webhook status reporter
- `jamie/agent/controller.py` — Integrate reporter

#### Testing Requirements
- Webhook called on state changes
- Retries on 5xx errors
- Logs failure if webhook unreachable

---

## E4: Communication Layer

### [E4-T1] Define Error Codes

**Priority:** P0  
**Type:** task  
**Estimate:** S (1 hour)  
**Dependencies:** None

#### Description
Create standardized error codes for the system. These codes are used in API responses and status updates.

#### Acceptance Criteria
- [ ] Error code enum or constants
- [ ] All codes from technical spec defined
- [ ] Each code has HTTP status mapping
- [ ] Each code has user-friendly message template
- [ ] Documentation of recovery actions

#### Technical Context
From Technical Spec Section 2.3.3:
```
ERR_BUSY (409) — Another stream is active
ERR_INVALID_URL (400) — URL not parseable
ERR_SANDBOX_FAILED (503) — Docker sandbox won't start
ERR_LOGIN_FAILED (401) — Discord login failed
ERR_2FA_REQUIRED (401) — Account requires 2FA
ERR_CAPTCHA (401) — CAPTCHA required
ERR_CHANNEL_NOT_FOUND (404) — Voice channel not accessible
ERR_SHARE_FAILED (500) — Screen share didn't work
ERR_TIMEOUT (504) — Operation timed out
ERR_BUDGET_EXCEEDED (402) — API cost limit reached
ERR_MAX_ITERATIONS (500) — Agent loop exceeded limit
ERR_UNKNOWN (500) — Unexpected error
```

#### Files to Create/Modify
- `jamie/shared/errors.py` — Error codes and messages

#### Testing Requirements
- All error codes have HTTP status
- All error codes have message template

---

### [E4-T2] Implement Webhook Receiver in Bot

**Priority:** P0  
**Type:** task  
**Estimate:** M (2 hours)  
**Dependencies:** E2-T2, E3-T1

#### Description
Create HTTP endpoint in Jamie Bot to receive status webhooks from CUA Controller. Update session state and notify users.

#### Acceptance Criteria
- [ ] FastAPI or aiohttp server in bot process
- [ ] `POST /status` endpoint receives StatusUpdate
- [ ] Validates session_id matches current session
- [ ] Updates SessionManager with new status
- [ ] Sends DM to requester on status changes
- [ ] Handles "streaming" → send success message
- [ ] Handles "error" → send error message
- [ ] Handles "ended" → send completion message

#### Technical Context
Bot runs webhook receiver alongside Discord client:
```python
# In bot startup
app = FastAPI()

@app.post("/status")
async def receive_status(update: StatusUpdate):
    session = bot.session_manager.current_session
    if session and session.session_id == update.session_id:
        await bot.session_manager.update_status(
            update.session_id, 
            map_status(update.status)
        )
        # Send DM to requester
        user = await bot.fetch_user(session.requester_id)
        await user.send(format_status_message(update))
```

#### Files to Create/Modify
- `jamie/bot/webhook.py` — Webhook receiver
- `jamie/bot/main.py` — Integrate webhook server

#### Testing Requirements
- Webhook updates session state
- User receives DM on streaming start
- User receives DM on error

---

### [E4-T3] Implement Request/Response Validation

**Priority:** P1  
**Type:** task  
**Estimate:** S (1 hour)  
**Dependencies:** E3-T1

#### Description
Add request validation middleware to CUA Controller. Ensure all requests conform to API contracts.

#### Acceptance Criteria
- [ ] FastAPI handles Pydantic validation errors
- [ ] Custom exception handlers for validation errors
- [ ] Return 400 with clear error message on invalid request
- [ ] Log validation failures for debugging
- [ ] Validate URL format in StreamRequest

#### Technical Context
FastAPI automatic validation with custom error responses:
```python
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    return JSONResponse(
        status_code=400,
        content={
            "error": "ERR_INVALID_REQUEST",
            "message": str(exc),
            "details": exc.errors()
        }
    )
```

#### Files to Create/Modify
- `jamie/agent/controller.py` — Add validation handlers

#### Testing Requirements
- Invalid JSON returns 400
- Missing required fields returns 400
- Invalid URL format returns 400

---

### [E4-T4] Add Health Check Endpoints

**Priority:** P1  
**Type:** task  
**Estimate:** S (1 hour)  
**Dependencies:** E2-T6, E3-T6

#### Description
Implement health check endpoints for both bot and controller for monitoring and orchestration.

#### Acceptance Criteria
- [ ] CUA Controller: GET /health returns HealthResponse
- [ ] Includes: status, sandbox_ready, active_sessions, version
- [ ] Bot: health check method/endpoint
- [ ] Health degrades if sandbox not ready
- [ ] Health degrades if session stuck

#### Technical Context
From Technical Spec Section 2.3.1:
```python
class HealthResponse(BaseModel):
    status: Literal["healthy", "degraded", "unhealthy"]
    sandbox_ready: bool
    active_sessions: int
    version: str
```

#### Files to Create/Modify
- `jamie/agent/controller.py` — Health endpoint
- `jamie/shared/models.py` — HealthResponse model

#### Testing Requirements
- Returns healthy when idle
- Returns degraded when sandbox issues
- Returns active_sessions count

---

### [E4-T5] Implement Retry Logic

**Priority:** P1  
**Type:** task  
**Estimate:** M (2 hours)  
**Dependencies:** E2-T3, E3-T7

#### Description
Add retry logic with exponential backoff for HTTP communications between components.

#### Acceptance Criteria
- [ ] CUAClient retries on 5xx errors
- [ ] StatusReporter retries on 5xx errors
- [ ] Exponential backoff: 1s, 2s, 4s
- [ ] Max 3 retries before failing
- [ ] Timeout per request (30s default)
- [ ] Log retry attempts

#### Technical Context
```python
async def _request_with_retry(
    self, 
    method: str, 
    url: str, 
    **kwargs
) -> aiohttp.ClientResponse:
    for attempt in range(3):
        try:
            async with self._session.request(method, url, **kwargs) as resp:
                if resp.status < 500:
                    return resp
                # Retry on 5xx
        except aiohttp.ClientError:
            pass
        
        await asyncio.sleep(2 ** attempt)  # 1, 2, 4
    
    raise CUAError("Max retries exceeded")
```

#### Files to Create/Modify
- `jamie/bot/cua_client.py` — Add retry logic
- `jamie/agent/reporter.py` — Add retry logic
- `jamie/shared/http_utils.py` — Shared retry utilities (optional)

#### Testing Requirements
- Retries on 500 error
- Succeeds after transient failure
- Fails after max retries

---

## E5: Integration & Testing

### [E5-T1] Create Bot Entry Point

**Priority:** P0  
**Type:** task  
**Estimate:** S (1 hour)  
**Dependencies:** E2-T6, E2-T7, E4-T2

#### Description
Create the main entry point script for running the Jamie Bot. Load configuration, initialize bot, and run event loop.

#### Acceptance Criteria
- [ ] `jamie/bot/__main__.py` for `python -m jamie.bot`
- [ ] Loads settings from environment
- [ ] Initializes JamieBot with CUA endpoint
- [ ] Registers MessageHandler
- [ ] Starts webhook server in background
- [ ] Runs bot with token from config
- [ ] Graceful shutdown on SIGINT/SIGTERM

#### Technical Context
```python
# jamie/bot/__main__.py
import asyncio
from .main import JamieBot
from .handlers import MessageHandler
from .webhook import start_webhook_server
from config.settings import BotSettings

async def main():
    settings = BotSettings()
    bot = JamieBot(cua_endpoint=settings.cua_endpoint)
    MessageHandler(bot)
    
    # Start webhook server
    asyncio.create_task(start_webhook_server(bot, port=8080))
    
    await bot.start(settings.discord_token)

if __name__ == "__main__":
    asyncio.run(main())
```

#### Files to Create/Modify
- `jamie/bot/__main__.py` — Entry point

#### Testing Requirements
- Bot starts and connects to Discord
- Webhook server accepts connections
- Graceful shutdown works

---

### [E5-T2] Create Agent Entry Point

**Priority:** P0  
**Type:** task  
**Estimate:** S (1 hour)  
**Dependencies:** E3-T6

#### Description
Create the main entry point script for running the CUA Controller server.

#### Acceptance Criteria
- [ ] `jamie/agent/__main__.py` for `python -m jamie.agent`
- [ ] Loads settings from environment
- [ ] Configures uvicorn with host/port from config
- [ ] Default port 8000
- [ ] Graceful shutdown handling

#### Technical Context
```python
# jamie/agent/__main__.py
import uvicorn
from .controller import app
from config.settings import AgentSettings

if __name__ == "__main__":
    settings = AgentSettings()
    uvicorn.run(
        app,
        host=settings.host,
        port=settings.port,
        log_level="info"
    )
```

#### Files to Create/Modify
- `jamie/agent/__main__.py` — Entry point

#### Testing Requirements
- Server starts on configured port
- Health endpoint responds
- Graceful shutdown works

---

### [E5-T3] Write Unit Tests for Bot Components

**Priority:** P0  
**Type:** task  
**Estimate:** L (3 hours)  
**Dependencies:** E2-T1 through E2-T8

#### Description
Create unit tests for all bot components: URL parsing, session management, voice detection (mocked), handlers.

#### Acceptance Criteria
- [ ] pytest configured with pytest-asyncio
- [ ] Tests for URL pattern matching (all platforms)
- [ ] Tests for SessionManager (all methods)
- [ ] Tests for StreamSession state transitions
- [ ] Tests for CUAClient (mocked responses)
- [ ] Tests for message handler routing
- [ ] Tests for stream request handler logic
- [ ] Coverage target: 80%+

#### Technical Context
Use pytest-asyncio for async tests, aioresponses for mocking HTTP:
```python
@pytest.mark.asyncio
async def test_session_manager_blocks_when_busy():
    manager = SessionManager()
    session1 = StreamSession(session_id="1", ...)
    session2 = StreamSession(session_id="2", ...)
    
    assert await manager.create_session(session1) is True
    assert await manager.create_session(session2) is False
```

#### Files to Create/Modify
- `jamie/tests/__init__.py`
- `jamie/tests/bot/test_url_parser.py`
- `jamie/tests/bot/test_session.py`
- `jamie/tests/bot/test_cua_client.py`
- `jamie/tests/bot/test_handlers.py`
- `jamie/pytest.ini` or pyproject.toml pytest config

#### Testing Requirements
- All tests pass
- No mocked Discord API calls (those are integration tests)

---

### [E5-T4] Write Unit Tests for Agent Components

**Priority:** P0  
**Type:** task  
**Estimate:** L (3 hours)  
**Dependencies:** E3-T1 through E3-T7

#### Description
Create unit tests for agent components: models, controller endpoints, status reporter.

#### Acceptance Criteria
- [ ] Tests for API models (serialization, validation)
- [ ] Tests for controller endpoints (mocked agent)
- [ ] Tests for status reporter (mocked HTTP)
- [ ] Tests for error handling
- [ ] Tests for sandbox configuration
- [ ] Coverage target: 80%+

#### Technical Context
Use FastAPI TestClient for endpoint tests:
```python
from fastapi.testclient import TestClient
from jamie.agent.controller import app

def test_health_check():
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_stream_returns_409_when_busy():
    client = TestClient(app)
    # Start first stream
    client.post("/stream", json={...})
    # Try second stream
    response = client.post("/stream", json={...})
    assert response.status_code == 409
```

#### Files to Create/Modify
- `jamie/tests/agent/test_models.py`
- `jamie/tests/agent/test_controller.py`
- `jamie/tests/agent/test_reporter.py`

#### Testing Requirements
- All tests pass
- CUA agent itself is mocked (no actual sandbox)

---

### [E5-T5] Create End-to-End Integration Test

**Priority:** P0  
**Type:** task  
**Estimate:** XL (4 hours)  
**Dependencies:** E5-T1, E5-T2, E5-T3, E5-T4

#### Description
Create integration test that runs the full flow: DM → bot → controller → agent (mocked) → webhook → bot. Uses real HTTP, mocked Discord and CUA.

#### Acceptance Criteria
- [ ] Test harness starts bot and controller
- [ ] Discord API mocked (DM receive, send)
- [ ] CUA agent mocked (returns success)
- [ ] Full flow completes: request → ack → streaming → stop → ended
- [ ] Webhook communication verified
- [ ] Error flow tested: CUA fails → user gets error DM

#### Technical Context
Integration test flow:
1. Start CUA Controller (real FastAPI, mocked agent)
2. Start Jamie Bot (real discord.py, mocked gateway)
3. Simulate DM with URL
4. Verify acknowledgment sent
5. Verify CUA Controller received request
6. Simulate webhook callback "streaming"
7. Verify user received streaming DM
8. Simulate "stop" DM
9. Verify stop sent to controller
10. Simulate webhook callback "ended"
11. Verify user received ended DM

#### Files to Create/Modify
- `jamie/tests/integration/test_full_flow.py`
- `jamie/tests/integration/conftest.py` — Fixtures

#### Testing Requirements
- Full happy path completes
- Error path completes
- No real external calls (Discord, Anthropic)

---

### [E5-T6] Manual End-to-End Test Script

**Priority:** P0  
**Type:** task  
**Estimate:** M (2 hours)  
**Dependencies:** E5-T1, E5-T2

#### Description
Create a manual test script/checklist for validating the full system with real Discord and real CUA sandbox.

#### Acceptance Criteria
- [ ] `scripts/manual_test.md` checklist
- [ ] Setup instructions (env vars, Docker)
- [ ] Step-by-step test procedure
- [ ] Expected outcomes at each step
- [ ] Troubleshooting section
- [ ] Test YouTube URL streaming
- [ ] Test Twitch URL streaming
- [ ] Test stop command
- [ ] Test error scenarios

#### Technical Context
Checklist items:
```markdown
## Prerequisites
- [ ] Docker running
- [ ] CUA sandbox image pulled
- [ ] Discord bot token configured
- [ ] Discord streaming account configured
- [ ] Anthropic API key configured

## Test Procedure
1. [ ] Start CUA Controller: `python -m jamie.agent`
   - Expected: Server running on port 8000
   - Verify: `curl localhost:8000/health`

2. [ ] Start Jamie Bot: `python -m jamie.bot`
   - Expected: Bot online in Discord

3. [ ] Join a voice channel in test server

4. [ ] DM Jamie: `https://youtube.com/watch?v=dQw4w9WgXcQ`
   - Expected: Acknowledgment within 5 seconds
   - Expected: "Now streaming" within 60 seconds

5. [ ] Verify stream visible in voice channel

6. [ ] DM Jamie: `stop`
   - Expected: "Stream ended" message
```

#### Files to Create/Modify
- `jamie/scripts/manual_test.md`

#### Testing Requirements
- Checklist is complete and accurate
- All expected outcomes documented

---

## E6: Documentation & Polish

### [E6-T1] Create User-Facing Documentation

**Priority:** P1  
**Type:** task  
**Estimate:** M (2 hours)  
**Dependencies:** E5-T6

#### Description
Write documentation for end users on how to use Jamie.

#### Acceptance Criteria
- [ ] `docs/USER_GUIDE.md` with usage instructions
- [ ] How to invite Jamie to a server
- [ ] How to use DM commands
- [ ] Supported platforms (YouTube, Twitch, Vimeo)
- [ ] FAQ section
- [ ] Troubleshooting common issues

#### Technical Context
From Product Spec UX section:
```markdown
## Using Jamie

1. **Join a voice channel** in a server Jamie is in
2. **DM Jamie** with a URL (YouTube, Twitch, Vimeo, or any webpage)
3. **Wait ~30-60 seconds** for the stream to start
4. **Watch together** with everyone in the voice channel
5. **DM "stop"** when you're done

## Commands
- Send a URL — Start streaming that URL
- `stop` — End the current stream
- `status` — Check if Jamie is streaming
- `help` — Show help message
```

#### Files to Create/Modify
- `jamie/docs/USER_GUIDE.md`

#### Testing Requirements
- All commands documented
- Screenshots where helpful

---

### [E6-T2] Create Deployment Guide

**Priority:** P1  
**Type:** task  
**Estimate:** M (2 hours)  
**Dependencies:** E5-T1, E5-T2

#### Description
Write deployment documentation for self-hosting Jamie.

#### Acceptance Criteria
- [ ] `docs/DEPLOYMENT.md` with setup instructions
- [ ] Prerequisites (Python, Docker, Discord app)
- [ ] Environment variable reference
- [ ] Docker Compose deployment instructions
- [ ] Running without Docker (development)
- [ ] Monitoring and logs section
- [ ] Security considerations

#### Technical Context
```markdown
## Prerequisites
- Python 3.12+
- Docker 24.0+
- Discord Bot Application (with token)
- Discord Account for streaming (email/password)
- Anthropic API Key

## Quick Start
1. Clone repository
2. Copy `.env.example` to `.env` and fill in values
3. `docker compose up -d`
4. Invite bot to your Discord server
```

#### Files to Create/Modify
- `jamie/docs/DEPLOYMENT.md`

#### Testing Requirements
- Instructions are complete and accurate
- Fresh deployment works following the guide

---

### [E6-T3] Add Bot Response Polish

**Priority:** P1  
**Type:** task  
**Estimate:** S (1 hour)  
**Dependencies:** E2-T7, E2-T8

#### Description
Polish the bot's response messages for better user experience. Add personality and helpful details.

#### Acceptance Criteria
- [ ] Consistent emoji usage
- [ ] Helpful tips in error messages
- [ ] Progress indicators where appropriate
- [ ] Friendly, conversational tone
- [ ] All error messages include next steps

#### Technical Context
From Product Spec UX section:
```
🎬 Got it! Streaming to **Movie Night** on **Your Server**...
This usually takes 30-60 seconds to set up.

✅ Now streaming! Everyone in the channel should see it.
DM me **stop** when you're done.

⏹️ Stream ended. Thanks for watching!

❌ You're not in any voice channel I can see.
Join a voice channel in a server we share, then try again.
```

#### Files to Create/Modify
- `jamie/bot/messages.py` — Centralized message templates
- `jamie/bot/handlers.py` — Use message templates

#### Testing Requirements
- All user-facing messages reviewed
- Consistent formatting

---

### [E6-T4] Add Metrics and Observability

**Priority:** P2  
**Type:** task  
**Estimate:** L (3 hours)  
**Dependencies:** E5-T1, E5-T2

#### Description
Add Prometheus metrics for monitoring stream success rate, latency, and costs.

#### Acceptance Criteria
- [ ] prometheus-client integrated
- [ ] `streams_total` counter (labels: status)
- [ ] `stream_duration_seconds` histogram
- [ ] `stream_latency_seconds` histogram (time to start)
- [ ] `agent_cost_usd` counter
- [ ] `/metrics` endpoint on controller
- [ ] Basic Grafana dashboard JSON (optional)

#### Technical Context
From Product Spec success metrics:
- Stream Success Rate (> 80%)
- Time to Stream (< 60s)
- Session Duration (> 5 min)
- Cost per Stream (< $1)

```python
from prometheus_client import Counter, Histogram

streams_total = Counter(
    'jamie_streams_total',
    'Total streams',
    ['status']  # success, failed, cancelled
)

stream_duration = Histogram(
    'jamie_stream_duration_seconds',
    'Stream duration in seconds'
)
```

#### Files to Create/Modify
- `jamie/shared/metrics.py` — Metrics definitions
- `jamie/agent/controller.py` — Expose /metrics
- `jamie/agent/streamer.py` — Record metrics

#### Testing Requirements
- Metrics endpoint returns valid Prometheus format
- Counters increment on stream events

---

## Dependency Graph

```
                                E1-T1 (Project Structure)
                                          │
                    ┌─────────────────────┼─────────────────────┐
                    │                     │                     │
                E1-T2 (Bot Deps)     E1-T3 (Agent Deps)    E1-T4 (Docker)
                    │                     │                     │
                    └─────────┬───────────┘                     │
                              │                                 │
                          E1-T5 (Config)                        │
                              │                                 │
                    ┌─────────┴─────────┐                       │
                    │                   │                       │
                E1-T6 (Logging)     E2-T1 (Models)              │
                                        │                       │
                                    E2-T2 (SessionMgr)          │
                                        │                       │
                    ┌───────────────────┼───────────────────────┤
                    │                   │                       │
                E2-T4 (URL)         E2-T6 (JamieBot)       E3-T3 (Sandbox)
                    │                   │                       │
                E2-T5 (Voice)───────────┤                   E3-T4 (Prompts)
                    │                   │                       │
                    └─────────┬─────────┘                       │
                              │                                 │
                          E2-T7 (DM Handler)               E3-T2 (AgentModels)
                              │                                 │
                          E2-T8 (Stream Handler)           E3-T5 (StreamAgent)
                              │                                 │
                              │                            E3-T1 (API Models)
                              │                                 │
                          E2-T3 (CUA Client)───────────────E3-T6 (Controller)
                              │                                 │
                          E4-T2 (Webhook Rx)───────────────E3-T7 (Reporter)
                              │                                 │
                    ┌─────────┴─────────┐                       │
                    │                   │                       │
                E5-T1 (Bot Entry)   E5-T2 (Agent Entry)         │
                    │                   │                       │
                    └─────────┬─────────┘                       │
                              │                                 │
                    ┌─────────┼─────────┐                       │
                    │         │         │                       │
            E5-T3 (Bot Tests) │  E5-T4 (Agent Tests)            │
                    │         │         │                       │
                    └─────────┼─────────┘                       │
                              │                                 │
                          E5-T5 (Integration Test)              │
                              │                                 │
                          E5-T6 (Manual Test)                   │
                              │                                 │
                    ┌─────────┴─────────┐                       │
                    │                   │                       │
            E6-T1 (User Docs)    E6-T2 (Deploy Docs)            │
                                        │                       │
                                E6-T3 (Message Polish)──────────┘
                                        │
                                E6-T4 (Metrics) [P2]
```

---

## MVP Milestone

### Critical Path (Must Complete in Order)

| Order | Ticket | Description | Estimate |
|-------|--------|-------------|----------|
| 1 | E1-T1 | Project structure | S |
| 2 | E1-T2, E1-T3, E1-T4 | Dependencies + Docker (parallel) | S each |
| 3 | E1-T5 | Configuration | S |
| 4 | E3-T1 | Shared API models | M |
| 5 | E4-T1 | Error codes | S |
| 6 | E2-T1 | Bot session models | S |
| 7 | E2-T2 | Session manager | M |
| 8 | E3-T2, E3-T4 | Agent models + prompts (parallel) | S, M |
| 9 | E3-T3 | Sandbox creation | M |
| 10 | E3-T5 | Streaming agent | XL |
| 11 | E3-T6 | CUA Controller | L |
| 12 | E3-T7 | Webhook reporter | M |
| 13 | E2-T3 | CUA HTTP client | M |
| 14 | E2-T4 | URL parsing | S |
| 15 | E2-T6 | JamieBot class | M |
| 16 | E2-T5 | Voice detection | M |
| 17 | E2-T7 | DM handler | L |
| 18 | E2-T8 | Stream request handler | L |
| 19 | E4-T2 | Webhook receiver | M |
| 20 | E5-T1, E5-T2 | Entry points (parallel) | S each |
| 21 | E5-T3, E5-T4 | Unit tests (parallel) | L each |
| 22 | E5-T5 | Integration test | XL |
| 23 | E5-T6 | Manual test script | M |

### MVP Ticket Summary

**Required for MVP (P0):**
- E1: All 6 tasks (E1-T6 is P1 but minimal logging is P0)
- E2: All 8 tasks
- E3: All 7 tasks
- E4: E4-T1, E4-T2 (E4-T3/T4/T5 are P1)
- E5: All 6 tasks

**Total MVP Tickets:** 27 tasks

**Estimated Total Effort:** 
- XS (30m): 2 tasks = 1 hour
- S (1h): 9 tasks = 9 hours
- M (2h): 11 tasks = 22 hours
- L (3h): 6 tasks = 18 hours
- XL (4h): 2 tasks = 8 hours
- **Total: ~58 hours** (roughly 7-8 working days for a single agent)

### Post-MVP Tickets (P1/P2)

| Ticket | Description | Priority |
|--------|-------------|----------|
| E1-T6 | Structured logging (enhanced) | P1 |
| E4-T3 | Request validation | P1 |
| E4-T4 | Health check polish | P1 |
| E4-T5 | Retry logic | P1 |
| E6-T1 | User documentation | P1 |
| E6-T2 | Deployment guide | P1 |
| E6-T3 | Message polish | P1 |
| E6-T4 | Metrics/observability | P2 |

---

## Appendix: File Index

| Path | Ticket | Description |
|------|--------|-------------|
| `jamie/pyproject.toml` | E1-T1 | Project metadata |
| `jamie/requirements-bot.txt` | E1-T2 | Bot dependencies |
| `jamie/requirements-agent.txt` | E1-T3 | Agent dependencies |
| `jamie/docker/docker-compose.yml` | E1-T4 | Docker config |
| `jamie/config/settings.py` | E1-T5 | Settings management |
| `jamie/shared/logging.py` | E1-T6 | Logging config |
| `jamie/shared/models.py` | E3-T1 | API models |
| `jamie/shared/errors.py` | E4-T1 | Error codes |
| `jamie/bot/models.py` | E2-T1 | Session models |
| `jamie/bot/session.py` | E2-T2 | Session manager |
| `jamie/bot/cua_client.py` | E2-T3 | CUA HTTP client |
| `jamie/bot/url_parser.py` | E2-T4 | URL patterns |
| `jamie/bot/voice.py` | E2-T5 | Voice detection |
| `jamie/bot/main.py` | E2-T6 | JamieBot class |
| `jamie/bot/handlers.py` | E2-T7, E2-T8 | Message handlers |
| `jamie/bot/webhook.py` | E4-T2 | Webhook receiver |
| `jamie/bot/__main__.py` | E5-T1 | Bot entry point |
| `jamie/agent/models.py` | E3-T2 | Agent models |
| `jamie/agent/sandbox.py` | E3-T3 | Sandbox creation |
| `jamie/agent/prompts.py` | E3-T4 | Automation prompts |
| `jamie/agent/streamer.py` | E3-T5 | Streaming agent |
| `jamie/agent/controller.py` | E3-T6 | FastAPI controller |
| `jamie/agent/reporter.py` | E3-T7 | Status reporter |
| `jamie/agent/__main__.py` | E5-T2 | Agent entry point |
| `jamie/tests/` | E5-T3, E5-T4, E5-T5 | Test files |
| `jamie/scripts/manual_test.md` | E5-T6 | Test checklist |
| `jamie/docs/USER_GUIDE.md` | E6-T1 | User docs |
| `jamie/docs/DEPLOYMENT.md` | E6-T2 | Deploy docs |

---

*Document generated from TECHNICAL_SPEC.md, PRODUCT_SPEC.md, and ARCHITECTURE.md*
