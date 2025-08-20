# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia

import math
import numpy as np
import pytest
from numpy.testing import assert_allclose, assert_array_equal

from pypnm.api.routes.basic.common.signal_capture_agg import SignalCaptureAggregator

@pytest.fixture
def agg():
    return SignalCaptureAggregator()


def test_add_coordinate_basic_and_len(agg: SignalCaptureAggregator):
    agg.add_coordinate(1.0, 10.0)
    agg.add_coordinate(2.0, 20.0)
    assert len(agg) == 2
    xs, ys = agg.get_series()
    assert xs.dtype == np.float64 and ys.dtype == np.float64
    assert_array_equal(xs, np.array([1.0, 2.0], dtype=np.float64))
    assert_array_equal(ys, np.array([10.0, 20.0], dtype=np.float64))


def test_add_coordinate_skips_non_numeric_and_non_finite(agg: SignalCaptureAggregator, caplog):
    agg.add_coordinate("NaN", 1.0)          # non-numeric
    agg.add_coordinate(1.0, float("inf"))   # non-finite
    agg.add_coordinate(np.nan, 1.0)         # non-finite
    assert len(agg) == 0
    # Ensure warnings were emitted
    assert any("Skipping non-numeric point" in r.message for r in caplog.records) or \
           any("Skipping non-finite point" in r.message for r in caplog.records)


def test_add_series_and_shape_mismatch(agg: SignalCaptureAggregator):
    agg.add_series([0, 1, 2], [10, 11, 12])
    assert len(agg) == 3
    with pytest.raises(ValueError):
        agg.add_series([0, 1], [1])  # shape mismatch


def test_get_series_reduces_duplicates_with_mean_by_default(agg: SignalCaptureAggregator):
    agg.add_coordinate(1.0, 10.0)
    agg.add_coordinate(1.0, 14.0)
    agg.add_coordinate(2.0, 20.0)
    xs, ys = agg.get_series()
    assert_array_equal(xs, np.array([1.0, 2.0]))
    assert_allclose(ys, np.array([12.0, 20.0]))  # mean of 10 and 14


@pytest.mark.parametrize("name,expected", [
    ("mean", 12.0),
    ("max", 14.0),
    ("min", 10.0),
    ("sum", 24.0),
])
def test_reconstruct_duplicate_reducers(name, expected):
    agg = SignalCaptureAggregator(reducer=name)
    agg.add_coordinate(0.0, 10.0)
    agg.add_coordinate(0.0, 14.0)
    gx, gy = agg.reconstruct(step=1.0)
    assert_array_equal(gx, np.array([0.0]))
    assert_allclose(gy, np.array([expected]))


def test_reconstruct_with_custom_reducer_callable():
    agg = SignalCaptureAggregator(reducer=lambda a: float(np.median(a)) if a.size else 0.0)
    agg.add_coordinate(0.0, 10.0)
    agg.add_coordinate(0.0, 100.0)
    gx, gy = agg.reconstruct(step=1.0)
    assert_array_equal(gx, np.array([0.0]))
    assert_allclose(gy, np.array([55.0]))  # median


def test_reconstruct_infers_step_from_median_diff(agg: SignalCaptureAggregator):
    # Non-uniform diffs, median positive diff is 1.0
    agg.add_series([0.0, 1.0, 2.0, 4.0], [1, 2, 3, 5])
    gx, gy = agg.reconstruct()  # infer step
    # Expect grid from 0 to 4 inclusive, step ~1.0
    assert_allclose(gx, np.array([0, 1, 2, 3, 4], dtype=np.float64))
    # y at x=3 should be fill (default 0), others as provided
    assert_allclose(gy, np.array([1, 2, 3, 0, 5], dtype=np.float64))


def test_reconstruct_with_provided_step_and_fill_value():
    agg = SignalCaptureAggregator(fill_value=-1.0)
    agg.add_series([0.0, 2.0, 4.0], [10.0, 20.0, 40.0])
    gx, gy = agg.reconstruct(step=1.0)  # use default fill_value from ctor
    assert_allclose(gx, np.arange(0.0, 5.0, 1.0))
    assert_allclose(gy, np.array([10.0, -1.0, 20.0, -1.0, 40.0]))
    # Override fill at call-site
    gx2, gy2 = agg.reconstruct(step=1.0, fill_value=999.0)
    assert_allclose(gy2, np.array([10.0, 999.0, 20.0, 999.0, 40.0]))


def test_reconstruct_tolerance_snapping_and_out_of_tol_logging(caplog):
    agg = SignalCaptureAggregator()
    # Step = 1.0, points near 1.0:
    agg.add_coordinate(0.0, 0.0)
    agg.add_coordinate(1.49, 10.0)  # outside default tol=0.5 of 1.0 (snap to 1.0)
    gx, gy = agg.reconstruct(step=1.0)  # tol defaults to 0.5
    assert_allclose(gx, np.array([0.0, 1.0], dtype=np.float64))
    # y at 1.0 remains fill (0.0) because 1.49 is out of tolerance
    assert_allclose(gy, np.array([0.0, 0.0]))
    # Now with increased tolerance so it snaps
    gx2, gy2 = agg.reconstruct(step=1.0, tolerance=0.51)
    assert_allclose(gx2, np.array([0.0, 1.0], dtype=np.float64))
    assert_allclose(gy2, np.array([0.0, 10.0]))
    # Ensure a debug log was emitted for the first reconstruct
    assert any("did not fit grid" in r.message for r in caplog.records)


def test_reconstruct_empty_returns_empty_arrays(agg: SignalCaptureAggregator):
    gx, gy = agg.reconstruct()  # no data
    assert gx.size == 0 and gy.size == 0
    assert gx.dtype == np.float64 and gy.dtype == np.float64


def test_reconstruct_invalid_step_or_tolerance_errors(agg: SignalCaptureAggregator):
    agg.add_coordinate(0.0, 1.0)
    agg.add_coordinate(1.0, 2.0)
    with pytest.raises(ValueError):
        agg.reconstruct(step=0.0)
    with pytest.raises(ValueError):
        agg.reconstruct(step=1.0, tolerance=0.0)


def test_reconstruct_cannot_infer_step_when_all_x_identical(agg: SignalCaptureAggregator):
    agg.add_series([1.0, 1.0, 1.0], [10.0, 11.0, 12.0])
    with pytest.raises(ValueError):
        agg.reconstruct()  # cannot infer step if all x equal


def test_get_series_returns_sorted_unique_reduced_without_reconstruct(agg: SignalCaptureAggregator):
    # Two at x=0 (mean=15), one at x=1
    agg.add_series([1.0, 0.0, 0.0], [20.0, 10.0, 20.0])
    xs, ys = agg.get_series()
    assert_array_equal(xs, np.array([0.0, 1.0], dtype=np.float64))
    assert_allclose(ys, np.array([15.0, 20.0], dtype=np.float64))


def test_clear_resets_state(agg: SignalCaptureAggregator):
    agg.add_coordinate(0.0, 1.0)
    agg.reconstruct(step=1.0)
    agg.clear()
    assert len(agg) == 0
    xs, ys = agg.get_series()
    assert xs.size == 0 and ys.size == 0


def test_reconstruct_override_reducer_runtime():
    agg = SignalCaptureAggregator(reducer="sum")
    agg.add_coordinate(0.0, 1.0)
    agg.add_coordinate(0.0, 3.0)
    # override reducer at call time to 'max' behavior
    gx, gy = agg.reconstruct(step=1.0, reducer=lambda a: float(np.max(a)) if a.size else 0.0)
    assert_array_equal(gx, np.array([0.0], dtype=np.float64))
    assert_allclose(gy, np.array([3.0], dtype=np.float64))
