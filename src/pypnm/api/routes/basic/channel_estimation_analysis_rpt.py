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
from pypnm.api.routes.common.classes.analysis.model.chan_est_schema import ChanEstCarrierModel, DsChannelEstAnalysisModel
from pypnm.lib.csv.manager import CSVManager
from pypnm.lib.matplot.manager import MatplotManager, PlotConfig
from pypnm.lib.numeric_scaler import NumericScaler
from pypnm.lib.signal_processing.linear_regression import LinearRegression1D
from pypnm.lib.types import ArrayLike, ComplexArray, FloatSeries, FloatSeries, PathLike


class ChanEstimationParametersRptModel(BaseModel):
    """
    Parameters that augment channel estimation analysis output.
    - regression_line : Per-subcarrier fitted values (ŷ) from linear regression over index domain
    """
    model_config = ConfigDict(populate_by_name=True, extra="ignore")
    regression_line: FloatSeries = Field(..., description="Regression fitted values per subcarrier")
    group_delay: FloatSeries = Field(..., description="Group Delay")

class ChanEstimationAnalysisRptModel(CommonAnalysis):
    """
    Analysis view over channel estimation data (extends CommonAnalysis).
    """
    parameters: ChanEstimationParametersRptModel = Field(..., description="Channel estimation analysis parameters and limits.")


class ChanEstimationReport(AnalysisReport):
    """Concrete report builder for channel estimation measurements."""

    FNAME_TAG = 'chanest'

    def __init__(self, analysis: Analysis):
        super().__init__(analysis)
        self.logger             = logging.getLogger("ChanEstimationReport")
        self._results           : Dict[int, ChanEstimationAnalysisRptModel] = {}
        self._sig_cap_agg       : SignalCaptureAggregator           = SignalCaptureAggregator()

    def create_csv(self, **kwargs) -> List[CSVManager]:
        """
        Stream validated models into CSVs. Assumes `_process()` already enforced
        """
        csv_mgr_list: List[CSVManager] = []
        any_models:bool = False

        for common_model in self.get_common_analysis_model():
            any_models = True
            model      = cast(ChanEstimationAnalysisRptModel, common_model)
            chan       = int(model.channel_id)

            x: ArrayLike        = model.raw_x
            y: ArrayLike        = model.raw_y
            ca: ComplexArray    = model.raw_complex
            rl: FloatSeries     = model.parameters.regression_line

            # Single Channel Capture
            try:
                csv_mgr: CSVManager    = self.csv_manager_factory()
                csv_fname:PathLike     = self.create_csv_fname(tags=[str(chan), self.FNAME_TAG])
                csv_mgr.set_path_fname(csv_fname)

                csv_mgr.set_header(["ChannelID", "Frequency(Hz)", "Magnitude(Linear)", "Regression(Linear)", "Real(Linear)", "Imaginary(Linear)"])
                for rx, ry, reg, cmp in zip(x, y, rl, ca):
                    real, img = cmp
                    csv_mgr.insert_row([chan, rx, ry, reg, real, img])

                self.logger.info(f"CSV created for channel {chan}: {csv_fname} (rows={len(x)})")
                csv_mgr_list.append(csv_mgr)

            except Exception as exc:
                self.logger.exception(f"Failed to create CSV for channel {chan}: {exc}")

        if not any_models:
            self.logger.info("No analysis data available; no CSVs created.")

        return csv_mgr_list

    def create_matplot(self, **kwargs) -> List[MatplotManager]:
        """
        Generate per-channel line and multi-line plots from validated models.
        """
        matplot_mgr: List[MatplotManager]   = []
        any_models:bool                     = False
        chan_id_list: FloatSeries = []

        for common_model in self.get_common_analysis_model():
            any_models          = True
            model               = cast(ChanEstimationAnalysisRptModel, common_model)
            chan                = int(model.channel_id)
            chan_id_list.append(chan)

            x_hz: ArrayLike     = model.raw_x
            y_ln: ArrayLike     = model.raw_y
            cplex: ComplexArray = model.raw_complex
            rl: FloatSeries     = model.parameters.regression_line
            gd_us: FloatSeries  = model.parameters.group_delay

            x_khz, _ = NumericScaler().to_prefix(values=x_hz, target="k")

            # Channel Estimation with Regression Line - OFDM DS Channel
            try:
                cfg = PlotConfig(
                    title=f"Channel Estimation - OFDM Channel: {chan}",
                    x=x_khz,            xlabel="Frequency (kHz)",
                    y_multi=[y_ln, rl], y_multi_label=["Channel Estimation", "Regression Line"],
                    grid=True, legend=True, transparent=False,
                )

                multi = self.create_png_fname(tags=[str(chan), self.FNAME_TAG])
                self.logger.info("Creating MatPlot: %s for channel: %s", multi, chan)

                mgr = MatplotManager(default_cfg=cfg)
                mgr.plot_multi_line(filename=multi)
                matplot_mgr.append(mgr)

            except Exception as exc:
                self.logger.exception("Failed to create plot for channel %s: %s", chan, exc)

            # Group Delay - OFDM DS Channel
            try:
                cfg = PlotConfig(
                    title=f"Group Delay - OFDM Channel: {chan}",
                    x=x_khz,                xlabel="Frequency (kHz)",
                    y=gd_us,                ylabel="uS",
                    grid=True, legend=True, transparent=False,
                )

                multi = self.create_png_fname(tags=[str(chan), self.FNAME_TAG, 'groupdelay'])
                self.logger.info("Creating Group Delay MatPlot: %s for channel: %s", multi, chan)

                mgr = MatplotManager(default_cfg=cfg)
                mgr.plot_line(filename=multi)
                matplot_mgr.append(mgr)

            except Exception as exc:
                self.logger.exception("Failed to create plot for channel %s: %s", chan, exc)

        if not any_models:
            self.logger.info("No analysis data available; no plots created.")

        return matplot_mgr

    def _process(self) -> None:
        """
        Normalize validated `DsChannelEstAnalysisModel` items into `ChanEstimationAnalysis`
        and register them for reporting/plotting.

        This method expects `self.get_analysis_model()` to return a list of
        `DsChannelEstAnalysisModel` instances (already validated upstream).
        """
        data_list               : List[DsChannelEstAnalysisModel] = cast(List[DsChannelEstAnalysisModel], self.get_analysis_model())

        for idx, data in enumerate(data_list):
            try:
                # Pull strongly-typed fields directly from BaseModel (no dict parsing)
                channel_id: int          = int(data.channel_id)

                # Carrier values block
                cv:ChanEstCarrierModel      = data.carrier_values
                x_raw: FloatSeries          = list(cv.frequency)
                y_raw: FloatSeries          = list(cv.magnitudes)
                cplex: ComplexArray         = list(cv.complex)
                group_delay: FloatSeries    = list(cv.group_delay.magnitude)

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
                y_hat: FloatSeries  = cast(FloatSeries, LinearRegression1D(cast(ArrayLike,y)).fitted_values())

                params = ChanEstimationParametersRptModel(
                    regression_line               = y_hat,
                    group_delay                   = group_delay,
                )

                model = ChanEstimationAnalysisRptModel(
                    channel_id                    = channel_id,
                    raw_x                         = x,
                    raw_y                         = y,
                    raw_complex                   = cplex,
                    parameters                    = params,
                )

                # Register model for downstream CSV/plot generation
                self.register_common_analysis_model(channel_id, model)

                # Add to Signal Capture Aggregator
                self.logger.debug(f"Adding Channel Estimation, ChannelID: {channel_id} for aggregated signal capture")
                self._sig_cap_agg.add_series(x, y)

            except Exception as exc:
                self.logger.exception(f"Failed to process Channel Estimation item {idx}: Reason: {exc}")

        # Finalize signal capture aggregation
        self._sig_cap_agg.reconstruct()
