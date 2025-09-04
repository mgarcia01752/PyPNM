
from __future__ import annotations

# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia

from typing import Optional, Callable, Union, List
from pydantic import BaseModel
import logging

from pypnm.snmp.snmp_v2c import Snmp_v2c


class DocsPnmCmDsConstDispFields(BaseModel):
    docsPnmCmDsConstDispTrigEnable: Optional[bool] = None
    docsPnmCmDsConstDispModOrderOffset: Optional[int] = None
    docsPnmCmDsConstDispNumSampleSymb: Optional[int] = None
    docsPnmCmDsConstDispSelModOrder: Optional[int] = None  # DsOfdmModulationType
    docsPnmCmDsConstDispMeasStatus: Optional[int] = None   # MeasStatusType
    docsPnmCmDsConstDispFileName: Optional[str] = None


class DocsPnmCmDsConstDispMeasEntry(BaseModel):
    index: int
    channel_id: int
    entry: DocsPnmCmDsConstDispFields

    @classmethod
    async def from_snmp(cls, index: int, snmp: Snmp_v2c) -> "DocsPnmCmDsConstDispMeasEntry":
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

        entry = DocsPnmCmDsConstDispFields(
            docsPnmCmDsConstDispTrigEnable=await fetch("docsPnmCmDsConstDispTrigEnable", Snmp_v2c.truth_value),
            docsPnmCmDsConstDispModOrderOffset=await fetch("docsPnmCmDsConstDispModOrderOffset", int),
            docsPnmCmDsConstDispNumSampleSymb=await fetch("docsPnmCmDsConstDispNumSampleSymb", int),
            docsPnmCmDsConstDispSelModOrder=await fetch("docsPnmCmDsConstDispSelModOrder", int),
            docsPnmCmDsConstDispMeasStatus=await fetch("docsPnmCmDsConstDispMeasStatus", int),
            docsPnmCmDsConstDispFileName=await fetch("docsPnmCmDsConstDispFileName", str),
        )

        return cls(index=index, channel_id=index, entry=entry)

    @classmethod
    async def get(cls, snmp: Snmp_v2c, indices: List[int]) -> List["DocsPnmCmDsConstDispMeasEntry"]:
        logger = logging.getLogger(cls.__name__)
        results: List[DocsPnmCmDsConstDispMeasEntry] = []

        for idx in indices:
            try:
                entry = await cls.from_snmp(idx, snmp)
                results.append(entry)
            except Exception as e:
                logger.warning(f"Failed to fetch Constellation Display entry for index {idx}: {e}")

        return results
