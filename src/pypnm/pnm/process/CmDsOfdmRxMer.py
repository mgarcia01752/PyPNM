# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia

import json
import logging
import struct
from typing import Dict, List, Optional, Tuple

from lib.shannon.series import ShannonSeries
from pypnm.pnm.lib.signal_statistics import SignalStatistics
from pypnm.pnm.process.pnm_file_type import PnmFileType
from pypnm.pnm.process.pnm_header import PnmHeader


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

        self.channel_id: Optional[int] = None
        self.mac_address: Optional[str] = None
        self.subcarrier_zero_frequency: Optional[int] = None
        self.first_active_subcarrier_index: Optional[int] = None
        self.subcarrier_spacing: Optional[int] = None
        self.rxmer_data_length: Optional[int] = None
        self.rxmer_data: Optional[bytes] = None
        self.rx_mer_float_data: Optional[List[float]] = None

        self._process_rxmer_data()

    def _process_rxmer_data(self) -> None:
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

            self.channel_id = unpacked_data[0]
            self.mac_address = ':'.join(f'{b:02x}' for b in unpacked_data[1])
            self.subcarrier_zero_frequency = unpacked_data[2]
            self.first_active_subcarrier_index = unpacked_data[3]
            self.subcarrier_spacing = unpacked_data[4] * 1000 # Khz
            self.rxmer_data_length = unpacked_data[5]
            self.rxmer_data = self.pnm_data[head_len:head_len + self.rxmer_data_length]

            if len(self.rxmer_data) < self.rxmer_data_length:
                raise ValueError(f"Insufficient RxMER data length: {len(self.rxmer_data)} based on header field: {self.rxmer_data_length}")

            self.logger.debug(f"Parsed RxMER header: "
                              f"channel_id={self.channel_id}, mac={self.mac_address}, "
                              f"zero_freq={self.subcarrier_zero_frequency}, active_idx={self.first_active_subcarrier_index}, "
                              f"spacing={self.subcarrier_spacing}, data_len={self.rxmer_data_length}")
        except struct.error as e:
            self.logger.error(f"Struct unpack error: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Error processing RxMER data: {e}")
            raise

    def get_rxmer_values(self) -> List[float]:
        """
        Converts raw RxMER bytes to float values in quarter-dB steps.

        Returns:
            List[float]: Decoded RxMER values.
        """
        if self.rx_mer_float_data is not None:
            return self.rx_mer_float_data

        if not self.rxmer_data:
            self.logger.error("RxMER data is empty or uninitialized.")
            return []

        self.rx_mer_float_data = [
            min(max(byte / 4.0, 0.0), 63.5)
            for byte in self.rxmer_data
        ]
        self.logger.debug(f"Decoded {len(self.rx_mer_float_data)} RxMER float values.")
        return self.rx_mer_float_data

    def get_raw_data(self) -> Tuple[Optional[int], Optional[str], Optional[int],
                                    Optional[int], Optional[int], Optional[int], Optional[bytes]]:
        """
        Returns a tuple of all parsed header fields and the raw RxMER bytes.

        Returns:
            Tuple containing channel_id, mac_address, zero_frequency, active_subcarrier_index,
            subcarrier_spacing, rxmer_data_length, and raw rxmer_data bytes.
        """
        return (
            self.channel_id,
            self.mac_address,
            self.subcarrier_zero_frequency,
            self.first_active_subcarrier_index,
            self.subcarrier_spacing,
            self.rxmer_data_length,
            self.rxmer_data
        )

    def to_dict(self, header_only: bool = False) -> Dict[str, object]:
        """
        Returns a dictionary representation of the RxMER header and optionally the values.

        Args:
            header_only (bool): If True, only include header fields.

        Returns:
            Dict[str, object]: Parsed RxMER data.
        """
        data = self.getPnmHeader(header_only=True)
        
        data.update({
            "channel_id": self.channel_id,
            "mac_address": self.mac_address,
            "zero_frequency": self.subcarrier_zero_frequency,
            "first_active_subcarrier_index": self.first_active_subcarrier_index,
            "subcarrier_spacing": self.subcarrier_spacing,
            "data_length": self.rxmer_data_length,
            "occupied_channel_bandwidth": (self.rxmer_data_length * self.subcarrier_spacing),
        })
        
        if not header_only:
            data["value_units"] = "dB"
            values:List[float] = self.get_rxmer_values()
            data["values"]= values
            data["signal_statistics"] = SignalStatistics(values).compute()
            data["modulation_statistics"] = ShannonSeries(values).to_dict()

        return data

    def to_json(self, header_only: bool = False) -> str:
        """
        Returns a JSON string representation of the RxMER data.

        Args:
            header_only (bool): If True, only include header fields.

        Returns:
            str: JSON string of RxMER data.
        """
        try:
            return json.dumps(self.to_dict(header_only=header_only), indent=2)
        except Exception as e:
            self.logger.error(f"Failed to serialize RxMER data to JSON: {e}")
            return "{}"
