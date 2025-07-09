# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia

import logging
from typing import Optional, Callable, Union, List
from pydantic import BaseModel

from pypnm.snmp.snmp_v2c import Snmp_v2c

class DocsIfUpstreamEntry(BaseModel):
    docsIfUpChannelId: Optional[int] = None
    docsIfUpChannelFrequency: Optional[int] = None
    docsIfUpChannelWidth: Optional[int] = None
    docsIfUpChannelModulationProfile: Optional[int] = None
    docsIfUpChannelSlotSize: Optional[int] = None
    docsIfUpChannelTxTimingOffset: Optional[int] = None
    docsIfUpChannelRangingBackoffStart: Optional[int] = None
    docsIfUpChannelRangingBackoffEnd: Optional[int] = None
    docsIfUpChannelTxBackoffStart: Optional[int] = None
    docsIfUpChannelTxBackoffEnd: Optional[int] = None
    docsIfUpChannelType: Optional[int] = None
    docsIfUpChannelCloneFrom: Optional[int] = None
    docsIfUpChannelUpdate: Optional[bool] = None
    docsIfUpChannelStatus: Optional[int] = None
    docsIfUpChannelPreEqEnable: Optional[bool] = None

    # DOCS-IF3-MIB extensions
    docsIf3CmStatusUsTxPower: Optional[float] = None
    docsIf3CmStatusUsT3Timeouts: Optional[int] = None
    docsIf3CmStatusUsT4Timeouts: Optional[int] = None
    docsIf3CmStatusUsRangingAborteds: Optional[int] = None
    docsIf3CmStatusUsModulationType: Optional[int] = None
    docsIf3CmStatusUsEqData: Optional[str] = None
    docsIf3CmStatusUsT3Exceededs: Optional[int] = None
    docsIf3CmStatusUsIsMuted: Optional[bool] = None
    docsIf3CmStatusUsRangingStatus: Optional[int] = None

class DocsIfUpstreamChannelEntry(BaseModel):
    index: int
    channel_id: int
    entry: DocsIfUpstreamEntry

    @classmethod
    async def from_snmp(cls, index: int, snmp: Snmp_v2c) -> "DocsIfUpstreamChannelEntry":
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

        entry = DocsIfUpstreamEntry(
            docsIfUpChannelId=await fetch("docsIfUpChannelId", int),
            docsIfUpChannelFrequency=await fetch("docsIfUpChannelFrequency", int),
            docsIfUpChannelWidth=await fetch("docsIfUpChannelWidth", int),
            docsIfUpChannelModulationProfile=await fetch("docsIfUpChannelModulationProfile", int),
            docsIfUpChannelSlotSize=await fetch("docsIfUpChannelSlotSize", int),
            docsIfUpChannelTxTimingOffset=await fetch("docsIfUpChannelTxTimingOffset", int),
            docsIfUpChannelRangingBackoffStart=await fetch("docsIfUpChannelRangingBackoffStart", int),
            docsIfUpChannelRangingBackoffEnd=await fetch("docsIfUpChannelRangingBackoffEnd", int),
            docsIfUpChannelTxBackoffStart=await fetch("docsIfUpChannelTxBackoffStart", int),
            docsIfUpChannelTxBackoffEnd=await fetch("docsIfUpChannelTxBackoffEnd", int),
            docsIfUpChannelType=await fetch("docsIfUpChannelType", int),
            docsIfUpChannelCloneFrom=await fetch("docsIfUpChannelCloneFrom", int),
            docsIfUpChannelUpdate=await fetch("docsIfUpChannelUpdate", Snmp_v2c.truth_value),
            docsIfUpChannelStatus=await fetch("docsIfUpChannelStatus", int),
            docsIfUpChannelPreEqEnable=await fetch("docsIfUpChannelPreEqEnable", Snmp_v2c.truth_value),

            docsIf3CmStatusUsTxPower=await fetch("docsIf3CmStatusUsTxPower", tenthdBmV_to_float),
            docsIf3CmStatusUsT3Timeouts=await fetch("docsIf3CmStatusUsT3Timeouts", int),
            docsIf3CmStatusUsT4Timeouts=await fetch("docsIf3CmStatusUsT4Timeouts", int),
            docsIf3CmStatusUsRangingAborteds=await fetch("docsIf3CmStatusUsRangingAborteds", int),
            docsIf3CmStatusUsModulationType=await fetch("docsIf3CmStatusUsModulationType", int),
            docsIf3CmStatusUsEqData=await fetch("docsIf3CmStatusUsEqData", str),
            docsIf3CmStatusUsT3Exceededs=await fetch("docsIf3CmStatusUsT3Exceededs", int),
            docsIf3CmStatusUsIsMuted=await fetch("docsIf3CmStatusUsIsMuted", Snmp_v2c.truth_value),
            docsIf3CmStatusUsRangingStatus=await fetch("docsIf3CmStatusUsRangingStatus", int)
        )

        return cls(
            index=index,
            channel_id=entry.docsIfUpChannelId or 0,
            entry=entry
        )

    @classmethod
    async def get(cls, snmp: Snmp_v2c, indices: List[int]) -> List["DocsIfUpstreamChannelEntry"]:
        logger = logging.getLogger(cls.__name__)
        results: List[DocsIfUpstreamChannelEntry] = []

        if not indices:
            logger.warning("No upstream ATDMA indices found.")
            return results

        for index in indices:
            try:
                result = await cls.from_snmp(index, snmp)
                results.append(result)
            except Exception as e:
                logger.warning(f"Failed to retrieve upstream channel {index}: {e}")

        return results
