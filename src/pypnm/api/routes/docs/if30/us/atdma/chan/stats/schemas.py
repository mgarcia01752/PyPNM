
from __future__ import annotations

# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia

from pydantic import BaseModel, Field
from typing import Dict, Any

class UsScQamChannelRequest(BaseModel):
    mac_address: str = Field(..., example="a0:b1:c2:d3:e4:f5")
    ip_address: str = Field(..., example="192.168.100.1")

class UsScQamChannelEntryResponse(BaseModel):
    index: int = Field(..., description="Upstream channel table index")
    channel_id: int = Field(..., description="docsIfUpChannelId")
    entry: Dict[str, Any] = Field(..., description="All other DOCSIS Upstream channel fields")
