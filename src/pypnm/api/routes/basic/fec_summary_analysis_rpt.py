# pypnm/api/routes/basic/reports/FecSummaryAnalysisReport.py
# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia

from __future__ import annotations

import logging
from typing import Any, Dict, List, Mapping, Sequence, Tuple, cast

from pydantic import Field

from pypnm.api.routes.basic.abstract.analysis_report import AnalysisReport, AnalysisRptMatplotConfig
from pypnm.api.routes.basic.abstract.base_models.common_analysis import CommonAnalysis
from pypnm.api.routes.common.classes.analysis.analysis import Analysis
from pypnm.api.routes.common.classes.analysis.model.schema import OfdmFecSummaryAnalysisModel
from pypnm.lib.types import ArrayLike, ChannelId
from pypnm.lib.csv.manager import CSVManager
from pypnm.lib.matplot.manager import MatplotManager, PlotConfig


class FecSummaryAnalysisRptModel(CommonAnalysis):
    """
    CommonAnalysis wrapper for OFDM FEC Summary outputs.

    Attributes
    ----------
    parameters : OfdmFecSummaryAnalysisModel
        Structured FEC summary model produced by the analysis layer.
    """
    parameters: OfdmFecSummaryAnalysisModel = Field(
        ..., description="Structured OFDM FEC summary model (per-channel, per-profile codeword time series).",
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

    def __init__(
        self,
        analysis: Analysis,
        analysis_matplot_config: AnalysisRptMatplotConfig = AnalysisRptMatplotConfig(),
        **kwargs: Any,
    ):
        """Initialize report generator and internal result registry."""
        super().__init__(analysis, analysis_matplot_config)
        self.logger = logging.getLogger(f"{self.__class__.__name__}")
        self._results: Dict[int, FecSummaryAnalysisRptModel] = {}

    # ───────────────────────── internal helpers ─────────────────────────

    @staticmethod
    def _as_seq(x: Any) -> List[Any]:
        """Convert input to list; None→[], tuples/arrays→list, scalars→[x]."""
        if x is None:
            return []
        if isinstance(x, (list, tuple)):
            return list(x)
        try:
            return list(x)
        except Exception:
            return [x]

    @staticmethod
    def _get(obj: Any, *names: str) -> Any:
        """Get attribute or mapping key by trying a list of candidate names."""
        for n in names:
            if hasattr(obj, n):
                return getattr(obj, n)
            if isinstance(obj, Mapping) and n in obj:
                return obj[n]
        return None

    def _resolve_profile(self, profile_entry: Any) -> str:
        """Return profile id as string from various schema field names."""
        p = self._get(profile_entry, "profile", "profile_id", "id")
        try:
            return str(int(p))
        except Exception:
            return str(p) if p is not None else "unknown"

    def _resolve_codewords(
        self, profile_entry: Any
    ) -> Tuple[List[Any], List[int], List[int], List[int], Dict[str, int]]:
        """
        Resolve (timestamps, total, corrected, uncorrected) arrays from schema variants.

        Returns
        -------
        Tuple[List[Any], List[int], List[int], List[int], Dict[str,int]]
            Timestamps, totals, corrected, uncorrected, and a small shape dict for logging.
        """
        cw = self._get(profile_entry, "codewords", "codeword_entries", "entries", "codeword")
        shape: Dict[str, int] = {}
        candidates = [cw, self._get(cw, "values"), self._get(cw, "data")]

        ts = tc = cc = uc = []
        for node in candidates:
            if node is None:
                continue
            ts = self._as_seq(self._get(node, "timestamps", "timestamp"))
            tc = self._as_seq(self._get(node, "total_codewords", "total", "totals"))
            cc = self._as_seq(self._get(node, "corrected"))
            uc = self._as_seq(self._get(node, "uncorrected"))
            if any((ts, tc, cc, uc)):
                break

        try: tc = [int(v) for v in tc]
        except Exception: pass
        try: cc = [int(v) for v in cc]
        except Exception: pass
        try: uc = [int(v) for v in uc]
        except Exception: pass

        shape["ts"] = len(ts)
        shape["tc"] = len(tc)
        shape["cc"] = len(cc)
        shape["uc"] = len(uc)
        return ts, tc, cc, uc, shape

    def _log_preview(self, ch: ChannelId, profile: str, ts: Sequence[Any], tc: Sequence[int], cc: Sequence[int], uc: Sequence[int]) -> None:
        """Log a short preview of the first few points for debugging."""
        def head(seq: Sequence[Any], k: int = 5) -> List[Any]:
            return list(seq[:k])
        self.logger.debug(
            "Preview ch=%s prof=%s ts[:5]=%s total[:5]=%s corr[:5]=%s unc[:5]=%s",
            int(ch), profile, head(ts), head(tc), head(cc), head(uc),
        )

    # ───────────────────────── outputs ─────────────────────────

    def create_csv(self, **kwargs: Any) -> List[CSVManager]:
        """
        Produce CSV files with per-timestamp codeword counters for each channel/profile.

        Returns
        -------
        List[CSVManager]
            Managers pointing at the generated CSV files.
        """
        mgr_out: List[CSVManager] = []
        for common_model in self.get_common_analysis_model():
            c_model = cast(FecSummaryAnalysisRptModel, common_model)
            channel_id: int = int(c_model.channel_id)
            analysis_model = c_model.parameters
            profiles = getattr(analysis_model, "profiles", []) or []

            for profile_entry in profiles:
                profile = self._resolve_profile(profile_entry)
                ts, tc, cc, uc, shape = self._resolve_codewords(profile_entry)
                n = min(len(ts), len(tc), len(cc), len(uc))
                self.logger.debug("CSV series lengths ch=%s prof=%s shape=%s n=%d", channel_id, profile, shape, n)
                if n == 0:
                    self.logger.warning("No data for Channel %s, Profile %s (timestamps/counters empty).", channel_id, profile)
                    continue

                try:
                    csv_mgr: CSVManager = self.csv_manager_factory()
                    csv_mgr.set_header(["ChannelID", "Profile", "Timestamp", "TotalCodewords", "Corrected", "Uncorrected"])
                    csv_fname = self.create_csv_fname(tags=[str(channel_id), profile, self.FNAME_TAG])
                    csv_mgr.set_path_fname(csv_fname)
                    for i in range(n):
                        csv_mgr.insert_row([channel_id, profile, ts[i], tc[i], cc[i], uc[i]])
                    self._log_preview(channel_id, profile, ts, tc, cc, uc)
                    self.logger.debug("CSV created ch=%s prof=%s -> %s (rows=%d)", channel_id, profile, csv_fname, csv_mgr.get_row_count())
                    mgr_out.append(csv_mgr)
                except Exception as exc:
                    self.logger.exception("Failed to create CSV for channel %s (profile %s): %s", channel_id, profile, exc)
        return mgr_out

    def create_matplot(self, **kwargs: Any) -> List[MatplotManager]:
        """
        Produce PNG plots (Total/Corrected/Uncorrected) for each channel/profile.

        Notes
        -----
        - X axis ticks are hidden.
        - A single human-readable time range ("start → end") is used as the xlabel.

        Returns
        -------
        List[MatplotManager]
            Managers used to generate and reference plot outputs.
        """
        mgr_out: List[MatplotManager] = []
        for common_model in self.get_common_analysis_model():
            c_model = cast(FecSummaryAnalysisRptModel, common_model)
            ch_id: ChannelId = ChannelId(c_model.channel_id)
            analysis_model = c_model.parameters
            profiles = getattr(analysis_model, "profiles", []) or []

            for profile_entry in profiles:
                profile = self._resolve_profile(profile_entry)
                ts, tc, cc, uc, shape = self._resolve_codewords(profile_entry)
                n = min(len(ts), len(tc), len(cc), len(uc))
                self.logger.debug("Plot series lengths ch=%s prof=%s shape=%s n=%d", int(ch_id), profile, shape, n)
                if n == 0:
                    self.logger.warning("No data for Channel %s, Profile %s (timestamps/counters empty).", int(ch_id), profile)
                    continue

                try:
                    cfg = PlotConfig(
                        title               = f"FEC Summary - OFDM Channel {int(ch_id)} (Profile {profile})",
                        x                   = cast(ArrayLike, ts[:n]),
                        ylabel              = "Codeword Count",
                        y_multi             = [cast(ArrayLike, tc[:n]), cast(ArrayLike, cc[:n]), cast(ArrayLike, uc[:n])],
                        y_multi_label       = ["Total", "Corrected", "Uncorrected"],
                        grid                = True,
                        legend              = True,
                        transparent         = False,
                        theme               = self.getAnalysisRptMatplotConfig().theme,
                        line_colors         = ["tab:blue", "tab:green", "tab:red"],
                        
                        # ── X-axis time range label & tick suppression ──
                        x_ticks_visible = False,                 # hide all x ticks/labels
                        x_time_labels   = "from_to",             # render "start → end" as xlabel
                        x_time_input_unit = "s",                 # timestamps are epoch seconds
                        x_time_format   = "%Y-%m-%d %H:%M",      # adjust as needed
                        xlabel_prefix   = "Time Range: ",        # optional prefix before start→end
                    )

                    mgr = MatplotManager(default_cfg=cfg)
                    png_path = self.create_png_fname(tags=[str(int(ch_id)), profile, self.FNAME_TAG])
                    self._log_preview(ch_id, profile, ts, tc, cc, uc)
                    self.logger.debug("Creating MatPlot: %s ch=%s prof=%s", png_path, int(ch_id), profile)
                    mgr.plot_multi_line(filename=png_path)
                    mgr_out.append(mgr)
                except Exception as exc:
                    self.logger.exception("Failed to create plot for channel %s (profile %s): %s", int(ch_id), profile, exc)
        return mgr_out

    def _process(self) -> None:
        """
        Register CommonAnalysis wrappers for each OfdmFecSummaryAnalysisModel.

        Expected
        --------
        The analysis model list is `List[OfdmFecSummaryAnalysisModel]`.
        """
        models: List[OfdmFecSummaryAnalysisModel] = cast(List[OfdmFecSummaryAnalysisModel], self.get_analysis_model())
        for model in models:
            channel_id: int = int(model.channel_id)
            a_model = FecSummaryAnalysisRptModel(channel_id=channel_id, parameters=model)
            self.register_common_analysis_model(channel_id, a_model)
