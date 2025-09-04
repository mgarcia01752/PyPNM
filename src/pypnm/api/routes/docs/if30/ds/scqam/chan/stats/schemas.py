
from __future__ import annotations

# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia

from pydantic import Field
from pypnm.api.routes.common.classes.common_endpoint_classes.snmp.schemas import SnmpRequest

class CodewordErrorRateRequest(SnmpRequest):
    sample_time_elapsed: float = Field(default=5, description="Time elapse between Codeword Counters, default is 5 seconds.")

