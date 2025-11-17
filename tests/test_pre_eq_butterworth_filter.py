# SPDX-License-Identifier: MIT
# tests/test_pre_eq_butterworth_filter.py

from __future__ import annotations

import numpy as np
import pytest

from pypnm.lib.signal_processing.butterworth import (PreEqButterworthConfig, PreEqButterworthFilter,)
from pypnm.lib.types import FrequencyHz, NDArrayC128


def _make_test_coefficients(n: int = 128) -> NDArrayC128:
    """Generate a deterministic complex sequence with both low and high frequency content."""
    x = np.linspace(0.0, 2.0 * np.pi, n, endpoint=False)

    low  = np.exp(1j * x)                 # low-frequency complex tone
    high = 0.3 * np.exp(1j * 8.0 * x)     # higher-frequency component

    rng_real = np.random.RandomState(0)
    rng_imag = np.random.RandomState(1)
    noise = 0.05 * (rng_real.randn(n) + 1j * rng_imag.randn(n))

    return (low + high + noise).astype(np.complex128)


def test_from_subcarrier_spacing_builds_equivalent_config() -> None:
    subcarrier_spacing_hz: FrequencyHz = FrequencyHz(50_000)
    cutoff_hz:            FrequencyHz = FrequencyHz(5_000)
    order: int = 6
    zero_phase: bool = False

    filt = PreEqButterworthFilter.from_subcarrier_spacing(
        subcarrier_spacing_hz = subcarrier_spacing_hz,
        cutoff_hz             = cutoff_hz,
        order                 = order,
        zero_phase            = zero_phase,
    )

    assert isinstance(filt.config, PreEqButterworthConfig)
    assert int(filt.config.sample_rate_hz) == int(subcarrier_spacing_hz)
    assert int(filt.config.cutoff_hz)      == int(cutoff_hz)
    assert filt.config.order               == order
    assert filt.config.zero_phase         is zero_phase


def test_apply_zero_phase_preserves_shape_and_types() -> None:
    subcarrier_spacing_hz: FrequencyHz = FrequencyHz(50_000)
    cutoff_hz:            FrequencyHz = FrequencyHz(5_000)

    filt = PreEqButterworthFilter.from_subcarrier_spacing(
        subcarrier_spacing_hz = subcarrier_spacing_hz,
        cutoff_hz             = cutoff_hz,
        order                 = 4,
        zero_phase            = True,
    )

    coeffs: NDArrayC128 = _make_test_coefficients(256)

    result = filt.apply(coeffs)

    assert int(result.sample_rate_hz) == int(subcarrier_spacing_hz)
    assert int(result.cutoff_hz)      == int(cutoff_hz)
    assert result.order               == 4
    assert result.zero_phase         is True

    assert isinstance(result.original_coefficients, np.ndarray)
    assert isinstance(result.filtered_coefficients, np.ndarray)

    assert result.original_coefficients.shape == coeffs.shape
    assert result.filtered_coefficients.shape == coeffs.shape

    assert result.original_coefficients.dtype == np.complex128
    assert result.filtered_coefficients.dtype == np.complex128

    # Zero-phase filtering should change the sequence for non-trivial input
    assert not np.allclose(result.filtered_coefficients, result.original_coefficients)


def test_apply_causal_filter_path_runs_and_changes_data() -> None:
    subcarrier_spacing_hz: FrequencyHz = FrequencyHz(50_000)
    cutoff_hz:            FrequencyHz = FrequencyHz(5_000)

    filt = PreEqButterworthFilter.from_subcarrier_spacing(
        subcarrier_spacing_hz = subcarrier_spacing_hz,
        cutoff_hz             = cutoff_hz,
        order                 = 4,
        zero_phase            = False,
    )

    coeffs: NDArrayC128 = _make_test_coefficients(256)

    result = filt.apply(coeffs)

    assert result.zero_phase is False
    assert isinstance(result.filtered_coefficients, np.ndarray)
    assert result.filtered_coefficients.shape == coeffs.shape
    assert not np.allclose(result.filtered_coefficients, result.original_coefficients)


def test_apply_constant_sequence_is_stable() -> None:
    subcarrier_spacing_hz: FrequencyHz = FrequencyHz(50_000)
    cutoff_hz:            FrequencyHz = FrequencyHz(5_000)

    filt = PreEqButterworthFilter.from_subcarrier_spacing(
        subcarrier_spacing_hz = subcarrier_spacing_hz,
        cutoff_hz             = cutoff_hz,
        order                 = 4,
        zero_phase            = True,
    )

    constant_value = 1.0 + 0.5j
    coeffs: NDArrayC128 = np.full(128, constant_value, dtype=np.complex128)

    result = filt.apply(coeffs)

    # For a constant complex sequence, a low-pass filter should return (approximately) the same value
    assert np.allclose(result.filtered_coefficients, constant_value, atol=1e-6)


def test_apply_raises_on_empty_array() -> None:
    subcarrier_spacing_hz: FrequencyHz = FrequencyHz(50_000)
    cutoff_hz:            FrequencyHz = FrequencyHz(5_000)

    filt = PreEqButterworthFilter.from_subcarrier_spacing(
        subcarrier_spacing_hz = subcarrier_spacing_hz,
        cutoff_hz             = cutoff_hz,
    )

    empty: NDArrayC128 = np.array([], dtype=np.complex128)

    with pytest.raises(ValueError, match="received an empty coefficient array"):
        filt.apply(empty)


def test_apply_raises_on_non_1d_array() -> None:
    subcarrier_spacing_hz: FrequencyHz = FrequencyHz(50_000)
    cutoff_hz:            FrequencyHz = FrequencyHz(5_000)

    filt = PreEqButterworthFilter.from_subcarrier_spacing(
        subcarrier_spacing_hz = subcarrier_spacing_hz,
        cutoff_hz             = cutoff_hz,
    )

    coeffs_2d: NDArrayC128 = np.zeros((4, 4), dtype=np.complex128)

    with pytest.raises(ValueError, match="expects a one-dimensional ComplexArray"):
        filt.apply(coeffs_2d)


def test_invalid_normalized_cutoff_raises_on_init() -> None:
    sample_rate_hz: FrequencyHz = FrequencyHz(50_000)
    cutoff_hz:      FrequencyHz = FrequencyHz(int(sample_rate_hz) // 2)  # normalized == 1.0 → invalid

    config = PreEqButterworthConfig(
        sample_rate_hz = sample_rate_hz,
        cutoff_hz      = cutoff_hz,
        order          = 4,
        zero_phase     = True,
    )

    with pytest.raises(ValueError, match="Normalized cutoff"):
        PreEqButterworthFilter(config=config)
