"""HTTP client for CUA agent controller."""

import asyncio
from dataclasses import dataclass
from typing import Callable, Optional, TypeVar

import aiohttp

from jamie.shared.errors import ErrorCode, JamieError, is_retryable


class CUAClientError(JamieError):
    """Error communicating with CUA controller."""

    pass


@dataclass
class CUAClientConfig:
    """Configuration for CUA client."""

    base_url: str = "http://localhost:8000"
    timeout: int = 30
    max_retries: int = 3
    retry_delay: float = 1.0


# Type variable for retry return type
T = TypeVar("T")


class CUAClient:
    """HTTP client for CUA agent controller.

    Provides async methods for communicating with the CUA controller:
    - health_check: Verify controller is healthy
    - start_stream: Request a new streaming session
    - stop_stream: Stop an active streaming session

    Supports automatic retries for transient failures and proper
    session lifecycle management via async context manager.

    Example:
        async with CUAClient(config) as client:
            health = await client.health_check()
            response = await client.start_stream(request)
    """

    def __init__(self, config: Optional[CUAClientConfig] = None):
        self.config = config or CUAClientConfig()
        self._session: Optional[aiohttp.ClientSession] = None

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session."""
        if self._session is None or self._session.closed:
            timeout = aiohttp.ClientTimeout(total=self.config.timeout)
            self._session = aiohttp.ClientSession(timeout=timeout)
        return self._session

    async def close(self) -> None:
        """Close the HTTP session."""
        if self._session and not self._session.closed:
            await self._session.close()

    async def _retry(
        self,
        operation: Callable[[], T],
        error_code: ErrorCode = ErrorCode.CUA_UNAVAILABLE,
    ) -> T:
        """Execute operation with retry logic for transient failures.

        Args:
            operation: Async callable to execute
            error_code: Default error code if all retries fail

        Returns:
            Result of the operation

        Raises:
            CUAClientError: If all retries fail
        """
        last_error: Optional[Exception] = None

        for attempt in range(self.config.max_retries):
            try:
                return await operation()
            except CUAClientError as e:
                last_error = e
                # Only retry if the error is retryable
                if not is_retryable(e.code):
                    raise
                # Don't sleep on the last attempt
                if attempt < self.config.max_retries - 1:
                    await asyncio.sleep(
                        self.config.retry_delay * (attempt + 1)  # Linear backoff
                    )
            except aiohttp.ClientError as e:
                last_error = e
                # Connection errors are transient, retry
                if attempt < self.config.max_retries - 1:
                    await asyncio.sleep(self.config.retry_delay * (attempt + 1))

        # All retries exhausted
        if isinstance(last_error, CUAClientError):
            raise last_error
        raise CUAClientError(
            code=error_code,
            message=f"All {self.config.max_retries} retries failed: {last_error}",
        )

    async def health_check(self) -> "HealthResponse":
        """Check if CUA controller is healthy.

        Returns:
            HealthResponse with controller status

        Raises:
            CUAClientError: If health check fails
        """
        from jamie.shared.models import HealthResponse

        async def _do_health_check() -> HealthResponse:
            session = await self._get_session()
            try:
                async with session.get(f"{self.config.base_url}/health") as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        return HealthResponse(**data)
                    raise CUAClientError(
                        code=ErrorCode.CUA_UNAVAILABLE,
                        message=f"Health check failed with status {resp.status}",
                    )
            except aiohttp.ClientError as e:
                raise CUAClientError(
                    code=ErrorCode.CUA_UNAVAILABLE,
                    message=f"Cannot connect to CUA: {e}",
                )

        return await self._retry(_do_health_check)

    async def start_stream(self, request: "StreamRequest") -> "StreamResponse":
        """Request CUA to start streaming.

        Args:
            request: Stream request with URL and channel details

        Returns:
            StreamResponse with session status

        Raises:
            CUAClientError: If stream request fails
        """
        from jamie.shared.models import StreamResponse

        async def _do_start_stream() -> StreamResponse:
            session = await self._get_session()
            try:
                async with session.post(
                    f"{self.config.base_url}/stream",
                    json=request.model_dump(mode="json"),
                ) as resp:
                    data = await resp.json()
                    if resp.status == 200:
                        return StreamResponse(**data)
                    # Map HTTP status to error code
                    if resp.status == 409:
                        error_code = ErrorCode.ALREADY_STREAMING
                    elif resp.status == 400:
                        error_code = ErrorCode.INVALID_URL
                    else:
                        error_code = ErrorCode.CUA_UNAVAILABLE
                    raise CUAClientError(
                        code=error_code,
                        message=f"Stream request failed: {data.get('detail', 'Unknown error')}",
                    )
            except aiohttp.ClientError as e:
                raise CUAClientError(
                    code=ErrorCode.CUA_UNAVAILABLE,
                    message=f"Cannot connect to CUA: {e}",
                )

        return await self._retry(_do_start_stream)

    async def stop_stream(
        self, session_id: str, requester_id: str
    ) -> "StreamResponse":
        """Request CUA to stop streaming.

        Args:
            session_id: ID of the session to stop
            requester_id: ID of the user requesting the stop

        Returns:
            StreamResponse with final session status

        Raises:
            CUAClientError: If stop request fails
        """
        from jamie.shared.models import StopRequest, StreamResponse

        async def _do_stop_stream() -> StreamResponse:
            session = await self._get_session()
            request = StopRequest(session_id=session_id, requester_id=requester_id)
            try:
                async with session.post(
                    f"{self.config.base_url}/stop/{session_id}",
                    json=request.model_dump(mode="json"),
                ) as resp:
                    data = await resp.json()
                    if resp.status in (200, 204):
                        return StreamResponse(**data)
                    raise CUAClientError(
                        code=ErrorCode.CUA_UNAVAILABLE,
                        message=f"Stop request failed: {data.get('detail', 'Unknown error')}",
                    )
            except aiohttp.ClientError as e:
                raise CUAClientError(
                    code=ErrorCode.CUA_UNAVAILABLE,
                    message=f"Cannot connect to CUA: {e}",
                )

        return await self._retry(_do_stop_stream)

    async def __aenter__(self) -> "CUAClient":
        """Enter async context manager."""
        return self

    async def __aexit__(self, *args) -> None:
        """Exit async context manager, closing session."""
        await self.close()
