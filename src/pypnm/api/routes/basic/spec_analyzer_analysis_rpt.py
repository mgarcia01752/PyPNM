# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia

from __future__ import annotations

import logging
from typing import Any, Dict, List, cast
from pydantic import BaseModel, ConfigDict, Field

from pypnm.api.routes.basic.abstract.analysis_report import AnalysisReport
from pypnm.api.routes.basic.abstract.base_models.common_analysis import CommonAnalysis
from pypnm.api.routes.common.classes.analysis.analysis import Analysis
from pypnm.api.routes.common.classes.analysis.model.spectrum_analyzer_schema import SpectrumAnalyzerAnalysisModel
from pypnm.lib.csv.manager import CSVManager
from pypnm.lib.log_files import LogFile
from pypnm.lib.matplot.manager import MatplotManager, PlotConfig
from pypnm.lib.types import FloatSeries, IntSeries
from pypnm.lib.utils import Utils

class SpecAnaWindowAvgRptModel(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="ignore")
    window_size:int                 = Field(..., description="")
    windows_average:FloatSeries     = Field(..., description="")
    length:int                      = Field(..., description="")

class SpectrumAnalyzerSignalProcessRptModel(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="ignore")
    frequency:IntSeries                 = Field(..., description="")
    amplitude:FloatSeries               = Field(..., description="")
    anti_log:FloatSeries                = Field(..., description="")
    window:SpecAnaWindowAvgRptModel     = Field(..., description="")

class SpectrumAnalyzerAnalysisRptModel(CommonAnalysis):
    signal: SpectrumAnalyzerSignalProcessRptModel = Field(..., description="")


class SpectrumAnalyzerReport(AnalysisReport):
    FNAME_TAG: str = "SpectrumAnalyzer"

    def __init__(self, analysis: Analysis):
        super().__init__(analysis)
        self.logger = logging.getLogger("SpectrumAnalyzerReport")
        self._results: Dict[int, SpectrumAnalyzerAnalysisRptModel] = {}

    def create_csv(self, **kwargs: Any) -> List[CSVManager]:
        """Emit one CSV per channel with per-bin histogram rows."""
        csv_mgr_list: List[CSVManager] = []

        for common_model in self.get_common_analysis_model():
            model                   = cast(SpectrumAnalyzerAnalysisRptModel, common_model)
            channel_id: int         = model.channel_id


            try:
                csv_mgr: CSVManager = self.csv_manager_factory()
                csv_mgr.set_header(["ChannelID", "BinIndex", "HitCount", "Symmetry", "DwellCount"])
                csv_fname = self.create_csv_fname(tags=[str(channel_id), self.FNAME_TAG])
                csv_mgr.set_path_fname(csv_fname)

                self.logger.info(f"CSV created for channel {channel_id}: {csv_fname} (rows={csv_mgr.get_row_count()})")
                csv_mgr_list.append(csv_mgr)

            except Exception as exc:
                self.logger.exception(f"Failed to create CSV for channel {channel_id}: {exc}", exc_info=True)

        return csv_mgr_list

    def create_matplot(self, **kwargs: Any) -> List[MatplotManager]:
        """
        Render a per-channel histogram view from **pre-binned counts** using `MatplotManager.plot_histogram`.

        Keyword args (optional):
            normalized (bool): If True, use probability density (fractions) instead of raw counts. Default False.
            cumulative (bool): If True, draw the cumulative histogram. Default False.
            orientation (str): "vertical" (default) or "horizontal".
            histtype (str): One of {"bar", "step", "stepfilled", "barstacked"}. Default "bar".
            align (str): "mid" | "left" | "right". Default "mid".
            bins (int | Sequence[number]): Optional override for bin edges/count. By default uses unit-width bins per entry in `hit_counts`.
            label (str | None): Optional legend label.
        """
        out: List[MatplotManager] = []

        for common_model in self.get_common_analysis_model():
            model = cast(SpectrumAnalyzerAnalysisRptModel, common_model)


            # Title/labels
            title = "Spectrum Analyzer"
            xlabel = "Bin Index"
            ylabel = "Hit Count"

            png = self.create_png_fname(tags=png_tags)
            self.logger.info(f"Creating Spectrum plot: {png}")

            cfg = PlotConfig(title=title, 
                             x=bin_indices,     xlabel=xlabel, 
                             y=hit_counts,      ylabel=ylabel, 
                             grid=True, legend=(label is not None), transparent=False)
            
            mgr = MatplotManager(default_cfg=cfg)

            out.append(mgr)

        return out

    def _process(self) -> None:
        """
        Expected per-item shape (keys are case-sensitive):

            {
                "status": "SUCCESS",
                "pnm_header": {
                    "file_type": "PNN",
                    "file_type_version": 9,
                    "major_version": 1,
                    "minor_version": 0,
                    "capture_time": 1756915479
                },
                "channel_id": 0,
                "mac_address": "38:ad:2b:3e:87:7c",
                "first_segment_center_frequency": 300000000,
                "last_segment_center_frequency": 900000000,
                "segment_frequency_span": 1000000,
                "num_bins_per_segment": 256,
                "equivalent_noise_bandwidth": 150.0,
                "window_function": 1,
                "bin_frequency_spacing": 3906,
                "spectrum_analysis_data_length": 307712,
                "spectrum_analysis_data" "hex",
                "amplitude_bin_segments_float": [ [.float.], [.float.]]
        """
        models:List[SpectrumAnalyzerAnalysisModel] = cast(List[SpectrumAnalyzerAnalysisModel], self.get_analysis_model())

        for idx, model in enumerate(models):
            f = f'{self.FNAME_TAG}.{Utils.time_stamp()}.json'
            LogFile().write(fname=f, data=model.model_dump_json())
