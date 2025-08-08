# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List, Union
from pydantic import BaseModel, Field

import pandas as pd
import matplotlib.pyplot as plt
import zipfile

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
        # Ensure parent directory exists
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

    def set_csv_fname(self, tags: List[str]) -> str:
        return self._generate_fname(tags=tags, ext='csv')

    def set_png_fname(self, tags: List[str]) -> str:
        return self._generate_fname(tags=tags, ext='png')

    def get_csv_manager(self) -> CSVManager:
        return CSVManager()

    def get_base_filename(self) -> str:
        """
        Returns the base filename for the analysis report.
        """
        return self._generate_fname()
    
    @abstractmethod
    def create_csv(self, **kwargs) -> CSVManager:
        """
        """
        pass

    @abstractmethod
    def create_png_plot(self, **kwargs) -> None:
        """
        """
        pass

    def __init(self):
        self._data_list:List[Dict[str, Any]] = analysis.get_results().get('analysis') # type: ignore

        self._png_dir = SystemConfigSettings.png_dir
        self._csv_dir = SystemConfigSettings.csv_dir
        self._group_time = Utils.time_stamp()        
        self._base_filename:str = ""

        data = self._data_list[0]
        self._mac_address:MacAddress = MacAddress(data.get('mac_address'))
        self._sys_descr:SystemDescriptor = SystemDescriptor.load_from_dict(data['device_details']['sysDescr'])

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