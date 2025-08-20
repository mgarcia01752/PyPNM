# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia

from __future__ import annotations

import logging
import math
from typing import Any, Dict, List, cast

from pydantic import BaseModel, ConfigDict, Field

from pypnm.api.routes.basic.abstract.analysis_report import AnalysisReport
from pypnm.api.routes.basic.abstract.base_models.common_analysis import CommonAnalysis
from pypnm.api.routes.basic.common.signal_capture_agg import SignalCaptureAggregator
from pypnm.api.routes.common.classes.analysis.analysis import Analysis
from pypnm.lib.csv.manager import CSVManager
from pypnm.lib.matplot.manager import MatplotManager, PlotConfig
from pypnm.lib.numeric_scaler import NumericScaler
from pypnm.lib.signal.linear_regression import LinearRegression1D
from pypnm.lib.types import ArrayLike, ComplexArray


class ChanEstimationParameters(BaseModel):
    """
    Parameters that augment channel estimation analysis output.
    - regression_line : Per-subcarrier fitted values (ŷ) from linear regression over index domain
    """
    model_config                        = ConfigDict(populate_by_name=True, extra="ignore")
    regression_line: List[float]        = Field(..., description="Regression fitted values per subcarrier")
    group_delay:List[float]             = Field(..., description="Group Delay")

class ChanEstimationAnalysis(CommonAnalysis):
    """
    Analysis view over channel estimation data (extends CommonAnalysis).
    """
    parameters: ChanEstimationParameters = Field(..., description="Channel estimation analysis parameters and limits.")

class ChanEstimationReport(AnalysisReport):
    """Concrete report builder for channel estimation measurements."""

    def __init__(self, analysis: Analysis):
        super().__init__(analysis)
        self.logger = logging.getLogger("ChanEstimationReport")
        self._results: Dict[int, ChanEstimationAnalysis] = {}
        self._sig_cap_agg: SignalCaptureAggregator = SignalCaptureAggregator()

    def create_csv(self, **kwargs) -> List[CSVManager]:
        """
        Stream validated models into CSVs. Assumes `_process()` already enforced
        """
        csv_mgr_list: List[CSVManager] = []
        any_models = False

        for common_model in self.get_common_analysis_model():
            any_models = True
            model = cast(ChanEstimationAnalysis, common_model)
            chan = int(model.channel_id)

            x:ArrayLike     = model.raw_x
            y:ArrayLike     = model.raw_y
            ca:ComplexArray = model.raw_complex
            rl:ArrayLike    = model.parameters.regression_line

            """
            Single Channel Capture
            """
            try:

                csv_mgr: CSVManager = self.csv_manager_factory()
                csv_fname = self.create_csv_fname(tags=[str(chan)])
                csv_mgr.set_path_fname(csv_fname)
                
                csv_mgr.set_header(["ChannelID", "Frequency(Hz)", "Magnitude(Linear)", "Regression(Linear)", "Real(Linear)", "Imaginary(Linear)"])
                for rx, ry, reg, cmp in zip(x, y, rl, ca):
                    csv_mgr.insert_row([chan, rx, ry, reg, cmp])

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
        out: List[MatplotManager] = []
        any_models = False
        chan_id_list:List[int] = []

        for common_model in self.get_common_analysis_model():
            any_models = True
            model = cast(ChanEstimationAnalysis, common_model)
            chan = int(model.channel_id)
            chan_id_list.append(chan)

            x_hz:ArrayLike      = model.raw_x
            y_db:ArrayLike      = model.raw_y
            cplex:ComplexArray  = model.raw_complex
            rl:ArrayLike        = model.parameters.regression_line
            
            x_khz, _ = NumericScaler().to_prefix(values=x_hz, target="k")

            '''
            Channel Estimation with Regression Line - All OFDM DS Channels
            '''
            try:

                cfg = PlotConfig(
                    title=f"Channel Estimation OFDM Channel: {chan}",
                    x=x_khz, xlabel="Frequency (kHz)",
                    y_multi=[y_db, rl],
                    y_multi_label=["Channel Estimation", "Regression Line"],
                    grid=True, legend=True, transparent=False,)

                multi = self.create_png_fname(tags=[str(chan), 'chan_est'])
                self.logger.info("Creating MatPlot: %s for channel: %s", multi, chan)

                mgr = MatplotManager(default_cfg=cfg)
                mgr.plot_multi_line(filename=multi)

                out.append(mgr)

            except Exception as exc:
                self.logger.exception("Failed to create plot for channel %s: %s", chan, exc)

        if not any_models:
            self.logger.info("No analysis data available; no plots created.")

        return out

    def _process(self) -> None:
        """
        Normalize raw measurement dicts into fully-validated RxMerAnalysis models.

        Required input shape per item:
        {
            "pnm_header": measurement.get("pnm_header"),
            "mac_address": measurement.get("mac_address"),
            "channel_id": measurement.get("channel_id"),
            "frequency_unit": "Hz",
            "magnitude_unit": "dB",
            "group_delay_unit": "microsecond",
            "complex_unit": "[Real, Imaginary]",
            "carrier_values": {
                "occupied_channel_bandwidth": occupied_channel_bandwidth,
                "carrier_count": len(freqs),
                "frequency": freqs,
                "magnitude": magnitudes_db.tolist(),
                "group_delay": group_delay.tolist(),
                "complex": values,
                "complex_dimension": f"{complex_arr.ndim}"
            },
            "signal_statistics_target": "magnitude",
            "signal_statistics": signal_stats
        }

        """
        data_list: List[Dict[str, Any]] = self.get_analysis_data() or []

        for idx, data in enumerate(data_list):

            try:
                channel_id = int(data.get("channel_id", self.INVALID_CHANNEL_ID))
                cv:Dict             = data.get("carrier_values") or {}
                x_raw:ArrayLike     = list(cv.get("frequency") or [])
                y_raw:ArrayLike     = list(cv.get("magnitude") or [])
                cplex:ComplexArray  = list(cv.get("complex") or [])
                grp_delay:ArrayLike = list(cv.get("group_delay") or [])

                # coerce -> float (and finiteness)
                def coerce_finite(seq, name: str) -> List[float]:
                    out: List[float] = []
                    for v in seq:
                        fv = float(v)
                        if not math.isfinite(fv):
                            raise ValueError(f"non-finite {name} value: {v!r}")
                        out.append(fv)
                    return out

                x = coerce_finite(x_raw, "raw_x")
                y = coerce_finite(y_raw, "raw_y")
                y_hat = cast(List[float], LinearRegression1D(y).fitted_values())

                params = ChanEstimationParameters(
                    regression_line = y_hat,
                    group_delay     = coerce_finite(grp_delay, "group_delay"))       

                model = ChanEstimationAnalysis(
                        channel_id  =   channel_id,
                        raw_x=x,        raw_y=y,
                        raw_complex =   cplex, 
                        parameters  =   params,)

                # Must register Model
                self.register_common_analysis_model(channel_id, model)

                # Add to Signal Capture Aggregator
                self.logger.debug(f"Adding Channel Estimation, ChannelID: {channel_id} for aggregated signal capture")
                self._sig_cap_agg.add_series(x, y)

            except Exception as exc:
                self.logger.exception(f"Failed to process Channel Estimation item {idx}: Reason: {exc}")

        # Finalize signal capture aggregation
        self._sig_cap_agg.reconstruct()

