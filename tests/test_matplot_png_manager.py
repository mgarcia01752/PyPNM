
from __future__ import annotations

# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia

import unittest
import tempfile
from pathlib import Path

import numpy as np

# Adjust the import if your package path differs
from pypnm.lib.matplot.manager import MatplotManager, PlotConfig
from pypnm.lib.types import ArrayLike


class TestMatplotManager(unittest.TestCase):
    def setUp(self):
        # per-test temporary output directory
        self._tmpdir = tempfile.TemporaryDirectory()
        self.tmp_path = Path(self._tmpdir.name)

    def tearDown(self):
        # cleanup
        self._tmpdir.cleanup()

    # ---------- helpers ----------

    def _assert_png(self, p: Path):
        self.assertTrue(p.is_file(), f"File not created: {p}")
        self.assertGreater(p.stat().st_size, 100, f"File size too small: {p.stat().st_size} bytes")
        with p.open("rb") as f:
            sig = f.read(8)
        # PNG signature: 89 50 4E 47 0D 0A 1A 0A
        self.assertEqual(sig, b"\x89PNG\r\n\x1a\n", f"Not a PNG file: signature {sig!r}")

    # ---------- tests ----------

    def test_plot_line_creates_png(self):
        mgr = MatplotManager(self.tmp_path, dpi=120, figsize=(6, 4))
        x = np.linspace(0, 10, 200)
        y = np.sin(x)
        p = mgr.plot_line(
            x, y, "line.png", label="sine", title="Sine Wave",
            xlabel="x", ylabel="sin(x)", grid=True
        )
        self._assert_png(p)

    def test_plot_line_length_mismatch_raises(self):
        mgr = MatplotManager(self.tmp_path)
        x = np.arange(10)
        y = np.arange(11)
        with self.assertRaises(ValueError):
            mgr.plot_line(x, y, "bad.png", label="test")

    def test_plot_multi_line_creates_png(self):
        x = np.linspace(0, 2 * np.pi, 100)
        s1 = np.sin(x)
        s2 = np.cos(x)
        s3 = np.tan(x) / 5.0
        cfg = PlotConfig(y_multi=[s1, s2, s3])
        mgr = MatplotManager(self.tmp_path, default_cfg=cfg)
        p = mgr.plot_multi_line("multi.png",)

        self._assert_png(p)

    def test_plot_scatter_with_colorbar(self):
        mgr = MatplotManager(self.tmp_path)
        rng = np.random.default_rng(42)
        x = rng.normal(0, 1, 300)
        y = rng.normal(0, 1, 300)
        c = np.hypot(x, y)
        p = mgr.plot_scatter(
            x, y, "scatter.png", c=c,
            add_colorbar=True
        )
        self._assert_png(p)

    def test_heatmap2d_basic_and_with_extent(self):
        mgr = MatplotManager(self.tmp_path)
        Z = np.random.default_rng(1).normal(size=(32, 64))
        p1 = mgr.heatmap2d(Z, "hm2d_basic.png")
        self._assert_png(p1)

        # With explicit axes extents
        x = np.linspace(100, 200, Z.shape[1])
        y = np.linspace(0, 1, Z.shape[0])
        p2 = mgr.heatmap2d(
            Z, "hm2d_extent.png", x=x, y=y
        )
        self._assert_png(p2)

    def test_heatmap2d_invalid_shape_raises(self):
        mgr = MatplotManager(self.tmp_path)
        Z = np.arange(10)  # 1D -> invalid
        with self.assertRaises(ValueError):
            mgr.heatmap2d(Z, "bad2d.png")

    def test_heatmap3d_surface_and_wireframe(self):
        mgr = MatplotManager(self.tmp_path, dpi=110, figsize=(7, 5))
        y = np.linspace(-2, 2, 40)
        x = np.linspace(-3, 3, 60)
        X, Y = np.meshgrid(x, y)
        R = np.hypot(X, Y) + 1e-9
        Z = np.sin(R) / R

        p_surface = mgr.heatmap3d(
            Z, "surf.png", x=x, y=y
        )
        self._assert_png(p_surface)

        p_wire = mgr.heatmap3d(
            Z, "wire.png", x=x, y=y,
            wireframe=True
        )
        self._assert_png(p_wire)

    def test_heatmap3d_invalid_x_y_lengths_raise(self):
        mgr = MatplotManager(self.tmp_path)
        Z = np.zeros((10, 20))
        bad_x = np.arange(19)  # should be 20
        good_y = np.arange(10)
        with self.assertRaises(ValueError):
            mgr.heatmap3d(Z, "bad3d_x.png", x=bad_x, y=good_y)

        good_x = np.arange(20)
        bad_y = np.arange(9)  # should be 10
        with self.assertRaises(ValueError):
            mgr.heatmap3d(Z, "bad3d_y.png", x=good_x, y=bad_y)

    def test_transparent_background_option(self):
        mgr = MatplotManager(self.tmp_path)
        x = np.linspace(0, 1, 50)
        y:ArrayLike = x ** 2
        p = mgr.plot_line(x, y, "transparent.png", "Line Plot", label="x^2")
        self._assert_png(p)


if __name__ == "__main__":
    unittest.main()
