# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia

import numpy as np
from typing import Sequence, Union, Tuple, Dict, Any

class GroupDelayCalculator:
    """
    Compute group delay from per-subcarrier complex channel estimates,
    supporting single, multi-snapshot, and real/imag input arrays.

    Accepted input shapes for H:
      - 1D array-like of complex values (length K)
      - 2D array-like of shape (M, K) of complex values
      - 2D array-like of shape (K, 2) representing one snapshot of real/imag pairs
      - 3D array-like of shape (M, K, 2) of real/imag pairs

    Methods:
      - compute_group_delay_full() -> (freqs, tau_g) : full-length per-subcarrier delays
      - snapshot_group_delay()    -> np.ndarray      : full-length per-snapshot delays
      - median_group_delay()      -> (freqs, tau_med): median delay per subcarrier
      - dataset_info()            -> dict            : dataset dimensions
      - to_dict()                 -> dict            : comprehensive output
    """

    def __init__(
        self,
        H: Union[
            Sequence[complex],
            Sequence[Sequence[complex]],
            Sequence[Sequence[float]]
        ],
        freqs: Sequence[float]
    ):
        # Frequency array
        self.f = np.asarray(freqs, dtype=float).flatten()
        if self.f.ndim != 1:
            raise ValueError("freqs must be a 1D sequence of frequencies.")

        # Raw input to array
        H_arr_raw = np.asarray(H)
        # If 2D real/imag of shape (K,2), treat as single snapshot
        if H_arr_raw.ndim == 2 and H_arr_raw.shape[1] == 2 and not np.iscomplexobj(H_arr_raw):
            H_arr_raw = H_arr_raw[np.newaxis, :, :]
        # If 3D real/imag shape (M, K, 2)
        if H_arr_raw.ndim == 3 and H_arr_raw.shape[2] == 2 and not np.iscomplexobj(H_arr_raw):
            # Interpret last axis as [real, imag]
            H_complex = H_arr_raw[..., 0] + 1j * H_arr_raw[..., 1]
        else:
            # Cast directly to complex, supports 1D or 2D
            H_complex = np.asarray(H_arr_raw, dtype=complex)

        # Now require H_complex to be 1D or 2D
        if H_complex.ndim == 1:
            if H_complex.size != self.f.size:
                raise ValueError("Length of H must match length of freqs.")
            self.H_raw = H_complex.reshape(1, -1)
        elif H_complex.ndim == 2:
            M, K = H_complex.shape
            if K != self.f.size:
                raise ValueError(f"Each snapshot must have length {self.f.size}, got {K}")
            self.H_raw = H_complex
        else:
            raise ValueError(
                "H must be 1D complex, 2D complex, or real/imag array of shape (K,2) or (M,K,2)."
            )

        # Coherently average across snapshots
        self.H_avg = np.mean(self.H_raw, axis=0)

    def compute_group_delay_full(self) -> Tuple[np.ndarray, np.ndarray]:
        """
        Compute group delay at each subcarrier frequency with length K:
          - forward difference at index 0
          - central difference for k=1..K-2
          - backward difference at index K-1
        Returns:
          freqs: np.ndarray shape (K,)
          tau_g: np.ndarray shape (K,), group delay in seconds
        """
        phi = np.unwrap(np.angle(self.H_avg))
        K = self.f.size
        tau_g = np.zeros(K)
        df = np.diff(self.f)
        # forward difference
        tau_g[0] = -(phi[1] - phi[0]) / (2 * np.pi * df[0])
        # central differences
        for k in range(1, K-1):
            tau_g[k] = -(phi[k+1] - phi[k-1]) / (
                2 * np.pi * (self.f[k+1] - self.f[k-1])
            )
        # backward difference
        tau_g[-1] = -(phi[-1] - phi[-2]) / (2 * np.pi * df[-1])
        return self.f, tau_g

    def snapshot_group_delay(self) -> np.ndarray:
        """
        Compute group delay for each snapshot, full length per subcarrier.
        Returns:
          array of shape (M, K).
        """
        M, K = self.H_raw.shape
        taus = np.zeros((M, K))
        for m in range(M):
            phi = np.unwrap(np.angle(self.H_raw[m]))
            df = np.diff(self.f)
            taus[m, 0] = -(phi[1] - phi[0]) / (2 * np.pi * df[0])
            for k in range(1, K-1):
                taus[m, k] = -(phi[k+1] - phi[k-1]) / (
                    2 * np.pi * (self.f[k+1] - self.f[k-1])
                )
            taus[m, -1] = -(phi[-1] - phi[-2]) / (2 * np.pi * df[-1])
        return taus

    def median_group_delay(self) -> Tuple[np.ndarray, np.ndarray]:
        """
        Compute the median group delay across snapshots per subcarrier.
        Returns:
          freqs: np.ndarray shape (K,)
          tau_med: np.ndarray shape (K,)
        """
        taus = self.snapshot_group_delay()
        tau_med = np.median(taus, axis=0)
        return self.f, tau_med

    def dataset_info(self) -> Dict[str, Any]:
        """
        Return dataset dimensions: number of subcarriers (K) and snapshots (M).
        """
        M, K = self.H_raw.shape
        return {'subcarriers': K, 'snapshots': M}

    def to_dict(self) -> Dict[str, Any]:
        """
        Return all relevant data and computed metrics as a dictionary.
        """
        freqs_list = self.f.tolist()
        H_raw_list = [row.tolist() for row in self.H_raw]
        H_avg_list = self.H_avg.tolist()

        f_full, tau_full = self.compute_group_delay_full()
        tau_snap = self.snapshot_group_delay()
        f_med, tau_med = self.median_group_delay()

        return {
            'dataset_info': self.dataset_info(),
            'freqs': freqs_list,
            'H_raw': H_raw_list,
            'H_avg': H_avg_list,
            'group_delay_full': {
                'freqs': f_full.tolist(),
                'tau_g': tau_full.tolist()
            },
            'snapshot_group_delay': tau_snap.tolist(),
            'median_group_delay': {
                'freqs': f_med.tolist(),
                'tau_med': tau_med.tolist()
            }
        }
