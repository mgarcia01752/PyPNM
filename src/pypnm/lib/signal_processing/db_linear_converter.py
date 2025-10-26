# SPDX-License-Identifier: MIT
from __future__ import annotations

from typing import Optional, Union, Literal

import numpy as np

from pypnm.lib.types import FloatSeries, ComplexArray


class DbLinearConverter:
    """
    Conversions between linear and dB, plus utilities for complex [re, im] pairs.

    Notes
    -----
    - Power convention: dB = 10 * log10(P).
    - `linear_to_db(values, ref=...)` supports absolute (ref=None) or relative dB.
    - For complex samples, power per sample is (re**2 + im**2).
    - All methods accept Python lists (or NumPy arrays) and always return lists.
    """

    @staticmethod
    def db_to_linear(values: FloatSeries) -> FloatSeries:
        """
        Convert dB values to linear power scale (absolute).

        Parameters
        ----------
        values : FloatSeries
            dB values.

        Returns
        -------
        FloatSeries
            Linear power values.
        """
        arr = np.asarray(values, dtype=float)
        return (10.0 ** (arr / 10.0)).tolist()

    @staticmethod
    def linear_to_db(
        values: FloatSeries,
        ref: Optional[float] = None,
        eps: float = 1e-20,
    ) -> FloatSeries:
        """
        Convert linear power values to dB.

        - positives  -> 10*log10(v/ref)
        - zeros      -> -inf
        - negatives  -> NaN
        """
        arr = np.asarray(values, dtype=float)

        # choose denominator for relative dB (absolute if ref=None)
        denom = max(float(ref), eps) if ref is not None else 1.0

        out = np.empty_like(arr, dtype=float)
        neg_mask  = arr < 0.0
        zero_mask = arr == 0.0
        pos_mask  = arr > 0.0

        # negatives -> NaN
        out[neg_mask] = np.nan
        # zeros -> -inf
        out[zero_mask] = -np.inf

        with np.errstate(divide="ignore", invalid="ignore"):
            out[pos_mask] = 10.0 * np.log10(arr[pos_mask] / denom)

        return out.tolist()
    @staticmethod
    def complex_to_Linear(values: ComplexArray) -> FloatSeries:
        """
        Convert complex-valued samples (as [real, imag] pairs) to linear power.

        For each pair [re, im], returns re**2 + im**2.

        Parameters
        ----------
        values : ComplexArray
            Sequence of [real, imag] pairs.

        Returns
        -------
        FloatSeries
            Linear power per sample.
        """
        arr = np.asarray(values, dtype=float)
        if arr.size == 0:
            return []
        if arr.ndim != 2 or arr.shape[1] != 2:
            raise ValueError("values must be a sequence of [real, imag] pairs")
        power = np.sum(arr * arr, axis=1)
        return power.tolist()

    @staticmethod
    def complex_to_db(
        values: ComplexArray,
        ref: Optional[Union[float, Literal["max"]]] = None,
        eps: float = 1e-20,
    ) -> FloatSeries:
        """
        Convert complex samples (as [re, im] pairs) to power in dB.

        Parameters
        ----------
        values : ComplexArray
            Sequence of [real, imag] pairs (N x 2).
        ref : Optional[float | 'max']
            - None  : absolute dB (reference = 1.0).
            - float : relative dB w.r.t. this power reference.
            - "max" : relative dB w.r.t. the maximum power in `values` (peak → 0 dB).
        eps : float
            Numerical floor to avoid log10(0).

        Returns
        -------
        FloatSeries
            dB power per input pair.
        """
        arr = np.asarray(values, dtype=float)
        if arr.size == 0:
            return []
        if arr.ndim != 2 or arr.shape[1] != 2:
            raise ValueError("values must be a sequence of [real, imag] pairs")

        power = np.sum(arr * arr, axis=1)

        if ref == "max":
            ref_power = float(np.max(power)) if power.size else 1.0
        elif isinstance(ref, (int, float)):
            ref_power = float(ref)
        else:
            ref_power = 1.0  # absolute dB

        denom = max(ref_power, eps)
        with np.errstate(divide="ignore", invalid="ignore"):
            db = 10.0 * np.log10(np.maximum(power, 0.0) / denom)
        return db.tolist()
