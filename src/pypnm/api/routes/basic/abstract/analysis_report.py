# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia

from __future__ import annotations

import logging

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List, Union, cast
from pydantic import BaseModel, Field
from pypnm.api.routes.basic.abstract.base_models.common_analysis import CommonAnalysis
from pypnm.api.routes.common.classes.analysis.analysis import Analysis
from pypnm.api.routes.common.classes.analysis.model.schema import BaseAnalysisModel
from pypnm.api.routes.docs.pnm.files.service import MacAddress
from pypnm.config.system_config_settings import SystemConfigSettings
from pypnm.docsis.cm_snmp_operation import SystemDescriptor
from pypnm.lib.archive.manager import ArchiveManager
from pypnm.lib.constants import INVALID_CHANNEL_ID
from pypnm.lib.csv.manager import CSVManager
from pypnm.lib.matplot.manager import MatplotManager, ThemeType
from pypnm.lib.types import PathArray, PathLike
from pypnm.lib.utils import Utils

AnalysisData    = List[Dict[str, Any]]

class AnalysisOutputModel(BaseModel):
    """
    Structured output describing the artifacts produced by a report run.

    Use this as the return payload from `AnalysisReport.to_model()` after
    `build_report()` has generated the CSVs, plots, and archive.

    Typical flow:
        report = MyReport(analysis)
        report.build_report()
        payload = report.to_model()
    """
    time: int               = Field(..., description="Ephoc Time")
    csv_files: PathArray    = Field(..., description="List of CSV file(s)")
    plot_files: PathArray   = Field(..., description="List of PNG Matplot file(s)")
    archive_file: PathLike  = Field(..., description="File name of archive file containging analysis files")


class AnalysisRptMatplotConfig(BaseModel):
    """
    Configuration parameters for Matplotlib figures in an AnalysisReport.

    Extend this model in subclasses to add specific plot configuration options.
    """
    theme: ThemeType = Field(default="dark", description="")

class AnalysisReport(ABC):
    '''
    Abstract base class for converting an `Analysis` into persisted artifacts
    (CSV files, plots, and a ZIP archive), plus a lightweight model for API use.

    Usage pattern:
        - Subclass and implement `_process()`, `create_csv()`, and `create_matplot()`.
        - Construct with an `Analysis` instance.
        - Call `build_report()` to emit files, then `to_model()` for response data.
    '''
    def __init__(self, analysis: Analysis, armc: AnalysisRptMatplotConfig = AnalysisRptMatplotConfig()):
        """Set up logging, store the `Analysis`, and initialize runtime context."""
        self.logger = logging.getLogger("AnalysisReport")
        self._analysis = analysis
        self._armc = armc
        self.__init()
        
        self.csv_files: List[PathLike]  = []
        self.plot_files: List[PathLike] = []

    def getAnalysisRptMatplotConfig(self) -> AnalysisRptMatplotConfig:
        return self._armc

    def get_analysis_data(self) -> AnalysisData:
        """Return the raw per-item analysis data extracted from the `Analysis` results."""
        return self._data_list

    def get_analysis_model(self) -> Union[BaseAnalysisModel, List[BaseAnalysisModel]]:
        """Return the parsed analysis model(s) produced by the upstream pipeline."""
        return self._analysis.get_model()

    def get_mac_address(self) -> MacAddress:    
        """Return the cable-modem MAC address associated with this report session."""
        return self._mac_address

    def get_system_description(self) -> SystemDescriptor:
        """Return the device SystemDescriptor used for filenames and labeling."""
        return self._system_description

    def get_group_time(self) -> int:
        """Return the session/group timestamp used to namespace output filenames."""
        return self._group_time
    
    def to_model(self) -> AnalysisOutputModel:
        """
        Produce a serializable model of the generated artifacts (time, CSVs, plots, archive).

        Call this after `build_report()` to pass paths and metadata to API callers.
        """
        return AnalysisOutputModel(
            time         =   self._group_time,
            csv_files    =   self.csv_files,
            plot_files   =   self.plot_files,
            archive_file =   self.archive_file,
        )

    def create_csv_fname(self, tags: List[str] = []) -> PathLike:
        '''
        Build a CSV filename of the form:
            <csv_dir>/<mac>_<model>_<timestamp>[_TAGS].csv

        Example:
            fname = self.create_csv_fname(tags=["ch1", "rpt"])
        '''
        return f"{self._csv_dir}/{self.create_generic_fname(tags=tags, ext='csv')}"

    def create_png_fname(self, tags: List[str] = []) -> PathLike:
        '''
        Build a PNG filename of the form:
            <png_dir>/<mac>_<model>_<timestamp>[_TAGS].png

        Example:
            fname = self.create_png_fname(tags=["spectrum"])
        '''        
        return f"{self._png_dir}/{self.create_generic_fname(tags=tags, ext='png')}"

    def create_archive_fname(self, tags: List[str] = []) -> PathLike:
        '''
        Build a ZIP archive filename of the form:
            <archive_dir>/<mac>_<model>_<timestamp>[_TAGS].zip

        Example:
            fname = self.create_archive_fname(tags=["bundle"])
        '''        
        return f"{self._archive_dir}/{self.create_generic_fname(tags=tags, ext='zip')}"

    def create_generic_fname(self, tags: List[str], ext: str = "") -> str:
        """
        Generate a generic filename using the current session metadata plus tags.

        Args:
            tags: Optional descriptors to append (e.g., ["ch1", "rpt"]).
            ext:  Optional file extension (e.g., "csv", ".png").

        Returns:
            The constructed filename (no directories).

        Example:
            name = self.create_generic_fname(tags=["debug"], ext="json")
        """
        return self._generate_fname(tags=tags, ext=ext)

    def csv_manager_factory(self) -> CSVManager:
        """Return a `CSVManager` instance. Subclasses may override to customize behavior."""
        return CSVManager()

    def get_base_filename(self) -> str:
        """
        Return the base filename (no extension) derived from MAC/model/time.

        Useful when emitting multiple related files for the same report run.
        """
        return self._generate_fname()

    def register_common_analysis_model(self, channel_id:int, model: CommonAnalysis) -> None:
        """
        Register (or overwrite) a `CommonAnalysis` model keyed by channel ID.

        Args:
            channel_id: Channel identifier.
            model:      The analysis model to store.

        Example:
            self.register_common_analysis_model(channel_id=1, model=foo)
        """
        if not isinstance(model, CommonAnalysis):
            raise TypeError("model must be an instance of CommonAnalysis")
        
        if channel_id in self._common_analysis_model:
            self.logger.warning(f"Channel ID {channel_id} already exists. Overwriting the existing model.")
            self._common_analysis_model[channel_id] = model
        
        self._common_analysis_model[channel_id] = model
    
    def get_common_analysis_model(self, channel_id: int = -1) -> List[CommonAnalysis]:
        """
        Retrieve one or more `CommonAnalysis` models.

        Args:
            channel_id: Specific channel ID, or -1 to return all (default).

        Returns:
            A list of models. When `channel_id == -1`, results are ordered by channel ID.

        Raises:
            KeyError: If a specific `channel_id` is requested but not present.

        Examples:
            all_models = self.get_common_analysis_model()
            one = self.get_common_analysis_model(channel_id=5)
        """
        if channel_id == INVALID_CHANNEL_ID:
            # Return all models sorted by channel_id
            return [self._common_analysis_model[cid] for cid in sorted(self._common_analysis_model)]

        if channel_id not in self._common_analysis_model:
            raise KeyError(f"Channel ID {channel_id} not found in results.")

        return [self._common_analysis_model[channel_id]]

    def get_common_analysis_models_channel_ids(self) -> List[int]:
        """
        Return the list of channel IDs with registered models.

        Example:
            ids = self.get_common_analysis_models_channel_ids()
        """
        return list(self._common_analysis_model.keys())

    def build_report(self) -> Path:
        """
        Run the full report pipeline: `_process()` → CSV generation → plot rendering → ZIP.

        Returns:
            The path to the created ZIP archive.

        Typical use:
            archive = report.build_report()
            return report.to_model()
        """
        self._process()

        f:PathArray = [Path('')]

        for csv_mgr in self.create_csv():
            
            if not csv_mgr.write():
                self.logger.error(f"Failed to write CSV: {csv_mgr.get_path_fname()}")
                continue

            self.logger.debug(f'Wrote CSV File: {csv_mgr.get_path_fname()}')
            self.csv_files.append(csv_mgr.get_path_fname())
            f.append(csv_mgr.get_path_fname())

        for matplot_mgr in self.create_matplot():
            for fn in matplot_mgr.get_png_files():
                self.logger.debug(f'Wrote Matplotlib Figure: {fn}')
                self.plot_files.append(fn)
                f.append(fn)

        try:
            self.archive_file = ArchiveManager().zip_files(files=f, archive_path=self.create_archive_fname())

        except Exception as e:
            self.logger.error(f"Failed to create archive: {e}")

        return self.archive_file

    def get_all_generated_files(self, include_archive:bool=False) -> List[PathLike]:
        """
        Return a flat list of generated file paths (CSVs and plots).

        Note:
            `include_archive` is accepted for API symmetry but ignored; the
            archive path is available via `to_model().archive_file`.
        """
        _:List[PathLike] = []
        _.extend(self.csv_files)
        _.extend(self.plot_files)
        return _

    @abstractmethod
    def _process(self) -> None:
        """
        Populate per-channel report models from analysis results.

        Implement in subclasses:
            - Parse `self.get_analysis_model()` and/or `self.get_analysis_data()`.
            - Build models and register with:
              `self.register_common_analysis_model(channel_id, model)`.
        """
        pass

    @abstractmethod
    def create_csv(self) -> List[CSVManager]:
        """
        Build one or more `CSVManager` instances ready to `write()`.

        Implement in subclasses:
            - Serialize registered models into CSV rows.
            - Return the list of configured `CSVManager` instances.
        """
        pass

    @abstractmethod
    def create_matplot(self) -> List[MatplotManager]:
        """
        Build one or more `MatplotManager` instances to render PNG figures.

        Implement in subclasses:
            - Configure figures from registered models.
            - Return the list of configured `MatplotManager` instances.
        """
        pass

    def __init(self) -> None:
        """Initialize runtime context: data cache, output dirs, timestamps, and descriptors."""
        # Acquire analysis data
        self._data_list: AnalysisData = list(self._analysis.get_results().get("analysis", []))
        self.logger.debug("Analysis items received: %d", len(self._data_list))

        if not self._data_list:
            self.logger.error("Unable to acquire analysis data (empty 'analysis' list).")
            raise ValueError("No analysis data available")

        # Directories / session metadata
        self._png_dir: PathLike       = SystemConfigSettings.png_dir
        self._csv_dir: PathLike       = SystemConfigSettings.csv_dir
        self._archive_dir: PathLike   = SystemConfigSettings.archive_dir

        self._group_time              = Utils.time_stamp()
        self._base_filename: str      = ""
        self._common_analysis_model: Dict[int, BaseModel] = {}

        # Normalize first item to a dict (supports both dict and BaseModel)
        first_item = self._data_list[0]
        if isinstance(first_item, BaseModel):
            first_dict: Dict[str, Any] = first_item.model_dump()
        else:
            first_dict = cast(Dict[str, Any], first_item)

        # MAC addresses (prefer 'mac_address', fall back to 'cm_mac_address')
        mac_str: str = (
            first_dict.get("mac_address")
            or first_dict.get("cm_mac_address")
            or MacAddress.null()
        )
        cmts_mac_str: str  = first_dict.get("cmts_mac_address", MacAddress.null())

        self._mac_address: MacAddress      = MacAddress(mac_str)
        self._cmts_mac_address: MacAddress = MacAddress(cmts_mac_str)

        # System descriptor (robust to missing keys)
        dev_details: Dict[str, Any]                   = cast(Dict[str, Any], first_dict.get("device_details", {}))
        system_description_dict: Dict[str, Any]                = cast(Dict[str, Any], dev_details.get("system_description", {}))
        self._system_description: SystemDescriptor             = SystemDescriptor.load_from_dict(system_description_dict)

    def _generate_fname(self, tags: List[str] = [], ext: str = "") -> str:
        """
        Construct a sanitized filename from:
          - MAC address (colon-free, lowercase)
          - device model (`system_description.model`, spaces → underscores, lowercase)
          - group timestamp
          - optional tag suffix (underscored)
          - optional extension

        Args:
            tags: Descriptive tokens to append (e.g., ["ch1", "rpt"]).
            ext:  Extension with or without leading dot.

        Returns:
            The finalized filename string (no directory).

        Example:
            self._generate_fname(tags=["ch1", "rpt"], ext="csv")
        """
        mac = self.get_mac_address().to_mac_format()
        model = self.get_system_description().model.replace(" ", "_").lower()
        ts = str(self.get_group_time())

        clean_tags = []
        for t in tags:
            t_clean = str(t).strip().replace(" ", "_").lower()
            if t_clean:
                clean_tags.append(t_clean)

        tag_part = f"_{'_'.join(clean_tags)}" if clean_tags else ""
        ext = ext.lstrip(".")
        ext_part = f".{ext}" if ext else ""

        return f"{mac}_{model}_{ts}{tag_part}{ext_part}"
