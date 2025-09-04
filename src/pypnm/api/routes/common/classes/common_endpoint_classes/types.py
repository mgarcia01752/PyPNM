
from __future__ import annotations

# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia

from typing import Union
from fastapi.responses import FileResponse

from pypnm.api.routes.common.classes.common_endpoint_classes.schemas import PnmAnalysisResponse, PnmMeasurementResponse
from pypnm.api.routes.common.classes.common_endpoint_classes.snmp.schemas import SnmpResponse

MeasurementCommonResponse       = Union[PnmMeasurementResponse, SnmpResponse]
MeasurementStatsCommonResponse  = Union[SnmpResponse]
AnalysisCommonResponse          = Union[PnmAnalysisResponse, FileResponse, SnmpResponse]
