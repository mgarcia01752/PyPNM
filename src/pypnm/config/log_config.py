# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia

"""
Logging configuration for OpenPNM Web API service.

This module sets up both file and console logging using values defined in the config/system_config.json file.
It includes timestamped filenames, customizable log levels, and fallback values for robustness.

Expected JSON config structure:
{
    "logging": {
        "log_level": "DEBUG",
        "log_dir": "logs",
        "log_filename": "service-%Y%m%d-%H%M%S.log"
    }
}
"""

import logging
import os
from datetime import datetime
from pypnm.config.config_manager import ConfigManager

# Load logging configuration
config_mgr = ConfigManager()
log_dir = config_mgr.get("logging", "log_dir", fallback="logs")
log_level = config_mgr.get("logging", "log_level", fallback="DEBUG").upper()
log_filename_template = config_mgr.get("logging", "log_filename", fallback="service-%Y%m%d-%H%M%S.log")

# Create log directory if it doesn't exist
os.makedirs(log_dir, exist_ok=True)

# Generate a timestamped log filename
log_filename = datetime.now().strftime(os.path.join(log_dir, log_filename_template))

# Configure file logging
logging.basicConfig(
    level=getattr(logging, log_level, logging.DEBUG),
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    filename=log_filename,
    filemode="w"
)

# Configure console logging
console = logging.StreamHandler()
console.setLevel(getattr(logging, log_level, logging.DEBUG))
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(name)s - %(message)s")
console.setFormatter(formatter)

# Add the console handler to the root logger
logging.getLogger("").addHandler(console)
