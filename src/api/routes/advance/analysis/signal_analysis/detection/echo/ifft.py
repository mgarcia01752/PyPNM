# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia

import numpy as np
from typing import Sequence, Union, Dict, Any, Tuple

class IfftEchoDetector:
    """
    FFT/IFFT-based echo detector for OFDM channel estimates,
    supporting various input formats and exposing detailed outputs.

    Accepted input shapes for `freq_data`:
      - 1D complex array of shape (N,)
      - 2D complex array of shape (M, N) for multiple snapshots
      - 2D real/imag pairs of shape (N, 2) for a single snapshot
      - 3D real/imag array of shape (M, N, 2) for multiple snapshots

    Constructor arguments:
      - `freq_data`: Frequency-domain channel estimates (complex or real/imag lists)
      - `sample_rate`: Sampling rate in **Hz** (samples per second) for generating the IFFT time axis (Δt = 1/sample_rate)
      - `prop_speed_frac`: Velocity factor (fraction of light speed) for distance calculation

    Methods:
      - compute_time_response() -> (time_axis, time_response)
      - detect_reflection() -> dict of echo metrics
      - compute_freq_response() -> np.ndarray
      - to_dict() -> dict of all inputs/outputs
    """
    # Speed of light in vacuum (m/s)
    c0 = 299_792_458

    def __init__(
        self,
        freq_data: Union[
            Sequence[complex],
            Sequence[Sequence[complex]],
            Sequence[Sequence[float]]
        ],
        sample_rate: float,
        prop_speed_frac: float = 0.87
    ):
        """
        Initialize the echo detector.

        Parameters:
        freq_data : complex or real/imag array
            Frequency-domain channel estimates. Supported shapes:
            - (N,) complex array
            - (M, N) complex array for multiple snapshots
            - (N, 2) real/imag pairs for one snapshot
            - (M, N, 2) real/imag pairs for multiple snapshots
        sample_rate : float
            Sampling rate in Hz (e.g., `64 * subcarrier_spacing`).
        prop_speed_frac : float, optional
            Velocity factor (fraction of c0) in the propagation medium.
        """
        # Convert raw input to complex array
        data = np.asarray(freq_data)

        # Handle real/imag inputs
        if data.ndim == 3 and data.shape[2] == 2 and not np.iscomplexobj(data):
            # (M, N, 2) -> (M, N) complex
            H_complex = data[..., 0] + 1j * data[..., 1]
        elif data.ndim == 2 and data.shape[1] == 2 and not np.iscomplexobj(data):
            # (N, 2) -> reshape to (1, N)
            H_complex = (data[np.newaxis, ..., 0] + 1j * data[np.newaxis, ..., 1])
        else:
            # Assume 1D or 2D complex
            H_complex = data.astype(np.complex128)

        # Ensure 2D snapshot array
        if H_complex.ndim == 1:
            H_snap = H_complex.reshape(1, -1)
        elif H_complex.ndim == 2:
            H_snap = H_complex
        else:
            raise ValueError(
                "freq_data must be 1D complex, 2D complex, or real/imag array of shape"
                " (N,2) or (M,N,2)."
            )

        # Store snapshots and compute coherent average
        self.H_snap = H_snap
        self.H_avg = H_snap.mean(axis=0)
        self.freq_data = self.H_avg

        # Sampling and propagation settings
        self.sample_rate = sample_rate
        self.prop_speed = self.c0 * prop_speed_frac
        self.N = self.freq_data.size

        # Placeholders for time-domain results
        self.time_axis: np.ndarray = None       # type: ignore
        self.time_response: np.ndarray = None   # type: ignore

    def compute_time_response(self) -> Tuple[np.ndarray, np.ndarray]:
        """
        Compute and return the time-domain impulse response via IFFT.

        Returns:
        --------
        time_axis : np.ndarray of shape (N,)
            Time stamps in seconds (Δt = 1/sample_rate).
        time_response : np.ndarray of shape (N,)
            Complex impulse response.
        """
        h = np.fft.ifft(self.freq_data, n=self.N)
        t = np.arange(self.N) / self.sample_rate
        self.time_response = h
        self.time_axis = t
        return t, h

    def detect_reflection(
        self,
        threshold_frac: float = 0.2,
        min_separation: int = 1
    ) -> Dict[str, Any]:
        """
        Locate the direct path and first echo in |h(t)|.

        Returns:
        --------
        dict with keys:
          - direct_index: int
          - echo_index: int
          - time_direct_s: float
          - time_echo_s: float
          - reflection_delay_s: float
          - reflection_distance_m: float
        """
        if self.time_response is None:
            self.compute_time_response()

        mag = np.abs(self.time_response)
        i0 = int(np.argmax(mag))
        amp0 = mag[i0]
        thresh = threshold_frac * amp0

        for idx in range(i0 + min_separation, self.N):
            if mag[idx] >= thresh:
                ie = idx
                break
        else:
            raise RuntimeError("No echo found above threshold_frac")

        t0 = self.time_axis[i0]
        te = self.time_axis[ie]
        delay = te - t0
        dist = (delay * self.prop_speed) / 2

        return {
            "direct_index": i0,
            "echo_index": ie,
            "time_direct_s": t0,
            "time_echo_s": te,
            "reflection_delay_s": delay,
            "reflection_distance_m": dist
        }

    def compute_freq_response(
        self,
        time_data: Sequence[complex]
    ) -> np.ndarray:
        """
        Compute the frequency response (FFT) of a time-domain signal.
        """
        td = np.asarray(time_data, dtype=complex).flatten()
        return np.fft.fft(td, n=td.size)

    def to_dict(self) -> Dict[str, Any]:
        """
        Return all relevant inputs and computed outputs as a dict.

        Always includes:
          - 'reflection': echo metrics
          - 'sample_rate': in Hz
          - 'prop_speed': in m/s
          - 'N': number of subcarriers
          - 'H_snap': list of snapshots (complex values)
          - 'H_avg': averaged channel (complex values)

        If time-response has been computed, also includes:
          - 'time_axis' and 'time_response'
        """
        result = {
            "reflection": self.detect_reflection(),
            "sample_rate": self.sample_rate,
            "prop_speed": self.prop_speed,
            "N": self.N,
            "H_snap": [[complex(val) for val in row] for row in self.H_snap],
            "H_avg": [complex(val) for val in self.H_avg]
        }
        if self.time_response is not None:
            result.update({
                "time_axis": self.time_axis.tolist(),
                "time_response": [complex(val) for val in self.time_response]
            })
        return result
