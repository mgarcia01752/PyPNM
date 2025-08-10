# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia


from typing import Any, Dict, List
from pypnm.api.routes.basic.analysis_output_abstract import AnalysisReport
from pypnm.api.routes.common.classes.analysis.analysis import Analysis
from pypnm.lib.csv.csv_manager import CSVManager
from pypnm.lib.math.linear_regression import LinearRegression1D

class RxMerAnalysisReport(AnalysisReport):
    """RxMerAnalysisReport is a concrete implementation of AnalysisReport
    for handling RxMER analysis reports.
    """
    def __init__(self, analysis:Analysis):
        super().__init__(analysis)
        self._process()

    def create_csv(self, **kwargs) -> CSVManager:
        # Implementation for creating CSV file
        csv_mgr = self.get_csv_manager()
        return csv_mgr

    def create_png_plot(self, **kwargs):
        # Implementation for creating PNG plot
        pass

    def _process(self) -> None:
        '''
            result = {
                "device_details": measurement.get("device_details"),
                "pnm_header": measurement.get("pnm_header"),
                "mac_address": measurement.get("mac_address"),
                "channel_id": measurement.get("channel_id"),
                "magnitude_unit": "dB",
                "frequency_unit": "Hz",            
                "carrier_status_map": {
                    RxMerCarrierType.EXCLUSION.name.lower(): RxMerCarrierType.EXCLUSION.value,
                    RxMerCarrierType.CLIPPED.name.lower(): RxMerCarrierType.CLIPPED.value,
                    RxMerCarrierType.NORMAL.name.lower(): RxMerCarrierType.NORMAL.value,
                },
                "carrier_values": {
                    "carrier_count": len(freqs),
                    "magnitude": magnitudes,
                    "frequency": freqs,            
                    "carrier_status": carrier_status,
                },
                "modulation_statistics": ss.to_dict()           
            }        
        
        '''

        data_list:List[Dict[str, Any]] = self.get_analysis_data()

        for data in data_list:
            
            chan_id:int = data['channel_id']
            raw_x:List[int] = data['carrier_values']['frequency']
            raw_y:List[float] = data['carrier_values']['magnitude']
            linear_regression: List[float] = LinearRegression1D(raw_y).to_list()



        