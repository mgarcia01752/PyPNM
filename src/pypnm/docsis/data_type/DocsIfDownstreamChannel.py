# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia

import logging
from typing import Optional, Callable, Union, List
from pydantic import BaseModel

from pypnm.snmp.snmp_v2c import Snmp_v2c


class DocsIfDownstreamEntry(BaseModel):
    docsIfDownChannelId: Optional[int] = None
    docsIfDownChannelFrequency: Optional[int] = None
    docsIfDownChannelWidth: Optional[int] = None
    docsIfDownChannelModulation: Optional[int] = None
    docsIfDownChannelInterleave: Optional[int] = None
    docsIfDownChannelPower: Optional[float] = None
    docsIfSigQUnerroreds: Optional[int] = None
    docsIfSigQCorrecteds: Optional[int] = None
    docsIfSigQUncorrectables: Optional[int] = None
    docsIfSigQMicroreflections: Optional[int] = None
    docsIfSigQExtUnerroreds: Optional[int] = None
    docsIfSigQExtCorrecteds: Optional[int] = None
    docsIfSigQExtUncorrectables: Optional[int] = None
    docsIf3SignalQualityExtRxMER: Optional[float] = None


class DocsIfDownstreamChannelEntry(BaseModel):
    index: int
    channel_id: int
    entry: DocsIfDownstreamEntry

    @classmethod
    async def from_snmp(cls, index: int, snmp: Snmp_v2c) -> "DocsIfDownstreamChannelEntry":
        logger = logging.getLogger(cls.__name__)

        def tenthdBmV_to_float(value: str) -> Optional[float]:
            try:
                return float(value) / 10.0
            except Exception:
                return None

        def to_float(value: str) -> Optional[float]:
            try:
                return float(value)
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
                logger.warning(f"Failed to fetch {field}.{index}: {e}")
                return None

        entry = DocsIfDownstreamEntry(
            docsIfDownChannelId=await fetch("docsIfDownChannelId", int),
            docsIfDownChannelFrequency=await fetch("docsIfDownChannelFrequency", int),
            docsIfDownChannelWidth=await fetch("docsIfDownChannelWidth", int),
            docsIfDownChannelModulation=await fetch("docsIfDownChannelModulation", int),
            docsIfDownChannelInterleave=await fetch("docsIfDownChannelInterleave", int),
            docsIfDownChannelPower=await fetch("docsIfDownChannelPower", tenthdBmV_to_float),
            docsIfSigQUnerroreds=await fetch("docsIfSigQUnerroreds", int),
            docsIfSigQCorrecteds=await fetch("docsIfSigQCorrecteds", int),
            docsIfSigQUncorrectables=await fetch("docsIfSigQUncorrectables", int),
            docsIfSigQMicroreflections=await fetch("docsIfSigQMicroreflections", int),
            docsIfSigQExtUnerroreds=await fetch("docsIfSigQExtUnerroreds", int),
            docsIfSigQExtCorrecteds=await fetch("docsIfSigQExtCorrecteds", int),
            docsIfSigQExtUncorrectables=await fetch("docsIfSigQExtUncorrectables", int),
            docsIf3SignalQualityExtRxMER=await fetch("docsIf3SignalQualityExtRxMER", to_float)
        )

        return cls(
            index=index,
            channel_id=entry.docsIfDownChannelId or 0,
            entry=entry
        )

    @classmethod
    async def get(cls, snmp: Snmp_v2c, indices: List[int]) -> List["DocsIfDownstreamChannelEntry"]:
        logger = logging.getLogger(cls.__name__)
        results: List[DocsIfDownstreamChannelEntry] = []

        if not indices:
            logger.warning("No downstream SC-QAM channel indices provided.")
            return results

        for index in indices:
            try:
                result = await cls.from_snmp(index, snmp)
                results.append(result)
            except Exception as e:
                logger.warning(f"Failed to retrieve downstream channel {index}: {e}")

        return results
