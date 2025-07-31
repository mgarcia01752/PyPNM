# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia

from pathlib import Path
from fastapi import APIRouter
from typing import Dict


class PyPnmSystemWebServiceAPI:
    """
    API class for managing PyPNM System Web Service endpoints.
    """

    def __init__(self):
        """
        Initializes the System Web Service API and registers routes.
        """
        self.router = APIRouter(
            prefix="/pypnm/system/webService",
            tags=["PyPNM System Web Service"],)

        self.router.get(
            "/reload",
            summary="Restart PyPNM System Web Service")(self.trigger_reload)

    async def trigger_reload(self) -> Dict[str, str]:
        """
        **Trigger PyPNM System Web Service Reload**

        This endpoint triggers a hot reload of the PyPNM web service.
        Useful for development to apply code changes without restarting the server.

        [API Guide - Reload FastAPI Web Service](https://github.com/mgarcia01752/PyPNM/blob/main/documentation/api/fast-api/system/reload-web-service.md)
        """
        try:
            Path(__file__).touch()
            return {"status": "reload triggered"}
        except Exception as exc:
            return {"status": "reload failed", "error": str(exc)}


# Instantiate router for easy inclusion in the main FastAPI app
router = PyPnmSystemWebServiceAPI().router
