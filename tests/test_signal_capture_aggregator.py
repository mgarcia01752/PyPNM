
from __future__ import annotations

# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia

import unittest
import numpy as np
from numpy.testing import assert_allclose, assert_array_equal

from pypnm.api.routes.basic.common.signal_capture_agg import SignalCaptureAggregator


# Helper to get the logger name likely used inside the class' module
_LOGGER_NAME = SignalCaptureAggregator.__module__


def _as_np_f64(a):
    return np.asarray(a, dtype=np.float64)


class TestSignalCaptureAggregator(unittest.TestCase):
    def setUp(self):
        self.agg = SignalCaptureAggregator()

    # ----------------------------
    # Basic add/get
    # ----------------------------
    def test_add_coordinate_basic_and_len(self):
        self.agg.add_coordinate(1.0, 10.0)
        self.agg.add_coordinate(2.0, 20.0)
        self.assertEqual(len(self.agg), 2)
        xs, ys = self.agg.get_series()
        self.assertEqual(xs.dtype, np.float64)
        self.assertEqual(ys.dtype, np.float64)
        assert_array_equal(xs, _as_np_f64([1.0, 2.0]))
        assert_array_equal(ys, _as_np_f64([10.0, 20.0]))

    def test_add_coordinate_skips_non_numeric_and_non_finite(self):
        with self.assertLogs(_LOGGER_NAME, level="DEBUG") as cm:
            self.agg.add_coordinate("NaN", 1.0)          # type: ignore # non-numeric
            self.agg.add_coordinate(1.0, float("inf"))   # non-finite
            self.agg.add_coordinate(np.nan, 1.0)         # non-finite
        self.assertEqual(len(self.agg), 0)
        # Ensure warnings/debug were emitted
        combined = "\n".join(cm.output)
        self.assertTrue(
            ("Skipping non-numeric point" in combined) or
            ("Skipping non-finite point" in combined),
            msg=f"No expected warning in logs:\n{combined}"
        )

    def test_add_series_and_shape_mismatch(self):
        self.agg.add_series([0, 1, 2], [10, 11, 12])
        self.assertEqual(len(self.agg), 3)
        with self.assertRaises(ValueError):
            self.agg.add_series([0, 1], [1])  # shape mismatch

    def test_get_series_reduces_duplicates_with_mean_by_default(self):
        self.agg.add_coordinate(1.0, 10.0)
        self.agg.add_coordinate(1.0, 14.0)
        self.agg.add_coordinate(2.0, 20.0)
        xs, ys = self.agg.get_series()
        assert_array_equal(xs, _as_np_f64([1.0, 2.0]))
        assert_allclose(ys, _as_np_f64([12.0, 20.0]))  # mean of 10 and 14

    # ----------------------------
    # Reducers
    # ----------------------------
    def test_reconstruct_duplicate_reducers(self):
        cases = [
            ("mean", 12.0),
            ("max", 14.0),
            ("min", 10.0),
            ("sum", 24.0),
        ]
        for name, expected in cases:
            with self.subTest(reducer=name):
                agg = SignalCaptureAggregator(reducer=name) # type: ignore
                agg.add_coordinate(0.0, 10.0)
                agg.add_coordinate(0.0, 14.0)
                gx, gy = agg.reconstruct(step=1.0)
                assert_array_equal(gx, _as_np_f64([0.0]))
                assert_allclose(gy, _as_np_f64([expected]))

    def test_reconstruct_with_custom_reducer_callable(self):
        agg = SignalCaptureAggregator(reducer=lambda a: float(np.median(a)) if a.size else 0.0)
        agg.add_coordinate(0.0, 10.0)
        agg.add_coordinate(0.0, 100.0)
        gx, gy = agg.reconstruct(step=1.0)
        assert_array_equal(gx, _as_np_f64([0.0]))
        assert_allclose(gy, _as_np_f64([55.0]))  # median

    # ----------------------------
    # Reconstruct: step inference & filling
    # ----------------------------
    def test_reconstruct_infers_step_from_median_diff(self):
        # Non-uniform diffs, median positive diff is 1.0
        self.agg.add_series([0.0, 1.0, 2.0, 4.0], [1, 2, 3, 5])
        gx, gy = self.agg.reconstruct()  # infer step
        # Expect grid from 0 to 4 inclusive, step ~1.0
        assert_allclose(gx, _as_np_f64([0, 1, 2, 3, 4]))
        # y at x=3 should be fill (default 0), others as provided
        assert_allclose(gy, _as_np_f64([1, 2, 3, 0, 5]))

    def test_reconstruct_with_provided_step_and_fill_value(self):
        agg = SignalCaptureAggregator(fill_value=-1.0)
        agg.add_series([0.0, 2.0, 4.0], [10.0, 20.0, 40.0])
        gx, gy = agg.reconstruct(step=1.0)  # use default fill_value from ctor
        assert_allclose(gx, _as_np_f64(np.arange(0.0, 5.0, 1.0)))
        assert_allclose(gy, _as_np_f64([10.0, -1.0, 20.0, -1.0, 40.0]))
        # Override fill at call-site
        gx2, gy2 = agg.reconstruct(step=1.0, fill_value=999.0)
        assert_allclose(gy2, _as_np_f64([10.0, 999.0, 20.0, 999.0, 40.0]))

    def test_reconstruct_tolerance_snapping_and_out_of_tol_logging(self):
        agg = SignalCaptureAggregator()
        # Step = 1.0, points near 1.0:
        agg.add_coordinate(0.0, 0.0)
        agg.add_coordinate(1.49, 10.0)  # outside default tol=0.5 of 1.0 (should NOT snap)

        with self.assertLogs(_LOGGER_NAME, level="DEBUG") as cm:
            gx, gy = agg.reconstruct(step=1.0)  # tol defaults to 0.5
        assert_allclose(gx, _as_np_f64([0.0, 1.0]))
        # y at 1.0 remains fill (0.0) because 1.49 is out of tolerance
        assert_allclose(gy, _as_np_f64([0.0, 0.0]))

        # Now with increased tolerance so it snaps
        gx2, gy2 = agg.reconstruct(step=1.0, tolerance=0.51)
        assert_allclose(gx2, _as_np_f64([0.0, 1.0]))
        assert_allclose(gy2, _as_np_f64([0.0, 10.0]))

        # Ensure a debug/warn log was emitted for the first reconstruct
        combined = "\n".join(cm.output)
        self.assertIn("did not fit grid", combined)

    def test_reconstruct_empty_returns_empty_arrays(self):
        # new aggregator with no data
        agg = SignalCaptureAggregator()
        gx, gy = agg.reconstruct()
        self.assertEqual(gx.size, 0)
        self.assertEqual(gy.size, 0)
        self.assertEqual(gx.dtype, np.float64)
        self.assertEqual(gy.dtype, np.float64)

    def test_reconstruct_invalid_step_or_tolerance_errors(self):
        self.agg.add_coordinate(0.0, 1.0)
        self.agg.add_coordinate(1.0, 2.0)
        with self.assertRaises(ValueError):
            self.agg.reconstruct(step=0.0)
        with self.assertRaises(ValueError):
            self.agg.reconstruct(step=1.0, tolerance=0.0)

    def test_reconstruct_cannot_infer_step_when_all_x_identical(self):
        self.agg.add_series([1.0, 1.0, 1.0], [10.0, 11.0, 12.0])
        with self.assertRaises(ValueError):
            self.agg.reconstruct()  # cannot infer step if all x equal

    def test_get_series_returns_sorted_unique_reduced_without_reconstruct(self):
        # Two at x=0 (mean=15), one at x=1
        self.agg.add_series([1.0, 0.0, 0.0], [20.0, 10.0, 20.0])
        xs, ys = self.agg.get_series()
        assert_array_equal(xs, _as_np_f64([0.0, 1.0]))
        assert_allclose(ys, _as_np_f64([15.0, 20.0]))

    def test_clear_resets_state(self):
        self.agg.add_coordinate(0.0, 1.0)
        self.agg.reconstruct(step=1.0)
        self.agg.clear()
        self.assertEqual(len(self.agg), 0)
        xs, ys = self.agg.get_series()
        self.assertEqual(xs.size, 0)
        self.assertEqual(ys.size, 0)

    def test_reconstruct_override_reducer_runtime(self):
        agg = SignalCaptureAggregator(reducer="sum")
        agg.add_coordinate(0.0, 1.0)
        agg.add_coordinate(0.0, 3.0)
        # override reducer at call time to 'max' behavior
        gx, gy = agg.reconstruct(step=1.0, reducer=lambda a: float(np.max(a)) if a.size else 0.0)
        assert_array_equal(gx, _as_np_f64([0.0]))
        assert_allclose(gy, _as_np_f64([3.0]))


if __name__ == "__main__":
    unittest.main()
