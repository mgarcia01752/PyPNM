
from __future__ import annotations

# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia
import json
import os
from typing import Any, TypeVar

T = TypeVar("T")


class ConfigManager:
    """
    Manages application configuration stored in JSON format.

    Loads configuration two levels above this file:
    Example: src/pypnm/system.json
    """

    def __init__(self, config_path: str | None = None) -> None:

        CONFIG_NAME = "system.json"
        CONFIG_DIR = "settings"
        CONFIG_PATH = os.path.join(CONFIG_DIR, CONFIG_NAME)

        if config_path:
            self._config_path = config_path
        else:
            # Two folders up from this file
            current_dir = os.path.dirname(os.path.abspath(__file__))
            root_dir = os.path.abspath(os.path.join(current_dir, ".."))
            self._config_path = os.path.join(root_dir, CONFIG_PATH)

        self._config_data: dict[str, Any] = {}
        self._load()

    def get_config_path(self) -> str:
        """Returns the path to the configuration file."""
        return self._config_path

    def _load(self) -> None:
        """Loads the configuration JSON from disk."""
        if not os.path.exists(self._config_path):
            raise FileNotFoundError(f"Config file not found: {self._config_path}")
        with open(self._config_path) as f:
            self._config_data = json.load(f)

    def get(self, *keys: str, fallback: T | None = None) -> T | None:
        """
        Retrieves a deeply nested value from the config.

        Args:
            *keys (str): Sequence of keys to traverse the nested dictionary.
            fallback (Optional[Any]): A value to return if any key is not found.

        Returns:
            Any: The value from the configuration or the fallback.

        Example:
            config.get("database", "host")
        """
        data = self._config_data
        for key in keys:
            if not isinstance(data, dict) or key not in data:
                return fallback
            data = data[key]
        return data

    def reload(self) -> None:
        """Reloads the configuration from disk."""
        self._load()

    def as_dict(self) -> dict[str, Any]:
        """Returns the entire configuration as a dictionary."""
        return self._config_data.copy()

    def save(self, new_config: dict[str, Any]) -> None:
        """Overwrites and saves the entire config."""
        self._config_data = new_config
        with open(self._config_path, "w") as f:
            json.dump(self._config_data, f, indent=4)
