# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia

from __future__ import annotations

import logging
import numpy as np

from enum import Enum
from typing import List, Dict, Any, Mapping, Sequence, Union, cast

from pypnm.api.routes.advance.analysis.signal_analysis.detection.echo.echo_detector import EchoDetector, EchoDetectorReport
from pypnm.api.routes.advance.analysis.signal_analysis.detection.echo.type import EchoDetectorType
from pypnm.api.routes.common.classes.analysis.model.chan_est_schema import ChanEstCarrierModel, DsChannelEstAnalysisModel
from pypnm.api.routes.common.classes.analysis.model.mod_profile_schema import (
    CarrierItemModel, CarrierValuesListModel, CarrierValuesModel, CarrierValuesSplitModel, 
    DsModulationProfileAnalysisModel, ProfileAnalysisEntryModel)
from pypnm.api.routes.common.classes.analysis.model.schema import (
    BaseAnalysisModel, ConstellationDisplayAnalysisModel, DsHistogramAnalysisModel, DsRxMerAnalysisModel, EchoDatasetModel, 
    FecSummaryCodeWordModel, GrpDelayStatsModel, OfdmFecSummaryAnalysisModel, OfdmFecSummaryProfileModel, 
    OfdmaUsPreEqCarrierModel, RegressionModel, RxMerCarrierValuesModel, UsOfdmaUsPreEqAnalysisModel)
from pypnm.api.routes.common.classes.analysis.model.spectrum_analyzer_schema import (
    DEFAULT_POINT_AVG, MagnitudeSeries, SpecAnaAnalysisResults, SpectrumAnalyzerAnalysisModel, WindowAverage)
from pypnm.api.routes.common.extended.common_messaging_service import MessageResponse
from pypnm.api.routes.docs.pnm.files.service import SystemConfigSettings
from pypnm.api.routes.docs.pnm.spectrumAnalyzer.schemas import SpecAnCapturePara
from pypnm.docsis.cm_snmp_operation import SystemDescriptor, Utils
from pypnm.lib.constants import CABLE_VF, INVALID_CHANNEL_ID, INVALID_PROFILE_ID, INVALID_SCHEMA_TYPE, INVALID_START_VALUE, SPEED_OF_LIGHT, CableType
from pypnm.lib.file_processor import FileProcessor
from pypnm.lib.log_files import LogFile
from pypnm.lib.mac_address import MacAddress
from pypnm.lib.qam.lut_mgr import QamLutManager
from pypnm.lib.qam.types import QamModulation
from pypnm.lib.signal_processing.averager import MovingAverage
from pypnm.lib.signal_processing.complex_array_ops import ComplexArrayOps
from pypnm.lib.signal_processing.group_delay import GroupDelay
from pypnm.lib.signal_processing.linear_regression import LinearRegression1D
from pypnm.lib.types import ArrayLike, ChannelId, ComplexArray, FloatSeries, FrequencyHz, FrequencySeriesHz, MacAddressStr
from pypnm.pnm.data_type.DocsIf3CmSpectrumAnalysisCtrlCmd import WindowFunction
from pypnm.pnm.data_type.DsOfdmModulationType import DsOfdmModulationType
from pypnm.pnm.lib.signal_statistics import SignalStatistics, SignalStatisticsModel
from pypnm.pnm.process.CmDsOfdmChanEstimateCoef import CmDsOfdmChanEstimateCoefModel, ComplexSeries
from pypnm.pnm.process.CmDsOfdmModulationProfile import (
    CmDsOfdmModulationProfile, CmDsOfdmModulationProfileModel, ModulationOrderType, 
    RangeModulationProfileSchemaModel, SkipModulationProfileSchemaModel)
from pypnm.pnm.process.pnm_file_type import PnmFileType
from pypnm.lib.signal_processing.shan.series import Shannon, ShannonSeries
from pypnm.lib.signal_processing.groupdelay.ofdm import (
    SpacedFrequencyAxisHz, GroupDelayOptions, SignConvention, OFDMGroupDelay)

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
    BASIC               = 0

class Analysis:
    """Core analysis runner.

    This orchestrator normalizes the payload's ``data`` into a list of
    measurement dictionaries and dispatches to the appropriate analysis
    routine based on the inferred PNM file type. For echo detection, the
    provided ``cable_type`` controls the velocity factor used to convert
    echo time delays to physical distances.

    Parameters
    ----------
    analysis_type : AnalysisType
        Selected analysis mode (e.g., ``AnalysisType.BASIC``).
    msg_response : MessageResponse
        Wrapped transport of the measurement payload; must expose
        ``payload_to_dict()`` with a top-level ``"data"`` entry.
    cable_type : CableType, default CableType.RG6
        Cable type used by echo-detection analysis to determine the
        propagation velocity factor for distance calculations.

    """

    def __init__(self, analysis_type: AnalysisType, 
                 msg_response: MessageResponse, 
                 cable_type: CableType = CableType.RG6) -> None:
        self.logger = logging.getLogger(f"{self.__class__.__name__}")
        self.analysis_type: "AnalysisType"      = analysis_type
        self.msg_response: "MessageResponse"    = msg_response
        self._cable_type: CableType             = cable_type
        payload: Dict[str, Any]                 = msg_response.payload_to_dict() or {}
        _raw_data                               = payload.get("data", [])
        self._result_model:List[BaseAnalysisModel] = []
        self._processed_pnm_type:List[PnmFileType] = []

        if isinstance(_raw_data, Mapping):
            self.measurement_data: List[Dict[str, Any]] = [dict(_raw_data)]
        elif isinstance(_raw_data, Sequence) and not isinstance(_raw_data, (str, bytes, bytearray)):
            self.measurement_data = [dict(m) for m in _raw_data]
        else:
            self.measurement_data = []

        self._analysis_dict: List[Dict[str, Any]] = []

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
                self.logger.error('PNM FileType not Found')
                LogFile.write(fname=f'rxmer-analysis-measurment-{Utils.time_stamp()}.dict' , data=measurement)
                pass

            if self.analysis_type == AnalysisType.BASIC:
                self.logger.debug(f'Performing Basic Analysis on PNM: {pnm_file_type} on Channel: {channel_id}')
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

        """
        if pnm_file_type == PnmFileType.OFDM_CHANNEL_ESTIMATE_COEFFICIENT.value:
            self.logger.debug("Processing: OFDM_CHANNEL_ESTIMATE_COEFFICIENT")
            model = self.basic_analysis_ds_chan_est(measurement)
            self.__update_result_model(model)
            self.__update_result_dict(model.model_dump())
            self.__add_pnmType(PnmFileType.OFDM_CHANNEL_ESTIMATE_COEFFICIENT)

        elif pnm_file_type == PnmFileType.DOWNSTREAM_CONSTELLATION_DISPLAY.value:
            self.logger.debug("Processing: DOWNSTREAM_CONSTELLATION_DISPLAY")
            model = self.basic_analysis_ds_constellation_display(measurement)
            self.__update_result_model(model)
            self.__update_result_dict(model.model_dump())
            self.__add_pnmType(PnmFileType.DOWNSTREAM_CONSTELLATION_DISPLAY) 

        elif pnm_file_type == PnmFileType.RECEIVE_MODULATION_ERROR_RATIO.value:
            self.logger.info("Processing: RECEIVE_MODULATION_ERROR_RATIO")
            model:DsRxMerAnalysisModel = self.basic_analysis_rxmer(measurement)
            self.__update_result_model(model)
            self.__update_result_dict(model.model_dump())
            self.__add_pnmType(PnmFileType.RECEIVE_MODULATION_ERROR_RATIO)             

        elif pnm_file_type == PnmFileType.DOWNSTREAM_HISTOGRAM.value:
            self.logger.debug("Processing: DOWNSTREAM_HISTOGRAM")
            model = self.basic_analysis_ds_histogram(measurement)
            self.__update_result_model(model)
            self.__update_result_dict(model.model_dump())
            self.__add_pnmType(PnmFileType.DOWNSTREAM_HISTOGRAM)

        elif pnm_file_type == PnmFileType.UPSTREAM_PRE_EQUALIZER_COEFFICIENTS.value:
            self.logger.debug("Processing: UPSTREAM_PRE_EQUALIZER_COEFFICIENTS")
            model = self.basic_analysis_us_ofdma_pre_equalization(measurement)
            self.__update_result_model(model)
            self.__update_result_dict(model.model_dump())
            self.__add_pnmType(PnmFileType.UPSTREAM_PRE_EQUALIZER_COEFFICIENTS)   
  
        elif pnm_file_type == PnmFileType.UPSTREAM_PRE_EQUALIZER_COEFFICIENTS_LAST_UPDATE.value:
            self.logger.debug("Stub: Processing: UPSTREAM_PRE_EQUALIZER_COEFFICIENTS_LAST_UPDATE")
            # model = self.basic_analysis_us_ofdma_pre_equalization(measurement)
            # self.__update_result_model(model)
            # self.__update_result_dict(model.model_dump())
            # self.__add_pnmType(PnmFileType.UPSTREAM_PRE_EQUALIZER_COEFFICIENTS)             
            pass

        elif pnm_file_type == PnmFileType.OFDM_FEC_SUMMARY.value:
            self.logger.debug("Processing: OFDM_FEC_SUMMARY")
            model = self.basic_analysis_ds_ofdm_fec_summary(measurement)
            self.__update_result_model(model)
            self.__update_result_dict(model.model_dump())
            self.__add_pnmType(PnmFileType.OFDM_FEC_SUMMARY)

        elif pnm_file_type == PnmFileType.SPECTRUM_ANALYSIS.value:
            self.logger.debug("Processing: SPECTRUM_ANALYSIS")
            model = self.basic_analysis_spectrum_analyzer(measurement)
            self.__update_result_model(model)
            self.__update_result_dict(model.model_dump())
            self.__add_pnmType(PnmFileType.SPECTRUM_ANALYSIS)

        elif pnm_file_type == PnmFileType.OFDM_MODULATION_PROFILE.value:
            self.logger.debug("Processing: OFDM_MODULATION_PROFILE")
            model = self.basic_analysis_ds_modulation_profile(measurement)
            self.__update_result_model(model)
            self.__update_result_dict(model.model_dump())
            self.__add_pnmType(PnmFileType.OFDM_MODULATION_PROFILE)             

        elif pnm_file_type == PnmFileType.LATENCY_REPORT.value:
            self.logger.warning("Stub: Processing: LATENCY_REPORT")
            self.__add_pnmType(PnmFileType.LATENCY_REPORT) 
            pass

        else:
            self.logger.error(f"Unknown PNM file type: ({pnm_file_type})")

    def get_pnm_type(self) -> List[PnmFileType]: 
        return self._processed_pnm_type

    def get_results(self, full_dict: bool = True) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
        """
        Return accumulated analysis results.

        Behavior
        --------
        - full_dict=True  -> always: {"analysis": [dict, dict, ...]}
        - full_dict=False -> if exactly one result: dict
                            else: {"analysis": [dict, dict, ...]}
        """
        results: List[Dict[str, Any]] = self._analysis_dict

        if full_dict:
            return {"analysis": results}

        if len(results) == 1 and isinstance(results[0], dict):
            return results[0]

        return {"analysis": results}

    def get_model(self) -> Union[BaseAnalysisModel, List[BaseAnalysisModel]]:
        """Get the accumulated analysis results (typed models).

        Returns
        -------
        BaseAnalysisModel or list of BaseAnalysisModel
            The collected Pydantic models for analyses that produce them.
        """
        return self._result_model

    def get_dicts(self) -> List[Dict[str,Any]]:
        return self._analysis_dict

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
    
    def __update_result_dict(self, model_dict:Dict[str,Any]):
        """Append a plain-dict analysis result to the results cache.

        Parameters
        ----------
        model : dict
            The dictionary result to record.
        """
        self._analysis_dict.append(model_dict)

    def __add_pnmType(self, pft:PnmFileType):
        self._processed_pnm_type.append(pft)

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
        freqs:FloatSeries = [base_freq + (i * subcarrier_spacing) for i in range(len(values))]
        magnitudes:FloatSeries = values

        def classify(v: int) -> int:
            if v == RXMER_EXCLUSION:
                return int(RxMerCarrierType.EXCLUSION.value)
            elif v in (RXMER_CLIPPED_LOW, RXMER_CLIPPED_HIGH):
                return int(RxMerCarrierType.CLIPPED.value)
            else:
                return int(RxMerCarrierType.NORMAL.value)

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
            carrier_status      = carrier_status)

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
    def basic_analysis_ds_modulation_profile(cls, measurement: Mapping[str, Any], split_carriers: bool = True) -> DsModulationProfileAnalysisModel:
        """
        Analyze the Downstream OFDM Modulation Profile and return a typed model.

        Parameters
        ----------
        measurement : Mapping[str, Any]
            Expected keys (subset):
            - subcarrier_spacing : int (Hz)
            - first_active_subcarrier_index : int
            - subcarrier_zero_frequency : int (Hz)
            - mac_address : str
            - channel_id : int
            - device_details : Mapping[str, Any] (optional passthrough)
            - pnm_header : Mapping[str, Any] (optional passthrough)
            - profiles : list of dicts:
                    {
                        "profile_id": int,
                        "schemes": list[SchemeModel-like]
                    }

            Each scheme item is one of:
            - schema_type = 0 (range):
                    { 
                        "schema_type": 0,
                        "modulation_order": "qam_256" | "plc" | "exclusion" | "continuous_pilot" | ...,
                        "num_subcarriers": int 
                    }
            - schema_type = 1 (skip):
                    { 
                        "schema_type": 1,
                        "main_modulation_order": "...",
                        "skip_modulation_order": "...",
                        "num_subcarriers": int 
                    }

        split_carriers : bool, default True
            Controls how per-carrier results are represented in the output:

            * True  → **split layout** (compact parallel arrays). Best for fast analytics,
                    vectorized ops, plotting, and storage efficiency.
            * False → **list layout** (verbose per-carrier records). Best for inspection/logging.

        Returns
        -------
        DsModulationProfileAnalysisModel

        Raises
        ------
        ValueError
            If spacing/indices/frequencies are invalid.
        """
        spacing: int       = int(measurement.get("subcarrier_spacing", INVALID_START_VALUE))
        active_index: int  = int(measurement.get("first_active_subcarrier_index", INVALID_START_VALUE))
        zero_freq: int     = int(measurement.get("subcarrier_zero_frequency", INVALID_START_VALUE))

        if active_index < 0 or zero_freq < 0 or spacing <= 0:
            raise ValueError(
                f"Invalid parameters: spacing={spacing}, active_index={active_index}, zero_freq={zero_freq}")

        #Calculate Start Frequency
        start_freq = zero_freq + spacing * active_index

        out = DsModulationProfileAnalysisModel(
            device_details      = measurement.get("device_details", {}),
            pnm_header          = measurement.get("pnm_header", {}),
            mac_address         = str(measurement.get("mac_address", MacAddress.null())),
            channel_id          = int(measurement.get("channel_id", INVALID_CHANNEL_ID)),
            frequency_unit      = "Hz",
            shannon_min_unit    = "dB",
            profiles            = [],
        )

        # --- Per-profile assembly ---
        for profile in measurement.get("profiles", []) or []:
            profile_id  = int(profile.get("profile_id", INVALID_PROFILE_ID))
            schemes     = profile.get("schemes", []) or []

            freq_list: FrequencySeriesHz    = []
            mod_list:  List[str]    = []
            shan_list: List[float]  = []
            carrier_items: List[CarrierItemModel] = []

            freq_ptr = start_freq

            for scheme in schemes:
                schema_type = int(scheme.get("schema_type", INVALID_SCHEMA_TYPE))

                # Determine which modulation name & count to use
                if schema_type == CmDsOfdmModulationProfile.RANGE_MODULATION:
                    mod_name: str   = str(scheme.get("modulation_order"))
                    count: int      = int(scheme.get("num_subcarriers", 0))

                elif schema_type == CmDsOfdmModulationProfile.SKIP_MODULATION:
                    mod_name = str(scheme.get("main_modulation_order"))
                    count    = int(scheme.get("num_subcarriers", 0))
                
                else:
                    # Unknown schema; skip conservatively
                    logging.warning(f'basic_analysis_ds_modulation_profile() -> Unknown Schema: {schema_type}')
                    continue

                for _ in range(count):
                    # Compute Shannon minimum MER (perfect FEC) per modulation-order-type

                    if mod_name in (ModulationOrderType.continuous_pilot.name, 
                                    ModulationOrderType.exclusion.name):
                        s_min = 0.0

                    elif mod_name == ModulationOrderType.plc.name:
                        # Treat PLC as 16-QAM (4 bits/s/Hz) at the Shannon min
                        s_min = Shannon.bits_to_snr(4)
                    
                    else:
                        # Map strings like 'qam_256' → Shannon SNR (dB)
                        s_min = Shannon.snr_from_modulation(mod_name)

                    s_min = round(float(s_min), 2)
                    f_val = int(freq_ptr)

                    if split_carriers:
                        freq_list.append(f_val)
                        mod_list.append(mod_name)
                        shan_list.append(s_min)
                    else:
                        carrier_items.append(
                            CarrierItemModel(
                                frequency       = f_val,
                                modulation      = mod_name,
                                shannon_min_mer = s_min,
                            )
                        )

                    freq_ptr += spacing

            # Attach carrier values according to layout
            if split_carriers:
                carrier_values: CarrierValuesModel = CarrierValuesSplitModel(
                    layout          =   "split",
                    frequency       =   freq_list,
                    modulation      =   mod_list,
                    shannon_min_mer =   shan_list,
                )

            else:
                carrier_values = CarrierValuesListModel(
                    layout      =   "list",
                    carriers    =   carrier_items,
                )

            out.profiles.append(
                ProfileAnalysisEntryModel(
                    profile_id      =   profile_id,
                    carrier_values  =   carrier_values,
                )
            )

        return out

    @classmethod
    def basic_analysis_us_ofdma_pre_equalization(cls, measurement: Dict[str, Any]) -> UsOfdmaUsPreEqAnalysisModel:
        """
        Perform basic analysis of upstream OFDMA pre-equalization data and return a typed model.

        Computes:
        - Per-carrier frequency (Hz)
        - Magnitude (dB) from complex coefficients
        - Group delay (µs) from unwrapped phase gradient
        - Complex samples passthrough
        - Signal statistics over the magnitude sequence
        """
        # --- inputs / sanity ---
        spacing: int                    = int(measurement.get("subcarrier_spacing", 0))               
        active_index: int               = int(measurement.get("first_active_subcarrier_index", 0))
        zero_freq: int                  = int(measurement.get("subcarrier_zero_frequency", 0))        
        base_freq: int                  = zero_freq + (spacing * active_index)

        values: ComplexArray            = measurement.get("values", [])
        if not values:
            raise ValueError("No complex channel estimation values provided in measurement.")

        # --- core calculations ---
        complex_values                  = np.array([complex(r, i) for r, i in values], dtype=complex)
        magnitudes_db                   = 20.0 * np.log10(np.abs(complex_values) + 1e-12)             

        # Group delay  (τ = - dφ/df).  φ from unwrapped angle; spacing in Hz → τ in microseconds
        phase                           = np.unwrap(np.angle(complex_values))
        group_delay_us                  = -np.gradient(phase, spacing) * 1e6                          
        freqs: List[int]                = [base_freq + i * spacing for i in range(len(complex_values))]
        complex_ndim: int               = int(np.asarray(values, dtype=complex).ndim)

        # --- models: nested blocks ---
        grp_delay_model: GrpDelayStatsModel = GrpDelayStatsModel(
            group_delay_unit            = "microsecond",
            magnitude                   = group_delay_us.tolist(),
        )

        carrier_values: OfdmaUsPreEqCarrierModel = OfdmaUsPreEqCarrierModel(
            carrier_count               = len(freqs),
            frequency_unit              = "Hz",
            frequency                   = freqs,
            complex                     = values,
            complex_dimension           = complex_ndim,
            magnitudes                  = magnitudes_db.tolist(),
            group_delay                 = grp_delay_model,
            occupied_channel_bandwidth  = int(measurement.get("occupied_channel_bandwidth", 0)),
        )

        # Signal statistics over magnitudes (dB)
        signal_stats_model: SignalStatisticsModel = SignalStatistics(magnitudes_db.tolist()).compute()

        # --- assemble top-level analysis model ---
        result_model: UsOfdmaUsPreEqAnalysisModel = UsOfdmaUsPreEqAnalysisModel(
            device_details              = measurement.get("device_details", {}),
            pnm_header                  = measurement.get("pnm_header", {}),
            mac_address                 = str(measurement.get("mac_address", "")),
            channel_id                  = int(measurement.get("channel_id", 0)),
            subcarrier_spacing          = spacing,
            first_active_subcarrier_index = active_index,
            subcarrier_zero_frequency   = zero_freq,
            carrier_values              = carrier_values,
            signal_statistics           = signal_stats_model,
        )

        return result_model

    @classmethod
    def basic_analysis_ds_constellation_display(cls, measurement: Dict[str, Any]) -> ConstellationDisplayAnalysisModel:
        """
        Build a minimal constellation analysis payload from a downstream OFDM
        measurement dictionary.

        CM Output Assumption
        --------------------
        The DOCSIS spec states the constellation display samples are provided as
        s2.13 **soft decisions scaled to ~unit average power** at the slicer input.
        Because your LUT hard points are likewise normalized, **do not rescale**
        the CM-provided soft points here.

        Parameters
        ----------
        measurement : dict
            Expected keys (subset):
            - ``samples`` : ComplexArray (list of [real, imag]) — required
            - ``pnm_header`` : dict
            - ``mac_address`` : str
            - ``channel_id`` : int
            - ``num_sample_symbols`` : int (defaults to len(samples))
            - ``actual_modulation_order`` : int | str (e.g., 256 or "QAM-256")

        Returns
        -------
        ConstellationDisplayAnalysisModel
            Typed model carrying device/header info, inferred QAM order,
            **hard** constellation points from the LUT, and the **unscaled soft**
            decision coordinates provided by the CM.

        Raises
        ------
        ValueError
            If ``samples`` is missing or empty.
        """
        samples: ComplexArray = measurement.get("samples") or []
        if not samples:
            raise ValueError("measurement['samples'] is required and must be a non-empty ComplexArray.")

        # Map actual modulation order → QamModulation
        amo: int | str = measurement.get("actual_modulation_order", DsOfdmModulationType.UNKNOWN)
        qm: QamModulation = QamModulation.from_DsOfdmModulationType(amo)

        # Hard points come from LUT (already normalized)
        hard = QamLutManager().get_hard_decisions(qm)

        # IMPORTANT: Do NOT rescale the CM soft decisions; they are already unit-power normalized (s2.13).
        soft = samples

        return ConstellationDisplayAnalysisModel(
            device_details      = measurement.get("device_details", SystemDescriptor.empty()),
            pnm_header          = measurement.get("pnm_header", {}),
            mac_address         = measurement.get("mac_address", MacAddress.null()),
            channel_id          = measurement.get("channel_id", INVALID_CHANNEL_ID),
            num_sample_symbols  = measurement.get("num_sample_symbols", len(samples)),
            modulation_order    = qm,       # QamModulation
            hard                = hard,     # LUT hard points (normalized)
            soft                = soft      # CM soft decisions (already normalized) ← changed
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
            "device_details": {"system_description": {...}},
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
            profile_id: int     = int(prof.get("profile_id", INVALID_CHANNEL_ID))
            declared_sets: int  = int(prof.get("number_of_sets", 0))
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
                timestamps      =   ts_list,
                total_codewords =   tot_list,
                corrected       =   cor_list,
                uncorrected     =   unc_list,
            )

            profiles.append(
                OfdmFecSummaryProfileModel(
                    profile         =   profile_id,
                    number_of_sets  =   n,
                    codewords       =   cw,
                )
            )

        # Optional sanity check: header-declared num_profiles vs parsed count
        declared_num_profiles = int(measurement.get("num_profiles", len(profiles)))
        if declared_num_profiles != len(profiles):
            log.debug(f"num_profiles declared={declared_num_profiles}, parsed={len(profiles)}")

        return OfdmFecSummaryAnalysisModel(
            device_details      =   measurement.get("device_details", SystemDescriptor.empty()),
            pnm_header          =   measurement.get("pnm_header", {}),
            mac_address         =   measurement.get("mac_address", MacAddress.null()),
            channel_id          =   int(measurement.get("channel_id", INVALID_CHANNEL_ID)),
            profiles            =   profiles,
        )

    @classmethod
    def basic_analysis_spectrum_analyzer(cls, measurement: Dict[str, Any]) -> SpectrumAnalyzerAnalysisModel:
        """
        Build SpectrumAnalyzerAnalysisModel from converted PNM measurement:
        """
        # --- core params ---
        first_seg_cf  = int(measurement.get("first_segment_center_frequency", 0))
        last_seg_cf   = int(measurement.get("last_segment_center_frequency", 0))
        seg_span_hz   = int(measurement.get("segment_frequency_span", 0))
        bins_per_seg  = int(measurement.get("num_bins_per_segment", 0))
        enbw_hz       = float(measurement.get("equivalent_noise_bandwidth", 0.0))
        noise_bw_khz  = int(round(enbw_hz / 1_000.0)) if enbw_hz > 0.0 else 0

        wf_raw        = int(measurement.get("window_function", WindowFunction.HANN.value))
        try:
            wf_enum: WindowFunction = WindowFunction(wf_raw)
        except Exception:
            wf_enum = WindowFunction.HANN

        bin_bw = int(measurement.get("bin_frequency_spacing", 0))
        if bin_bw <= 0 and seg_span_hz > 0 and bins_per_seg > 0:
            bin_bw = max(1, seg_span_hz // bins_per_seg)

        # --- segments & magnitudes ---
        segments = measurement.get("amplitude_bin_segments_float", [])
        num_segments = len(segments)
        if bins_per_seg <= 0 and num_segments:
            bins_per_seg = len(segments[0])

        # Normalize each segment length to bins_per_seg (clip/pad NaN)
        norm_segments: List[List[float]] = []
        for s in segments:
            if len(s) >= bins_per_seg:
                norm_segments.append([float(x) for x in s[:bins_per_seg]])
            else:
                pad = [float("nan")] * (bins_per_seg - len(s))
                norm_segments.append([float(x) for x in s] + pad)

        magnitudes: MagnitudeSeries = [x for seg in norm_segments for x in seg]

        # --- compute frequency axis across segments ---
        frequencies: FrequencySeriesHz = []
        if num_segments > 0 and bins_per_seg > 0 and seg_span_hz > 0 and bin_bw > 0 and first_seg_cf > 0:
            seg_step_hz = (last_seg_cf - first_seg_cf) // (num_segments - 1) if num_segments > 1 else 0
            # start at center - span/2, align to bin center with +bin_bw/2
            seg0_start = first_seg_cf - (seg_span_hz // 2) + (bin_bw // 2)

            freqs: List[int] = []
            for s_idx in range(num_segments):
                start_hz = seg0_start + s_idx * seg_step_hz
                freqs.extend(int(start_hz + i * bin_bw) for i in range(bins_per_seg))
            frequencies = cast(FloatSeries, freqs)

        # --- align lengths (trim to shortest) ---
        if frequencies and magnitudes and len(frequencies) != len(magnitudes):
            n = min(len(frequencies), len(magnitudes))
            frequencies = frequencies[:n]
            magnitudes  = magnitudes[:n]
        if not frequencies or not magnitudes:
            frequencies, magnitudes = [], []

        # --- windowed average (same length) ---
        window_points  = int(measurement.get("window_average_points", DEFAULT_POINT_AVG))
        try:
            ma = MovingAverage(max(1, window_points), mode="reflect")
            smoothed = ma.apply(magnitudes) if magnitudes else []
        except Exception:
            smoothed = list(magnitudes)

        if len(smoothed) != len(frequencies):
            smoothed = smoothed[:len(frequencies)]

        window_avg = WindowAverage(points=max(1, window_points), magnitudes=smoothed)

        results = SpecAnaAnalysisResults(
            bin_bandwidth  = bin_bw,
            segment_length = bins_per_seg,
            frequencies    = frequencies,
            magnitudes     = magnitudes,
            window_average = window_avg,
        )

        capture_parameters: SpecAnCapturePara = SpecAnCapturePara(
            first_segment_center_freq = first_seg_cf,
            last_segment_center_freq  = last_seg_cf,
            segment_freq_span         = seg_span_hz,
            num_bins_per_segment      = bins_per_seg,
            noise_bw                  = noise_bw_khz,
            window_function           = wf_enum,
        )

        return SpectrumAnalyzerAnalysisModel(
            device_details     = measurement.get("device_details", SystemDescriptor.empty()),
            pnm_header         = measurement.get("pnm_header", {}),
            mac_address        = measurement.get("mac_address", MacAddress.null()),
            channel_id         = int(measurement.get("channel_id", 0)),
            capture_parameters = capture_parameters,
            signal_analysis    = results,
        )

#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++#

    @classmethod
    def basic_analysis_ds_modulation_profile_from_model(cls, model: CmDsOfdmModulationProfileModel, 
                                                        split_carriers: bool = True) -> DsModulationProfileAnalysisModel:
        """
        Analyze a Downstream OFDM Modulation Profile using a parsed model
        from :class:`CmDsOfdmModulationProfile`.
        """
        spacing: int      = int(model.subcarrier_spacing)
        active_index: int = int(model.first_active_subcarrier_index)
        zero_freq: int    = int(model.subcarrier_zero_frequency)

        if active_index < 0 or zero_freq < 0 or spacing <= 0:
            raise ValueError(
                f"Invalid parameters: spacing={spacing}, active_index={active_index}, zero_freq={zero_freq}")

        start_freq = zero_freq + spacing * active_index

        result = DsModulationProfileAnalysisModel(
            device_details      = {},
            pnm_header          = model.pnm_header.model_dump() if hasattr(model.pnm_header, "model_dump") else {},
            mac_address         = str(model.mac_address),
            channel_id          = int(model.channel_id),
            frequency_unit      = "Hz",
            shannon_min_unit    = "dB",
            profiles            = [],
        )

        for profile in model.profiles:
            profile_id = int(profile.profile_id)
            freq_list: FrequencySeriesHz = []
            mod_list: list[str] = []
            shan_list: list[float] = []
            carrier_items: list[CarrierItemModel] = []
            freq_ptr = start_freq

            for scheme in profile.schemes:
                # ---- branch by schema type / model ----
                if isinstance(scheme, RangeModulationProfileSchemaModel):
                    mod_name = str(scheme.modulation_order)
                    count = int(scheme.num_subcarriers)

                elif isinstance(scheme, SkipModulationProfileSchemaModel):
                    mod_name = str(scheme.main_modulation_order)
                    count = int(scheme.num_subcarriers)

                else:
                    logging.warning(
                        f"Unknown modulation profile schema type: {getattr(scheme, 'schema_type', '?')}"
                    )
                    continue

                for _ in range(count):
                    if mod_name in (
                        ModulationOrderType.continuous_pilot.name,
                        ModulationOrderType.exclusion.name,
                    ):
                        s_min = 0.0
                    elif mod_name == ModulationOrderType.plc.name:
                        s_min = Shannon.bits_to_snr(4)
                    else:
                        s_min = Shannon.snr_from_modulation(mod_name)

                    s_min = round(float(s_min), 2)
                    f_val = int(freq_ptr)

                    if split_carriers:
                        freq_list.append(f_val)
                        mod_list.append(mod_name)
                        shan_list.append(s_min)
                    else:
                        carrier_items.append(
                            CarrierItemModel(
                                frequency       = f_val,
                                modulation      = mod_name,
                                shannon_min_mer = s_min,
                            )
                        )
                    freq_ptr += spacing

            if split_carriers:
                carrier_values: CarrierValuesModel = CarrierValuesSplitModel(
                    layout          = "split",
                    frequency       = freq_list,
                    modulation      = mod_list,
                    shannon_min_mer = shan_list,
                )
            else:
                carrier_values = CarrierValuesListModel(
                    layout      = "list",
                    carriers    = carrier_items,
                )

            result.profiles.append(
                ProfileAnalysisEntryModel(
                    profile_id      = profile_id,
                    carrier_values  = carrier_values,
                )
            )

        return result
    
    @classmethod
    def basic_analysis_ds_chan_est_from_model_DEPRECATE(cls, model: CmDsOfdmChanEstimateCoefModel) -> DsChannelEstAnalysisModel:
        """
        Model-based variant of downstream channel estimation analysis.

        Parameters
        ----------
        model : CmDsOfdmChanEstimateCoefModel
            Parsed coefficients + metadata for DS OFDM channel estimation.

        Returns
        -------
        DsChannelEstAnalysisModel
            Typed analysis result identical in shape to the dict-based version.

        Raises
        ------
        ValueError
            If required parameters are invalid or values are empty.
        """
        subcarrier_spacing: int                 = int(getattr(model, "subcarrier_spacing", INVALID_START_VALUE))
        first_active_subcarrier_index: int      = int(getattr(model, "first_active_subcarrier_index", INVALID_START_VALUE))
        subcarrier_zero_frequency: FrequencyHz  = cast(FrequencyHz, int(getattr(model, "subcarrier_zero_frequency", INVALID_START_VALUE)))
        occupied_channel_bandwidth: int         = int(getattr(model, "occupied_channel_bandwidth", 0))

        if (first_active_subcarrier_index < 0) or (subcarrier_zero_frequency < 0) or (subcarrier_spacing <= 0):
            raise ValueError(
                f"Active index: {first_active_subcarrier_index} or "
                f"zero frequency: {subcarrier_zero_frequency} or "
                f"spacing: {subcarrier_spacing} must be non-negative"
            )

        values: ComplexArray = cast(ComplexArray, getattr(model, "values", []))
        if not values:
            raise ValueError("No complex channel estimation values provided in model.")

        start_freq: int  = (subcarrier_spacing * first_active_subcarrier_index) + subcarrier_zero_frequency
        freqs: List[int] = [start_freq + (i * subcarrier_spacing) for i in range(len(values))]

        gd = GroupDelay.from_channel_estimate(Hhat=values, df_hz=subcarrier_spacing, f0_hz=start_freq)
        gd_results = gd.to_result()

        # --- magnitudes (power in dB from complex coefficients) ---
        cao = ComplexArrayOps(values)
        magnitudes_db: FloatSeries = cao.to_list(cao.power_db())

        # --- signal statistics on magnitudes ---
        signal_stats_model = SignalStatistics(magnitudes_db).compute()

        # --- complex dimensionality (metadata only) ---
        complex_ndim: int = int(np.asarray(values, dtype=complex).ndim)

        # --- nested models ---
        group_delay_stats: GrpDelayStatsModel = GrpDelayStatsModel(
            group_delay_unit    =   "microsecond",
            magnitude           =   ComplexArrayOps.to_list(gd_results.group_delay_us),
        )

        carrier_values: ChanEstCarrierModel = ChanEstCarrierModel(
            carrier_count               =   len(freqs),
            frequency_unit              =   "Hz",
            frequency                   =   freqs,
            complex                     =   values,
            complex_dimension           =   complex_ndim,
            magnitudes                  =   magnitudes_db,
            group_delay                 =   group_delay_stats,
            occupied_channel_bandwidth  =   occupied_channel_bandwidth,)

        # --- assemble top-level result ---
        result_model: DsChannelEstAnalysisModel = DsChannelEstAnalysisModel(
            device_details                  =   getattr(model, "device_details", {}),  # model may not carry device details
            pnm_header                      =   model.pnm_header.model_dump() if hasattr(model.pnm_header, "model_dump") else {},
            mac_address                     =   cast(MacAddressStr, getattr(model, "mac_address", "")),
            channel_id                      =   cast(ChannelId, int(getattr(model, "channel_id", INVALID_START_VALUE))),
            subcarrier_spacing              =   subcarrier_spacing,
            first_active_subcarrier_index   =   first_active_subcarrier_index,
            subcarrier_zero_frequency       =   subcarrier_zero_frequency,
            carrier_values                  =   carrier_values,
            signal_statistics               =   signal_stats_model,)

        return result_model

    @classmethod
    def basic_analysis_ds_chan_est_from_model(cls, model: CmDsOfdmChanEstimateCoefModel) -> DsChannelEstAnalysisModel:
        """
        Model-based variant of downstream channel estimation analysis.

        Parameters
        ----------
        model : CmDsOfdmChanEstimateCoefModel
            Parsed coefficients + metadata for DS OFDM channel estimation.

        Returns
        -------
        DsChannelEstAnalysisModel
            Typed analysis result identical in shape to the dict-based version.

        Raises
        ------
        ValueError
            If required parameters are invalid or values are empty.
        """
        subcarrier_spacing: int                 = int(getattr(model, "subcarrier_spacing", INVALID_START_VALUE))
        first_active_subcarrier_index: int      = int(getattr(model, "first_active_subcarrier_index", INVALID_START_VALUE))
        subcarrier_zero_frequency: FrequencyHz  = cast(FrequencyHz, int(getattr(model, "subcarrier_zero_frequency", INVALID_START_VALUE)))
        occupied_channel_bandwidth: int         = int(getattr(model, "occupied_channel_bandwidth", 0))

        if (first_active_subcarrier_index < 0) or (subcarrier_zero_frequency < 0) or (subcarrier_spacing <= 0):
            raise ValueError(
                f"Active index: {first_active_subcarrier_index} or "
                f"zero frequency: {subcarrier_zero_frequency} or "
                f"spacing: {subcarrier_spacing} must be non-negative"
            )

        values: ComplexArray = cast(ComplexArray, getattr(model, "values", []))
        if not values:
            raise ValueError("No complex channel estimation values provided in model.")

        start_freq: int  = (subcarrier_spacing * first_active_subcarrier_index) + subcarrier_zero_frequency
        freqs: List[int] = [start_freq + (i * subcarrier_spacing) for i in range(len(values))]

        # ── Group delay via OFDMGroupDelay ──
        H_complex: ComplexSeries = [complex(r, i) for r, i in values]
        axis = SpacedFrequencyAxisHz(f0_hz=FrequencyHz(int(start_freq)), df_hz=float(subcarrier_spacing))
        gd_full = OFDMGroupDelay(
            H       = H_complex,
            axis    = axis,
            options = GroupDelayOptions(sign=SignConvention.PLUS)
        ).result()

        # --- magnitudes (power in dB from complex coefficients) ---
        cao = ComplexArrayOps(values)
        magnitudes_db: FloatSeries = cao.to_list(cao.power_db())

        # --- signal statistics on magnitudes ---
        signal_stats_model = SignalStatistics(magnitudes_db).compute()

        # --- complex dimensionality (metadata only) ---
        complex_ndim: int = int(np.asarray(values, dtype=complex).ndim)

        # --- nested models ---
        group_delay_stats: GrpDelayStatsModel = GrpDelayStatsModel(
            group_delay_unit    =   "microsecond",
            magnitude           =   gd_full.tau_us,
        )

        carrier_values: ChanEstCarrierModel = ChanEstCarrierModel(
            carrier_count               =   len(freqs),
            frequency_unit              =   "Hz",
            frequency                   =   freqs,
            complex                     =   values,
            complex_dimension           =   complex_ndim,
            magnitudes                  =   magnitudes_db,
            group_delay                 =   group_delay_stats,
            occupied_channel_bandwidth  =   occupied_channel_bandwidth,
        )

        # --- assemble top-level result ---
        # Run echo detection analysis
        echo_report = cls.basic_analysis_echo_detection_ifft(model)
        echo_dataset = EchoDatasetModel(type=EchoDetectorType.IFFT, report=echo_report)

        result_model: DsChannelEstAnalysisModel = DsChannelEstAnalysisModel(
            device_details                  =   getattr(model, "device_details", {}),
            pnm_header                      =   model.pnm_header.model_dump() if hasattr(model.pnm_header, "model_dump") else {},
            mac_address                     =   cast(MacAddressStr, getattr(model, "mac_address", "")),
            channel_id                      =   cast(ChannelId, int(getattr(model, "channel_id", INVALID_START_VALUE))),
            subcarrier_spacing              =   subcarrier_spacing,
            first_active_subcarrier_index   =   first_active_subcarrier_index,
            subcarrier_zero_frequency       =   subcarrier_zero_frequency,
            carrier_values                  =   carrier_values,
            signal_statistics               =   signal_stats_model,
            echo                            =   echo_dataset,
        )

        return result_model

    @classmethod
    def basic_analysis_echo_detection_ifft(
        cls,
        model: CmDsOfdmChanEstimateCoefModel,
        cable_type: CableType = CableType.RG6,
    ) -> EchoDetectorReport:
        """
        Run FFT/IFFT-based echo detection from a single Channel-Estimation snapshot.

        Overview
        --------
        Builds a time response h(t) from the complex channel-estimation spectrum H(f),
        identifies the direct path, then scans for echo peaks subject to a conservative
        threshold, guard region, and optional time-response attachment.

        Inputs (from model)
        -------------------
        values : ComplexArray
            List of complex-like samples for H(f). Accepted shapes:
            - [(re, im), ...] pairs or
            - [complex, ...]
        subcarrier_spacing : float
            Δf in Hz between OFDM subcarriers.
        channel_id : int
            Downstream channel ID, used for metadata only.

        Parameters
        ----------
        cable_type : CableType, default CableType.RG6
            Cable type to derive the velocity factor for distance conversion.

        Returns
        -------
        EchoDetectorReport
            Structured result including dataset metadata, direct-path info, an array
            of detected echoes (if any), and optional time-response block.

        Notes
        -----
        - n_fft is chosen as the next power of two ≥ N (min 1024) for finer time sampling.
        - Thresholding defaults to “dB-down” mode (70 dB below direct peak), with an
          automatic fallback to 80 dB if nothing is found.
        """
        log = logging.getLogger(f"{cls.__name__}")

        values = cast(Sequence[Union[complex, Sequence[float]]], getattr(model, "values", []))
        if not values:
            raise ValueError("Echo detection requires non-empty channel-estimation values.")

        df_hz = float(getattr(model, "subcarrier_spacing", 0.0))
        if df_hz <= 0.0:
            raise ValueError("Invalid subcarrier spacing for echo detection.")

        channel_id = cast(ChannelId, getattr(model, "channel_id", INVALID_CHANNEL_ID))

        # Choose IFFT length for finer time resolution
        N = len(values)
        n_fft = 1 << (N - 1).bit_length()
        if n_fft < 1024:
            n_fft = 1024

        # Detector
        det = EchoDetector(
            freq_data             = values,
            subcarrier_spacing_hz = df_hz,
            n_fft                 = n_fft,
            cable_type            = cable_type.name,
            channel_id            = int(channel_id),
        )

        log.info(
            "Init EchoDetector: N=%d, Δf=%.3f Hz, fs=%.3f Hz, n_fft=%d, cable=%s, chan=%s",
            N, df_hz, N * df_hz, n_fft, cable_type.name, str(channel_id),
        )

        # Conservative defaults, with auto-fallback if nothing exceeds threshold
        echo_report: EchoDetectorReport = det.multi_echo(
            threshold_mode        = "db_down",    # primary threshold strategy
            threshold_db_down     = 70.0,         # 70 dB below the direct path
            guard_bins            = 8,            # keep away from main-lobe skirt
            min_separation_s      = 0.0,          # allow closely spaced echoes if present
            max_delay_s           = 7.7e-6,       # ~1 km one-way at VF≈0.87
            max_peaks             = 5,            # cap number of echoes returned
            include_time_response = False,        # keep payload small by default
            direct_at_zero        = True,         # recenter direct path to t=0
            window                = "hann",       # reduce sidelobes before IFFT
            auto_fallback         = True,         # try stricter fallback if none found
            fallback_db_down      = 80.0,         # fallback threshold
        )

        return echo_report


    @classmethod
    def basic_analysis_ds_chan_est(
        cls,
        measurement: Dict[str, Any],
        cable_type: CableType = CableType.RG6
    ) -> DsChannelEstAnalysisModel:
        """
        Perform downstream channel-estimation analysis.

        Computes:
        - Per-subcarrier frequency axis (Hz)
        - Magnitude sequence (dB) from complex coefficients
        - Group delay (µs) from phase slope across subcarriers
        - Echo detection via IFFT of H(f) → h(t) with conservative thresholds

        Expected Keys (subset) in `measurement`
        ---------------------------------------
        channel_id : int
            Downstream channel ID.
        subcarrier_spacing : int
            Δf in Hz between subcarriers.
        first_active_subcarrier_index : int
            Index of the first active subcarrier relative to subcarrier 0.
        subcarrier_zero_frequency : int
            Frequency (Hz) of subcarrier 0.
        occupied_channel_bandwidth : int
            Occupied bandwidth for metadata.
        values : ComplexArray
            List of complex-like samples for H(f). [(re, im), ...] or [complex, ...].

        Returns
        -------
        DsChannelEstAnalysisModel
            Typed model with carrier values, signal statistics, and echo results.
        """
        log = logging.getLogger(f"{cls.__name__}")

        channel_id: ChannelId                   = measurement.get("channel_id",                    INVALID_CHANNEL_ID)
        subcarrier_spacing: int                 = measurement.get("subcarrier_spacing",            INVALID_START_VALUE)
        first_active_subcarrier_index: int      = measurement.get("first_active_subcarrier_index", INVALID_START_VALUE)
        subcarrier_zero_frequency: FrequencyHz  = measurement.get("subcarrier_zero_frequency",     INVALID_START_VALUE)
        occupied_channel_bandwidth: int         = measurement.get("occupied_channel_bandwidth",    INVALID_START_VALUE)

        if (first_active_subcarrier_index < 0) or (subcarrier_zero_frequency < 0) or (subcarrier_spacing <= 0):
            raise ValueError(
                f"Active index: {first_active_subcarrier_index} or "
                f"zero frequency: {subcarrier_zero_frequency} or "
                f"spacing: {subcarrier_spacing} must be non-negative"
            )

        values: ComplexArray = measurement.get("values", [])
        if not values:
            raise ValueError("No complex channel estimation values provided in measurement.")

        # Frequency axis
        start_freq: FrequencyHz    = cast(FrequencyHz, (subcarrier_spacing * first_active_subcarrier_index) + subcarrier_zero_frequency)
        freqs: FrequencySeriesHz   = [start_freq + (i * subcarrier_spacing) for i in range(len(values))]

        # Group delay and magnitudes
        gd = GroupDelay.from_channel_estimate(Hhat=values, df_hz=subcarrier_spacing, f0_hz=start_freq)
        gd_results = gd.to_result()

        cao = ComplexArrayOps(values)
        magnitudes_db: FloatSeries = cao.to_list(cao.power_db())
        signal_stats_model = SignalStatistics(magnitudes_db).compute()
        complex_arr = np.asarray(values, dtype=complex)

        group_delay_stats: GrpDelayStatsModel = GrpDelayStatsModel(
            group_delay_unit = "microsecond",
            magnitude        = ComplexArrayOps.to_list(gd_results.group_delay_us),
        )

        # ── IFFT Echo Detection (tightened window & stricter floor) ──
        N = len(values)
        n_fft = 1 << (N - 1).bit_length()
        if n_fft < 1024:
            n_fft = 1024

        det = EchoDetector(
            freq_data             = values,
            subcarrier_spacing_hz = float(subcarrier_spacing),
            n_fft                 = n_fft,
            cable_type            = cable_type.name,
            channel_id            = ChannelId(channel_id),
        )

        fs = float(N) * float(subcarrier_spacing)
        # limit echoes to ~3.5 µs ⇒ ≈ 457 m one-way @ RG6 VF=0.87
        max_delay_s = 3.5e-6

        # log the window in both bins and meters so we can sanity-check field runs
        v = SPEED_OF_LIGHT * CABLE_VF.get(cable_type.name, 0.87)
        max_dist_m = 0.5 * v * max_delay_s
        i_stop = int(max_delay_s * fs)
        log.info(
            "EchoDetector window: fs=%.3f Hz, n_fft=%d, i_stop=%d bins, max_delay=%.2fus, max_dist≈%.1f m",
            fs, n_fft, i_stop, max_delay_s * 1e6, max_dist_m
        )

        det = EchoDetector(
            freq_data               = values,
            subcarrier_spacing_hz   = float(subcarrier_spacing),
            n_fft                   = 4096,
            cable_type              = cable_type.name,
            channel_id              = channel_id,
        )

        # Parameters you pass to the detector (keep these as you already set them)
        max_delay_s_used = 3.5e-6  # ← use the same value you log/print; adjust if you changed it
        echo_report: EchoDetectorReport = det.multi_echo(
            threshold_mode        = "db_down",
            threshold_db_down     = 60.0,
            normalize_power       = True,
            guard_bins            = 16,
            min_separation_s      = 8.0 / det.fs,
            max_delay_s           = max_delay_s_used,
            max_peaks             = 3,
            include_time_response = False,
            direct_at_zero        = True,
            window                = "hann",
        )

        # ── INSERT TRIM HERE ───────────────────────────────────────────────────────
        # Enforce hard edge trim near the stop index to avoid edge/alias artifacts.
        # Compute i_stop the same way you printed/logged it:
        i_stop     = int(np.ceil(max_delay_s_used * det.fs))
        edge_guard = 8
        if echo_report.echoes:
            echo_report.echoes = [
                e for e in echo_report.echoes
                if (e.bin_index < (i_stop - edge_guard))
            ]
        # ───────────────────────────────────────────────────────────────────────────

        echo_rpt = EchoDatasetModel(type=EchoDetectorType.IFFT, report=echo_report)


        carrier_values: ChanEstCarrierModel = ChanEstCarrierModel(
            carrier_count               = len(freqs),
            frequency_unit              = "Hz",
            frequency                   = freqs,
            complex                     = values,
            complex_dimension           = int(complex_arr.ndim),
            magnitudes                  = magnitudes_db,
            group_delay                 = group_delay_stats,
            occupied_channel_bandwidth  = occupied_channel_bandwidth,
        )

        result_model: DsChannelEstAnalysisModel = DsChannelEstAnalysisModel(
            device_details                  = measurement.get("device_details", {}),
            pnm_header                      = measurement.get("pnm_header", {}),
            mac_address                     = measurement.get("mac_address", ""),
            channel_id                      = ChannelId(measurement.get("channel_id", INVALID_START_VALUE)),
            subcarrier_spacing              = subcarrier_spacing,
            first_active_subcarrier_index   = first_active_subcarrier_index,
            subcarrier_zero_frequency       = subcarrier_zero_frequency,
            carrier_values                  = carrier_values,
            signal_statistics               = signal_stats_model,
            echo                            = echo_rpt,
        )

        return result_model
