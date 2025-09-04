
from __future__ import annotations

# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia

import logging
from pypnm.api.routes.common.classes.analysis.analysis import Analysis
from pypnm.lib.mac_address import MacAddress

class AnalysisParseUtils:
    
    def __init__(self, analysis:Analysis):
        self.logger = logging.getLogger(f"{self.__class__.__name__}")
        self.analysis = analysis
        
        self.mac_address:MacAddress = None
        
        self._process()

    def _process(self):
        
        # Get the raw list of instances
        if hasattr(self.analysis, "get_results"):
            result_dict = self.analysis.get_results()
            raw_instances = result_dict.get("analysis", []) if isinstance(result_dict, dict) else []
        else:
            raw_instances = self.analysis

        for item in raw_instances:
            inst = None
            
            if isinstance(inst, dict):
                """
                    Collect Common Data Point:
                        Assumption that all Analysis Results are:
                        * From the same Mac Address
                        * Capture Times are roughly within a few seconds                
                 """
                if not self.mac_address:
                    self.mac_address = MacAddress(inst.get("mac_address", MacAddress.null()))
                    self.capture_time = int(inst.get("pnm_header",{}).get("capture_time", "0"))
                    if self.capture_time == 0:
                        self.logger.warning(f"Unexpected Capture Time: {self.capture_time}")
            
            else:
                self.logger.error(f"Unexpected item type: {type(inst)}")
            
    def get_mac_address(self) -> MacAddress:
        return  self.mac_address      

    def get_capture_time(self) -> int:
        return self.capture_time
    