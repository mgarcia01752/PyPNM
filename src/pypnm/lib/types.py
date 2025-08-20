# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia

from __future__ import annotations

from pathlib import Path
from typing import (
    Any,
    Dict,
    Iterable,
    List,
    Mapping,
    MutableMapping,
    MutableSequence,
    NewType,
    Optional,
    Sequence,
    Tuple,
    Union,
)

import numpy as np
from numpy.typing import NDArray

# ────────────────────────────────────────────────────────────────────────────────
# Core numerics
# ────────────────────────────────────────────────────────────────────────────────
Number = Union[int, float, np.number]
Float64 = np.float64

# Generic array-likes (inputs)
ArrayLike = Union[Sequence[Number], NDArray[Any]]
ArrayLikeF64 = Union[Sequence[float], NDArray[np.float64]]

# Canonical ndarray outputs (internal processing should normalize to these)
NDArrayF64 = NDArray[np.float64]
NDArrayI64 = NDArray[np.int64]

# Simple series types
FloatSeries = List[float]
IntSeries = List[int]
TwoDFloatSeries = List[FloatSeries]  # e.g., heatmaps

# Complex Number
Complex = Tuple[float, float]
ComplexArray = List[Complex]

# ────────────────────────────────────────────────────────────────────────────────
# Paths / filesystem
# ────────────────────────────────────────────────────────────────────────────────
PathLike = Union[str, Path]

# ────────────────────────────────────────────────────────────────────────────────
# JSON-like structures for REST I/O
# ────────────────────────────────────────────────────────────────────────────────
JSONScalar = Union[str, int, float, bool, None]
JSONDict = Dict[str, "JSONValue"]
JSONList = List["JSONValue"]
JSONValue = Union[JSONScalar, JSONDict, JSONList]

# ────────────────────────────────────────────────────────────────────────────────
# Unit-tagged NewTypes (stronger intent in signatures; runtime = underlying type)
# Use these in public APIs to signal semantics without heavy wrappers.
# ────────────────────────────────────────────────────────────────────────────────
# Time / index
TimestampSec = NewType("TimestampSec", float)   # seconds since epoch or relative
SampleIndex  = NewType("SampleIndex", int)

# RF / PHY units (floats)
FrequencyHz  = NewType("FrequencyHz", float)
BandwidthHz  = NewType("BandwidthHz", float)
PowerdBmV    = NewType("PowerdBmV", float)
PowerdB      = NewType("PowerdB", float)        # generic dB (e.g., MER/SNR)
MERdB        = NewType("MERdB", float)
SNRdB        = NewType("SNRdB", float)

# DOCSIS identifiers
ChannelId    = NewType("ChannelId", int)        # downstream/upstream logical channel id
SubcarrierId = NewType("SubcarrierId", int)

# SNMP identifiers
OidStr       = NewType("OidStr", str)           # symbolic or dotted-decimal
OidNumTuple  = NewType("OidNumTuple", Tuple[int, ...])

# Network addressing (store as plain strings; validate elsewhere)
MacAddressStr = NewType("MacAddressStr", str)   # "aa:bb:cc:dd:ee:ff"
IPv4Str       = NewType("IPv4Str", str)         # "192.168.0.1"
IPv6Str       = NewType("IPv6Str", str)         # "2001:db8::1"

# File tokens
FileStem = NewType("FileStem", str)             # name without extension
FileExt  = NewType("FileExt", str)              # ".csv", ".png", …

# ────────────────────────────────────────────────────────────────────────────────
# Analysis-specific small tuples
# ────────────────────────────────────────────────────────────────────────────────
RegressionCoeffs = Tuple[float, float]          # (slope, intercept)
RegressionStats  = Tuple[float, float, float]    # (slope, intercept, r2)

# RxMER / spectrum containers
FrequencySeriesHz = FloatSeries                  # alias for intent
MerSeriesdB       = FloatSeries
ShannonSeriesdB   = FloatSeries

# ────────────────────────────────────────────────────────────────────────────────
# Explicit public surface
# ────────────────────────────────────────────────────────────────────────────────
__all__ = [
    # numerics
    "Number", "Float64", "ArrayLike", "ArrayLikeF64", "NDArrayF64", "NDArrayI64",
    "FloatSeries", "IntSeries", "TwoDFloatSeries",
    # paths
    "PathLike",
    # JSON
    "JSONScalar", "JSONDict", "JSONList", "JSONValue",
    # unit-tagged
    "TimestampSec", "SampleIndex",
    "FrequencyHz", "BandwidthHz", "PowerdBmV", "PowerdB", "MERdB", "SNRdB",
    "ChannelId", "SubcarrierId",
    "OidStr", "OidNumTuple",
    "MacAddressStr", "IPv4Str", "IPv6Str",
    "FileStem", "FileExt",
    # analysis tuples / series
    "RegressionCoeffs", "RegressionStats",
    "FrequencySeriesHz", "MerSeriesdB", "ShannonSeriesdB",
]
