# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia

from __future__ import annotations

import numpy as np
from typing import Any, Dict
from pydantic import BaseModel, Field

from pypnm.api.routes.common.classes.analysis.analysis import SignalStatistics, SignalStatisticsModel
from pypnm.lib.types import ComplexMatrix, FloatSeries, NDArrayF64

# ──────────────────────────────────────────────────────────────────────────────
# Type aliases
# ──────────────────────────────────────────────────────────────────────────────
PrecisionInt      = int                   # Decimal places for rounding


# ──────────────────────────────────────────────────────────────────────────────
# Pydantic Models
# ──────────────────────────────────────────────────────────────────────────────
class MinAvgMaxComplexVector(BaseModel):
    """Per-index statistics for real or imaginary components."""
    min: FloatSeries = Field(..., description="Minimum per-index values")
    avg: FloatSeries = Field(..., description="Average per-index values")
    max: FloatSeries = Field(..., description="Maximum per-index values")


class MinAvgMaxComplexSignalStats(BaseModel):
    """Signal statistics for min/avg/max across real and imaginary parts."""
    min: SignalStatisticsModel = Field(..., description="Aggregate stats of min values")
    avg: SignalStatisticsModel = Field(..., description="Aggregate stats of avg values")
    max: SignalStatisticsModel = Field(..., description="Aggregate stats of max values")


class MinAvgMaxComplexModel(BaseModel):
    """Full complex statistics split into real and imaginary components."""
    real: MinAvgMaxComplexVector = Field(..., description="Real part statistics")
    imag: MinAvgMaxComplexVector = Field(..., description="Imaginary part statistics")
    precision: PrecisionInt = Field(..., ge=0, description="Rounding precision (decimal places)")
    signal_statistics_real: MinAvgMaxComplexSignalStats = Field(..., description="Aggregate stats for real part")
    signal_statistics_imag: MinAvgMaxComplexSignalStats = Field(..., description="Aggregate stats for imaginary part")


# ──────────────────────────────────────────────────────────────────────────────
# Core Computation Class
# ──────────────────────────────────────────────────────────────────────────────
class MinAvgMaxComplex:
    """
    Compute min/avg/max values for real and imaginary components separately
    across multiple complex-valued per-subcarrier vectors.

    Each input vector must have equal length.

    Parameters
    ----------
    complex_values : ComplexMatrix
        List of complex-valued 1D arrays (must be same shape).
    precision : int, optional
        Rounding precision for outputs (default = 2).

    Raises
    ------
    ValueError
        If input matrix is empty or shape is invalid.
    """

    def __init__(self, complex_values: ComplexMatrix, precision: PrecisionInt = 2) -> None:
        arr = np.array(complex_values, dtype=np.complex128)

        if arr.ndim != 2 or arr.shape[0] == 0 or arr.shape[1] == 0:
            raise ValueError("Input must be a 2D complex matrix of shape (M×N)")

        self.precision: PrecisionInt = precision
        self.real: NDArrayF64 = np.real(arr)
        self.imag: NDArrayF64 = np.imag(arr)

        self.min_real = [round(float(v), precision) for v in self.real.min(axis=0)]
        self.avg_real = [round(float(v), precision) for v in self.real.mean(axis=0)]
        self.max_real = [round(float(v), precision) for v in self.real.max(axis=0)]

        self.min_imag = [round(float(v), precision) for v in self.imag.min(axis=0)]
        self.avg_imag = [round(float(v), precision) for v in self.imag.mean(axis=0)]
        self.max_imag = [round(float(v), precision) for v in self.imag.max(axis=0)]

    def length(self) -> int:
        """Number of subcarriers in each vector."""
        return len(self.avg_real)

    def to_model(self) -> MinAvgMaxComplexModel:
        """Convert result to a full Pydantic model."""
        stat_real_min = SignalStatistics(self.min_real).compute()
        stat_real_avg = SignalStatistics(self.avg_real).compute()
        stat_real_max = SignalStatistics(self.max_real).compute()

        stat_imag_min = SignalStatistics(self.min_imag).compute()
        stat_imag_avg = SignalStatistics(self.avg_imag).compute()
        stat_imag_max = SignalStatistics(self.max_imag).compute()

        return MinAvgMaxComplexModel(
            real=MinAvgMaxComplexVector(min=self.min_real, avg=self.avg_real, max=self.max_real),
            imag=MinAvgMaxComplexVector(min=self.min_imag, avg=self.avg_imag, max=self.max_imag),
            precision=self.precision,
            signal_statistics_real=MinAvgMaxComplexSignalStats(
                min=SignalStatisticsModel.model_validate(stat_real_min),
                avg=SignalStatisticsModel.model_validate(stat_real_avg),
                max=SignalStatisticsModel.model_validate(stat_real_max),
            ),
            signal_statistics_imag=MinAvgMaxComplexSignalStats(
                min=SignalStatisticsModel.model_validate(stat_imag_min),
                avg=SignalStatisticsModel.model_validate(stat_imag_avg),
                max=SignalStatisticsModel.model_validate(stat_imag_max),
            ),
        )

    def to_dict(self) -> Dict[str, Any]:
        """Return the result as a dictionary (nested keys)."""
        return self.to_model().model_dump()
