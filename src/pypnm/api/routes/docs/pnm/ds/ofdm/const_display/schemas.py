# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia

from pydantic import Field

from api.routes.common.classes.common_endpoint_classes.schemas import PnmDataResponse, PnmRequest
from docsis.data_type.DsCmConstDisplay import CmDsConstellationDisplayConst as ConsDisplaConstant

class PnmConstellationDisplayRequest(PnmRequest):
    """Request model used to trigger measurement-related operations on a cable modem."""
    modulation_order_offset:int = Field(default=ConsDisplaConstant.MODULATION_OFFSET.value, description="")
    number_sample_symbol:int = Field(default=ConsDisplaConstant.NUM_SAMPLE_SYMBOL.value, description="")

class PnmConstellationDisplayResponse(PnmDataResponse):
    """Generic response container for most PNM operations."""
