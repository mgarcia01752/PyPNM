# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia

import logging
from typing import Optional, Callable, Union, List
from pydantic import BaseModel

from pypnm.snmp.snmp_v2c import Snmp_v2c

class DocsIf31CmUsOfdmaChan(BaseModel):
    docsIf31CmUsOfdmaChanChannelId: Optional[int] = None
    docsIf31CmUsOfdmaChanConfigChangeCt: Optional[int] = None
    docsIf31CmUsOfdmaChanSubcarrierZeroFreq: Optional[int] = None
    docsIf31CmUsOfdmaChanFirstActiveSubcarrierNum: Optional[int] = None
    docsIf31CmUsOfdmaChanLastActiveSubcarrierNum: Optional[int] = None
    docsIf31CmUsOfdmaChanNumActiveSubcarriers: Optional[int] = None
    docsIf31CmUsOfdmaChanSubcarrierSpacing: Optional[int] = None
    docsIf31CmUsOfdmaChanCyclicPrefix: Optional[int] = None
    docsIf31CmUsOfdmaChanRollOffPeriod: Optional[int] = None
    docsIf31CmUsOfdmaChanNumSymbolsPerFrame: Optional[int] = None
    docsIf31CmUsOfdmaChanTxPower: Optional[float] = None
    docsIf31CmUsOfdmaChanPreEqEnabled: Optional[bool] = None
    docsIf31CmStatusOfdmaUsT3Timeouts: Optional[int] = None
    docsIf31CmStatusOfdmaUsT4Timeouts: Optional[int] = None
    docsIf31CmStatusOfdmaUsRangingAborteds: Optional[int] = None
    docsIf31CmStatusOfdmaUsT3Exceededs: Optional[int] = None
    docsIf31CmStatusOfdmaUsIsMuted: Optional[bool] = None
    docsIf31CmStatusOfdmaUsRangingStatus: Optional[str] = None

class DocsIf31CmUsOfdmaChanEntry(BaseModel):
    index: int
    channel_id: int
    entry: DocsIf31CmUsOfdmaChan

    @classmethod
    async def from_snmp(cls, index: int, snmp: Snmp_v2c) -> "DocsIf31CmUsOfdmaChanEntry":
        logger = logging.getLogger(cls.__name__)

        def tenthdBmV_to_float(value: str) -> Optional[float]:
            try:
                return float(value) / 10.0
            except Exception:
                return None

        def safe_cast(value: str, cast: Callable) -> Union[int, float, str, bool, None]:
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
                logger.warning(f"Failed to fetch {field}: {e}")
                return None

        entry = DocsIf31CmUsOfdmaChan(
            docsIf31CmUsOfdmaChanChannelId=await fetch("docsIf31CmUsOfdmaChanChannelId", int),
            docsIf31CmUsOfdmaChanConfigChangeCt=await fetch("docsIf31CmUsOfdmaChanConfigChangeCt", int),
            docsIf31CmUsOfdmaChanSubcarrierZeroFreq=await fetch("docsIf31CmUsOfdmaChanSubcarrierZeroFreq", int),
            docsIf31CmUsOfdmaChanFirstActiveSubcarrierNum=await fetch("docsIf31CmUsOfdmaChanFirstActiveSubcarrierNum", int),
            docsIf31CmUsOfdmaChanLastActiveSubcarrierNum=await fetch("docsIf31CmUsOfdmaChanLastActiveSubcarrierNum", int),
            docsIf31CmUsOfdmaChanNumActiveSubcarriers=await fetch("docsIf31CmUsOfdmaChanNumActiveSubcarriers", int),
            docsIf31CmUsOfdmaChanSubcarrierSpacing=await fetch("docsIf31CmUsOfdmaChanSubcarrierSpacing", int),
            docsIf31CmUsOfdmaChanCyclicPrefix=await fetch("docsIf31CmUsOfdmaChanCyclicPrefix", int),
            docsIf31CmUsOfdmaChanRollOffPeriod=await fetch("docsIf31CmUsOfdmaChanRollOffPeriod", int),
            docsIf31CmUsOfdmaChanNumSymbolsPerFrame=await fetch("docsIf31CmUsOfdmaChanNumSymbolsPerFrame", int),
            docsIf31CmUsOfdmaChanTxPower=await fetch("docsIf31CmUsOfdmaChanTxPower", tenthdBmV_to_float),
            docsIf31CmUsOfdmaChanPreEqEnabled=await fetch("docsIf31CmUsOfdmaChanPreEqEnabled", Snmp_v2c.truth_value),
            docsIf31CmStatusOfdmaUsT3Timeouts=await fetch("docsIf31CmStatusOfdmaUsT3Timeouts", int),
            docsIf31CmStatusOfdmaUsT4Timeouts=await fetch("docsIf31CmStatusOfdmaUsT4Timeouts", int),
            docsIf31CmStatusOfdmaUsRangingAborteds=await fetch("docsIf31CmStatusOfdmaUsRangingAborteds", int),
            docsIf31CmStatusOfdmaUsT3Exceededs=await fetch("docsIf31CmStatusOfdmaUsT3Exceededs", int),
            docsIf31CmStatusOfdmaUsIsMuted=await fetch("docsIf31CmStatusOfdmaUsIsMuted", Snmp_v2c.truth_value),
            docsIf31CmStatusOfdmaUsRangingStatus=await fetch("docsIf31CmStatusOfdmaUsRangingStatus", str)
        )

        return cls(
            index=index,
            channel_id=entry.docsIf31CmUsOfdmaChanChannelId or 0,
            entry=entry
        )

    @classmethod
    async def get(cls, snmp: Snmp_v2c, indices: List[int]) -> List["DocsIf31CmUsOfdmaChanEntry"]:
        logger = logging.getLogger(cls.__name__)
        results: List[DocsIf31CmUsOfdmaChanEntry] = []

        if not indices:
            logger.warning("No upstream OFDMA indices found.")
            return results

        for index in indices:
            try:
                result = await cls.from_snmp(index, snmp)
                results.append(result)
            except Exception as e:
                logger.warning(f"Failed to retrieve OFDMA channel {index}: {e}")

        return results
