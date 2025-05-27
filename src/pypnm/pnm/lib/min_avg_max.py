# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia

import numpy as np
from typing import List, Union, Dict, Any

from pypnm.pnm.lib.signal_statistics import SignalStatistics

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

    def __init__(
        self,
        amplitude: List[List[Union[int, float]]],
        precision: int = 2
    ) -> None:
        arr = np.array(amplitude, dtype=float)
        # Must be a 2D array and have at least one column
        if arr.ndim != 2 or arr.shape[1] == 0:
            raise ValueError(
                "`amplitude` must be a non-empty list of equally-sized lists"
            )

        self.precision: int = precision

        # Compute per-column (i.e. per-index) stats
        raw_min = arr.min(axis=0)
        raw_avg = arr.mean(axis=0)
        raw_max = arr.max(axis=0)

        # Round each value to the specified precision
        self.min_values: List[float] = [round(float(v), self.precision) for v in raw_min]
        self.avg_values: List[float] = [round(float(v), self.precision) for v in raw_avg]
        self.max_values: List[float] = [round(float(v), self.precision) for v in raw_max]

    def length(self) -> int:
        return len(self.avg_values)
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Serialize the computed statistics.

        Returns:
            A dict containing three lists, each of length N (the series length):
            - 'min': minimum at each position
            - 'avg': average at each position
            - 'max': maximum at each position
            - 'precision': the rounding precision used
        """
        
        stats = {
            "signal_statistics": {
                "min": SignalStatistics(self.min_values).compute(),
                "avg": SignalStatistics(self.avg_values).compute(),
                "max": SignalStatistics(self.max_values).compute(),
            }
        }
        
        data = {
            "min": self.min_values,
            "avg": self.avg_values,
            "max": self.max_values,
            "precision": self.precision,
        }
        
        data.update(stats)
        
        return data