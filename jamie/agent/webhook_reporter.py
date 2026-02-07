"""Webhook status reporter for CUA agent."""

from typing import Optional
import aiohttp
from datetime import datetime

from jamie.shared.models import StatusUpdate, StreamStatus
from jamie.shared.logging import get_logger

log = get_logger(__name__)


class WebhookReporter:
    """Reports status updates to the bot via webhook."""
    
    def __init__(self, webhook_url: Optional[str] = None):
        self.webhook_url = webhook_url
        self._session: Optional[aiohttp.ClientSession] = None
    
    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
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
        """Send status update to webhook. Returns True if successful."""
        
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
        
        try:
            session = await self._get_session()
            async with session.post(
                self.webhook_url,
                json=update.model_dump(mode="json"),
                timeout=aiohttp.ClientTimeout(total=10),
            ) as resp:
                if resp.status == 200:
                    log.info("webhook_sent", session_id=session_id, status=status)
                    return True
                else:
                    log.warning(
                        "webhook_failed",
                        session_id=session_id,
                        status_code=resp.status,
                    )
                    return False
        except Exception as e:
            log.error("webhook_error", session_id=session_id, error=str(e))
            return False
    
    async def __aenter__(self) -> "WebhookReporter":
        return self
    
    async def __aexit__(self, *args) -> None:
        await self.close()
