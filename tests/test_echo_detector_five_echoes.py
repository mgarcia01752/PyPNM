# tests/test_echo_detector_five_echoes.py
from __future__ import annotations
import numpy as np
import pytest

from pypnm.api.routes.advance.analysis.signal_analysis.detection.echo.echo_detector import EchoDetector
from pypnm.lib.constants import CABLE_VF, SPEED_OF_LIGHT
from pypnm.lib.types import ChannelId


def _make_time_impulses(
    n: int,
    peaks: list[tuple[int, float, float]],
) -> np.ndarray:
    """
    Build a complex time series h(t) of length n with impulses at given bins.

    peaks: list of (bin_index, amplitude, phase_radians)
           bin_index must be in [0, n-1]
    """
    h = np.zeros(n, dtype=np.complex128)
    for i, amp, phi in peaks:
        h[i] += amp * np.exp(1j * phi)
    return h


@pytest.mark.parametrize("df", [25_000.0, 50_000.0])  # DOCSIS 3.1/4.0 symbol spacings
def test_multi_echo_five_echoes_synthetic(df: float) -> None:
    """
    Create an impulse response with a direct path + 5 echoes.
    Ensure multi_echo() returns exactly those 5 echoes in the right order
    with reasonable time/distance monotonicity.
    """
    N  = 2048
    i0 = 120                              # direct-path bin
    # choose echo bins well-separated and inside [0, N)
    i1, i2, i3, i4, i5 = 260, 420, 580, 820, 1100

    # descending amplitudes; arbitrary, but above threshold
    amps  = [1.0, 0.7, 0.55, 0.4, 0.32, 0.25]
    # distinct phases to exercise complex handling
    phis  = [0.00, 0.40, 1.10, -0.75, 2.30, -1.60]

    peaks = [
        (i0, amps[0], phis[0]),
        (i1, amps[1], phis[1]),
        (i2, amps[2], phis[2]),
        (i3, amps[3], phis[3]),
        (i4, amps[4], phis[4]),
        (i5, amps[5], phis[5]),
    ]

    # time-domain -> frequency-domain
    h  = _make_time_impulses(N, peaks)
    Hf = np.fft.fft(h, n=N)

    det = EchoDetector(Hf, subcarrier_spacing_hz=df, n_fft=N, cable_type="RG6")

    # threshold comfortably below smallest echo / main ratio (0.25 / 1.0)
    rep = det.multi_echo(
        threshold_frac          =   0.15,
        guard_bins              =   3,
        min_separation_s        =   0.0,
        max_delay_s             =   None,
        max_peaks               =   5,                 # request up to 5 echoes
        include_time_response   =   True,  # nice to validate sizes
        channel_id              =   ChannelId(99),
    )

    # direct path
    assert rep.direct_path.bin_index == i0

    # exactly 5 echoes detected
    assert len(rep.echoes) == 5

    # echo bin order should be by amplitude/time selection; since they’re well-separated
    # and all above threshold, we expect the five we placed in ascending bin order.
    expected_bins = [i1, i2, i3, i4, i5]
    got_bins      = [e.bin_index for e in rep.echoes]
    assert got_bins == expected_bins

    # times strictly increasing after direct-path
    t0 = rep.direct_path.time_s
    echo_times = [e.time_s for e in rep.echoes]
    assert all(echo_times[k] > (t0 if k == 0 else echo_times[k-1]) for k in range(len(echo_times)))

    # distances non-negative and increasing
    dists = [e.distance_m for e in rep.echoes]
    assert all(d >= 0 for d in dists)
    assert all(dists[k] > (0.0 if k == 0 else dists[k-1]) for k in range(len(dists)))

    # optional time-response block present & sized to n_fft
    assert rep.time_response is not None
    assert rep.time_response.n_fft == N
    assert len(rep.time_response.time_axis_s) == N
    assert len(rep.time_response.time_response) == N

    # quick physical sanity: distance = (v * Δt)/2, where Δt = (Δbins / fs)
    fs = N * df
    v  = SPEED_OF_LIGHT * CABLE_VF["RG6"]
    for e in rep.echoes:
        dt = e.time_s - t0
        d_expected = (v * dt) / 2.0
        assert e.distance_m == pytest.approx(d_expected, rel=1e-12)
