# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia

from __future__ import annotations

from typing import Any, Optional


def measurement_status(v: Any) -> str:
    try:
        from pypnm.docsis.data_type.enums import MeasStatusType
        return str(MeasStatusType(int(v)))
    except Exception:
        return "other"

def as_bool(v: Any) -> bool:
    try:
        return bool(int(v))
    except Exception:
        return bool(v)


def as_int(v: Any) -> int:
    return int(v)


def as_str(v: Any) -> str:
    return str(v)


def as_float0(v: Any) -> float:
    return float(v)


def as_float2(v: Any) -> float:
    # SNMP returns fixed-point ints → two-decimal float
    return round(float(v) / 100.0, 2)


def scale(v: Any, factor: float, *, ndigits: Optional[int] = None) -> float:
    x = float(v) * factor
    return round(x, ndigits) if ndigits is not None else x


def per_hundred(v: Any, *, ndigits: int = 2) -> float:
    return round(float(v) / 100.0, ndigits)


def per_thousand(v: Any, *, ndigits: int = 3) -> float:
    """
    Generic helper for MIB units expressed in 0.001 steps
    (ThousandthdB, ThousandthNsec, ThousandthdB/MHz, ThousandthNsec/MHz).
    """
    return round(float(v) / 1000.0, ndigits)
