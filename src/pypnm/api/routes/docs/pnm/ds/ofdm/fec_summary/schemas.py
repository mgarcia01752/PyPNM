# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia

from pydantic import Field

from pypnm.api.routes.common.classes.common_endpoint_classes.schemas import PnmDataResponse, PnmRequest
from pypnm.docsis.cm_snmp_operation import FecSummaryType

class PnmFecSummaryRequest(PnmRequest):
    """Request model used to trigger measurement-related operations on a cable modem."""
    fec_summary_type:int = Field(
        default=int(FecSummaryType.TEN_MIN.value), description="FEC Summuary 10 Min = 2, 24 Hr = 3"
    )

class PnmFecSummaryResponse(PnmDataResponse):
    """Generic response container for most PNM operations."""
