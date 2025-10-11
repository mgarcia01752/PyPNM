# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia

from __future__ import annotations

from typing import List, TypeVar, cast
from pypnm.lib.types import CaptureTime, ChannelId, Number, ProfileId

KHZ:Number  = 1_000
MHZ:Number  = 1_000_000
GHZ:Number  = 1_000_000_000

NULL_ARRAY_NUMBER:List[Number] = [0]

INVALID_CHANNEL_ID: ChannelId       = cast(ChannelId,-1)
INVALID_PROFILE_ID:ProfileId        = cast(ProfileId,-1)
INVALID_START_VAULE: int            = -1
INVALID_SCHEMA_TYPE: int            = -1
INVALID_CAPTURE_TIME: CaptureTime   = cast(CaptureTime,-1)

DEFAULT_CAPTURE_TIME: CaptureTime = cast(CaptureTime,19700101)  # epoch start

T = TypeVar("T")