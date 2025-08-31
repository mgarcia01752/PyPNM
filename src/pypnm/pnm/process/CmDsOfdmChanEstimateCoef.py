# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia

import logging
from struct import calcsize, unpack
from typing import List, Optional, Tuple, Dict, cast

from pydantic import Field

from pypnm.api.routes.docs.pnm.files.service import MacAddress
from pypnm.lib.constants import INVALID_CHANNEL_ID, KHZ
from pypnm.lib.types import ComplexArray
from pypnm.pnm.lib.fixed_point_decoder import FixedPointDecoder
from pypnm.pnm.process.model.pnm_base_model import PnmBaseModel
from pypnm.pnm.process.pnm_file_type import PnmFileType
from pypnm.pnm.process.pnm_header import PnmHeader


class CmDsOfdmChanEstimateCoefModel(PnmBaseModel):
    """
    Canonical payload for **DOCSIS OFDM downstream channel-estimation coefficients**.

    This extends `PnmBaseModel` (providing `pnm_header`, `channel_id`, `mac_address`,
    and OFDM subcarrier metadata) with complex tap values for each active subcarrier.

    Notes
    -----
    - `value_units` is fixed to `"complex"`.
    - `data_length` is the **byte length** of the coefficient payload in the PNM file,
      which must be a multiple of 4 (2 bytes real + 2 bytes imag per subcarrier).
    - The number of complex points equals `data_length // 4`.
    - `occupied_channel_bandwidth` is derived as
      `(#complex points) * subcarrier_spacing` (Hz).

    Fields
    ------
    data_length : int
        Raw byte length of the complex coefficient payload (≥ 0; multiple of 4).
    occupied_channel_bandwidth : int
        Total occupied OFDM bandwidth in Hertz.
    value_units : str
        Non-mutable indicator of units; always `"complex"`.
    values : ComplexArray
        Per-subcarrier complex coefficients represented as `[real, imag]` pairs
        (rounded or raw depending on producer).
    """
    data_length: int                        = Field(..., ge=0, description="Number of points (subcarriers)")
    occupied_channel_bandwidth: int         = Field(..., ge=0, description="OFDM Occupied Bandwidth (Hz)")
    value_units:str                         = Field(default="complex", description="Non-mutable")
    values:ComplexArray                     = Field(..., description="")


class CmDsOfdmChanEstimateCoef(PnmHeader):
    """
    Parser/adapter for **DOCSIS OFDM Downstream Channel Estimation Coefficients**.

    Responsibilities
    ----------------
    1. Validate the incoming PNM stream is of type `OFDM_CHANNEL_ESTIMATE_COEFFICIENT`.
    2. Unpack the header and payload from the binary stream.
    3. Decode fixed-point complex coefficients using `FixedPointDecoder`.
    4. Materialize a `CmDsOfdmChanEstimateCoefModel` with metadata and values.

    Expected binary header format (big-endian)
    -----------------------------------------
    Struct format: ``'>B6sIHBI'``

    - ``B``  : Channel ID (uint8)
    - ``6s`` : MAC address (6 bytes)
    - ``I``  : Subcarrier-zero frequency, Hz (uint32)
    - ``H``  : First active subcarrier index (uint16)
    - ``B``  : Subcarrier spacing, **kHz** (uint8; later scaled by `KHZ` to Hz)
    - ``I``  : Coefficient payload length, **bytes** (uint32; must be multiple of 4)

    Coefficient encoding
    --------------------
    - Each complex coefficient is stored as **2 bytes real + 2 bytes imag** in a
      Signed-Magnitude fixed-point format `(S.M, N)` specified by `sm_n_format`.
    """

    def __init__(self, binary_data: bytes, sm_n_format: Tuple[int, int] = (2, 13), round_precision: int = 6):
        """
        Construct and immediately parse a channel-estimation coefficient blob.

        Parameters
        ----------
        binary_data : bytes
            Raw PNM file buffer sourced from SNMP/TFTP capture.
        sm_n_format : Tuple[int, int], default (2, 13)
            Signed-Magnitude fixed-point configuration as `(integer_bits, fractional_bits)`
            used by `FixedPointDecoder.decode_complex_data`.
        round_precision : int
            Decimal places to round `[real, imag]` pairs when producing `values`.
            If `None`, no rounding is applied.

        Raises
        ------
        ValueError
            If validation of file type, header size, payload size, or alignment fails.
        struct.error
            If the header cannot be unpacked with the expected struct layout.
        """
        super().__init__(binary_data)
        self.logger = logging.getLogger(self.__class__.__name__)
        self._sm_n_format = sm_n_format
        self._round_precision = round_precision
        
        self._channel_id: int                                = INVALID_CHANNEL_ID
        self._mac_address: Optional[str]                     = MacAddress.null()
        self._subcarrier_zero_frequency: int                 = -1
        self._first_active_subcarrier_index: int             = -1
        self._subcarrier_spacing: int                        = -1
        self._coefficient_data_length: int                   = -1
        self._coefficient_data: Optional[List[complex]]      = None
        self._coeff_values_rounded: ComplexArray

        self._model:CmDsOfdmChanEstimateCoefModel

        self._process()

    def _process(self) -> None:
        """
        Parse the binary stream and decode complex coefficients.

        Workflow
        --------
        1. Ensure the PNM file type is `OFDM_CHANNEL_ESTIMATE_COEFFICIENT`.
        2. Validate buffer size for the fixed header (`'>B6sIHBI'`).
        3. Unpack header fields; verify `coefficient_data_length` is a multiple of 4.
        4. Slice the complex payload and decode via `FixedPointDecoder.decode_complex_data`.
        5. Normalize MAC address formatting and convert spacing from kHz to Hz.
        6. Build the pydantic model (`CmDsOfdmChanEstimateCoefModel`) with rounded pairs.

        Raises
        ------
        ValueError
            If header/payload are truncated, the type is incorrect,
            or the coefficient byte length is misaligned.
        struct.error
            If unpacking the header fails.
        """
        if self.get_pnm_file_type() != PnmFileType.OFDM_CHANNEL_ESTIMATE_COEFFICIENT:
            cann = PnmFileType.OFDM_CHANNEL_ESTIMATE_COEFFICIENT.get_pnm_cann()
            raise ValueError(f"PNM File Stream is not RxMER file type: {cann}, Error: {self.get_pnm_file_type().get_pnm_cann()}")
                
        header_format = '>B6sIHBI'
        header_size = calcsize(header_format)

        if len(self.pnm_data) < header_size:
            raise ValueError("Insufficient binary data for CmDsOfdmChanEstimateCoef header.")

        (
            self._channel_id,
            mac_raw,
            self._subcarrier_zero_frequency,
            self._first_active_subcarrier_index,
            self._subcarrier_spacing,
            self._coefficient_data_length
        ) = unpack(header_format, self.pnm_data[:header_size])

        if self._coefficient_data_length % 4 != 0:
            raise ValueError("Coefficient data length must be a multiple of 4 bytes (2 bytes real + 2 bytes imag).")

        coef_start = header_size
        coef_end = coef_start + self._coefficient_data_length
        if len(self.pnm_data) < coef_end:
            raise ValueError("Coefficient data segment is truncated or incomplete.")

        complex_bytes = self.pnm_data[coef_start:coef_end]
        self._coefficient_data = FixedPointDecoder.decode_complex_data(complex_bytes, self._sm_n_format)

        self._mac_address = ':'.join(f'{b:02x}' for b in mac_raw)
        self._subcarrier_spacing = self._subcarrier_spacing * cast(int,KHZ)
        obw:int = (len(self._coefficient_data) * self._subcarrier_spacing)

        self._coeff_values_rounded = [
            [round(c.real, self._round_precision), 
             round(c.imag, self._round_precision)] if self._round_precision is not None else [c.real, c.imag]
            for c in self._coefficient_data
        ]        

        self._model = CmDsOfdmChanEstimateCoefModel(
            pnm_header                      = self.getPnmHeaderParameterModel(),
            channel_id                      = self._channel_id,
            mac_address                     = self._mac_address,
            subcarrier_zero_frequency       = self._first_active_subcarrier_index,
            subcarrier_spacing              = self._subcarrier_spacing,
            data_length                     = self._coefficient_data_length,
            first_active_subcarrier_index   = self._first_active_subcarrier_index,
            occupied_channel_bandwidth      = obw,
            values                          = self._coeff_values_rounded,
        )

    def get_coefficients(self, precision:str="rounded") -> ComplexArray:
        """
        Retrieve channel-estimation coefficients.

        Parameters
        ----------
        precision : {"rounded", "raw"}, default "rounded"
            - `"rounded"` returns `[real, imag]` pairs with `round_precision` applied.
            - `"raw"` returns the original complex values decoded from the payload.

        Returns
        -------
        ComplexArray
            Coefficients in the requested representation.
        """
        if precision == "rounded":
            return self._coeff_values_rounded
        
        return cast(ComplexArray, self._coefficient_data)
        
    def to_model(self) -> CmDsOfdmChanEstimateCoefModel:
        """
        Return the fully-populated pydantic model representation.

        Returns
        -------
        CmDsOfdmChanEstimateCoefModel
            Structured payload including header metadata and coefficients.
        """
        return self._model

    def to_dict(self) -> Dict:
        """
        Export the parsed header and coefficient metadata as a Python dictionary.

        Returns
        -------
        dict
            A `model_dump()` of the internal pydantic model, suitable for JSON serialization.
        """              
        return self.to_model().model_dump()

    def to_json(self, indent:int=2) -> str:
        """
        Export the parsed data as a JSON string.

        Parameters
        ----------
        indent : int, default 2
            Indentation level for pretty-printed JSON.

        Returns
        -------
        str
            JSON document describing the coefficients and associated metadata.
        """
        return self.to_model().model_dump_json(indent=indent)
