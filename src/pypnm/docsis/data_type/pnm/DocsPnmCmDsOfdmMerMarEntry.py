from typing import Optional, List, Callable, Union
from pydantic import BaseModel
import logging

from pypnm.snmp.snmp_v2c import Snmp_v2c


class DocsPnmCmDsOfdmMerMarFields(BaseModel):
    docsPnmCmDsOfdmMerMarProfileId: Optional[int] = None
    docsPnmCmDsOfdmMerMarThrshldOffset: Optional[int] = None
    docsPnmCmDsOfdmMerMarMeasEnable: Optional[bool] = None
    docsPnmCmDsOfdmMerMarNumSymPerSubCarToAvg: Optional[int] = None
    docsPnmCmDsOfdmMerMarReqAvgMer: Optional[int] = None
    docsPnmCmDsOfdmMerMarNumSubCarBelowThrshld: Optional[int] = None
    docsPnmCmDsOfdmMerMarMeasuredAvgMer: Optional[int] = None
    docsPnmCmDsOfdmMerMarAvgMerMargin: Optional[int] = None
    docsPnmCmDsOfdmMerMarMeasStatus: Optional[int] = None


class DocsPnmCmDsOfdmMerMarEntry(BaseModel):
    index: int
    channel_id: int
    entry: DocsPnmCmDsOfdmMerMarFields

    @classmethod
    async def from_snmp(cls, index: int, snmp: Snmp_v2c) -> "DocsPnmCmDsOfdmMerMarEntry":
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

        entry = DocsPnmCmDsOfdmMerMarFields(
            docsPnmCmDsOfdmMerMarProfileId=await fetch("docsPnmCmDsOfdmMerMarProfileId", int),
            docsPnmCmDsOfdmMerMarThrshldOffset=await fetch("docsPnmCmDsOfdmMerMarThrshldOffset", int),
            docsPnmCmDsOfdmMerMarMeasEnable=await fetch("docsPnmCmDsOfdmMerMarMeasEnable", Snmp_v2c.truth_value),
            docsPnmCmDsOfdmMerMarNumSymPerSubCarToAvg=await fetch("docsPnmCmDsOfdmMerMarNumSymPerSubCarToAvg", int),
            docsPnmCmDsOfdmMerMarReqAvgMer=await fetch("docsPnmCmDsOfdmMerMarReqAvgMer", int),
            docsPnmCmDsOfdmMerMarNumSubCarBelowThrshld=await fetch("docsPnmCmDsOfdmMerMarNumSubCarBelowThrshld", int),
            docsPnmCmDsOfdmMerMarMeasuredAvgMer=await fetch("docsPnmCmDsOfdmMerMarMeasuredAvgMer", int),
            docsPnmCmDsOfdmMerMarAvgMerMargin=await fetch("docsPnmCmDsOfdmMerMarAvgMerMargin", int),
            docsPnmCmDsOfdmMerMarMeasStatus=await fetch("docsPnmCmDsOfdmMerMarMeasStatus", int),
        )

        return cls(index=index, channel_id=index, entry=entry)

    @classmethod
    async def get(cls, snmp: Snmp_v2c, indices: List[int]) -> List["DocsPnmCmDsOfdmMerMarEntry"]:
        logger = logging.getLogger(cls.__name__)
        results: List[DocsPnmCmDsOfdmMerMarEntry] = []

        for idx in indices:
            try:
                entry = await cls.from_snmp(idx, snmp)
                results.append(entry)
            except Exception as e:
                logger.warning(f"Failed to fetch OFDM MER Margin entry for index {idx}: {e}")

        return results
