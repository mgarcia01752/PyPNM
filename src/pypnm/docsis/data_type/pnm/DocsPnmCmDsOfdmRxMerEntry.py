# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia

import logging
from typing import Optional, Callable, Union, List
from pydantic import BaseModel

from pypnm.snmp.snmp_v2c import Snmp_v2c

class DocsPnmCmDsOfdmRxMerFields(BaseModel):
    docsPnmCmDsOfdmRxMerFileEnable: Optional[bool] = None
    docsPnmCmDsOfdmRxMerPercentile: Optional[int] = None
    docsPnmCmDsOfdmRxMerMean: Optional[int] = None
    docsPnmCmDsOfdmRxMerStdDev: Optional[int] = None
    docsPnmCmDsOfdmRxMerThrVal: Optional[int] = None
    docsPnmCmDsOfdmRxMerThrHighestFreq: Optional[int] = None
    docsPnmCmDsOfdmRxMerMeasStatus: Optional[int] = None
    docsPnmCmDsOfdmRxMerFileName: Optional[str] = None

class class DocsPnmCmOfdmChanEstCoefEntry(BaseModel):
    index: int
    channel_id: int
    entry: DocsPnmCmDsOfdmRxMerFields

    @classmethod
    async def from_snmp(cls, index: int, snmp: Snmp_v2c) -> "class DocsPnmCmOfdmChanEstCoefEntry":
        logger = logging.getLogger(cls.__name__)

        async def fetch(oid: str, cast: Optional[Callable] = None) -> Union[str, int, bool, None]:
            try:
                result = await snmp.get(f"{oid}.{index}")
                value = Snmp_v2c.get_result_value(result)
                if value is None:
                    return None
                if cast:
                    return cast(value)
                return value
            except Exception as e:
                logger.warning(f"Fetch error for {oid}.{index}: {e}")
                return None

        entry = DocsPnmCmDsOfdmRxMerFields(
            docsPnmCmDsOfdmRxMerFileEnable=await fetch("docsPnmCmDsOfdmRxMerFileEnable", Snmp_v2c.truth_value),
            docsPnmCmDsOfdmRxMerPercentile=await fetch("docsPnmCmDsOfdmRxMerPercentile", int),
            docsPnmCmDsOfdmRxMerMean=await fetch("docsPnmCmDsOfdmRxMerMean", int),
            docsPnmCmDsOfdmRxMerStdDev=await fetch("docsPnmCmDsOfdmRxMerStdDev", int),
            docsPnmCmDsOfdmRxMerThrVal=await fetch("docsPnmCmDsOfdmRxMerThrVal", int),
            docsPnmCmDsOfdmRxMerThrHighestFreq=await fetch("docsPnmCmDsOfdmRxMerThrHighestFreq", int),
            docsPnmCmDsOfdmRxMerMeasStatus=await fetch("docsPnmCmDsOfdmRxMerMeasStatus", int),
            docsPnmCmDsOfdmRxMerFileName=await fetch("docsPnmCmDsOfdmRxMerFileName", str)
        )

        return cls(index=index, channel_id=index, entry=entry)  # assuming channel_id == index unless otherwise specified

    @classmethod
    async def get(cls, snmp: Snmp_v2c, indices: List[int]) -> List["class DocsPnmCmOfdmChanEstCoefEntry"]:
        logger = logging.getLogger(cls.__name__)
        results: List[class DocsPnmCmOfdmChanEstCoefEntry] = []

        if not indices:
            logger.warning("No RxMER indices found.")
            return results

        for idx in indices:
            try:
                entry = await cls.from_snmp(idx, snmp)
                results.append(entry)
            except Exception as e:
                logger.warning(f"Failed to fetch RxMER entry for index {idx}: {e}")

        return results
