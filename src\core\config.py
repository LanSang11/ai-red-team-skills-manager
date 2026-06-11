"""Configuration management with YAML persistence and ecosystem auto-detection."""

import os
import yaml
from pathlib import Path
from typing import Any, Dict, Optional


# Sensible defaults - ecosystem auto-detection will override these
DEFAULT_CONFIG = {
    "shared_skills_path": str(Path.home() / "ai-red-team-skills" / "shared-skills"),
    "agents": {
        "claude-code": {
            "skills_path": str(Path.home() / ".claude" / "skills"),
            "format": "claude",
            "enabled": True,
        },
        "openclaw": {
            "skills_path": str(Path.home() / ".openclaw" / "skills"),
            "format": "openclaw",
            "enabled": True,
        },
        "hermes": {
            "skills_path": str(Path.home() / ".hermes" / "skills"),
            "format": "hermes",
            "enabled": True,
        },
    },
    "categories": {
        "security": [
            "security", "vulnerability", "exploit", "attack", "bypass",
            "injection", "xss", "csrf", "rce", "ssti", "idor", "jwt",
            "oauth", "red-team", "pentest", "c2", "payload", "shellcode",
        ],
        "recon": [
            "recon", "scan", "nmap", "osint", "intelligence", "discovery",
            "enumeration", "fofa", "subdomain", "asset",
        ],
        "tools": [
            "tool", "utility", "helper", "framework", "automation",
            "collaboration", "management", "search",
        ],
    },
    "auto_install": {
        "enabled": True,
        "trusted_sources": ["official", "well-known"],
        "auto_categories": ["security", "recon", "exploitation", "red-team"],
    },
    "audit": {
        "scan_depth": "full",
        "check_integrity": True,
        "check_prompt_injection": True,
        "suspicious_extensions": [".exe", ".bat", ".ps1", ".cmd", ".vbs", ".js"],
    },
    "log_file": str(Path.home() / ".ai-red-team-skills-manager" / "skills-manager.log"),
    "debug": False,
}


class Config:
    """Configuration manager with YAML persistence and ecosystem auto-detection.

    Supports dot-notation access: config.get("agents.claude-code.format")
    Auto-detects existing skills ecosystem on first run.
    """

    def __init__(self, config_path: Optional[str] = None):
        if config_path is None:
            config_path = str(
                Path.home() / ".ai-red-team-skills-manager" / "config.yaml"
            )
        self.config_path = Path(config_path)
        self.config: Dict[str, Any] = {}
        self._load_config()

    def _load_config(self):
        """Load configuration from file, create default if not exists."""
        # Start with defaults
        self.config = _deep_copy(DEFAULT_CONFIG)

        # Load from file if exists
        if self.config_path.exists():
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    loaded = yaml.safe_load(f)
                    if isinstance(loaded, dict):
                        _deep_merge(loaded, self.config)
            except Exception as e:
                print(f"Warning: Failed to load config: {e}. Using defaults.")

        # Auto-detect existing ecosystem
        self._detect_ecosystem()

        # Save if config file didn't exist
        if not self.config_path.exists():
            self._save_config()

    def _detect_ecosystem(self):
        """Auto-detect existing skills ecosystem and adjust config."""
        candidates = [
            Path.home() / "ai-red-team-skills" / "shared-skills",
            Path.home() / "ai-red-team-skills",
        ]

        for candidate in candidates:
            if not candidate.exists():
                continue

            # Check for config/paths.yaml
            paths_yaml = candidate / "config" / "paths.yaml"
            if paths_yaml.exists():
                try:
                    with open(paths_yaml, "r", encoding="utf-8") as f:
                        paths = yaml.safe_load(f)
                        if isinstance(paths, dict):
                            if "shared_skills_path" in paths:
                                self.config["shared_skills_path"] = paths["shared_skills_path"]
                            if "agents" in paths:
                                for name, info in paths["agents"].items():
                                    if name not in self.config["agents"]:
                                        self.config["agents"][name] = info
                except Exception:
                    pass

            # Check for config/user-profile.yaml
            profile_yaml = candidate / "config" / "user-profile.yaml"
            if profile_yaml.exists():
                try:
                    with open(profile_yaml, "r", encoding="utf-8") as f:
                        profile = yaml.safe_load(f)
                        if isinstance(profile, dict):
                            self.config["user_profile"] = profile
                except Exception:
                    pass

            # Update shared_skills_path if we found it
            shared = candidate / "shared-skills"
            if shared.exists():
                self.config["shared_skills_path"] = str(shared)
            elif candidate.name == "shared-skills":
                self.config["shared_skills_path"] = str(candidate)

            break

    def get(self, key: str, default: Any = None) -> Any:
        """Get config value by dot-notation key (e.g. 'agents.claude-code.format')."""
        keys = key.split(".")
        value = self.config
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
            else:
                return default
            if value is None:
                return default
        return value

    def set(self, key: str, value: Any, auto_save: bool = True):
        """Set config value by dot-notation key."""
        keys = key.split(".")
        target = self.config
        for k in keys[:-1]:
            if k not in target or not isinstance(target[k], dict):
                target[k] = {}
            target = target[k]
        target[keys[-1]] = value
        if auto_save:
            self._save_config()

    def _save_config(self):
        """Save config to file."""
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_path, "w", encoding="utf-8") as f:
            yaml.dump(self.config, f, default_flow_style=False, allow_unicode=True)

    # --- Convenience methods ---

    def get_shared_skills_path(self) -> Path:
        """Get shared skills directory path."""
        return Path(self.config.get("shared_skills_path", DEFAULT_CONFIG["shared_skills_path"]))

    def get_agent_skills_path(self, agent_name: str) -> Optional[Path]:
        """Get skills path for a specific agent."""
        agents = self.config.get("agents", {})
        agent = agents.get(agent_name, {})
        path = agent.get("skills_path")
        return Path(path) if path else None

    def get_agents(self) -> Dict[str, Dict]:
        """Get all configured agents."""
        return self.config.get("agents", {})

    def get_enabled_agents(self) -> Dict[str, Dict]:
        """Get only enabled agents."""
        return {
            name: info
            for name, info in self.get_agents().items()
            if info.get("enabled", True)
        }

    def get_skill_categories(self) -> Dict[str, list]:
        """Get skill category definitions."""
        return self.config.get("categories", DEFAULT_CONFIG["categories"])

    def get_user_profile(self) -> Dict[str, Any]:
        """Get user profile (interests, tools, preferences)."""
        return self.config.get("user_profile", {})


# --- Utility functions ---


def _deep_copy(d: dict) -> dict:
    """Deep copy a dictionary."""
    result = {}
    for k, v in d.items():
        if isinstance(v, dict):
            result[k] = _deep_copy(v)
        else:
            result[k] = v
    return result


def _deep_merge(source: dict, target: dict):
    """Recursively merge source into target (source values override)."""
    for key, value in source.items():
        if key in target and isinstance(value, dict) and isinstance(target[key], dict):
            _deep_merge(value, target[key])
        else:
            target[key] = value
