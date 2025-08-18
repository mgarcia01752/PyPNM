# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia

from __future__ import annotations

from typing import Iterable, Sequence, Tuple, List, Dict, Union, Final
import numpy as np

__all__: Final = ["LinearRegression1D"]  # explicit public surface

# Internal numeric-like alias (kept private)
Number = Union[int, float, np.number]


class LinearRegression1D:
    """
    Robust 1D linear regression (y = m*x + b) with validation, metrics, and a small API.

    Features
    --------
    - Optional x-values; if omitted, uses 0..N-1.
    - Filters out non-finite (NaN/Inf) pairs before fitting.
    - Clear errors for length mismatch, insufficient points, or near-zero x-variance.
    - Provides slope, intercept, R², RMSE, residuals, fitted values, and predictions.
    - Convenience accessors for the regression line (full series or just endpoints).
    - Namespace-safe: only `LinearRegression1D` is exported via `__all__`.

    Parameters
    ----------
    y_values : Iterable[Number]
        Sequence of y-values.
    x_values : Iterable[Number] | None, optional
        Sequence of x-values. If None, uses range(len(y_values)).
    dtype : type, optional
        Numpy dtype for coercion (default: np.float64).

    Attributes
    ----------
    x : np.ndarray
        Cleaned, finite x-values used for fit.
    y : np.ndarray
        Cleaned, finite y-values used for fit.
    n : int
        Number of samples used.
    slope : float
        Fitted slope (m).
    intercept : float
        Fitted intercept (b).
    r2 : float
        Coefficient of determination on training data.
    rmse : float
        Root Mean Squared Error on training data.
    """

    __slots__ = ("x", "y", "n", "slope", "intercept", "r2", "rmse")

    def __init__(
        self,
        y_values: Iterable[Number],
        x_values: Iterable[Number] | None = None,
        *,
        dtype: type = np.float64,
    ) -> None:
        y_arr = np.asarray(list(y_values), dtype=dtype)
        x_arr = (
            np.arange(len(y_arr), dtype=dtype)
            if x_values is None
            else np.asarray(list(x_values), dtype=dtype)
        )

        if x_arr.shape != y_arr.shape:
            raise ValueError("x and y must have the same length and shape.")

        # Keep only finite pairs
        mask = np.isfinite(x_arr) & np.isfinite(y_arr)
        x_clean = x_arr[mask]
        y_clean = y_arr[mask]

        if x_clean.size < 2:
            raise ValueError("At least two finite (x, y) points are required.")

        # Guard against singular design matrix
        x_var = np.var(x_clean)
        if not np.isfinite(x_var) or x_var <= np.finfo(dtype).eps:
            raise ValueError("x has zero or near-zero variance; cannot fit a line.")

        # Least squares fit: A @ theta ≈ y, with A = [x, 1]
        A = np.vstack([x_clean, np.ones_like(x_clean)]).T
        theta, *_ = np.linalg.lstsq(A, y_clean, rcond=None)  # [slope, intercept]
        slope, intercept = float(theta[0]), float(theta[1])

        # Metrics
        y_hat = slope * x_clean + intercept
        residuals = y_clean - y_hat
        ss_res = float(np.sum(residuals**2))
        y_mean = float(np.mean(y_clean))
        ss_tot = float(np.sum((y_clean - y_mean)**2))
        eps = float(np.finfo(dtype).eps)

        # Robust R² with constant-y handling
        if ss_tot <= eps:
            # All y equal: perfect fit -> R²=1.0, otherwise 0.0
            r2 = 1.0 if ss_res <= eps else 0.0
        else:
            r2 = 1.0 - ss_res / ss_tot

        rmse = float(np.sqrt(ss_res / x_clean.size))

        # Store
        self.x = x_clean
        self.y = y_clean
        self.n = int(x_clean.size)
        self.slope = slope
        self.intercept = intercept
        self.r2 = float(r2)
        self.rmse = float(rmse)

    # --------------------------
    # Public API
    # --------------------------

    def to_list(self) -> List[float]:
        """Return `[slope, intercept, r2]` for compact consumption."""
        return [self.slope, self.intercept, self.r2]

    def to_dict(self) -> Dict[str, float]:
        """Return a detailed mapping of results and metrics."""
        return {
            "slope": self.slope,
            "intercept": self.intercept,
            "r2": self.r2,
            "rmse": self.rmse,
            "n": float(self.n),
        }

    def predict(self, x_new: Number | Sequence[Number] | np.ndarray) -> np.ndarray:
        """Predict y for new x values."""
        x_arr = np.asarray(x_new, dtype=np.float64)
        return self.slope * x_arr + self.intercept

    def fitted_values(self) -> np.ndarray:
        """Return fitted y-hat for training x."""
        return self.slope * self.x + self.intercept

    def residuals(self) -> np.ndarray:
        """Return residuals y - y_hat for training data."""
        return self.y - self.fitted_values()

    def params(self) -> Tuple[float, float]:
        """Return `(slope, intercept)`."""
        return self.slope, self.intercept

    def regression_line(self, y_axis_only:bool=True) -> Union[np.ndarray, Tuple[np.ndarray, np.ndarray]]:
        """
        Return the fitted regression line as `(x, y_hat)` over the training domain.

        """
        if y_axis_only:
            return self.fitted_values()
        else:
            return self.x, self.fitted_values()

    def regression_endpoints(self) -> Tuple[Tuple[float, float], Tuple[float, float]]:
        """
        Return two endpoints of the fitted line at the min and max of training x.

        Useful when you want to draw the line with just two points instead of
        plotting the entire series.

        Returns
        -------
        ((float, float), (float, float))
            (x_min, y_hat_min), (x_max, y_hat_max)
        """
        x0 = float(self.x.min())
        x1 = float(self.x.max())
        return (x0, self.slope * x0 + self.intercept), (x1, self.slope * x1 + self.intercept)

    def __repr__(self) -> str:
        return (
            f"LinearRegression1D(n={self.n}, slope={self.slope:.6g}, "
            f"intercept={self.intercept:.6g}, r2={self.r2:.6g}, rmse={self.rmse:.6g})"
        )
