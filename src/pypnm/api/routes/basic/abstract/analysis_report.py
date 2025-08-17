# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia

from abc import ABC, abstractmethod
import logging
from pathlib import Path
from typing import Any, Dict, List, Union
from pydantic import BaseModel, Field

import pandas as pd
import matplotlib.pyplot as plt
import zipfile

from pypnm.api.routes.basic.abstract.base_models.common_analysis import CommonAnalysis
from pypnm.api.routes.common.classes.analysis.analysis import Analysis
from pypnm.api.routes.docs.pnm.files.service import MacAddress
from pypnm.config.system_config_settings import SystemConfigSettings

from pypnm.docsis.cm_snmp_operation import SystemDescriptor
from pypnm.lib.csv.csv_manager import CSVManager
from pypnm.lib.utils import Utils

class AnalysisOutputModel(BaseModel):
    """
    Pydantic model for SingleChannelAnalysisOutput data.
    """
    time: str = Field(..., description="Time")
    csv_file: List[str] = Field(..., description="List of CSV file(s)")
    plot_file: List[str] = Field(..., description="List of PNG plot file(s)")
    archive_file: str = Field(..., description="File name of archive file containging analysis files")
    
class AnalysisReport(ABC):
    """
    """
    def __init__(self, analysis: Analysis):
        self.logger = logging.getLogger("AnalysisReport")
        self._analysis = analysis
        self.__init()
        
        # Dict[Filename, Data]
        self.csv_files: Dict[str, Union[str, CSVManager]] = {}
        self.plot_files: Dict[str, Union[str, bytes]] = {}

    def get_analysis_data(self) -> List[Dict[str, Any]]:
        return self._data_list

    def get_mac_address(self) -> MacAddress:    
        return self._mac_address

    def get_sys_descr(self) -> SystemDescriptor:
        return self._sys_descr

    def get_group_time(self) -> int:
        return self._group_time
    
    def compress_output(self, zip_path: Union[str, Path]) -> None:
        """
        Compress the CSV and plot PNG into a ZIP archive.

        Args:
            zip_path (Union[str, Path]): Destination path for the ZIP file.
        """
        zip_path = Path(zip_path)
        zip_path.parent.mkdir(parents=True, exist_ok=True)

        with zipfile.ZipFile(zip_path, mode='w', compression=zipfile.ZIP_DEFLATED) as archive:
            if self.csv_file and self.csv_file.exists():
                archive.write(self.csv_file, arcname=self.csv_file.name)
            if self.plot_file and self.plot_file.exists():
                archive.write(self.plot_file, arcname=self.plot_file.name)

        self.archive_file = zip_path

    def to_model(self) -> AnalysisOutputModel:
        """
        Convert this instance into its Pydantic BaseModel representation.
        """
        return AnalysisOutputModel(
            time=self._group_time,
            csv_file=self.csv_file,
            plot_file=self.plot_file,
            archive_file=self.archive_file,
        )

    def create_csv_fname(self, tags: List[str]) -> str:
        '''
        <csv_dir_path>/<mac_address>_<sys_descr.model>_<YYYYMMDD_HHMMSS>_<TAGS>.csv
        '''
        return f"{self._csv_dir}/{self.create_generic_fname(tags=tags, ext='csv')}"

    def create_png_fname(self, tags: List[str]) -> str:
        '''
        <png_dir_path>/<mac_address>_<sys_descr.model>_<YYYYMMDD_HHMMSS>_<TAGS>.png
        '''        
        return f"{self._png_dir}/{self.create_generic_fname(tags=tags, ext='png')}"

    def create_generic_fname(self, tags: List[str], ext: str = "") -> str:
        """
        Generate a generic filename with the specified tags and extension.
        
        Args:
            tags (List[str]): List of tags to include in the filename.
            ext (str): File extension to append to the filename.
        
        Returns:
            str: Generated filename.
        """
        return self._generate_fname(tags=tags, ext=ext)

    def get_csv_manager(self) -> CSVManager:
        return CSVManager()

    def get_base_filename(self) -> str:
        """
        Returns the base filename for the analysis report.
        """
        return self._generate_fname()

    def add_common_analysis_model(self, channel_id:int, model: CommonAnalysis) -> None:
        """
        Add a common analysis model to the report.

        Args:
            channel_id (int): The channel ID for the model.
            model (CommonAnalysis): The analysis model to add.
        """
        if not isinstance(model, CommonAnalysis):
            raise TypeError("model must be an instance of CommonAnalysis")
        
        if channel_id in self._common_analysis_model:
            raise ValueError(f"Channel ID {channel_id} already exists in results.")
        
        self._common_analysis_model[channel_id] = model
    
    def get_common_analysis_model(self, channel_id: int = -1) -> List[CommonAnalysis]:
        """
        Retrieve one or more CommonAnalysis models by channel ID.

        Args:
            channel_id (int, optional): 
                The channel ID of the model to retrieve.
                If set to -1 (default), returns all models in ascending
                channel ID order.

        Returns:
            List[CommonAnalysis]: 
                A list containing one or more CommonAnalysis instances.
                If a specific channel_id is provided, the list will contain
                only the matching model.

        Raises:
            KeyError: If the specified channel_id does not exist.
        """
        if channel_id == -1:
            # Return all models sorted by channel_id
            return [self._common_analysis_model[cid] for cid in sorted(self._common_analysis_model)]

        if channel_id not in self._common_analysis_model:
            raise KeyError(f"Channel ID {channel_id} not found in results.")

        return [self._common_analysis_model[channel_id]]

    def get_common_analysis_models_channel_ids(self) -> List[int]:

        """
        Get a list of channel IDs for the common analysis models.
        Returns:
            List[int]: List of channel IDs.
        """
        return list(self._common_analysis_model.keys())

    def build_report(self) -> None:
        """
        Build the analysis report.
        """
        self._process()
        csv_mrg_list:List[CSVManager] = self.create_csv()

        for csv_mgr in csv_mrg_list:
            if not csv_mgr.write():
                self.logger.error(f"Failed to write CSV: {csv_mgr.get_path_fname()}")
                continue
            self.logger.debug(f'Wrote CSV File: {csv_mgr.get_path_fname()}')

        # self.create_png_plot()

    @abstractmethod
    def _process(self) -> None:
        """
        Process the analysis data and populate the report.
        """
        pass

    @abstractmethod
    def create_csv(self, **kwargs) -> List[CSVManager]:
        """
        """
        pass

    @abstractmethod
    def create_png_plot(self, **kwargs) -> None:
        """
        """
        pass

    def __init(self):

        self._data_list:List[Dict[str, Any]] = self._analysis.get_results().get('analysis') # type: ignore

        self._png_dir = SystemConfigSettings.png_dir
        self._csv_dir = SystemConfigSettings.csv_dir
        self._group_time = Utils.time_stamp()        
        self._base_filename:str = ""
        self._common_analysis_model:Dict[int, BaseModel] = {}

        data = self._data_list[0]
        self._mac_address:MacAddress = MacAddress(data.get('mac_address'))
        self._sys_descr:SystemDescriptor = SystemDescriptor.load_from_dict(data['device_details']['sys_descr'])

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