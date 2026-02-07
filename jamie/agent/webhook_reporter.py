"""Webhook status reporter for CUA agent."""

import asyncio
from typing import Optional
import aiohttp
from datetime import datetime

from jamie.shared.models import StatusUpdate, StreamStatus
from jamie.shared.logging import get_logger

log = get_logger(__name__)

# Retry configuration
MAX_RETRIES = 3
TOTAL_TIMEOUT = 30  # seconds
# Exponential backoff delays: 1s, 2s, 4s
BACKOFF_DELAYS = [1.0, 2.0, 4.0]


class WebhookReporter:
    """Reports status updates to the bot via webhook."""
    
    def __init__(self, webhook_url: Optional[str] = None):
        self.webhook_url = webhook_url
        self._session: Optional[aiohttp.ClientSession] = None
    
    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            timeout = aiohttp.ClientTimeout(total=TOTAL_TIMEOUT)
            self._session = aiohttp.ClientSession(timeout=timeout)
        return self._session
    
    async def close(self) -> None:
        if self._session and not self._session.closed:
            await self._session.close()
    
    async def report(
        self,
        session_id: str,
        status: str,
        message: str = "",
        error_code: Optional[str] = None,
        details: Optional[dict] = None,
    ) -> bool:
        """Send status update to webhook with retry logic.
        
        Uses exponential backoff: 1s, 2s, 4s delays between retries.
        Max 3 retries with 30s total timeout.
        
        Returns True if successful.
        """
        
        if not self.webhook_url:
            log.debug("no_webhook_url", session_id=session_id)
            return True  # Not an error, just no webhook configured
        
        # Map string status to StreamStatus enum
        try:
            stream_status = StreamStatus(status)
        except ValueError:
            stream_status = StreamStatus.STREAMING  # fallback
        
        update = StatusUpdate(
            session_id=session_id,
            status=stream_status,
            message=message,
            timestamp=datetime.utcnow(),
            error_code=error_code,
            details=details,
        )
        
        last_error: Optional[Exception] = None
        
        for attempt in range(MAX_RETRIES):
            try:
                session = await self._get_session()
                async with session.post(
                    self.webhook_url,
                    json=update.model_dump(mode="json"),
                ) as resp:
                    if resp.status == 200:
                        log.info("webhook_sent", session_id=session_id, status=status)
                        return True
                    else:
                        # Non-200 response - retry if we have attempts left
                        last_error = Exception(f"HTTP {resp.status}")
                        if attempt < MAX_RETRIES - 1:
                            delay = BACKOFF_DELAYS[attempt]
                            log.warning(
                                "webhook_failed_retrying",
                                session_id=session_id,
                                status_code=resp.status,
                                attempt=attempt + 1,
                                max_retries=MAX_RETRIES,
                                delay=delay,
                            )
                            await asyncio.sleep(delay)
                        else:
                            log.warning(
                                "webhook_failed",
                                session_id=session_id,
                                status_code=resp.status,
                            )
            except Exception as e:
                last_error = e
                if attempt < MAX_RETRIES - 1:
                    delay = BACKOFF_DELAYS[attempt]
                    log.warning(
                        "webhook_error_retrying",
                        session_id=session_id,
                        error=str(e),
                        attempt=attempt + 1,
                        max_retries=MAX_RETRIES,
                        delay=delay,
                    )
                    await asyncio.sleep(delay)
                else:
                    log.error(
                        "webhook_error",
                        session_id=session_id,
                        error=str(e),
                        attempts_exhausted=True,
                    )
        
        return False
    
    async def __aenter__(self) -> "WebhookReporter":
        return self
    
    async def __aexit__(self, *args) -> None:
        await self.close()
