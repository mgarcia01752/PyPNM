# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia

from pydantic import BaseModel, Field
from pypnm.api.routes.common.classes.common_endpoint_classes.schemas import PnmRequest

class MerMarginParams(BaseModel):
    MerMarThrshldOffset: int = Field(..., description="Threshold offset in quarter-dB units")
    MerMarNumSymPerSubCarToAvg: int = Field(..., description="Number of symbols to average per subcarrier")
    MerMarReqAvgMer: int = Field(..., description="Required average MER in quarter-dB units")

class MerMarginConfig(BaseModel):
    channel_id: int = Field(..., description="OFDMA channel ID to test")
    profile_id: int = Field(..., description="OFDM profile ID to test against")
    params: MerMarginParams

class PnmMerMarginRequest(PnmRequest):
    mer_margin: MerMarginConfig
