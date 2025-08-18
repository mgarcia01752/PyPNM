# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia

from __future__ import annotations

import logging
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Iterable, List, Optional, Sequence, Tuple, Union

import numpy as np
import matplotlib
matplotlib.use("Agg")  # Headless rendering for servers/CI
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D  # noqa: F401  (registers '3d' projection)

Number = Union[int, float, np.number]
ArrayLike = Union[Sequence[Number], np.ndarray]


@dataclass(frozen=True)
class PlotConfig:
    """
    Lightweight, reusable plot options and optional shared data vectors.

    Precedence (for any overlapping option/data):
        method arg > cfg.field > manager.default_cfg.field > method default

    Legend handling:
      - legend=None  -> auto (show if any labeled artists exist)
      - legend=True  -> force show
      - legend=False -> force hide
    """
    # Optional shared data
    x: Optional[ArrayLike] = None
    y: Optional[ArrayLike] = None
    z: Optional[ArrayLike] = None
    y_multi: Optional[List[ArrayLike]] = None

    # Optional labels for multi-series
    y_multi_label: Optional[List[str]] = None

    # Axis labels / title
    xlabel: Optional[str] = None
    ylabel: Optional[str] = None
    zlabel: Optional[str] = None
    title: Optional[str] = None

    # Limits and style
    xlim: Optional[Tuple[Number, Number]] = None
    ylim: Optional[Tuple[Number, Number]] = None
    grid: Optional[bool] = None
    legend: Optional[bool] = None
    transparent: Optional[bool] = None

    def update(self, **kwargs) -> "PlotConfig":
        return replace(self, **kwargs)


class MatplotManager:
    """
    Lightweight Matplotlib manager for saving common plot types as PNG files.

    - Uses the headless Agg backend (safe for servers/CI).
    - Accepts a PlotConfig for shared options / data.
    - All methods save and return the output `pathlib.Path`.
    """

    def __init__(
        self,
        output_dir: Union[str, Path] = ".",
        *,
        dpi: int = 150,
        figsize: Tuple[float, float] = (8.0, 5.0),
        tight_layout: bool = True,
        default_cfg: Optional[PlotConfig] = None,
        logger: Optional[logging.Logger] = None,
    ) -> None:
        self.output_dir = Path(output_dir).resolve()
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.dpi = dpi
        self.figsize = figsize
        self.tight_layout = tight_layout
        self.default_cfg = default_cfg or PlotConfig()
        self.logger = logger or logging.getLogger(__name__)
        self._png_files: List[Path] = []

    # ──────────────────────────── internals ────────────────────────────
    def _new_fig(self, projection: Optional[str] = None):
        fig = plt.figure(figsize=self.figsize, dpi=self.dpi)
        ax = fig.add_subplot(111, projection=projection) if projection else fig.add_subplot(111)
        return fig, ax

    def _resolve_path(self, filename: Union[str, Path]) -> Path:
        p = Path(filename)
        return p if p.is_absolute() else (self.output_dir / p)

    def _update_png_file(self, fname: Path) -> Path:
        self._png_files.append(fname)
        return fname

    def get_png_files(self) -> List[Path]:
        return self._png_files

    def _merge_cfg(self, user_cfg: Optional[PlotConfig], method_defaults: PlotConfig) -> PlotConfig:
        base = self.default_cfg

        def pick(top, mid, low):
            return top if top is not None else (mid if mid is not None else low)

        return PlotConfig(
            title       = pick(user_cfg.title       if user_cfg else None, base.title,       method_defaults.title),
            xlabel      = pick(user_cfg.xlabel      if user_cfg else None, base.xlabel,      method_defaults.xlabel),
            ylabel      = pick(user_cfg.ylabel      if user_cfg else None, base.ylabel,      method_defaults.ylabel),
            zlabel      = pick(user_cfg.zlabel      if user_cfg else None, base.zlabel,      method_defaults.zlabel),
            xlim        = pick(user_cfg.xlim        if user_cfg else None, base.xlim,        method_defaults.xlim),
            ylim        = pick(user_cfg.ylim        if user_cfg else None, base.ylim,        method_defaults.ylim),
            grid        = pick(user_cfg.grid        if user_cfg else None, base.grid,        method_defaults.grid),
            legend      = pick(user_cfg.legend      if user_cfg else None, base.legend,      method_defaults.legend),
            transparent = pick(user_cfg.transparent if user_cfg else None, base.transparent, method_defaults.transparent),
            x           = pick(user_cfg.x           if user_cfg else None, base.x,           method_defaults.x),
            y           = pick(user_cfg.y           if user_cfg else None, base.y,           method_defaults.y),
            z           = pick(user_cfg.z           if user_cfg else None, base.z,           method_defaults.z),
            y_multi     = pick(user_cfg.y_multi     if user_cfg else None, base.y_multi,     method_defaults.y_multi),
            y_multi_label = pick(user_cfg.y_multi_label if user_cfg else None, base.y_multi_label, method_defaults.y_multi_label),
        )

    def _finish(self, fig, ax, path: Path, cfg: PlotConfig) -> Path:
        if cfg.title:  ax.set_title(cfg.title)
        if cfg.xlabel: ax.set_xlabel(cfg.xlabel)
        if cfg.ylabel: ax.set_ylabel(cfg.ylabel)
        if cfg.xlim:   ax.set_xlim(*cfg.xlim)
        if cfg.ylim:   ax.set_ylim(*cfg.ylim)
        if cfg.grid is True:
            ax.grid(True, which="both", linestyle="--", alpha=0.4)

        # Legend: None => auto (only if any labels exist)
        if cfg.legend is None:
            handles, labels = ax.get_legend_handles_labels()
            if any(labels):
                ax.legend(loc="best")
        elif cfg.legend is True:
            ax.legend(loc="best")

        if self.tight_layout:
            fig.tight_layout()

        path = path.with_suffix(".png")
        path.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(path, dpi=self.dpi, bbox_inches="tight", transparent=bool(cfg.transparent))
        plt.close(fig)
        self._update_png_file(path)
        self.logger.info("Saved plot: %s", path)
        return path

    # ---- tolerant array helpers (less validation) ----
    def _to_1d(self, a: Optional[ArrayLike]) -> np.ndarray:
        if a is None:
            return np.array([], dtype=float)
        arr = np.asarray(a, dtype=float).ravel()
        return arr

    def _coerce_xy(self, x: Optional[ArrayLike], y: Optional[ArrayLike]) -> Tuple[np.ndarray, np.ndarray]:
        xa = self._to_1d(x)
        ya = self._to_1d(y)
        if ya.size == 0 and xa.size > 0:
            # No Y but we have X: create zeros
            ya = np.zeros_like(xa, dtype=float)
            self.logger.warning("Y missing; using zeros (len=%d).", ya.size)
        if xa.size == 0 and ya.size > 0:
            xa = np.arange(ya.size, dtype=float)
            self.logger.debug("X missing; using arange(len(y)) (len=%d).", xa.size)
        if xa.size and ya.size and xa.size != ya.size:
            n = min(xa.size, ya.size)
            self.logger.warning("Length mismatch x=%d, y=%d; truncating to %d.", xa.size, ya.size, n)
            xa, ya = xa[:n], ya[:n]
        return xa, ya

    # ──────────────────────────── plots ────────────────────────────
    def plot_line(
        self,
        filename: Union[str, Path],
        *,
        x: Optional[ArrayLike] = None,
        y: Optional[ArrayLike] = None,
        label: Optional[str] = None,
        linewidth: Optional[float] = None,
        marker: Optional[str] = None,
        cfg: Optional[PlotConfig] = None,
    ) -> Path:
        defaults = PlotConfig(grid=True, legend=None, transparent=False)
        cfg = self._merge_cfg(cfg, defaults)
        x, y = self._coerce_xy(x if x is not None else cfg.x, y if y is not None else cfg.y)
        fig, ax = self._new_fig()
        ax.plot(x, y, label=label, linewidth=linewidth, marker=marker)
        return self._finish(fig, ax, self._resolve_path(filename), cfg)

    def plot_multi_line(
        self,
        series: Iterable[Tuple[ArrayLike, ArrayLike, Optional[str]]],
        filename: Union[str, Path],
        *,
        cfg: Optional[PlotConfig] = None,
    ) -> Path:
        defaults = PlotConfig(grid=True, legend=None, transparent=False)
        cfg = self._merge_cfg(cfg, defaults)
        fig, ax = self._new_fig()
        for x, y, label in series:
            x, y = self._coerce_xy(x, y)
            ax.plot(x, y, label=label)
        return self._finish(fig, ax, self._resolve_path(filename), cfg)

    def plot_multi_line_from_cfg(
        self,
        filename: Union[str, Path],
        *,
        cfg: Optional[PlotConfig] = None,
    ) -> Path:
        if cfg is None:
            cfg = PlotConfig()
        defaults = PlotConfig(grid=True, legend=None, transparent=False)
        cfg = self._merge_cfg(cfg, defaults)

        X = self._to_1d(cfg.x)
        ys = cfg.y_multi or []
        if not len(ys):
            self.logger.warning("cfg.y_multi is empty; producing empty axes.")
        labels = (cfg.y_multi_label or []) + [None] * max(0, len(ys) - len(cfg.y_multi_label or []))
        labels = labels[:len(ys)]

        fig, ax = self._new_fig()
        for i, (Y, lab) in enumerate(zip(ys, labels)):
            x_i, y_i = self._coerce_xy(X, Y)
            ax.plot(x_i, y_i, label=lab)
        return self._finish(fig, ax, self._resolve_path(filename), cfg)

    def plot_scatter(
        self,
        x: Optional[ArrayLike],
        y: Optional[ArrayLike],
        filename: Union[str, Path],
        *,
        c: Optional[ArrayLike] = None,
        s: Optional[ArrayLike] = None,
        add_colorbar: bool = True,
        cfg: Optional[PlotConfig] = None,
    ) -> Path:
        defaults = PlotConfig(grid=True, legend=None, transparent=False)
        cfg = self._merge_cfg(cfg, defaults)
        x, y = self._coerce_xy(x if x is not None else cfg.x, y if y is not None else cfg.y)
        fig, ax = self._new_fig()
        sc = ax.scatter(x, y,
                        c=None if c is None else np.asarray(c).ravel()[:len(x)],
                        s=None if s is None else np.asarray(s).ravel()[:len(x)])
        if add_colorbar and c is not None:
            fig.colorbar(sc, ax=ax)
        return self._finish(fig, ax, self._resolve_path(filename), cfg)

    def plot_bar(
        self,
        categories: Sequence[Union[str, Number]],
        values: ArrayLike,
        filename: Union[str, Path],
        *,
        orientation: str = "vertical",
        cfg: Optional[PlotConfig] = None,
    ) -> Path:
        vals = np.asarray(values, dtype=float).ravel()
        cats = list(categories)
        if len(cats) != len(vals):
            n = min(len(cats), len(vals))
            self.logger.warning("Bar: length mismatch; truncating to %d.", n)
            cats, vals = cats[:n], vals[:n]
        orient = "vertical" if orientation not in ("vertical", "horizontal") else orientation

        defaults = PlotConfig(grid=True, legend=None, transparent=False)
        cfg = self._merge_cfg(cfg, defaults)
        fig, ax = self._new_fig()
        idx = np.arange(len(cats))

        if orient == "vertical":
            ax.bar(idx, vals)
            ax.set_xticks(idx, labels=[str(c) for c in cats], rotation=0)
        else:
            ax.barh(idx, vals)
            ax.set_yticks(idx, labels=[str(c) for c in cats], rotation=0)

        return self._finish(fig, ax, self._resolve_path(filename), cfg)

    def plot_histogram(
        self,
        data: ArrayLike,
        filename: Union[str, Path],
        *,
        bins: Union[int, Sequence[Number]] = 30,
        range: Optional[Tuple[Number, Number]] = None,
        density: bool = False,
        cfg: Optional[PlotConfig] = None,
    ) -> Path:
        vals = np.asarray(data, dtype=float).ravel()
        defaults = PlotConfig(grid=True, legend=None, transparent=False)
        cfg = self._merge_cfg(cfg, defaults)
        fig, ax = self._new_fig()
        ax.hist(vals, bins=bins, range=range, density=density)
        return self._finish(fig, ax, self._resolve_path(filename), cfg)

    def plot_step(
        self,
        x: Optional[ArrayLike],
        y: Optional[ArrayLike],
        filename: Union[str, Path],
        *,
        where: str = "pre",
        cfg: Optional[PlotConfig] = None,
    ) -> Path:
        defaults = PlotConfig(grid=True, legend=None, transparent=False)
        cfg = self._merge_cfg(cfg, defaults)
        x, y = self._coerce_xy(x if x is not None else cfg.x, y if y is not None else cfg.y)
        fig, ax = self._new_fig()
        ax.step(x, y, where=where)
        return self._finish(fig, ax, self._resolve_path(filename), cfg)

    def plot_stem(
        self,
        x: Optional[ArrayLike],
        y: Optional[ArrayLike],
        filename: Union[str, Path],
        *,
        use_line_collection: bool = True,
        cfg: Optional[PlotConfig] = None,
    ) -> Path:
        defaults = PlotConfig(grid=True, legend=None, transparent=False)
        cfg = self._merge_cfg(cfg, defaults)
        x, y = self._coerce_xy(x if x is not None else cfg.x, y if y is not None else cfg.y)
        fig, ax = self._new_fig()
        markerline, stemlines, baseline = ax.stem(x, y, use_line_collection=use_line_collection)
        return self._finish(fig, ax, self._resolve_path(filename), cfg)

    def plot_errorbar(
        self,
        x: Optional[ArrayLike],
        y: Optional[ArrayLike],
        yerr: Optional[ArrayLike],
        filename: Union[str, Path],
        *,
        capsize: float = 3.0,
        cfg: Optional[PlotConfig] = None,
    ) -> Path:
        defaults = PlotConfig(grid=True, legend=None, transparent=False)
        cfg = self._merge_cfg(cfg, defaults)
        x, y = self._coerce_xy(x if x is not None else cfg.x, y if y is not None else cfg.y)
        ye = None if yerr is None else np.asarray(yerr, dtype=float).ravel()[:len(y)]
        fig, ax = self._new_fig()
        ax.errorbar(x, y, yerr=ye, capsize=capsize)
        return self._finish(fig, ax, self._resolve_path(filename), cfg)

    def plot_area(
        self,
        x: Optional[ArrayLike],
        y: Optional[ArrayLike],
        filename: Union[str, Path],
        *,
        y2: Optional[ArrayLike] = None,
        baseline: float = 0.0,
        cfg: Optional[PlotConfig] = None,
    ) -> Path:
        defaults = PlotConfig(grid=True, legend=None, transparent=False)
        cfg = self._merge_cfg(cfg, defaults)
        x, y = self._coerce_xy(x if x is not None else cfg.x, y if y is not None else cfg.y)
        fig, ax = self._new_fig()
        if y2 is not None:
            y2a = np.asarray(y2, dtype=float).ravel()[:len(y)]
            n = min(len(x), len(y), len(y2a))
            ax.fill_between(x[:n], y[:n], y2a[:n], alpha=0.3)
        else:
            ax.fill_between(x, baseline, y, alpha=0.3)
        return self._finish(fig, ax, self._resolve_path(filename), cfg)

    def heatmap2d(
        self,
        Z: ArrayLike,
        filename: Union[str, Path],
        *,
        x: Optional[ArrayLike] = None,
        y: Optional[ArrayLike] = None,
        interpolation: str = "nearest",
        origin: str = "lower",
        add_colorbar: bool = True,
        vmin: Optional[float] = None,
        vmax: Optional[float] = None,
        cfg: Optional[PlotConfig] = None,
    ) -> Path:
        Z = np.asarray(Z, dtype=float)
        if Z.ndim > 2:
            self.logger.warning("Z has ndim=%d; squeezing to 2D.", Z.ndim)
            Z = np.squeeze(Z)
        if Z.ndim == 1:
            Z = Z.reshape(-1, 1)

        defaults = PlotConfig(grid=False, legend=None, transparent=False)
        cfg = self._merge_cfg(cfg, defaults)

        # Use provided or cfg-based extents if available
        x = self._to_1d(x if x is not None else cfg.x)
        y = self._to_1d(y if y is not None else cfg.y)

        fig, ax = self._new_fig()
        extent = None
        if x.size and y.size:
            extent = [float(np.min(x)), float(np.max(x)), float(np.min(y)), float(np.max(y))]
        im = ax.imshow(Z, origin=origin, interpolation=interpolation,
                       vmin=vmin, vmax=vmax, extent=extent, aspect="auto")
        if add_colorbar:
            fig.colorbar(im, ax=ax)
        return self._finish(fig, ax, self._resolve_path(filename), cfg)

    def heatmap3d(
        self,
        Z: ArrayLike,
        filename: Union[str, Path],
        *,
        x: Optional[ArrayLike] = None,
        y: Optional[ArrayLike] = None,
        rstride: int = 1,
        cstride: int = 1,
        antialiased: bool = True,
        wireframe: bool = False,
        zlabel: Optional[str] = None,
        cfg: Optional[PlotConfig] = None,
    ) -> Path:
        Z = np.asarray(Z, dtype=float)
        if Z.ndim > 2:
            self.logger.warning("Z has ndim=%d; squeezing to 2D.", Z.ndim)
            Z = np.squeeze(Z)
        if Z.ndim == 1:
            Z = Z.reshape(-1, 1)
        ny, nx = Z.shape

        defaults = PlotConfig(grid=None, legend=None, transparent=False)
        cfg = self._merge_cfg(cfg, defaults)

        x = self._to_1d(x if x is not None else cfg.x)
        y = self._to_1d(y if y is not None else cfg.y)

        if not x.size:
            x = np.arange(nx, dtype=float)
        if not y.size:
            y = np.arange(ny, dtype=float)
        # If lengths mismatch, truncate
        if x.size != nx:
            n = min(x.size, nx)
            self.logger.warning("3D: x len=%d, nx=%d; truncating to %d.", x.size, nx, n)
            x = x[:n]; Z = Z[:, :n]; nx = n
        if y.size != ny:
            n = min(y.size, ny)
            self.logger.warning("3D: y len=%d, ny=%d; truncating to %d.", y.size, ny, n)
            y = y[:n]; Z = Z[:n, :]; ny = n

        X, Y = np.meshgrid(x, y)
        fig, ax = self._new_fig(projection="3d")
        if wireframe:
            ax.plot_wireframe(X, Y, Z, rstride=rstride, cstride=cstride, antialiased=antialiased)
        else:
            ax.plot_surface(X, Y, Z, rstride=rstride, cstride=cstride, antialiased=antialiased)

        if cfg.title:  ax.set_title(cfg.title)
        if cfg.xlabel: ax.set_xlabel(cfg.xlabel)
        if cfg.ylabel: ax.set_ylabel(cfg.ylabel)
        zl = zlabel if zlabel is not None else cfg.zlabel
        if zl: ax.set_zlabel(zl)
        if self.tight_layout:
            fig.tight_layout()

        path = self._resolve_path(filename).with_suffix(".png")
        path.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(path, dpi=self.dpi, bbox_inches="tight", transparent=bool(cfg.transparent))
        plt.close(fig)
        self._update_png_file(path)
        self.logger.info("Saved 3D plot: %s", path)
        return path
