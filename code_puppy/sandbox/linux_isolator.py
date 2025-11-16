"""
Linux filesystem isolation using bubblewrap (bwrap).
"""

import os
import shlex
import shutil

from .base import FilesystemIsolator, SandboxOptions


class BubblewrapIsolator(FilesystemIsolator):
    """Filesystem isolation using bubblewrap on Linux."""

    def is_available(self) -> bool:
        """Check if bwrap is available on the system."""
        return shutil.which("bwrap") is not None

    def get_platform(self) -> str:
        """Get the platform this isolator supports."""
        return "linux"

    def wrap_command(
        self,
        command: str,
        options: SandboxOptions,
    ) -> tuple[str, dict[str, str]]:
        """
        Wrap a command with bubblewrap isolation.

        Args:
            command: The shell command to wrap
            options: Sandbox configuration options

        Returns:
            Tuple of (wrapped_command, environment_dict)
        """
        bwrap_args = ["bwrap"]

        # Core isolation settings
        bwrap_args.extend([
            "--unshare-all",  # Unshare all namespaces
            "--share-net",  # But keep network (for proxy)
            "--die-with-parent",  # Kill sandbox when parent dies
            "--new-session",  # New session to avoid signal leakage
        ])

        # Mount essential system directories (read-only)
        essential_paths = [
            "/usr",
            "/lib",
            "/lib64",
            "/bin",
            "/sbin",
        ]

        for path in essential_paths:
            if os.path.exists(path):
                bwrap_args.extend(["--ro-bind", path, path])

        # Mount /proc and /dev (required for most programs)
        bwrap_args.extend([
            "--proc", "/proc",
            "--dev", "/dev",
        ])

        # Create tmpfs for /tmp
        bwrap_args.extend(["--tmpfs", "/tmp"])

        # Get the working directory (resolve to absolute path)
        cwd = os.path.abspath(options.cwd)

        # Allow read-write access to working directory
        bwrap_args.extend(["--bind", cwd, cwd])

        # Add additional allowed read paths
        for read_path in options.allowed_read_paths:
            abs_path = os.path.abspath(read_path)
            if os.path.exists(abs_path):
                bwrap_args.extend(["--ro-bind", abs_path, abs_path])

        # Add additional allowed write paths
        for write_path in options.allowed_write_paths:
            abs_path = os.path.abspath(write_path)
            if os.path.exists(abs_path):
                bwrap_args.extend(["--bind", abs_path, abs_path])

        # Set working directory
        bwrap_args.extend(["--chdir", cwd])

        # Pass through specific environment variables
        env_vars = options.env or {}
        safe_env_vars = [
            "PATH",
            "HOME",
            "USER",
            "LANG",
            "LC_ALL",
            "TERM",
            "SHELL",
        ]

        for var in safe_env_vars:
            value = env_vars.get(var) or os.environ.get(var)
            if value:
                bwrap_args.extend(["--setenv", var, value])

        # Add proxy environment variables if network isolation is enabled
        if options.network_isolation and options.proxy_socket_path:
            proxy_url = "socks5://localhost:9050"  # Will be configured later
            bwrap_args.extend([
                "--setenv", "HTTP_PROXY", proxy_url,
                "--setenv", "HTTPS_PROXY", proxy_url,
                "--setenv", "http_proxy", proxy_url,
                "--setenv", "https_proxy", proxy_url,
            ])

        # Run the command via shell
        bwrap_args.extend([
            "--",
            "/bin/sh",
            "-c",
            command,
        ])

        wrapped_command = " ".join(shlex.quote(arg) for arg in bwrap_args)

        return wrapped_command, env_vars
