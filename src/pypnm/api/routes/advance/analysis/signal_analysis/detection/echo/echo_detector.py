# SPDX-License-Identifier: MIT
# Copyright (c) 2025

from __future__ import annotations

import numpy as np
from typing import List, Optional, Sequence, Tuple
from numpy.typing import NDArray
from pydantic import BaseModel, Field, ConfigDict, field_validator

from pypnm.lib.constants import SPEED_OF_LIGHT, FEET_PER_METER, CableType, CableTypes, CABLE_VF
from pypnm.lib.types import ChannelId, ComplexArray, FloatSeries


# ──────────────────────────────────────────────────────────────
# Models
# ──────────────────────────────────────────────────────────────

class EchoDatasetInfo(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    subcarriers: int                    = Field(..., description="Number of frequency bins (N)")
    snapshots: int                      = Field(..., description="Number of snapshots (M)")
    subcarrier_spacing_hz: float        = Field(..., description="Δf (Hz)")
    sample_rate_hz: float               = Field(..., description="fs = N · Δf (Hz)")

    @field_validator("subcarriers", "snapshots")
    @classmethod
    def _ge_one(cls, v: int) -> int:
        if v < 1:
            raise ValueError("Must be >= 1.")
        return v

class TimeResponse(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    n_fft: int                          = Field(..., description="IFFT length used")
    time_axis_s: FloatSeries            = Field(..., description="Time axis (s), length n_fft")
    time_response: ComplexArray         = Field(..., description="Complex values as (re, im) pairs")

    @field_validator("time_axis_s", "time_response")
    @classmethod
    def _match_len(cls, v, info):
        n = info.data.get("n_fft")
        if n is not None and len(v) != n:
            raise ValueError(f"Expected length {n}, got {len(v)}.")
        return v

class EchoPath(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    bin_index: int                      = Field(..., description="Reported index in original-N bins")
    time_s: float                       = Field(..., description="Time at peak (s)")
    amplitude: float                    = Field(..., description="|h| at peak")
    distance_m: float                   = Field(..., description="One-way distance (m)")
    distance_ft: float                  = Field(..., description="One-way distance (ft)")

class EchoReflection(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    direct_index: int                   = Field(..., description="Direct-path bin (original-N domain)")
    echo_index: int                     = Field(..., description="First-echo bin (original-N domain)")
    time_direct_s: float                = Field(..., description="Time at direct-path peak (s)")
    time_echo_s: float                  = Field(..., description="Time at echo peak (s)")
    reflection_delay_s: float           = Field(..., description="Echo delay relative to direct (s)")
    reflection_distance_m: float        = Field(..., description="Estimated echo distance (m, one-way)")
    amp_direct: float                   = Field(..., description="|h| at direct path")
    amp_echo: float                     = Field(..., description="|h| at echo")
    amp_ratio: float                    = Field(..., description="amp_echo / amp_direct")
    threshold_frac: float               = Field(..., description="Threshold as fraction of |h| at direct")
    guard_bins: int                     = Field(..., description="Guard bins skipped after main peak")
    max_delay_s: Optional[float]        = Field(default=None, description="Optional max search window (s)")

class EchoDetectorReport(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, populate_by_name=True)

    channel_id: ChannelId               = Field(..., description="OFDM downstream channel ID")
    dataset: EchoDatasetInfo            = Field(..., description="Dataset shape and sampling")
    cable_type: CableTypes              = Field(default=CableType.RG6.name, description="Cable type used to pick VF")
    velocity_factor: float              = Field(..., description="Velocity factor actually used (0..1)")
    prop_speed_mps: float               = Field(..., description="Propagation speed (m/s)")

    direct_path: EchoPath               = Field(..., description="Strongest path")
    echoes: List[EchoPath]              = Field(..., description="Detected echoes (amplitude-sorted)")

    threshold_frac: float               = Field(..., description="Threshold as fraction of |h| at direct")
    guard_bins: int                     = Field(..., description="Bins skipped after direct peak")
    min_separation_s: float             = Field(..., description="Minimum Δt between echoes")
    max_delay_s: Optional[float]        = Field(default=None, description="Optional search window after direct (s)")
    max_peaks: int                      = Field(..., description="Max echoes returned (not counting direct)")

    time_response: Optional[TimeResponse] = Field(default=None, description="Optional (t,h) for plotting")


# ──────────────────────────────────────────────────────────────
# Detector
# ──────────────────────────────────────────────────────────────

class EchoDetector:
    """
    FFT/IFFT-based echo detector for OFDM channel estimates.

    Accepts frequency-domain data in any of these shapes:
      • (N,) complex
      • (M,N) complex
      • (N,2) real/imag pairs
      • (M,N,2) real/imag pairs

    The IFFT length `n_fft` can be larger than N (zero-padding) to improve
    time sampling. Reported `bin_index` values are always mapped back to the
    original-N domain, while timing and distances use the padded time axis.
    """

    def __init__(
        self,
        freq_data: Sequence[complex] | Sequence[Sequence[complex]] | Sequence[Sequence[float]],
        *,
        subcarrier_spacing_hz: float,
        n_fft: Optional[int]    = None,
        cable_type: CableTypes  = CableType.RG6.name,
        channel_id: ChannelId   = ChannelId(-1),
    ):
        """
        Parameters
        ----------
        freq_data : array-like
            Channel estimates H(f) as complex or (re, im) pairs.
        subcarrier_spacing_hz : float
            Subcarrier spacing Δf (Hz); sample rate is fs = N · Δf.
        n_fft : int | None
            Preset IFFT length to use by default (>= N). Methods can override.
        cable_type : CableType
            Default cable type used for VF if methods do not override.
        channel_id : ChannelId
            Channel identifier to stamp on reports.
        """
        arr = np.asarray(freq_data)

        if arr.ndim == 3 and arr.shape[2] == 2 and not np.iscomplexobj(arr):
            Hc = arr[..., 0] + 1j * arr[..., 1]
        elif arr.ndim == 2 and arr.shape[1] == 2 and not np.iscomplexobj(arr):
            Hc = (arr[np.newaxis, ..., 0] + 1j * arr[np.newaxis, ..., 1])
        else:
            Hc = arr.astype(np.complex128, copy=False)

        if Hc.ndim == 1:
            H_snap = Hc.reshape(1, -1)
        elif Hc.ndim == 2:
            H_snap = Hc
        else:
            raise ValueError("freq_data must be 1D/2D complex, or real/imag (N,2)/(M,N,2).")

        self.H_snap: NDArray[np.complex128] = H_snap
        self.H_avg: NDArray[np.complex128] = H_snap.mean(axis=0)
        self.N: int = int(H_snap.shape[1])
        self.M: int = int(H_snap.shape[0])

        self.delta_f: float = float(subcarrier_spacing_hz)
        self.fs: float = float(self.N * self.delta_f)

        self.channel_id: ChannelId = channel_id
        self.default_cable_type: CableTypes = cable_type
        self._preset_n_fft: Optional[int] = int(n_fft) if n_fft is not None else None

        self._n_fft: Optional[int] = None
        self._t: Optional[NDArray[np.float64]] = None
        self._h: Optional[NDArray[np.complex128]] = None

    @staticmethod
    def _vec_to_pairs(v: NDArray[np.complex128]) -> ComplexArray:
        return [(float(x.real), float(x.imag)) for x in v]

    def _effective_n_fft(self, n_fft: Optional[int]) -> int:
        if n_fft is not None:
            return int(n_fft)
        if self._preset_n_fft is not None:
            return int(self._preset_n_fft)
        return self.N

    def _ensure_time_response(self, n_fft: Optional[int]) -> None:
        n_use = self._effective_n_fft(n_fft)
        if n_use < self.N:
            raise ValueError(f"n_fft ({n_use}) must be >= N ({self.N}).")
        self._h = np.fft.ifft(self.H_avg, n=n_use).astype(np.complex128, copy=False)
        self._t = (np.arange(n_use, dtype=np.float64) / self.fs)
        self._n_fft = n_use

    def _to_N_bins(self, i_raw: int) -> int:
        if self._n_fft is None or self._n_fft == self.N:
            return int(i_raw)
        return int(round(i_raw * self.N / self._n_fft))

    def _default_cable(self, cable_type: Optional[CableTypes]) -> CableTypes:
        return cable_type if cable_type is not None else self.default_cable_type

    # ───────── Public API

    def compute_time_response(self, *, n_fft: Optional[int] = None) -> Tuple[FloatSeries, ComplexArray]:
        """
        Compute the time response h(t) = IFFT{H(f)} with optional zero-padding.

        Parameters
        ----------
        n_fft : int | None
            IFFT length (>= N). If None, uses preset from constructor or N.

        Returns
        -------
        (time_axis_s, time_response_pairs)
            Time axis (seconds) and complex response as (re, im) pairs.
        """
        self._ensure_time_response(n_fft)
        assert self._t is not None and self._h is not None
        return [float(x) for x in self._t.tolist()], self._vec_to_pairs(self._h)

    def detect_first_echo(
        self,
        *,
        cable_type: Optional[CableTypes] = None,
        velocity_factor: Optional[float] = None,
        threshold_frac: float = 0.2,
        guard_bins: int = 1,
        max_delay_s: Optional[float] = None,
        n_fft: Optional[int] = None,
    ) -> EchoReflection:
        """
        Detect the direct path and the first echo peak in |h(t)| above a threshold.
        """
        self._ensure_time_response(n_fft)
        assert self._t is not None and self._h is not None and self._n_fft is not None

        ctype = self._default_cable(cable_type)
        vf = float(velocity_factor) if velocity_factor is not None else float(CABLE_VF[ctype])
        prop_speed = float(SPEED_OF_LIGHT * vf)

        mag = np.abs(self._h).astype(np.float64, copy=False)
        i0_raw = int(np.argmax(mag))
        amp0 = float(mag[i0_raw])
        if amp0 <= 0.0:
            raise RuntimeError("Direct-path magnitude is zero; cannot threshold.")

        thresh = float(threshold_frac) * amp0
        start = int(i0_raw + max(0, int(guard_bins)))

        if max_delay_s is not None and max_delay_s > 0:
            max_bins = int(np.ceil(max_delay_s * self.fs))
            stop = min(mag.size, i0_raw + max_bins + 1)
        else:
            stop = mag.size

        ie_raw: Optional[int] = None
        for i in range(start, stop):
            if mag[i] >= thresh:
                ie_raw = int(i)
                break
        if ie_raw is None:
            raise RuntimeError("No echo found above threshold within the search window.")

        t0 = float(self._t[i0_raw])
        te = float(self._t[ie_raw])
        delay = float(te - t0)
        dist_m = float((delay * prop_speed) / 2.0)
        ratio = float(mag[ie_raw] / amp0) if amp0 > 0 else 0.0

        return EchoReflection(
            direct_index            =   self._to_N_bins(i0_raw),
            echo_index              =   self._to_N_bins(ie_raw),
            time_direct_s           =   t0,
            time_echo_s             =   te,
            reflection_delay_s      =   delay,
            reflection_distance_m   =   dist_m,
            amp_direct              =   amp0,
            amp_echo                =   float(mag[ie_raw]),
            amp_ratio               =   ratio,
            threshold_frac          =   float(threshold_frac),
            guard_bins              =   int(guard_bins),
            max_delay_s             =   float(max_delay_s) if max_delay_s is not None else None,
        )

    def detect_multiple_echoes(
        self,
        *,
        cable_type: Optional[CableTypes] = None,
        velocity_factor: Optional[float] = None,
        threshold_frac: float = 0.2,
        guard_bins: int = 1,
        min_separation_s: float = 0.0,
        max_delay_s: Optional[float] = None,
        max_peaks: int = 5,
        n_fft: Optional[int] = None,
        include_time_response: bool = True,
        channel_id: Optional[ChannelId] = None,
    ) -> EchoDetectorReport:
        """
        Detect local-maxima echoes above threshold, with spacing constraints.

        Parameters
        ----------
        channel_id : ChannelId | None
            Optional override for the channel id to stamp on the report.
        """
        self._ensure_time_response(n_fft)
        assert self._t is not None and self._h is not None and self._n_fft is not None

        mag = np.abs(self._h).astype(np.float64, copy=False)
        i0_raw = int(np.argmax(mag))
        amp0 = float(mag[i0_raw])
        if amp0 <= 0.0:
            raise RuntimeError("Direct-path magnitude is zero; cannot threshold.")

        thresh = float(threshold_frac) * amp0
        start = int(i0_raw + max(0, int(guard_bins)))

        if max_delay_s is not None and max_delay_s > 0:
            max_bins = int(np.ceil(max_delay_s * self.fs))
            stop = min(mag.size, i0_raw + max_bins + 1)
        else:
            stop = mag.size

        region = mag[start:stop]
        local_idxs: List[int] = []
        if region.size >= 3:
            for k in range(1, region.size - 1):
                if region[k] >= region[k - 1] and region[k] > region[k + 1]:
                    if region[k] >= thresh:
                        local_idxs.append(k)
        cand_idxs = [start + k for k in local_idxs]

        min_sep_bins = int(np.ceil(max(0.0, min_separation_s) * self.fs))
        cand_idxs = [i for i in cand_idxs if abs(i - i0_raw) >= min_sep_bins]

        cand_idxs.sort(key=lambda i: mag[i], reverse=True)
        selected: List[int] = []
        for i in cand_idxs:
            if not selected or all(abs(i - j) >= min_sep_bins for j in selected):
                selected.append(i)
            if len(selected) >= max_peaks:
                break

        ctype = self._default_cable(cable_type)
        vf = float(velocity_factor) if velocity_factor is not None else float(CABLE_VF[ctype])
        prop_speed = float(SPEED_OF_LIGHT * vf)

        i0_rep = self._to_N_bins(i0_raw)
        t0 = float(self._t[i0_raw])
        direct = EchoPath(
            bin_index   =   i0_rep,
            time_s      =   t0,
            amplitude   =   amp0,
            distance_m  =   0.0,
            distance_ft =   0.0,
        )

        echoes: List[EchoPath] = []
        for ie_raw in selected:
            te = float(self._t[ie_raw])
            delay = float(te - t0)
            dist_m = float((delay * prop_speed) / 2.0)
            dist_ft = float(dist_m * FEET_PER_METER)
            echoes.append(
                EchoPath(
                    bin_index   =   self._to_N_bins(ie_raw),
                    time_s      =   te,
                    amplitude   =   float(mag[ie_raw]),
                    distance_m  =   dist_m,
                    distance_ft =   dist_ft,
                )
            )

        dataset = EchoDatasetInfo(
            subcarriers             =   self.N,
            snapshots               =   self.M,   
            subcarrier_spacing_hz   =   float(self.delta_f),
            sample_rate_hz          =   float(self.fs),
        )

        tr_block: Optional[TimeResponse] = None
        if include_time_response:
            tr_block = TimeResponse(
                n_fft           =   int(self._n_fft),
                time_axis_s     =   [float(x) for x in self._t.tolist()],
                time_response   =   self._vec_to_pairs(self._h),
            )

        return EchoDetectorReport(
            channel_id          =   self.channel_id if channel_id is None else channel_id,
            dataset             =   dataset,
            cable_type          =   ctype,
            velocity_factor     =   vf,
            prop_speed_mps      =   prop_speed,
            direct_path         =   direct,
            echoes              =   echoes,
            threshold_frac      =   float(threshold_frac),
            guard_bins          =   int(guard_bins),
            min_separation_s    =   float(min_separation_s),
            max_delay_s         =   float(max_delay_s) if max_delay_s is not None else None,
            max_peaks           =   int(max_peaks),
            time_response       =   tr_block,
        )

    # ───────── Compatibility wrappers for tests ─────────

    def first_echo(
        self,
        *,
        threshold_frac: float = 0.2,
        guard_bins: int = 1,
        max_delay_s: Optional[float] = None,
        cable_type: Optional[CableTypes] = None,
        velocity_factor: Optional[float] = None,
        n_fft: Optional[int] = None,
    ) -> EchoReflection:
        """
        Compatibility wrapper. See `detect_first_echo`.
        """
        return self.detect_first_echo(
            cable_type      =   cable_type,
            velocity_factor =   velocity_factor,
            threshold_frac  =   threshold_frac,
            guard_bins      =   guard_bins,
            max_delay_s     =   max_delay_s,
            n_fft           =   n_fft,)

    def multi_echo(
        self,
        *,
        threshold_frac: float = 0.2,
        guard_bins: int = 1,
        min_separation_s: float = 0.0,
        max_delay_s: Optional[float] = None,
        max_peaks: int = 5,
        cable_type: Optional[CableTypes] = None,
        velocity_factor: Optional[float] = None,
        n_fft: Optional[int] = None,
        include_time_response: bool = True,
        channel_id: Optional[ChannelId] = None,
    ) -> EchoDetectorReport:
        """
        Compatibility wrapper. See `detect_multiple_echoes`.
        """
        return self.detect_multiple_echoes(
            cable_type              =   cable_type,
            velocity_factor         =   velocity_factor,
            threshold_frac          =   threshold_frac,
            guard_bins              =   guard_bins,
            min_separation_s        =   min_separation_s,
            max_delay_s             =   max_delay_s,
            max_peaks               =   max_peaks,
            n_fft                   =   n_fft,
            include_time_response   =   include_time_response,
            channel_id              =   channel_id,
        )
