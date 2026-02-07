"""
Pre-defined prompts for Discord automation tasks.

This module contains structured prompts that guide the CUA agent
through specific Discord operations. Each prompt provides clear
step-by-step instructions and expected outcomes.

Constants:
    DISCORD_LOGIN_PROMPT: Navigate to Discord and authenticate
    JOIN_VOICE_CHANNEL_PROMPT: Find and join a voice channel
    OPEN_URL_PROMPT: Open streaming content in new tab
    START_SCREEN_SHARE_PROMPT: Initiate Discord screen sharing
    STOP_SCREEN_SHARE_PROMPT: End screen share and leave voice
    HANDLE_DISCONNECT_PROMPT: Recover from unexpected disconnects
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


HANDLE_DISCONNECT_PROMPT = """
Handle an unexpected disconnect:

1. Check if you're still connected to voice
2. If disconnected, try rejoining: click the voice channel again
3. If screen share stopped, restart it using the "Share Your Screen" button
4. Report current status: RECONNECTED, FAILED_TO_RECONNECT, or STREAMING
"""
