
from __future__ import annotations

# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia
from pypnm.api.routes.common.classes.common_endpoint_classes.schemas import PnmRequest


class PnmRxMerPlotRequest(PnmRequest):
   analysis_type:int
