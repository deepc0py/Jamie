"""Webhook receiver for CUA agent status updates."""

from aiohttp import web
from typing import Callable, Awaitable, Optional
import asyncio

from jamie.shared.models import StatusUpdate, HealthResponse
from jamie.shared.logging import get_logger

log = get_logger(__name__)


StatusCallback = Callable[[StatusUpdate], Awaitable[None]]


class WebhookReceiver:
    """Receives status updates from CUA agent via HTTP webhooks."""
    
    def __init__(
        self,
        host: str = "0.0.0.0",
        port: int = 8080,
        callback: Optional[StatusCallback] = None,
    ):
        self.host = host
        self.port = port
        self.callback = callback
        self._app: Optional[web.Application] = None
        self._runner: Optional[web.AppRunner] = None
        self._site: Optional[web.TCPSite] = None
    
    async def start(self) -> None:
        """Start the webhook server."""
        self._app = web.Application()
        self._app.router.add_post("/webhook/status", self._handle_status)
        self._app.router.add_get("/health", self._handle_health)
        
        self._runner = web.AppRunner(self._app)
        await self._runner.setup()
        
        self._site = web.TCPSite(self._runner, self.host, self.port)
        await self._site.start()
        
        log.info("webhook_started", host=self.host, port=self.port)
    
    async def stop(self) -> None:
        """Stop the webhook server."""
        if self._runner:
            await self._runner.cleanup()
            log.info("webhook_stopped")
    
    async def _handle_status(self, request: web.Request) -> web.Response:
        """Handle status update from CUA agent."""
        try:
            data = await request.json()
            update = StatusUpdate(**data)
            
            log.info(
                "status_received",
                session_id=update.session_id,
                status=update.status,
            )
            
            if self.callback:
                await self.callback(update)
            
            return web.json_response({"status": "ok"})
        except Exception as e:
            log.error("webhook_error", error=str(e))
            return web.json_response(
                {"status": "error", "message": str(e)},
                status=400
            )
    
    async def _handle_health(self, request: web.Request) -> web.Response:
        """Health check endpoint."""
        response = HealthResponse(
            status="healthy",
            version="0.1.0",
            active_sessions=0,  # Webhook receiver doesn't track sessions
        )
        return web.json_response(response.model_dump())
    
    def set_callback(self, callback: StatusCallback) -> None:
        """Set the callback for status updates."""
        self.callback = callback
