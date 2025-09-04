
from __future__ import annotations

# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia

import logging
from typing import List
from fastapi import HTTPException

from pypnm.api.routes.common.classes.common_endpoint_classes.schemas import PnmResponse
from pypnm.api.routes.common.service.status_codes import ServiceStatusCode
from pypnm.api.routes.docs.dev.schemas import EventLogEntry
from pypnm.docsis.cable_modem import CableModem
from pypnm.lib.inet import Inet
from pypnm.lib.mac_address import MacAddress

logger = logging.getLogger(__name__)

class CmDocsDevService:
    
    def __init__(self, mac_address: str, ip_address: str):
        self.mac = MacAddress(mac_address)
        self.ip = Inet(ip_address)
        self.cm = CableModem(mac_address=self.mac, inet=self.ip)
        
    async def fetch_event_log(self) -> List[EventLogEntry]:
        """
        Fetch DOCSIS event log entries and return a list of structured models.
        """        
        raw_entries: List[dict] = await self.cm.getDocsDevEventEntry(to_dict=True)

        log_entries = []
        for raw in raw_entries:
            if not isinstance(raw, dict) or not raw:
                continue

            try:
                _, event_data = next(iter(raw.items()))
                log_entries.append(EventLogEntry(
                    docsDevEvFirstTime=event_data.get("docsDevEvFirstTime", ""),
                    docsDevEvLastTime=event_data.get("docsDevEvLastTime", ""),
                    docsDevEvCounts=event_data.get("docsDevEvCounts", 0),
                    docsDevEvLevel=event_data.get("docsDevEvLevel", 0),
                    docsDevEvId=event_data.get("docsDevEvId", 0),
                    docsDevEvText=event_data.get("docsDevEvText", ""),
                ))
            except Exception:
                continue

        return log_entries

    async def reset_cable_modem(self) -> PnmResponse:
        try:
            if not await self.cm.setDocsDevResetNow():
                return PnmResponse(
                    mac_address=self.mac.__str__(),
                    status=ServiceStatusCode.RESET_NOW_FAILED,
                    message=f"Reset command to cable modem at {self.ip} failed."
                )

            return PnmResponse(
                mac_address=self.mac.__str__(),
                status=ServiceStatusCode.SUCCESS,
                message=f"Reset command sent to cable modem at {self.ip} successfully."
            )

        except Exception as e:
            logger.exception("Failed to reset cable modem")
            raise HTTPException(status_code=500, detail=str(e))

    async def ping_cable_modem(self) -> PnmResponse:
        try:
            if not self.cm.is_ping_reachable():
                return PnmResponse(
                    mac_address=str(self.mac),
                    status=ServiceStatusCode.PING_FAILED,
                    message=f"Ping to {self.ip} failed."
                )

            return PnmResponse(
                mac_address=str(self.mac),
                status=ServiceStatusCode.SUCCESS,
                message=f"Ping to cable modem at {self.ip} succeeded."
            )

        except Exception as e:
            logger.exception("Failed to send ping to cable modem")
            raise HTTPException(status_code=500, detail=str(e))
