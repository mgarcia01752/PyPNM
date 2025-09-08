# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia

from __future__ import annotations

import logging
from typing import Any, Dict, List, Sequence, cast

from pydantic import Field

from pypnm.api.routes.basic.abstract.analysis_report import AnalysisReport
from pypnm.api.routes.basic.abstract.base_models.common_analysis import CommonAnalysis
from pypnm.api.routes.common.classes.analysis.analysis import Analysis
from pypnm.api.routes.common.classes.analysis.model.schema import OfdmFecSummaryAnalysisModel
from pypnm.lib.types import ArrayLike
from pypnm.lib.csv.manager import CSVManager
from pypnm.lib.matplot.manager import MatplotManager, PlotConfig


class FecSummaryAnalysisRptModel(CommonAnalysis):
    """
    CommonAnalysis wrapper for OFDM FEC Summary outputs.

    Attributes
    ----------
    parameters:
        Structured FEC summary model produced by the analysis layer.
    """
    parameters: OfdmFecSummaryAnalysisModel = Field(
        ...,
        description="Structured OFDM FEC summary model (per-channel, per-profile codeword time series).",
    )


class FecSummaryAnalysisReport(AnalysisReport):
    """
    Report generator for OFDM FEC Summary analysis.

    Responsibilities
    ----------------
    - Emit one CSV per channel/profile with time-series codeword counters.
    - Emit one PNG per channel/profile with Total/Corrected/Uncorrected curves.
    """
    FNAME_TAG: str = "FecSummary"

    def __init__(self, analysis: Analysis):
        super().__init__(analysis)
        self.logger = logging.getLogger("FecSummaryAnalysisReport")
        self._results: Dict[int, FecSummaryAnalysisRptModel] = {}

    def create_csv(self, **kwargs: Any) -> List[CSVManager]:
        """
        Create CSV files containing per-timestamp codeword counters.

        Returns
        -------
        List[CSVManager]
            Managers for each produced CSV file (one or more per channel/profile).
        """
        mgr_out: List[CSVManager] = []

        for common_model in self.get_common_analysis_model():
            c_model = cast(FecSummaryAnalysisRptModel, common_model)
            channel_id: int = int(c_model.channel_id)

            analysis_model = c_model.parameters
            profiles = analysis_model.profiles

            for profile_entry in profiles:
                profile = str(profile_entry.profile)
                codewords = profile_entry.codewords

                try:
                    csv_mgr: CSVManager = self.csv_manager_factory()
                    csv_mgr.set_header(
                        ["ChannelID", "Profile", "Timestamp", "TotalCodewords", "Corrected", "Uncorrected"]
                    )
                    csv_fname = self.create_csv_fname(tags=[str(channel_id), profile, self.FNAME_TAG])
                    csv_mgr.set_path_fname(csv_fname)

                    timestamps: Sequence[Any] = cast(Sequence[Any], codewords.timestamps)
                    total_codewords: Sequence[int] = cast(Sequence[int], codewords.total_codewords)
                    corrected: Sequence[int] = cast(Sequence[int], codewords.corrected)
                    uncorrected: Sequence[int] = cast(Sequence[int], codewords.uncorrected)

                    # Basic length guard to avoid IndexError and keep CSV rows aligned.
                    n = min(len(timestamps), len(total_codewords), len(corrected), len(uncorrected))
                    if n == 0:
                        self.logger.warning(
                            "No data for Channel %s, Profile %s (timestamps/counters empty).", channel_id, profile
                        )
                        continue

                    for idx in range(n):
                        ts = timestamps[idx]
                        tc = total_codewords[idx]
                        cc = corrected[idx]
                        uc = uncorrected[idx]
                        csv_mgr.insert_row([channel_id, profile, ts, tc, cc, uc])

                    self.logger.debug(
                        "CSV created for Channel %s, Profile %s -> %s (rows=%d)",
                        channel_id, profile, csv_fname, csv_mgr.get_row_count()
                    )
                    mgr_out.append(csv_mgr)

                except Exception as exc:
                    # Keep going on other profiles/channels if one fails.
                    self.logger.exception("Failed to create CSV for channel %s (profile %s): %s",
                                          channel_id, profile, exc)

        return mgr_out

    def create_matplot(self, **kwargs: Any) -> List[MatplotManager]:
        """
        Create PNG line plots (multi-series) for Total/Corrected/Uncorrected codewords.

        Returns
        -------
        List[MatplotManager]
            Managers for each produced plot (one or more per channel/profile).
        """
        mgr_out: List[MatplotManager] = []

        for common_model in self.get_common_analysis_model():
            c_model = cast(FecSummaryAnalysisRptModel, common_model)
            channel_id: int = int(c_model.channel_id)

            analysis_model = c_model.parameters
            profiles = analysis_model.profiles

            for profile_entry in profiles:
                profile = str(profile_entry.profile)
                codewords = profile_entry.codewords

                timestamps      = cast(ArrayLike, codewords.timestamps)
                total_codewords = cast(ArrayLike, codewords.total_codewords)
                corrected       = cast(ArrayLike, codewords.corrected)
                uncorrected     = cast(ArrayLike, codewords.uncorrected)

                try:
                    cfg = PlotConfig(
                        title=f"FEC Summary - OFDM Channel {channel_id} (Profile {profile})",
                        x=timestamps,   xlabel="Timestamp",
                        y_multi         = [total_codewords, corrected, uncorrected],
                        y_multi_label   = ["Total Codewords", "Corrected", "Uncorrected"],
                        grid=True, legend=True, transparent=False,
                    )

                    mgr = MatplotManager(default_cfg=cfg)

                    png_path = self.create_png_fname(tags=[str(channel_id), profile, self.FNAME_TAG])
                    self.logger.debug(f"Creating MatPlot: {png_path} for channel: {channel_id}, profile: {profile}")
                    mgr.plot_multi_line(filename=png_path)
                    mgr_out.append(mgr)

                except Exception as exc:
                    self.logger.exception(
                        "Failed to create plot for channel %s (profile %s): %s",
                        channel_id, profile, exc)


        return mgr_out

    def _process(self) -> None:
        """
        Build FecSummaryAnalysis wrappers for each OfdmFecSummaryAnalysisModel.

        Expected per-item shape: OfdmFecSummaryAnalysisModel (case-sensitive fields as defined in schema).
        """
        models: List[OfdmFecSummaryAnalysisModel] = cast(
            List[OfdmFecSummaryAnalysisModel],
            self.get_analysis_model(),
        )

        for model in models:
            channel_id: int = int(model.channel_id)
            a_model = FecSummaryAnalysisRptModel(
                channel_id=channel_id,
                parameters=model,
            )
            self.register_common_analysis_model(channel_id, a_model)
