"""Discord automation prompts for CUA agent.

These prompts provide step-by-step instructions for the vision-language model
to automate Discord interactions. Each prompt includes:
- Clear goal statement
- Step-by-step instructions
- Verification steps
- Error handling guidance

Placeholders use {placeholder_name} format for dynamic values.
"""

# =============================================================================
# LOGIN PROMPT
# =============================================================================

DISCORD_LOGIN_PROMPT = """
You are automating Discord login in a browser.

GOAL: Log into Discord with the provided credentials.

CURRENT STATE: Browser open at discord.com/login

CREDENTIALS:
- Email: {email}
- Password: {password}

STEPS:
1. Locate the email/phone input field (labeled "Email or Phone Number")
2. Click on the email input field to focus it
3. Type the email address: {email}
4. Locate the password input field (labeled "Password")
5. Click on the password field to focus it
6. Type the password: {password}
7. Click the "Log In" button (blue button below the password field)
8. Wait for Discord to load (3-5 seconds)

VERIFICATION:
- After login, you should see the Discord app interface
- The left sidebar should show the server list (vertical strip of server icons)
- If you see the server list, report: LOGIN_SUCCESS

ERROR HANDLING:
- If you see "Invalid login credentials" → report: LOGIN_FAILED_INVALID_CREDENTIALS
- If you see a CAPTCHA challenge → report: LOGIN_FAILED_CAPTCHA
- If you see "New login location" or 2FA/verification prompt → report: LOGIN_FAILED_2FA_REQUIRED
- If you see "Too many login attempts" → report: LOGIN_FAILED_RATE_LIMITED
- If the page doesn't load → report: LOGIN_FAILED_PAGE_ERROR
- If any step fails after 3 attempts → report: LOGIN_FAILED_UNKNOWN

IMPORTANT:
- Do NOT click any "Download" or "Get Discord for..." buttons
- Do NOT dismiss or accept cookie banners if they appear (work around them)
- Take a screenshot after each major step to verify progress
"""

# =============================================================================
# JOIN VOICE CHANNEL PROMPT
# =============================================================================

JOIN_VOICE_CHANNEL_PROMPT = """
You are automating Discord to join a voice channel.

GOAL: Join the specified voice channel in the specified server.

TARGET:
- Server: {server_name}
- Voice Channel: {channel_name}

STEPS:
1. Look at the left sidebar for the server list (vertical strip of circular server icons)
2. Find and click the server icon for "{server_name}"
   - Hover over icons to see server names in tooltips if needed
   - The server icon may show the first letter(s) of the server name
3. Wait for the server's channel list to load (shows in the channel sidebar)
4. Scroll through the channel list if needed to find the voice channel
5. Look for "{channel_name}" with a speaker/audio icon (🔊) next to it
6. Click on the voice channel "{channel_name}" to join
7. Wait for the connection to establish (1-2 seconds)

VERIFICATION:
- Your username should appear under the voice channel name
- You should see voice controls at the bottom (mute, deafen, disconnect buttons)
- A green/connected indicator may appear
- Report: JOINED_CHANNEL

ERROR HANDLING:
- If server not found in sidebar → scroll the server list, then report: SERVER_NOT_FOUND
- If voice channel not found in channel list → scroll channel list, then report: CHANNEL_NOT_FOUND
- If channel is locked (🔒 icon) → report: CHANNEL_LOCKED
- If prompted for microphone permission → click "Allow" and continue
- If connection fails repeatedly → report: CONNECTION_FAILED
- If you see "You must verify your phone" → report: PHONE_VERIFICATION_REQUIRED

IMPORTANT:
- Voice channels have a speaker icon (🔊), text channels have a hash (#)
- The channel may be inside a category - expand categories by clicking them
- Take a screenshot after joining to confirm your presence in the channel
"""

# =============================================================================
# OPEN URL IN NEW TAB PROMPT
# =============================================================================

OPEN_URL_IN_NEW_TAB_PROMPT = """
You are automating a browser to open a URL in a new tab.

GOAL: Open the specified URL in a new browser tab and prepare it for streaming.

URL TO OPEN: {url}

STEPS:
1. Open a new browser tab using keyboard shortcut Ctrl+T
2. Wait for the new tab to open and the address bar to be focused
3. Type the URL: {url}
4. Press Enter to navigate to the URL
5. Wait for the page to fully load (watch for loading indicators to stop)

FOR VIDEO CONTENT (YouTube, Twitch, Vimeo):
6. Wait for the video player to initialize
7. If the video doesn't auto-play, locate and click the play button
8. If there's an ad, wait for it to finish or click "Skip Ad" when available
9. Optionally expand to theater mode for better viewing (if available)

FOR OTHER CONTENT:
6. Wait for all content to load
7. Scroll if needed to see the main content

VERIFICATION:
- The URL bar should show the expected domain
- For videos: the player should be visible and playing
- For other content: the page should be fully rendered
- Report: URL_LOADED

ERROR HANDLING:
- If "This site can't be reached" → report: URL_UNREACHABLE
- If "Video unavailable" → report: VIDEO_UNAVAILABLE
- If age verification required → report: AGE_VERIFICATION_REQUIRED
- If login/subscription wall → report: LOGIN_REQUIRED
- If region blocked → report: REGION_BLOCKED
- If page loads but content fails → report: CONTENT_LOAD_FAILED

IMPORTANT:
- Don't close the Discord tab - we need both tabs open
- Make sure audio/video is playing before proceeding
- Take a screenshot to confirm the content is ready
"""

# =============================================================================
# START SCREEN SHARE PROMPT
# =============================================================================

START_SCREEN_SHARE_PROMPT = """
You are automating Discord to start screen sharing in a voice channel.

GOAL: Share the browser tab containing streaming content to the voice channel.

PRECONDITIONS:
- You must already be connected to a voice channel
- The content tab (YouTube/Twitch/etc) must already be open

STEPS:
1. Switch to the Discord tab (use Ctrl+Tab or click the Discord tab)
2. Confirm you're still connected to the voice channel (see voice controls at bottom)
3. Locate the screen share button in the voice controls area
   - It looks like a monitor with an arrow (📺 or 🖥️)
   - Usually between the video and disconnect buttons
4. Click the "Share Your Screen" button
5. A screen picker dialog will appear with options:
   - "Screens" tab - shows full monitors
   - "Windows" tab - shows application windows
   - "Browser tabs" or "Chrome Tab"/"Firefox Tab" - shows individual tabs
6. Click on the tab containing the streaming content ({url})
   - Look for the thumbnail matching your content
7. IMPORTANT: If there's an "Also share tab audio" or "Share audio" checkbox, make sure it's CHECKED
8. Click the "Share" or "Go Live" button (usually blue)
9. Wait for the stream to start (1-2 seconds)

VERIFICATION:
- You should see a small preview of your stream in Discord
- The screen share button may change appearance (highlight or different icon)
- Other users in the channel should see "LIVE" or streaming indicator next to your name
- Report: SCREEN_SHARE_STARTED

ERROR HANDLING:
- If screen share button not visible → report: SCREEN_SHARE_BUTTON_NOT_FOUND
- If picker dialog doesn't appear → try clicking the button again, then report: PICKER_FAILED
- If target tab not in picker → report: TAB_NOT_FOUND_IN_PICKER
- If "Share" button is grayed out → report: SHARE_NOT_AVAILABLE
- If permission denied → report: PERMISSION_DENIED
- If stream starts but no audio → report: AUDIO_NOT_SHARED

IMPORTANT:
- Audio sharing is critical - make sure "Share audio" is enabled if available
- The tab MUST be the active/focused tab in that browser window to appear in picker
- Take a screenshot after sharing to confirm the stream preview is visible
"""

# =============================================================================
# STOP SCREEN SHARE PROMPT
# =============================================================================

STOP_SCREEN_SHARE_PROMPT = """
You are automating Discord to stop an active screen share.

GOAL: Stop the current screen share/stream.

PRECONDITIONS:
- You must currently be screen sharing/streaming

STEPS:
1. Switch to the Discord tab if not already there
2. Locate the stop sharing option. It can be found in one of these places:
   a. A "Stop Streaming" button in the stream preview window
   b. A red "Stop" button in the voice controls area at the bottom
   c. Click the screen share button again (it should offer a stop option)
   d. A popup/overlay near the screen share preview
3. Click "Stop Streaming" or "Stop Sharing"
4. Wait for the stream to end (1-2 seconds)

VERIFICATION:
- The stream preview should disappear
- The screen share button should return to its normal/inactive state
- You should still be connected to the voice channel
- Report: SCREEN_SHARE_STOPPED

ERROR HANDLING:
- If you can't find the stop button → try clicking the screen share button in voice controls
- If clicking doesn't stop the stream → try Escape key to close any popups first
- If stream won't stop → report: STOP_FAILED
- If you're disconnected from voice after stopping → report: DISCONNECTED_AFTER_STOP

IMPORTANT:
- This only stops screen sharing - you should remain in the voice channel
- Take a screenshot to confirm the stream preview is gone
"""

# =============================================================================
# LEAVE VOICE CHANNEL PROMPT
# =============================================================================

LEAVE_VOICE_CHANNEL_PROMPT = """
You are automating Discord to leave the current voice channel.

GOAL: Disconnect from the voice channel cleanly.

PRECONDITIONS:
- You must currently be connected to a voice channel

STEPS:
1. Switch to the Discord tab if not already there
2. Look at the voice controls area at the bottom of the screen
3. Find the disconnect button:
   - It looks like a phone with an X (📞❌) 
   - Usually red or turns red on hover
   - Located in the voice control bar next to mute/deafen buttons
4. Click the disconnect button
5. Wait for disconnection to complete (1-2 seconds)

VERIFICATION:
- The voice controls bar at the bottom should disappear or collapse
- You should no longer see yourself under any voice channel
- The voice channel should no longer show you as a member
- Report: LEFT_CHANNEL

ERROR HANDLING:
- If disconnect button not visible → scroll down or look for collapsed voice panel
- If clicking doesn't disconnect → try pressing Escape key first, then retry
- If still connected after clicking → report: DISCONNECT_FAILED
- If error message appears → report the error message

IMPORTANT:
- If screen sharing is active, it will stop automatically when you leave
- Make sure to actually click the disconnect button, not the mute or deafen buttons
- Take a screenshot to confirm you're no longer in the voice channel
"""

# =============================================================================
# HELPER/UTILITY PROMPTS
# =============================================================================

TAKE_SCREENSHOT_PROMPT = """
Take a screenshot of the current screen state.

GOAL: Capture the current state for verification.

STEPS:
1. Take a screenshot of the entire visible screen
2. Report what you observe in the screenshot

REPORT FORMAT:
Describe:
- What application/website is currently visible
- Key UI elements you can see
- Any error messages or dialogs
- Current state relevant to the streaming task
"""

HANDLE_ERROR_PROMPT = """
An error occurred during automation. Attempt recovery.

ERROR CONTEXT: {error_description}

RECOVERY STEPS:
1. Take a screenshot to assess current state
2. Based on the current state, determine if:
   a. The error is recoverable (retry the failed action)
   b. A different approach is needed
   c. The error is unrecoverable (report for human intervention)

FOR COMMON ERRORS:
- Page not responding → Try refreshing (F5 or Ctrl+R)
- Dialog/popup blocking → Press Escape or click outside to dismiss
- Wrong tab focused → Use Ctrl+Tab to switch tabs
- Element not found → Scroll the page to find it
- Network error → Wait 5 seconds and retry

REPORT:
- RECOVERED: if you successfully recovered and can continue
- NEEDS_RETRY: if the specific step should be retried
- UNRECOVERABLE: if human intervention is needed (explain why)
"""
