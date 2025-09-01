# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia

import logging
import numpy as np

from enum import Enum
from typing import Callable, List, Dict, Any, Mapping, Sequence, Union, cast

from pypnm.api.routes.common.classes.analysis.model.schema import (
    BaseAnalysisModel, ConstellationDisplayAnalysisModel, DsHistogramAnalysisModel, DsRxMerAnalysisModel, 
    FecSummaryCodeWordModel, OfdmFecSummaryAnalysisModel, OfdmFecSummaryProfileModel, RegressionModel, RxMerCarrierValuesModel)
from pypnm.api.routes.common.extended.common_messaging_service import MessageResponse
from pypnm.api.routes.docs.pnm.files.service import SystemConfigSettings
from pypnm.docsis.cm_snmp_operation import SystemDescriptor, Utils
from pypnm.lib.constants import INVALID_CHANNEL_ID
from pypnm.lib.file_processor import FileProcessor
from pypnm.lib.log_files import LogFile
from pypnm.lib.mac_address import MacAddress
from pypnm.lib.qam.lut_mgr import QamLutManager
from pypnm.lib.qam.types import QamModulation
from pypnm.lib.signal_processing.complex_array_ops import ComplexArrayOps
from pypnm.lib.signal_processing.group_delay import GroupDelay
from pypnm.lib.signal_processing.linear_regression import LinearRegression1D
from pypnm.lib.types import ArrayLike, ComplexArray, FloatSeries, IntSeries, StringArray
from pypnm.pnm.data_type.DsOfdmModulationType import DsOfdmModulationType
from pypnm.pnm.lib.signal_statistics import SignalStatistics
from pypnm.pnm.process.CmDsOfdmModulationProfile import ModulationOrderType
from pypnm.pnm.process.pnm_file_type import PnmFileType
from pypnm.lib.signal_processing.shan.series import Shannon, ShannonSeries

class RxMerCarrierType(Enum):
    """
    RxMER carrier classification labels.

    Members
    -------
    EXCLUSION : str
        "0". Subcarriers marked as excluded (e.g., guard bands, PLC gaps).
    CLIPPED : str
        "1". Values clipped/saturated (e.g., 0.0 dB or 63.5 dB).
    NORMAL : str
        "2". Valid, non-clipped RxMER readings.
    """
    EXCLUSION   = "0"
    CLIPPED     = "1"
    NORMAL      = "2"

# RxMER special sentinel values used for classification:
RXMER_EXCLUSION = 63.75
RXMER_CLIPPED_LOW = 0.0
RXMER_CLIPPED_HIGH = 63.5
    
class AnalysisType(Enum):
    """
    Analysis mode selector.

    Notes
    -----
    BASIC
        Provides (frequency, magnitude) and selected meta-data depending on the
        detected PNM file type. Additional per-type metrics may be included
        (e.g., group delay, Shannon limits, histogram counts).
    """
    BASIC = 0

class Analysis:
    """Core analysis runner.

    This orchestrator normalizes the payload's ``data`` into a list of
    measurement dictionaries and dispatches to the appropriate basic
    analysis routine based on the inferred PNM file type.

    Parameters
    ----------
    analysis_type : AnalysisType
        Analysis mode (currently ``AnalysisType.BASIC``).
    msg_response : MessageResponse
        Wrapped transport of the measurement payload; expected to expose
        ``payload_to_dict()`` with a top-level ``"data"`` entry.

    Attributes
    ----------
    logger : logging.Logger
        Component logger named after the class.
    analysis_type : AnalysisType
        Selected analysis mode.
    msg_response : MessageResponse
        Original message/measurement container.
    measurement_data : list of dict
        Normalized list of measurement dicts derived from the payload.
    _result_model : list of BaseAnalysisModel
        Collected typed results (when a Pydantic model is produced).
    _analysis_dict : list of dict
        Collected plain-dict results for serialization.

    Notes
    -----
    If the logger is configured at ``DEBUG`` level, the raw message response
    is persisted to disk via :meth:`save_message_response`.
    """

    def __init__(self, analysis_type: "AnalysisType", msg_response: "MessageResponse") -> None:
        self.logger = logging.getLogger(f"{self.__class__.__name__}")
        self.analysis_type: "AnalysisType" = analysis_type
        self.msg_response: "MessageResponse" = msg_response

        payload: Dict[str, Any] = msg_response.payload_to_dict() or {}
        raw_data = payload.get("data", [])

        self._result_model:List[BaseAnalysisModel] = []

        # Normalize measurement_data to List[Dict[str, Any]]
        if isinstance(raw_data, Mapping):
            self.measurement_data: List[Dict[str, Any]] = [dict(raw_data)]
        elif isinstance(raw_data, Sequence) and not isinstance(raw_data, (str, bytes, bytearray)):
            self.measurement_data = [dict(m) for m in raw_data]  # type: ignore[arg-type]
        else:
            self.measurement_data = []

        self._analysis_dict: List[Dict[str, Any]] = []

        # Persist the raw message when DEBUG is enabled
        if self.logger.isEnabledFor(logging.DEBUG):
            self.save_message_response(self.msg_response)

        self._process()

    def _process(self) -> None:
        """Iterate and dispatch analysis per measurement.

        For each normalized measurement, this method assembles the combined
        PNM file type string from the header fields and routes to the
        corresponding *basic* analysis handler.

        Notes
        -----
        Unknown or missing file types are logged; the measurement is
        serialized for troubleshooting via :class:`LogFile`.
        """
        
        for idx, measurement in enumerate(self.measurement_data):

            pnm_header: Dict[str, Any] = measurement.get("pnm_header") or {}
            channel_id: int =  measurement.get("channel_id", INVALID_CHANNEL_ID)

            self.logger.debug(f"PNM-HEADER[{idx}]: {pnm_header}")

            file_type       = str(pnm_header.get("file_type", ""))
            file_ver        = str(pnm_header.get("file_type_version", ""))
            pnm_file_type   = f'{file_type}{file_ver}'

            if not pnm_file_type:
                self.logger.error(f'PNM FileType not Found')
                LogFile.write(fname=f'rxmer-analysis-measurment-{Utils.time_stamp()}.dict' , data=measurement)
                pass

            if self.analysis_type == AnalysisType.BASIC:                    # type: ignore[name-defined]
                self.logger.info(f'Performing Basic Analysis on PNM: {pnm_file_type} on Channel: {channel_id}')
                self._basic_analysis(pnm_file_type, measurement)
            
            else:
                self.logger.error(f'Unknown AnalysisType: {self.analysis_type}')
                raise

    def _basic_analysis(self, pnm_file_type: str, measurement):
        """
        Route to the appropriate BASIC analysis handler.

        Parameters
        ----------
        pnm_file_type : str
            Concatenated PNM file type identifier, e.g.
            ``PnmFileType.RECEIVE_MODULATION_ERROR_RATIO.value``.
        measurement : dict
            Single measurement dictionary. Expected keys vary by file type,
            but generally include:
                - ``pnm_header`` : dict with ``file_type`` and version
                - ``channel_id`` : int
                - ``device_details`` : dict
                - per-type fields such as subcarrier spacing, values, profiles, etc.

        Notes
        -----
        This method only dispatches. See the specific handlers for field
        expectations and returned structures:

        - :meth:`basic_analysis_ds_chan_est`
        - :meth:`basic_analysis_ds_constellation_display`
        - :meth:`basic_analysis_rxmer`
        - :meth:`basic_analysis_ds_histogram`
        - :meth:`basic_analysis_us_ofdma_pre_equalization`
        - :meth:`basic_analysis_ds_ofdm_fec_summary`
        - :meth:`basic_analysis_ds_modulation_profile`
        """
        if pnm_file_type == PnmFileType.OFDM_CHANNEL_ESTIMATE_COEFFICIENT.value:
            self.logger.info("Processing: OFDM_CHANNEL_ESTIMATE_COEFFICIENT")
            self.__update_result_dict(self.basic_analysis_ds_chan_est(measurement))
            # model = self.basic_analysis_ds_chan_est(measurement)
            # self.__update_result_model(model)
            # self.__update_result_dict(model.model_dump())   

        elif pnm_file_type == PnmFileType.DOWNSTREAM_CONSTELLATION_DISPLAY.value:
            self.logger.debug("Processing: DOWNSTREAM_CONSTELLATION_DISPLAY")
            model = self.basic_analysis_ds_constellation_display(measurement)
            self.__update_result_model(model)
            self.__update_result_dict(model.model_dump())

        elif pnm_file_type == PnmFileType.RECEIVE_MODULATION_ERROR_RATIO.value:
            self.logger.info("Processing: RECEIVE_MODULATION_ERROR_RATIO")
            model = self.basic_analysis_rxmer(measurement)
            self.__update_result_model(model)
            self.__update_result_dict(model.model_dump())            

        elif pnm_file_type == PnmFileType.DOWNSTREAM_HISTOGRAM.value:
            self.logger.debug("Processing: DOWNSTREAM_HISTOGRAM")
            model = self.basic_analysis_ds_histogram(measurement)
            self.__update_result_model(model)
            self.__update_result_dict(model.model_dump())

        elif pnm_file_type == PnmFileType.UPSTREAM_PRE_EQUALIZER_COEFFICIENTS.value:
            self.logger.debug("Processing: UPSTREAM_PRE_EQUALIZER_COEFFICIENTS")
            self.__update_result_dict(self.basic_analysis_us_ofdma_pre_equalization(measurement))
            # model = self.basic_analysis_us_ofdma_pre_equalization(measurement)
            # self.__update_result_model(model)
            # self.__update_result_dict(model.model_dump())
  
        elif pnm_file_type == PnmFileType.UPSTREAM_PRE_EQUALIZER_COEFFICIENTS_LAST_UPDATE.value:
            self.logger.debug("Stub: Processing: UPSTREAM_PRE_EQUALIZER_COEFFICIENTS_LAST_UPDATE")
            # model = self.basic_analysis_us_ofdma_pre_equalization(measurement)
            # self.__update_result_model(model)
            # self.__update_result_dict(model.model_dump())             
            pass

        elif pnm_file_type == PnmFileType.OFDM_FEC_SUMMARY.value:
            self.logger.debug("Processing: OFDM_FEC_SUMMARY")
            model = self.basic_analysis_ds_ofdm_fec_summary(measurement)
            self.__update_result_model(model)
            self.__update_result_dict(model.model_dump())

        elif pnm_file_type == PnmFileType.SPECTRUM_ANALYSIS.value:
            self.logger.debug("Stub: Processing: SPECTRUM_ANALYSIS")
            pass

        elif pnm_file_type == PnmFileType.OFDM_MODULATION_PROFILE.value:
            self.logger.info("Processing: OFDM_MODULATION_PROFILE")
            self.__update_result_dict(self.basic_analysis_ds_modulation_profile(measurement))
            # model = self.basic_analysis_ds_modulation_profile(measurement)
            # self.__update_result_model(model)
            # self.__update_result_dict(model.model_dump())             

        elif pnm_file_type == PnmFileType.LATENCY_REPORT.value:
            self.logger.warning("Stub: Processing: LATENCY_REPORT")
            pass

        else:
            self.logger.error(f"Unknown PNM file type: ({pnm_file_type})")

    def get_results(self, full_dict = True) -> Dict[str, Any]:
        """
        Get the accumulated analysis results (dict form).

        Parameters
        ----------
        full_dict : bool, default True
            Present for interface compatibility; this implementation always
            returns a dict with a single ``"analysis"`` key mapping to the
            internal list of dict results.

        Returns
        -------
        dict
            Structure of the form ``{"analysis": List[Dict[str, Any]]}``.
        """
        return {"analysis": self._analysis_dict}

    def get_model(self) -> Union[BaseAnalysisModel, List[BaseAnalysisModel]]:
        """Get the accumulated analysis results (typed models).

        Returns
        -------
        BaseAnalysisModel or list of BaseAnalysisModel
            The collected Pydantic models for analyses that produce them.
        """
        return self._result_model

    def save_message_response(self, msg_response: MessageResponse) -> None:
        """Persist the raw message response (debug aid).

        Parameters
        ----------
        msg_response : MessageResponse
            Source container that will be serialized to disk. The filename
            includes the MAC address (if present) and a timestamp.
        """
        msg_rsp_dict:Dict[Any, Any] = msg_response.payload_to_dict()
        mac = msg_rsp_dict.get('mac_address')
        fname = f'{SystemConfigSettings().message_response_dir}/{mac}_{Utils.time_stamp()}.msg'
        self.logger.debug(f'Saving Message Response: {fname}')

        fp = FileProcessor(fname)
        fp.write_file(msg_rsp_dict)
        fp.close()

    def __update_result_model(self, model:BaseAnalysisModel) :
        """Append a typed analysis model to the results cache.

        Parameters
        ----------
        model : BaseAnalysisModel
            The model instance to record.
        """
        self._result_model.append(model)
    
    def __update_result_dict(self, model:Dict[str,Any]):
        """Append a plain-dict analysis result to the results cache.

        Parameters
        ----------
        model : dict
            The dictionary result to record.
        """
        self._analysis_dict.append(model)

    @classmethod
    def basic_analysis_rxmer(cls, measurement: Dict[str, Any]) -> DsRxMerAnalysisModel:
        """
        Perform basic RxMER (Receive Modulation Error Ratio) analysis.

        Computes frequency per subcarrier, propagates magnitudes, and assigns a
        carrier status classification for each element (``EXCLUSION``, ``CLIPPED``,
        or ``NORMAL``). Also provides a simple regression line over the magnitudes
        and Shannon-series metadata.

        Parameters
        ----------
        measurement : dict
            Expected keys (subset):
                - ``channel_id`` : int
                - ``pnm_header`` : dict
                - ``device_details`` : dict
                - ``mac_address`` : str
                - ``subcarrier_spacing`` : int (Hz)
                - ``first_active_subcarrier_index`` : int
                - ``subcarrier_zero_frequency`` : int (Hz)
                - ``values`` : List[float] (RxMER in dB)

        Returns
        -------
        DsRxMerAnalysisModel
            Typed model with ``carrier_values.frequency``, ``carrier_values.magnitude``,
            and ``carrier_values.carrier_status`` aligned by index, plus regression
            and modulation statistics.

        Raises
        ------
        ValueError
            If required parameters are missing/negative, or lengths mismatch.
        """
        out: DsRxMerAnalysisModel

        channel_id                          = measurement.get("channel_id", INVALID_CHANNEL_ID)
        pnm_header                          = measurement.get("pnm_header",{})
        device_details                      = measurement.get("device_details",{})
        mac_address:str                     = measurement.get("mac_address",MacAddress.null()) 
        subcarrier_spacing:int              = measurement.get("subcarrier_spacing",-1)           
        first_active_subcarrier_index:int   = measurement.get("first_active_subcarrier_index",-1)
        subcarrier_zero_frequency:int       = measurement.get("subcarrier_zero_frequency", -1)
        values                              = measurement.get("values", [])
        
        if first_active_subcarrier_index < 0 or subcarrier_zero_frequency < 0 or subcarrier_spacing <0:
            raise ValueError(f"Active index: {first_active_subcarrier_index} or "
                             f"zero frequency: {subcarrier_zero_frequency} or "
                             f"spacing: {subcarrier_spacing} ALL must be non-negative")

        if not values:
            raise ValueError("No RxMER values provided in measurement.")

        base_freq = (subcarrier_spacing * first_active_subcarrier_index) + subcarrier_zero_frequency
        freqs:IntSeries = [base_freq + (i * subcarrier_spacing) for i in range(len(values))]
        magnitudes:FloatSeries = values

        classify: Callable[[float], int] = lambda v: int(
            RxMerCarrierType.EXCLUSION.value
            if v == RXMER_EXCLUSION
            else RxMerCarrierType.CLIPPED.value
            if v in (RXMER_CLIPPED_LOW, RXMER_CLIPPED_HIGH)
            else RxMerCarrierType.NORMAL.value
        )

        # carrier_status will be List[int]
        carrier_status: List[int] = [classify(v) for v in values]

        if not (len(freqs) == len(magnitudes) == len(carrier_status)):
            raise ValueError(
                f"Length mismatch detected: frequencies({len(freqs)}), "
                f"magnitudes({len(magnitudes)}), carrier_status({len(carrier_status)})"
            )

        ss = ShannonSeries(magnitudes)
        
        regession_model = RegressionModel(
            slope   = cast(FloatSeries, LinearRegression1D(cast(ArrayLike,magnitudes), 
                                                           cast(ArrayLike,freqs)).regression_line())
        )

        csm:Dict[str, Any] = { 
            RxMerCarrierType.EXCLUSION.name.lower(): RxMerCarrierType.EXCLUSION.value,
            RxMerCarrierType.CLIPPED.name.lower(): RxMerCarrierType.CLIPPED.value,
            RxMerCarrierType.NORMAL.name.lower(): RxMerCarrierType.NORMAL.value,
        }

        cv = RxMerCarrierValuesModel(
            carrier_status_map  = csm, 
            carrier_count       = len(freqs),
            magnitude           = magnitudes,
            frequency           = freqs,
            carrier_status      = carrier_status
        )

        out = DsRxMerAnalysisModel(
            device_details                  = device_details,
            pnm_header                      = pnm_header,
            channel_id                      = channel_id,
            mac_address                     = mac_address,
            subcarrier_spacing              = subcarrier_spacing,
            first_active_subcarrier_index   = first_active_subcarrier_index,
            subcarrier_zero_frequency       = subcarrier_zero_frequency,
            carrier_values                  = cv,
            regression                      = regession_model,
            modulation_statistics           = ss.to_model()
        )

        return out

    @classmethod
    def basic_analysis_ds_chan_est(cls, measurement: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform downstream channel estimation analysis.

        Computes per-subcarrier frequency, magnitude in dB (from complex
        channel estimates), group delay (from phase slope), and basic
        signal statistics.

        Parameters
        ----------
        measurement : dict
            Expected keys (subset):
                - ``subcarrier_spacing`` : int (Hz)
                - ``first_active_subcarrier_index`` : int
                - ``subcarrier_zero_frequency`` : int (Hz)
                - ``occupied_channel_bandwidth`` : int
                - ``values`` : ComplexArray (list of [real, imag])

        Returns
        -------
        dict
            Result dictionary containing:
                - ``carrier_values.frequency`` : List[int]
                - ``carrier_values.magnitude`` : List[float] (dB)
                - ``carrier_values.group_delay`` : List[float] (µs)
                - ``carrier_values.complex`` : original ComplexArray
                - meta-fields (units, header, device details, etc.)

        Raises
        ------
        ValueError
            If required parameters are missing/negative, or ``values`` is empty.
        """
        subcarrier_spacing:int = measurement.get("subcarrier_spacing",-1)                              # Hz
        first_active_subcarrier_index:int = measurement.get("first_active_subcarrier_index",-1)              # index
        subcarrier_zero_frequency:int = measurement.get("subcarrier_zero_frequency", -1)                    # Hz
        occupied_channel_bandwidth:int = measurement.get("occupied_channel_bandwidth", -1)  #
        
        if first_active_subcarrier_index < 0 or subcarrier_zero_frequency < 0 or subcarrier_spacing <0:
            raise ValueError(f"Active index: {first_active_subcarrier_index} or zero frequency: {subcarrier_zero_frequency} or spacing: {subcarrier_spacing} must be non-negative")

        values:ComplexArray = measurement.get("values", []) # Complex Values
        if not values:
            raise ValueError("No complex channel estimation values provided in measurement.")
        
        start_freq = (subcarrier_spacing * first_active_subcarrier_index) + subcarrier_zero_frequency
        freqs:List[int] = [start_freq + (i * subcarrier_spacing) for i in range(len(values))]

        # Group delay calculation
        gd = GroupDelay.from_channel_estimate(Hhat=values, df_hz=subcarrier_spacing, f0_hz=start_freq)
        gd_results = gd.to_result()
       
        # Calculate Per-subcarrer Complex Numerbers
        cao = ComplexArrayOps(values)

        logging.info(f'Power: {cao.to_list(cao.power_db())}')

        signal_stats = SignalStatistics(cao.power_db()).compute()
        complex_arr = np.asarray(values, dtype=complex)

        result = {
            "device_details": measurement.get("device_details"),
            "pnm_header": measurement.get("pnm_header"),
            "mac_address": measurement.get("mac_address"),
            "channel_id": measurement.get("channel_id"),
            "frequency_unit": "Hz",
            "magnitude_unit": "dB",
            "group_delay_unit": "microsecond",
            "complex_unit": "[Real, Imaginary]",
            "carrier_values": {
                "occupied_channel_bandwidth": occupied_channel_bandwidth,
                "carrier_count": len(freqs),
                "frequency": freqs,
                "magnitude": cao.to_list(cao.power_db()),
                "group_delay": ComplexArrayOps.to_list(gd_results.group_delay_us),
                "complex": values,
                "complex_dimension": f"{complex_arr.ndim}"
            },
            "signal_statistics_target": "magnitude",
            "signal_statistics": signal_stats
        }

        return result

    @classmethod
    def basic_analysis_ds_modulation_profile(cls, measurement: Dict[str, Any], split_carriers: bool = True) -> Dict[str, Any]:
        """
        Analyze the Downstream OFDM Modulation Profile.

        Parameters
        ----------
        measurement : dict
            Expected keys (subset):
                - ``subcarrier_spacing`` : int (Hz)
                - ``first_active_subcarrier_index`` : int
                - ``zero_frequency`` : int (Hz)
                - ``profiles`` : list of dicts with:
                    * ``profile_id`` : int
                    * ``schemes`` : list with items:
                        - ``modulation_order`` : str (e.g., "qam256", "plc", "exclusion")
                        - ``num_subcarriers`` : int
        split_carriers : bool, default True
            If ``True``, output carrier lists in split arrays
            (``frequency``/``modulation``/``shannon_min_mer``). If ``False``,
            emit a list of per-carrier dicts.

        Returns
        -------
        dict
            Contains header/device info and a ``profiles`` list with
            ``carrier_values`` per profile, either split arrays or a list of
            carrier dicts.

        Raises
        ------
        ValueError
            If spacing/indices/frequencies are invalid.
        """
        spacing:int      = measurement.get("subcarrier_spacing", -1)
        active_index:int = measurement.get("first_active_subcarrier_index", -1)
        zero_freq:int    = measurement.get("subcarrier_zero_frequency", -1)

        if active_index < 0 or zero_freq < 0 or spacing < 0:
            raise ValueError(f"Invalid parameters: spacing={spacing}, active_index={active_index}, zero_freq={zero_freq}")

        start_freq = zero_freq + spacing * active_index

        result: Dict[str, Any] = {
            "device_details":       measurement.get("device_details"),
            "pnm_header":           measurement.get("pnm_header"),
            "mac_address":          measurement.get("mac_address"),
            "channel_id":           measurement.get("channel_id"),
            "frequency_unit":       "Hz",
            "shannon_limit_unit":   "dB",
            "profiles":             [] 
        }

        for profile in measurement.get("profiles", []):
            profile_id  = profile.get("profile_id")
            schemes     = profile.get("schemes", [])

            freqs:    IntSeries             = []
            mods:     StringArray           = []
            shannons: FloatSeries           = []
            carriers: List[Dict[str, Any]]  = []

            freq_ptr = start_freq
            for scheme in schemes:
                mod_type:str = scheme.get("modulation_order")
                count:int    = scheme.get("num_subcarriers", 0)

                mod_type = ModulationOrderType(int(mod_type)).name

                for _ in range(count):
                    if mod_type in ("continuous_pilot", "exclusion"):
                        s_limit = 0.0
                    elif mod_type == "plc":                                 # treat as 16-QAM
                        s_limit = Shannon.bits_to_snr(4)
                    else:
                        s_limit = Shannon.snr_from_modulation(mod_type)

                    s_limit = round(s_limit, 2)
                    f_val   = int(freq_ptr)

                    if split_carriers:
                        freqs.append(f_val)
                        mods.append(mod_type)
                        shannons.append(s_limit)
                    else:
                        carriers.append({
                            "frequency":        f_val,
                            "modulation":       mod_type,
                            "shannon_min_mer":  s_limit
                        })

                    freq_ptr += spacing

            entry: Dict[str, Any] = {"profile_id": profile_id}
            if split_carriers:
                entry["carrier_values"] = {
                    "frequency": freqs,
                    "modulation": mods,
                    "shannon_min_mer": shannons
                }
            else:
                entry["carrier_values"] = {
                    "carriers": carriers
                }

            result["profiles"].append(entry)
        
        return result

    @classmethod
    def basic_analysis_us_ofdma_pre_equalization(cls, measurement: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform basic analysis of upstream OFDMA pre-equalization data.

        Computes:
            - Per-carrier frequency (Hz)
            - Magnitude (dB) from complex coefficients
            - Group delay (µs) from unwrapped phase gradient
            - Complex samples passthrough

        Parameters
        ----------
        measurement : dict
            Expected keys (subset):
                - ``subcarrier_spacing`` : int (Hz)
                - ``first_active_subcarrier_index`` : int
                - ``subcarrier_zero_frequency`` : int (Hz)
                - ``values`` : list of [real, imag]

        Returns
        -------
        dict
            Dictionary with units, per-carrier arrays, and metadata.

        Raises
        ------
        ValueError
            If ``values`` is empty.
        """
        spacing: int = measurement.get("subcarrier_spacing", 0)  # in Hz
        active_index: int = measurement.get("first_active_subcarrier_index", 0)
        zero_freq: int = measurement.get("subcarrier_zero_frequency", 0)  # in Hz
        base_freq = zero_freq + (spacing * active_index)

        values: List[List[float]] = measurement.get("values", [])
        if not values:
            raise ValueError("No complex channel estimation values provided in measurement.")

        complex_values = np.array([complex(r, i) for r, i in values])
        magnitudes_db = 20 * np.log10(np.abs(complex_values) + 1e-12)

        # Group delay = -dφ/df, φ = phase
        phase = np.unwrap(np.angle(complex_values))
        group_delay = -np.gradient(phase, spacing) * 1e6  # in microseconds

        freqs = [base_freq + i * spacing for i in range(len(complex_values))]

        result = {
            "pnm_header": measurement.get("pnm_header"),
            "mac_address": measurement.get("mac_address"),
            "channel_id": measurement.get("channel_id"),
            "frequency_unit": "Hz",
            "magnitude_unit": "dB",
            "group_delay_unit": "microsecond",
            "complex_unit": "[Real, Imaginary]",
            "carrier_values": {
                "carrier_count": len(freqs),
                "frequency": freqs,
                "magnitude": magnitudes_db.tolist(),
                "group_delay": group_delay.tolist(),
                "complex": values
            }
        }

        return result

    @classmethod
    def basic_analysis_ds_constellation_display(cls, measurement: Dict[str, Any]) -> ConstellationDisplayAnalysisModel:
        """
        Build a minimal constellation analysis payload from a downstream OFDM
        measurement dictionary.

        Parameters
        ----------
        measurement : dict
            Expected keys (subset):
                - ``samples`` : ComplexArray (list of [real, imag]); required
                - ``pnm_header`` : dict
                - ``mac_address`` : str
                - ``channel_id`` : int
                - ``num_sample_symbols`` : int (defaults to len(samples))
                - ``actual_modulation_order`` : int | str (e.g., 256 or "QAM-256")

        Returns
        -------
        ConstellationDisplayAnalysisModel
            Typed model carrying device/header info, inferred QAM order,
            and hard/soft decision coordinates (scaled).

        Raises
        ------
        ValueError
            If ``samples`` is missing or empty.
        """
        samples: ComplexArray   = measurement.get("samples") or []
        if not samples:
            raise ValueError("measurement['values'] is required and must be a non-empty ComplexArray.")

        #Get Hard/Soft Decsions
        amo:int                 = measurement.get("actual_modulation_order", DsOfdmModulationType.UNKNOWN)
        qm:QamModulation    = QamModulation.from_DsOfdmModulationType(amo)
        hard                = QamLutManager().get_hard_decisions(qm)
        soft                = QamLutManager().scale_soft_decisions(qm, samples)

        return ConstellationDisplayAnalysisModel(
            device_details      = measurement.get("device_details", SystemDescriptor.empty()),
            pnm_header          = measurement.get("pnm_header", {}),
            mac_address         = measurement.get("mac_address", MacAddress.null()),
            channel_id          = measurement.get("channel_id", INVALID_CHANNEL_ID),
            num_sample_symbols  = measurement.get("num_sample_symbols", len(samples)),
            modulation_order    = qm,           # QamModulation 
            hard                = hard,         # Scaled
            soft                = soft          # Scaled
        )

    @classmethod
    def basic_analysis_ds_histogram(cls, measurement: Dict[str, Any]) -> DsHistogramAnalysisModel:
        """
        Build a :class:`DsHistogramAnalysisModel` from a downstream histogram payload.

        Parameters
        ----------
        measurement : dict
            Expected keys (subset):
                - ``device_details`` : dict
                - ``pnm_header`` : dict
                - ``mac_address`` : str
                - ``channel_id`` : int
                - ``symmetry`` : int
                - ``dwell_count`` : int
                - ``hit_counts`` : List[int]

        Returns
        -------
        DsHistogramAnalysisModel
            Typed model with histogram metrics and metadata.
        """
        return DsHistogramAnalysisModel(
            device_details  = measurement.get("device_details", SystemDescriptor.empty()),
            pnm_header      = measurement.get("pnm_header", {}),
            mac_address     = measurement.get("mac_address", MacAddress.null()),
            channel_id      = measurement.get("channel_id", INVALID_CHANNEL_ID),
            symmetry        = measurement.get("symmetry", INVALID_CHANNEL_ID),
            dwell_count     = measurement.get("dwell_count_values", INVALID_CHANNEL_ID),
            hit_counts      = measurement.get("hit_count_values", []),
        )

    @classmethod
    def basic_analysis_ds_ofdm_fec_summary(cls, measurement: Dict[str, Any]) -> OfdmFecSummaryAnalysisModel:
        """
        Build an :class:`OfdmFecSummaryAnalysisModel` from a DS OFDM FEC summary payload.

        Expected input (keys are case-sensitive)
        ----------------------------------------
        {
            "device_details": {"sys_descr": {...}},
            "pnm_header": {...},
            "channel_id": int,
            "mac_address": "xx:xx:xx:xx:xx:xx",
            "summary_type": int,                # e.g., 2 | 3 (aggregation code)
            "num_profiles": int,
            "fec_summary_data": [
                {
                    "profile_id": int,
                    "number_of_sets": int,
                    "codeword_entries": {
                        "timestamp": List[int],
                        "total_codewords": List[int],
                        "corrected": List[int],
                        "uncorrected": List[int]
                    }
                },
                ...
            ]
        }

        Behavior
        --------
        - Coerces all codeword series to ints.
        - If series lengths differ, truncates to the shortest and logs a warning.
        - Uses the **computed** series length for ``number_of_sets`` (logs if it disagrees with declared).

        Parameters
        ----------
        measurement : dict
            DS OFDM FEC summary structure as shown above.

        Returns
        -------
        OfdmFecSummaryAnalysisModel
            Collection of per-profile codeword time-series aligned by shortest length,
            plus header/device metadata.

        Notes
        -----
        The top-level ``num_profiles`` is compared with the actual parsed count and
        differences are logged at DEBUG level.
        """
        log = logging.getLogger(getattr(cls, "__name__", "OfdmFecSummaryAnalysis"))

        profiles: List[OfdmFecSummaryProfileModel] = []

        for prof in (measurement.get("fec_summary_data") or []):
            profile_id: int = int(prof.get("profile_id", INVALID_CHANNEL_ID))
            declared_sets: int = int(prof.get("number_of_sets", 0))

            cwe: Dict[str, Any] = prof.get("codeword_entries") or {}

            # Extract parallel arrays and coerce to int lists
            ts_list:  List[int] = [int(x) for x in (cwe.get("timestamp") or [])]
            tot_list: List[int] = [int(x) for x in (cwe.get("total_codewords") or [])]
            cor_list: List[int] = [int(x) for x in (cwe.get("corrected") or [])]
            unc_list: List[int] = [int(x) for x in (cwe.get("uncorrected") or [])]

            # Enforce equal lengths by truncating to the shortest (robustness over hard failure)
            n = min(len(ts_list), len(tot_list), len(cor_list), len(unc_list)) if any(
                (ts_list, tot_list, cor_list, unc_list)
            ) else 0

            if n and any(len(lst) != n for lst in (ts_list, tot_list, cor_list, unc_list)):
                log.warning(
                    f"Profile {profile_id}: series length mismatch; truncating to {n} "
                    f"(ts={len(ts_list)}, total={len(tot_list)}, corrected={len(cor_list)}, uncorrected={len(unc_list)})"
                )
                ts_list, tot_list, cor_list, unc_list = (
                    ts_list[:n], tot_list[:n], cor_list[:n], unc_list[:n]
                )

            if declared_sets and declared_sets != n:
                log.debug(
                    f"Profile {profile_id}: number_of_sets declared={declared_sets}, computed={n}; using computed."
                )

            cw = FecSummaryCodeWordModel(
                timestamps      =ts_list,
                total_codewords =tot_list,
                corrected       =cor_list,
                uncorrected     =unc_list,
            )

            profiles.append(
                OfdmFecSummaryProfileModel(
                    profile         =profile_id,
                    number_of_sets  =n,
                    codewords       =cw,
                )
            )

        # Optional sanity check: header-declared num_profiles vs parsed count
        declared_num_profiles = int(measurement.get("num_profiles", len(profiles)))
        if declared_num_profiles != len(profiles):
            log.debug(f"num_profiles declared={declared_num_profiles}, parsed={len(profiles)}")

        return OfdmFecSummaryAnalysisModel(
            device_details      =measurement.get("device_details", SystemDescriptor.empty()),
            pnm_header          =measurement.get("pnm_header", {}),
            mac_address         =measurement.get("mac_address", MacAddress.null()),
            channel_id          =int(measurement.get("channel_id", INVALID_CHANNEL_ID)),
            profiles            =profiles,
        )
