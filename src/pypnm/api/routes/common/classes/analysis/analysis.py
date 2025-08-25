# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia

import logging
import numpy as np

from enum import Enum
from typing import Callable, List, Dict, Any

from pypnm.api.routes.common.classes.analysis.model.schema import ConstellationDisplayAnalysisModel
from pypnm.api.routes.common.extended.common_messaging_service import MessageResponse
from pypnm.api.routes.docs.pnm.files.service import SystemConfigSettings
from pypnm.docsis.cm_snmp_operation import SystemDescriptor, Utils
from pypnm.lib.constants import INVALID_CHANNEL_ID
from pypnm.lib.file_processor import FileProcessor
from pypnm.lib.mac_address import MacAddress
from pypnm.lib.qam.lut_mgr import QamLutManager
from pypnm.lib.qam.types import QamModulation
from pypnm.lib.signal_processing.complex_array_ops import ComplexArrayOps
from pypnm.lib.signal_processing.group_delay import GroupDelay
from pypnm.lib.signal_processing.linear_regression import LinearRegression1D
from pypnm.lib.types import ComplexArray, FloatSeries, IntSeries, StringArray
from pypnm.pnm.data_type.DsOfdmModulationType import DsOfdmModulationType
from pypnm.pnm.lib.signal_statistics import SignalStatistics
from pypnm.pnm.process.pnm_file_type import PnmFileType
from pypnm.lib.signal_processing.shan.series import Shannon, ShannonSeries

class RxMerCarrierType(Enum):
    EXCLUSION   = "0"
    CLIPPED     = "1"
    NORMAL      = "2"

RXMER_EXCLUSION = 63.75
RXMER_CLIPPED_LOW = 0.0
RXMER_CLIPPED_HIGH = 63.5
    
class AnalysisType(Enum):
    """
    BASIC provides (Frequency, Magnitude) and some meta-data depending on PNM FileType.
    """
    BASIC = 0

class Analysis:
        
    def __init__(self, analysis_type: AnalysisType, msg_response: MessageResponse):
        self.logger = logging.getLogger(f"{self.__class__.__name__}")
        self.analysis_type = analysis_type
        self.msg_response = msg_response
        self.measurement_data = self.msg_response.payload_to_dict().get("data", [])
        self.analysis: List[Dict[str, Any]] = []
        
        # how to check to see if logger.DEBUG is enable
        if self.logger.isEnabledFor(logging.DEBUG):
            self.save_message_response(self.msg_response)

        self._process()

    def _process(self):
        """
        Processes each measurement in the payload based on the analysis type.
        """
        for measurement in self.measurement_data:
            pnm_header = measurement.get("pnm_header")
            pnm_file_type = f'{pnm_header.get("file_type")}{pnm_header.get("file_type_version")}'

            if self.analysis_type == AnalysisType.BASIC:
                self._basic_analysis(pnm_file_type, measurement)

    def _basic_analysis(self, pnm_file_type: str, measurement):

        if pnm_file_type == PnmFileType.OFDM_CHANNEL_ESTIMATE_COEFFICIENT.value:
            self.logger.info("Processing OFDM_CHANNEL_ESTIMATE_COEFFICIENT")
            self.analysis.append(self.basic_analysis_ds_chan_est(measurement))

        elif pnm_file_type == PnmFileType.DOWNSTREAM_CONSTELLATION_DISPLAY.value:
            self.logger.debug("Processing DOWNSTREAM_CONSTELLATION_DISPLAY")
            self.analysis.append(self.basic_analysis_ds_constellation_display(measurement).model_dump())

        elif pnm_file_type == PnmFileType.RECEIVE_MODULATION_ERROR_RATIO.value:
            self.logger.debug("Processing RECEIVE_MODULATION_ERROR_RATIO")
            self.analysis.append(self.basic_analysis_rxmer(measurement))

        elif pnm_file_type == PnmFileType.DOWNSTREAM_HISTOGRAM.value:
            self.logger.debug("Stub: Processing DOWNSTREAM_HISTOGRAM")
            pass

        elif pnm_file_type == PnmFileType.UPSTREAM_PRE_EQUALIZER_COEFFICIENTS.value:
            self.logger.debug("Processing UPSTREAM_PRE_EQUALIZER_COEFFICIENTS")
            self.analysis.append(self.basic_analysis_us_ofdma_pre_equalization(measurement))

        elif pnm_file_type == PnmFileType.UPSTREAM_PRE_EQUALIZER_COEFFICIENTS_LAST_UPDATE.value:
            self.logger.debug("Stub: Processing UPSTREAM_PRE_EQUALIZER_COEFFICIENTS_LAST_UPDATE")
            pass

        elif pnm_file_type == PnmFileType.OFDM_FEC_SUMMARY.value:
            self.logger.debug("Stub: Processing OFDM_FEC_SUMMARY")
            pass

        elif pnm_file_type == PnmFileType.SPECTRUM_ANALYSIS.value:
            self.logger.debug("Stub: Processing SPECTRUM_ANALYSIS")
            pass

        elif pnm_file_type == PnmFileType.OFDM_MODULATION_PROFILE.value:
            self.logger.debug("Processing OFDM_MODULATION_PROFILE")
            self.analysis.append(self.basic_analysis_ds_modulation_profile(measurement))

        elif pnm_file_type == PnmFileType.LATENCY_REPORT.value:
            self.logger.warning("Stub: Processing LATENCY_REPORT")
            pass

        else:
            self.logger.warning(f"Unknown PNM file type: {pnm_file_type}")
   
    @classmethod
    def basic_analysis_rxmer(cls, measurement: Dict[str, Any]) -> Dict[str, Any]:
        """
        Performs a basic RxMER (Received Modulation Error Ratio) analysis on the provided measurement data.

        This method calculates the subcarrier frequencies, extracts the RxMER magnitudes, and classifies each
        subcarrier into one of three categories:
            - EXCLUSION (63.75 dB): typically marks unusable spectrum regions
            - CLIPPED (0.0 or 63.5 dB): values that are clipped or saturated
            - NORMAL (all other values): valid RxMER readings

        It also validates that the lengths of the frequency, magnitude, and classification lists match.

        Args:
            measurement (Dict[str, Any]): A dictionary containing subcarrier spacing, active index,
                                        zero frequency, and RxMER values under the "values" key.

        Returns:
            Dict[str, Any]: A dictionary containing the computed frequency list, RxMER magnitudes,
                            subcarrier classifications, and relevant metadata.

        Raises:
            ValueError: If the RxMER values list is missing or if frequency, magnitude, and classification
                        arrays have mismatched lengths.
        """
        spacing:int = measurement.get("subcarrier_spacing",-1)                  # Hz
        active_index:int = measurement.get("first_active_subcarrier_index",-1)  # index
        zero_freq:int = measurement.get("zero_frequency", -1)                   # Hz
        
        if active_index < 0 or zero_freq < 0 or spacing <0:
            raise ValueError(f"Active index: {active_index} or zero frequency: {zero_freq} or spacing: {spacing} must be non-negative")

        values = measurement.get("values", [])
        if not values:
            raise ValueError("No complex channel estimation values provided in measurement.")

        base_freq = (spacing * active_index) + zero_freq
        freqs:List[int] = [base_freq + (i * spacing) for i in range(len(values))]
        magnitudes:List[float] = values

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
        
        result = {
            "device_details": measurement.get("device_details"),
            "pnm_header": measurement.get("pnm_header"),
            "mac_address": measurement.get("mac_address"),
            "channel_id": measurement.get("channel_id"),
            "magnitude_unit": "dB",
            "frequency_unit": "Hz",            
            "carrier_status_map": {
                RxMerCarrierType.EXCLUSION.name.lower(): RxMerCarrierType.EXCLUSION.value,
                RxMerCarrierType.CLIPPED.name.lower(): RxMerCarrierType.CLIPPED.value,
                RxMerCarrierType.NORMAL.name.lower(): RxMerCarrierType.NORMAL.value,
            },
            "carrier_values": {
                "carrier_count": len(freqs),
                "magnitude": magnitudes,
                "frequency": freqs,            
                "carrier_status": carrier_status,
            },
            "regression": {
                "slope": LinearRegression1D(magnitudes, freqs).regression_line(),
            },
            "modulation_statistics": ss.to_dict()
        }

        return result

    @classmethod
    def basic_analysis_ds_chan_est(cls, measurement: Dict[str, Any]) -> Dict[str, Any]:
        """
        Performs Channel Estimation analysis, including frequency, magnitude in dB, and group delay.

        Args:
            measurement (Dict[str, Any]): Contains complex values per subcarrier and metadata.

        Returns:
            Dict[str, Any]: Analysis results with magnitude and group delay per subcarrier.
        """
        spacing:int = measurement.get("subcarrier_spacing",-1)                              # Hz
        active_index:int = measurement.get("first_active_subcarrier_index",-1)              # index
        zero_freq:int = measurement.get("zero_frequency", -1)                               # Hz
        occupied_channel_bandwidth:int = measurement.get("occupied_channel_bandwidth", -1)  #
        
        if active_index < 0 or zero_freq < 0 or spacing <0:
            raise ValueError(f"Active index: {active_index} or zero frequency: {zero_freq} or spacing: {spacing} must be non-negative")

        values:ComplexArray = measurement.get("values", []) # Complex Values
        if not values:
            raise ValueError("No complex channel estimation values provided in measurement.")
        
        start_freq = (spacing * active_index) + zero_freq
        freqs:List[int] = [start_freq + (i * spacing) for i in range(len(values))]

        # Group delay calculation
        gd = GroupDelay.from_channel_estimate(Hhat=values, df_hz=spacing, f0_hz=start_freq)
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

        Args:
            measurement: Parsed profile measurement dict.
            split_carriers: 
                - False (default): carrier_values → {"carriers": [ {freq,mod,shannon}, … ]}
                - True:            carrier_values → {"freqs": […], "mods": […], "shannons": […]}

        Returns:
            Dict containing:
              - pnm_header
              - channel_id
              - frequency_unit: 'Hz'
              - shannon_limit_unit: 'dB'
              - profiles: List of dicts with:
                  * profile_id
                  * carrier_values (see above)
        """
        spacing:int      = measurement.get("subcarrier_spacing", -1)
        active_index:int = measurement.get("first_active_subcarrier_index", -1)
        zero_freq:int    = measurement.get("zero_frequency", -1)

        if active_index < 0 or zero_freq < 0 or spacing < 0:
            raise ValueError(f"Invalid parameters: spacing={spacing}, "
                             f"active_index={active_index}, zero_freq={zero_freq}")

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
            - Frequency per carrier
            - Complex values
            - Magnitude in dB
            - Group delay (phase derivative)

        Args:
            measurement (Dict[str, Any]): Measurement data containing channel estimation values and metadata.

        Returns:
            Dict[str, Any]: Dictionary with per-carrier analysis results.
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
    def basic_analysis_ds_constellation_display(cls,measurement: Dict[str, Any],) -> ConstellationDisplayAnalysisModel:
        """
        Build a minimal constellation analysis payload from a downstream OFDM
        measurement dictionary.

        Expected keys in `measurement`
        ------------------------------
        - values : ComplexArray                  # required; list of (real, imag)
        - pnm_header : dict                      # optional
        - mac_address : str                      # optional
        - channel_id : int                       # optional
        - num_sample_symbols : int               # optional; defaults to len(values)
        - actual_modulation_order : int|str      # optional; 'QAM-256' normalized → 256

        Returns
        -------
        ConstellationDisplayAnalysisModel
        """
        samples: ComplexArray = measurement.get("samples") or []
        if not samples:
            raise ValueError("measurement['values'] is required and must be a non-empty ComplexArray.")

        amo:int = measurement.get("actual_modulation_order", DsOfdmModulationType.UNKNOWN)
        num_sample_symbols = int(measurement.get("num_sample_symbols", len(samples)))

        #Get Hard/Soft Decsions
        qm:QamModulation    = QamModulation.from_DsOfdmModulationType(amo)
        hard                = QamLutManager().get_hard_decisions(qm)
        soft                = QamLutManager().scale_soft_decisions(qm, samples)

        return ConstellationDisplayAnalysisModel(
            device_details      = measurement.get("device_details", SystemDescriptor.empty()),
            pnm_header          = measurement.get("pnm_header", {}),
            mac_address         = measurement.get("mac_address", MacAddress.null()),
            channel_id          = measurement.get("channel_id", INVALID_CHANNEL_ID),
            num_sample_symbols  = num_sample_symbols,
            modulation_order    = qm,           # QamModulation 
            hard                = hard,         # Scaled
            soft                = soft          # Scaled
        )

    def get_results(self, full_dict = True) -> Dict[str, Any]:
        """
        Returns the list of processed analysis results.
        If full_dict is True, returns the entire analysis dictionary.
        
        Args    :
            full_dict (bool): If True, returns the full analysis dictionary.
                              If False, returns only the analysis list.

        Returns:
            Dict[str, Any]: The analysis results. 
              {
                "analysis": Dict[str, Any]
            }    
        """
        return {"analysis": self.analysis}
    
    def save_message_response(self, msg_response: MessageResponse) -> None:
        msg_rsp_dict:Dict[Any, Any] = msg_response.payload_to_dict()
        mac = msg_rsp_dict.get('mac_address')
        fname = f'{SystemConfigSettings().message_response_dir}/{mac}_{Utils.time_stamp()}.msg'
        self.logger.debug(f'Saving Message Response: {fname}')

        fp = FileProcessor(fname)
        fp.write_file(msg_rsp_dict)
        fp.close()

        