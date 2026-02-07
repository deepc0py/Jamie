# Jamie User Guide

Welcome to Jamie! 🎬

Jamie is your friendly Discord streaming assistant. Send Jamie a video link, and it'll stream it directly to your voice channel so everyone can watch together.

---

## Quick Start

1. **Join a voice channel** in a server where Jamie is a member
2. **DM Jamie** with a video URL (like a YouTube link)
3. **Enjoy the show!** 🍿

That's it! Jamie handles the rest.

---

## Getting Jamie on Your Server

### Invite Link

Ask your server admin to invite Jamie using the official invite link. Once Jamie is in your server, any member can use it by DMing the bot directly.

> **Note:** Jamie needs permission to join voice channels and stream. Your server admin may need to adjust role permissions.

### Checking if Jamie is Available

Look for Jamie in your server's member list. If Jamie shows as online, you're ready to go!

---

## How to Use Jamie

### Step-by-Step Instructions

**Step 1: Join a Voice Channel**

Open Discord and join any voice channel in a server where Jamie is a member. Jamie will stream to whatever channel you're in when you send the request.

**Step 2: Open a DM with Jamie**

Click on Jamie's name in the member list and select "Message" to open a direct message.

**Step 3: Send Your URL**

Paste the URL of what you want to watch. Just send the link by itself—no special formatting needed!

Example:
```
https://www.youtube.com/watch?v=dQw4w9WgXcQ
```

**Step 4: Wait for Confirmation**

Jamie will respond with:
```
🎬 Starting stream to #your-channel in Your Server...
```

**Step 5: Watch the Stream**

In Discord, you'll see Jamie (or the streaming account) appear in your voice channel with a "Live" indicator. Click it to watch!

**Step 6: Stop When Done**

When you're finished, send `stop` to Jamie in DMs. The stream will end, and the channel is freed up for others.

---

## Commands

All commands are sent via DM to Jamie.

| Command | What It Does |
|---------|--------------|
| *Any URL* | Start streaming that link to your voice channel |
| `stop` | Stop your current stream |
| `status` | Check if you have an active stream |
| `help` | Show available commands |

### Examples

**Start a stream:**
```
https://www.youtube.com/watch?v=dQw4w9WgXcQ
```

**Stop your stream:**
```
stop
```

**Check what's playing:**
```
status
```

---

## Supported Platforms

Jamie works with all of these:

### ✅ YouTube
- Regular videos: `youtube.com/watch?v=...`
- Short links: `youtu.be/...`
- YouTube Shorts: `youtube.com/shorts/...`
- Live streams: `youtube.com/live/...`
- Embedded videos: `youtube.com/embed/...`

### ✅ Twitch
- Live channels: `twitch.tv/channelname`
- Past broadcasts and clips

### ✅ Vimeo
- Video pages: `vimeo.com/123456789`

### ✅ Wikipedia
- Article pages (for research watch parties!)

### ✅ Other Websites
- Jamie also supports most other URLs—it'll try to stream whatever's on the page. Results may vary for less common sites.

---

## Frequently Asked Questions

### "Why isn't Jamie responding to my message?"

Make sure you're:
- Sending a **direct message (DM)** to Jamie, not posting in a server channel
- Sending a valid URL that starts with `https://` or `http://`
- Not blocked by Jamie or having DMs disabled

### "Jamie says I need to be in a voice channel"

Jamie streams to whatever voice channel you're in. Join a voice channel first, then send your URL.

### "Can I change the video while streaming?"

Not directly—send `stop` first to end the current stream, then send the new URL.

### "Why can't Jamie find my voice channel?"

Jamie can only see voice channels in servers where it's a member. Make sure:
- Jamie is in the same server as you
- You're in a voice channel (not just online in the server)
- The voice channel isn't hidden from bots by permission settings

### "Can multiple people use Jamie at once?"

Each user can have one active stream at a time. Multiple users can each start their own streams in different channels.

### "How do I invite Jamie to my server?"

Contact your server admin—they'll need the official invite link and admin permissions to add bots.

### "Is there a time limit on streams?"

There's no hard limit, but very long streams (several hours) might time out. If that happens, just send the link again.

### "Why is there no audio?"

Some streams might have audio issues depending on the source. Try:
- Refreshing your view of the stream (leave and rejoin)
- Using a different URL for the same content
- Checking your Discord audio settings

---

## Troubleshooting

### Common Issues

**"You already have an active stream"**
> You can only stream one thing at a time. Send `stop` to end your current stream, then try again.

**"I don't have an active stream" (when you think you do)**
> The stream may have ended on its own. Try sending your URL again.

**"Failed to start stream"**
> Something went wrong on Jamie's end. Wait a moment and try again, or try a different URL.

**Stream won't stop**
> If `stop` doesn't work, wait a minute and try again. The stream might still be shutting down.

**No response from Jamie**
> - Check that Jamie is online (green status indicator)
> - Make sure you're in DMs, not a server channel
> - Try sending `help` to test if Jamie is responsive

### Still Having Problems?

If nothing here helps, contact your server admin—they may need to check Jamie's permissions or server settings.

---

## Tips & Best Practices

💡 **Join voice first** — Always be in a voice channel before sending a URL.

💡 **Use direct links** — `youtube.com/watch?v=...` works better than playlist links or channel pages.

💡 **One at a time** — Stop your stream before starting a new one.

💡 **Be patient** — Starting a stream takes a few seconds. Wait for Jamie's confirmation.

💡 **Keep it simple** — Just paste the URL. No need for extra text or commands.

---

## Quick Reference Card

```
┌─────────────────────────────────────────┐
│           JAMIE QUICK REFERENCE         │
├─────────────────────────────────────────┤
│  1. Join voice channel                  │
│  2. DM Jamie a URL                      │
│  3. Watch the stream!                   │
├─────────────────────────────────────────┤
│  COMMANDS (send in DM)                  │
│  • [URL]    → Start streaming           │
│  • stop     → End your stream           │
│  • status   → Check stream status       │
│  • help     → Show help                 │
├─────────────────────────────────────────┤
│  SUPPORTED SITES                        │
│  ✓ YouTube  ✓ Twitch  ✓ Vimeo          │
│  ✓ Wikipedia  ✓ Most other URLs        │
└─────────────────────────────────────────┘
```

---

Happy streaming! 🎬🍿
