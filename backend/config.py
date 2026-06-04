# config.py
"""Gerenciamento de configurações da aplicação."""

from __future__ import annotations
import json
import os
from typing import Any, Dict, Tuple

CONFIG_FILE = "config.json"

DEFAULT_CONFIG = {
    "theme": "dark",  # "dark" or "light"
    "window_width": 1000,
    "window_height": 700,
    "last_backup": None,
}


class ConfigManager:
    """Manages user preferences and configuration."""

    def __init__(self, config_file: str = CONFIG_FILE):
        self.config_file = config_file
        self.config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file or create with defaults."""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
                    # Merge with defaults to handle new keys
                    config = DEFAULT_CONFIG.copy()
                    config.update(loaded)
                    return config
            except (json.JSONDecodeError, IOError):
                return DEFAULT_CONFIG.copy()
        return DEFAULT_CONFIG.copy()

    def save(self) -> bool:
        """Save current configuration to file."""
        try:
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
            return True
        except IOError:
            return False

    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value."""
        return self.config.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """Set a configuration value and save."""
        self.config[key] = value
        self.save()

    def get_theme(self) -> str:
        """Get current theme setting."""
        return self.config.get("theme", "dark")

    def set_theme(self, theme: str) -> None:
        """Set theme and save."""
        self.set("theme", theme)

    def get_window_size(self) -> Tuple[int, int]:
        """Retorna o tamanho salvo da janela."""
        return (
            self.config.get("window_width", 1000),
            self.config.get("window_height", 700)
        )

    def set_window_size(self, width: int, height: int) -> None:
        """Save window size."""
        self.config["window_width"] = width
        self.config["window_height"] = height
        self.save()
