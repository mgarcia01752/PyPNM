# SPDX-License-Identifier: MIT
# Copyright (c) 2025

from __future__ import annotations

from typing import Dict, List, Literal, TypeVar, cast
from typing_extensions import Final, TypeAlias
from pypnm.lib.types import CaptureTime, ChannelId, FloatEnum, FrequencyHz, Number, ProfileId

HZ:  int = 1
KHZ: int = 1_000
MHZ: int = 1_000_000
GHZ: int = 1_000_000_000

FEET_PER_METER: Final[float] = 3.280839895013123
SPEED_OF_LIGHT: Final[float] = 299_792_458.0  # m/s

NULL_ARRAY_NUMBER: Final[List[Number]] = [0]

INVALID_CHANNEL_ID: Final[ChannelId]                = cast(ChannelId, -1)
INVALID_PROFILE_ID: Final[ProfileId]                = cast(ProfileId, -1)
INVALID_SUB_CARRIER_ZERO_FREQ: Final[FrequencyHz]   = cast(FrequencyHz, 0)
INVALID_START_VALUE: Final[int]                     = -1
INVALID_SCHEMA_TYPE: Final[int]                     = -1
INVALID_CAPTURE_TIME: Final[CaptureTime]            = cast(CaptureTime, -1)

DEFAULT_CAPTURE_TIME: Final[CaptureTime]            = cast(CaptureTime, 19700101)  # epoch start

CableTypes: TypeAlias = Literal["RG6", "RG59", "RG11"]

# Velocity Factor (VF) by cable type (fraction of c0)
CABLE_VF: Final[Dict[CableTypes, float]] = {
    "RG6":  0.87,
    "RG59": 0.82,
    "RG11": 0.87,
}

class CableType(FloatEnum):
    RG6  = 0.87
    RG59 = 0.82
    RG11 = 0.87

T = TypeVar("T")

DEFAULT_SPECTRUM_ANALYZER_INDICES: Final[List[int]] = [0]

__all__ = [
    "HZ", "KHZ", "MHZ", "GHZ",
    "FEET_PER_METER", "SPEED_OF_LIGHT",
    "NULL_ARRAY_NUMBER",
    "INVALID_CHANNEL_ID", "INVALID_PROFILE_ID", "INVALID_SUB_CARRIER_ZERO_FREQ",
    "INVALID_START_VALUE", "INVALID_SCHEMA_TYPE", "INVALID_CAPTURE_TIME",
    "DEFAULT_CAPTURE_TIME",
    "CableTypes", "CABLE_VF",
    "DEFAULT_SPECTRUM_ANALYZER_INDICES"
]
