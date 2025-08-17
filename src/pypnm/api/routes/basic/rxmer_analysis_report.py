# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia

from __future__ import annotations

import logging
from typing import Any, Dict, List, cast

from pydantic import BaseModel, ConfigDict, Field

from pypnm.api.routes.basic.abstract.analysis_report import AnalysisReport
from pypnm.api.routes.basic.abstract.base_models.common_analysis import CommonAnalysis
from pypnm.api.routes.common.classes.analysis.analysis import Analysis
from pypnm.lib.csv.csv_manager import CSVManager
from pypnm.lib.signal.linear_regression import LinearRegression1D

class RxMerAnalysisParameters(BaseModel):
    """
    Parameters that augment RxMER analysis output.

    Fields:
      - shannon_limit_db: Optional per-subcarrier Shannon/SNR limit (dB).
      - regression_basis : Whether linear regression uses raw_x (frequency) or index 0..N-1.
    """
    model_config = ConfigDict(populate_by_name=True, extra="ignore")
    shannon_limit_db: List[float] = Field(default_factory=list, description="Shannon/SNR limit per subcarrier (dB)")
    regression_basis: List[float] = Field(..., description="")

class RxMerAnalysis(CommonAnalysis):
    """
    Analysis view over RxMER data (extends CommonAnalysis).

    Adds:
      - parameters: RxMerAnalysisParameters (shannon bounds + regression basis)
      - linear_regression (computed): [slope, intercept, r2]
    """
    parameters: RxMerAnalysisParameters = Field(...,description="RxMER analysis parameters and limits.")

class RxMerAnalysisReport(AnalysisReport):
    """
    Concrete report builder for RxMER measurements.

    """

    INVALID_CHANNEL_ID:int = -1

    def __init__(self, analysis: Analysis):
        super().__init__(analysis)
        self.logger = logging.getLogger("RxMerAnalysisReport")

        self._results: Dict[int, RxMerAnalysis] = {}
        self._process()

    def create_csv(self, **kwargs) -> List[CSVManager]:
        """
        Create and write per-channel RxMER CSVs.

        Returns:
            List[CSVManager]: CSV managers for channels that were successfully written.
        """
        csv_mgr_list: List[CSVManager] = []

        for common_analysis_model in self.get_common_analysis_model():
            model = cast(RxMerAnalysis, common_analysis_model)

            # Basic presence checks
            params = getattr(model, "parameters", None)
            if params is None:
                self.logger.error(f"Missing parameters for channel {model.channel_id}")
                continue

            raw_x = getattr(model, "raw_x", [0])
            raw_y = getattr(model, "raw_y", [0])
            shannon = getattr(params, "shannon_limit_db", [0])
            basis = getattr(params, "regression_basis", [0])

            missing = [name for name, val in [
                ("raw_x", raw_x), ("raw_y", raw_y),
                ("parameters.shannon_limit_db", shannon),
                ("parameters.regression_basis", basis)
            ] if val is None]

            if missing:
                self.logger.error(f"Required data missing for channel {model.channel_id}: {', '.join(missing)}")
                continue

            # Length validation
            if not (len(raw_x) == len(raw_y) == len(shannon)):
                self.logger.warning(
                    "Length mismatch for channel %s: raw_x=%d raw_y=%d shannon=%d basis=%d",
                    model.channel_id, len(raw_x), len(raw_y), len(shannon), len(basis))
                continue

            # Prepare CSV
            csv_mgr: CSVManager = self.get_csv_manager()
            csv_mgr.set_header(["channel_id", "raw_x", "raw_y", "shannon_limit_db"])

            # Populate rows
            for rx, ry, s in zip(raw_x, raw_y, shannon):
                csv_mgr.insert_row([model.channel_id, rx, ry, s])

            # Write file
            csv_fname = self.create_csv_fname(tags=[f"{model.channel_id}"])
            csv_mgr.set_path_fname(csv_fname)

            self.logger.info(f"CSV file created: {csv_fname}")
            csv_mgr_list.append(csv_mgr)

        return csv_mgr_list


    def create_png_plot(self, **kwargs) -> None:
        """
        Stub for PNG plot creation (left to concrete plotting lib).
        Intended to iterate self.results and generate figures.
        """
        # Example idea (pseudo):
        # for r in self.results:
        #     fig = plot_rxmer(r.raw_x, r.raw_y, r.linear_regression, ...)
        #     save_fig(fig, path)
        pass

    def _process(self) -> None:
        """
        Normalize raw measurement dicts into validated RxMerAnalysis models.

        Expects each item like:
            {
              "channel_id": int,
              "carrier_values": {
                "frequency": List[int|float],
                "magnitude": List[int|float]
              },
              "modulation_statistics": {
                "snr_db_limit": List[float]
              }
            }
        """
        data_list: List[Dict[str, Any]] = self.get_analysis_data() or []

        for idx, data in enumerate(data_list):
            try:
                # Defensive extraction with clear fallbacks
                channel_id: int = int(data.get("channel_id", self.INVALID_CHANNEL_ID))
                cv: Dict[str, Any] = data.get("carrier_values") or {}
                ms: Dict[str, Any] = data.get("modulation_statistics") or {}

                raw_x: List[float] = list(cv.get("frequency") or [])
                raw_y: List[float] = list(cv.get("magnitude") or [])
                shannon_limit_db: List[float] = list(ms.get("snr_db_limit") or [])

                # Parameters: default to regression vs index (0..N-1).
                params = RxMerAnalysisParameters(
                    shannon_limit_db=shannon_limit_db,
                    regression_basis=LinearRegression1D(raw_y).to_list())

                # Build validated model (CommonAnalysis ensures x/y length & finiteness)
                model = RxMerAnalysis(channel_id=channel_id, 
                                      raw_x=raw_x, raw_y=raw_y,
                                      parameters=params,)
                
                self.add_common_analysis_model(channel_id, model)


            except Exception as exc:
                self.logger.exception(f"Failed to process RxMER item {idx}: reason: {exc}")
                continue
