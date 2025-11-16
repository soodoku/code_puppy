"""
macOS filesystem isolation using sandbox-exec.
"""

import os
import shlex
import shutil
import tempfile
from pathlib import Path

from .base import FilesystemIsolator, SandboxOptions


class SandboxExecIsolator(FilesystemIsolator):
    """Filesystem isolation using sandbox-exec on macOS."""

    def is_available(self) -> bool:
        """Check if sandbox-exec is available on the system."""
        return shutil.which("sandbox-exec") is not None

    def get_platform(self) -> str:
        """Get the platform this isolator supports."""
        return "macos"

    def _generate_sandbox_profile(self, options: SandboxOptions) -> str:
        """
        Generate a sandbox profile in Scheme for sandbox-exec.

        Args:
            options: Sandbox configuration options

        Returns:
            Sandbox profile as a string
        """
        cwd = os.path.abspath(options.cwd)

        # Build allowed read paths list
        allowed_read = [cwd] + [os.path.abspath(p) for p in options.allowed_read_paths]

        # Build allowed write paths list
        allowed_write = [cwd] + [os.path.abspath(p) for p in options.allowed_write_paths]

        # Create the sandbox profile in Scheme
        profile = """(version 1)

;; Deny everything by default
(deny default)

;; Allow basic system operations
(allow process-exec*)
(allow process-fork)
(allow signal)
(allow sysctl-read)
(allow mach-lookup)
(allow ipc-posix-shm)

;; Allow network access (for proxy)
(allow network*)

;; Allow reading from essential system directories
(allow file-read*
    (subpath "/usr/lib")
    (subpath "/usr/bin")
    (subpath "/usr/share")
    (subpath "/bin")
    (subpath "/sbin")
    (subpath "/System/Library")
    (subpath "/Library")
    (subpath "/private/var/db/timezone")
    (subpath "/dev")
)

;; Allow temporary file access
(allow file*
    (subpath "/tmp")
    (subpath "/private/tmp")
    (subpath "/var/tmp")
)

"""

        # Add allowed read paths
        for path in allowed_read:
            profile += f';; Allow read access to: {path}\n'
            profile += f'(allow file-read*\n    (subpath "{path}")\n)\n\n'

        # Add allowed write paths
        for path in allowed_write:
            profile += f';; Allow read-write access to: {path}\n'
            profile += f'(allow file*\n    (subpath "{path}")\n)\n\n'

        # Block access to sensitive directories
        profile += """;; Explicitly deny access to sensitive directories
(deny file*
    (subpath (string-append (param "HOME") "/.ssh"))
    (subpath (string-append (param "HOME") "/.aws"))
    (subpath (string-append (param "HOME") "/.config"))
    (subpath (string-append (param "HOME") "/.gnupg"))
)
"""

        return profile

    def wrap_command(
        self,
        command: str,
        options: SandboxOptions,
    ) -> tuple[str, dict[str, str]]:
        """
        Wrap a command with sandbox-exec isolation.

        Args:
            command: The shell command to wrap
            options: Sandbox configuration options

        Returns:
            Tuple of (wrapped_command, environment_dict)
        """
        # Generate the sandbox profile
        profile = self._generate_sandbox_profile(options)

        # Write profile to a temporary file
        # We'll use a predictable path so it can be cleaned up
        profile_dir = Path(tempfile.gettempdir()) / "code_puppy_sandbox"
        profile_dir.mkdir(exist_ok=True)

        profile_file = profile_dir / f"profile_{os.getpid()}.sb"
        profile_file.write_text(profile)

        # Build the sandbox-exec command
        sandbox_args = [
            "sandbox-exec",
            "-f", str(profile_file),
        ]

        # Set HOME parameter for the profile
        env_vars = options.env or {}
        home = env_vars.get("HOME") or os.environ.get("HOME", str(Path.home()))

        # Add parameters for the sandbox profile
        sandbox_args.extend([
            "-D", f"HOME={home}",
        ])

        # Add the shell command to execute
        sandbox_args.extend([
            "/bin/sh",
            "-c",
            command,
        ])

        wrapped_command = " ".join(shlex.quote(arg) for arg in sandbox_args)

        # Add proxy environment variables if network isolation is enabled
        if options.network_isolation and options.proxy_socket_path:
            proxy_url = "socks5://localhost:9050"
            env_vars.update({
                "HTTP_PROXY": proxy_url,
                "HTTPS_PROXY": proxy_url,
                "http_proxy": proxy_url,
                "https_proxy": proxy_url,
            })

        return wrapped_command, env_vars
