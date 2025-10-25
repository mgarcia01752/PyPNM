# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia

from __future__ import annotations

import numpy as np
from pypnm.lib.types import FloatSeries

class DbLinearConverter:
    """
    Convert between dB and linear scale for lists of floats.

    Notes
    -----
    - Uses power ratio convention: dB = 10 * log10(linear).
    - Input values are expected to be non-negative when converting
      from linear → dB. Zero maps to -inf (handled as float("-inf")).
    - Output length always matches input length.
    """

    @staticmethod
    def db_to_linear(values: FloatSeries) -> FloatSeries:
        """
        Convert dB values to linear scale.

        Parameters
        ----------
        values : FloatSeries
            Input values in dB.

        Returns
        -------
        FloatSeries
            Values converted to linear scale.
        """
        arr = np.asarray(values, dtype=float)
        return (10 ** (arr / 10.0)).tolist()

    @staticmethod
    def linear_to_db(values: FloatSeries) -> FloatSeries:
        """
        Convert linear values to dB scale.

        Parameters
        ----------
        values : FloatSeries
            Input values in linear scale (must be >= 0).

        Returns
        -------
        FloatSeries
            Values converted to dB scale.
        """
        arr = np.asarray(values, dtype=float)
        with np.errstate(divide="ignore"):
            out = 10.0 * np.log10(arr)
        return out.tolist()
