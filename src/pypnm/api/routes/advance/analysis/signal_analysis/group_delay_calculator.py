# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia

import numpy as np
from typing import Sequence, Union, Tuple, Dict, Any

class GroupDelayCalculator:
    """
    Compute group delay from per-subcarrier complex channel estimates.
    
    Supports:
        - Single snapshot or multiple snapshots
        - Complex arrays or real/imaginary pairs

    Accepted input formats for `H`:
        - 1D list/array of complex values (length K)
        - 2D list/array of shape (M, K) of complex values
        - 2D array of shape (K, 2) → one snapshot of real/imag pairs
        - 3D array of shape (M, K, 2) → M snapshots of real/imag pairs

    Parameters:
        H (array-like): Channel estimates (complex or real/imag format)
        freqs (array-like): 1D array of subcarrier frequencies (Hz)

    Raises:
        ValueError: For invalid input shapes or dimension mismatches

    Attributes:
        f (np.ndarray): 1D frequency array (length K)
        H_raw (np.ndarray): Shape (M, K), raw complex data
        H_avg (np.ndarray): Shape (K,), average channel response
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
        # Validate frequency shape BEFORE flattening
        freqs = np.asarray(freqs, dtype=float)
        if freqs.ndim != 1:
            raise ValueError("freqs must be a 1D sequence of frequencies.")
        self.f = freqs.flatten()

        # Parse input H to complex array
        H_arr_raw = np.asarray(H)

        # Real/imag formats
        if H_arr_raw.ndim == 2 and H_arr_raw.shape[1] == 2 and not np.iscomplexobj(H_arr_raw):
            H_arr_raw = H_arr_raw[np.newaxis, :, :]  # Add batch dim
        if H_arr_raw.ndim == 3 and H_arr_raw.shape[2] == 2 and not np.iscomplexobj(H_arr_raw):
            H_complex = H_arr_raw[..., 0] + 1j * H_arr_raw[..., 1]
        else:
            H_complex = np.asarray(H_arr_raw, dtype=complex)

        # Validate and reshape
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
            raise ValueError("H must be 1D complex, 2D complex, or real/imag array of shape (K,2) or (M,K,2).")

        # Snapshot-averaged channel
        self.H_avg = np.mean(self.H_raw, axis=0)

    def compute_group_delay_full(self) -> Tuple[np.ndarray, np.ndarray]:
        """
        Compute group delay for the average channel H_avg at each subcarrier.

        Uses:
            - forward difference at index 0
            - central difference at k=1...K-2
            - backward difference at index K-1

        Returns:
            Tuple[freqs, tau_g]:
                freqs: ndarray, shape (K,)
                tau_g: ndarray, group delay in seconds, shape (K,)
        """
        phi = np.unwrap(np.angle(self.H_avg))
        K = self.f.size
        tau_g = np.zeros(K)
        df = np.diff(self.f)

        tau_g[0] = -(phi[1] - phi[0]) / (2 * np.pi * df[0])
        for k in range(1, K - 1):
            tau_g[k] = -(phi[k + 1] - phi[k - 1]) / (
                2 * np.pi * (self.f[k + 1] - self.f[k - 1])
            )
        tau_g[-1] = -(phi[-1] - phi[-2]) / (2 * np.pi * df[-1])
        return self.f, tau_g

    def snapshot_group_delay(self) -> np.ndarray:
        """
        Compute group delay for each snapshot in H_raw.

        Returns:
            ndarray: shape (M, K), one row per snapshot
        """
        M, K = self.H_raw.shape
        taus = np.zeros((M, K))
        df = np.diff(self.f)

        for m in range(M):
            phi = np.unwrap(np.angle(self.H_raw[m]))
            taus[m, 0] = -(phi[1] - phi[0]) / (2 * np.pi * df[0])
            for k in range(1, K - 1):
                taus[m, k] = -(phi[k + 1] - phi[k - 1]) / (
                    2 * np.pi * (self.f[k + 1] - self.f[k - 1])
                )
            taus[m, -1] = -(phi[-1] - phi[-2]) / (2 * np.pi * df[-1])

        return taus

    def median_group_delay(self) -> Tuple[np.ndarray, np.ndarray]:
        """
        Compute the median group delay across all snapshots for each subcarrier.

        Returns:
            Tuple[freqs, tau_med]:
                freqs: ndarray of shape (K,)
                tau_med: median group delay values, shape (K,)
        """
        taus = self.snapshot_group_delay()
        tau_med = np.median(taus, axis=0)
        return self.f, tau_med

    def dataset_info(self) -> Dict[str, Any]:
        """
        Return the dataset shape information.

        Returns:
            Dict[str, int]: {'subcarriers': K, 'snapshots': M}
        """
        M, K = self.H_raw.shape
        return {'subcarriers': K, 'snapshots': M}

    def to_dict(self) -> Dict[str, Any]:
        """
        Serialize group delay analysis into a dictionary.

        Returns:
            Dict[str, Any]: All input, metadata, and computed outputs.
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
