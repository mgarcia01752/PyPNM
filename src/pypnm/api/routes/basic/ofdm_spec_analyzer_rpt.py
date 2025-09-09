# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia

from __future__ import annotations

import logging
from typing import Any, Dict, List, cast

from pydantic import BaseModel

from pypnm.api.routes.basic.abstract.analysis_report import AnalysisReport
from pypnm.api.routes.basic.spec_analyzer_analysis_rpt import (
    SpecAnaWindowAvgRptModel, SpectrumAnalyzerAnalysisRptModel, SpectrumAnalyzerSignalProcessRptModel)
from pypnm.api.routes.common.classes.analysis.analysis import Analysis
from pypnm.api.routes.common.classes.analysis.model.spectrum_analyzer_schema import (
    BaseAnalysisModel, SpectrumAnalyzerAnalysisModel)
from pypnm.api.routes.common.classes.analysis.multi_analysis import MultiAnalysis
from pypnm.config.pnm_config_manager import SystemConfigSettings
from pypnm.docsis.cable_modem import MacAddress
from pypnm.lib.archive.manager import ArchiveManager
from pypnm.lib.csv.manager import CSVManager
from pypnm.lib.matplot.manager import MatplotManager, PlotConfig
from pypnm.lib.types import ArrayLike, FloatSeries, IntSeries, Path, PathLike
from pypnm.lib.utils import Utils


class OfdmSpecAnalysisRptModel(BaseModel):
    """Pydantic model for a compiled SC-QAM Spectrum Analyzer report.
    """
    models:List[BaseAnalysisModel]


class OfdmSpecAnalyzerAnalysisReport():
    """Coordinator that compiles per-channel Spectrum Analyzer artifacts into a single deliverable.

    The class iterates over a :class:`MultiAnalysis` container, invokes
    :class:`SingleOfdmSpecAnalyzerReport` for each constituent
    :class:`Analysis`, collects all generated files (CSV/plots), and can bundle
    them into a zip archive.

    Parameters
    ----------
    multi_analysis : MultiAnalysis
        A container of individual Spectrum Analyzer analyses to be reported.

    Examples
    --------
    >>> rpt = OfdmSpecAnalyzerReport(multi_analysis)
    >>> rpt.build_report()
    >>> archive_path = rpt._build_archive()
    >>> rpt_dict = rpt.to_dict()
    """

    def __init__(self, multi_analysis:MultiAnalysis):
        """Initialize the report coordinator.

        Parameters
        ----------
        multi_analysis : MultiAnalysis
            Source of per-channel :class:`Analysis` objects to process.
        """
        self._multi_analysis = multi_analysis
        self._archive_path:PathLike = SystemConfigSettings.archive_dir
        self._analysis_files:List[PathLike] = []
        self._archive_file:PathLike

    def build_report(self) -> PathLike:
        """
        Generate and collect all per-channel analysis artifacts into a final archive.

        This method iterates over each :class:`Analysis` object within a 
        :class:`MultiAnalysis` instance, generating CSVs and plots using 
        :class:`SingleOfdmSpecAnalyzerReport`. It then aggregates all 
        generated files and produces a single ZIP archive.

        Returns:
            PathLike: The path to the created archive file.

        Workflow:
            1. For each `Analysis`, create and execute a 
            `SingleOfdmSpecAnalyzerReport`.
            2. Collect all generated files using 
            :meth:`SingleOfdmSpecAnalyzerReport.get_all_generated_files`.
            3. Combine them into a single archive using :meth:`_build_archive`.

        Notes:
            - The internal list of report files is updated via `_analysis_files`.
            - Only the archive file path is returned; individual CSVs and plots
            remain accessible through their respective report instances.
        """
        for a in self._get_analyses():
            rpt = SingleOfdmSpecAnalyzerReport(a)
            rpt.build_report()
            rpt.get_all_generated_files()
            self._analysis_files.extend(rpt.get_all_generated_files())

        return self._build_archive()

    def _get_analyses(self) -> List[Analysis]:
        """Return the list of analyses sourced from the bound :class:`MultiAnalysis`."""
        return self._multi_analysis.get_analyses()

    def _report_files(self) -> List[PathLike]:
        """Return the list of file paths collected during :meth:`build_report`."""
        return self._analysis_files

    def _build_archive(self) -> PathLike:
        """Create a zip archive containing all collected report files.

        Returns
        -------
        PathLike
            Absolute or relative filesystem path to the generated archive.

        Notes
        -----
        The archive location defaults to :data:`SystemConfigSettings.archive_dir`
        and is cached internally for retrieval via :meth:`get_archive`.
        """
        self._archive_file = ArchiveManager().zip_files(files=self._report_files(), 
                                                        archive_path=self._create_archive_fname())
        return self._archive_file

    def _create_archive_fname(self) -> PathLike:
        """Create a unique archive name based on the current timestamp.

        Returns
        -------
        PathLike
            The generated archive name.
        """
        mac = self.get_mac_address().to_mac_format()

        return Path(self._archive_path) / f"scqam_report_{mac}_{Utils.time_stamp()}.zip"

    def get_mac_address(self) -> MacAddress:
        """Return the MAC address associated with the report.

        Notes
        -----
        Assumes all analyses in the bound :class:`MultiAnalysis` share the same MAC.
        """
        analyses = self._get_analyses()
        if not analyses:
            raise ValueError("No analyses available to extract MAC address.")
        
        first_analysis = analyses[0]

        return MacAddress(cast(BaseAnalysisModel,first_analysis.get_model()[0].mac_address))
        
    def get_archive(self) -> PathLike:
        """Return the path to the previously created archive.

        Notes
        -----
        Call :meth:`_build_archive` before invoking this method.
        """
        return self._archive_file
    
    def to_model(self) -> OfdmSpecAnalysisRptModel:
        """Return a structured model of the aggregated report output.

        Notes
        -----
        The model schema is minimal today and will evolve as fields stabilize.
        """
        return OfdmSpecAnalysisRptModel(
            models=self._multi_analysis.to_model())
    
    def to_dict(self) -> Dict[str,Any]:
        """Return the report as a serializable ``dict`` via Pydantic's ``model_dump``."""
        return self._multi_analysis.to_dict()


class SingleOfdmSpecAnalyzerReport(AnalysisReport):
    """Emitter for CSV and plots from a single SC-QAM Spectrum Analyzer analysis.

    This concrete :class:`AnalysisReport`:
      * builds a CSV (Frequency, Magnitude dBmV, Moving Average),
      * generates two line plots per channel (raw spectrum, windowed average),
      * materializes a :class:`SpectrumAnalyzerAnalysisRptModel` for downstream use.

    Attributes
    ----------
    FNAME_TAG : str
        Base tag used in output filenames to consistently label Spectrum Analyzer artifacts.
    """
    FNAME_TAG: str = "SpectrumAnalyzerReport"

    def __init__(self, analysis: Analysis):
        """Create a report instance bound to a single :class:`Analysis`.

        Parameters
        ----------
        analysis : Analysis
            The source analysis whose models/results will be rendered to artifacts.
        """
        super().__init__(analysis)
        self.logger = logging.getLogger("SpectrumAnalyzerReport")
        self._results: Dict[int, SpectrumAnalyzerAnalysisRptModel] = {}

    def create_csv(self, **kwargs: Any) -> List[CSVManager]:
        """Emit a CSV per channel with ``Frequency``, ``Magnitude(dBmV)``, and ``MovingAverage``.

        Returns
        -------
        List[CSVManager]
            One manager per generated CSV (already populated and path-bound).

        Notes
        -----
        - Rows are aligned by index across frequency, amplitude, and moving-average series.
        - Filenames include the channel id and :data:`FNAME_TAG`.
        - Exceptions are logged; partial outputs may still be returned.
        """
        csv_mgr_list: List[CSVManager] = []

        for common_model in self.get_common_analysis_model():
            model = cast(SpectrumAnalyzerAnalysisRptModel, common_model)
            channel_id: int = model.channel_id
            sig = model.signal

            try:
                csv_mgr: CSVManager = self.csv_manager_factory()
                csv_mgr.set_header(["Frequency", "Magnitude(dBmV)", "MovingAverage"])

                # Rows aligned by index
                for f_hz, mag_dbmv, ma in zip(sig.frequency, sig.amplitude, sig.window.windows_average):
                    csv_mgr.insert_row ([f_hz, mag_dbmv, ma])

                csv_fname = self.create_csv_fname(tags=[str(channel_id), self.FNAME_TAG])
                csv_mgr.set_path_fname(csv_fname)

                self.logger.debug(
                    "CSV created for channel %s: %s (rows=%s)",
                    channel_id, csv_fname, csv_mgr.get_row_count()
                )
                csv_mgr_list.append(csv_mgr)

            except Exception as exc:
                self.logger.exception(
                    "Failed to create CSV for channel %s: %s",
                    channel_id, exc, exc_info=True
                )

        return csv_mgr_list

    def create_matplot(self, **kwargs: Any) -> List[MatplotManager]:
        """Create two line plots per channel: raw spectrum and windowed average.

        Returns
        -------
        List[MatplotManager]
            One manager per produced figure, in creation order.

        Notes
        -----
        Each figure is saved to disk using a filename built from the channel id
        and :data:`FNAME_TAG`. Plot configuration includes titles, axis labels,
        and optional grid; legends are disabled.
        """
        out: List[MatplotManager] = []

        for common_model in self.get_common_analysis_model():
            m = cast(SpectrumAnalyzerAnalysisRptModel, common_model)
            ch = m.channel_id
            sig = m.signal

            # --- Raw spectrum ---
            try:
                fname = self.create_png_fname(tags=[str(ch), self.FNAME_TAG, "raw"])
                self.logger.debug("Creating Spectrum plot: %s", fname)

                cfg = PlotConfig(
                    title   =   "Spectrum Analyzer",
                    x = cast(ArrayLike, sig.frequency),  xlabel = "Frequency (Hz)",
                    y = cast(ArrayLike, sig.amplitude),  ylabel = "Magnitude (dBmV)",
                    grid    =   True, legend=False, transparent=False,)
                
                mgr = MatplotManager(default_cfg=cfg)
                mgr.plot_line(filename=fname)
                out.append(mgr)

            except Exception as exc:
                self.logger.exception("Failed to create plot for channel %s (raw): %s", ch, exc, exc_info=True)

            # --- Moving average only ---
            try:
                fname = self.create_png_fname(tags=[str(ch), self.FNAME_TAG, "moving_average"])
                self.logger.debug("Creating Spectrum plot: %s", fname)

                cfg = PlotConfig(
                    title   =   f"Spectrum Analyzer - Window Average n={sig.window.window_size}",
                    x = cast(ArrayLike, sig.frequency),  xlabel = "Frequency (Hz)",
                    y = cast(ArrayLike, sig.window.windows_average),  ylabel = "Magnitude (dBmV)",
                    grid    =   True, legend=False, transparent=False,)
                
                mgr = MatplotManager(default_cfg=cfg)
                mgr.plot_line(filename=fname)
                out.append(mgr)

            except Exception as exc:
                self.logger.exception("Failed to create plot for channel %s (moving avg): %s", ch, exc, exc_info=True)

        return out

    def _process(self) -> None:
        """Convert :class:`SpectrumAnalyzerAnalysisModel` → :class:`SpectrumAnalyzerAnalysisRptModel` per channel.

        Notes
        -----
        - Casts/normalizes series types (Hz, dBmV, moving average).
        - Computes an anti-log (linear-ratio) view of amplitudes for convenience.
        - Registers each channel’s report model for subsequent CSV/plot generation.
        """
        models: List[SpectrumAnalyzerAnalysisModel] = cast(List[SpectrumAnalyzerAnalysisModel], self.get_analysis_model())

        for idx, _model in enumerate(models):
            # Optional: debug dump
            # LogFile().write(fname=f"{self.FNAME_TAG}.{Utils.time_stamp()}.json", data=amodel.model_dump_json())

            sig_analysis = _model.signal_analysis
            freq_hz: IntSeries      = [int(f) for f in sig_analysis.frequencies]
            mag_dbmv: FloatSeries   = list(sig_analysis.magnitudes)
            ma_vals: FloatSeries    = list(sig_analysis.window_average.magnitudes)

            # Anti-log in linear ratio (suitable for amplitude-like values)
            anti_log: FloatSeries = [10.0 ** (v / 20.0) for v in mag_dbmv]

            window = SpecAnaWindowAvgRptModel(
                window_size     =   sig_analysis.window_average.points,
                windows_average =   ma_vals,
                length          =   len(ma_vals),
            )

            signal = SpectrumAnalyzerSignalProcessRptModel(
                frequency   =   freq_hz,
                amplitude   =   mag_dbmv,
                anti_log    =   anti_log,
                window      =   window,
            )

            rpt = SpectrumAnalyzerAnalysisRptModel(
                channel_id      =   _model.channel_id,
                signal          =   signal,
            )

            self.register_common_analysis_model(_model.channel_id, rpt)
