
from __future__ import annotations

# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia

from pypnm.lib.types import _StrEnum

class OutputType(_StrEnum):
    JSON    =   'json'
    ARCHIVE =   'archive'
    
class AnalysisType(_StrEnum):
    BASIC   =   'basic'