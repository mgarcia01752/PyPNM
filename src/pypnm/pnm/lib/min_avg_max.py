from __future__ import annotations

# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia

import numpy as np
from typing import List, Union, Dict, Any

from pydantic import BaseModel, Field

from pypnm.pnm.lib.signal_statistics import SignalStatistics, SignalStatisticsModel


class MinAvgMaxSignalStatisticsModel(BaseModel):
    min: SignalStatisticsModel = Field(..., description="Aggregate stats over per-index minima")
    avg: SignalStatisticsModel = Field(..., description="Aggregate stats over per-index averages")
    max: SignalStatisticsModel = Field(..., description="Aggregate stats over per-index maxima")


class MinAvgMaxModel(BaseModel):
    """
    Pydantic model representing per-index minimum/average/maximum arrays and metadata.

    Fields
    ------
    min : List[float]
        Minimum value at each index across the input series.
    avg : List[float]
        Average value at each index across the input series.
    max : List[float]
        Maximum value at each index across the input series.
    precision : int
        Decimal places used when rounding the statistics.
    signal_statistics : MinAvgMaxSignalStatisticsModel
        Aggregate statistics computed over each of the three arrays.
    """
    min: List[float]                                 = Field(..., description="Per-index minimum values")
    avg: List[float]                                 = Field(..., description="Per-index average values")
    max: List[float]                                 = Field(..., description="Per-index maximum values")
    precision: int                                   = Field(..., ge=0, description="Rounding precision (decimal places)")
    signal_statistics: MinAvgMaxSignalStatisticsModel = Field(..., description="Aggregate stats of min/avg/max arrays")


class MinAvgMax:
    """
    Compute minimum, average, and maximum values across multiple amplitude series,
    rounding each statistic to a specified number of decimal places.

    Each series must have equal length.

    Args:
        amplitude: List of M amplitude lists, each with the same (non-zero) length.
        precision: Number of decimal places to round each statistic (default: 2).

    Raises:
        ValueError: If `amplitude` is empty or the sublists are not all the same length.

    Attributes:
        min_values: Minimum values at each index across series, rounded.
        avg_values: Average values at each index across series, rounded.
        max_values: Maximum values at each index across series, rounded.
        precision: The number of decimal places used for rounding.
    """

    def __init__(self, amplitude: List[List[Union[int, float]]], precision: int = 2) -> None:
        arr = np.array(amplitude, dtype=float)
        if arr.ndim != 2 or arr.shape[1] == 0:
            raise ValueError("`amplitude` must be a non-empty list of equally-sized lists")

        self.precision: int = precision

        raw_min = arr.min(axis=0)
        raw_avg = arr.mean(axis=0)
        raw_max = arr.max(axis=0)

        self.min_values: List[float] = [round(float(v), self.precision) for v in raw_min]
        self.avg_values: List[float] = [round(float(v), self.precision) for v in raw_avg]
        self.max_values: List[float] = [round(float(v), self.precision) for v in raw_max]

    def length(self) -> int:
        return len(self.avg_values)

    def to_model(self) -> MinAvgMaxModel:
        """
        Build a MinAvgMaxModel with nested SignalStatistics models.
        """
        sig_min = SignalStatisticsModel.model_validate(
            SignalStatistics(self.min_values).compute()
        )

        sig_avg = SignalStatisticsModel.model_validate(
            SignalStatistics(self.avg_values).compute()
        )
        
        sig_max = SignalStatisticsModel.model_validate(
            SignalStatistics(self.max_values).compute()
        )

        return MinAvgMaxModel(
            min               = self.min_values,
            avg               = self.avg_values,
            max               = self.max_values,
            precision         = self.precision,
            signal_statistics = MinAvgMaxSignalStatisticsModel(
                min = sig_min,
                avg = sig_avg,
                max = sig_max,
            ),
        )

    def to_dict(self) -> Dict[str, Any]:
        """
        Serialize via the Pydantic model.
        """
        return self.to_model().model_dump()
