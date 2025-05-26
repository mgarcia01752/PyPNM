# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia

from enum import Enum
import logging
from typing import Any, Dict

from pnm.process.CmDsConstDispMeas import CmDsConstDispMeas
from pnm.process.CmDsOfdmChanEstimateCoef import CmDsOfdmChanEstimateCoef
from pnm.process.CmDsOfdmFecSummary import CmDsOfdmFecSummary
from pnm.process.CmDsOfdmModulationProfile import CmDsOfdmModulationProfile
from pnm.process.CmDsOfdmRxMer import CmDsOfdmRxMer
from pnm.process.CmUsPreEq import CmUsPreEq
from pnm.process.pnm_file_type import PnmFileType
from pnm.process.pnm_header import PnmHeader


class PnmObjectAndParameters(PnmHeader):
    """
    Parses raw PNM file byte streams, dispatches to type-specific parsers,
    and exposes core parameters in a standardized dict form.

    Inherits:
        PnmHeader: provides `file_type` and `file_type_num` properties.

    Public Methods:
        to_dict(): Returns parameters or error details as a dict.
    """

    def __init__(self, byte_stream: bytes):
        """
        Initialize the parser with raw PNM data.

        Args:
            file_byte_stream: Full contents of a PNM file, header + payload.
        """
        super().__init__(byte_stream)
        self.logger = logging.getLogger(self.__class__.__name__)
        self.byte_stream = byte_stream
        
        # Normalize header type fields to ASCII strings
        if isinstance(self.file_type, (bytes, bytearray)):
            file_type_str = self.file_type.decode('ascii', errors='ignore')
        else:
            file_type_str = str(self.file_type)

        if isinstance(self.file_type_num, (bytes, bytearray)):
            file_type_num_str = self.file_type_num.decode('ascii', errors='ignore')
        else:
            file_type_num_str = str(self.file_type_num)

        self.pnm_type = f"{file_type_str}{file_type_num_str}"
        self.logger.debug(f"Processing PNM-Type: ({self.pnm_type})")

    def to_dict(self) -> Dict[str, Any]:
        """
        Process the PNM file and return a dict of core parameters, including
        any error encountered.

        Returns:
            Dict with keys:
              - file_type (str): 4-char PNM code
              - capture_time (int|None)
              - channel_id (int|None)
              - mac_address (str|None)
              - subcarrier_zero_frequency (int|None)
              - first_active_subcarrier_index (int|None)
              - subcarrier_spacing (int|None)
              - error (str, optional)
        """
        result: Dict[str, Any] = {"file_type": self.pnm_type}
        try:
            parsed = self._process()
            # Order of keys matters for consistency
            result.update({
                "capture_time": getattr(parsed, "capture_time", None),
                "channel_id": getattr(parsed, "channel_id", None),
                "mac_address": getattr(parsed, "mac_address", None),
                "subcarrier_zero_frequency": getattr(parsed, "subcarrier_zero_frequency", None),
                "first_active_subcarrier_index": getattr(parsed, "first_active_subcarrier_index", None),
                "subcarrier_spacing": getattr(parsed, "subcarrier_spacing", None),
            })
        except NotImplementedError as nie:
            result["error"] = str(nie)
        except ValueError as ve:
            result["error"] = str(ve)
        except Exception as exc:
            result["error"] = f"Unexpected error: {exc}"
        return result

    def _process(self) -> Any:
        """
        Determine PNM type and call the associated parser.

        Returns:
            The object returned by the specific _process_* method.

        Raises:
            ValueError: For unknown PNM codes.
            NotImplementedError: For unimplemented handlers.
        """
            
        try:
            file_type_enum = PnmFileType(self.pnm_type)
        except ValueError:
            raise ValueError(f"Unsupported PNM file type code: {self.pnm_type}")

        self.logger.debug(f'PNM-File-Type-Enum: {file_type_enum}')
        
        # Dispatch in enum order
        dispatch_map = {
            PnmFileType.SYMBOL_CAPTURE: self._process_symbol_capture,
            PnmFileType.OFDM_CHANNEL_ESTIMATE_COEFFICIENT: self._process_ofdm_channel_estimate,
            PnmFileType.DOWNSTREAM_CONSTELLATION_DISPLAY: self._process_constellation_display,
            PnmFileType.RECEIVE_MODULATION_ERROR_RATIO: self._process_rxmer,
            PnmFileType.DOWNSTREAM_HISTOGRAM: self._process_histogram,
            PnmFileType.UPSTREAM_PRE_EQUALIZER_COEFFICIENTS: self._process_upstream_pre_eq,
            PnmFileType.UPSTREAM_PRE_EQUALIZER_COEFFICIENTS_LAST_UPDATE: self._process_upstream_pre_eq_update,
            PnmFileType.OFDM_FEC_SUMMARY: self._process_fec_summary,
            PnmFileType.SPECTRUM_ANALYSIS: self._process_spectrum_analysis,
            PnmFileType.OFDM_MODULATION_PROFILE: self._process_modulation_profile,
            PnmFileType.LATENCY_REPORT: self._process_latency_report,
        }

        handler = dispatch_map.get(file_type_enum)
        if handler is None:
            raise NotImplementedError(f"Handler not implemented for {file_type_enum.name}")
        return handler()

    # Handlers in enum order:
    def _process_symbol_capture(self) -> Any:
        """Symbol capture parser (not implemented)."""
        raise NotImplementedError("Symbol capture parsing not implemented.")

    def _process_ofdm_channel_estimate(self) -> CmDsOfdmChanEstimateCoef:
        """OFDM channel estimate coefficient parser."""
        return CmDsOfdmChanEstimateCoef(self.byte_stream)

    def _process_constellation_display(self) -> CmDsConstDispMeas:
        """Downstream constellation display parser."""
        return CmDsConstDispMeas(self.byte_stream)

    def _process_rxmer(self) -> CmDsOfdmRxMer:
        """Receive modulation error ratio (RxMER) parser."""
        return CmDsOfdmRxMer(self.byte_stream)

    def _process_histogram(self) -> Any:
        """Downstream histogram parser (not implemented)."""
        raise NotImplementedError("Histogram parsing not implemented.")

    def _process_upstream_pre_eq(self) -> CmUsPreEq:
        """Upstream pre-equalizer coefficients parser."""
        return CmUsPreEq(self.byte_stream)

    def _process_upstream_pre_eq_update(self) -> Any:
        """Latest upstream pre-equalizer update parser (not implemented)."""
        raise NotImplementedError("Upstream pre-equalizer update parsing not implemented.")

    def _process_fec_summary(self) -> CmDsOfdmFecSummary:
        """OFDM FEC summary parser."""
        return CmDsOfdmFecSummary(self.byte_stream)

    def _process_spectrum_analysis(self) -> Any:
        """Spectrum analysis parser (not implemented)."""
        raise NotImplementedError("Spectrum analysis parsing not implemented.")

    def _process_modulation_profile(self) -> CmDsOfdmModulationProfile:
        """OFDM modulation profile parser."""
        return CmDsOfdmModulationProfile(self.byte_stream)

    def _process_latency_report(self) -> Any:
        """Latency report parser (not implemented)."""
        raise NotImplementedError("Latency report parsing not implemented.")
