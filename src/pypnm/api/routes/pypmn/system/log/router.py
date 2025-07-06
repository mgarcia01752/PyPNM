# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia

import os
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from pypnm.config.system_config_settings import SystemConfigSettings

class PyPnmSystemLog:
    """
    Provides an API endpoint to download the PyPNM system log file.

    This is useful for diagnostics, debugging, or automated log collection
    from the backend.
    """

    def __init__(self):
        """
        Initialize the PyPNM System Log API router and bind routes.
        """
        self.router = APIRouter(prefix="/pypnm/system/log",tags=["PyPNM System Log"])
        self.router.post("/download", summary="Download PyPNM Log File")(self.get_pypnm_log)

    async def get_pypnm_log(self):
        """
        **Download PyPNM System Log**

        This endpoint retrieves the current PyPNM system log as a downloadable text file.
        Useful for debugging, system monitoring, and auditing.

        📘 [API Guide](https://github.com/mgarcia01752/PyPNM/blob/main/documentation/api/fast-api/system/log.md)
        """
        try:
            log_path = os.path.join(SystemConfigSettings.log_dir, SystemConfigSettings.log_filename)

            if not os.path.isfile(log_path):
                raise FileNotFoundError(f"Log file not found at: {log_path}")

            return FileResponse(
                path=log_path,
                filename=SystemConfigSettings.log_filename,
                media_type="text/plain")

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to retrieve log: {e}")

# Expose router for FastAPI app
router = PyPnmSystemLog().router
