
from __future__ import annotations

# SPDX-License-Identifier: MIT
# pytest -q
import unittest
import numpy as np
import pytest

from pypnm.lib.signal_processing.group_delay import GroupDelay, GroupDelayResult
from pypnm.lib.types import ArrayLikeF64

def as_pairs(z: np.ndarray):
    z = np.asarray(z, dtype=np.complex128).ravel()
    return [(float(c.real), float(c.imag)) for c in z]

class TestGroupDelay(unittest.TestCase):

    def test_constant_spacing_linear_phase_mean_matches_tau(self):
        N = 64
        df_hz = 25_000.0
        tau_us = 2.5
        tau_s = tau_us * 1e-6

        f = np.arange(N) * df_hz
        H = np.exp(-1j * 2 * np.pi * f * tau_s)
        gd = GroupDelay.from_channel_estimate(as_pairs(H), df_hz=df_hz, unwrap=True)

        freq_hz, tau_s_out = gd.to_tuple()
        assert freq_hz.shape == (N,)
        assert tau_s_out.shape == (N,)

        # constant group delay (allow tiny numeric error)
        assert np.allclose(tau_s_out, tau_s, atol=1e-12)

    def test_absolute_freq_vector_linear_phase(self):
        N = 48
        f0 = 300e6
        df = 25_000.0
        freq_hz: ArrayLikeF64 = (f0 + np.arange(N) * df).astype(np.float64)

        tau_us = 1.2
        tau_s = tau_us * 1e-6
        H = np.exp(-1j * 2 * np.pi * freq_hz * tau_s)

        gd = GroupDelay(as_pairs(H), freq_hz=freq_hz, unwrap=True)
        f_out, tau_s_out = gd.to_tuple()

        assert np.allclose(f_out, freq_hz, rtol=0, atol=0)
        assert np.allclose(tau_s_out, tau_s, atol=1e-12)

    def test_f0_hz_offset_with_df_axis(self):
        N = 16
        df = 50_000.0
        f0 = 123.456e6
        tau_s = 3e-6

        f = f0 + np.arange(N) * df
        H = np.exp(-1j * 2 * np.pi * f * tau_s)

        gd = GroupDelay.from_channel_estimate(as_pairs(H), df_hz=df, f0_hz=f0, unwrap=True)
        f_out, tau_s_out = gd.to_tuple()

        assert np.allclose(f_out, f0 + np.arange(N) * df)
        assert np.allclose(tau_s_out, tau_s, atol=1e-12)

        res = gd.to_result()
        assert isinstance(res, GroupDelayResult)
        assert pytest.approx(res.freq_hz[0], rel=0, abs=0) == f0
        assert np.allclose(np.array(res.group_delay_s), tau_s, atol=1e-12)
        assert res.params["df_hz"] == df
        # f0_hz is set only when freq_hz was not provided
        assert res.params["f0_hz"] == f0

    def test_active_mask_excludes_bins(self):
        N = 32
        df = 25_000.0
        tau_s = 1e-6
        f = np.arange(N) * df
        H = np.exp(-1j * 2 * np.pi * f * tau_s)

        mask = np.ones(N, dtype=bool)
        mask[:3] = False
        mask[-2:] = False

        gd = GroupDelay.from_channel_estimate(as_pairs(H), df_hz=df, active_mask=mask, unwrap=True)
        _, tau_s_out = gd.to_tuple()

        assert np.all(np.isnan(tau_s_out[~mask]))
        assert np.allclose(tau_s_out[mask], tau_s, atol=1e-12)

    def test_smoothing_reduces_outlier(self):
        N = 64
        df = 25_000.0
        tau_s = 2e-6
        f = np.arange(N) * df
        H = np.exp(-1j * 2 * np.pi * f * tau_s)

        # Inject a local phase glitch at k0
        k0 = 20
        dphi = 0.8  # radians
        H_glitch = H.copy()
        H_glitch[k0] *= np.exp(1j * dphi)

        gd_no_smooth = GroupDelay.from_channel_estimate(as_pairs(H_glitch), df_hz=df, unwrap=True, smooth_win=None)
        gd_smooth    = GroupDelay.from_channel_estimate(as_pairs(H_glitch), df_hz=df, unwrap=True, smooth_win=3)

        _, y_no = gd_no_smooth.to_tuple()
        _, y_sm = gd_smooth.to_tuple()

        # The smoothed value at the glitch index should be closer to true tau
        err_no = abs(y_no[k0] - tau_s)
        err_sm = abs(y_sm[k0] - tau_s)
        assert err_sm <= err_no

    def test_unwrap_needed_for_large_phase_slope(self):
        # Choose df and tau so that per-step phase change ≈ 2π (wrap each bin)
        N = 64
        df = 1_000_000.0
        tau_s = 1e-6  # 2π * df * tau ≈ 2π
        f = np.arange(N) * df
        H = np.exp(-1j * 2 * np.pi * f * tau_s)

        gd_wrapped = GroupDelay.from_channel_estimate(as_pairs(H), df_hz=df, unwrap=False)
        gd_unwrap  = GroupDelay.from_channel_estimate(as_pairs(H), df_hz=df, unwrap=True)

        _, y_wrapped = gd_wrapped.to_tuple()
        _, y_unwrap  = gd_unwrap.to_tuple()

        # With unwrap=True we should recover tau_s; without unwrap, mean is badly biased.
        assert np.isfinite(np.nanmean(y_unwrap))
        assert np.allclose(np.nanmean(y_unwrap), tau_s, atol=1e-9)
        # Wrapped gradient will be near zero on most bins → mean far from tau_s
        assert abs(np.nanmean(y_wrapped) - tau_s) > 1e-7

    def test_to_result_contents_and_mean(self):
        N = 40
        df = 25_000.0
        tau_s = 1.5e-6
        f = np.arange(N) * df
        H = np.exp(-1j * 2 * np.pi * f * tau_s)

        mask = np.ones(N, dtype=bool)
        mask[::7] = False  # drop a few bins

        gd = GroupDelay.from_channel_estimate(as_pairs(H), df_hz=df, active_mask=mask, unwrap=True)
        res = gd.to_result()

        # shapes
        assert len(res.freq_hz) == N
        assert len(res.group_delay_s) == N
        assert len(res.group_delay_us) == N
        assert len(res.valid_mask) == N

        # mean over valid bins ≈ tau_s (in microseconds)
        gd_us = np.array(res.group_delay_us)
        valid = np.array(res.valid_mask, dtype=bool)
        mean_us = np.nanmean(gd_us[valid])
        assert np.isclose(mean_us, tau_s * 1e6, atol=1e-9)

    @pytest.mark.parametrize(
        "kwargs, err_msg",
        [
            # both freq_hz and df_hz
            (dict(freq_hz=np.array([0.0, 1.0]), df_hz=1.0), "Provide exactly one"),
            # neither freq_hz nor df_hz
            (dict(), "Provide exactly one"),
        ],
    )
    def test_freq_inputs_exclusivity(kwargs, err_msg):
        H = as_pairs(np.array([1+0j, 1+0j]))
        with pytest.raises(ValueError) as e:
            GroupDelay(H, **kwargs)
        assert err_msg in str(e.value)

    def test_invalid_inputs_raise(self):
        # H too short
        with pytest.raises(ValueError):
            GroupDelay(as_pairs(np.array([1+0j])), df_hz=1.0)

        # mask length mismatch
        H = as_pairs(np.array([1+0j, 1+0j, 1+0j]))
        with pytest.raises(ValueError):
            GroupDelay(H, df_hz=1.0, active_mask=np.array([True, False]))  # wrong length

        # freq_hz duplicates
        with pytest.raises(ValueError):
            GroupDelay(H, freq_hz=np.array([0.0, 1.0, 1.0]))

        # df_hz zero
        with pytest.raises(ValueError):
            GroupDelay(H, df_hz=0.0)

        # smooth_win invalid (even / <3 / non-int)
        with pytest.raises(ValueError):
            GroupDelay(H, df_hz=1.0, smooth_win=2)
        with pytest.raises(ValueError):
            GroupDelay(H, df_hz=1.0, smooth_win=1)
        with pytest.raises(ValueError):
            GroupDelay(H, df_hz=1.0, smooth_win=4)

    def test_repr_contains_summary(self):
        N = 8
        df = 10.0
        tau_s = 5e-6
        f = np.arange(N) * df
        H = np.exp(-1j * 2 * np.pi * f * tau_s)
        gd = GroupDelay.from_channel_estimate(as_pairs(H), df_hz=df)
        r = repr(gd)
        assert "GroupDelay(n=" in r

if __name__ == "__main__":
    unittest.main()