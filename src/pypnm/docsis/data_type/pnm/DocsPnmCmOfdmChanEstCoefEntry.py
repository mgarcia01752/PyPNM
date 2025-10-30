# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia

from __future__ import annotations

import logging
from typing import Any, Callable, ClassVar, List, cast
from pydantic import BaseModel

from pypnm.snmp.snmp_v2c import Snmp_v2c
from pypnm.snmp.casts import as_bool, as_int, as_str, as_float2
from pypnm.docsis.cm_snmp_operation import MeasStatusType


class DocsPnmCmOfdmChanEstCoefFields(BaseModel):
    docsPnmCmOfdmChEstCoefTrigEnable: bool
    docsPnmCmOfdmChEstCoefAmpRipplePkToPk: float
    docsPnmCmOfdmChEstCoefAmpRippleRms: float
    docsPnmCmOfdmChEstCoefAmpSlope: float
    docsPnmCmOfdmChEstCoefGrpDelayRipplePkToPk: int
    docsPnmCmOfdmChEstCoefGrpDelayRippleRms: int
    docsPnmCmOfdmChEstCoefMeasStatus: str
    docsPnmCmOfdmChEstCoefFileName: str
    docsPnmCmOfdmChEstCoefAmpMean: float
    docsPnmCmOfdmChEstCoefGrpDelaySlope: int
    docsPnmCmOfdmChEstCoefGrpDelayMean: int


class DocsPnmCmOfdmChanEstCoefEntry(BaseModel):
    index: int
    channel_id: int
    entry: DocsPnmCmOfdmChanEstCoefFields

    DEBUG: ClassVar[bool] = False

    @classmethod
    async def from_snmp(cls, index: int, snmp: Snmp_v2c) -> "DocsPnmCmOfdmChanEstCoefEntry":
        log = logging.getLogger(cls.__name__)

        async def fetch(sym: str, caster: Callable[[Any], Any]) -> Any:
            res = await snmp.get(f"{sym}.{index}")
            raw = Snmp_v2c.get_result_value(res)
            val = None if raw is None else caster(raw)
            if cls.DEBUG and log.isEnabledFor(logging.DEBUG): log.debug("idx=%s %s raw=%r cast=%r", index, sym, raw, val)
            return val

        async def req(sym: str, caster: Callable[[Any], Any], key: str) -> Any:
            val = await fetch(sym, caster)
            if val is None: raise ValueError(f"ChanEstCoef idx={index}: missing required field: {key}")
            return val

        trig_en   = cast(bool,   await req("docsPnmCmOfdmChEstCoefTrigEnable",           as_bool,  "trig_en"))
        amp_pp    = cast(float,  await req("docsPnmCmOfdmChEstCoefAmpRipplePkToPk",      as_float2,"amp_pp"))
        amp_rms   = cast(float,  await req("docsPnmCmOfdmChEstCoefAmpRippleRms",         as_float2,"amp_rms"))
        amp_slope = cast(float,  await req("docsPnmCmOfdmChEstCoefAmpSlope",             as_float2,"amp_slope"))
        gd_pp     = cast(int,    await req("docsPnmCmOfdmChEstCoefGrpDelayRipplePkToPk", as_int,   "gd_pp"))
        gd_rms    = cast(int,    await req("docsPnmCmOfdmChEstCoefGrpDelayRippleRms",    as_int,   "gd_rms"))
        meas_raw  = cast(int,    await req("docsPnmCmOfdmChEstCoefMeasStatus",           as_int,   "meas_raw"))
        file_name = cast(str,    await req("docsPnmCmOfdmChEstCoefFileName",             as_str,   "file_name"))
        amp_mean  = cast(float,  await req("docsPnmCmOfdmChEstCoefAmpMean",              as_float2,"amp_mean"))
        gd_slope  = cast(int,    await req("docsPnmCmOfdmChEstCoefGrpDelaySlope",        as_int,   "gd_slope"))
        gd_mean   = cast(int,    await req("docsPnmCmOfdmChEstCoefGrpDelayMean",         as_int,   "gd_mean"))

        entry = DocsPnmCmOfdmChanEstCoefFields(
            docsPnmCmOfdmChEstCoefTrigEnable           = bool(trig_en),
            docsPnmCmOfdmChEstCoefAmpRipplePkToPk      = float(amp_pp),
            docsPnmCmOfdmChEstCoefAmpRippleRms         = float(amp_rms),
            docsPnmCmOfdmChEstCoefAmpSlope             = float(amp_slope),
            docsPnmCmOfdmChEstCoefGrpDelayRipplePkToPk = int(gd_pp),
            docsPnmCmOfdmChEstCoefGrpDelayRippleRms    = int(gd_rms),
            docsPnmCmOfdmChEstCoefMeasStatus           = str(MeasStatusType(int(meas_raw))),
            docsPnmCmOfdmChEstCoefFileName             = str(file_name),
            docsPnmCmOfdmChEstCoefAmpMean              = float(amp_mean),
            docsPnmCmOfdmChEstCoefGrpDelaySlope        = int(gd_slope),
            docsPnmCmOfdmChEstCoefGrpDelayMean         = int(gd_mean),
        )
        return cls(index=index, channel_id=index, entry=entry)

    @classmethod
    async def get(cls, snmp: Snmp_v2c, indices: List[int]) -> List["DocsPnmCmOfdmChanEstCoefEntry"]:
        if not indices: return []
        out: List[DocsPnmCmOfdmChanEstCoefEntry] = []
        for idx in indices: out.append(await cls.from_snmp(idx, snmp))
        return out
