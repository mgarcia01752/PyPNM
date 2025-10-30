# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia

# tests/test_echo_detector.py
from __future__ import annotations
import numpy as np
import pytest

from pypnm.api.routes.advance.analysis.signal_analysis.detection.echo.echo_detector import (
    EchoDetector, EchoDetectorReport, EchoReflection,)
from pypnm.lib.constants import CABLE_VF, SPEED_OF_LIGHT
from pypnm.lib.types import ChannelId

def _build_freq_from_time_impulses(n: int, direct_bin: int, echo_bin: int, amp_direct: float = 1.0, amp_echo: float = 0.5) -> np.ndarray:
    """Helper: create H(f) by FFT of an impulse-y h(t) with two peaks."""
    h = np.zeros(n, dtype=np.complex128)
    h[direct_bin] = amp_direct + 0j
    h[echo_bin] = amp_echo + 0j
    return np.fft.fft(h, n=n)


@pytest.mark.parametrize("df", [25_000.0, 50_000.0])
def test_first_echo_basic(df: float) -> None:
    """
    Build a synthetic time response with a direct peak and a later echo,
    transform to frequency domain, and verify first_echo() finds the right bins,
    times, and distance.
    """
    N = 1024
    i0 = 100
    ie = 220
    H = _build_freq_from_time_impulses(N, i0, ie, amp_direct=1.0, amp_echo=0.4)

    det = EchoDetector(H, subcarrier_spacing_hz=df, n_fft=N, cable_type="RG6")
    ref: EchoReflection = det.first_echo(threshold_frac=0.2, guard_bins=2, max_delay_s=None)

    fs = N * df
    delay_expected = (ie - i0) / fs
    v = SPEED_OF_LIGHT * CABLE_VF["RG6"]
    dist_expected = (v * delay_expected) / 2.0

    assert ref.direct_index == i0
    assert ref.echo_index == ie
    assert ref.time_echo_s - ref.time_direct_s == pytest.approx(delay_expected, rel=0, abs=1e-12)
    assert ref.reflection_delay_s == pytest.approx(delay_expected, rel=0, abs=1e-12)
    assert ref.reflection_distance_m == pytest.approx(dist_expected, rel=1e-12)
    assert ref.amp_echo < ref.amp_direct
    assert 0.0 < ref.amp_ratio < 1.0


def test_multi_echo_pairs_and_padding() -> None:
    """
    Verify multi_echo() with (N,2) real/imag input and zero-padding returns
    a well-formed report including the optional time_response block.
    """
    N = 512
    i0, i1, i2 = 50, 120, 300
    H = _build_freq_from_time_impulses(N, i0, i1, amp_direct=1.0, amp_echo=0.6)
    # encode as (re, im) pairs shape (N, 2)
    H_pairs = np.stack((np.real(H), np.imag(H)), axis=1)

    det = EchoDetector(H_pairs, subcarrier_spacing_hz=50_000.0, n_fft=2048, cable_type="RG11")
    rep: EchoDetectorReport = det.multi_echo(
        threshold_frac=0.2,
        guard_bins=1,
        min_separation_s=0.0,
        max_delay_s=None,
        max_peaks=3,
        include_time_response=True,
        channel_id=ChannelId(42),
    )

    assert rep.channel_id == ChannelId(42)
    assert rep.dataset.subcarriers == N
    assert rep.dataset.sample_rate_hz == pytest.approx(N * 50_000.0, rel=0, abs=0.0)
    assert rep.velocity_factor == pytest.approx(CABLE_VF["RG11"], rel=0, abs=0.0)
    assert rep.direct_path.bin_index == i0
    # At least one echo detected (the designed i1). Zero-padding shouldn't change peak indices.
    assert len(rep.echoes) >= 1
    assert rep.echoes[0].bin_index == i1
    # Time response block present and length matches n_fft
    assert rep.time_response is not None
    assert rep.time_response.n_fft == 2048
    assert len(rep.time_response.time_axis_s) == 2048
    assert len(rep.time_response.time_response) == 2048


def test_multi_echo_snapshots_min_separation() -> None:
    """
    Feed multiple snapshots with small noise; enforce minimum separation so that
    close peaks are not both selected.
    """
    N = 1024
    df = 25_000.0
    i0 = 80
    close_echo = 86       # very close to main lobe (should be suppressed by guard or min separation)
    far_echo = 280

    H_base = _build_freq_from_time_impulses(N, i0, far_echo, amp_direct=1.0, amp_echo=0.5)
    # Add a *tiny* close echo into the time-domain then FFT, by modifying h then re-FFT:
    h = np.fft.ifft(H_base)
    h[close_echo] += 0.3
    H_with_close = np.fft.fft(h)

    # Create M snapshots with light complex noise in frequency domain
    rng = np.random.default_rng(123)
    M = 4
    noise = (rng.normal(scale=1e-6, size=(M, N)) + 1j * rng.normal(scale=1e-6, size=(M, N))).astype(np.complex128)
    H_snap = np.broadcast_to(H_with_close, (M, N)).copy()
    H_snap += noise

    det = EchoDetector(H_snap, subcarrier_spacing_hz=df, cable_type="RG59")
    # Guard out a few bins past the direct path, and set a minimum separation bigger than (close_echo - i0)
    rep = det.multi_echo(
        threshold_frac=0.2,
        guard_bins=3,
        min_separation_s=10 / (N * df),  # 10 bins worth of time spacing
        max_delay_s=None,
        max_peaks=5,
        include_time_response=False,
        channel_id=ChannelId(7),
    )

    # Direct path is correct
    assert rep.direct_path.bin_index == i0
    # The "close_echo" should be filtered; the far echo should remain
    echo_bins = [e.bin_index for e in rep.echoes]
    assert far_echo in echo_bins
    assert close_echo not in echo_bins
    # Distances must be non-negative and roughly increasing with time
    distances = [e.distance_m for e in rep.echoes]
    assert all(d >= 0 for d in distances)
