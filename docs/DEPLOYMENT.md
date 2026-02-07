# Jamie Deployment Guide

This guide covers deploying Jamie, the Discord streaming bot powered by CUA (Computer Use Agent).

## Table of Contents

- [Prerequisites](#prerequisites)
- [Environment Variables](#environment-variables)
- [Docker Compose Deployment](#docker-compose-deployment)
- [Development Setup](#development-setup)
- [Monitoring and Logging](#monitoring-and-logging)
- [Security Considerations](#security-considerations)

---

## Prerequisites

### Required Software

| Software | Version | Purpose |
|----------|---------|---------|
| Python | 3.12+ | Runtime for bot and agent |
| Docker | 24.0+ | Container orchestration |
| Docker Compose | 2.20+ | Multi-container deployment |
| Git | 2.40+ | Version control |

### Discord Bot Setup

1. **Create a Discord Application**
   - Go to [Discord Developer Portal](https://discord.com/developers/applications)
   - Click "New Application" and name it (e.g., "Jamie")
   - Navigate to the "Bot" section
   - Click "Add Bot"

2. **Configure Bot Permissions**
   - Enable these Privileged Gateway Intents:
     - `MESSAGE CONTENT INTENT`
     - `SERVER MEMBERS INTENT`
   - Under OAuth2 > URL Generator, select scopes:
     - `bot`
     - `applications.commands`
   - Select bot permissions:
     - `Send Messages`
     - `Embed Links`
     - `Read Message History`
     - `Connect` (voice)
     - `Speak` (voice)
     - `Use Voice Activity`

3. **Get Your Bot Token**
   - In the Bot section, click "Reset Token"
   - Copy and save the token securely (you'll need it for `JAMIE_BOT_DISCORD_TOKEN`)

4. **Invite the Bot**
   - Use the generated OAuth2 URL to invite the bot to your server

### Anthropic API Key

1. Sign up at [Anthropic Console](https://console.anthropic.com/)
2. Generate an API key
3. Save it for `JAMIE_AGENT_ANTHROPIC_API_KEY`

---

## Environment Variables

Create a `.env` file in the project root. All variables use prefixes to indicate which component they configure.

### Bot Configuration (`JAMIE_BOT_` prefix)

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `JAMIE_BOT_DISCORD_TOKEN` | ✅ | — | Discord bot token |
| `JAMIE_BOT_CUA_ENDPOINT` | ❌ | `http://localhost:8000` | CUA controller HTTP endpoint |
| `JAMIE_BOT_CUA_TIMEOUT` | ❌ | `30` | CUA request timeout (seconds) |
| `JAMIE_BOT_WEBHOOK_HOST` | ❌ | `0.0.0.0` | Webhook listener bind address |
| `JAMIE_BOT_WEBHOOK_PORT` | ❌ | `8080` | Webhook listener port |

### Agent Configuration (`JAMIE_AGENT_` prefix)

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `JAMIE_AGENT_DISCORD_EMAIL` | ✅ | — | Discord email for web login |
| `JAMIE_AGENT_DISCORD_PASSWORD` | ✅ | — | Discord password for web login |
| `JAMIE_AGENT_ANTHROPIC_API_KEY` | ✅ | — | Anthropic API key |
| `JAMIE_AGENT_MODEL` | ❌ | `anthropic/claude-sonnet-4-5-20250929` | Vision-language model for CUA |
| `JAMIE_AGENT_MAX_BUDGET_PER_SESSION` | ❌ | `2.0` | Max cost in USD per session |
| `JAMIE_AGENT_SANDBOX_IMAGE` | ❌ | `trycua/cua-xfce:latest` | Docker image for CUA sandbox |
| `JAMIE_AGENT_DISPLAY_RESOLUTION` | ❌ | `1024x768` | Sandbox display resolution |
| `JAMIE_AGENT_HOST` | ❌ | `0.0.0.0` | Controller HTTP bind address |
| `JAMIE_AGENT_PORT` | ❌ | `8000` | Controller HTTP port |

### Example `.env` File

```bash
# ===================
# Bot Configuration
# ===================
JAMIE_BOT_DISCORD_TOKEN=your-discord-bot-token-here
JAMIE_BOT_CUA_ENDPOINT=http://jamie-agent:8000
JAMIE_BOT_CUA_TIMEOUT=30

# ===================
# Agent Configuration  
# ===================
JAMIE_AGENT_DISCORD_EMAIL=your-discord-email@example.com
JAMIE_AGENT_DISCORD_PASSWORD=your-discord-password
JAMIE_AGENT_ANTHROPIC_API_KEY=sk-ant-xxxxxxxxxxxxx
JAMIE_AGENT_MODEL=anthropic/claude-sonnet-4-5-20250929
JAMIE_AGENT_MAX_BUDGET_PER_SESSION=2.0
JAMIE_AGENT_SANDBOX_IMAGE=trycua/cua-xfce:latest
```

---

## Docker Compose Deployment

This is the recommended deployment method for production.

### Quick Start

```bash
# Clone the repository
git clone https://github.com/your-org/jamie.git
cd jamie

# Create environment file
cp .env.example .env
# Edit .env with your credentials

# Build and start services
docker compose up -d --build

# Check status
docker compose ps

# View logs
docker compose logs -f
```

### Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                    Docker Network                        │
│  ┌─────────────┐       HTTP        ┌─────────────────┐  │
│  │  jamie-bot  │ ───────────────▶  │   jamie-agent   │  │
│  │  (Discord)  │                   │  (CUA Controller)│  │
│  └─────────────┘                   └────────┬────────┘  │
│                                             │            │
│                                    Docker-in-Docker     │
│                                             │            │
│                                    ┌────────▼────────┐  │
│                                    │   CUA Sandbox   │  │
│                                    │  (Headless X11) │  │
│                                    └─────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

### Service Details

**jamie-bot:**
- Discord bot handling user commands
- Lightweight Python container
- Communicates with agent via HTTP

**jamie-agent:**
- CUA controller managing browser automation
- Requires privileged mode for Docker-in-Docker
- Mounts Docker socket for sandbox management
- Persists browser profile for session continuity

### Managing the Deployment

```bash
# Start services
docker compose up -d

# Stop services
docker compose down

# Restart a specific service
docker compose restart jamie-bot

# Rebuild after code changes
docker compose up -d --build

# View logs for specific service
docker compose logs -f jamie-agent

# Shell into a container
docker compose exec jamie-bot /bin/bash

# Check resource usage
docker stats
```

### Updating

```bash
# Pull latest changes
git pull origin main

# Rebuild and restart
docker compose up -d --build
```

---

## Development Setup

For local development without Docker.

### 1. Clone and Setup Virtual Environment

```bash
git clone https://github.com/your-org/jamie.git
cd jamie

# Create virtual environment
python3.12 -m venv .venv
source .venv/bin/activate  # Linux/macOS
# or: .venv\Scripts\activate  # Windows

# Install dependencies
pip install -e ".[dev]"
```

### 2. Configure Environment

```bash
# Copy example env file
cp .env.example .env

# Edit with your credentials
# For local dev, use localhost endpoints:
# JAMIE_BOT_CUA_ENDPOINT=http://localhost:8000
```

### 3. Run Components

**Terminal 1 - Agent Controller:**
```bash
source .venv/bin/activate
python -m jamie.agent.main
# Starts on http://localhost:8000
```

**Terminal 2 - Discord Bot:**
```bash
source .venv/bin/activate
python -m jamie.bot.main
```

### 4. Running Tests

```bash
# Run all tests
pytest

# With coverage
pytest --cov=jamie --cov-report=html

# Run specific test file
pytest tests/test_config.py -v

# Run with asyncio debugging
pytest --tb=short -v
```

### 5. Code Quality

```bash
# Format code
black jamie/ tests/

# Lint
ruff check jamie/ tests/

# Type checking
mypy jamie/
```

---

## Monitoring and Logging

### Structured Logging

Jamie uses `structlog` for structured JSON logging. Logs include:

- Timestamps
- Log levels
- Component identifiers
- Request IDs for tracing
- Contextual metadata

### Viewing Logs

**Docker Compose:**
```bash
# All services
docker compose logs -f

# Specific service with timestamps
docker compose logs -f --timestamps jamie-agent

# Last 100 lines
docker compose logs --tail=100 jamie-bot
```

**Log Levels:**
Set via environment variable:
```bash
LOG_LEVEL=DEBUG  # DEBUG, INFO, WARNING, ERROR
```

### Key Metrics to Monitor

| Metric | Location | Description |
|--------|----------|-------------|
| Session starts | Agent logs | CUA sessions initiated |
| Session costs | Agent logs | API spend per session |
| API errors | Agent logs | Anthropic API failures |
| Discord events | Bot logs | Commands, messages |
| Sandbox health | Agent logs | Container lifecycle |

### Health Checks

```bash
# Check agent health endpoint
curl http://localhost:8000/health

# Check bot is connected to Discord
docker compose logs jamie-bot | grep "Connected"
```

### Alerting Recommendations

For production, consider:

1. **Log aggregation** - Ship logs to ELK, Datadog, or similar
2. **Uptime monitoring** - Monitor `/health` endpoints
3. **Cost alerting** - Alert when `max_budget_per_session` is approached
4. **Discord status** - Monitor bot connection status

---

## Security Considerations

### Token and Secret Handling

**DO:**
- ✅ Store secrets in `.env` files (never commit to git)
- ✅ Use `SecretStr` types (already implemented in config)
- ✅ Rotate tokens periodically
- ✅ Use environment-specific credentials (dev vs prod)

**DON'T:**
- ❌ Commit `.env` files to version control
- ❌ Log secret values (SecretStr prevents this)
- ❌ Share tokens in Discord or chat
- ❌ Use the same credentials across environments

### .gitignore Essentials

Ensure these are in `.gitignore`:
```
.env
.env.*
*.pem
*.key
browser-profile/
```

### Discord Account Security

The agent requires Discord web credentials for browser automation:

1. **Use a dedicated account** - Don't use your personal Discord account
2. **Enable 2FA** - But note this may complicate automation
3. **Limit permissions** - Only grant necessary server permissions
4. **Monitor activity** - Watch for unexpected login locations

### Sandbox Isolation

The CUA sandbox provides isolation:

- **Docker container** - Browser runs in isolated container
- **No persistent state** - Sandbox is ephemeral by default
- **Network isolation** - Sandbox on separate Docker network
- **Resource limits** - Can set memory/CPU limits

**Additional hardening:**
```yaml
# docker-compose.yml additions
jamie-agent:
  security_opt:
    - no-new-privileges:true
  cap_drop:
    - ALL
  cap_add:
    - SYS_ADMIN  # Required for sandbox
  read_only: true
  tmpfs:
    - /tmp
```

### API Key Protection

Anthropic API keys:

1. **Set spending limits** in Anthropic Console
2. **Use per-session budgets** via `JAMIE_AGENT_MAX_BUDGET_PER_SESSION`
3. **Monitor usage** in Anthropic dashboard
4. **Rotate keys** if compromised

### Network Security

For production deployments:

1. **Don't expose ports publicly** - Agent port 8000 should be internal only
2. **Use reverse proxy** - If external access needed, use nginx/traefik
3. **Enable TLS** - For any external endpoints
4. **Firewall rules** - Restrict access to Docker host

### Privileged Container Warning

The agent container runs with `privileged: true` for Docker-in-Docker. This grants elevated permissions. Mitigations:

1. Run on dedicated VM/host
2. Use rootless Docker if possible
3. Implement strict network policies
4. Regular security updates

---

## Troubleshooting

### Common Issues

**Bot won't connect to Discord:**
```bash
# Check token is set
docker compose exec jamie-bot env | grep DISCORD_TOKEN

# Check for authentication errors
docker compose logs jamie-bot | grep -i "auth\|token\|login"
```

**Agent can't start sandbox:**
```bash
# Verify Docker socket mount
docker compose exec jamie-agent docker ps

# Check sandbox image exists
docker compose exec jamie-agent docker images | grep cua
```

**API budget exceeded:**
```bash
# Check current spend in logs
docker compose logs jamie-agent | grep "budget\|cost"

# Increase limit if needed
# JAMIE_AGENT_MAX_BUDGET_PER_SESSION=5.0
```

### Getting Help

1. Check existing [documentation](./ARCHITECTURE.md)
2. Review [technical spec](./TECHNICAL_SPEC.md)
3. Open an issue on GitHub
