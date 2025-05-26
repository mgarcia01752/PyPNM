# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia

import json
import os
from typing import Any, Optional

class ConfigManager:
    """
    Manages application configuration stored in JSON format.

    Loads configuration from a file and provides access to its keys using 
    section/key-style access.

    Expected config file path: `config/system.json`
    """

    _config_data: dict[str, Any] = {}
    _config_path: str = os.path.join("config", "system.json")

    def __init__(self, config_path: Optional[str] = None) -> None:
        """
        Initializes the ConfigManager.

        Args:
            config_path (Optional[str]): Optional custom path to the config JSON file.
        """
        if config_path:
            self._config_path = config_path
        self._load()

    def _load(self) -> None:
        """Loads the configuration JSON from disk."""
        if not os.path.exists(self._config_path):
            raise FileNotFoundError(f"Config file not found: {self._config_path}")
        with open(self._config_path, "r") as f:
            self._config_data = json.load(f)

    def get(self, *keys: str, fallback: Optional[Any] = None) -> Any:
        """
        Retrieves a deeply nested value from the config.

        Args:
            *keys (str): Sequence of keys to traverse the nested dictionary.
            fallback (Optional[Any]): A value to return if any key is not found.

        Returns:
            Any: The value from the configuration or the fallback.
        
        Example:
            .get("key1","key2")
            
        """
        data = self._config_data
        for key in keys:
            if not isinstance(data, dict) or key not in data:
                return fallback
            data = data[key]
        return data

    def reload(self) -> None:
        """
        Reloads the configuration from disk.
        """
        self._load()

    def as_dict(self) -> dict[str, Any]:
        """
        Returns the entire configuration as a dictionary.

        Returns:
            dict[str, Any]: The full config.
        """
        return self._config_data.copy()
    
    def save(self, new_config: dict[str, Any]) -> None:
        """
        Overwrites the entire config with new_config and writes to the config file.
        """
        self._config_data = new_config
        with open(self._config_path, "w") as f:
            json.dump(self._config_data, f, indent=4)

