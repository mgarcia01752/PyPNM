# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia


import struct
from pathlib import Path

import numpy as np
import pytest

from pypnm.lib.matplot.manager import MatplotManager

def _assert_png(p: Path):
    assert p.is_file(), f"File not created: {p}"
    assert p.stat().st_size > 100, f"File size too small: {p.stat().st_size} bytes"
    with p.open("rb") as f:
        sig = f.read(8)
    # PNG signature: 89 50 4E 47 0D 0A 1A 0A
    assert sig == b"\x89PNG\r\n\x1a\n", f"Not a PNG file: signature {sig!r}"


def test_plot_line_creates_png(tmp_path: Path):
    mgr = MatplotManager(tmp_path, dpi=120, figsize=(6, 4))
    x = np.linspace(0, 10, 200)
    y = np.sin(x)
    p = mgr.plot_line(
        x, y, "line.png", label="sine", title="Sine Wave",
        xlabel="x", ylabel="sin(x)", grid=True
    )
    _assert_png(p)


def test_plot_line_length_mismatch_raises(tmp_path: Path):
    mgr = MatplotManager(tmp_path)
    x = np.arange(10)
    y = np.arange(11)
    with pytest.raises(ValueError):
        mgr.plot_line(x, y, "bad.png")


def test_plot_multi_line_creates_png(tmp_path: Path):
    mgr = MatplotManager(tmp_path)
    x = np.linspace(0, 2 * np.pi, 100)
    s1 = (x, np.sin(x), "sin")
    s2 = (x, np.cos(x), "cos")
    s3 = (x, np.tan(x) / 5.0, "tan/5")
    p = mgr.plot_multi_line([s1, s2, s3], "multi.png",
                            title="Trig", xlabel="x", ylabel="val")
    _assert_png(p)


def test_plot_scatter_with_colorbar(tmp_path: Path):
    mgr = MatplotManager(tmp_path)
    rng = np.random.default_rng(42)
    x = rng.normal(0, 1, 300)
    y = rng.normal(0, 1, 300)
    c = np.hypot(x, y)
    p = mgr.plot_scatter(x, y, "scatter.png", c=c,
                         title="Scatter", xlabel="X", ylabel="Y",
                         add_colorbar=True)
    _assert_png(p)


def test_heatmap2d_basic_and_with_extent(tmp_path: Path):
    mgr = MatplotManager(tmp_path)
    Z = np.random.default_rng(1).normal(size=(32, 64))
    p1 = mgr.heatmap2d(Z, "hm2d_basic.png", title="HM2D Basic")
    _assert_png(p1)

    # With explicit axes extents
    x = np.linspace(100, 200, Z.shape[1])
    y = np.linspace(0, 1, Z.shape[0])
    p2 = mgr.heatmap2d(Z, "hm2d_extent.png", x=x, y=y,
                       title="HM2D Extent", xlabel="Freq", ylabel="Time")
    _assert_png(p2)


def test_heatmap2d_invalid_shape_raises(tmp_path: Path):
    mgr = MatplotManager(tmp_path)
    Z = np.arange(10)  # 1D -> invalid
    with pytest.raises(ValueError):
        mgr.heatmap2d(Z, "bad2d.png")


def test_heatmap3d_surface_and_wireframe(tmp_path: Path):
    mgr = MatplotManager(tmp_path, dpi=110, figsize=(7, 5))
    y = np.linspace(-2, 2, 40)
    x = np.linspace(-3, 3, 60)
    X, Y = np.meshgrid(x, y)
    R = np.hypot(X, Y) + 1e-9
    Z = np.sin(R) / R

    p_surface = mgr.heatmap3d(Z, "surf.png", x=x, y=y,
                              title="3D Surface", xlabel="x", ylabel="y", zlabel="z")
    _assert_png(p_surface)

    p_wire = mgr.heatmap3d(Z, "wire.png", x=x, y=y,
                           wireframe=True, title="3D Wireframe")
    _assert_png(p_wire)


def test_heatmap3d_invalid_x_y_lengths_raise(tmp_path: Path):
    mgr = MatplotManager(tmp_path)
    Z = np.zeros((10, 20))
    bad_x = np.arange(19)  # should be 20
    good_y = np.arange(10)
    with pytest.raises(ValueError):
        mgr.heatmap3d(Z, "bad3d_x.png", x=bad_x, y=good_y)

    good_x = np.arange(20)
    bad_y = np.arange(9)  # should be 10
    with pytest.raises(ValueError):
        mgr.heatmap3d(Z, "bad3d_y.png", x=good_x, y=bad_y)


def test_transparent_background_option(tmp_path: Path):
    mgr = MatplotManager(tmp_path)
    x = np.linspace(0, 1, 50)
    y = x**2
    p = mgr.plot_line(x, y, "transparent.png", transparent=True, label="x^2")
    _assert_png(p)
