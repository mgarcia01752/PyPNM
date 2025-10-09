# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia

from __future__ import annotations

import logging
import struct
from typing import Any, Dict

from pydantic.fields import Field

from pypnm.lib.constants import KHZ
from pypnm.lib.mac_address import MacAddress
from pypnm.lib.signal_processing.shan.series import ShannonSeries
from pypnm.pnm.lib.signal_statistics import SignalStatistics, SignalStatisticsModel
from pypnm.pnm.process.model.pnm_base_model import PnmBaseModel
from pypnm.pnm.process.pnm_file_type import PnmFileType
from pypnm.pnm.process.pnm_header import PnmHeader
from pypnm.lib.types import FloatSeries, FrequencySeriesHz, MacAddressStr

class CmDsOfdmRxMerModel(PnmBaseModel):
    """
    Canonical Pydantic model for a **single downstream OFDM RxMER dataset**.

    This model extends `PnmBaseModel` (which provides `pnm_header`, `channel_id`, `mac_address`,
    and OFDM subcarrier metadata) with RxMER-specific fields and summary statistics.

    Notes
    -----
    - `value_units` is fixed to `"dB"` (MER in decibels).
    - `data_length` should equal `len(values)`.
    - `occupied_channel_bandwidth` is derived as `data_length * subcarrier_spacing` (Hz).
    - `signal_statistics` is produced by `SignalStatistics(values).compute()`.
    - `modulation_statistics` is produced by `ShannonSeries(values).to_dict()`.

    Fields
    ------
    data_length : int
        Number of RxMER points (subcarriers); must be ≥ 0.
    occupied_channel_bandwidth : int
        Total occupied OFDM bandwidth in Hertz.
    value_units : str
        Unit for `values` (non-mutable), always `"dB"`.
    values : FloatSeries
        Decoded MER values per active subcarrier (floats in dB).
    signal_statistics : Dict[str, Any]
        Aggregate statistics over `values` (min/max/mean, etc.).
    modulation_statistics : Dict[str, Any]
        Shannon-related metrics derived from `values`.
    """
    data_length: int                        = Field(..., ge=0, description="Number of RxMER points (subcarriers)")
    occupied_channel_bandwidth: int         = Field(..., ge=0, description="OFDM Occupied Bandwidth (Hz)")
    value_units:str                         = Field(default="dB", description="Non-mutable")
    values:FloatSeries                      = Field(..., description="RxMER values per active subcarrier (dB)")
    signal_statistics:SignalStatisticsModel = Field(..., description="Aggregate statistics computed from values")
    modulation_statistics:Dict[str, Any]    = Field(..., description="Shannon-based modulation metrics")


class CmDsOfdmRxMer(PnmHeader):
    """
    Parser and container for **DOCSIS 3.1 CM Downstream OFDM RxMER** binary data.

    This class:
      1) Validates the PNM file type as RxMER.
      2) Unpacks the RxMER header and payload from the binary stream.
      3) Decodes the MER byte array into floats (quarter-dB steps, saturated).
      4) Materializes a `CmDsOfdmRxMerModel` with metadata and derived statistics.

    Binary Layout (big-endian)
    --------------------------
    Format string: ``'!B6sIHBI'``

    - ``B``  : `channel_id` (uint8)
    - ``6s`` : `mac_address` (6 raw bytes)
    - ``I``  : `subcarrier_zero_frequency` (uint32, Hz)
    - ``H``  : `first_active_subcarrier_index` (uint16)
    - ``B``  : `subcarrier_spacing` (uint8, kHz → multiplied by `KHZ` to get Hz)
    - ``I``  : `data_length` (uint32, number of RxMER points)

    MER Decoding
    ------------
    Each MER byte represents quarter-dB units. The decoder divides by 4.0 and clamps
    to the implementation’s upper bound (here 63.5 dB).
    """

    def __init__(self, binary_data: bytes):
        """
        Initialize and immediately parse the provided RxMER binary blob.

        Parameters
        ----------
        binary_data : bytes
            Raw PNM file data containing an RxMER measurement.

        Raises
        ------
        ValueError
            If the PNM stream is not of RxMER type, or if the data is too short for the header,
            or if the declared data length exceeds the available bytes.
        struct.error
            If unpacking the header fails due to a malformed binary layout.
        """
        super().__init__(binary_data)
        self.logger = logging.getLogger(self.__class__.__name__)
        self._rxmer_model:CmDsOfdmRxMerModel

        self._channel_id: int                     = 0
        self._mac_address: MacAddressStr          = MacAddress.null()
        self._subcarrier_zero_frequency: int      = 0
        self._first_active_subcarrier_index: int  = 0
        self._subcarrier_spacing: int             = 0
        self._rxmer_data_length: int              = 0
        self._rxmer_data: bytes                    
        self._rx_mer_float_data: FloatSeries      = []

        self._process()
      
    def _process(self) -> None:
        """
        Parse header fields and extract the RxMER payload from the binary stream.

        Workflow
        --------
        1) Verify that the PNM file type is `RECEIVE_MODULATION_ERROR_RATIO`.
        2) Compute the header size from the struct format and validate the input length.
        3) Unpack header fields and slice out the RxMER payload.
        4) Build the pydantic model via `_update_model()`.

        Raises
        ------
        ValueError
            If the file type is not RxMER, if the binary data is shorter than the header,
            or if the payload is shorter than the declared `data_length`.
        struct.error
            If the binary header cannot be unpacked using the expected format.
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
        """
        Construct and return the `CmDsOfdmRxMerModel` from parsed fields.

        Notes
        -----
        - `occupied_channel_bandwidth` is computed as `data_length * subcarrier_spacing`.
        - `signal_statistics` is generated via `SignalStatistics(values).compute()`.
        - `modulation_statistics` is generated via `ShannonSeries(values).to_dict()`.

        Returns
        -------
        CmDsOfdmRxMerModel
            The fully populated RxMER model for this measurement.
        """
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
        Decode the raw RxMER payload (bytes) into floating-point MER values (dB).

        Details
        -------
        - Each input byte encodes MER in **quarter-dB**.
        - Values are converted as `byte / 4.0` and saturated to the range `[0.0, 63.5]` dB.
        - Results are cached in `_rx_mer_float_data` on first call.

        Returns
        -------
        FloatSeries
            A list of decoded MER values (dB), one per active subcarrier.
        """
        if self._rx_mer_float_data:
            self.logger.debug(f"RxMER Float Data: {self._rx_mer_float_data}")
            return self._rx_mer_float_data

        if not self._rxmer_data:
            self.logger.error("RxMER data is empty or uninitialized.")
            return []

        self._rx_mer_float_data = [min(max(byte / 4.0, 0.0), 63.5) for byte in self._rxmer_data]

        self.logger.debug(f"Decoded {len(self._rx_mer_float_data)} RxMER float values.")

        return self._rx_mer_float_data

    def get_frequencies(self) -> FrequencySeriesHz:
        """
        Compute per-subcarrier center frequencies (Hz).

        Formula
        -------
        f[k] = subcarrier_zero_frequency + subcarrier_spacing * (first_active_subcarrier_index + k)

        Returns
        -------
        FrequencySeriesHz
            List of per-subcarrier frequencies in Hz, one entry per RxMER value.
        """
        spacing = int(self._subcarrier_spacing)
        f_zero = int(self._subcarrier_zero_frequency)
        first_idx = int(self._first_active_subcarrier_index)
        n = int(self._rxmer_data_length)

        if spacing <= 0 or n <= 0:
            return []

        start = f_zero + spacing * first_idx
        freqs: FrequencySeriesHz = [start + i * spacing for i in range(n)]
        return freqs

    def to_model(self) -> CmDsOfdmRxMerModel:
        """
        Return the parsed, structured `CmDsOfdmRxMerModel`.

        Returns
        -------
        CmDsOfdmRxMerModel
            The pydantic model containing header, metadata, values, and statistics.
        """
        return self._rxmer_model
    
    def to_dict(self) -> Dict[str, object]:
        """
        Export the RxMER data as a plain Python dictionary.

        Returns
        -------
        Dict[str, object]
            A `dict` equivalent of `to_model().model_dump()`, suitable for JSON serialization.
        """
        return self.to_model().model_dump()

    def to_json(self) -> str:
        """
        Export the RxMER data as a JSON string.

        Returns
        -------
        str
            A JSON document equivalent to `to_model().model_dump_json()`.
        """
        return self.to_model().model_dump_json()
