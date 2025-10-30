from __future__ import annotations

# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia


from dataclasses import dataclass
from enum import Enum
from typing import List, Sequence, Union
import numpy as np
from numpy.typing import NDArray

Number = Union[int, float, np.number]

__all__ = ["FreqScale", "RescaledArray", "PerValueRescaled", "AutoUnitScaler", "axis_unit_label"]


class FreqScale(Enum):
    HZ  = ("Hz",  1.0)
    KHZ = ("kHz", 1e3)
    MHZ = ("MHz", 1e6)
    GHZ = ("GHz", 1e9)

    @property
    def unit(self) -> str: return self.value[0]

    @property
    def factor(self) -> float: return float(self.value[1])


@dataclass(frozen=True)
class RescaledArray:
    data: NDArray[np.float64]
    scale: FreqScale
    factor: float
    unit: str


@dataclass(frozen=True)
class PerValueRescaled:
    values: NDArray[np.float64]
    scales: NDArray[np.object_]
    units: NDArray[np.str_]


class AutoUnitScaler:
    __slots__ = ("_x",)

    def __init__(self, values: Sequence[Number] | NDArray[np.number]):
        arr = np.asarray(values, dtype=np.float64)
        if arr.ndim == 0: arr = arr.reshape(1)
        if not np.isfinite(arr).all(): raise ValueError("Input contains NaN or infinite values.")
        self._x = arr

    @staticmethod
    def _choose_by_max(max_abs: float) -> FreqScale:
        if max_abs >= 1e9: return FreqScale.GHZ
        if max_abs >= 1e6: return FreqScale.MHZ
        if max_abs >= 1e3: return FreqScale.KHZ
        return FreqScale.HZ

    @staticmethod
    def _parse_unit(u: str | FreqScale) -> FreqScale:
        if isinstance(u, FreqScale): return u
        m = u.strip().lower()
        return {"hz": FreqScale.HZ, "khz": FreqScale.KHZ, "mhz": FreqScale.MHZ, "ghz": FreqScale.GHZ}[m]

    # Whole-array: one unit chosen by the max magnitude (great for axis units)
    def rescale(self, target_unit: str | FreqScale | None = None) -> RescaledArray:
        scale = self._choose_by_max(float(np.max(np.abs(self._x)))) if target_unit is None else self._parse_unit(target_unit)
        out = (self._x / scale.factor).astype(np.float64)
        return RescaledArray(out, scale, scale.factor, scale.unit)

    # Per-element: each value gets its own best unit (for labels/legends, not axes)
    def rescale_per_value(self) -> PerValueRescaled:
        if self._x.size == 0:
            zf = np.array([], dtype=np.float64)
            return PerValueRescaled(zf, np.array([], dtype=object), np.array([], dtype=str))
        av = np.abs(self._x)
        scales = np.full(self._x.shape, FreqScale.HZ, dtype=object)
        scales[av >= 1e3] = FreqScale.KHZ
        scales[av >= 1e6] = FreqScale.MHZ
        scales[av >= 1e9] = FreqScale.GHZ
        factors = np.vectorize(lambda s: s.factor, otypes=[np.float64])(scales)
        units = np.vectorize(lambda s: s.unit, otypes=[str])(scales)
        vals = (self._x / factors).astype(np.float64)
        return PerValueRescaled(vals, scales, units)

    @staticmethod
    def format_units(pvr: PerValueRescaled, fmt: str = ".6g") -> List[str]:
        return [f"{v:{fmt}} {u}" for v, u in zip(pvr.values.tolist(), pvr.units.tolist())]


def axis_unit_label(base_label: str, scale: FreqScale) -> str:
    return f"{base_label} ({scale.unit})"
