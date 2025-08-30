# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia

import logging
import struct

from typing import Any, Dict, Optional

from pydantic.fields import Field

from pypnm.lib.constants import KHZ
from pypnm.lib.mac_address import MacAddress
from pypnm.lib.signal_processing.shan.series import ShannonSeries
from pypnm.pnm.lib.signal_statistics import SignalStatistics
from pypnm.pnm.process.model.pnm_base_model import PnmBaseModel
from pypnm.pnm.process.pnm_file_type import PnmFileType
from pypnm.pnm.process.pnm_header import PnmHeader
from pypnm.lib.types import FloatSeries

class CmDsOfdmRxMerModel(PnmBaseModel):
    """Downstream OFDM RxMER dataset for a single channel."""
    data_length: int                        = Field(..., ge=0, description="Number of RxMER points (subcarriers)")
    occupied_channel_bandwidth: int         = Field(..., ge=0, description="OFDM Occupied Bandwidth (Hz)")
    value_units:str                         = Field(default="dB", description="Non-mutable")
    values:FloatSeries                      = Field(..., description="OFDM Occupied Bandwidth (Hz)")
    signal_statistics:Dict[str, Any]        = Field(..., description="")
    modulation_statistics:Dict[str, Any]    = Field(..., description="")

class CmDsOfdmRxMer(PnmHeader):
    """
    Parses and represents DOCSIS 3.1 CM Downstream OFDM RxMER data.

    This class decodes a binary RxMER measurement, extracting metadata from the header and
    converting the RxMER byte array into float values representing MER in quarter-dB steps.
    """

    def __init__(self, binary_data: bytes):
        """
        Initializes the object and immediately processes the binary RxMER data.

        Args:
            binary_data (bytes): Raw binary data from a PNM file.
        """
        super().__init__(binary_data)
        self.logger = logging.getLogger(self.__class__.__name__)
        self._rxmer_model:CmDsOfdmRxMerModel

        self._channel_id: Optional[int]                     = 0
        self._mac_address: Optional[str]                    = MacAddress.null()
        self._subcarrier_zero_frequency: Optional[int]      = 0
        self._first_active_subcarrier_index: Optional[int]  = 0
        self._subcarrier_spacing: Optional[int]             = 0
        self._rxmer_data_length: Optional[int]              = 0
        self._rxmer_data: Optional[bytes]                    
        self._rx_mer_float_data: Optional[FloatSeries]      = []

        self._process()
      
    def _process(self) -> None:
        """
        Parses the header and extracts metadata and raw RxMER data.
        """
        if self.get_pnm_file_type() != PnmFileType.RECEIVE_MODULATION_ERROR_RATIO:
            cann = PnmFileType.RECEIVE_MODULATION_ERROR_RATIO.get_pnm_cann()
            raise ValueError(f"PNM File Stream is not RxMER file type: {cann}, Error: {self.get_pnm_file_type().get_pnm_cann()}")
        
        try:
            rxmer_data_format = '!B6sIHBI'  # channel_id, mac(6), zero_freq, active_idx, spacing, data_len
            head_len:int = struct.calcsize(rxmer_data_format)

            if len(self.pnm_data) < head_len:
                raise ValueError("Binary data too short to contain RxMER header.")

            unpacked_data = struct.unpack(rxmer_data_format, self.pnm_data[:head_len])

            self._channel_id                     = unpacked_data[0]
            self._mac_address                    = ':'.join(f'{b:02x}' for b in unpacked_data[1])
            self._subcarrier_zero_frequency      = unpacked_data[2]
            self._first_active_subcarrier_index  = unpacked_data[3]
            self._subcarrier_spacing             = unpacked_data[4] * KHZ
            self._rxmer_data_length              = unpacked_data[5]
            self._rxmer_data                     = self.pnm_data[head_len:head_len + self._rxmer_data_length]

            if len(self._rxmer_data) < self._rxmer_data_length:
                raise ValueError(f"Insufficient RxMER data length: {len(self._rxmer_data)} based on header field: {self._rxmer_data_length}")
            
            self._rxmer_model = self._update_model()

        except struct.error as e:
            self.logger.error(f"Struct unpack error: {e}")
            raise

        except Exception as e:
            self.logger.error(f"Error processing RxMER data: {e}")
            raise

    def _update_model(self) -> CmDsOfdmRxMerModel:

        values = self.get_rxmer_values()

        model = CmDsOfdmRxMerModel(
                pnm_header                      =   self.getPnmHeaderParameterModel(),       
                channel_id                      =   self._channel_id,
                mac_address                     =   self._mac_address,
                subcarrier_zero_frequency       =   self._subcarrier_zero_frequency,
                first_active_subcarrier_index   =   self._first_active_subcarrier_index,
                subcarrier_spacing              =   self._subcarrier_spacing,
                data_length                     =   self._rxmer_data_length,
                occupied_channel_bandwidth      =   self._rxmer_data_length * self._subcarrier_spacing,         
                values                          =   values,
                signal_statistics               =   SignalStatistics(values).compute(),
                modulation_statistics           =   ShannonSeries(values).to_dict()
            )

        return model

    def get_rxmer_values(self) -> FloatSeries:
        """
        Converts raw RxMER bytes to float values in quarter-dB steps.

        Returns:
            List[float]: Decoded RxMER values.
        """
        if self._rx_mer_float_data:
            self.logger.info(f"RxMER Float Data: {self._rx_mer_float_data}")
            return self._rx_mer_float_data

        if not self._rxmer_data:
            self.logger.error("RxMER data is empty or uninitialized.")
            return []

        self._rx_mer_float_data = [min(max(byte / 4.0, 0.0), 63.5) for byte in self._rxmer_data]

        self.logger.debug(f"Decoded {len(self._rx_mer_float_data)} RxMER float values.")

        return self._rx_mer_float_data

    def to_model(self) -> CmDsOfdmRxMerModel:
        return self._rxmer_model
    
    def to_dict(self) -> Dict[str, object]:
        """
        Returns a dictionary representation of the RxMER header and optionally the values.

        Args:
            header_only (bool): If True, only include header fields.

        Returns:
            Dict[str, object]: Parsed RxMER data.
        """
        return self.to_model().model_dump()

    def to_json(self) -> str:
        """
        Returns a JSON string representation of the RxMER data.

        Args:
            header_only (bool): If True, only include header fields.

        Returns:
            str: JSON string of RxMER data.
        """
        return self.to_model().model_dump_json()
