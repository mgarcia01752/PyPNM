# SPDX-License-Identifier: MIT
# Copyright (c) 2025

from __future__ import annotations

import unittest
from typing import List

from pypnm.lib.signal_processing.averager import MovingAverage

# Import the class under test
# from your_module_path import SlidingWindowAverager

class TestSlidingWindowAverager(unittest.TestCase):
    """Unit tests for SlidingWindowAverager."""

    def test_length_preserved(self) -> None:
        data: List[float]          = [1, 2, 3, 4, 5, 6, 7]
        sw: MovingAverage  = MovingAverage(n_points=3)
        out: List[float]           = sw.apply(data)
        self.assertEqual(len(out), len(data), "Output length must match input length")

    def test_window_size_one_is_identity(self) -> None:
        data: List[float]          = [0.5, -1.0, 2.5, 0.0]
        sw: MovingAverage  = MovingAverage(n_points=1)
        out: List[float]           = sw.apply(data)
        self.assertEqual(out, data, "Window size 1 should return the original sequence")

    def test_three_point_average_expected_values(self) -> None:
        data: List[float]          = [1, 2, 3, 4, 5, 6, 7]
        sw: MovingAverage  = MovingAverage(n_points=3)
        out: List[float]           = sw.apply(data)
        # NumPy 'same' mode with zero padding at edges:
        expected: List[float]      = [
            (0 + 1 + 2) / 3,  # 1.0
            (1 + 2 + 3) / 3,  # 2.0
            (2 + 3 + 4) / 3,  # 3.0
            (3 + 4 + 5) / 3,  # 4.0
            (4 + 5 + 6) / 3,  # 5.0
            (5 + 6 + 7) / 3,  # 6.0
            (6 + 7 + 0) / 3,  # 13/3 = 4.333...
        ]
        for a, b in zip(out, expected):
            self.assertAlmostEqual(a, b, places=9)

    def test_five_point_average_expected_values(self) -> None:
        data: List[float]          = [1, 2, 3, 4, 5, 6, 7]
        sw: MovingAverage  = MovingAverage(n_points=5)
        out: List[float]           = sw.apply(data)
        expected: List[float]      = [
            (0 + 0 + 1 + 2 + 3) / 5,  # 1.2
            (0 + 1 + 2 + 3 + 4) / 5,  # 2.0
            (1 + 2 + 3 + 4 + 5) / 5,  # 3.0
            (2 + 3 + 4 + 5 + 6) / 5,  # 4.0
            (3 + 4 + 5 + 6 + 7) / 5,  # 5.0
            (4 + 5 + 6 + 7 + 0) / 5,  # 4.4
            (5 + 6 + 7 + 0 + 0) / 5,  # 3.6
        ]
        for a, b in zip(out, expected):
            self.assertAlmostEqual(a, b, places=9)

    def test_empty_input(self) -> None:
        sw: MovingAverage  = MovingAverage(n_points=3)
        self.assertEqual(sw.apply([]), [], "Empty input should return empty output")

    def test_invalid_window_raises(self) -> None:
        with self.assertRaises(ValueError):
            MovingAverage(n_points=0)
        with self.assertRaises(ValueError):
            MovingAverage(n_points=-5)


if __name__ == "__main__":
    unittest.main(verbosity=2)
