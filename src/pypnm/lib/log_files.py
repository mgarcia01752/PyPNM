from __future__ import annotations

# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia

import os
from typing import Any, Union

from pydantic import BaseModel
from pypnm.config.pnm_config_manager import SystemConfigSettings
from pypnm.lib.file_processor import FileProcessor
from pypnm.lib.types import PathLike


class LogFile:
    log_dir: str = SystemConfigSettings.log_dir

    @classmethod
    def write(cls, fname: PathLike, data: Union[BaseModel, dict[Any, Any], str, bytes]) -> None:
        """
        Write log data into the configured log directory.

        Supports:
        ----------
        - BaseModel  → serialized via `.model_dump_json(indent=2)`
        - dict       → serialized as JSON string
        - str/bytes  → written directly
        """
        full_path = os.path.join(cls.log_dir, str(fname))
        fp = FileProcessor(full_path)

        if isinstance(data, BaseModel):
            fp.write_file(data.model_dump_json(indent=2))

        elif isinstance(data, dict):
            from json import dumps
            fp.write_file(dumps(data, indent=2))
        
        else:
            fp.write_file(data)
        
        fp.close()