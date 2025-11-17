from __future__ import annotations

# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia

from enum import Enum
from typing import Any, Optional, Callable, Union, List

import logging
from pydantic import BaseModel

from pypnm.snmp.snmp_v2c import Snmp_v2c
from pypnm.snmp.casts import as_bool, as_int, as_str, scale


class PreEqCoAdjStatus(Enum):
    """
    Enumeration of docsPnmCmUsPreEqPreEqCoAdjStatus.

    docsPnmCmUsPreEqPreEqCoAdjStatus OBJECT-TYPE
        SYNTAX      INTEGER {
                        other(1),
                        success(2),
                        clipped(3),
                        rejected(4)
                    }

    This represents whether the last set of Pre-Equalization coefficient
    adjustments were fully applied, clipped, rejected, or in some other state.

    Reference:
        CM-SP-CM-OSSI, CmUsPreEq::PreEqCoAdjStatus
    """

    OTHER    = 1  # Any state not described below
    SUCCESS  = 2  # Adjustments fully applied
    CLIPPED  = 3  # Partially applied due to excessive ripple/tilt
    REJECTED = 4  # Rejected / not applied

    def __str__(self) -> str:
        return self.name.lower()


class DocsPnmCmUsPreEqFields(BaseModel):
    docsPnmCmUsPreEqFileEnable: bool
    docsPnmCmUsPreEqAmpRipplePkToPk: float
    docsPnmCmUsPreEqAmpRippleRms: float
    docsPnmCmUsPreEqAmpSlope: float
    docsPnmCmUsPreEqGrpDelayRipplePkToPk: float
    docsPnmCmUsPreEqGrpDelayRippleRms: float
    docsPnmCmUsPreEqPreEqCoAdjStatus: str
    docsPnmCmUsPreEqMeasStatus: int
    docsPnmCmUsPreEqLastUpdateFileName: str
    docsPnmCmUsPreEqFileName: str
    docsPnmCmUsPreEqAmpMean: float
    docsPnmCmUsPreEqGrpDelaySlope: float
    docsPnmCmUsPreEqGrpDelayMean: float


class DocsPnmCmUsPreEqEntry(BaseModel):
    index: int
    channel_id: int
    entry: DocsPnmCmUsPreEqFields

    @staticmethod
    def thousandth_to_float(value: Any, *, ndigits: int = 3) -> float:
        """
        Generic helper to convert Thousandth* units (0.001 step) to float.
        Example: 12345 -> 12.345
        """
        return scale(value, 0.001, ndigits=ndigits)

    @staticmethod
    def to_pre_eq_status(value: Union[str, int]) -> PreEqCoAdjStatus:
        """
        Converts an integer value to PreEqCoAdjStatus enum, defaulting to OTHER.
        """
        try:
            return PreEqCoAdjStatus(int(value))
        except (ValueError, KeyError):
            return PreEqCoAdjStatus.OTHER

    @classmethod
    async def from_snmp(cls, index: int, snmp: Snmp_v2c) -> "DocsPnmCmUsPreEqEntry":
        logger = logging.getLogger(cls.__name__)

        async def fetch(oid: str, cast_fn: Optional[Callable[[Any], Any]] = None, default: Any = None) -> Any:
            try:
                result = await snmp.get(f"{oid}.{index}")
                value = Snmp_v2c.get_result_value(result)
                if value is None:
                    return default
                return cast_fn(value) if cast_fn else value
            except Exception as e:
                logger.warning("Fetch error for %s.%s: %s", oid, index, e)
                return default

        fields = DocsPnmCmUsPreEqFields(
            docsPnmCmUsPreEqFileEnable           = await fetch("docsPnmCmUsPreEqFileEnable",           as_bool,                default=False),
            docsPnmCmUsPreEqAmpRipplePkToPk      = await fetch("docsPnmCmUsPreEqAmpRipplePkToPk",      cls.thousandth_to_float, default=float("nan")),
            docsPnmCmUsPreEqAmpRippleRms         = await fetch("docsPnmCmUsPreEqAmpRippleRms",         cls.thousandth_to_float, default=float("nan")),
            docsPnmCmUsPreEqAmpSlope             = await fetch("docsPnmCmUsPreEqAmpSlope",             cls.thousandth_to_float, default=float("nan")),
            docsPnmCmUsPreEqGrpDelayRipplePkToPk = await fetch("docsPnmCmUsPreEqGrpDelayRipplePkToPk", cls.thousandth_to_float, default=float("nan")),
            docsPnmCmUsPreEqGrpDelayRippleRms    = await fetch("docsPnmCmUsPreEqGrpDelayRippleRms",    cls.thousandth_to_float, default=float("nan")),
            docsPnmCmUsPreEqPreEqCoAdjStatus     = await fetch("docsPnmCmUsPreEqPreEqCoAdjStatus",     lambda v: str(cls.to_pre_eq_status(v)), default=str(PreEqCoAdjStatus.OTHER)),
            docsPnmCmUsPreEqMeasStatus           = await fetch("docsPnmCmUsPreEqMeasStatus",           as_int,                 default=-1),
            docsPnmCmUsPreEqLastUpdateFileName   = await fetch("docsPnmCmUsPreEqLastUpdateFileName",   as_str,                 default=""),
            docsPnmCmUsPreEqFileName             = await fetch("docsPnmCmUsPreEqFileName",             as_str,                 default=""),
            docsPnmCmUsPreEqAmpMean              = await fetch("docsPnmCmUsPreEqAmpMean",              cls.thousandth_to_float, default=float("nan")),
            docsPnmCmUsPreEqGrpDelaySlope        = await fetch("docsPnmCmUsPreEqGrpDelaySlope",        cls.thousandth_to_float, default=float("nan")),
            docsPnmCmUsPreEqGrpDelayMean         = await fetch("docsPnmCmUsPreEqGrpDelayMean",         cls.thousandth_to_float, default=float("nan")),
        )

        channel_id = index
        return cls(index=index, channel_id=channel_id, entry=fields)

    @classmethod
    async def get(cls, snmp: Snmp_v2c, indices: List[int]) -> List["DocsPnmCmUsPreEqEntry"]:
        logger = logging.getLogger(cls.__name__)
        results: List[DocsPnmCmUsPreEqEntry] = []

        for idx in indices:
            try:
                entry = await cls.from_snmp(idx, snmp)
                results.append(entry)
            except Exception as e:
                logger.warning("Failed to fetch US PreEq entry for index %s: %s", idx, e)

        return results
