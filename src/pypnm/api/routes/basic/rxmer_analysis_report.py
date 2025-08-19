# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia

from __future__ import annotations

import logging
import math
from typing import Any, Dict, List, cast

from pydantic import BaseModel, ConfigDict, Field

from pypnm.api.routes.basic.abstract.analysis_report import AnalysisReport
from pypnm.api.routes.basic.abstract.base_models.common_analysis import CommonAnalysis
from pypnm.api.routes.common.classes.analysis.analysis import Analysis
from pypnm.lib.csv.manager import CSVManager
from pypnm.lib.matplot.manager import MatplotManager, PlotConfig
from pypnm.lib.numeric_scaler import NumericScaler
from pypnm.lib.signal.linear_regression import LinearRegression1D


class RxMerAnalysisParameters(BaseModel):
    """
    Parameters that augment RxMER analysis output.

    - shannon_limit_db: Per-subcarrier Shannon/SNR limit (dB), len == len(raw_x)
    - regression_line : Per-subcarrier fitted values (ŷ) from linear regression over index domain
    """
    model_config = ConfigDict(populate_by_name=True, extra="ignore")
    shannon_limit_db: List[float] = Field(default_factory=list, description="Shannon/SNR limit per subcarrier (dB)")
    regression_line: List[float]   = Field(default_factory=list, description="Regression fitted values per subcarrier")


class RxMerAnalysis(CommonAnalysis):
    """
    Analysis view over RxMER data (extends CommonAnalysis).
    """
    parameters: RxMerAnalysisParameters = Field(..., description="RxMER analysis parameters and limits.")


class RxMerAnalysisReport(AnalysisReport):
    """Concrete report builder for RxMER measurements."""

    INVALID_CHANNEL_ID: int = -1

    def __init__(self, analysis: Analysis):
        super().__init__(analysis)
        self.logger = logging.getLogger("RxMerAnalysisReport")
        self._results: Dict[int, RxMerAnalysis] = {}

    # ────────────────────────────────────────────────────────────────────────────
    # Public API
    # ────────────────────────────────────────────────────────────────────────────
    def create_csv(self, **kwargs) -> List[CSVManager]:
        """
        Stream validated models into CSVs. Assumes `_process()` already enforced
        float coercion & equal-length series.
        """
        csv_mgr_list: List[CSVManager] = []
        any_models = False

        for common_model in self.get_common_analysis_model():
            any_models = True
            model = cast(RxMerAnalysis, common_model)
            chan = int(model.channel_id)

            try:
                x = model.raw_x
                y = model.raw_y
                sh = model.parameters.shannon_limit_db
                rl = model.parameters.regression_line

                csv_mgr: CSVManager = self.get_csv_manager()
                csv_mgr.set_header(["channel_id", "raw_x", "raw_y", "shannon_limit_db", "regression_line"])

                for rx, ry, s, r in zip(x, y, sh, rl):
                    csv_mgr.insert_row([chan, rx, ry, s, r])

                csv_fname = self.create_csv_fname(tags=[str(chan)])
                csv_mgr.set_path_fname(csv_fname)
                self.logger.info("CSV created for channel %s: %s (rows=%d)", chan, csv_fname, len(x))
                csv_mgr_list.append(csv_mgr)

            except Exception as exc:
                self.logger.exception("Failed to create CSV for channel %s: %s", chan, exc)

        if not any_models:
            self.logger.info("No analysis data available; no CSVs created.")
        return csv_mgr_list

    def create_matplot(self, **kwargs) -> List[MatplotManager]:
        """
        Generate per-channel line and multi-line plots from validated models.
        """
        out: List[MatplotManager] = []
        any_models = False

        for common_model in self.get_common_analysis_model():
            any_models = True
            model = cast(RxMerAnalysis, common_model)
            chan = int(model.channel_id)

            try:
                x_hz = model.raw_x
                y_db = model.raw_y
                rl   = model.parameters.regression_line

                # Scale x to kHz for readability
                x_khz, _ = NumericScaler().to_prefix(values=x_hz, target="k")

                cfg = PlotConfig(
                    title=f"RxMER OFDM Channel: {chan}",
                    x=x_khz, xlabel="Frequency (kHz)",
                    y=y_db,  ylabel="Magnitude (dB)",
                    y_multi=[y_db, rl],
                    y_multi_label=["RxMER", "Regression Line"],
                    grid=True, legend=True, transparent=False,
                )

                base = self.create_png_fname(tags=[f"{chan}"])
                self.logger.info("Creating MatPlot: %s for channel: %s", base, chan)

                mgr = MatplotManager(default_cfg=cfg)
                mgr.plot_line(filename=base)

                multi = self.create_png_fname(tags=[f"{chan}_regression"])
                mgr.plot_multi_line(filename=multi)

                out.append(mgr)

            except Exception as exc:
                self.logger.exception("Failed to create plot for channel %s: %s", chan, exc)

        if not any_models:
            self.logger.info("No analysis data available; no plots created.")
        return out

    # ────────────────────────────────────────────────────────────────────────────
    # Data grooming + validation (single place)
    # ────────────────────────────────────────────────────────────────────────────
    def _process(self) -> None:
        """
        Normalize raw measurement dicts into fully-validated RxMerAnalysis models.

        Required input shape per item:
            {
              "channel_id": int,
              "carrier_values": { "frequency": List[number], "magnitude": List[number] },
              "modulation_statistics": { "snr_db_limit": List[number] }
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
                lr = LinearRegression1D(y)
                y_hat:List[float] = lr.fitted_values()  # aligned to y length

                params = RxMerAnalysisParameters(
                    shannon_limit_db=sh,
                    regression_line=y_hat,
                )

                model = RxMerAnalysis(
                    channel_id=channel_id,
                    raw_x=x, raw_y=y,
                    parameters=params,)
                
                # Only validated models make it past this point
                self.add_common_analysis_model(channel_id, model)

            except Exception as exc:
                self.logger.exception("Failed to process RxMER item %d: %s", idx, exc)
                # continue to next item
