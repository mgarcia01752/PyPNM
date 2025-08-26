# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia

from __future__ import annotations

import json
import logging
from typing import Any, Dict, List, Literal, Tuple, TypeVar, Iterable, cast

from pydantic import BaseModel, ConfigDict, Field

from pypnm.api.routes.basic.abstract.analysis_report import AnalysisReport
from pypnm.api.routes.basic.abstract.base_models.common_analysis import CommonAnalysis
from pypnm.api.routes.common.classes.analysis.analysis import Analysis
from pypnm.lib.constants import INVALID_CHANNEL_ID, ArrayLike
from pypnm.lib.csv.manager import CSVManager
from pypnm.lib.file_processor import FileProcessor
from pypnm.lib.matplot.manager import MatplotManager, PlotConfig
from pypnm.lib.types import IntSeries


class DsHistrogramParameters(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="ignore")
    symmetry: int           = Field(..., description="Histogram symmetry flag (implementation-defined)")
    dwell_count: int        = Field(..., description="Capture dwell count (implementation-defined)")
    hit_counts: List[int]   = Field(default_factory=list, description="Histogram bin hit counts")


class DsHistrogramAnalysis(CommonAnalysis):
    parameters: DsHistrogramParameters = Field(..., description="Ds Histogram parameters")


class DsHistrogramReport(AnalysisReport):
    FNAME_TAG: str = "DsHistrogram"

    def __init__(self, analysis: Analysis):
        super().__init__(analysis)
        self.logger = logging.getLogger("DsHistrogramReport")
        self._results: Dict[int, DsHistrogramAnalysis] = {}

    def create_csv(self, **kwargs: Any) -> List[CSVManager]:
        """Emit one CSV per channel with per-bin histogram rows."""
        csv_mgr_list: List[CSVManager] = []

        for common_model in self.get_common_analysis_model():
            model                   = cast(DsHistrogramAnalysis, common_model)
            channel_id: int         = int(model.channel_id)
            symmetry: int           = int(model.parameters.symmetry)
            dwell_count: int        = int(model.parameters.dwell_count)
            hit_counts: IntSeries   = model.parameters.hit_counts

            try:
                csv_mgr: CSVManager = self.csv_manager_factory()
                csv_mgr.set_header(["ChannelID", "BinIndex", "HitCount", "Symmetry", "DwellCount"])  # include bin index for clarity
                csv_fname = self.create_csv_fname(tags=[str(channel_id), self.FNAME_TAG])
                csv_mgr.set_path_fname(csv_fname)

                for idx, hit in enumerate(hit_counts):
                    csv_mgr.insert_row([channel_id, idx, int(hit), symmetry, dwell_count])

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

        normalized: bool = bool(kwargs.get("normalized", False))
        cumulative: bool = bool(kwargs.get("cumulative", False))
        orientation: str = str(kwargs.get("orientation", "vertical")).lower()
        histtype: str = str(kwargs.get("histtype", "bar"))
        align: str = str(kwargs.get("align", "mid"))
        label = kwargs.get("label", None)
        bins_override = kwargs.get("bins", None)

        for common_model in self.get_common_analysis_model():
            model = cast(DsHistrogramAnalysis, common_model)
            channel_id: int = int(model.channel_id)
            hit_counts: List[float] = [float(v) for v in (model.parameters.hit_counts or [])]

            if not hit_counts:
                self.logger.info(f"Channel {channel_id} has empty hit_counts; skipping plot.")
                continue

            # Build a histogram from pre-binned counts: one sample per bin index with a weight equal to that bin's count.
            bin_indices: List[float] = [float(i) for i in range(len(hit_counts))]
            default_edges: List[float] = [float(i) for i in range(len(hit_counts) + 1)]  # unit-width bins
            bins_arg = bins_override if bins_override is not None else default_edges

            # Title/labels
            title = f"Downstream Histogram"
            xlabel = "Bin Index"
            ylabel = "Hit Count"

            if normalized and not cumulative:
                ylabel = "Fraction"
            elif not normalized and cumulative:
                ylabel = "Cumulative Count"
            elif normalized and cumulative:
                ylabel = "Cumulative Fraction"

            png_tags = [str(channel_id), self.FNAME_TAG]
            if normalized:
                png_tags.append("norm")
            if cumulative:
                png_tags.append("cum")
            if orientation == "horizontal":
                png_tags.append("h")

            png = self.create_png_fname(tags=png_tags)
            self.logger.info(f"Creating histogram plot: {png} for channel: {channel_id}")

            cfg = PlotConfig(title=title, 
                             x=bin_indices,     xlabel=xlabel, 
                             y=hit_counts,      ylabel=ylabel, 
                             grid=True, legend=(label is not None), transparent=False)
            
            mgr = MatplotManager(default_cfg=cfg)

            mgr.plot_histogram(
                data=bin_indices,
                filename=png,
                bins=bins_arg,
                density=normalized,
                weights=hit_counts,
                orientation=orientation,  # "vertical" or "horizontal"
                cumulative=cumulative,
                histtype=histtype,        # "bar", "step", etc.
                align=align,              # "mid", "left", "right"
                label=label,
                cfg=cfg,
            )

            out.append(mgr)

        return out

    def _process(self) -> None:
        """
        Expected per-item shape (keys are case-sensitive):

        {
            "device_details": {"sys_descr": {}},
            "pnm_header": {},
            "mac_address": "...",
            "channel_id": int,
            "symmetry": int,
            "dwell_count": int,
            "hit_counts": List[int]
        }
        """
        data_list: List[Dict[str, Any]] = self.get_analysis_data() or []

        FileProcessor(f'logs/error.json').write_file(json.dumps(data_list))

        for idx, data in enumerate(data_list):
            try:
                channel_id  = int(data.get("channel_id", INVALID_CHANNEL_ID))
                symmetry    = int(data.get("symmetry", 0))
                dwell_count = int(data.get("dwell_count", 0))
                hit_counts: List[int] = [int(v) for v in (data.get("hit_counts", []) or [])]

                raw_x = list(range(len(hit_counts)))
                raw_y:IntSeries = hit_counts

                model = DsHistrogramAnalysis(
                    channel_id=channel_id, 
                    raw_x=raw_x, raw_y=raw_y, 
                    parameters=DsHistrogramParameters(
                        symmetry    =   symmetry, 
                        dwell_count =   dwell_count, 
                        hit_counts  =   hit_counts
                    )
                )
                self.register_common_analysis_model(channel_id, model)

                

            except Exception as exc:
                self.logger.exception(f"Failed to process DS Histogram item {idx}: {exc}", exc_info=True)

    # ---------- Helpers ----------
    T = TypeVar("T")

    @staticmethod
    def _align_len(seq: Iterable[T] | List[T], n: int, *, fill: T) -> List[T]:
        lst = list(seq) if not isinstance(seq, list) else seq
        if n <= 0:
            return []
        if len(lst) >= n:
            return lst[:n]
        return lst + [fill] * (n - len(lst))
