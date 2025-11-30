
from __future__ import annotations

# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia

from typing import Any, Dict, NewType
from pypnm.lib.types import ChannelId


MultiBasicAnalysis = NewType("MultiBasicAnalysis",Dict[ChannelId, Any])
