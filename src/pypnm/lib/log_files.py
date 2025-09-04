
from __future__ import annotations

# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia

import os
from typing import Any, Union

from pypnm.config.pnm_config_manager import SystemConfigSettings
from pypnm.lib.file_processor import FileProcessor
from pypnm.lib.types import PathLike


class LogFile:
    log_dir: str = SystemConfigSettings.log_dir

    @classmethod
    def write(cls, fname: PathLike, data: Union[dict[Any, Any], str, bytes]) -> None:
        """Write log data into the configured log directory."""
        full_path = os.path.join(cls.log_dir, str(fname))
        FileProcessor(full_path).write_file(data)
