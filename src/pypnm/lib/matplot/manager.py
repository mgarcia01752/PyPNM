# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia

from __future__ import annotations

import logging
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Iterable, List, Optional, Sequence, Tuple, Union

import numpy as np
import matplotlib
matplotlib.use("Agg")  # Headless backend for servers/CI
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D  # noqa: F401  (registers '3d' projection)

from pypnm.lib.code_word.cw_generator import QamModulation
from pypnm.lib.types import ArrayLike, ComplexArray, Number


@dataclass(frozen=True)
class PlotConfig:
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

    # Constellation (new)
    qam: Optional[QamModulation] = None
    soft: Optional[ComplexArray] = None
    hard: Optional[ComplexArray] = None

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
            qam         = pick(user_cfg.qam         if user_cfg else None, base.qam,         method_defaults.qam),   # NEW
            soft        = pick(user_cfg.soft        if user_cfg else None, base.soft,        method_defaults.soft),  # NEW
            hard        = pick(user_cfg.hard        if user_cfg else None, base.hard,        method_defaults.hard),  # NEW
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

    def _split_complex_array(self, arr: Optional[ComplexArray]) -> Tuple[np.ndarray, np.ndarray]:
        """
        Convert ComplexArray[List[Tuple[float, float]]] -> (I, Q) float arrays.
        Returns empty arrays if arr is None or empty.
        """
        if not arr:
            return np.array([], dtype=float), np.array([], dtype=float)
        a = np.asarray(arr, dtype=float)
        if a.ndim != 2 or a.shape[-1] != 2:
            a = np.asarray(arr, dtype=float).ravel()
            if a.size % 2:
                a = a[:-1]
            a = a.reshape(-1, 2)
        return a[:, 0], a[:, 1]

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
        filename: Union[str, Path],
        *,
        series: Optional[Iterable[Tuple[ArrayLike, ArrayLike, Optional[str]]]] = None,
        linewidth: Optional[float] = None,
        marker: Optional[str] = None,
        cfg: Optional[PlotConfig] = None,
    ) -> Path:
        """
        Create and save a multi-line plot.

        Precedence (like plot_line):
        - If cfg.y_multi is provided, it overrides `series` entirely; uses cfg.x and cfg.y_multi_label.
        - Else, use `series`; if cfg.x is provided, it overrides each tuple's x.
        - If neither is provided, plot an empty axes and warn.

        Styling parity with plot_line: supports `linewidth` and `marker`.
        """
        defaults = PlotConfig(grid=True, legend=None, transparent=False)
        cfg = self._merge_cfg(cfg, defaults)
        fig, ax = self._new_fig()

        # Case 1: cfg provides the data for all lines (overrides `series`)
        if cfg and cfg.y_multi:
            X = self._to_1d(cfg.x)
            ys = list(cfg.y_multi)
            labels = list(cfg.y_multi_label or [])
            # pad/truncate labels to match y-series count
            if len(labels) < len(ys):
                labels += [None] * (len(ys) - len(labels))
            else:
                labels = labels[:len(ys)]

            for Y, lab in zip(ys, labels):
                x_i, y_i = self._coerce_xy(X, Y)
                ax.plot(x_i, y_i, label=lab, linewidth=linewidth, marker=marker)
            return self._finish(fig, ax, self._resolve_path(filename), cfg)

        # Case 2: use provided series; cfg.x (if present) overrides per-series x
        if series:
            override_x = (cfg.x is not None)
            X_override = self._to_1d(cfg.x) if override_x else None
            cfg_labels = list(cfg.y_multi_label or [])

            for idx, (sx, sy, slabel) in enumerate(series):
                label = cfg_labels[idx] if idx < len(cfg_labels) else slabel
                x_src = X_override if override_x else sx
                x_i, y_i = self._coerce_xy(x_src, sy)
                ax.plot(x_i, y_i, label=label, linewidth=linewidth, marker=marker)
            return self._finish(fig, ax, self._resolve_path(filename), cfg)

        # Case 3: nothing to plot
        self.logger.warning("plot_multi_line: no data provided (neither cfg.y_multi nor series).")
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
        sc = ax.scatter(
            x, y,
            c=None if c is None else np.asarray(c).ravel()[:len(x)],
            s=None if s is None else np.asarray(s).ravel()[:len(x)]
        )
        if add_colorbar and c is not None:
            fig.colorbar(sc, ax=ax)
        return self._finish(fig, ax, self._resolve_path(filename), cfg)

    def plot_constellation(
        self,
        soft: Optional[ComplexArray],
        filename: Union[str, Path],
        *,
        hard: Optional[ComplexArray] = None,
        show_boundaries: bool = True,
        boundary_alpha: float = 0.25,
        crosshair_size: float = 80.0,
        crosshair_lw: float = 1.8,
        cfg: Optional[PlotConfig] = None,
    ) -> Path:
        """
        Constellation plot (DOCSIS-style):
        - Soft decisions (I/Q samples) as points
        - Hard decisions as red '+' crosshairs
        - Decision boundaries (midpoints between unique hard I/Q levels)

        Data precedence: args.soft/args.hard > cfg.soft/cfg.hard
        """
        defaults = PlotConfig(grid=True, legend=None, transparent=False)
        cfg = self._merge_cfg(cfg, defaults)

        # Fallback to cfg if args not provided
        if soft is None:
            soft = cfg.soft
        if hard is None:
            hard = cfg.hard

        # Split soft/hard into I (x) and Q (y)
        x_soft, y_soft = self._split_complex_array(soft)
        x_hard, y_hard = self._split_complex_array(hard)

        if x_soft.size == 0 or y_soft.size == 0:
            self.logger.warning("plot_constellation: no soft samples provided; producing empty axes.")

        fig, ax = self._new_fig()

        # Soft cloud
        if x_soft.size and y_soft.size:
            ax.scatter(x_soft, y_soft, alpha=0.75, label="Soft")

        # Hard centroids as red crosshairs + decision boundaries
        if x_hard.size and y_hard.size:
            n = min(x_hard.size, y_hard.size)
            ax.scatter(
                x_hard[:n], y_hard[:n],
                marker="+",
                c="red",
                s=crosshair_size,
                linewidths=crosshair_lw,
                label="Hard",
            )

            if show_boundaries:
                # Unique decision levels and midpoints
                levels_i = np.unique(x_hard[:n])
                levels_q = np.unique(y_hard[:n])
                mids_i = (levels_i[1:] + levels_i[:-1]) / 2.0 if levels_i.size >= 2 else np.array([])
                mids_q = (levels_q[1:] + levels_q[:-1]) / 2.0 if levels_q.size >= 2 else np.array([])

                # Determine extents with small padding
                all_x = np.concatenate([x_soft, x_hard[:n]]) if x_soft.size else x_hard[:n]
                all_y = np.concatenate([y_soft, y_hard[:n]]) if y_soft.size else y_hard[:n]
                if all_x.size:
                    x_min, x_max = float(np.min(all_x)), float(np.max(all_x))
                    x_pad = 0.05 * (x_max - x_min if x_max > x_min else 1.0)
                    x_lo, x_hi = x_min - x_pad, x_max + x_pad
                else:
                    x_lo, x_hi = -1.0, 1.0
                if all_y.size:
                    y_min, y_max = float(np.min(all_y)), float(np.max(all_y))
                    y_pad = 0.05 * (y_max - y_min if y_max > y_min else 1.0)
                    y_lo, y_hi = y_min - y_pad, y_max + y_pad
                else:
                    y_lo, y_hi = -1.0, 1.0

                # Draw vertical (I) and horizontal (Q) decision midlines
                for mx in mids_i:
                    ax.axvline(mx, linestyle="--", linewidth=1.0, alpha=boundary_alpha, zorder=0)
                for my in mids_q:
                    ax.axhline(my, linestyle="--", linewidth=1.0, alpha=boundary_alpha, zorder=0)

                # Respect explicit cfg.xlim/ylim; otherwise apply computed limits
                if cfg.xlim is None:
                    ax.set_xlim(x_lo, x_hi)
                if cfg.ylim is None:
                    ax.set_ylim(y_lo, y_hi)

        # Square aspect for constellation geometry
        try:
            ax.set_aspect("equal", adjustable="datalim")
        except Exception:
            pass

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
        ax.stem(x, y, use_line_collection=use_line_collection)
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
