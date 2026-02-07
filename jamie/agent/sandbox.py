"""CUA Sandbox management for Jamie agent."""

from typing import Optional
from dataclasses import dataclass
import asyncio

# CUA imports
from computer import Computer


@dataclass
class SandboxConfig:
    """Configuration for CUA sandbox."""
    
    os_type: str = "linux"
    provider_type: str = "docker"
    image: str = "trycua/cua-xfce:latest"
    display: str = "1024x768"
    memory: str = "4GB"
    cpu: str = "2"
    timeout: int = 120


class SandboxManager:
    """Manages CUA sandbox lifecycle."""
    
    def __init__(self, config: Optional[SandboxConfig] = None):
        self.config = config or SandboxConfig()
        self._computer: Optional[Computer] = None
        self._is_running: bool = False
    
    @property
    def is_running(self) -> bool:
        """Check if sandbox is running."""
        return self._is_running
    
    @property
    def computer(self) -> Optional[Computer]:
        """Get the CUA Computer instance."""
        return self._computer
    
    async def start(self) -> Computer:
        """Start the CUA sandbox and return Computer instance."""
        if self._is_running:
            raise RuntimeError("Sandbox already running")
        
        self._computer = Computer(
            os_type=self.config.os_type,
            provider_type=self.config.provider_type,
            image=self.config.image,
            display=self.config.display,
            memory=self.config.memory,
            cpu=self.config.cpu,
            timeout=self.config.timeout,
        )
        
        await self._computer.run()
        self._is_running = True
        return self._computer
    
    async def stop(self) -> None:
        """Stop the CUA sandbox."""
        if self._computer and self._is_running:
            await self._computer.stop()
            self._is_running = False
            self._computer = None
    
    async def restart(self) -> Computer:
        """Restart the sandbox."""
        await self.stop()
        return await self.start()
    
    async def __aenter__(self) -> Computer:
        """Context manager entry."""
        return await self.start()
    
    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit."""
        await self.stop()


async def create_sandbox(
    image: str = "trycua/cua-xfce:latest",
    display: str = "1024x768",
) -> SandboxManager:
    """Factory function to create a sandbox manager."""
    config = SandboxConfig(image=image, display=display)
    return SandboxManager(config)
