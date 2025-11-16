"""
Sandboxing module for code-puppy.

Provides filesystem and network isolation for shell command execution,
inspired by Anthropic's Claude Code sandboxing approach.

Supports:
- Linux: bubblewrap (bwrap) for filesystem isolation
- macOS: sandbox-exec for filesystem isolation
- All platforms: Network proxy for domain restriction
"""

from .command_wrapper import SandboxCommandWrapper
from .config import SandboxConfig
from .filesystem_isolation import get_filesystem_isolator

__all__ = [
    "SandboxCommandWrapper",
    "SandboxConfig",
    "get_filesystem_isolator",
]
