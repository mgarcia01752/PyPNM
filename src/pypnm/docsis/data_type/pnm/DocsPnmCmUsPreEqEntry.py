from typing import Optional, Callable, Union, List
from pydantic import BaseModel
import logging

from pypnm.snmp.snmp_v2c import Snmp_v2c


class DocsPnmCmUsPreEqFields(BaseModel):
    docsPnmCmUsPreEqFileEnable: Optional[bool] = None
    docsPnmCmUsPreEqAmpRipplePkToPk: Optional[float] = None
    docsPnmCmUsPreEqAmpRippleRms: Optional[float] = None
    docsPnmCmUsPreEqAmpSlope: Optional[int] = None
    docsPnmCmUsPreEqGrpDelayRipplePkToPk: Optional[int] = None
    docsPnmCmUsPreEqGrpDelayRippleRms: Optional[int] = None
    docsPnmCmUsPreEqPreEqCoAdjStatus: Optional[int] = None
    docsPnmCmUsPreEqMeasStatus: Optional[int] = None
    docsPnmCmUsPreEqLastUpdateFileName: Optional[str] = None
    docsPnmCmUsPreEqFileName: Optional[str] = None
    docsPnmCmUsPreEqAmpMean: Optional[float] = None
    docsPnmCmUsPreEqGrpDelaySlope: Optional[int] = None
    docsPnmCmUsPreEqGrpDelayMean: Optional[int] = None


class DocsPnmCmUsPreEqEntry(BaseModel):
    index: int
    channel_id: int
    entry: DocsPnmCmUsPreEqFields

    @classmethod
    async def from_snmp(cls, index: int, snmp: Snmp_v2c) -> "DocsPnmCmUsPreEqEntry":
        logger = logging.getLogger(cls.__name__)

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

        entry = DocsPnmCmUsPreEqFields(
            docsPnmCmUsPreEqFileEnable=await fetch("docsPnmCmUsPreEqFileEnable", Snmp_v2c.truth_value),
            docsPnmCmUsPreEqAmpRipplePkToPk=await fetch("docsPnmCmUsPreEqAmpRipplePkToPk", float),
            docsPnmCmUsPreEqAmpRippleRms=await fetch("docsPnmCmUsPreEqAmpRippleRms", float),
            docsPnmCmUsPreEqAmpSlope=await fetch("docsPnmCmUsPreEqAmpSlope", int),
            docsPnmCmUsPreEqGrpDelayRipplePkToPk=await fetch("docsPnmCmUsPreEqGrpDelayRipplePkToPk", int),
            docsPnmCmUsPreEqGrpDelayRippleRms=await fetch("docsPnmCmUsPreEqGrpDelayRippleRms", int),
            docsPnmCmUsPreEqPreEqCoAdjStatus=await fetch("docsPnmCmUsPreEqPreEqCoAdjStatus", int),
            docsPnmCmUsPreEqMeasStatus=await fetch("docsPnmCmUsPreEqMeasStatus", int),
            docsPnmCmUsPreEqLastUpdateFileName=await fetch("docsPnmCmUsPreEqLastUpdateFileName", str),
            docsPnmCmUsPreEqFileName=await fetch("docsPnmCmUsPreEqFileName", str),
            docsPnmCmUsPreEqAmpMean=await fetch("docsPnmCmUsPreEqAmpMean", float),
            docsPnmCmUsPreEqGrpDelaySlope=await fetch("docsPnmCmUsPreEqGrpDelaySlope", int),
            docsPnmCmUsPreEqGrpDelayMean=await fetch("docsPnmCmUsPreEqGrpDelayMean", int),
        )

        return cls(index=index, channel_id=index, entry=entry)

    @classmethod
    async def get(cls, snmp: Snmp_v2c, indices: List[int]) -> List["DocsPnmCmUsPreEqEntry"]:
        logger = logging.getLogger(cls.__name__)
        results: List[DocsPnmCmUsPreEqEntry] = []

        for idx in indices:
            try:
                entry = await cls.from_snmp(idx, snmp)
                results.append(entry)
            except Exception as e:
                logger.warning(f"Failed to fetch US PreEq entry for index {idx}: {e}")

        return results
