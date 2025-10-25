
from __future__ import annotations

# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia

import logging
from struct import unpack, calcsize
from typing import Optional, Dict

from pydantic import Field

from pypnm.lib.constants import KHZ
from pypnm.pnm.lib.fixed_point_decoder import FixedPointDecoder
from pypnm.pnm.process.model.pnm_base_model import PnmBaseModel
from pypnm.pnm.process.pnm_file_type import PnmFileType
from pypnm.pnm.process.pnm_header import PnmHeader
from pypnm.lib.types import ComplexArray

class CmDsConstDispMeasModel(PnmBaseModel):
    """
    """
    actual_modulation_order: int    = Field(..., ge=0, description="")
    num_sample_symbols: int         = Field(..., ge=0, description="Number of constellation soft-decision symbol samples")
    sample_length: int              = Field(..., ge=0, description="Number of constellation soft-decision complex pairs")
    sample_units: str               = Field(default="[Real(I), Imaginary(Q)]", description="Non-mutable")
    samples: ComplexArray           = Field(..., description="Constellation soft-decision samples")

class CmDsConstDispMeas(PnmHeader):
    """
    Parses and processes Downstream Constellation Display Measurement (CmDsConstDispMeas) data.
    Inherits from PnmHeader to handle binary SNMP-based CM measurement data.
    """
    CONST_DISPLAY_DATA_COMPLEX_LENGTH:int = 4

    def __init__(self, binary_data: bytes):
        """
        Initializes the CmDsConstDispMeas instance and parses the binary payload.

        Args:
            binary_data (bytes): Raw binary data from SNMP or TFTP source.
        """
        super().__init__(binary_data)
        self.logger = logging.getLogger(self.__class__.__name__)

        self._channel_id: int
        self._mac_address: str
        self._subcarrier_zero_frequency: int
        self._actual_modulation_order: int
        self._num_sample_symbols: int
        self._subcarrier_spacing: int
        self._display_data_length: int
        self._constellation_display_data: bytes
        self._parsed_constellation_data: ComplexArray
        self._model: CmDsConstDispMeasModel

        self.__process()

    def __process(self) -> None:
        """
        Parses the binary payload for constellation display measurement.

        Expected binary format:
            - 1 byte: channel ID
            - 6 bytes: CM MAC address
            - 4 bytes: subcarrier zero frequency    (Hz)
            - 2 bytes: actual modulation order      (DsOfdmModulationType)
            - 2 bytes: number of sample symbols
            - 1 byte:  subcarrier spacing           (kHz)
            - 4 bytes: display data length          (bytes)
            - N bytes: constellation display data   (complex samples)
        """
        
        if self.get_pnm_file_type() != PnmFileType.DOWNSTREAM_CONSTELLATION_DISPLAY:
            cann = PnmFileType.DOWNSTREAM_CONSTELLATION_DISPLAY.get_pnm_cann()
            raise ValueError(f"PNM File Stream is not RxMER file type: {cann}, Error: {self.get_pnm_file_type().get_pnm_cann()}")
        
        const_disp_meas_format = '>B6sIHHBI'
        const_disp_meas_size = calcsize(const_disp_meas_format)
        unpacked_data = unpack(const_disp_meas_format, self.pnm_data[:const_disp_meas_size])

        self._channel_id                 = unpacked_data[0]
        self._mac_address                = unpacked_data[1].hex(':')
        self._subcarrier_zero_frequency  = unpacked_data[2]
        self._actual_modulation_order    = unpacked_data[3]
        self._num_sample_symbols         = unpacked_data[4]
        self._subcarrier_spacing         = unpacked_data[5] * KHZ
        self._display_data_length        = unpacked_data[6]
        self._constellation_display_data = self.pnm_data[const_disp_meas_size:]

        self._model = CmDsConstDispMeasModel(
            pnm_header                      =   self.getPnmHeaderParameterModel(),
            channel_id                      =   self._channel_id,
            mac_address                     =   self._mac_address,
            subcarrier_zero_frequency       =   self._subcarrier_zero_frequency,
            subcarrier_spacing              =   self._subcarrier_spacing,
            actual_modulation_order         =   self._actual_modulation_order,
            num_sample_symbols              =   self._num_sample_symbols,
            sample_length                   =   self._display_data_length,
            samples                         =   self._process_constellation_display_data(),
        )

    def _process_constellation_display_data(self) -> ComplexArray:
        """
        Decodes the constellation display binary data into a list of [i, q] float pairs.

        This reduced format is optimized for REST payload transmission.

        Returns:
            List of [i, q] float pairs.
        """
        offset = 0
        raw:bytes = self._constellation_display_data
        decode_list = []

        while offset + self.CONST_DISPLAY_DATA_COMPLEX_LENGTH <= len(raw):
            decoded = FixedPointDecoder.decode_complex_data(raw[offset:offset + 4], (2, 13))
            
            for pt in decoded:
                decode_list.append([float(pt.real), float(pt.imag)])
            
            offset += 4

        return decode_list

    def to_model(self) -> CmDsConstDispMeasModel:
        return self._model

    def to_dict(self) -> Dict[str, Optional[object]]:
        """
        Returns:
            dict: Alias for `get_const_disp_meas()`.
        """
        return self.to_model().model_dump()
    
    def to_json(self, indent:int=2) -> str:
        """
        Serializes the parsed measurement data to a JSON string.

        Returns:
            str: JSON-formatted string representation of the data.
        """
        return self.to_model().model_dump_json(indent=indent)