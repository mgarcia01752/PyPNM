# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia

from __future__ import annotations

from typing import List, Literal, TypeVar, cast
from typing_extensions import Final
from pypnm.lib.types import CaptureTime, ChannelId, Number, ProfileId

KHZ:Number  = 1_000
MHZ:Number  = 1_000_000
GHZ:Number  = 1_000_000_000

FEET_PER_METER: Final[float] = 3.280839895013123
SPEED_OF_LIGHT:Final[float] = 299_792_458.0         # speed of light (m/s)

NULL_ARRAY_NUMBER:List[Number] = [0]

INVALID_CHANNEL_ID: ChannelId       = cast(ChannelId,-1)
INVALID_PROFILE_ID:ProfileId        = cast(ProfileId,-1)
INVALID_START_VAULE: int            = -1
INVALID_SCHEMA_TYPE: int            = -1
INVALID_CAPTURE_TIME: CaptureTime   = cast(CaptureTime,-1)

DEFAULT_CAPTURE_TIME: CaptureTime = cast(CaptureTime,19700101)  # epoch start

CableType = Literal["RG6", "RG59", "RG11"]


T = TypeVar("T")