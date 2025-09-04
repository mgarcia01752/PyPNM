
from __future__ import annotations

# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia

from pydantic import BaseModel
from typing import List

from pypnm.api.routes.common.classes.common_endpoint_classes.common_req_resp import CommonResponse

class EventLogEntry(BaseModel):
    """
    Represents a single DOCSIS event log entry retrieved from the modem.

    Attributes:
        docsDevEvFirstTime (str): Timestamp of the first occurrence of the event.
        docsDevEvLastTime (str): Timestamp of the last occurrence of the event.
        docsDevEvCounts (int): Number of times the event was recorded.
        docsDevEvLevel (int): Severity level of the event (e.g., 1=critical, 4=warning).
        docsDevEvId (int): Unique event identifier code.
        docsDevEvText (str): Human-readable description of the event.
    """
    docsDevEvFirstTime: str
    docsDevEvLastTime: str
    docsDevEvCounts: int
    docsDevEvLevel: int
    docsDevEvId: int
    docsDevEvText: str

class EventLogResponse(CommonResponse):
    """
    Response model for returning the results of a DOCSIS event log query.

    Attributes:
        status (str): Status code string, typically "0" for success.
        logs (List[EventLogEntry]): List of parsed DOCSIS event log entries.
    """
    logs: List[EventLogEntry]
