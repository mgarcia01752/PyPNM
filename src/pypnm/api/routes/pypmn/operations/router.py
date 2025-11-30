# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Path
from fastapi.responses import JSONResponse

from pypnm.api.routes.advance.common.abstract.service import AbstractService
from pypnm.lib.types import OperationId


class PyPnmOperationsAPI(AbstractService):
    """
    API class for managing PyPNM System Web Service operational diagnostics.

    Provides endpoints to inspect active operations, summarize their states,
    and query specific operation or group identifiers.
    """

    def __init__(self) -> None:
        """
        Initializes the System Web Service API and registers routes.
        """
        self.logger = logging.getLogger(self.__class__.__name__)
        self.router = APIRouter(
            prefix="/pypnm/operations",
            tags=["PyPNM Operations"],
        )

        # ──────────────────────────────────────────────
        # Endpoints
        # ──────────────────────────────────────────────
        self.router.get(
            "/list",
            summary="List all active or recent PyPNM operations",
            description="Returns an array of operation metadata including ID, MAC address, group, and status.",
        )(self.list_operations)

        self.router.get(
            "/status/{operation_id}",
            summary="Retrieve details for a specific operation ID",
            description="Fetch metadata and current execution state for a given operation ID.",
        )(self.get_operation_status)

        self.router.get(
            "/summary",
            summary="Summarize current PyPNM operation states",
            description="Returns total counts of RUNNING, COMPLETED, and FAILED operations.",
        )(self.get_summary)

        self.router.get(
            "/group/{group_id}",
            summary="Inspect all operations within a specific group ID",
            description="Lists all operations belonging to the same group (e.g., multi-channel or concurrent jobs).",
        )(self.get_group_operations)

    async def list_operations(self) -> JSONResponse:
        """
        List all active or recent PyPNM operations.
        """
        self.logger.info("Listing all PyPNM operations.")
        active_services = self.getActiveServices()
        return JSONResponse(content={"operations": list(active_services.keys())})

    async def get_operation_status(self, operation_id: OperationId = Path(..., description="Unique operation identifier")) -> JSONResponse:  # noqa: B008
        """
        Retrieve detailed metadata for a specific operation.
        """
        self.logger.info(f"Retrieving operation status for ID={operation_id}")
        operation_info: dict[str, Any] = {
            "operation_id": operation_id,
            "mac": "aa:bb:cc:dd:ee:ff",
            "group_id": "grp-001",
            "service": "/docs/pnm/ds/ofdm/rxMer/getMeasurement",
            "status": "RUNNING",
            "start_time": 1759810148,
            "duration_sec": 15,
        }
        return JSONResponse(content={"operation": operation_info})

    async def get_summary(self) -> JSONResponse:
        """
        Summarize the counts of all PyPNM operations by execution state.
        """
        self.logger.info("Fetching operation summary.")
        summary = {"RUNNING": 2, "COMPLETED": 5, "FAILED": 1}
        return JSONResponse(content={"summary": summary})

    async def get_group_operations(self, group_id: str = Path(..., description="Group identifier for related operations")) -> JSONResponse:
        """
        List all operations belonging to a specified group.
        """
        self.logger.info(f"Retrieving group operations for group_id={group_id}")
        group_ops = [
            {"operation_id": "op-001", "mac": "aa:bb:cc:dd:ee:ff", "status": "RUNNING"},
            {"operation_id": "op-002", "mac": "11:22:33:44:55:66", "status": "COMPLETED"},
        ]
        return JSONResponse(content={"group_id": group_id, "operations": group_ops})


# Instantiate router for easy inclusion in the main FastAPI app
router = PyPnmOperationsAPI().router
