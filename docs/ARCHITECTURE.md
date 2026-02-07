# Jamie - "Can You Pull That Up For Me"

> A Discord bot that joins voice channels and streams URLs on demand, inspired by Joe Rogan's "Jamie, pull that up."

## Overview

Jamie is a hybrid system combining a Discord bot (for coordination) with a CUA agent (for browser automation). This architecture is necessary because **Discord bots cannot screen share** — the streaming API is client-only.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         User Flow                                │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. User joins voice channel "Movie Night"                       │
│  2. User DMs Jamie: "https://youtube.com/watch?v=..."           │
│  3. Jamie detects user is in "Movie Night" on "hey lol" server  │
│  4. Jamie spawns CUA agent with task                            │
│  5. CUA agent:                                                   │
│     a. Opens browser with Discord web                           │
│     b. Logs into Discord                                        │
│     c. Joins "Movie Night" voice channel                        │
│     d. Opens YouTube URL in new tab                             │
│     e. Shares tab via Discord screen share                      │
│  6. User watches stream in voice channel                        │
│  7. User DMs "stop" → Jamie terminates CUA agent                │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Components

### 1. Jamie Bot (discord.py)

**Role:** Coordinator — receives commands, finds voice channels, triggers CUA agents

**Stack:**
- Python 3.12+
- discord.py 2.0+
- Redis or HTTP for CUA communication

**Key Responsibilities:**
- Listen for DMs with URLs or commands
- Detect user's current voice channel via `member.voice.channel`
- Spawn/manage CUA agent sessions
- Report status back to user
- Handle stop/cancel commands

**Required Intents:**
```python
intents.message_content = True   # Read DM content
intents.dm_messages = True       # Receive DMs
intents.guilds = True            # Access guild data
intents.voice_states = True      # Detect voice presence
```

**Core Pattern:**
```python
async def find_user_voice_channel(user: discord.User) -> Optional[discord.VoiceChannel]:
    """Find user's current voice channel across shared guilds."""
    for guild in client.guilds:
        member = guild.get_member(user.id)
        if member and member.voice and member.voice.channel:
            return member.voice.channel
    return None
```

### 2. CUA Agent (Computer Use Agent)

**Role:** Worker — browser automation in isolated sandbox

**Stack:**
- Python 3.12 or 3.13 (required by CUA)
- CUA Framework (`cua-computer`, `cua-agent`)
- Docker sandbox (`trycua/cua-xfce:latest`)
- Claude Sonnet 4.5 or similar VLM

**Why CUA over raw Anthropic API:**
- Batteries included (sandboxes, SDK, agent loops)
- Docker integration out of the box
- Unified interface across providers
- Built-in budget control and callbacks

**Sandbox Setup:**
```bash
docker pull --platform=linux/amd64 trycua/cua-xfce:latest
```

**Agent Task Flow:**
1. Start Docker sandbox
2. Launch Firefox
3. Navigate to Discord web, log in
4. Join specified voice channel (by name or ID)
5. Open new tab with streaming URL
6. Return to Discord tab
7. Click "Share Screen" → Select tab → Confirm
8. Monitor stream, report status
9. On stop command: end share, leave channel, shutdown

### 3. Communication Layer

**Options (in order of simplicity):**

| Method | Pros | Cons |
|--------|------|------|
| **HTTP API** | Simple, stateless | Need to run server in sandbox |
| **Redis Queue** | Decoupled, reliable | Extra infrastructure |
| **Subprocess** | Direct control | Tighter coupling |
| **File-based** | Dead simple | Polling overhead |

**Recommended: HTTP API**

Jamie bot sends POST request to CUA controller:
```json
{
  "action": "stream",
  "url": "https://youtube.com/watch?v=...",
  "guild_id": "123456789",
  "channel_id": "987654321",
  "channel_name": "Movie Night",
  "discord_credentials": {
    "email": "...",
    "password": "..."
  }
}
```

CUA controller responds with session ID, status updates via webhook or polling.

## Implementation Plan

### Phase 1: Minimal Prototype
**Goal:** Join voice, stream a single Wikipedia page

- [ ] Jamie bot skeleton (DM handling, voice detection)
- [ ] CUA sandbox setup (Docker XFCE)
- [ ] Basic agent script:
  - Open Discord web
  - Log in (hardcoded creds for testing)
  - Join voice channel
  - Open Wikipedia in new tab
  - Share tab
- [ ] Manual trigger (no bot integration yet)

### Phase 2: Bot Integration
**Goal:** Full DM → stream flow

- [ ] HTTP API for Jamie → CUA communication
- [ ] Session management (track active streams)
- [ ] Stop/cancel commands
- [ ] Error handling and status reporting
- [ ] User feedback (DM confirmations)

### Phase 3: Polish
**Goal:** Production-ready

- [ ] Credential management (secure storage)
- [ ] Multiple concurrent streams (if needed)
- [ ] Stream health monitoring
- [ ] Reconnection handling
- [ ] Rate limiting
- [ ] Logging and observability

### Phase 4: Research Mode (Stretch Goal)
**Goal:** "Find me an airbnb in the mojave"

- [ ] Parse natural language requests
- [ ] Agent researches autonomously
- [ ] User watches agent work in real-time
- [ ] Agent narrates actions (optional TTS?)

## Technical Details

### Resolution

CUA/Anthropic recommend **XGA (1024x768)** for best accuracy. Higher resolutions require coordinate scaling and may reduce accuracy.

```python
computer = Computer(
    os_type="linux",
    provider_type="docker",
    image="trycua/cua-xfce:latest",
    display="1024x768"
)
```

### Discord Login Flow

Agent needs to:
1. Navigate to `discord.com/login`
2. Enter email, click Continue
3. Enter password, click Log In
4. Handle 2FA if enabled (challenge)
5. Wait for app to load

**Consideration:** 2FA will complicate automation. Options:
- Use account without 2FA (security risk)
- Implement 2FA code entry (user provides code via DM)
- Use session token injection instead of login

### Tab Sharing Flow

Discord web tab sharing:
1. Click voice channel to join
2. Click "Share Your Screen" button
3. Browser shows sharing picker
4. Select "Chrome Tab" or "Firefox Tab"
5. Choose the correct tab
6. Click "Share"

Agent must:
- Identify Discord's share button
- Navigate browser's tab picker UI
- Select correct tab by title/content
- Confirm share

### Budget Control

Prevent runaway costs with CUA's budget management:

```python
agent = ComputerAgent(
    model="anthropic/claude-sonnet-4-5-20250929",
    tools=[computer],
    max_trajectory_budget=2.0  # Max $2 per stream session
)
```

### Error Handling

Common failure modes:
- Discord login fails (bad creds, rate limit, captcha)
- Voice channel not found
- Tab sharing blocked by browser
- Stream URL fails to load
- Agent gets stuck/loops

Each needs detection and graceful recovery or user notification.

## Security Considerations

1. **Credentials:** Never hardcode. Use environment variables or secure vault.
2. **Sandbox Isolation:** CUA runs in Docker, isolated from host.
3. **Prompt Injection:** Agent sees screenshots — malicious content on screen could manipulate it.
4. **Rate Limits:** Discord will rate limit aggressive automation.
5. **ToS:** Browser automation of Discord may violate ToS. Use at own risk.

## File Structure

```
jamie/
├── bot/
│   ├── __init__.py
│   ├── main.py           # Discord bot entry point
│   ├── handlers.py       # DM and voice handlers
│   └── cua_client.py     # HTTP client for CUA controller
├── agent/
│   ├── __init__.py
│   ├── controller.py     # HTTP server for receiving tasks
│   ├── streamer.py       # CUA agent logic
│   └── discord_actions.py # Discord-specific automation
├── config/
│   ├── settings.py       # Configuration management
│   └── credentials.py    # Secure credential handling
├── docker/
│   └── docker-compose.yml
├── docs/
│   ├── ARCHITECTURE.md   # This file
│   ├── discord-py-api.md
│   ├── cua-framework.md
│   └── anthropic-computer-use.md
└── README.md
```

## Dependencies

### Jamie Bot
```
discord.py>=2.0
aiohttp
python-dotenv
redis  # if using Redis queue
```

### CUA Agent
```
cua-computer
cua-agent
python-dotenv
fastapi  # for HTTP controller
uvicorn
```

## Environment Variables

```bash
# Discord
DISCORD_BOT_TOKEN=
DISCORD_EMAIL=
DISCORD_PASSWORD=

# CUA
CUA_API_KEY=  # if using cloud, optional for local
ANTHROPIC_API_KEY=

# Communication
JAMIE_CUA_ENDPOINT=http://localhost:8000
```

## Open Questions

1. **2FA Handling:** How to handle Discord 2FA? Skip, user-provided codes, or session tokens?
2. **Multi-stream:** Support multiple simultaneous streams to different channels?
3. **Audio:** Does tab sharing include audio automatically, or does Discord need configuration?
4. **Persistence:** Should agent stay logged in between streams, or fresh login each time?
5. **Model Choice:** Claude Sonnet 4.5 vs cheaper models? Local models viable?

## Next Steps

1. **Set up development environment**
   - Install Python 3.12+
   - Pull Docker image
   - Create Discord bot application

2. **Build minimal prototype**
   - Jamie bot: DM listener + voice detection
   - CUA agent: Discord login + voice join + tab share
   - Manual integration test

3. **Iterate based on what breaks**

---

*Created: 2026-02-07*
*Authors: Rodrigo 🦞 + Jesse*

---

## Additional Requirements (Added 2026-02-07)

### Authentication
- **Claude Code Subscription Auth:** Jamie should support authentication via Claude Code subscription, not just raw API keys
- This enables users with Claude Code subscriptions to use Jamie without separate Anthropic API billing

### OpenClaw Integration
- **Component Architecture:** Jamie should work as a component/plugin of OpenClaw
- This means Jamie can be triggered via OpenClaw's messaging system, cron jobs, or direct commands
- Consider: OpenClaw skill, channel plugin, or standalone service that OpenClaw can invoke

### Implications
1. Auth layer should abstract between API key and Claude Code subscription
2. Entry points should support both standalone execution and OpenClaw invocation
3. Configuration should support OpenClaw environment variables where applicable
