# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia

from typing import Any, Dict
import numpy as np

from pypnm.lib.types import ArrayLikeF64

class SignalStatistics:
    """
    Compute common time-domain statistics for 1D signals,
    returning average power instead of RMS.

    Available statistics:
      - mean: Arithmetic average of the signal values.
      - median: Middle value when the data is sorted, robust to outliers.
      - std: Population standard deviation, measures data dispersion around the mean.
      - variance: Population variance, square of the standard deviation.
      - power: Mean squared value of the signal (average power).
      - peak_to_peak: Difference between maximum and minimum values (signal range).
      - mean_abs_deviation: Mean of absolute deviations from the mean, another measure of dispersion.
      - skewness: Third standardized moment, indicates signal asymmetry.
      - kurtosis: Fourth standardized moment, indicates heaviness of tails versus a Gaussian.
      - crest_factor: Ratio of peak amplitude to the square root of power, shows peak prominence.
      - zero_crossing_rate: Fraction of successive sample sign changes, indicates signal frequency content.
      - zero_crossings: Total count of sign changes in the signal.
    """
    def __init__(self, data: ArrayLikeF64) -> None:
        
        # ensure data is a 1-D float array
        self.data = np.asarray(data, dtype=float).flatten()
        
        if self.data.size == 0:
            raise ValueError("Input data must contain at least one sample.")
    
    def compute(self) -> Dict[str, Any]:
        x = self.data
        n = x.size
        mean = x.mean()
        std = x.std()                       # population std
        var = x.var()
        power = np.mean(x**2)               # average power
        ptp = x.max() - x.min()             # peak-to-peak
        mad = np.mean(np.abs(x - mean))     # mean absolute deviation
        
        # skewness and kurtosis (population definitions)
        skewness = np.mean((x - mean)**3) / std**3 if std > 0 else np.nan
        kurtosis = np.mean((x - mean)**4) / std**4 if std > 0 else np.nan
        
        # crest factor = peak amplitude / sqrt(power)
        peak = np.abs(x).max()
        crest_factor = peak / np.sqrt(power) if power > 0 else np.nan
        
        # zero crossing rate
        crossings = np.sum(x[:-1] * x[1:] < 0)
        zcr = crossings / (n - 1)
        
        return {
            "mean": mean,
            "median": np.median(x),
            "std": std,
            "variance": var,
            "power": power,
            "peak_to_peak": ptp,
            "mean_abs_deviation": mad,
            "skewness": skewness,
            "kurtosis": kurtosis,
            "crest_factor": crest_factor,
            "zero_crossing_rate": zcr,
            "zero_crossings": int(crossings),
        }
