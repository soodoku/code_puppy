"""
Base classes and interfaces for sandbox implementations.
"""

import platform
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional


@dataclass
class SandboxOptions:
    """Options for sandbox execution."""

    # Filesystem isolation
    filesystem_isolation: bool = True
    allowed_read_paths: list[str] = None
    allowed_write_paths: list[str] = None

    # Network isolation
    network_isolation: bool = True
    proxy_socket_path: Optional[str] = None

    # Working directory for the command
    cwd: str = "."

    # Environment variables
    env: Optional[dict[str, str]] = None

    def __post_init__(self):
        """Initialize default values."""
        if self.allowed_read_paths is None:
            self.allowed_read_paths = []
        if self.allowed_write_paths is None:
            self.allowed_write_paths = []


class FilesystemIsolator(ABC):
    """Abstract base class for filesystem isolation implementations."""

    @abstractmethod
    def is_available(self) -> bool:
        """Check if the isolation mechanism is available on this system."""
        pass

    @abstractmethod
    def wrap_command(
        self,
        command: str,
        options: SandboxOptions,
    ) -> tuple[str, dict[str, str]]:
        """
        Wrap a command with filesystem isolation.

        Args:
            command: The shell command to wrap
            options: Sandbox configuration options

        Returns:
            Tuple of (wrapped_command, environment_dict)
        """
        pass

    @abstractmethod
    def get_platform(self) -> str:
        """Get the platform this isolator supports."""
        pass


def get_current_platform() -> str:
    """Get the current platform name."""
    system = platform.system().lower()
    if system == "darwin":
        return "macos"
    return system
