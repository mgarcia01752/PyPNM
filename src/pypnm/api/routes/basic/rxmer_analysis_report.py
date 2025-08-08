# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia


from pypnm.api.routes.basic.analysis_output_abstract import AnalysisReport
from pypnm.api.routes.common.classes.analysis.analysis import Analysis
from pypnm.lib.csv.csv_manager import CSVManager

class RxMerAnalysisReport(AnalysisReport):
    """RxMerAnalysisReport is a concrete implementation of AnalysisReport
    for handling RxMER analysis reports.
    """
    def __init__(self, analysis:Analysis):
        super().__init__(analysis)
        self._base_filename = "rxmer_analysis_report"

    def create_csv(self, **kwargs) -> CSVManager:
        # Implementation for creating CSV file
        csv_mgr = self.get_csv_manager()
        csv_fname = self.set_csv_fname(tags=[self._base_filename])

        return csv_mgr

    def create_png_plot(self, **kwargs):
        # Implementation for creating PNG plot
        pass

