# pypnm/lib/matplot/manager.py
# SPDX-License-Identifier: MIT
from __future__ import annotations

import logging
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Iterable, List, Literal, Optional, Sequence, Tuple, Union
from itertools import cycle
from contextlib import nullcontext
from datetime import datetime

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import EngFormatter, FuncFormatter, ScalarFormatter

from pypnm.lib.code_word.cw_generator import QamModulation
from pypnm.lib.types import ArrayLike, ComplexArray, Number

ThemeType = Literal["dark", "light", True, False]

CROSSHAIR_MARKER_SIZE_PTS: float = 24.0
CROSSHAIR_LINEWIDTH_PTS: float = 0.6


@dataclass(frozen=True)
class PlotConfig:
    """
    Lightweight configuration bundle for Matplotlib plots.

    Notes
    -----
    - Theme: set `theme="dark"` or True for dark_background style.
    - X-tick formatting:
        * x_tick_mode="none" → raw numeric ticks.
        * x_tick_mode="eng"  → SI engineering formatter with Hz unit.
        * x_tick_mode="unit" → force ticks into Hz/kHz/MHz/GHz via x_unit_from/x_unit_out.
    - Human time label:
        * x_time_labels="from_to" uses X limits as epoch to render "start → end" as xlabel.
        * x_time_input_unit in {"s","ms","ns"} controls epoch scaling.
        * x_ticks_visible=False hides ticks/labels while keeping the single range label.
    - X label prefix:
        * xlabel_prefix prepends a string to any resolved x-axis label (explicit, unit/eng, or from_to).
    """
    # Data
    x: Optional[ArrayLike] = None
    y: Optional[ArrayLike] = None
    z: Optional[ArrayLike] = None
    y_multi: Optional[List[ArrayLike]] = None
    y_multi_label: Optional[List[str]] = None

    # Labels / title
    xlabel: Optional[str] = None
    ylabel: Optional[str] = None
    zlabel: Optional[str] = None
    title: Optional[str] = None
    xlabel_prefix: Optional[str] = None

    # Limits and style
    xlim: Optional[Tuple[Number, Number]] = None
    ylim: Optional[Tuple[Number, Number]] = None
    grid: Optional[bool] = None
    legend: Optional[bool] = None
    transparent: Optional[bool] = None

    # Constellation data
    qam: Optional[QamModulation] = None
    soft: Optional[ComplexArray] = None
    hard: Optional[ComplexArray] = None

    # Theme
    theme: Optional[ThemeType] = None

    # X tick formatting
    x_tick_mode: Optional[Literal["none", "eng", "unit"]] = "none"
    x_unit_from: Optional[Literal["hz", "khz", "mhz", "ghz"]] = "hz"
    x_unit_out: Optional[Literal["hz", "khz", "mhz", "ghz"]] = "mhz"
    x_tick_decimals: Optional[int] = None
    xlabel_base: Optional[str] = None

    # Line color controls
    line_color: Optional[str] = None
    line_colors: Optional[List[str]] = None

    # X-axis visibility / human time label
    x_ticks_visible: bool = True
    x_time_labels: Optional[Literal["none", "from_to"]] = "none"
    x_time_input_unit: Optional[Literal["s", "ms", "ns"]] = "s"
    x_time_format: Optional[str] = "%Y-%m-%d %H:%M:%S"

    def update(self, **kwargs) -> "PlotConfig":
        """Create a new PlotConfig with fields replaced by kwargs."""
        return replace(self, **kwargs)


class MatplotManager:
    """
    Lightweight Matplotlib wrapper for saving common plot types as PNG files.

    Parameters
    ----------
    output_dir : Union[str, Path]
        Directory where PNGs are written.
    dpi : int
        Figure DPI.
    figsize : Tuple[float, float]
        Figure size in inches.
    tight_layout : bool
        Apply `fig.tight_layout()` prior to save.
    default_cfg : Optional[PlotConfig]
        Default configuration applied to all plots (can be overridden per call).
    logger : Optional[logging.Logger]
        Logger instance; defaults to module logger.
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

    # ───────────────────────── internals ─────────────────────────

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
        """Return a list of all PNG paths created by this manager instance."""
        return self._png_files

    def _merge_cfg(self, user_cfg: Optional[PlotConfig], method_defaults: PlotConfig) -> PlotConfig:
        base = self.default_cfg
        def pick(top, mid, low):
            return top if top is not None else (mid if mid is not None else low)
        return PlotConfig(
            title               = pick(user_cfg.title               if user_cfg else None, base.title,       method_defaults.title),
            xlabel              = pick(user_cfg.xlabel              if user_cfg else None, base.xlabel,      method_defaults.xlabel),
            ylabel              = pick(user_cfg.ylabel              if user_cfg else None, base.ylabel,      method_defaults.ylabel),
            zlabel              = pick(user_cfg.zlabel              if user_cfg else None, base.zlabel,      method_defaults.zlabel),
            xlabel_prefix       = pick(user_cfg.xlabel_prefix       if user_cfg else None, base.xlabel_prefix, method_defaults.xlabel_prefix),
            xlim                = pick(user_cfg.xlim                if user_cfg else None, base.xlim,        method_defaults.xlim),
            ylim                = pick(user_cfg.ylim                if user_cfg else None, base.ylim,        method_defaults.ylim),
            grid                = pick(user_cfg.grid                if user_cfg else None, base.grid,        method_defaults.grid),
            legend              = pick(user_cfg.legend              if user_cfg else None, base.legend,      method_defaults.legend),
            transparent         = pick(user_cfg.transparent         if user_cfg else None, base.transparent, method_defaults.transparent),
            x                   = pick(user_cfg.x                   if user_cfg else None, base.x,           method_defaults.x),
            y                   = pick(user_cfg.y                   if user_cfg else None, base.y,           method_defaults.y),
            z                   = pick(user_cfg.z                   if user_cfg else None, base.z,           method_defaults.z),
            y_multi             = pick(user_cfg.y_multi             if user_cfg else None, base.y_multi,     method_defaults.y_multi),
            y_multi_label       = pick(user_cfg.y_multi_label       if user_cfg else None, base.y_multi_label, method_defaults.y_multi_label),
            qam                 = pick(user_cfg.qam                 if user_cfg else None, base.qam,         method_defaults.qam),
            soft                = pick(user_cfg.soft                if user_cfg else None, base.soft,        method_defaults.soft),
            hard                = pick(user_cfg.hard                if user_cfg else None, base.hard,        method_defaults.hard),
            theme               = pick(user_cfg.theme               if user_cfg else None, base.theme,       method_defaults.theme),
            x_tick_mode         = pick(user_cfg.x_tick_mode         if user_cfg else None, base.x_tick_mode, method_defaults.x_tick_mode),
            x_unit_from         = pick(user_cfg.x_unit_from         if user_cfg else None, base.x_unit_from, method_defaults.x_unit_from),
            x_unit_out          = pick(user_cfg.x_unit_out          if user_cfg else None, base.x_unit_out,  method_defaults.x_unit_out),
            x_tick_decimals     = pick(user_cfg.x_tick_decimals     if user_cfg else None, base.x_tick_decimals, method_defaults.x_tick_decimals),
            xlabel_base         = pick(user_cfg.xlabel_base         if user_cfg else None, base.xlabel_base, method_defaults.xlabel_base),
            line_color          = pick(user_cfg.line_color          if user_cfg else None, base.line_color,  method_defaults.line_color),
            line_colors         = pick(user_cfg.line_colors         if user_cfg else None, base.line_colors, method_defaults.line_colors),
            x_ticks_visible     = pick(user_cfg.x_ticks_visible     if user_cfg else None, base.x_ticks_visible,   method_defaults.x_ticks_visible),
            x_time_labels       = pick(user_cfg.x_time_labels       if user_cfg else None, base.x_time_labels,     method_defaults.x_time_labels),
            x_time_input_unit   = pick(user_cfg.x_time_input_unit   if user_cfg else None, base.x_time_input_unit, method_defaults.x_time_input_unit),
            x_time_format       = pick(user_cfg.x_time_format       if user_cfg else None, base.x_time_format,     method_defaults.x_time_format),
        )

    def _theme_context(self, cfg: Optional[PlotConfig]):
        theme = getattr(cfg, "theme", None) if cfg is not None else None
        if theme in ("dark", True):
            return plt.style.context("dark_background")
        return nullcontext()

    def _apply_x_ticks(self, ax, cfg: PlotConfig):
        """Apply x-axis tick formatter/visibility and optional human time label."""
        mode = (cfg.x_tick_mode or "none").lower()
        try:
            ax.ticklabel_format(axis="x", style="plain", useOffset=False)
            sf = ScalarFormatter(useOffset=False)
            sf.set_scientific(False)
            ax.xaxis.set_major_formatter(sf)
            ax.get_xaxis().get_offset_text().set_visible(False)
        except Exception:
            pass

        # Optional single "start → end" label from epoch timestamps
        if (cfg.x_time_labels or "none") == "from_to":
            x_min, x_max = ax.get_xlim()
            unit = (cfg.x_time_input_unit or "s").lower()
            if unit == "ms":
                x_min /= 1_000.0; x_max /= 1_000.0
            elif unit == "ns":
                x_min /= 1_000_000_000.0
            fmt = cfg.x_time_format or "%Y-%m-%d %H:%M:%S"
            try:
                start_str = datetime.fromtimestamp(float(x_min)).strftime(fmt)
                end_str   = datetime.fromtimestamp(float(x_max)).strftime(fmt)
                if not cfg.xlabel:
                    prefix = cfg.xlabel_prefix or ""
                    ax.set_xlabel(f"{prefix}{start_str} → {end_str}")
            except Exception:
                pass
            if cfg.x_ticks_visible is False:
                ax.set_xticks([])
                ax.tick_params(axis="x", which="both", labelbottom=False)
                return

        if cfg.x_ticks_visible is False:
            ax.set_xticks([])
            ax.tick_params(axis="x", which="both", labelbottom=False)
            return

        if mode == "none":
            return
        if mode == "eng":
            ax.xaxis.set_major_formatter(EngFormatter(unit="Hz"))
            if not cfg.xlabel:
                base = cfg.xlabel_base or "Frequency"
                prefix = cfg.xlabel_prefix or ""
                ax.set_xlabel(f"{prefix}{base}")
            return
        if mode == "unit":
            unit_info = {"hz": (1.0, "Hz"), "khz": (1e3, "kHz"), "mhz": (1e6, "MHz"), "ghz": (1e9, "GHz")}
            u_in  = (cfg.x_unit_from or "hz").lower()
            u_out = (cfg.x_unit_out  or "mhz").lower()
            fin,  _       = unit_info.get(u_in,  unit_info["hz"])
            fout, lab_out = unit_info.get(u_out, unit_info["mhz"])
            mult = fin / fout

            if cfg.x_tick_decimals is None:
                def _fmt(v, m=mult):
                    s = f"{v*m:.6f}".rstrip("0").rstrip(".")
                    return s if s else "0"
            else:
                d = max(0, int(cfg.x_tick_decimals))
                def _fmt(v, m=mult, d=d):
                    return f"{v*m:.{d}f}"

            ax.xaxis.set_major_formatter(FuncFormatter(lambda v, pos: _fmt(v)))
            try:
                ax.get_xaxis().get_offset_text().set_visible(False)
            except Exception:
                pass
            if not cfg.xlabel:
                base = cfg.xlabel_base or "Frequency"
                prefix = cfg.xlabel_prefix or ""
                ax.set_xlabel(f"{prefix}{base} ({lab_out})")

    def _finish(self, fig, ax, path: Path, cfg: "PlotConfig") -> Path:
        """
        Finalize axes styling, save PNG to disk, and register the output path.

        Returns
        -------
        Path
            Absolute path to the saved PNG.
        """
        if cfg.title:
            ax.set_title(cfg.title)

        # If user supplied an explicit xlabel, prepend prefix here
        if cfg.xlabel:
            prefix = cfg.xlabel_prefix or ""
            ax.set_xlabel(f"{prefix}{cfg.xlabel}")

        if cfg.ylabel:
            ax.set_ylabel(cfg.ylabel)
        if cfg.xlim:
            ax.set_xlim(*cfg.xlim)
        if cfg.ylim:
            ax.set_ylim(*cfg.ylim)

        if cfg.grid is True:
            ax.grid(True, which="both", linestyle="--", alpha=0.4)

        if cfg.legend is None:
            handles, labels = ax.get_legend_handles_labels()
            if any(labels):
                ax.legend(loc="best")
        elif cfg.legend is True:
            ax.legend(loc="best")

        if self.tight_layout:
            fig.tight_layout()

        out = path.with_suffix(".png")
        out.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(out, dpi=self.dpi, bbox_inches="tight", transparent=bool(cfg.transparent))
        plt.close(fig)

        self._update_png_file(out)
        self.logger.debug("Saved plot: %s", out)
        return out

    # ───────────────────────── helpers ─────────────────────────

    def _to_1d(self, a: Optional[ArrayLike]) -> np.ndarray:
        """Convert input to a flattened float64 numpy array (empty if None)."""
        if a is None:
            return np.array([], dtype=float)
        return np.asarray(a, dtype=float).ravel()

    def _coerce_xy(self, x: Optional[ArrayLike], y: Optional[ArrayLike]) -> Tuple[np.ndarray, np.ndarray]:
        """Validate/align X and Y arrays; auto-generate missing axis, truncate to min length."""
        xa = self._to_1d(x if x is not None else None)
        ya = self._to_1d(y if y is not None else None)
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
        """Split ComplexArray into (I, Q) float arrays, accepting [N,2] or flat [2N] inputs."""
        if not arr:
            return np.array([], dtype=float), np.array([], dtype=float)
        a = np.asarray(arr, dtype=float)
        if a.ndim != 2 or a.shape[-1] != 2:
            a = np.asarray(arr, dtype=float).ravel()
            if a.size % 2:
                a = a[:-1]
            a = a.reshape(-1, 2)
        return a[:, 0], a[:, 1]

    def _resolve_colors(self, count: int, cfg: PlotConfig) -> List[Optional[str]]:
        """Resolve per-series colors: cycle cfg.line_colors or use Matplotlib defaults."""
        if not cfg.line_colors:
            return [None] * count
        if len(cfg.line_colors) >= count:
            return list(cfg.line_colors[:count])
        cyc = cycle(cfg.line_colors)
        return [next(cyc) for _ in range(count)]

    # ───────────────────────── plots ─────────────────────────

    def plot_line(
        self,
        filename: Union[str, Path],
        *,
        x: Optional[ArrayLike] = None,
        y: Optional[ArrayLike] = None,
        label: Optional[str] = None,
        linewidth: Optional[float] = None,
        marker: Optional[str] = None,
        color: Optional[str] = None,
        cfg: Optional[PlotConfig] = None,
    ) -> Path:
        """
        Plot a single line and save as PNG.

        Returns
        -------
        Path
            Absolute path to the saved PNG.
        """
        defaults = PlotConfig(grid=True, legend=None, transparent=False)
        cfg = self._merge_cfg(cfg, defaults)
        x, y = self._coerce_xy(x if x is not None else cfg.x, y if y is not None else cfg.y)
        resolved_color = color if color is not None else cfg.line_color
        with self._theme_context(cfg):
            fig, ax = self._new_fig()
            ax.plot(x, y, label=label, linewidth=linewidth, marker=marker, color=resolved_color)
            self._apply_x_ticks(ax, cfg)
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
        Plot multiple line series and save as PNG.

        Notes
        -----
        - Uses `cfg.y_multi`/`cfg.y_multi_label` if provided; otherwise consumes `series`.
        - Colors cycle through `cfg.line_colors` or Matplotlib defaults.

        Returns
        -------
        Path
            Absolute path to the saved PNG.
        """
        defaults = PlotConfig(grid=True, legend=None, transparent=False)
        cfg = self._merge_cfg(cfg, defaults)
        with self._theme_context(cfg):
            fig, ax = self._new_fig()

            if cfg and cfg.y_multi:
                X = self._to_1d(cfg.x)
                ys = list(cfg.y_multi)
                labels = list(cfg.y_multi_label or [])
                if len(labels) < len(ys):
                    labels += [None] * (len(ys) - len(labels))
                else:
                    labels = labels[:len(ys)]
                colors = self._resolve_colors(len(ys), cfg)
                for Y, lab, col in zip(ys, labels, colors):
                    x_i, y_i = self._coerce_xy(X, Y)
                    ax.plot(x_i, y_i, label=lab, linewidth=linewidth, marker=marker, color=col)
                self._apply_x_ticks(ax, cfg)
                return self._finish(fig, ax, self._resolve_path(filename), cfg)

            if series:
                override_x = (cfg.x is not None)
                X_override = self._to_1d(cfg.x) if override_x else None
                ser = list(series)
                colors = self._resolve_colors(len(ser), cfg)
                cfg_labels = list(cfg.y_multi_label or [])
                for idx, ((sx, sy, slabel), col) in enumerate(zip(ser, colors)):
                    label = cfg_labels[idx] if idx < len(cfg_labels) else slabel
                    x_src = X_override if override_x else sx
                    x_i, y_i = self._coerce_xy(x_src, sy)
                    ax.plot(x_i, y_i, label=label, linewidth=linewidth, marker=marker, color=col)
                self._apply_x_ticks(ax, cfg)
                return self._finish(fig, ax, self._resolve_path(filename), cfg)

            self.logger.warning("plot_multi_line: no data provided (neither cfg.y_multi nor series).")
            self._apply_x_ticks(ax, cfg)
            return self._finish(fig, ax, self._resolve_path(filename), cfg)

    def plot_multi_line_from_cfg(self, filename: Union[str, Path], *, cfg: Optional[PlotConfig] = None) -> Path:
        """
        Plot multiple line series using only the provided PlotConfig.

        Returns
        -------
        Path
            Absolute path to the saved PNG.
        """
        if cfg is None:
            cfg = PlotConfig()
        defaults = PlotConfig(grid=True, legend=None, transparent=False)
        cfg = self._merge_cfg(cfg, defaults)

        X = self._to_1d(cfg.x)
        ys = cfg.y_multi or []
        labels = (cfg.y_multi_label or []) + [None] * max(0, len(ys) - len(cfg.y_multi_label or []))
        labels = labels[:len(ys)]
        colors = self._resolve_colors(len(ys), cfg)

        with self._theme_context(cfg):
            fig, ax = self._new_fig()
            for Y, lab, col in zip(ys, labels, colors):
                x_i, y_i = self._coerce_xy(X, Y)
                ax.plot(x_i, y_i, label=lab, color=col)
            self._apply_x_ticks(ax, cfg)
            return self._finish(fig, ax, self._resolve_path(filename), cfg)

    def plot_constellation(
        self,
        filename: Union[str, Path],
        *,
        hard: Optional[ComplexArray] = None,
        soft: Optional[ComplexArray] = None,
        show_boundaries: bool = True,
        boundary_alpha: float = 0.25,
        cfg: Optional[PlotConfig] = None,
    ) -> Path:
        """
        Plot a QAM constellation. Axis ticks are suppressed; only axis labels are shown.

        Returns
        -------
        Path
            Absolute path to the saved PNG.
        """
        import matplotlib.patches as mpatches
        defaults = PlotConfig(grid=False, legend=None, transparent=False)
        cfg = self._merge_cfg(cfg, defaults)

        if soft is None:
            soft = cfg.soft
        if hard is None:
            hard = cfg.hard

        x_soft, y_soft = self._split_complex_array(soft)
        x_hard, y_hard = self._split_complex_array(hard)

        with self._theme_context(cfg):
            fig, ax = self._new_fig()

            if x_soft.size and y_soft.size:
                ax.scatter(x_soft, y_soft, marker='.', s=8, linewidths=0, edgecolors='none', alpha=0.75, label='Soft', rasterized=True)

            n = min(x_hard.size, y_hard.size)
            if n:
                ax.scatter(x_hard[:n], y_hard[:n], marker="+", c="red", s=CROSSHAIR_MARKER_SIZE_PTS, linewidths=CROSSHAIR_LINEWIDTH_PTS, label="Hard")

            if show_boundaries and n:
                levels_i = np.unique(x_hard[:n])
                levels_q = np.unique(y_hard[:n])

                def half_step(levels: np.ndarray) -> float:
                    if levels.size < 2:
                        return 0.5
                    gaps = np.diff(np.sort(levels))
                    if not np.all(np.isfinite(gaps)) or gaps.size == 0:
                        return 0.5
                    return float(np.min(gaps)) / 2.0

                hx = half_step(levels_i)
                hy = half_step(levels_q)
                lw = 0.3
                for xi, yi in zip(x_hard[:n], y_hard[:n]):
                    rect = mpatches.Rectangle((xi - hx, yi - hy), 2.0 * hx, 2.0 * hy, fill=False, linewidth=lw, alpha=boundary_alpha, edgecolor="gray", zorder=0, clip_on=True)
                    ax.add_patch(rect)

                all_x = np.concatenate([x_soft, x_hard[:n]]) if x_soft.size else x_hard[:n]
                all_y = np.concatenate([y_soft, y_hard[:n]]) if y_soft.size else y_hard[:n]
                if all_x.size and cfg.xlim is None:
                    x_min, x_max = float(np.min(all_x)), float(np.max(all_x))
                    pad = 0.05 * max(1e-9, (x_max - x_min))
                    ax.set_xlim(x_min - pad, x_max + pad)
                if all_y.size and cfg.ylim is None:
                    y_min, y_max = float(np.min(all_y)), float(np.max(all_y))
                    pad = 0.05 * max(1e-9, (y_max - y_min))
                    ax.set_ylim(y_min - pad, y_max + pad)

            try:
                ax.set_aspect("equal", adjustable="datalim")
            except Exception:
                pass

            if not cfg.xlabel:
                ax.set_xlabel("In-phase (I)")
            if not cfg.ylabel:
                ax.set_ylabel("Quadrature (Q)")

            ax.tick_params(axis="x", which="both", labelbottom=False)
            ax.tick_params(axis="y", which="both", labelleft=False)
            try:
                ax.get_xaxis().get_offset_text().set_visible(False)
                ax.get_yaxis().get_offset_text().set_visible(False)
            except Exception:
                pass

            self._apply_x_ticks(ax, cfg)
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
        """
        Plot a bar chart (vertical or horizontal) and save as PNG.

        Returns
        -------
        Path
            Absolute path to the saved PNG.
        """
        vals = np.asarray(values, dtype=float).ravel()
        cats = list(categories)
        if len(cats) != len(vals):
            n = min(len(cats), len(vals))
            self.logger.warning("Bar: length mismatch; truncating to %d.", n)
            cats, vals = cats[:n], vals[:n]
        orient = "vertical" if orientation not in ("vertical", "horizontal") else orientation

        defaults = PlotConfig(grid=True, legend=None, transparent=False)
        cfg = self._merge_cfg(cfg, defaults)
        with self._theme_context(cfg):
            fig, ax = self._new_fig()
            idx = np.arange(len(cats))

            if orient == "vertical":
                ax.bar(idx, vals)
                ax.set_xticks(idx, labels=[str(c) for c in cats], rotation=0)
            else:
                ax.barh(idx, vals)
                ax.set_yticks(idx, labels=[str(c) for c in cats], rotation=0)

            self._apply_x_ticks(ax, cfg)
            return self._finish(fig, ax, self._resolve_path(filename), cfg)

    def plot_histogram(
        self,
        data: ArrayLike,
        filename: Union[str, Path],
        *,
        bins: Union[int, Sequence[Number]] = 30,
        range: Optional[Tuple[Number, Number]] = None,
        density: bool = False,
        weights: Optional[ArrayLike] = None,
        orientation: Literal["vertical", "horizontal"] = "vertical",
        cumulative: bool = False,
        histtype: Literal["bar", "step", "stepfilled", "barstacked"] = "bar",
        align: Literal["mid", "left", "right"] = "mid",
        label: Optional[str] = None,
        cfg: Optional[PlotConfig] = None,
    ) -> Path:
        """
        Plot a histogram and save as PNG.

        Returns
        -------
        Path
            Absolute path to the saved PNG.
        """
        vals = np.asarray(data, dtype=float).ravel()

        w = None
        if weights is not None:
            w = np.asarray(weights, dtype=float).ravel()
            if w.size != vals.size:
                n = min(w.size, vals.size)
                vals = vals[:n]; w = w[:n]

        defaults = PlotConfig(grid=True, legend=None, transparent=False)
        cfg = self._merge_cfg(cfg, defaults)
        with self._theme_context(cfg):
            fig, ax = self._new_fig()

            ax.hist(
                vals,
                bins=bins,
                range=range,
                density=density,
                weights=w,
                orientation=orientation,
                cumulative=cumulative,
                histtype=histtype,
                align=align,
                label=label,
            )

            if label is not None and cfg.legend is not False:
                ax.legend()

            self._apply_x_ticks(ax, cfg)
            out_path = self._finish(fig, ax, self._resolve_path(filename), cfg)

        if hasattr(self, "logger"):
            try:
                self.logger.info(f"Saved histogram to {out_path}")
            except Exception:
                pass
        return out_path

    def plot_step(
        self,
        x: Optional[ArrayLike],
        y: Optional[ArrayLike],
        filename: Union[str, Path],
        *,
        where: str = "pre",
        cfg: Optional[PlotConfig] = None,
    ) -> Path:
        """
        Plot a step chart and save as PNG.

        Returns
        -------
        Path
            Absolute path to the saved PNG.
        """
        defaults = PlotConfig(grid=True, legend=None, transparent=False)
        cfg = self._merge_cfg(cfg, defaults)
        x, y = self._coerce_xy(x if x is not None else cfg.x, y if y is not None else cfg.y)
        with self._theme_context(cfg):
            fig, ax = self._new_fig()
        ax.step(x, y, where=where)
        self._apply_x_ticks(ax, cfg)
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
        """
        Plot a stem chart and save as PNG.

        Returns
        -------
        Path
            Absolute path to the saved PNG.
        """
        defaults = PlotConfig(grid=True, legend=None, transparent=False)
        cfg = self._merge_cfg(cfg, defaults)
        x, y = self._coerce_xy(x if x is not None else cfg.x, y if y is not None else cfg.y)
        with self._theme_context(cfg):
            fig, ax = self._new_fig()
            ax.stem(x, y, use_line_collection=use_line_collection)
            self._apply_x_ticks(ax, cfg)
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
        """
        Plot a line with error bars and save as PNG.

        Returns
        -------
        Path
            Absolute path to the saved PNG.
        """
        defaults = PlotConfig(grid=True, legend=None, transparent=False)
        cfg = self._merge_cfg(cfg, defaults)
        x, y = self._coerce_xy(x if x is not None else cfg.x, y if y is not None else cfg.y)
        ye = None if yerr is None else np.asarray(yerr, dtype=float).ravel()[:len(y)]
        with self._theme_context(cfg):
            fig, ax = self._new_fig()
            ax.errorbar(x, y, yerr=ye, capsize=capsize)
            self._apply_x_ticks(ax, cfg)
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
        """
        Plot a filled area (optionally between y and y2) and save as PNG.

        Returns
        -------
        Path
            Absolute path to the saved PNG.
        """
        defaults = PlotConfig(grid=True, legend=None, transparent=False)
        cfg = self._merge_cfg(cfg, defaults)
        x, y = self._coerce_xy(x if x is not None else cfg.x, y if y is not None else cfg.y)
        with self._theme_context(cfg):
            fig, ax = self._new_fig()
            if y2 is not None:
                y2a = np.asarray(y2, dtype=float).ravel()[:len(y)]
                n = min(len(x), len(y), len(y2a))
                ax.fill_between(x[:n], y[:n], y2a[:n], alpha=0.3)
            else:
                ax.fill_between(x, baseline, y, alpha=0.3)
            self._apply_x_ticks(ax, cfg)
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
        """
        Plot a 2D heatmap and save as PNG.

        Returns
        -------
        Path
            Absolute path to the saved PNG.
        """
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

        with self._theme_context(cfg):
            fig, ax = self._new_fig()
            extent = None
            if x.size and y.size:
                extent = [float(np.min(x)), float(np.max(x)), float(np.min(y)), float(np.max(y))]
            im = ax.imshow(Z, origin=origin, interpolation=interpolation,
                           vmin=vmin, vmax=vmax, extent=extent, aspect="auto")
            if add_colorbar:
                fig.colorbar(im, ax=ax)
            self._apply_x_ticks(ax, cfg)
            return self._finish(fig, ax, self._resolve_path(filename), cfg)
