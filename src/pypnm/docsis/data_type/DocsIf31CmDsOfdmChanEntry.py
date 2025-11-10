from __future__ import annotations

# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia

import logging
from typing import Optional, Callable, Union, List

from pydantic import BaseModel
from pypnm.lib.constants import INVALID_CHANNEL_ID, KHZ
from pypnm.lib.types import ChannelId, FrequencyHz
from pypnm.snmp.snmp_v2c import Snmp_v2c


class DocsIf31CmDsOfdmChanEntry(BaseModel):
    """
    DOCSIS 3.1 CM Downstream OFDM Channel attributes (docsIf31CmDsOfdmChanTable).

    Notes
    -----
    - All values are retrieved via symbolic OIDs (no compiled OIDs).
    - Presence of fields depends on device/MIB support.
    """
    docsIf31CmDsOfdmChanChannelId:                ChannelId = INVALID_CHANNEL_ID
    docsIf31CmDsOfdmChanChanIndicator:            Optional[int] = None
    docsIf31CmDsOfdmChanSubcarrierZeroFreq:       Optional[FrequencyHz] = None
    docsIf31CmDsOfdmChanFirstActiveSubcarrierNum: Optional[int] = None
    docsIf31CmDsOfdmChanLastActiveSubcarrierNum:  Optional[int] = None
    docsIf31CmDsOfdmChanNumActiveSubcarriers:     Optional[int] = None
    docsIf31CmDsOfdmChanSubcarrierSpacing:        Optional[int] = None
    docsIf31CmDsOfdmChanCyclicPrefix:             Optional[int] = None
    docsIf31CmDsOfdmChanRollOffPeriod:            Optional[int] = None
    docsIf31CmDsOfdmChanPlcFreq:                  Optional[FrequencyHz] = None
    docsIf31CmDsOfdmChanNumPilots:                Optional[int] = None
    docsIf31CmDsOfdmChanTimeInterleaverDepth:     Optional[int] = None
    docsIf31CmDsOfdmChanPlcTotalCodewords:        Optional[int] = None
    docsIf31CmDsOfdmChanPlcUnreliableCodewords:   Optional[int] = None
    docsIf31CmDsOfdmChanNcpTotalFields:           Optional[int] = None
    docsIf31CmDsOfdmChanNcpFieldCrcFailures:      Optional[int] = None


class DocsIf31CmDsOfdmChanChannelEntry(BaseModel):
    """
    Container for a single downstream OFDM channel record retrieved via SNMP.

    Attributes
    ----------
    index : int
        Table index used to query SNMP (instance suffix).
    channel_id : int
        Mirrored from ``docsIf31CmDsOfdmChanChannelId``; 0 if absent.
    entry : DocsIf31CmDsOfdmChanEntry
        Populated OFDM channel attributes for this index.
    """
    index: int
    channel_id: int
    entry: DocsIf31CmDsOfdmChanEntry

    @classmethod
    async def from_snmp(cls, index: int, snmp: Snmp_v2c) -> "DocsIf31CmDsOfdmChanChannelEntry":
        logger = logging.getLogger(cls.__name__)

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

                if cast is not None:
                    return safe_cast(val, cast)

                s = str(val).strip()
                if s.isdigit():
                    return int(s)
                if s.lower() in ("true", "false"):
                    return s.lower() == "true"
                try:
                    return float(s)
                except ValueError:
                    return s
            except Exception as e:
                logger.warning(f"Failed to fetch {field}.{index}: {e}")
                return None

        entry = DocsIf31CmDsOfdmChanEntry(
            docsIf31CmDsOfdmChanChannelId                 = await fetch("docsIf31CmDsOfdmChanChannelId", ChannelId),
            docsIf31CmDsOfdmChanChanIndicator             = await fetch("docsIf31CmDsOfdmChanChanIndicator", int),
            docsIf31CmDsOfdmChanSubcarrierZeroFreq        = await fetch("docsIf31CmDsOfdmChanSubcarrierZeroFreq", FrequencyHz),
            docsIf31CmDsOfdmChanFirstActiveSubcarrierNum  = await fetch("docsIf31CmDsOfdmChanFirstActiveSubcarrierNum", int),
            docsIf31CmDsOfdmChanLastActiveSubcarrierNum   = await fetch("docsIf31CmDsOfdmChanLastActiveSubcarrierNum", int),
            docsIf31CmDsOfdmChanNumActiveSubcarriers      = await fetch("docsIf31CmDsOfdmChanNumActiveSubcarriers", int),
            docsIf31CmDsOfdmChanSubcarrierSpacing         = await fetch("docsIf31CmDsOfdmChanSubcarrierSpacing", int) * KHZ,
            docsIf31CmDsOfdmChanCyclicPrefix              = await fetch("docsIf31CmDsOfdmChanCyclicPrefix", int),
            docsIf31CmDsOfdmChanRollOffPeriod             = await fetch("docsIf31CmDsOfdmChanRollOffPeriod", int),
            docsIf31CmDsOfdmChanPlcFreq                   = await fetch("docsIf31CmDsOfdmChanPlcFreq", FrequencyHz),
            docsIf31CmDsOfdmChanNumPilots                 = await fetch("docsIf31CmDsOfdmChanNumPilots", int),
            docsIf31CmDsOfdmChanTimeInterleaverDepth      = await fetch("docsIf31CmDsOfdmChanTimeInterleaverDepth", int),
            docsIf31CmDsOfdmChanPlcTotalCodewords         = await fetch("docsIf31CmDsOfdmChanPlcTotalCodewords", int),
            docsIf31CmDsOfdmChanPlcUnreliableCodewords    = await fetch("docsIf31CmDsOfdmChanPlcUnreliableCodewords", int),
            docsIf31CmDsOfdmChanNcpTotalFields            = await fetch("docsIf31CmDsOfdmChanNcpTotalFields", int),
            docsIf31CmDsOfdmChanNcpFieldCrcFailures       = await fetch("docsIf31CmDsOfdmChanNcpFieldCrcFailures", int),
        )

        return cls(
            index      = index,
            channel_id = entry.docsIf31CmDsOfdmChanChannelId or 0,
            entry      = entry
        )

    @classmethod
    async def get(cls, snmp: Snmp_v2c, indices: List[int]) -> List["DocsIf31CmDsOfdmChanChannelEntry"]:
        logger = logging.getLogger(cls.__name__)
        results: List[DocsIf31CmDsOfdmChanChannelEntry] = []

        if not indices:
            logger.warning("No OFDM channel indices provided.")
            return results

        for i in indices:
            try:
                results.append(await cls.from_snmp(i, snmp))
            except Exception as e:
                logger.warning(f"Failed to retrieve OFDM channel {i}: {e}")

        return results

    # NEW: entries-only helper to accommodate your existing method signature.
    @classmethod
    async def get_entries(cls, snmp: Snmp_v2c, indices: List[int]) -> List[DocsIf31CmDsOfdmChanEntry]:
        """
        Convenience wrapper that returns only the `DocsIf31CmDsOfdmChanEntry`
        objects (no channel wrapper), preserving a return type of
        `List[DocsIf31CmDsOfdmChanEntry]`.

        This is intended to fit code like:
            await self.getDocsIf31CmDsOfdmChanEntry() -> List[DocsIf31CmDsOfdmChanEntry]
        """
        wrappers = await cls.get(snmp, indices)
        return [w.entry for w in wrappers]
