
from __future__ import annotations

# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia

from pydantic import BaseModel
from typing import Any, Dict

class SystemConfigModel(BaseModel):
    FastApiRequestDefault: Dict[str, Any]
    SNMP: Dict[str, Any]
    PnmBulkDataTransfer: Dict[str, Any]
    PnmFileRetrieval: Dict[str, Any]
    logging: Dict[str, Any]
