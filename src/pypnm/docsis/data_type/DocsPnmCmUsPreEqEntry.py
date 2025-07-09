# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia

import logging
from typing import Optional, Callable, Union
from pydantic import BaseModel

from pypnm.snmp.snmp_v2c import Snmp_v2c

class DocsPnmCmUsPreEqEntry(BaseModel):
    index: int
    docsPnmCmUsPreEqFileEnable: Optional[int] = None
    docsPnmCmUsPreEqAmpRipplePkToPk: Optional[int] = None
    docsPnmCmUsPreEqAmpRippleRms: Optional[int] = None
    docsPnmCmUsPreEqAmpSlope: Optional[int] = None
    docsPnmCmUsPreEqGrpDelayRipplePkToPk: Optional[int] = None
    docsPnmCmUsPreEqGrpDelayRippleRms: Optional[int] = None
    docsPnmCmUsPreEqPreEqCoAdjStatus: Optional[int] = None
    docsPnmCmUsPreEqMeasStatus: Optional[int] = None
    docsPnmCmUsPreEqLastUpdateFileName: Optional[str] = None
    docsPnmCmUsPreEqFileName: Optional[str] = None
    docsPnmCmUsPreEqAmpMean: Optional[int] = None
    docsPnmCmUsPreEqGrpDelaySlope: Optional[int] = None
    docsPnmCmUsPreEqGrpDelayMean: Optional[int] = None

    @classmethod
    async def from_snmp(cls, index: int, snmp: Snmp_v2c) -> "DocsPnmCmUsPreEqEntry":
        logger = logging.getLogger(cls.__name__)

        def safe_cast(value: str, cast: Callable) -> Union[int, float, str, None]:
            try:
                return cast(value)
            except Exception:
                return None

        async def fetch(field: str, cast: Optional[Callable] = None):
            try:
                raw = await snmp.get(f"{field}.{index}")
                val = Snmp_v2c.get_result_value(raw)

                if val is None or val == "":
                    return None

                if cast:
                    return safe_cast(val, cast)

                val = val.strip()
                if val.isdigit():
                    return int(val)
                if val.lower() in ("true", "false"):
                    return val.lower() == "true"
                try:
                    return float(val)
                except ValueError:
                    return val
            except Exception as e:
                logger.warning(f"Failed to fetch {field}.{index}: {e}")
                return None

        try:
            return cls(
                index=index,
                docsPnmCmUsPreEqFileEnable=await fetch("docsPnmCmUsPreEqFileEnable", int),
                docsPnmCmUsPreEqAmpRipplePkToPk=await fetch("docsPnmCmUsPreEqAmpRipplePkToPk", int),
                docsPnmCmUsPreEqAmpRippleRms=await fetch("docsPnmCmUsPreEqAmpRippleRms", int),
                docsPnmCmUsPreEqAmpSlope=await fetch("docsPnmCmUsPreEqAmpSlope", int),
                docsPnmCmUsPreEqGrpDelayRipplePkToPk=await fetch("docsPnmCmUsPreEqGrpDelayRipplePkToPk", int),
                docsPnmCmUsPreEqGrpDelayRippleRms=await fetch("docsPnmCmUsPreEqGrpDelayRippleRms", int),
                docsPnmCmUsPreEqPreEqCoAdjStatus=await fetch("docsPnmCmUsPreEqPreEqCoAdjStatus", int),
                docsPnmCmUsPreEqMeasStatus=await fetch("docsPnmCmUsPreEqMeasStatus", int),
                docsPnmCmUsPreEqLastUpdateFileName=await fetch("docsPnmCmUsPreEqLastUpdateFileName", str),
                docsPnmCmUsPreEqFileName=await fetch("docsPnmCmUsPreEqFileName", str),
                docsPnmCmUsPreEqAmpMean=await fetch("docsPnmCmUsPreEqAmpMean", int),
                docsPnmCmUsPreEqGrpDelaySlope=await fetch("docsPnmCmUsPreEqGrpDelaySlope", int),
                docsPnmCmUsPreEqGrpDelayMean=await fetch("docsPnmCmUsPreEqGrpDelayMean", int)
            )

        except Exception as e:
            logger.exception("Unexpected error during SNMP population")
            raise
