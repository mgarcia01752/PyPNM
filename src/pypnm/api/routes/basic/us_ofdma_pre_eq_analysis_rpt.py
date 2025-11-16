# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia

from __future__ import annotations

import logging
import math
from typing import Dict, List, cast

from pydantic import BaseModel, ConfigDict, Field

from pypnm.api.routes.basic.abstract.analysis_report import AnalysisReport
from pypnm.api.routes.basic.abstract.base_models.common_analysis import CommonAnalysis
from pypnm.api.routes.basic.common.signal_capture_agg import SignalCaptureAggregator
from pypnm.api.routes.common.classes.analysis.analysis import Analysis
from pypnm.api.routes.common.classes.analysis.model.schema import ComplexDataCarrierModel, UsOfdmaUsPreEqAnalysisModel
from pypnm.lib.csv.manager import CSVManager
from pypnm.lib.matplot.manager import MatplotManager, PlotConfig
from pypnm.lib.signal_processing.linear_regression import LinearRegression1D
from pypnm.lib.types import ArrayLike, ChannelId, ComplexArray, FloatSeries, PathLike


class OfdmaPreEqParameters(BaseModel):
    """
    Parameters that augment OFDMA US Pre-Equalization analysis output.

    - regression_line : Per-subcarrier fitted values (ŷ) from linear regression over index domain
    """
    model_config                   = ConfigDict(populate_by_name=True, extra="ignore")
    regression_line: FloatSeries   = Field(..., description="Regression fitted values per subcarrier.")
    group_delay: FloatSeries       = Field(..., description="Group delay (µs) per subcarrier.")


class OfdmaPreEqAnalysis(CommonAnalysis):
    """
    Analysis view over OFDMA US Pre-Equalization data (extends CommonAnalysis).
    """
    parameters: OfdmaPreEqParameters = Field(..., description="Pre-EQ analysis parameters and derived series.")


class CmUsOfdmaPreEqReport(AnalysisReport):
    """Concrete report builder for OFDMA US Pre-Equalization measurements."""

    FNAME_TAG = "us_preeq"

    def __init__(self, analysis: Analysis):
        super().__init__(analysis)
        self.logger = logging.getLogger("CmUsOfdmaPreEqReport")
        self._results: Dict[int, OfdmaPreEqAnalysis] = {}
        self._sig_cap_agg: SignalCaptureAggregator   = SignalCaptureAggregator()

    def create_csv(self, **kwargs) -> List[CSVManager]:
        """
        Stream validated models into CSVs. Assumes `_process()` already enforced.
        """
        csv_mgr_list: List[CSVManager] = []
        any_models: bool               = False

        for common_model in self.get_common_analysis_model():
            any_models                 = True
            model                      = cast(OfdmaPreEqAnalysis, common_model)
            chan                       = int(model.channel_id)

            x: ArrayLike               = cast(ArrayLike, model.raw_x)
            y: ArrayLike               = cast(ArrayLike, model.raw_y)
            ca: ComplexArray           = model.raw_complex
            rl: FloatSeries            = model.parameters.regression_line

            # Single-channel capture
            try:
                csv_mgr: CSVManager    = self.csv_manager_factory()
                csv_fname: PathLike     = self.create_csv_fname(tags=[str(chan), self.FNAME_TAG])
                csv_mgr.set_path_fname(csv_fname)

                csv_mgr.set_header(["ChannelID", "Frequency(Hz)", "Magnitude(dB)", "Regression(dB)", "Real(Linear)", "Imaginary(Linear)"])
                for rx, ry, reg, cmp in zip(x, y, rl, ca):
                    real, img = cmp
                    csv_mgr.insert_row([chan, rx, ry, reg, real, img])

                self.logger.debug(f"CSV created for OFDMA US Pre-EQ channel {chan}: {csv_fname} (rows={len(x)})")
                csv_mgr_list.append(csv_mgr)

            except Exception as exc:
                self.logger.exception(f"Failed to create CSV for OFDMA US Pre-EQ channel {chan}: {exc}")

        if not any_models:
            self.logger.debug("No OFDMA US Pre-EQ analysis data available; no CSVs created.")

        return csv_mgr_list

    def create_matplot(self, **kwargs) -> List[MatplotManager]:
        """
        Generate per-channel plots from validated OFDMA US Pre-EQ models.
        """
        matplot_mgr: List[MatplotManager] = []
        any_models: bool                  = False
        chan_id_list: FloatSeries           = []

        for common_model in self.get_common_analysis_model():
            any_models                    = True
            model                         = cast(OfdmaPreEqAnalysis, common_model)
            channel_id:ChannelId          = model.channel_id
            chan_id_list.append(channel_id)

            x_hz: ArrayLike         = cast(ArrayLike, model.raw_x)
            y_db: ArrayLike         = cast(ArrayLike, model.raw_y)
            cplex: ComplexArray     = cast(ComplexArray, model.raw_complex)
            rl: ArrayLike           = cast(ArrayLike, model.parameters.regression_line)
            gd_us: ArrayLike        = cast(ArrayLike, model.parameters.group_delay)

            prefix_title = f"OFDMA US Pre-Equalization · Channel {channel_id}"

            # OFDMA US Pre-EQ magnitude with regression
            try:
                cfg = PlotConfig(
                    title           = f"{prefix_title} · Magnitude with Regression Line",
                    x               = x_hz,
                    x_tick_mode     = "unit",
                    x_unit_from     = "hz",
                    x_unit_out      = "mhz",
                    x_tick_decimals = 0,
                    xlabel_base     = "Frequency",
                    y_multi         = [y_db, rl],
                    y_multi_label   = ["Channel Estimation", "Regression Line"],
                    ylabel          = "dB",
                    grid            = True,
                    legend          = True,
                    transparent     = False,
                    theme           = self.getAnalysisRptMatplotConfig().theme,
                )

                multi = self.create_png_fname(tags=[str(channel_id), self.FNAME_TAG, "magnitude"])
                self.logger.debug("Creating OFDMA US Pre-EQ magnitude plot: %s for channel: %s", multi, channel_id)

                mgr = MatplotManager(default_cfg=cfg)
                mgr.plot_multi_line(filename=multi)
                matplot_mgr.append(mgr)

            except Exception as exc:
                self.logger.exception("Failed to create OFDMA US Pre-EQ magnitude plot for channel %s: %s", channel_id, exc)

            # OFDMA US Pre-EQ Group Delay
            try:
                cfg = PlotConfig(
                    title           = f"{prefix_title} · Group Delay",
                    x               = x_hz,
                    x_tick_mode     = "unit",
                    x_unit_from     = "hz",
                    x_unit_out      = "mhz",
                    xlabel_base     = "Frequency",
                    y               = gd_us,
                    ylabel          = "uS",
                    grid            = True,
                    legend          = False,
                    transparent     = False,
                    theme           = self.getAnalysisRptMatplotConfig().theme,
                )

                multi = self.create_png_fname(tags=[str(channel_id), self.FNAME_TAG, "groupdelay"])
                self.logger.debug("Creating OFDMA US Pre-EQ group-delay plot: %s for channel: %s", multi, channel_id)

                mgr                       = MatplotManager(default_cfg=cfg)
                mgr.plot_line(filename=multi)
                matplot_mgr.append(mgr)

            except Exception as exc:
                self.logger.exception("Failed to create OFDMA US Pre-EQ group-delay plot for channel %s: %s", channel_id, exc)

            # OFDMA US IQ scatter
            try:
                # Complex Scatter Plot
                reals: ArrayLike = [c[0] for c in cplex]
                imags: ArrayLike = [c[1] for c in cplex]
                cfg = PlotConfig(
                    title           = f"{prefix_title} · IQ Complex Scatter Plot",
                    x               = reals,
                    y               = imags,
                    xlabel          = "In-Phase",
                    ylabel          = "Quadrature",
                    grid            = False,
                    legend          = False,
                    transparent     = False,
                    theme           = self.getAnalysisRptMatplotConfig().theme,
                )

                scatter = self.create_png_fname(tags=[str(channel_id), self.FNAME_TAG, "scatter"])
                self.logger.debug("Creating OFDMA US Pre-EQ scatter plot: %s for channel: %s", scatter, channel_id)

                mgr = MatplotManager(default_cfg=cfg)
                mgr.plot_scatter(filename=scatter)
                matplot_mgr.append(mgr)

            except Exception as exc:
                self.logger.exception("Failed to create OFDMA US Pre-EQ group-delay plot for channel %s: %s", channel_id, exc)

        if not any_models:
            self.logger.warning("No OFDMA US Pre-EQ analysis data available; no plots created.")

        return matplot_mgr

    def _process(self) -> None:
        """
        Normalize validated `UsOfdmaUsPreEqAnalysisModel` items into `OfdmaPreEqAnalysis`
        and register them for reporting/plotting.

        This method expects `self.get_analysis_model()` to return a list of
        `UsOfdmaUsPreEqAnalysisModel` instances (already validated upstream).
        """
        models: List[UsOfdmaUsPreEqAnalysisModel] = cast(List[UsOfdmaUsPreEqAnalysisModel], self.get_analysis_model())

        for idx, model in enumerate(models):
            try:
                channel_id: ChannelId              = model.channel_id

                # Carrier values block
                cv: ComplexDataCarrierModel        = model.carrier_values
                x_raw: FloatSeries                 = list(cv.frequency)
                y_raw: FloatSeries                 = list(cv.magnitudes)
                cplex: ComplexArray                = list(cv.complex)
                group_delay: FloatSeries           = list(cv.group_delay.magnitude)

                # Coerce -> float and ensure finiteness
                def coerce_finite(seq, name: str) -> List[float]:
                    out: List[float] = []
                    for v in seq:
                        fv = float(v)
                        if not math.isfinite(fv):
                            raise ValueError(f"non-finite {name} value: {v!r}")
                        out.append(fv)
                    return out

                x: FloatSeries      = coerce_finite(x_raw, "raw_x")
                y: FloatSeries      = coerce_finite(y_raw, "raw_y")
                y_hat: FloatSeries  = cast(FloatSeries, LinearRegression1D(cast(ArrayLike, y)).fitted_values())

                params = OfdmaPreEqParameters(
                    regression_line = y_hat,
                    group_delay     = group_delay,
                )

                analysis_model = OfdmaPreEqAnalysis(
                    channel_id  = channel_id,
                    raw_x       = x,
                    raw_y       = y,
                    raw_complex = cplex,
                    parameters  = params,
                )

                # Register model for downstream CSV/plot generation
                self.register_common_analysis_model(channel_id, analysis_model)

                # Add to Signal Capture Aggregator
                self.logger.debug(f"Adding OFDMA US Pre-EQ series, ChannelID: {channel_id} for aggregated signal capture")
                self._sig_cap_agg.add_series(x, y)

            except Exception as exc:
                self.logger.exception(f"Failed to process OFDMA US Pre-EQ item {idx}: Reason: {exc}")

        # Finalize signal capture aggregation
        self._sig_cap_agg.reconstruct()
