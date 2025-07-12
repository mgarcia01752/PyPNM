# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia

import logging
from typing import Optional, Callable, Union, List
from pydantic import BaseModel

from pypnm.snmp.snmp_v2c import Snmp_v2c


class DocsPnmCmOfdmChanEstCoefFields(BaseModel):
    docsPnmCmOfdmChEstCoefTrigEnable: Optional[bool] = None
    docsPnmCmOfdmChEstCoefAmpRipplePkToPk: Optional[float] = None
    docsPnmCmOfdmChEstCoefAmpRippleRms: Optional[float] = None
    docsPnmCmOfdmChEstCoefAmpSlope: Optional[int] = None
    docsPnmCmOfdmChEstCoefGrpDelayRipplePkToPk: Optional[int] = None
    docsPnmCmOfdmChEstCoefGrpDelayRippleRms: Optional[int] = None
    docsPnmCmOfdmChEstCoefMeasStatus: Optional[int] = None
    docsPnmCmOfdmChEstCoefFileName: Optional[str] = None
    docsPnmCmOfdmChEstCoefAmpMean: Optional[float] = None
    docsPnmCmOfdmChEstCoefGrpDelaySlope: Optional[int] = None
    docsPnmCmOfdmChEstCoefGrpDelayMean: Optional[int] = None


class DocsPnmCmOfdmChanEstCoefEntry(BaseModel):
    index: int
    channel_id: int
    entry: DocsPnmCmOfdmChanEstCoefFields

    @classmethod
    async def from_snmp(cls, index: int, snmp: Snmp_v2c) -> "DocsPnmCmOfdmChanEstCoefEntry":
        logger = logging.getLogger(cls.__name__)

        def decode_thousandth_db(value: Union[int, str]) -> float:
            return int(value) / 1000.0

        async def fetch(oid: str, cast: Optional[Callable] = None) -> Union[str, int, float, bool, None]:
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

        entry = DocsPnmCmOfdmChanEstCoefFields(
            docsPnmCmOfdmChEstCoefTrigEnable=await fetch("docsPnmCmOfdmChEstCoefTrigEnable", Snmp_v2c.truth_value),
            docsPnmCmOfdmChEstCoefAmpRipplePkToPk=await fetch("docsPnmCmOfdmChEstCoefAmpRipplePkToPk", decode_thousandth_db),
            docsPnmCmOfdmChEstCoefAmpRippleRms=await fetch("docsPnmCmOfdmChEstCoefAmpRippleRms", decode_thousandth_db),
            docsPnmCmOfdmChEstCoefAmpSlope=await fetch("docsPnmCmOfdmChEstCoefAmpSlope", int),
            docsPnmCmOfdmChEstCoefGrpDelayRipplePkToPk=await fetch("docsPnmCmOfdmChEstCoefGrpDelayRipplePkToPk", int),
            docsPnmCmOfdmChEstCoefGrpDelayRippleRms=await fetch("docsPnmCmOfdmChEstCoefGrpDelayRippleRms", int),
            docsPnmCmOfdmChEstCoefMeasStatus=await fetch("docsPnmCmOfdmChEstCoefMeasStatus", int),
            docsPnmCmOfdmChEstCoefFileName=await fetch("docsPnmCmOfdmChEstCoefFileName", str),
            docsPnmCmOfdmChEstCoefAmpMean=await fetch("docsPnmCmOfdmChEstCoefAmpMean", decode_thousandth_db),
            docsPnmCmOfdmChEstCoefGrpDelaySlope=await fetch("docsPnmCmOfdmChEstCoefGrpDelaySlope", int),
            docsPnmCmOfdmChEstCoefGrpDelayMean=await fetch("docsPnmCmOfdmChEstCoefGrpDelayMean", int),
        )

        return cls(index=index, channel_id=index, entry=entry)

    @classmethod
    async def get(cls, snmp: Snmp_v2c, indices: List[int]) -> List["DocsPnmCmOfdmChanEstCoefEntry"]:
        logger = logging.getLogger(cls.__name__)
        results: List[DocsPnmCmOfdmChanEstCoefEntry] = []

        if not indices:
            logger.warning("No Channel Estimation Coefficient indices found.")
            return results

        for idx in indices:
            try:
                entry = await cls.from_snmp(idx, snmp)
                results.append(entry)
            except Exception as e:
                logger.warning(f"Failed to fetch Channel Estimation entry for index {idx}: {e}")

        return results


class DsOfdmChanEstCoefStatsResponse(BaseModel):
    mac_address: str
    status: int
    message: Optional[str]
    results: dict[str, list[DocsPnmCmOfdmChanEstCoefEntry]]
