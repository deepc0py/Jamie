# Jamie Product Specification

> "Jamie, pull that up" — A Discord bot that streams URLs to voice channels on demand

**Version:** 1.0  
**Last Updated:** 2026-02-07  
**Status:** Draft  
**Authors:** Product Team

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Problem Statement](#2-problem-statement)
3. [User Personas](#3-user-personas)
4. [User Stories](#4-user-stories)
5. [Functional Requirements](#5-functional-requirements)
6. [Non-Functional Requirements](#6-non-functional-requirements)
7. [User Experience](#7-user-experience)
8. [Success Metrics](#8-success-metrics)
9. [MVP Scope](#9-mvp-scope)
10. [Risks & Mitigations](#10-risks--mitigations)
11. [Open Questions](#11-open-questions)

---

## 1. Executive Summary

### What is Jamie?

Jamie is a Discord bot inspired by Joe Rogan's podcast sidekick ("Jamie, pull that up"). When a user wants to share a video, article, or website with their friends in a Discord voice channel, they simply DM Jamie with a URL. Jamie detects which voice channel the user is in, joins that channel, and streams the content for everyone to watch together.

### How Does It Work?

Jamie is a **hybrid system** combining two components:

1. **Jamie Bot (discord.py)** — A lightweight Discord bot that receives DMs, detects user voice presence, and coordinates streaming sessions
2. **CUA Agent (Computer Use Agent)** — Browser automation running in an isolated Docker sandbox that controls Discord Web to join voice channels and share screens

This architecture exists because **Discord's bot API does not support screen sharing**. The streaming API is client-only. Jamie works around this limitation by using a browser automation agent that operates Discord Web like a human user.

### Who Is It For?

- **Friend groups** who watch YouTube videos, Twitch streams, or browse the web together
- **Study groups** who share educational content during voice study sessions
- **Gaming communities** who share clips, tutorials, or stream content between matches
- **Podcast listeners** who want to share interesting episodes in real-time

### The Vision

Phase 1 (MVP): Stream URLs on demand  
Phase 2: Research Mode — "find me a nice airbnb in the mojave desert" and watch the agent browse in real-time

---

## 2. Problem Statement

### The Core Problem

Discord users want to share content with friends in voice channels, but the current options are frustrating:

| Current Option | Why It Fails |
|----------------|--------------|
| **Screen share yourself** | Requires you to have a good computer, stable connection, and ties up your screen |
| **Post links in chat** | Everyone watches separately, out of sync, different experiences |
| **Watch Party services** | Leave Discord, open new app, lose voice chat context |
| **Discord "Watch Together"** | Limited to specific platforms, often buggy, not universal |

### The Technical Barrier

**Discord bots cannot screen share.** The Discord API provides:
- ✅ Joining voice channels (audio only)
- ✅ Playing audio files/streams
- ❌ Screen sharing (client-only)
- ❌ Video streaming (client-only)

This is a deliberate API limitation. The streaming functionality is only available through Discord's client applications (desktop, web, mobile), not through the bot API.

### The Insight

If bots can't stream, but browser clients can, why not have a bot that *controls* a browser client?

This is exactly what Jamie does. The Jamie bot receives commands via DM and dispatches a Computer Use Agent that:
1. Opens Discord Web in a sandboxed browser
2. Logs in as a dedicated streaming account
3. Joins the specified voice channel
4. Opens the requested URL in another tab
5. Shares that tab via Discord's screen share

The result: a bot-like experience for users, powered by browser automation under the hood.

### Who Experiences This Problem?

- **Content Curators** — "I found this perfect video but I can't share it properly"
- **Group Leaders** — "I want everyone to see the same thing at the same time"
- **Remote Friends** — "We want to hang out and watch stuff together"

---

## 3. User Personas

### Persona 1: Alex the Content Curator

**Demographics:**
- Age: 22
- Role: Active Discord user, always finding interesting content
- Tech Savvy: Moderate (uses Discord daily, understands basic commands)

**Goals:**
- Share videos, articles, and websites with friends instantly
- Avoid the friction of "everyone open this link"
- Maintain the group's attention on shared content

**Pain Points:**
- When Alex screen shares, their laptop fans spin up and their game lags
- Friends often miss the "good parts" because they're out of sync
- Watch parties require leaving Discord and losing voice chat

**Quote:**
> "I just want to say 'Jamie, pull up this video' and have everyone see it. Like having my own podcast producer."

### Persona 2: Morgan the Study Group Leader

**Demographics:**
- Age: 28
- Role: Graduate student, leads weekly study sessions
- Tech Savvy: Low-moderate (uses Discord for voice, not much else)

**Goals:**
- Share lecture recordings, diagrams, and educational videos
- Keep study group focused on the same material
- Minimize technical friction during sessions

**Pain Points:**
- Different students have different connection speeds
- Some students don't know how to watch together
- Sharing screen uses too much of Morgan's bandwidth

**Quote:**
> "I need everyone looking at the same slide at the same time. I shouldn't have to be the one streaming it."

### Persona 3: Jordan the Gaming Community Admin

**Demographics:**
- Age: 32
- Role: Runs a 500-member gaming Discord
- Tech Savvy: High (manages bots, channels, integrations)

**Goals:**
- Stream tournament replays to watch parties
- Show tutorials and guides to new members
- Create shared experiences that build community

**Pain Points:**
- No good way to do "movie nights" in Discord
- Members ask for features Discord doesn't provide
- Third-party solutions require everyone to leave Discord

**Quote:**
> "We've tried everything — sync play apps, screen share rotations, posting timestamps. Nothing works smoothly."

### Persona 4: Sam the Researcher (Stretch Goal)

**Demographics:**
- Age: 35
- Role: Team lead who needs to research while presenting findings
- Tech Savvy: Moderate

**Goals:**
- Research topics collaboratively with team
- Show real-time browsing to stakeholders
- Let the AI do the tedious searching

**Pain Points:**
- Sharing research is time-consuming
- Hard to involve others in the discovery process
- Results get stale by the time they're presented

**Quote:**
> "I wish I could just say 'find me an Airbnb in the desert' and everyone watches the AI figure it out."

---

## 4. User Stories

### Core User Stories (MVP)

| ID | As a... | I want to... | So that... | Priority |
|----|---------|--------------|------------|----------|
| US-01 | Discord user in a voice channel | DM Jamie a URL | everyone in my voice channel can watch it together | **P0** |
| US-02 | Discord user | have Jamie detect my voice channel automatically | I don't have to specify which channel to join | **P0** |
| US-03 | User who initiated a stream | DM "stop" to Jamie | I can end the stream when we're done | **P0** |
| US-04 | User | receive confirmation when Jamie starts streaming | I know my request was received and is being processed | **P0** |
| US-05 | User | receive an error message if something fails | I know what went wrong and can try again | **P0** |

### Secondary User Stories (Post-MVP)

| ID | As a... | I want to... | So that... | Priority |
|----|---------|--------------|------------|----------|
| US-06 | User | request a different URL mid-stream | Jamie switches to the new content without leaving | P1 |
| US-07 | User | see what's currently streaming | I know what Jamie is playing before I join | P1 |
| US-08 | Voice channel member | DM "skip" to change content | any viewer can control the stream (if enabled) | P2 |
| US-09 | Server admin | configure which channels Jamie can stream to | I maintain control over bot behavior | P2 |
| US-10 | User | ask Jamie a natural language question | Jamie researches and streams the research process | P2 (Stretch) |

### Detailed User Story: US-01 (Primary Flow)

**Story:** As a Discord user in a voice channel, I want to DM Jamie a URL so that everyone in my voice channel can watch it together.

**Acceptance Criteria:**
1. User must be in a voice channel in a server Jamie can see
2. User DMs Jamie a valid URL (YouTube, Twitch, Vimeo, or general web)
3. Jamie acknowledges the request within 5 seconds
4. Jamie joins the user's voice channel within 30 seconds
5. Jamie starts screen sharing the URL content within 60 seconds
6. Other voice channel members see the stream
7. Audio from the stream is played through Discord

**Edge Cases:**
- User is in multiple voice channels (across servers) → Jamie asks which one
- User is not in any voice channel → Jamie prompts user to join one
- URL is invalid or inaccessible → Jamie reports the error
- Jamie is already streaming elsewhere → Jamie reports busy status
- URL is blocked/geolocked → Jamie reports access failure

---

## 5. Functional Requirements

### 5.1 Jamie Bot (Discord Interface)

| ID | Requirement | Description |
|----|-------------|-------------|
| FR-01 | **DM Listening** | Bot must receive and process direct messages from users |
| FR-02 | **URL Detection** | Bot must extract URLs from DM content (YouTube, Twitch, Vimeo, general HTTP/S) |
| FR-03 | **Voice Channel Detection** | Bot must determine user's current voice channel across all shared guilds |
| FR-04 | **Session Management** | Bot must track active streaming sessions (one session at a time for MVP) |
| FR-05 | **Stop Command** | Bot must accept "stop" to terminate active stream |
| FR-06 | **Status Reporting** | Bot must report stream status (starting, streaming, error, stopped) to user |
| FR-07 | **CUA Communication** | Bot must send streaming tasks to CUA agent via HTTP API |

### 5.2 CUA Agent (Browser Automation)

| ID | Requirement | Description |
|----|-------------|-------------|
| FR-08 | **Sandbox Execution** | Agent must run in isolated Docker container (trycua/cua-xfce) |
| FR-09 | **Discord Web Login** | Agent must log into Discord Web with provided credentials |
| FR-10 | **Voice Channel Join** | Agent must join specified voice channel by navigating Discord UI |
| FR-11 | **URL Loading** | Agent must open requested URL in a new browser tab |
| FR-12 | **Tab Sharing** | Agent must share the URL tab via Discord's screen share feature |
| FR-13 | **Stream Monitoring** | Agent must detect if stream fails and report status |
| FR-14 | **Graceful Termination** | Agent must stop sharing, leave channel, and shutdown on stop command |
| FR-15 | **Screenshot Capture** | Agent must use XGA resolution (1024x768) for optimal accuracy |

### 5.3 Communication Layer

| ID | Requirement | Description |
|----|-------------|-------------|
| FR-16 | **HTTP API** | CUA controller must expose HTTP endpoints for task submission |
| FR-17 | **Task Queue** | System must queue streaming requests (reject if busy for MVP) |
| FR-18 | **Status Webhook** | CUA agent must report status changes to Jamie bot |
| FR-19 | **Health Check** | System must support health checks for monitoring |

### 5.4 Supported Platforms

| Platform | URL Pattern | Priority |
|----------|-------------|----------|
| YouTube | `youtube.com/watch?v=`, `youtu.be/` | P0 |
| Twitch | `twitch.tv/` | P0 |
| Vimeo | `vimeo.com/` | P1 |
| Wikipedia | `wikipedia.org/` | P1 |
| General Web | Any `http://` or `https://` | P1 |

---

## 6. Non-Functional Requirements

### 6.1 Performance

| ID | Requirement | Target | Rationale |
|----|-------------|--------|-----------|
| NFR-01 | **Response Latency** | < 5 seconds from DM to acknowledgment | Users expect near-instant bot responses |
| NFR-02 | **Stream Start Time** | < 60 seconds from request to stream visible | Browser automation takes time; set expectations |
| NFR-03 | **Stream Quality** | 720p minimum, 30fps | Discord's default stream quality |
| NFR-04 | **Concurrent Streams** | 1 (MVP), 3+ (future) | Resource constraints of sandbox |
| NFR-05 | **Uptime** | 95% availability | Hobbyist project, not enterprise |

### 6.2 Security

| ID | Requirement | Description |
|----|-------------|-------------|
| NFR-06 | **Credential Storage** | Discord credentials must never be hardcoded; use environment variables or secure vault |
| NFR-07 | **Sandbox Isolation** | CUA agent must run in Docker container isolated from host |
| NFR-08 | **No Credential Exposure** | Bot must not log or transmit credentials in plaintext |
| NFR-09 | **Prompt Injection Mitigation** | Agent must not follow instructions found on streamed webpages |
| NFR-10 | **Rate Limiting** | Bot must respect Discord rate limits to avoid bans |

### 6.3 Reliability

| ID | Requirement | Description |
|----|-------------|-------------|
| NFR-11 | **Graceful Degradation** | If CUA agent crashes, Jamie bot must remain responsive and report error |
| NFR-12 | **Reconnection** | Agent must attempt reconnection if Discord stream drops |
| NFR-13 | **Timeout Handling** | Agent must timeout after 5 minutes of failed stream start |
| NFR-14 | **State Recovery** | Bot must not enter invalid state after agent crash |

### 6.4 Maintainability

| ID | Requirement | Description |
|----|-------------|-------------|
| NFR-15 | **Logging** | All components must log to stdout with structured JSON |
| NFR-16 | **Observability** | System must expose metrics for monitoring (stream count, error rate, latency) |
| NFR-17 | **Modularity** | Bot and agent must be independently deployable |

### 6.5 Cost Control

| ID | Requirement | Description |
|----|-------------|-------------|
| NFR-18 | **Budget Limits** | CUA agent must enforce per-session budget limit ($2 default) |
| NFR-19 | **Iteration Caps** | Agent loop must terminate after 50 iterations to prevent runaway |
| NFR-20 | **Model Selection** | Use Claude Sonnet 4.5 (cost-effective) rather than Opus for routine tasks |

---

## 7. User Experience

### 7.1 Interaction Flow

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           HAPPY PATH FLOW                                │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  1. USER joins voice channel "Movie Night"                               │
│                                                                          │
│  2. USER DMs Jamie:                                                      │
│     "https://youtube.com/watch?v=dQw4w9WgXcQ"                           │
│                                                                          │
│  3. JAMIE replies (< 5 sec):                                             │
│     "🎬 Got it! Streaming to **Movie Night** on **Your Server**..."     │
│                                                                          │
│  4. [CUA AGENT WORKING - 30-60 sec]                                      │
│     - Opens Discord Web                                                  │
│     - Logs in                                                            │
│     - Joins voice channel                                                │
│     - Opens YouTube in new tab                                           │
│     - Shares tab                                                         │
│                                                                          │
│  5. JAMIE replies:                                                       │
│     "✅ Now streaming! Everyone in the channel should see it."          │
│     "DM me **stop** when you're done."                                  │
│                                                                          │
│  6. [STREAMING - indefinite]                                             │
│     Users watch together in voice channel                                │
│                                                                          │
│  7. USER DMs Jamie:                                                      │
│     "stop"                                                               │
│                                                                          │
│  8. JAMIE replies:                                                       │
│     "⏹️ Stream ended. Thanks for watching!"                             │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### 7.2 Commands

| Command | Example | Description |
|---------|---------|-------------|
| **URL** | `https://youtube.com/watch?v=...` | Stream the URL to user's voice channel |
| **stop** | `stop` | End the current stream |
| **status** | `status` | Check if Jamie is currently streaming (future) |
| **help** | `help` | Show available commands (future) |

### 7.3 Bot Responses

#### Acknowledgment Messages

```
🎬 Got it! Streaming to **{channel_name}** on **{server_name}**...
This usually takes 30-60 seconds to set up.
```

#### Success Messages

```
✅ Now streaming! Everyone in the channel should see it.
DM me **stop** when you're done.
```

#### Error Messages

| Error | Message |
|-------|---------|
| Not in voice | "❌ You're not in any voice channel I can see. Join a voice channel and try again." |
| Invalid URL | "❌ I couldn't find a valid URL in your message. Send me a link to stream!" |
| Already streaming | "⏳ I'm already streaming somewhere else. DM **stop** to the current requester first, or wait for it to end." |
| Stream failed | "❌ Something went wrong setting up the stream. Try again, or try a different URL." |
| URL blocked | "❌ I couldn't load that URL. It might be geoblocked or require a login." |

#### Termination Messages

```
⏹️ Stream ended. Thanks for watching!
```

### 7.4 Error Recovery

| Scenario | System Behavior | User Experience |
|----------|-----------------|-----------------|
| CUA agent crashes | Bot detects lost session, marks as available | User gets error, can retry |
| Discord disconnects agent | Agent attempts reconnection (3 tries) | Users see brief interruption |
| URL fails to load | Agent reports failure, terminates | User gets error, can try different URL |
| User leaves voice channel | Stream continues for remaining viewers | No change until stop command |
| All viewers leave | Stream continues until stop (MVP) | Manual stop required |

---

## 8. Success Metrics

### 8.1 Primary Metrics

| Metric | Definition | Target (MVP) | Target (v1.1) |
|--------|------------|--------------|---------------|
| **Stream Success Rate** | % of requests that result in successful stream | > 80% | > 95% |
| **Time to Stream** | Seconds from request to stream visible | < 60s | < 45s |
| **Session Duration** | Average stream length | > 5 min | > 10 min |
| **User Retention** | % of users who use Jamie again within 7 days | > 50% | > 70% |

### 8.2 Engagement Metrics

| Metric | Definition | Target |
|--------|------------|--------|
| **Daily Active Users** | Unique users who send a DM to Jamie | Track, no target for MVP |
| **Streams per Day** | Total successful streams | Track, no target for MVP |
| **Avg Viewers per Stream** | Average voice channel size during stream | > 2 |
| **Error Rate** | % of requests that fail | < 20% (MVP), < 5% (v1.1) |

### 8.3 Operational Metrics

| Metric | Definition | Alert Threshold |
|--------|------------|-----------------|
| **Bot Uptime** | % time bot responds to DMs | < 95% |
| **Agent Health** | % successful agent spawns | < 90% |
| **Cost per Stream** | Average API cost per successful stream | > $1 |
| **P95 Latency** | 95th percentile time to stream | > 90s |

### 8.4 How We Measure

- **Bot metrics:** Logging + Prometheus/Grafana
- **Agent metrics:** CUA tracing + cost tracking
- **User metrics:** Discord message analytics (opt-in)
- **Qualitative:** User feedback via DM or server feedback channel

---

## 9. MVP Scope

### 9.1 What's In MVP (v1.0)

| Feature | Description | Status |
|---------|-------------|--------|
| ✅ DM-based URL streaming | User DMs URL, Jamie streams to their voice channel | **In Scope** |
| ✅ Voice channel detection | Automatically find user's current voice channel | **In Scope** |
| ✅ YouTube support | Stream YouTube videos | **In Scope** |
| ✅ Twitch support | Stream Twitch channels/VODs | **In Scope** |
| ✅ Stop command | End stream via DM | **In Scope** |
| ✅ Basic error handling | Report failures to user | **In Scope** |
| ✅ Single-stream limit | One stream at a time | **In Scope** |

### 9.2 What's NOT in MVP

| Feature | Reason | Target Version |
|---------|--------|----------------|
| ❌ Multi-stream support | Complexity, resource constraints | v1.1 |
| ❌ URL switching mid-stream | Adds complexity to agent | v1.1 |
| ❌ Server configuration | Admin controls not essential for personal use | v1.2 |
| ❌ Viewer controls (skip, pause) | Adds significant agent complexity | v1.2 |
| ❌ General web streaming | Focus on video platforms first | v1.1 |
| ❌ Research mode | Stretch goal, needs more agent sophistication | v2.0 |
| ❌ Audio-only mode | Screen share is the core feature | Maybe never |
| ❌ Mobile support | Desktop-first | v1.3 |

### 9.3 MVP Technical Constraints

- **One stream at a time:** Single CUA sandbox, single Discord account
- **Manual stop only:** No auto-stop when channel empties
- **No 2FA support:** Streaming Discord account must have 2FA disabled
- **XGA resolution:** 1024x768 for agent accuracy (may limit stream quality)
- **60-second startup:** Browser automation takes time

### 9.4 MVP Launch Checklist

- [ ] Jamie bot deployed and online
- [ ] CUA sandbox running and healthy
- [ ] HTTP API communication working
- [ ] YouTube streaming tested end-to-end
- [ ] Twitch streaming tested end-to-end
- [ ] Error handling tested
- [ ] Stop command tested
- [ ] Documentation written (user-facing)
- [ ] Monitoring/alerting in place

### 9.5 Post-MVP Roadmap

| Version | Focus | Timeline |
|---------|-------|----------|
| **v1.0 (MVP)** | Core streaming flow | Week 1-2 |
| **v1.1** | Reliability + more platforms | Week 3-4 |
| **v1.2** | Server configuration, viewer controls | Week 5-6 |
| **v2.0** | Research Mode (stretch goal) | TBD |

---

## 10. Risks & Mitigations

### 10.1 Technical Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| **Discord ToS violation** | Medium | High (account ban) | Use dedicated streaming account, don't abuse |
| **CUA agent gets stuck** | High | Medium | Iteration limits, timeout, manual reset |
| **Discord UI changes** | Medium | High | Agent uses visual recognition, somewhat resilient |
| **Browser/tab sharing breaks** | Low | High | Keep sandbox environment stable, test regularly |
| **High latency/lag** | Medium | Medium | Optimize agent steps, reduce screenshot frequency |
| **2FA requirement** | Low | High | Use account without 2FA, or implement code flow |
| **Rate limiting** | Medium | Medium | Respect limits, add backoff, one stream at a time |

### 10.2 Security Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| **Prompt injection via streamed content** | Medium | Medium | Don't let agent "read" streamed page content |
| **Credential exposure** | Low | High | Environment variables, never log credentials |
| **Agent executes malicious site** | Low | Medium | Sandbox isolation, no host access |
| **Discord account takeover** | Low | High | Dedicated bot account, strong password |

### 10.3 Product Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| **Users don't understand how to use** | Medium | Medium | Clear onboarding message, help command |
| **60-second startup feels too slow** | Medium | Medium | Set expectations in acknowledgment message |
| **Limited to one stream at a time** | Medium | Low | Be transparent about limitation, queue requests (v1.1) |
| **Low adoption** | Medium | Low | Dogfood with friends first, iterate |

### 10.4 Operational Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| **API costs exceed budget** | Medium | Medium | Per-session budget limits, cost alerts |
| **Sandbox resource exhaustion** | Low | Medium | Resource limits, monitoring, restart capability |
| **No one available to fix issues** | Medium | Low | Good logging, runbooks, auto-recovery where possible |

---

## 11. Open Questions

### 11.1 Decisions Needed Before MVP

| Question | Options | Recommendation | Decision |
|----------|---------|----------------|----------|
| **How to handle 2FA?** | A) Disable 2FA on bot account, B) Implement 2FA code flow, C) Use session tokens | A) Disable 2FA (simplest for MVP) | TBD |
| **Which VLM model?** | A) Claude Sonnet 4.5 ($3/M in), B) Claude Opus 4.5 ($15/M in), C) Local UI-TARS | A) Sonnet (cost-effective, sufficient accuracy) | TBD |
| **How to persist Discord login?** | A) Login every session, B) Save browser profile, C) Inject session token | B) Save browser profile (faster restarts) | TBD |
| **Audio handling?** | A) Rely on Discord tab share audio, B) Explicit audio routing | A) Tab share includes audio by default | TBD |

### 11.2 Future Considerations

| Question | Context | Timeline |
|----------|---------|----------|
| **Support multiple simultaneous streams?** | Requires multiple sandboxes, multiple bot accounts | v1.1+ |
| **Support server-based commands (not just DM)?** | "!jamie play URL" in a text channel | v1.2+ |
| **Auto-stop when channel empties?** | Need to monitor voice channel membership | v1.1+ |
| **Queue system for multiple requests?** | Fair ordering, timeout, cancellation | v1.1+ |
| **Integration with Watch Together / Activities?** | Discord's native features may evolve | Monitor |

### 11.3 Research Mode Questions

| Question | Notes |
|----------|-------|
| **What natural language queries to support?** | Start narrow: "find me X on Y platform" |
| **How to prevent agent from doing harmful searches?** | Content filtering, restricted domains |
| **How long should research sessions last?** | Time limit? Token limit? User stop only? |
| **Should agent narrate what it's doing?** | TTS? Text overlay? Chat messages? |

### 11.4 Legal/Policy Questions

| Question | Notes |
|----------|-------|
| **Does this violate Discord ToS?** | Probably gray area; automation of client UI. Use at own risk. |
| **Copyright concerns with streaming content?** | Same as any screen share; user's responsibility. |
| **Data retention requirements?** | Don't log message content beyond what's needed. |

---

## Appendices

### A. Technical Architecture Reference

See: [ARCHITECTURE.md](./ARCHITECTURE.md)

### B. Discord.py API Reference

See: [discord-py-api.md](./discord-py-api.md)

### C. CUA Framework Reference

See: [cua-framework.md](./cua-framework.md)

### D. Anthropic Computer Use Reference

See: [anthropic-computer-use.md](./anthropic-computer-use.md)

---

## Document History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-02-07 | Product Team | Initial draft |

---

*This document is the source of truth for Jamie's product requirements. Engineering should reference this document for scope decisions. Update this document as requirements evolve.*
