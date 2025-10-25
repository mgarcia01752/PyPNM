# SPDX-License-Identifier: MIT
# Copyright (c) 2025

from __future__ import annotations

import numpy as np
import pytest

from pypnm.api.routes.advance.analysis.signal_analysis.group_delay_calculator import (
    GroupDelayCalculator,
    GroupDelayCalculatorModel,
)

RTOL = 1e-6
ATOL = 1e-9


def _mk_linear_phase(freqs_hz: np.ndarray, tau_s: float) -> np.ndarray:
    """
    Build H(f) = exp(-j*2π f τ). Group delay should be constant τ.
    """
    return np.exp(-1j * 2.0 * np.pi * freqs_hz * tau_s)


@pytest.mark.pnm
def test_group_delay_constant_for_linear_phase_single_snapshot():
    K = 256
    tau_true = 5e-6  # 5 microseconds
    f0 = 100e6
    df = 25e3
    freqs = f0 + df * np.arange(K)

    H = _mk_linear_phase(freqs, tau_true)
    calc = GroupDelayCalculator(H, freqs)
    f_out, tau_g = calc.compute_group_delay_full()

    # shapes
    assert f_out.shape == (K,)
    assert tau_g.shape == (K,)

    # numeric: near-constant ≈ tau_true
    assert np.allclose(tau_g, tau_true, rtol=RTOL, atol=ATOL)


@pytest.mark.pnm
def test_group_delay_median_across_snapshots_with_noise():
    K = 128
    M = 5
    tau_true = 2.5e-6
    f0 = 90e6
    df = 50e3
    freqs = f0 + df * np.arange(K)

    # Build 5 snapshots with small random phase noise
    rng = np.random.default_rng(123)
    Hs = []
    for _ in range(M):
        H_clean = _mk_linear_phase(freqs, tau_true)
        phase_jitter = rng.normal(scale=1e-2, size=K)  # ~0.01 rad noise
        H_noisy = H_clean * np.exp(1j * phase_jitter)
        Hs.append(H_noisy)
    H = np.stack(Hs, axis=0)  # (M, K)

    calc = GroupDelayCalculator(H, freqs)
    f_med, tau_med = calc.median_group_delay()

    # shapes
    assert f_med.shape == (K,)
    assert tau_med.shape == (K,)

    # close to truth
    assert np.allclose(tau_med, tau_true, rtol=5e-3, atol=1e-7)


@pytest.mark.pnm
def test_input_encodings_pairs_and_mk2():
    K = 64
    tau_true = 1e-6
    f0 = 200e6
    df = 25e3
    freqs = f0 + df * np.arange(K)

    H_complex = _mk_linear_phase(freqs, tau_true)

    # (K,2) real/imag pairs
    pairs_K2 = np.stack([np.real(H_complex), np.imag(H_complex)], axis=1)  # (K,2)
    calc_pairs = GroupDelayCalculator(pairs_K2, freqs)
    _, tau_pairs = calc_pairs.compute_group_delay_full()

    # (M,K,2) pairs with M=1
    pairs_MK2 = pairs_K2[np.newaxis, ...]  # (1,K,2)
    calc_pairs_batched = GroupDelayCalculator(pairs_MK2, freqs)
    _, tau_pairs_batched = calc_pairs_batched.compute_group_delay_full()

    # complex baseline
    calc_c = GroupDelayCalculator(H_complex, freqs)
    _, tau_c = calc_c.compute_group_delay_full()

    assert np.allclose(tau_pairs, tau_c, rtol=RTOL, atol=ATOL)
    assert np.allclose(tau_pairs_batched, tau_c, rtol=RTOL, atol=ATOL)


@pytest.mark.pnm
def test_snapshot_group_delay_shape():
    K = 33
    M = 3
    tau_true = 4e-6
    f0, df = 50e6, 25e3
    freqs = f0 + df * np.arange(K)
    H = np.stack([_mk_linear_phase(freqs, tau_true) for _ in range(M)], axis=0)

    calc = GroupDelayCalculator(H, freqs)
    taus = calc.snapshot_group_delay()
    assert taus.shape == (M, K)
    # values close to tau_true
    assert np.allclose(taus, tau_true, rtol=RTOL, atol=ATOL)


@pytest.mark.pnm
def test_model_build_and_alias_fields():
    K = 40
    tau_true = 3e-6
    f0, df = 70e6, 25e3
    freqs = f0 + df * np.arange(K)
    H = _mk_linear_phase(freqs, tau_true)

    mdl: GroupDelayCalculatorModel = GroupDelayCalculator(H, freqs).to_model()

    # dataset info
    assert mdl.dataset_info.subcarriers == K
    assert mdl.dataset_info.snapshots == 1

    # alias "complex" is present and uses the exact literal
    assert mdl.complex_unit == "[Real, Imaginary]"

    # lengths line up
    assert len(mdl.freqs) == K
    assert len(mdl.H_avg) == K
    assert len(mdl.group_delay_full.freqs) == K
    assert len(mdl.group_delay_full.tau_g) == K

    # snapshot GD matrix MxK with M=1
    taus = mdl.snapshot_group_delay.taus
    assert len(taus) == 1 and len(taus[0]) == K

    # median also length K
    assert len(mdl.median_group_delay.freqs) == K
    assert len(mdl.median_group_delay.tau_med) == K

    # numerical sanity
    assert np.allclose(mdl.group_delay_full.tau_g, tau_true, rtol=RTOL, atol=ATOL)
    assert np.allclose(mdl.median_group_delay.tau_med, tau_true, rtol=RTOL, atol=ATOL)


@pytest.mark.pnm
def test_to_dict_uses_alias_and_is_serializable():
    K = 16
    tau_true = 1e-6
    f0, df = 10e6, 25e3
    freqs = f0 + df * np.arange(K)
    H = _mk_linear_phase(freqs, tau_true)

    dct = GroupDelayCalculator(H, freqs).to_dict()
    # has alias "complex" not "complex_unit"
    assert "complex" in dct
    assert dct["complex"] == "[Real, Imaginary]"
    # basic keys
    assert "H_raw" in dct and "H_avg" in dct and "group_delay_full" in dct


@pytest.mark.pnm
def test_validation_duplicate_freqs_and_mismatched_lengths():
    # duplicate freqs cause derivative failure
    freqs = np.array([100.0, 100.0, 200.0])
    H = np.array([1+0j, 1+0j, 1+0j])
    calc = GroupDelayCalculator(H, freqs)
    with pytest.raises(ValueError):
        _ = calc.compute_group_delay_full()

    # mismatched K between H and freqs
    freqs2 = np.array([1.0, 2.0, 3.0, 4.0])
    H2 = np.array([1+0j, 1+0j, 1+0j])
    with pytest.raises(ValueError):
        _ = GroupDelayCalculator(H2, freqs2)

    # invalid shapes
    with pytest.raises(ValueError):
        _ = GroupDelayCalculator(np.zeros((2, 3, 3)), np.array([1.0, 2.0, 3.0]))  # bad last dim
