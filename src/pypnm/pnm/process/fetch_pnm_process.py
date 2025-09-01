# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia

from pypnm.pnm.process.pnm_file_type import PnmFileType
from pypnm.pnm.process.pnm_header import PnmHeader

class PnmFileTypeObjectFetcher(PnmHeader):
    """
    Factory that inspects a PNM byte-stream header and returns an instance
    of the appropriate parser for that PNM file type.

    Usage:
        fetcher = PnmFileTypeObjectFetcher(byte_stream)
        parser = fetcher.get_parser()
        result = parser.parse()
    """
    def __init__(self, byte_stream: bytes):
        super().__init__(byte_stream)
        self._byte_stream = byte_stream
        self._parser = None
        self._process()

    def _process(self) -> None:
        """
        Determine the PNM file type and instantiate its parser via if/elif.
        """
        pnm_type = self.get_pnm_file_type()

        # Map PNM type to parser class explicitly
        if pnm_type == PnmFileType.SYMBOL_CAPTURE:
            from pypnm.pnm.process.CmSymbolCapture import CmSymbolCapture as ParserClass
        elif pnm_type == PnmFileType.OFDM_CHANNEL_ESTIMATE_COEFFICIENT:
            from pypnm.pnm.process.CmDsOfdmChanEstimateCoef import CmDsOfdmChanEstimateCoef as ParserClass
        elif pnm_type == PnmFileType.DOWNSTREAM_CONSTELLATION_DISPLAY:
            from pypnm.pnm.process.CmDsConstDispMeas import CmDsConstDispMeas as ParserClass
        elif pnm_type == PnmFileType.RECEIVE_MODULATION_ERROR_RATIO:
            from pypnm.pnm.process.CmDsOfdmRxMer import CmDsOfdmRxMer as ParserClass
        elif pnm_type == PnmFileType.DOWNSTREAM_HISTOGRAM:
            from pypnm.pnm.process.CmDsHist import CmDsHist as ParserClass
        elif pnm_type == PnmFileType.UPSTREAM_PRE_EQUALIZER_COEFFICIENTS:
            from pypnm.pnm.process.CmUsPreEq import CmUsOfdmaPreEq as ParserClass
        elif pnm_type == PnmFileType.UPSTREAM_PRE_EQUALIZER_COEFFICIENTS_LAST_UPDATE:
            from pypnm.pnm.process.CmUsPreEq import CmUsOfdmaPreEq as ParserClass
        elif pnm_type == PnmFileType.OFDM_FEC_SUMMARY:
            from pypnm.pnm.process.CmDsOfdmFecSummary import CmDsOfdmFecSummary as ParserClass
        elif pnm_type == PnmFileType.SPECTRUM_ANALYSIS:
            from pypnm.pnm.process.CmSpectrumAnalysis import CmSpectrumAnalysis as ParserClass
        elif pnm_type == PnmFileType.OFDM_MODULATION_PROFILE:
            from pypnm.pnm.process.CmDsOfdmModulationProfile import CmDsOfdmModulationProfile as ParserClass
        elif pnm_type == PnmFileType.LATENCY_REPORT:
            from pypnm.pnm.process.CmLatencyRpt import CmLatencyRpt as ParserClass
        else:
            raise ValueError(f"Unsupported PNM file type: {pnm_type}")

        # Instantiate the parser
        self._parser = ParserClass(self._byte_stream)

    def get_parser(self):
        """
        Return the parser instance for this PNM file.

        Raises:
            RuntimeError: if parser not initialized (unsupported type).
        """
        if not self._parser:
            raise RuntimeError(
                "PNM parser not available; unsupported file type or initialization error"
            )
        return self._parser
