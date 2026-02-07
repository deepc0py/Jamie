"""
HTTP client for communicating with the CUA Controller.

This module provides an async HTTP client that sends streaming requests
to the CUA Controller and handles responses.

Classes:
    CUAClient: Async HTTP client for CUA Controller API
    CUAError: Exception for CUA communication failures
"""

from typing import Optional


class CUAError(Exception):
    """Exception raised when CUA Controller communication fails."""
    
    def __init__(self, message: str, error_code: Optional[str] = None):
        super().__init__(message)
        self.error_code = error_code


class CUAClient:
    """
    Async HTTP client for CUA Controller communication.
    
    Provides methods to:
        - Start a new streaming session
        - Stop an active session
        - Check controller health
    
    Uses aiohttp for async HTTP requests with configurable timeouts.
    
    Attributes:
        base_url: CUA Controller base URL
        timeout: Request timeout in seconds
    
    Methods:
        start_stream: Send stream request, returns session info
        stop_stream: Request session termination
        health_check: Verify controller is responsive
        close: Clean up HTTP session resources
    """
    
    def __init__(self, base_url: str, timeout: float = 30.0):
        """
        Initialize the CUA client.
        
        Args:
            base_url: CUA Controller base URL (e.g., http://localhost:8000)
            timeout: Request timeout in seconds
        """
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        # TODO: Initialize aiohttp.ClientSession
    
    # TODO: Implement API methods
    pass
