# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia

from __future__ import annotations

import logging
import math
import re
from typing import Any, Dict, List, Mapping, Tuple, cast

from pydantic import BaseModel, ConfigDict, Field

from pypnm.api.routes.basic.abstract.analysis_report import AnalysisReport
from pypnm.api.routes.basic.abstract.base_models.common_analysis import CommonAnalysis
from pypnm.api.routes.basic.common.signal_capture_agg import SignalCaptureAggregator
from pypnm.api.routes.common.classes.analysis.analysis import Analysis
from pypnm.lib.csv.manager import CSVManager
from pypnm.lib.matplot.manager import MatplotManager, PlotConfig
from pypnm.lib.numeric_scaler import NumericScaler
from pypnm.lib.signal.linear_regression import LinearRegression1D
from pypnm.lib.signal.shan.series import Shannon
from pypnm.lib.types import IntSeries

class RxMerAnalysisParameters(BaseModel):
    """
    Parameters that augment RxMER analysis output.

    - shannon_limit_db: Per-subcarrier Shannon/SNR limit (dB), len == len(raw_x)
    - regression_line : Per-subcarrier fitted values (ŷ) from linear regression over index domain
    """
    model_config = ConfigDict(populate_by_name=True, extra="ignore")
    shannon_limit_db: List[float]       = Field(..., description="Shannon/SNR limit per subcarrier (dB)")
    regression_line: List[float]        = Field(..., description="Regression fitted values per subcarrier")
    modulation_count: Dict[str, int]    = Field(..., description="Number of supported modulation schemes")
class RxMerAnalysis(CommonAnalysis):
    """
    Analysis view over RxMER data (extends CommonAnalysis).
    """
    parameters: RxMerAnalysisParameters = Field(..., description="RxMER analysis parameters and limits.")

class RxMerAnalysisReport(AnalysisReport):
    """Concrete report builder for RxMER measurements."""

    def __init__(self, analysis: Analysis):
        super().__init__(analysis)
        self.logger = logging.getLogger("RxMerAnalysisReport")
        self._results: Dict[int, RxMerAnalysis] = {}
        self._sig_cap_agg: SignalCaptureAggregator = SignalCaptureAggregator()

    def create_csv(self, **kwargs) -> List[CSVManager]:
        """
        Stream validated models into CSVs. Assumes `_process()` already enforced
        """
        csv_mgr_list: List[CSVManager] = []
        any_models = False

        for common_model in self.get_common_analysis_model():
            any_models = True
            model = cast(RxMerAnalysis, common_model)
            chan = int(model.channel_id)

            x:List[float]   = model.raw_x
            y:List[float]   = model.raw_y
            sh:List[float]  = model.parameters.shannon_limit_db
            rl:List[float]  = model.parameters.regression_line

            """
                Single Channel Capture
            """
            try:

                csv_mgr: CSVManager = self.csv_manager_factory()
                csv_fname = self.create_csv_fname(tags=[str(chan)])
                csv_mgr.set_path_fname(csv_fname)
                
                csv_mgr.set_header(["channel_id", "Frequency(Hz)", "Magnitude(dB)", "shannon Limit(dB)", "Regression Line(dB)"])
                for rx, ry, s, r in zip(x, y, sh, rl):
                    csv_mgr.insert_row([chan, rx, ry, s, r])

                self.logger.info("CSV created for channel %s: %s (rows=%d)", chan, csv_fname, len(x))
                csv_mgr_list.append(csv_mgr)

            except Exception as exc:
                self.logger.exception("Failed to create CSV for channel %s: %s", chan, exc)

            """
                Signal Capture Aggregation - All OFDM DS Channels
            """
            try:

                csv_mgr: CSVManager = self.csv_manager_factory()
                csv_fname = self.create_csv_fname(tags=['signal_aggregate'])
                csv_mgr.set_path_fname(csv_fname)

                csv_mgr.set_header(["Frequency(Hz)", "Magnitude(dB)"])

                x_agg, y_agg = self._sig_cap_agg.get_series()
                for rx, ry in zip(x_agg, y_agg):
                    csv_mgr.insert_row([rx, ry])

                self.logger.info(f"CSV created: {csv_fname} (rows={len(x_agg)})")
                csv_mgr_list.append(csv_mgr)

            except Exception as exc:
                self.logger.exception(f"Failed to create CSV, Reason: {exc}")

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
            model = cast(RxMerAnalysis, common_model)
            chan = int(model.channel_id)
            chan_id_list.append(chan)

            x_hz = model.raw_x
            y_db = model.raw_y
            rl   = model.parameters.regression_line
            mc   = model.parameters.modulation_count 

            x_khz, _ = NumericScaler().to_prefix(values=x_hz, target="k")

            try:

                cfg = PlotConfig(
                    title=f"RxMER OFDM Channel: {chan}",
                    x=x_khz, xlabel="Frequency (kHz)",
                    y_multi=[y_db, rl],
                    y_multi_label=["RxMER", "Regression Line"],
                    grid=True, legend=True, transparent=False,
                )

                mod_count_fname = self.create_png_fname(tags=[f"{chan}"])
                self.logger.info("Creating MatPlot: %s for channel: %s", mod_count_fname, chan)

                mgr = MatplotManager(default_cfg=cfg)
                multi = self.create_png_fname(tags=[str(chan)])
                mgr.plot_multi_line(filename=multi)

                out.append(mgr)

            except Exception as exc:
                self.logger.exception("Failed to create plot for channel %s: %s", chan, exc)

            try:
                bpsym, order_count = self.__modulation_order_count_to_series(mc)
                
                cfg = PlotConfig(
                    title=f"RxMER OFDM Channel: {chan} - Modulation Order Count",
                    x=bpsym,                  xlabel="Bits Per Symbol (bps)",
                    y=order_count,            ylabel="Order Count",
                    grid=True, legend=True, transparent=False,
                )

                mod_count_fname = self.create_png_fname(tags=[str(chan), 'modulation_count'])
                self.logger.info("Creating MatPlot: %s for channel: %s", mod_count_fname, chan)

                mgr = MatplotManager(default_cfg=cfg)
                mgr.plot_line(filename=mod_count_fname)

                out.append(mgr)

            except Exception as exc:
                self.logger.exception("Failed to create plot for channel %s: %s", chan, exc)

            try:
                x, y = self._sig_cap_agg.get_series()
                cfg = PlotConfig(
                    title=f"RxMER OFDM Channels: ({chan_id_list})",
                    x=x,    xlabel="Frequency(Hz)",
                    y=y,    ylabel="Magnitude(dB)",
                    grid=True, legend=True, transparent=False,)

                mod_count_fname = self.create_png_fname(tags=['signal_agg'])
                self.logger.info(f"Creating MatPlot: {mod_count_fname} for aggregated signal capture")

                mgr = MatplotManager(default_cfg=cfg)
                mgr.plot_line(filename=mod_count_fname)

                out.append(mgr)

            except Exception as exc:
                self.logger.exception(f"Failed to create plot")

        if not any_models:
            self.logger.info("No analysis data available; no plots created.")

        return out

    def _process(self) -> None:
        """
        Normalize raw measurement dicts into fully-validated RxMerAnalysis models.

        Required input shape per item:
            {
                "channel_id": int,
                "carrier_values": { "frequency": List[number], "magnitude": List[number] },
                "modulation_statistics": { "snr_db_limit": List[number] 
                    "supported_modulation_counts": {
                        "qam_2": 7600,...
                    }
                }
            }

        Rules enforced here (and only here):
          - Coerce frequency/magnitude/shannon to float lists.
          - All lists must be same non-zero length.
          - All values must be finite.
          - Compute regression fitted values (index domain) to `parameters.regression_line`.
        """
        data_list: List[Dict[str, Any]] = self.get_analysis_data() or []

        for idx, data in enumerate(data_list):

            try:
                # channel id
                channel_id = int(data.get("channel_id", self.INVALID_CHANNEL_ID))

                # extract raw
                cv = data.get("carrier_values") or {}
                ms = data.get("modulation_statistics") or {}
                x_raw = list(cv.get("frequency") or [])
                y_raw = list(cv.get("magnitude") or [])
                sh_raw = list(ms.get("snr_db_limit") or [])
                mod_count:Dict[str,int] = ms.get("supported_modulation_counts") or {}

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
                sh = coerce_finite(sh_raw, "shannon_limit_db")

                # length checks (strict)
                n = len(x)
                if not (n and len(y) == n and len(sh) == n):
                    raise ValueError(
                        f"length mismatch x/y/shannon: {len(x)}/{len(y)}/{len(sh)} (n must be equal & > 0)")

                # compute regression (index domain 0..n-1) => fitted ŷ, len == n
                y_hat = LinearRegression1D(y).fitted_values()

                params = RxMerAnalysisParameters(
                    shannon_limit_db=sh, 
                    regression_line=y_hat,              # type: ignore
                    modulation_count=mod_count) 

                model = RxMerAnalysis(
                    channel_id=channel_id,
                    raw_x=x, raw_y=y,
                    parameters=params,)
                
                # Must register Model
                self.register_common_analysis_model(channel_id, model)

                # Add to Signal Capture Aggregator
                self.logger.debug(f"Adding OFDM RxMER Channel: {channel_id} for aggregated signal capture")
                self._sig_cap_agg.add_series(x_raw, y_raw)

            except Exception as exc:
                self.logger.exception("Failed to process RxMER item %d: %s", idx, exc)

        # Finalize signal capture aggregation
        self._sig_cap_agg.reconstruct()

    def __modulation_order_count_to_series(self, mod_count: Mapping[str, int]) -> Tuple[IntSeries, IntSeries]:
        """
        Convert {"qam_<M>": count} → (bits_per_symbol_series, count_series),
        sorted by ascending QAM order M. Skips malformed entries with warnings.

        Returns
        -------
        (order_bits, order_counts) : Tuple[IntSeries, IntSeries]
            - order_bits[i]   = bits per symbol for QAM-M_i (e.g., log2(M_i))
            - order_counts[i] = count for that modulation
        """
        if not mod_count:
            return [], []

        items = []  # (M, bits_per_symbol, count)

        for key, cnt in mod_count.items():
            # extract numeric order M from key (e.g., "qam_4096", "QAM-64", "qam4096")
            m = None
            if isinstance(key, str):
                m_match = re.search(r"(\d+)", key)
                if m_match:
                    try:
                        m = int(m_match.group(1))
                    except Exception:
                        pass
            if m is None:
                self.logger.warning("Skipping unsupported modulation key: %r", key)
                continue

            # validate count
            try:
                c_int = int(cnt)
            except Exception:
                self.logger.warning("Non-integer count for %s: %r", key, cnt)
                continue
            if c_int < 0:
                self.logger.warning("Negative count for %s (%d); clamping to 0", key, c_int)
                c_int = 0

            # compute bits/symbol via your Shannon helper
            try:
                bps = int(Shannon.bits_from_symbol_count(m))  # ensure int for powers-of-two M
            except Exception as e:
                self.logger.warning("Unable to compute bits/symbol for %s: %s", key, e)
                continue

            items.append((m, bps, c_int))

        if not items:
            return [], []

        # stable, deterministic series
        items.sort(key=lambda t: t[0])  # sort by QAM order M

        order_bits: IntSeries = [bps for _, bps, _ in items]
        order_counts: IntSeries = [c for _, _, c in items]
        
        self.logger.debug(f"Modulation order series: {order_bits}")
        self.logger.debug(f"Modulation order series: {order_counts}")

        return order_bits, order_counts