
from __future__ import annotations

# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia

import json
import logging
from struct import calcsize, unpack

from pydantic import BaseModel, Field
from pypnm.lib.types import IntSeries
from pypnm.pnm.process.pnm_file_type import PnmFileType
from pypnm.pnm.process.pnm_header import PnmHeader, PnmHeaderParameters
from pypnm.lib.mac_address import MacAddress

class CmDsHistModel(BaseModel):
    """
    """
    pnm_header:PnmHeaderParameters  = Field(..., description="")
    mac_address:str                 = Field(default=MacAddress.null(), description="Device MAC address")
    symmetry: int                   = Field(..., description="Histogram symmetry indicator (device-specific meaning).")
    dwell_count_values_length: int  = Field(..., description="Number of dwell count entries reported.")
    dwell_count_values: IntSeries   = Field(..., description="Dwell count values per bin.")
    hit_count_values_length: int    = Field(..., description="Number of hit count entries reported.")
    hit_count_values: IntSeries     = Field(..., description="Hit count values per bin.")


class CmDsHist(PnmHeader):
    """
    Represents the Downstream Histogram data collected from a Cable Modem (CM).

    This histogram provides a measurement of nonlinear effects in the downstream channel,
    such as amplifier compression and laser clipping. The CM captures a time-domain
    signal snapshot and sorts the values into bins (buckets) based on signal level,
    allowing visualization of distortions. This helps technicians identify signal issues.

    The histogram includes:
    - MAC address of the CM
    - Symmetry flag (1 byte, additional signal characterization)
    - Dwell Count: Number of samples considered per bin
    - Hit Count: Number of samples that actually fall into each bin
    
    The class extracts and exposes this data from binary format for further analysis.
    """

    def __init__(self, binary_data: bytes):
        super().__init__(binary_data)
        self.logger = logging.getLogger(self.__class__.__name__)

        self._mac_address: str
        self._symmetry: int
        self._dwell_count_values_length: int
        self._dwell_count_values: IntSeries
        self._hit_count_values_length: int
        self._hit_count_values: IntSeries
        self._model:CmDsHistModel

        self.__process()

    def __process(self) -> None:
        
        if self.get_pnm_file_type() != PnmFileType.DOWNSTREAM_HISTOGRAM:
            cann = PnmFileType.DOWNSTREAM_HISTOGRAM.get_pnm_cann()
            raise ValueError(f"PNM File Stream is not RxMER file type: {cann}, Error: {self.get_pnm_file_type().get_pnm_cann()}")
                
        mac_sym_format = '>6sB'
        mac_sym_header_size = calcsize(mac_sym_format)

        try:
            unpacked = unpack(mac_sym_format, self.pnm_data[:mac_sym_header_size])
            self._mac_address = ':'.join(f'{b:02X}' for b in unpacked[0])
            self._symmetry = unpacked[1]
        except Exception as e:
            raise ValueError(f"Failed to unpack header: {e}")

        offset = mac_sym_header_size

        # Dwell Count Values
        self._dwell_count_values_length = int.from_bytes(self.pnm_data[offset:offset + 4], byteorder='big')
        offset += 4
        count = self._dwell_count_values_length // 4
        self._dwell_count_values = [int.from_bytes(self.pnm_data[offset + i*4:offset + (i+1)*4], 'big') for i in range(count)]
        offset += self._dwell_count_values_length

        # Hit Count Values
        self._hit_count_values_length = int.from_bytes(self.pnm_data[offset:offset + 4], byteorder='big')
        offset += 4
        count = self._hit_count_values_length // 4
        self._hit_count_values = [int.from_bytes(self.pnm_data[offset + i*4:offset + (i+1)*4], 'big') for i in range(count)]

        self._model = CmDsHistModel(
            pnm_header                  =   self.getPnmHeaderParameterModel(),
            mac_address                 =   self._mac_address,
            symmetry                    =   self._symmetry,
            dwell_count_values_length   =   self._hit_count_values_length,
            dwell_count_values          =   self._dwell_count_values,
            hit_count_values_length     =   self._hit_count_values_length,
            hit_count_values            =   self._hit_count_values,
        )
    
    def to_model(self) -> CmDsHistModel:
        return self._model

    def to_dict(self) -> dict:
        """
        Returns a dictionary containing the summarized histogram data.

        Returns:
            dict: Summary of histogram measurement results.
        """
        return self.to_model().model_dump()

    def to_json(self, indent:int=2) -> str:
        """
        Returns a JSON-formatted string of the summarized histogram data.

        Returns:
            str: JSON representation of the histogram summary.
        """
        return self.to_model().model_dump_json(indent=indent)
