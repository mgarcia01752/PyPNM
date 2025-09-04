
from __future__ import annotations

# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia

import logging
from pypnm.pnm.process.pnm_file_type import PnmFileType
from pypnm.pnm.process.pnm_header import PnmHeader

class CmLatencyRpt(PnmHeader):
    def __init__(self, binary_data: bytes):
        super().__init__(binary_data)
        self.logger = logging.getLogger(self.__class__.__name__)
        self._process()
    
    def _process(self):
        '''
        Number of LatencySummaryData objects (n)    1 byte
        Latency Data                                n*LatencySummaryData
        '''
        if self.get_pnm_file_type() != PnmFileType.LATENCY_REPORT:
            cann = PnmFileType.LATENCY_REPORT.get_pnm_cann()
            raise ValueError(f"PNM File Stream is not RxMER file type: {cann}, Error: {self.get_pnm_file_type().get_pnm_cann()}")
 
        return None