# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia

from __future__ import annotations

from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, NewType, Sequence, Tuple, Union, TypeAlias

import numpy as np
from numpy.typing import NDArray

# Enum String Type
class _StrEnum(str, Enum):
    """Py3.10-compatible StrEnum shim."""
    pass

class FloatEnum(float, Enum):
    """Float-like Enum base: members behave like floats."""
    pass

# Basic strings
String: TypeAlias       = str
StringArray: TypeAlias  = List[String]

# ────────────────────────────────────────────────────────────────────────────────
# Core numerics
# ────────────────────────────────────────────────────────────────────────────────
Number       = Union[int, float, np.number]
Float64      = np.float64
ByteArray    = List[np.uint8]

# Generic array-likes (inputs)
# TODO: Review to remove -> _ArrayLike = Union[Sequence[Number], NDArray[Any]]
_ArrayLike   = Union[Sequence[Number], NDArray[Any]]

ArrayLike    = List[Number]
ArrayLikeF64 = Union[Sequence[float], NDArray[np.float64]]

# Canonical ndarray outputs (internal processing should normalize to these)
NDArrayF64   = NDArray[np.float64]
NDArrayI64   = NDArray[np.int64]

# ────────────────────────────────────────────────────────────────────────────────
# Simple series / containers  — use TypeAlias (recommended)
# ────────────────────────────────────────────────────────────────────────────────
IntSeries: TypeAlias        = List[int]
FloatSeries: TypeAlias      = List[float]
TwoDFloatSeries: TypeAlias  = List[FloatSeries]         # e.g., heatmaps M×K
FloatSequence: TypeAlias    = Sequence[float]

# Complex number encodings (JSON-safe)
Complex                  = Tuple[float, float]  # (re, im)
ComplexArray: TypeAlias  = List[Complex]        # K × (re, im)
ComplexSeries: TypeAlias = List[complex]        # Python complex list (internal use)

# ────────────────────────────────────────────────────────────────────────────────
# Modulation profile identifiers
# ────────────────────────────────────────────────────────────────────────────────
ProfileId = NewType("ProfileId", int)

# ────────────────────────────────────────────────────────────────────────────────
# Paths / filesystem
# ────────────────────────────────────────────────────────────────────────────────
PathLike  = Union[str, Path]
PathArray = List[PathLike]

# ────────────────────────────────────────────────────────────────────────────────
# JSON-like structures for REST I/O
# ────────────────────────────────────────────────────────────────────────────────
JSONScalar = Union[str, int, float, bool, None]
JSONDict   = Dict[str, "JSONValue"]
JSONList   = List["JSONValue"]
JSONValue  = Union[JSONScalar, JSONDict, JSONList]

# ────────────────────────────────────────────────────────────────────────────────
# Unit-tagged NewTypes (scalars only; runtime = underlying type)
# ────────────────────────────────────────────────────────────────────────────────
# Time / index
CaptureTime   = NewType("CaptureTime", int)
TimeStamp     = NewType("TimeStamp", int)
TimestampSec  = NewType("TimestampSec", int)
TimestampMs   = NewType("TimestampMs", int)
SampleIndex   = NewType("SampleIndex", int)

# RF / PHY units (keep as scalars with units)
FrequencyHz   = NewType("FrequencyHz", int)
BandwidthHz   = NewType("BandwidthHz", int)

PowerdBmV     = NewType("PowerdBmV", float)
PowerdB       = NewType("PowerdB", float)
MERdB         = NewType("MERdB", float)
SNRdB         = NewType("SNRdB", float)
SNRln         = NewType("SNRln", float)

# DOCSIS identifiers
ChannelId     = NewType("ChannelId", int)
SubcarrierId  = NewType("SubcarrierId", int)
SubcarrierIdx = NewType("SubcarrierIdx", int)

# SNMP identifiers
OidStr        = NewType("OidStr", str)              # symbolic or dotted-decimal
OidNumTuple   = NewType("OidNumTuple", Tuple[int, ...])

# Network addressing (store as plain strings; validate elsewhere)
MacAddressStr   = NewType("MacAddressStr", str)     # aa:bb:cc:dd:ee:ff
IPv4Str         = NewType("IPv4Str", str)           # 192.168.0.1
IPv6Str         = NewType("IPv6Str", str)           # 2001:db8::1
InetAddressStr  = NewType("InetAddressStr", str)    # 192.168.0.1 | 2001:db8::1

# File tokens
FileStem      = NewType("FileStem", str)            # name without extension
FileExt       = NewType("FileExt", str)             # ".csv", ".png", …
FileName      = NewType("FileName", str)

# ────────────────────────────────────────────────────────────────────────────────
# Analysis-specific tuples / series
# ────────────────────────────────────────────────────────────────────────────────
RegressionCoeffs = Tuple[float, float]              # (slope, intercept)
RegressionStats  = Tuple[float, float, float]       # (slope, intercept, r2)

# RxMER / spectrum containers
FrequencySeriesHz: TypeAlias = List[int]
MerSeriesdB: TypeAlias       = FloatSeries
ShannonSeriesdB: TypeAlias   = FloatSeries
MagnitudeSeries: TypeAlias   = FloatSeries

BitsPerSymbol       = NewType("BitsPerSymbol", int)
BitsPerSymbolSeries: TypeAlias = List[BitsPerSymbol]

Microseconds = NewType("Microseconds", float)

# ────────────────────────────────────────────────────────────────────────────────
# HTTP return code type
# ────────────────────────────────────────────────────────────────────────────────
HttpRtnCode = NewType("HttpRtnCode", int)

# ────────────────────────────────────────────────────────────────────────────────
# Explicit public surface
# ────────────────────────────────────────────────────────────────────────────────
__all__ = [
    "ByteArray",
    # numerics
    "Number", "Float64", "ArrayLike", "ArrayLikeF64", "NDArrayF64", "NDArrayI64",
    "FloatSeries", "TwoDFloatSeries", "FloatSequence", "IntSeries",
    # complex
    "Complex", "ComplexArray", "ComplexSeries",
    # paths
    "PathLike", "PathArray",
    # JSON
    "JSONScalar", "JSONDict", "JSONList", "JSONValue",
    # unit-tagged scalars
    "CaptureTime", "TimeStamp", "TimestampSec", "TimestampMs", "SampleIndex",
    "FrequencyHz", "BandwidthHz", "PowerdBmV", "PowerdB", "MERdB", "SNRdB", "SNRln",
    "ChannelId", "SubcarrierId",
    "OidStr", "OidNumTuple",
    "MacAddressStr", "IPv4Str", "IPv6Str",
    "FileStem", "FileExt", "FileName",
    # analysis tuples / series
    "RegressionCoeffs", "RegressionStats",
    "FrequencySeriesHz", "MerSeriesdB", "ShannonSeriesdB", "MagnitudeSeries",
    # modulation/profile & misc
    "ProfileId", "BitsPerSymbol", "BitsPerSymbolSeries", "Microseconds",
    "HttpRtnCode"
]
