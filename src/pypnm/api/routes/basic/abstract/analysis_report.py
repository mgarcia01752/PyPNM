from __future__ import annotations

# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia

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
from pypnm.lib.matplot.manager import MatplotManager
from pypnm.lib.types import PathArray, PathLike
from pypnm.lib.utils import Utils

AnalysisData    = List[Dict[str, Any]]

class AnalysisOutputModel(BaseModel):
    """
    Pydantic model for a single report output bundle.

    How to use:
        Return this from `to_model()` to expose file paths and time metadata
        after `build_report()` has generated outputs.
    """
    time: int               = Field(..., description="Ephoc Time")
    csv_files: PathArray    = Field(..., description="List of CSV file(s)")
    plot_files: PathArray   = Field(..., description="List of PNG Matplot file(s)")
    archive_file: PathLike  = Field(..., description="File name of archive file containging analysis files")
    
class AnalysisReport(ABC):
    '''
    Abstract base class for generating analysis reports from an `Analysis`.

    How to use:
        - Subclass and implement `_process()`, `create_csv()`, and `create_matplot()`.
        - Instantiate with an `Analysis` and call `build_report()` to produce files.
    '''
    def __init__(self, analysis: Analysis):
        """Initialize report context and cache analysis reference."""
        self.logger = logging.getLogger("AnalysisReport")
        self._analysis = analysis
        self.__init()
        
        self.csv_files: List[PathLike]  = []
        self.plot_files: List[PathLike] = []

    def get_analysis_data(self) -> AnalysisData:
        """Return the raw per-item analysis data list loaded from the `Analysis` results."""
        return self._data_list

    def get_analysis_model(self) -> Union[BaseAnalysisModel, List[BaseAnalysisModel]]:
        """Return the parsed analysis model(s) produced by the pipeline."""
        return self._analysis.get_model()

    def get_mac_address(self) -> MacAddress:    
        """Return the CM MAC address associated with this report session."""
        return self._mac_address

    def get_sys_descr(self) -> SystemDescriptor:
        """Return the SystemDescriptor used in filenames and labeling."""
        return self._sys_descr

    def get_group_time(self) -> int:
        """Return the group timestamp used to namespace output filenames."""
        return self._group_time
    
    def to_model(self) -> AnalysisOutputModel:
        """
        Convert this instance into its Pydantic BaseModel representation.

        How to use:
            Call after `build_report()` to return paths/time for API responses.
        """
        return AnalysisOutputModel(
            time         =   self._group_time,
            csv_files    =   self.csv_files,
            plot_files   =   self.plot_files,
            archive_file =   self.archive_file,
        )

    def create_csv_fname(self, tags: List[str] = []) -> PathLike:
        '''
        Build a CSV filename:
            <csv_dir>/<mac>_<model>_<timestamp>[_TAGS].csv

        How to use:
            `fname = self.create_csv_fname(tags=["ch1", "rpt"])`
        '''
        return f"{self._csv_dir}/{self.create_generic_fname(tags=tags, ext='csv')}"

    def create_png_fname(self, tags: List[str] = []) -> PathLike:
        '''
        Build a PNG filename:
            <png_dir>/<mac>_<model>_<timestamp>[_TAGS].png

        How to use:
            `fname = self.create_png_fname(tags=["spectrum"])`
        '''        
        return f"{self._png_dir}/{self.create_generic_fname(tags=tags, ext='png')}"

    def create_archive_fname(self, tags: List[str] = []) -> PathLike:
        '''
        Build a ZIP archive filename:
            <archive_dir>/<mac>_<model>_<timestamp>[_TAGS].zip

        How to use:
            `fname = self.create_archive_fname(tags=["bundle"])`
        '''        
        return f"{self._archive_dir}/{self.create_generic_fname(tags=tags, ext='zip')}"

    def create_generic_fname(self, tags: List[str], ext: str = "") -> str:
        """
        Generate a generic filename with the specified tags and extension.
        
        Args:           
            tags (List[str]): List of tags to include in the filename.
            ext (str): File extension to append to the filename.
        
        Returns:
            str: Generated filename.

        How to use:
            `name = self.create_generic_fname(tags=["debug"], ext="json")`
        """
        return self._generate_fname(tags=tags, ext=ext)

    def csv_manager_factory(self) -> CSVManager:
        """Factory for CSVManager; override in subclasses to customize CSV behavior."""
        return CSVManager()

    def get_base_filename(self) -> str:
        """
        Return the base filename (without extension) derived from MAC/model/time.

        How to use:
            Useful when constructing multiple related outputs for the same run.
        """
        return self._generate_fname()

    def register_common_analysis_model(self, channel_id:int, model: CommonAnalysis) -> None:
        """
        Add or overwrite a CommonAnalysis model keyed by channel ID.

        Args:
            channel_id (int): Channel identifier.
            model (CommonAnalysis): Analysis model to register.

        How to use:
            Call inside `_process()` after constructing per-channel report models.
        """
        if not isinstance(model, CommonAnalysis):
            raise TypeError("model must be an instance of CommonAnalysis")
        
        if channel_id in self._common_analysis_model:
            self.logger.warning(f"Channel ID {channel_id} already exists. Overwriting the existing model.")
            self._common_analysis_model[channel_id] = model
        
        self._common_analysis_model[channel_id] = model
    
    def get_common_analysis_model(self, channel_id: int = -1) -> List[CommonAnalysis]:
        """
        Retrieve CommonAnalysis models.

        Args:
            channel_id (int, optional): Specific channel ID; pass -1 for all (default).

        Returns:
            List[CommonAnalysis]: One or more models, ordered by channel ID when `-1`.

        Raises:
            KeyError: If a specific channel_id is requested but absent.

        How to use:
            `all_models = self.get_common_analysis_model()`  
            `one = self.get_common_analysis_model(channel_id=5)`
        """
        if channel_id == INVALID_CHANNEL_ID:
            # Return all models sorted by channel_id
            return [self._common_analysis_model[cid] for cid in sorted(self._common_analysis_model)]

        if channel_id not in self._common_analysis_model:
            raise KeyError(f"Channel ID {channel_id} not found in results.")

        return [self._common_analysis_model[channel_id]]

    def get_common_analysis_models_channel_ids(self) -> List[int]:
        """
        Return a list of channel IDs currently registered.

        How to use:
            `ids = self.get_common_analysis_models_channel_ids()`
        """
        return list(self._common_analysis_model.keys())

    def build_report(self) -> Path:
        """
        Run the full report pipeline: `_process()` → CSV → plots → ZIP.

        Returns:
            Path: The path to the created archive file (ZIP).

        How to use:
            `archive = report.build_report()` then serve/return `archive`.
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

    @abstractmethod
    def _process(self) -> None:
        """
        Populate per-channel report models from raw analysis data.

        How to use (in subclass):
            - Parse `self.get_analysis_model()` / `self.get_analysis_data()`
            - Build and `register_common_analysis_model(channel_id, model)`
        """
        pass

    @abstractmethod
    def create_csv(self, **kwargs) -> List[CSVManager]:
        """
        Create one or more CSVManager instances ready to `write()`.

        How to use (in subclass):
            Build CSV rows from registered models and return the managers.
        """
        pass

    @abstractmethod
    def create_matplot(self, **kwargs) -> List[MatplotManager]:
        """
        Create one or more MatplotManager instances to render PNG plots.

        How to use (in subclass):
            Configure figures from registered models and return the managers.
        """
        pass

    def __init(self) -> None:
        """Initialize runtime context (paths, metadata, first-item descriptors)."""
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
        sys_descr_dict: Dict[str, Any]                = cast(Dict[str, Any], dev_details.get("sys_descr", {}))
        self._sys_descr: SystemDescriptor             = SystemDescriptor.load_from_dict(sys_descr_dict)

    def _generate_fname(self, tags: List[str] = [], ext: str = "") -> str:
        """
        Generate a sanitized filename using:
        - MAC address (no colons, lower-case)
        - sys_descr.model (spaces → underscores, lower-case)
        - group_time (YYYYMMDD_HHMMSS if datetime, else str())
        - optional tags (joined with underscores)
        - optional extension (without duplicate dots)

        Args:
            tags: List of descriptor strings to append.
            ext: File extension (e.g. "csv" or ".png").

        Returns:
            A valid filename string.

        How to use:
            `_generate_fname(tags=["ch1", "rpt"], ext="csv")`
        """
        mac = self.get_mac_address().to_mac_format()
        model = self.get_sys_descr().model.replace(" ", "_").lower()
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
