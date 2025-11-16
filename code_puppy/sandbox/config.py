"""
Configuration management for sandboxing.
"""

import json
import logging
from pathlib import Path
from typing import Optional, Set

logger = logging.getLogger(__name__)


class SandboxConfig:
    """Manages sandbox configuration and persistence."""

    def __init__(self, config_dir: Optional[Path] = None):
        """
        Initialize sandbox configuration.

        Args:
            config_dir: Directory to store sandbox config (default: ~/.code_puppy)
        """
        if config_dir is None:
            config_dir = Path.home() / ".code_puppy"

        self.config_dir = config_dir
        self.config_file = self.config_dir / "sandbox_config.json"

        # Default configuration
        self._config = {
            "enabled": False,  # Opt-in by default
            "filesystem_isolation": True,
            "network_isolation": True,
            "allowed_domains": [],
            "allowed_read_paths": [],
            "allowed_write_paths": [],
            "require_approval_for_new_domains": True,
            "proxy_port": 9050,
        }

        # Load existing configuration
        self._load()

    def _load(self):
        """Load configuration from disk."""
        if self.config_file.exists():
            try:
                with open(self.config_file) as f:
                    loaded = json.load(f)
                    self._config.update(loaded)
            except Exception as e:
                logger.warning(f"Failed to load sandbox config: {e}")

    def save(self):
        """Save configuration to disk."""
        try:
            self.config_dir.mkdir(parents=True, exist_ok=True)
            with open(self.config_file, "w") as f:
                json.dump(self._config, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save sandbox config: {e}")

    @property
    def enabled(self) -> bool:
        """Check if sandboxing is enabled."""
        return self._config.get("enabled", False)

    @enabled.setter
    def enabled(self, value: bool):
        """Enable or disable sandboxing."""
        self._config["enabled"] = value
        self.save()

    @property
    def filesystem_isolation(self) -> bool:
        """Check if filesystem isolation is enabled."""
        return self._config.get("filesystem_isolation", True)

    @filesystem_isolation.setter
    def filesystem_isolation(self, value: bool):
        """Enable or disable filesystem isolation."""
        self._config["filesystem_isolation"] = value
        self.save()

    @property
    def network_isolation(self) -> bool:
        """Check if network isolation is enabled."""
        return self._config.get("network_isolation", True)

    @network_isolation.setter
    def network_isolation(self, value: bool):
        """Enable or disable network isolation."""
        self._config["network_isolation"] = value
        self.save()

    @property
    def allowed_domains(self) -> Set[str]:
        """Get the set of allowed domains."""
        return set(self._config.get("allowed_domains", []))

    def add_allowed_domain(self, domain: str):
        """Add a domain to the allowlist."""
        domains = self._config.get("allowed_domains", [])
        if domain not in domains:
            domains.append(domain)
            self._config["allowed_domains"] = domains
            self.save()

    def remove_allowed_domain(self, domain: str):
        """Remove a domain from the allowlist."""
        domains = self._config.get("allowed_domains", [])
        if domain in domains:
            domains.remove(domain)
            self._config["allowed_domains"] = domains
            self.save()

    @property
    def allowed_read_paths(self) -> list[str]:
        """Get the list of allowed read paths."""
        return self._config.get("allowed_read_paths", [])

    def add_allowed_read_path(self, path: str):
        """Add a path to the read allowlist."""
        paths = self._config.get("allowed_read_paths", [])
        abs_path = str(Path(path).resolve())
        if abs_path not in paths:
            paths.append(abs_path)
            self._config["allowed_read_paths"] = paths
            self.save()

    @property
    def allowed_write_paths(self) -> list[str]:
        """Get the list of allowed write paths."""
        return self._config.get("allowed_write_paths", [])

    def add_allowed_write_path(self, path: str):
        """Add a path to the write allowlist."""
        paths = self._config.get("allowed_write_paths", [])
        abs_path = str(Path(path).resolve())
        if abs_path not in paths:
            paths.append(abs_path)
            self._config["allowed_write_paths"] = paths
            self.save()

    @property
    def require_approval_for_new_domains(self) -> bool:
        """Check if approval is required for new domains."""
        return self._config.get("require_approval_for_new_domains", True)

    @require_approval_for_new_domains.setter
    def require_approval_for_new_domains(self, value: bool):
        """Set whether approval is required for new domains."""
        self._config["require_approval_for_new_domains"] = value
        self.save()

    @property
    def proxy_port(self) -> int:
        """Get the proxy port."""
        return self._config.get("proxy_port", 9050)

    @proxy_port.setter
    def proxy_port(self, value: int):
        """Set the proxy port."""
        self._config["proxy_port"] = value
        self.save()

    def get_status(self) -> dict:
        """Get current sandbox status as a dictionary."""
        return {
            "enabled": self.enabled,
            "filesystem_isolation": self.filesystem_isolation,
            "network_isolation": self.network_isolation,
            "allowed_domains_count": len(self.allowed_domains),
            "allowed_read_paths": self.allowed_read_paths,
            "allowed_write_paths": self.allowed_write_paths,
            "require_approval": self.require_approval_for_new_domains,
            "proxy_port": self.proxy_port,
        }
