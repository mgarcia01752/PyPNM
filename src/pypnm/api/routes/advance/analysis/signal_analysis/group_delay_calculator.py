# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia

from __future__ import annotations

import numpy as np
from typing import Sequence, Union, Tuple, List, Literal, Final
from numpy.typing import NDArray

from pydantic import BaseModel, Field, ConfigDict, field_validator

from pypnm.lib.types import FrequencyHz, FloatSeries, TwoDFloatSeries, ComplexArray


# Provide a Literal-typed constant to satisfy Pylance when passing the alias kwarg.
COMPLEX_LITERAL: Final[Literal["[Real, Imaginary]"]] = "[Real, Imaginary]"


# ──────────────────────────────────────────────────────────────
# Models (scoped to GroupDelayCalculator)
# ──────────────────────────────────────────────────────────────
class GroupDelayCalculatorDatasetInfo(BaseModel):
    """Shape metadata for a GroupDelayCalculator dataset."""
    model_config = ConfigDict(str_strip_whitespace=True)

    subcarriers: int = Field(..., description="Number of subcarriers (K)")
    snapshots:  int = Field(..., description="Number of snapshots (M)")

    @field_validator("subcarriers", "snapshots")
    @classmethod
    def _positive(cls, v: int) -> int:
        if v < 1:
            raise ValueError("Values must be >= 1.")
        return v


class GroupDelayCalculatorFullModel(BaseModel):
    """Per-subcarrier group delay for the averaged channel."""
    model_config = ConfigDict(str_strip_whitespace=True)

    freqs: List[FrequencyHz] = Field(..., description="K-length frequency axis (Hz)")
    tau_g: FloatSeries       = Field(..., description="K-length group delay (s)")

    @field_validator("tau_g")
    @classmethod
    def _match_len(cls, tau_g: FloatSeries, info) -> FloatSeries:
        freqs = info.data.get("freqs", [])
        if len(freqs) != len(tau_g):
            raise ValueError(f"Length mismatch: freqs={len(freqs)} vs tau_g={len(tau_g)}.")
        return tau_g


class GroupDelayCalculatorSnapshotModel(BaseModel):
    """Per-snapshot group delay matrix."""
    model_config = ConfigDict(str_strip_whitespace=True)

    taus: TwoDFloatSeries = Field(..., description="M×K group delay matrix (s)")

    @field_validator("taus")
    @classmethod
    def _rectangular(cls, v: TwoDFloatSeries) -> TwoDFloatSeries:
        if len(v) < 1 or len(v[0]) < 1:
            raise ValueError("Snapshot matrix must be non-empty M×K.")
        k = len(v[0])
        for row in v:
            if len(row) != k:
                raise ValueError("Snapshot matrix must be rectangular (all rows same length).")
        return v

    def shape(self) -> Tuple[int, int]:
        return len(self.taus), len(self.taus[0])


class GroupDelayCalculatorMedianModel(BaseModel):
    """Median group delay across snapshots for each subcarrier."""
    model_config = ConfigDict(str_strip_whitespace=True)

    freqs:   List[FrequencyHz] = Field(..., description="K-length frequency axis (Hz)")
    tau_med: FloatSeries       = Field(..., description="K-length median group delay (s)")

    @field_validator("tau_med")
    @classmethod
    def _match_len(cls, tau_med: FloatSeries, info) -> FloatSeries:
        freqs = info.data.get("freqs", [])
        if len(freqs) != len(tau_med):
            raise ValueError(f"Length mismatch: freqs={len(freqs)} vs tau_med={len(tau_med)}.")
        return tau_med


class GroupDelayCalculatorModel(BaseModel):
    """Canonical serialized payload for GroupDelayCalculator outputs."""
    model_config = ConfigDict(str_strip_whitespace=True, populate_by_name=True)

    dataset_info:         GroupDelayCalculatorDatasetInfo   = Field(..., description="Dataset shape metadata")
    freqs:                List[FrequencyHz]                 = Field(..., description="K-length frequency axis (Hz)")
    complex_unit:         Literal["[Real, Imaginary]"]      = Field("[Real, Imaginary]", alias="complex", description="Complex encoding")
    H_raw:                List[ComplexArray]                = Field(..., description="M×K complex channel estimates as (re, im)")
    H_avg:                ComplexArray                      = Field(..., description="K complex average across snapshots as (re, im)")
    group_delay_full:     GroupDelayCalculatorFullModel     = Field(..., description="Per-subcarrier group delay for averaged channel")
    snapshot_group_delay: GroupDelayCalculatorSnapshotModel = Field(..., description="Per-snapshot group delay matrix")
    median_group_delay:   GroupDelayCalculatorMedianModel   = Field(..., description="Median group delay across snapshots")

    @staticmethod
    def _is_pair(x: object) -> bool:
        if isinstance(x, (list, tuple)) and len(x) == 2:
            a, b = x
            return isinstance(a, (int, float)) and isinstance(b, (int, float))
        return False

    @field_validator("H_avg")
    @classmethod
    def _coerce_and_check_avg(cls, v: ComplexArray, info) -> ComplexArray:
        freqs = info.data.get("freqs", [])
        out: ComplexArray = []
        for item in v:
            if not cls._is_pair(item):
                raise ValueError("H_avg must contain (re, im) numeric pairs; no complex objects.")
            re, im = float(item[0]), float(item[1])  # type: ignore[index]
            out.append((re, im))
        if len(out) != len(freqs):
            raise ValueError(f"H_avg length {len(out)} must match freqs length {len(freqs)}.")
        return out

    @field_validator("H_raw")
    @classmethod
    def _coerce_and_check_raw(cls, v: List[ComplexArray], info) -> List[ComplexArray]:
        freqs = info.data.get("freqs", [])
        if not v or not v[0]:
            raise ValueError("H_raw must be non-empty M×K.")
        K = len(freqs)
        out: List[ComplexArray] = []
        for row in v:
            if len(row) != K:
                raise ValueError("H_raw must be rectangular and match frequency axis length.")
            row_out: ComplexArray = []
            for item in row:
                if not cls._is_pair(item):
                    raise ValueError("H_raw must contain (re, im) numeric pairs; no complex objects.")
                re, im = float(item[0]), float(item[1])  # type: ignore[index]
                row_out.append((re, im))
            out.append(row_out)
        return out

    @field_validator("snapshot_group_delay")
    @classmethod
    def _shape_match_snapshots(cls, v: GroupDelayCalculatorSnapshotModel, info) -> GroupDelayCalculatorSnapshotModel:
        k = len(info.data.get("freqs", []))
        _, k_taus = v.shape()
        if k_taus != k:
            raise ValueError(f"snapshot_group_delay K={k_taus} must match freqs length {k}.")
        return v


# ──────────────────────────────────────────────────────────────
# Calculator
# ──────────────────────────────────────────────────────────────
class GroupDelayCalculator:
    """Compute group delay from per-subcarrier complex channel estimates."""

    def __init__(
        self,
        H: Union[
            Sequence[complex],
            Sequence[Sequence[complex]],
            Sequence[Sequence[float]]
        ],
        freqs: Sequence[float]
    ):
        """Initialize the calculator with channel estimates and frequencies."""
        freqs_arr: NDArray[np.float64] = np.asarray(freqs, dtype=np.float64)
        if freqs_arr.ndim != 1:
            raise ValueError("freqs must be a 1D sequence of frequencies.")
        if freqs_arr.size < 2:
            raise ValueError("At least two frequency points are required to compute group delay.")
        self.f: NDArray[np.float64] = freqs_arr.reshape(-1)

        H_arr_raw = np.asarray(H)
        if H_arr_raw.ndim == 2 and H_arr_raw.shape[1] == 2 and not np.iscomplexobj(H_arr_raw):
            H_arr_raw = H_arr_raw[np.newaxis, :, :]
        if H_arr_raw.ndim == 3 and H_arr_raw.shape[2] == 2 and not np.iscomplexobj(H_arr_raw):
            H_complex: NDArray[np.complex128] = H_arr_raw[..., 0] + 1j * H_arr_raw[..., 1]
        else:
            H_complex = np.asarray(H_arr_raw, dtype=np.complex128)

        if H_complex.ndim == 1:
            if H_complex.size != self.f.size:
                raise ValueError("Length of H must match length of freqs.")
            self.H_raw: NDArray[np.complex128] = H_complex.reshape(1, -1)
        elif H_complex.ndim == 2:
            M, K = H_complex.shape
            if K != self.f.size:
                raise ValueError(f"Each snapshot must have length {self.f.size}, got {K}")
            self.H_raw = H_complex
        else:
            raise ValueError("H must be 1D complex, 2D complex, or real/imag array of shape (K,2) or (M,K,2).")

        self.H_avg: NDArray[np.complex128] = np.mean(self.H_raw, axis=0)

    def compute_group_delay_full(self) -> Tuple[NDArray[np.float64], NDArray[np.float64]]:
        """Compute per-subcarrier group delay on the averaged channel."""
        phi = np.unwrap(np.angle(self.H_avg))
        K = self.f.size
        tau_g: NDArray[np.float64] = np.zeros(K, dtype=np.float64)
        df = np.diff(self.f)
        if np.any(df == 0.0):
            raise ValueError("freqs contains duplicate values; cannot compute derivative.")
        tau_g[0] = -(phi[1] - phi[0]) / (2 * np.pi * df[0])
        for k in range(1, K - 1):
            tau_g[k] = -(phi[k + 1] - phi[k - 1]) / (2 * np.pi * (self.f[k + 1] - self.f[k - 1]))
        tau_g[-1] = -(phi[-1] - phi[-2]) / (2 * np.pi * df[-1])
        return self.f, tau_g

    def snapshot_group_delay(self) -> NDArray[np.float64]:
        """Compute group delay for each snapshot."""
        M, K = self.H_raw.shape
        taus: NDArray[np.float64] = np.zeros((M, K), dtype=np.float64)
        df = np.diff(self.f)
        if np.any(df == 0.0):
            raise ValueError("freqs contains duplicate values; cannot compute derivative.")
        for m in range(M):
            phi = np.unwrap(np.angle(self.H_raw[m]))
            taus[m, 0] = -(phi[1] - phi[0]) / (2 * np.pi * df[0])
            for k in range(1, K - 1):
                taus[m, k] = -(phi[k + 1] - phi[k - 1]) / (2 * np.pi * (self.f[k + 1] - self.f[k - 1]))
            taus[m, -1] = -(phi[-1] - phi[-2]) / (2 * np.pi * df[-1])
        return taus

    def median_group_delay(self) -> Tuple[NDArray[np.float64], NDArray[np.float64]]:
        """Compute the median group delay across snapshots."""
        taus = self.snapshot_group_delay()
        tau_med: NDArray[np.float64] = np.median(taus, axis=0)
        return self.f, tau_med

    @staticmethod
    def _complex_matrix_to_pairs(mat: NDArray[np.complex128]) -> List[ComplexArray]:
        """Encode a complex matrix as `(re, im)` pairs."""
        M, K = mat.shape
        out: List[ComplexArray] = []
        for m in range(M):
            row: ComplexArray = [(float(np.real(v)), float(np.imag(v))) for v in mat[m]]
            out.append(row)
        return out

    @staticmethod
    def _complex_vector_to_pairs(vec: NDArray[np.complex128]) -> ComplexArray:
        """Encode a complex vector as `(re, im)` pairs."""
        return [(float(np.real(v)), float(np.imag(v))) for v in vec]

    def to_model(self) -> GroupDelayCalculatorModel:
        """Build a `GroupDelayCalculatorModel` with all computed outputs."""
        M, K = self.H_raw.shape
        dataset = GroupDelayCalculatorDatasetInfo(subcarriers=K, snapshots=M)

        freqs_list: List[FrequencyHz] = [FrequencyHz(float(f)) for f in self.f.tolist()]
        H_raw_pairs: List[ComplexArray] = self._complex_matrix_to_pairs(self.H_raw)
        H_avg_pairs: ComplexArray = self._complex_vector_to_pairs(self.H_avg)

        f_full, tau_full = self.compute_group_delay_full()
        taus_snap = self.snapshot_group_delay()
        f_med, tau_med = self.median_group_delay()

        full = GroupDelayCalculatorFullModel(
            freqs=[FrequencyHz(float(f)) for f in f_full.tolist()],
            tau_g=[float(x) for x in tau_full.tolist()],
        )
        snaps = GroupDelayCalculatorSnapshotModel(
            taus=[[float(x) for x in row] for row in taus_snap.tolist()],
        )
        med = GroupDelayCalculatorMedianModel(
            freqs=[FrequencyHz(float(f)) for f in f_med.tolist()],
            tau_med=[float(x) for x in tau_med.tolist()],
        )

        # Pass the alias explicitly with a Literal-typed constant to satisfy Pylance.
        return GroupDelayCalculatorModel(
            dataset_info=dataset,
            freqs=freqs_list,
            complex=COMPLEX_LITERAL,  # alias kwarg; typed as Literal[...] so no error
            H_raw=H_raw_pairs,
            H_avg=H_avg_pairs,
            group_delay_full=full,
            snapshot_group_delay=snaps,
            median_group_delay=med,
        )

    def to_dict(self) -> dict:
        """Deprecated shim that returns `to_model().model_dump()` (by JSON aliases)."""
        return self.to_model().model_dump(by_alias=True)
