# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia

import asyncio
import logging
import math
import os
from pathlib import Path
import shutil
from time import sleep
import time
from typing import Dict, List,  Optional, Tuple, Union

from pypnm.api.routes.common.extended.common_measure_schema import (
    DownstreamOfdmParameters, UpstreamOfdmaParameters)
from pypnm.config.system_config_settings import SystemConfigSettings
from pypnm.config.config_manager import ConfigManager
from pypnm.api.routes.common.classes.file_capture.pnm_file_transaction import PnmFileTransaction
from pypnm.api.routes.common.extended.common_messaging_service import CommonMessagingService, MessageResponse
from pypnm.api.routes.common.service.status_codes import ServiceStatusCode
from pypnm.config.pnm_config_manager import PnmConfigManager
from pypnm.docsis.cable_modem import CableModem
from pypnm.docsis.cm_snmp_operation import (
    DocsPnmBulkFileUploadStatus, DocsPnmCmCtlStatus, FecSummaryType, MeasStatusType)
from pypnm.lib.file_processor import FileProcessor
from pypnm.lib.ftp.ftp_connector import FTPConnector
from pypnm.lib.inet import Inet
from pypnm.lib.ssh.ssh_connector import SSHConnector, SecureTransferMode
from pypnm.lib.tftp.tftp_connector import TFTPConnector
from pypnm.lib.utils import Utils
from pypnm.pnm.data_type.DocsIf3CmSpectrumAnalysisCtrlCmd import (
    DocsIf3CmSpectrumAnalysisCtrlCmd, SpectrumRetrievalType, WindowFunction)
from pypnm.pnm.data_type.pnm_test_types import DocsPnmCmCtlTest
from pypnm.snmp.modules import DocsisIfType
from pypnm.snmp.snmp_v2c import Snmp_v2c

class CommonMeasureService(CommonMessagingService):
    """
    Base service class for executing common Proactive Network Maintenance (PNM) measurement tests.

    Parameters:
        pnm_test_type (DocsPnmCmCtlTest): The type of PNM test to execute.
        cable_modem (CableModem): The cable modem instance used for the test.
        tftp_servers (Inet,Inet): (IPv4,IPv6)
        tftp_path (str, optional): The path on the TFTP server where test result files are stored. Default is an empty string.
        snmp_write_community (str, optional): The SNMP community string for write access. Default is "private".
        **extra_options (dict, optional): Additional keyword arguments specific to the test type, such as:
            - fec_summary_type (FecSummaryType): Required for tests involving FEC summary metrics.
            - Other parameters based on the test type.

    Notes:
        This class serves as a base for test-specific measurement operations. Subclasses should implement 
        specific tests such as:
        - Downstream OFDM codeword error rate
        - RXMER per subcarrier
        - FEC statistics, etc.

        It is expected that subclasses will extend this service and provide the necessary implementations for 
        executing and processing PNM measurements based on the test type and parameters.
    """
    def __init__(self, pnm_test_type:DocsPnmCmCtlTest, 
                 cable_modem: CableModem, 
                 tftp_servers: Tuple[Inet,Inet], 
                 tftp_path: str = "", 
                 snmp_write_community: str = "private", 
                 **extra_options):
        super().__init__()
        self.logger = logging.getLogger(self.__class__.__name__)
        
        self.pnm_filename:List[str]
        
        self._transactionId_pnmFile: Dict[str, str] = {}
        self.pnm_test_type:DocsPnmCmCtlTest = pnm_test_type
        self.cm:CableModem = cable_modem
        self.tftp_servers:Tuple[Inet,Inet] = tftp_servers
        self.tftp_path:str = tftp_path
        self.snmp_write_community:str = snmp_write_community
        self.extra_options = extra_options
        self.config_mgr:ConfigManager = ConfigManager()
        self.log_prefix:str = f"MAC: {self.cm.get_mac_address} - INET: {self.cm.get_inet_address}"
        self.save_dir = PnmConfigManager.get_save_dir()
        
        if self.extra_options:
            self.logger.debug(f"{self.log_prefix} - OPTIONS: {self.extra_options}")
            self._preload_interface_parameters()
            
        self._precheck() 

    def _precheck(self) -> None:
        """
        Perform pre-check and ensure the save directory exists.
        """
        self.logger.debug(f'PreCheck: SaveDir: {self.save_dir}')
        save_path = Path(self.save_dir)
        save_path.mkdir(parents=True, exist_ok=True)

    def _preload_interface_parameters(self) -> None:
        """
        Load optional interface parameters from extra_options dictionary.
        If not present, sets interface_parameters to None.
        """
        self.interface_parameters = self.extra_options.get("interface_parameters", None)
                
    async def set_and_go(self, interface_parameters: Optional[DownstreamOfdmParameters | UpstreamOfdmaParameters] = None, 
                         max_wait_count: int = 5,) -> MessageResponse:
        """
        Trigger PNM file capture and retrieval based on direction-specific parameters.

        Args:
            interface_parameters (InterfaceParameters, optional): 
                The configuration specifying the direction of capture:
                - `DownstreamOfdmParameters`: For OFDM downstream channels.
                - `UpstreamOfdmaParameters`: For OFDMA upstream channels.
                If `None` (default), all channels will be captured.
                
            max_wait_count (int, optional): 
                Maximum seconds to wait for measurement readiness. Default is 5.

        Returns:
            MessageResponse: Result indicating success or failure of the operation.
        """
          
        ##########################################################
        # Verify that we can connect to the CM via Ping and SNMP
        ##########################################################
        
        if not self.is_ping_reachable():
            self.logger.error(f"{self.log_prefix} - Unreachable via PING")
            return self.build_send_msg(ServiceStatusCode.UNREACHABLE_PING)

        if not await self.is_snmp_ready():
            self.logger.error(f"{self.log_prefix} - Unreachable via SNMP")
            return self.build_send_msg(ServiceStatusCode.UNREACHABLE_SNMP)

        #########################################################################
        #                   Spectrum Analysis SNMP Return                       #
        #########################################################################
        
        spec_rev_type = self.extra_options.get("spectrum_retrieval_type",SpectrumRetrievalType.UNKNOWN)
            
        if spec_rev_type == SpectrumRetrievalType.SNMP:
            self.logger.info(f"{self.log_prefix} - Performing Spectrum Analysis SNMP Amplitude Data")

            #Set Spectrum Analyzer
            __status = await self._generic_spectrum_analyzer_operation()
            if __status[0] != ServiceStatusCode.SUCCESS:
               self.logger.error(f"{self.log_prefix} - Unable to set Spectrum Analyzer Settings")
               return ServiceStatusCode.SPEC_ANALYZER_SET_CONFIG_ERROR
            
            # This is a blocking method, it will return SUCCESS or wait till timeout to return an ERROR
            status = await self._check_spectrum_amplitude_data_status()
            
            if status == ServiceStatusCode.SUCCESS:
                
                amp_data: bytes = await self.cm.getSpectrumAmplitudeData()
                
                prefix = DocsPnmCmCtlTest.SPECTRUM_ANALYZER_SNMP_AMP_DATA.name.lower()
                filename = f"{prefix}_{self.cm.get_mac_address}_{int(time.time())}.bin"
                
                tx_id = await PnmFileTransaction().insert(self.cm,
                    DocsPnmCmCtlTest.SPECTRUM_ANALYZER_SNMP_AMP_DATA, filename)
                
                save_dir = SystemConfigSettings.save_dir
                fpath = f"{save_dir}/{filename}"
                self.logger.debug(f'SpectrumAmplitudeData: - FNAME: {filename} - Length:{len(amp_data)} - TransactionID: {tx_id}')
                
                FileProcessor(fpath).write_file(amp_data)
                self.build_transaction_msg(tx_id, filename)

            return self.build_send_msg(status)

        #########################################################################
        # Ensure CM Inet and TFTP server address use the same IP version
        #
        # The TFTP server address must match the IP version (IPv4 or IPv6) used
        # by the Cable Modem (CM). By default, we assume IPv4.
        #
        # If the CM's IP address is IPv6 and matches the version of the 
        # secondary TFTP server entry, we switch to using the IPv6 TFTP server.
        #
        # TODO: Enhance this logic to support dual-stack (dual-home) cable modems,
        # where both IPv4 and IPv6 may be valid simultaneously.
        #########################################################################

        self.logger.info(f'{self.log_prefix} - TFTP-SERVERS: ({self.tftp_servers[0]} | {self.tftp_servers[1].inet})')

        # Default to using the IPv4 TFTP server
        tftp_server: Inet = self.tftp_servers[0]

        # Switch to IPv6 TFTP server if CM uses IPv6
        if self.cm.same_inet_version(self.tftp_servers[1]):
            tftp_server = self.tftp_servers[1]

        # Attempt to configure the CM with the selected TFTP server and path
        if not await self.cm.setDocsPnmBulk(tftp_server.inet, self.tftp_path):
            self.logger.error(
                f"{self.log_prefix} - Unable to set TFTP server {tftp_server.inet} "
                f"or TFTP path: {self.tftp_path}"
            )
            return self.build_send_msg(ServiceStatusCode.TFTP_SERVER_PATH_SET_FAIL)

        ##############################################################################################
        # This section is determine by the direction due to which interface and type we are accessing 
        ##############################################################################################

        status_index_channelId = await self._get_indexes_via_pnm_test_type(interface_parameters)
        if status_index_channelId[0] != ServiceStatusCode.SUCCESS:
            self.logger.error(f'{self.log_prefix} - Unable to aquire index from ChannelID')
            return self.build_send_msg(status_index_channelId)

        ##############################################################################################
        # This section runs through all the indexes, build PNM file, run measurement and check status
        ##############################################################################################
                        
        return self.build_send_msg(await self._pnm_measure_status_and_pnm_file_transfer(status_index_channelId[1], max_wait_count))
    

    def getInterfaceParameters(self,
        interface_type: DocsisIfType
    ) -> Union[DownstreamOfdmParameters, UpstreamOfdmaParameters]:
        """
        Instantiate and return the PNM test parameters for the specified DOCSIS interface.

        Args:
            interface_type (DocsisIfType):
                The DOCSIS interface type:
                - `DocsisIfType.docsOfdmDownstream` → returns DownstreamOfdmParameters
                - `DocsisIfType.docsOfdmaUpstream`  → returns UpstreamOfdmaParameters

        Returns:
            Union[DownstreamOfdmParameters, UpstreamOfdmaParameters]:
                A parameters object tailored to the requested interface.

        Raises:
            ValueError: If `interface_type` is not OFDM downstream or OFDMA upstream.
        """
        if interface_type == DocsisIfType.docsOfdmDownstream:
            return DownstreamOfdmParameters()
        if interface_type == DocsisIfType.docsOfdmaUpstream:
            return UpstreamOfdmaParameters()

        raise ValueError(
            f"Unsupported interface type: {interface_type!r}. "
            "Expected docsOfdmDownstream or docsOfdmaUpstream."
        )
                   
    def is_ping_reachable(self) -> bool:
        """
        Check if the cable modem is reachable via ICMP ping.

        Returns:
            bool: True if the modem responds to ping, False otherwise.
        """
        return self.cm.is_ping_reachable()

    async def is_snmp_ready(self) -> bool:
        """
        Asynchronously check if the cable modem is accessible via SNMP.

        Returns:
            bool: True if the modem responds to SNMP queries, False otherwise.
        """
        return await self.cm.is_snmp_reachable()

    ###################
    # Private Methods #
    ###################
    
    def _get_and_move_pnm_file(self, pnm_file_name: str) -> bool:
        """
        Retrieves and moves the specified PNM file based on the configured retrieval method.

        This method delegates the file retrieval operation to a protocol-specific handler method
        depending on the configuration defined under `PnmFileRetrieval.method`. Supported methods
        include: "local", "tftp", "ftp", "scp", "sftp", "http", and "https".

        Configuration keys used:
            - PnmFileRetrieval.method: The file retrieval method to use (e.g., "local", "tftp", etc.).
            - PnmFileRetrieval.retries: Optional number of retries for retrieval attempts (currently unused here).

        Args:
            pnm_file_name (str): The name of the file to retrieve and move.

        Returns:
            bool: True if the file was successfully retrieved and moved; False otherwise.
        """
        method = SystemConfigSettings.retrieval_method
        self.logger.info(f"{self.log_prefix} - Retrieval method: {method}")

        try:
            if method == "local":
                return self._handle_local_fetch(pnm_file_name)
            elif method == "tftp":
                return self._handle_tftp_fetch(pnm_file_name)
            elif method == "ftp":
                return self._handle_ftp_fetch(pnm_file_name)
            elif method == "scp":
                return self._handle_scp_fetch(pnm_file_name)
            elif method == "sftp":
                return self._handle_sftp_fetch(pnm_file_name)
            elif method == "http":
                return self._handle_http_fetch(pnm_file_name)
            elif method == "https":
                return self._handle_https_fetch(pnm_file_name)
            else:
                self.logger.error(f"{self.log_prefix} - Unsupported retrieval method: {method}")
                return False
        except Exception as e:
            self.logger.exception(f"{self.log_prefix} - File retrieval failed: {e}")
            return False
            
    async def _get_indexes_via_pnm_test_type(self, ifParameters: Optional[DownstreamOfdmParameters | UpstreamOfdmaParameters] = None
                                             ) -> Tuple["ServiceStatusCode", Optional[List[Tuple[int, int]]]]:
        """
        Determines the appropriate interface indexes and channel IDs to target for a given PNM test type.

        Depending on the configured PNM test type, this method selects the relevant interface and filters the index/ChannelID
        tuples based on user-specified parameters.

        Args:
            interface_parameters (Optional[InterfaceParameters]): Parameters specifying interface type ("ofdm" or "ofdma")
                and optionally a list of channel IDs to filter. If not provided, default parameters are selected based on test type.

        Returns:
            Tuple[ServiceStatusCode, Optional[List[Tuple[int, int]]]]: 
                A status code indicating success or reason for failure, and a list of (index, channelId) tuples.
        """
        if self.pnm_test_type in (DocsPnmCmCtlTest.DS_HISTOGRAM, DocsPnmCmCtlTest.LATENCY_REPORT):
            idx:List[int] = await self.cm.getIfTypeIndex(DocsisIfType.docsCableMaclayer)
            return ServiceStatusCode.SUCCESS, [(idx[0], 0)]

        elif self.pnm_test_type == DocsPnmCmCtlTest.SPECTRUM_ANALYZER:
            return ServiceStatusCode.SUCCESS, [(0, 0)]

        elif self.pnm_test_type in (DocsPnmCmCtlTest.DS_CONSTELLATION_DISP, 
                                    DocsPnmCmCtlTest.DS_OFDM_CHAN_EST_COEF,
                                    DocsPnmCmCtlTest.DS_OFDM_CODEWORD_ERROR_RATE,
                                    DocsPnmCmCtlTest.DS_OFDM_MODULATION_PROFILE,
                                    DocsPnmCmCtlTest.DS_OFDM_RXMER_PER_SUBCAR):

            if not ifParameters:
                ifParameters:DownstreamOfdmParameters = self.getInterfaceParameters(DocsisIfType.docsOfdmDownstream)
        
        elif self.pnm_test_type in (DocsPnmCmCtlTest.US_PRE_EQUALIZER_COEF,):
            self.logger.info(f'{DocsPnmCmCtlTest.US_PRE_EQUALIZER_COEF} Measurement')
            if not ifParameters:
                ifParameters:UpstreamOfdmaParameters = self.getInterfaceParameters(DocsisIfType.docsOfdmaUpstream)
                
        '''
        There is redundant code, but incase I may need to change due to 
        change of requiments depending on Downstream vs. Upstream
        
        TODO: lol, I am sure I will not revisit, but OK for now.
        '''
        if ifParameters.type == "ofdm":
            channel_id_list = ifParameters.channel_id
            idx_channelId = await self.cm.getDocsIf31DsOfdmChannelIdIndex()            

            if not idx_channelId:
                self.logger.warning("No OFDM channel data found.")
                return ServiceStatusCode.NO_OFDMA_CHAN_ID_INDEX_FOUND, []

            if channel_id_list:
                filtered = [tpl for tpl in idx_channelId if tpl[1] in channel_id_list]
                self.logger.info(f'Downstream: {ifParameters.type} -> ChanID(s): {channel_id_list} -> Filtered: {filtered}')
                return ServiceStatusCode.SUCCESS, filtered

            self.logger.info(f'Downstream: {ifParameters.type} -> IDX,CHAN_ID: {idx_channelId}')
                        
            return ServiceStatusCode.SUCCESS, idx_channelId
                
        elif ifParameters.type == "ofdma":
            channel_id_list = ifParameters.channel_id
            idx_channelId = await self.cm.getDocsIf31CmUsOfdmaChannelIdIndex()

            if not idx_channelId:
                self.logger.warning("No OFDMA channel data found.")
                return ServiceStatusCode.NO_OFDMA_CHAN_ID_INDEX_FOUND, []

            if channel_id_list:
                filtered = [tpl for tpl in idx_channelId if tpl[1] in channel_id_list]
                self.logger.info(f'Upstream: {ifParameters.type} -> ChanID(s): {channel_id_list} -> Filtered: {filtered}')
                return ServiceStatusCode.SUCCESS, filtered

            self.logger.info(f'Upstream: {ifParameters.type} -> IDX,CHAN_ID: {idx_channelId}')

        return ServiceStatusCode.SUCCESS, idx_channelId
       
    async def _pnm_measure_status_and_pnm_file_transfer(self, idx_channelId:List[Tuple[int,int]], max_wait_count:int) -> ServiceStatusCode:
        """
        Set and monitor the OFDM measurement test for specified (index, PLC) tuples.

        For each (index, PLC) pair:
            - Initiates the PNM test using SNMP.
            - Waits for the test status to reach READY.
            - Monitors for the measurement status to become SAMPLE_READY.
            - Retrieves the resulting PNM file and stores it locally.

        Args:
            idx_channelId (Tuple[int, int]): A list of tuples where each tuple consists of 
                the SNMP interface index and the corresponding PLC (center frequency).
            max_wait_count (int): Maximum number of seconds to wait for SAMPLE_READY status.

        Returns:
            ServiceStatusCode: SUCCESS if all steps completed successfully,
                otherwise a specific error status (e.g., if the file couldn't be retrieved
                or the measurement status did not become SAMPLE_READY).
        """
        for idx, channel_id in idx_channelId:

            #######################################################################
            # This sets the Measurement Table/Row for the specific PNM Measurement
            #######################################################################
            status_pnmfiles:ServiceStatusCode = await self._setDocsPnmCmMeasureTest(self.pnm_test_type, idx, channel_id)
            if status_pnmfiles[0] != ServiceStatusCode.SUCCESS:
                return status_pnmfiles[0]
            
            pnm_filenames = status_pnmfiles[1]
            self.logger.info(f'{self.log_prefix} - PNM File(s) -> {pnm_filenames}')

            count=1
            while True:
                status_pnmfiles = await self.cm.getDocsPnmCmCtlStatus()
                self.logger.info(f"{self.log_prefix} - PNM status: {str(status_pnmfiles).upper()} - count: {count}")
                if status_pnmfiles == DocsPnmCmCtlStatus.TEST_IN_PROGRESS:
                    count += 1
                    sleep(1)
                    continue                
                
                if status_pnmfiles == DocsPnmCmCtlStatus.READY:
                    break
                                
                if status_pnmfiles == DocsPnmCmCtlStatus.TEMP_REJECT:
                    break
                
                if status_pnmfiles == DocsPnmCmCtlStatus.SNMP_ERROR:
                    break
                                    
            self.logger.debug(f"{self.log_prefix} - Checking Measurement Status for {self.pnm_test_type} @ IDX: {idx}")
            
            wait_count = 0
            extract_idx = lambda idx: idx[0] if isinstance(idx, list) and idx else idx
            while wait_count < max_wait_count:
                meas_status = await self.cm.getPnmMeasurementStatus(self.pnm_test_type, extract_idx(idx))
                self.logger.info(f"{self.log_prefix} - MeasureStatus: {meas_status.name}")
                if meas_status == MeasStatusType.SAMPLE_READY:
                    break
                sleep(1)
                wait_count += 1
                
            else:
                self.logger.error(f"{self.log_prefix} - SAMPLE_READY not reached for ChannelID {channel_id}")
                return ServiceStatusCode.NOT_READY_AFTER_FILE_CAPTURE

            #Multiple PNM files for special cases
            for pnm_fname in pnm_filenames:
                
                status:ServiceStatusCode = await self._check_and_wait_for_tftp_upload(pnm_fname)
                
                if status != ServiceStatusCode.SUCCESS:
                    self.logger.error(f"{self.log_prefix} - Unable to Upload PNM File to TFTP({status})")
                    return status
                
                # Get and copy PNM file to local data directory
                if not self._get_and_move_pnm_file(pnm_fname):
                    self.logger.error(f"{self.log_prefix} - Uanble to copy PNM file to local {self.save_dir} dir")
                    return ServiceStatusCode.COPY_PNM_FILE_TO_LOCAL_SAVE_DIR_FAILED
                
                # Find Transaction ID via filename
                trans_id = self._get_transaction_id_by_filename(pnm_fname)
                self.logger.debug(f'{self.log_prefix} - TransID: {trans_id} -> Filename: {pnm_fname}')
                self.build_transaction_msg(trans_id, pnm_fname)        
            
        return ServiceStatusCode.SUCCESS
    
    async def _check_and_wait_for_tftp_upload(self, filename:str, max_wait_count:int=5) -> ServiceStatusCode:

            wait_count = 0
            while True:
                try:
                    status = await self.cm.getBulkFileUploadStatus(filename)
                except Exception as e:
                    self.logger.error(f"{self.log_prefix} - Error checking upload status for '{filename}': {e}")
                    return ServiceStatusCode.TFTP_PNM_FILE_UPLOAD_FAILURE

                # Completed!
                if status == DocsPnmBulkFileUploadStatus.UPLOAD_COMPLETED:
                    self.logger.info(f"{self.log_prefix} - File '{filename}' uploaded successfully.")
                    return ServiceStatusCode.SUCCESS

                # Immediate fail if the device reports an error
                if status == DocsPnmBulkFileUploadStatus.ERROR:
                    self.logger.error(f"{self.log_prefix} - Device reported ERROR for file upload '{filename}'.")
                    return ServiceStatusCode.TFTP_PNM_FILE_UPLOAD_FAILURE

                # Timeout?
                if wait_count >= max_wait_count:
                    self.logger.error(f"{self.log_prefix} - TFTP File '{filename}' upload timed out after {wait_count} seconds.")
                    return ServiceStatusCode.TFTP_PNM_FILE_UPLOAD_FAILURE

                # Otherwise keep waiting
                self.logger.debug(
                    f"{self.log_prefix} - Waiting for file '{filename}' to upload "
                    f"(status={status.name}, count={wait_count})"
                )
                await asyncio.sleep(1)
                wait_count += 1
                
                return ServiceStatusCode.TFTP_PNM_FILE_UPLOAD_FAILURE
                             
    async def _setDocsPnmCmMeasureTest(self, pnm_test_type:DocsPnmCmCtlTest, 
                                       interface_index:int, channel_id:int) -> Tuple[ServiceStatusCode, List[str]]:
        """
        Configure and trigger a specific PNM (Proactive Network Maintenance) measurement 
        test on a cable modem based on the test type.

        Depending on the `pnm_test_type`, this method:
        - Generates appropriate output file names.
        - Uses SNMP to set the modem to collect specific diagnostic data.
        - Handles various DOCSIS downstream and upstream tests, including:
            - US Pre-Equalizer Coefficients (requires two files per interface: pre-eq and last pre-eq)
            - DS OFDM RxMER per Subcarrier
            - DS OFDM Codeword Error Rate
            - DS OFDM Channel Estimation Coefficients
            - DS Constellation Display
            - DS Histogram
            - DS OFDM Modulation Profile
            - Spectrum Analyzer Scan

        Parameters:
            pnm_test_type (DocsPnmCmCtlTest): Enum value indicating the PNM test to perform.
            interface_index (int): The SNMP index for the OFDM channel (usually the interface index).
            channel_id (int): The channel ID associated with the modem interface.

        Returns:
            Tuple[ServiceStatusCode, List[str]]: Status of the operation and list of generated file names.
        """
        pnm_files = []
        
        if pnm_test_type == DocsPnmCmCtlTest.US_PRE_EQUALIZER_COEF:
            
            # Pre-Eq and Last Pre-EQ (2 files)            
            pre_eq_filename = await self._pnm_file_generator(self.pnm_test_type, str(channel_id))
            last_pre_eq_filename = await self._pnm_file_generator(self.pnm_test_type, f'last_pre-eq_{str(channel_id)}')
            
            self.logger.debug(f'{self.log_prefix} - Setting {self.pnm_test_type} for ChannelID: {channel_id} @ IDX: {interface_index} -> FN: {pre_eq_filename} {last_pre_eq_filename}')
            
            self.logger.info(f'{self.log_prefix} - Performing US_PRE_EQUALIZER_COEF measurement on IDX: ({interface_index})')
            if not await self.cm.setDocsPnmCmUsPreEq(ofdma_idx=interface_index,
                                                     filename=pre_eq_filename,
                                                     last_pre_eq_filename=last_pre_eq_filename):
                self.logger.error(f"{self.log_prefix} - Upstream OFDMA Pre-Equalization is Not Avalaible")
                return ServiceStatusCode.FILE_SET_FAIL 
            
            #Append files for later fetching
            pnm_files.extend([pre_eq_filename, last_pre_eq_filename])
            
        else:
            #The remaining PNM Measuresurement are single PNM file
            pnm_filename = await self._pnm_file_generator(self.pnm_test_type, str(channel_id))
            self.logger.debug(f'{self.log_prefix} - Setting {self.pnm_test_type} for ChannelID: {channel_id} @ IDX: {interface_index} -> FN: {pnm_filename}')
            pnm_files.append(pnm_filename)
            
            if pnm_test_type == DocsPnmCmCtlTest.DS_OFDM_RXMER_PER_SUBCAR:
                        
                if not await self.cm.setDocsPnmCmDsOfdmRxMer(ofdm_idx=interface_index, rxmer_file_name=pnm_filename):
                    self.logger.error(f"{self.log_prefix} - Failed to set PNM filename: {pnm_filename}")
                    return ServiceStatusCode.FILE_SET_FAIL, []
            
            elif pnm_test_type == DocsPnmCmCtlTest.DS_OFDM_CODEWORD_ERROR_RATE:
                
                fst = self.extra_options.get("fec_summary_type", FecSummaryType.TEN_MIN)
                            
                if not await self.cm.setDocsPnmCmDsOfdmFecSum(ofdm_idx=interface_index, fec_sum_file_name=pnm_filename, fec_sum_type=fst):
                    self.logger.error(f"{self.log_prefix} - Failed to set PNM filename: {pnm_filename}")
                    return ServiceStatusCode.FILE_SET_FAIL, []
            
            elif pnm_test_type == DocsPnmCmCtlTest.DS_OFDM_CHAN_EST_COEF:
            
                if not await self.cm.setDocsPnmCmOfdmChEstCoef(ofdm_idx=interface_index, chan_est_file_name=pnm_filename):
                    self.logger.error(f"{self.log_prefix} - Failed to set PNM filename: {pnm_filename}")
                    return ServiceStatusCode.FILE_SET_FAIL, []
            
            elif pnm_test_type == DocsPnmCmCtlTest.DS_CONSTELLATION_DISP:
                # OFDM Downstream Constellation Display setup
                # Extra SNMP options may include:
                #   - modulation_offset: Optional[int]
                #   - num_sample_symb: Optional[int]
                if not await self.cm.setDocsPnmCmDsConstDisp(
                    ofdm_idx=interface_index,
                    const_disp_name=pnm_filename,
                    modulation_order_offset=self.extra_options.get('modulation_order_offset'),
                    number_sample_symbol=self.extra_options.get('number_sample_symbol')
                ):
                    self.logger.error(f"{self.log_prefix} - Failed to set PNM filename: {pnm_filename}")
                    return ServiceStatusCode.FILE_SET_FAIL, []
            
            elif pnm_test_type == DocsPnmCmCtlTest.DS_HISTOGRAM:
                sample_duration = self.extra_options.get("histogram_sample_duration", 10)
                if not await self.cm.setDocsPnmCmDsHist(ds_histogram_file_name=pnm_filename, timeout=sample_duration):
                    self.logger.error(f"{self.log_prefix} - Failed to set PNM filename: {pnm_filename}")
                    return ServiceStatusCode.FILE_SET_FAIL, []
                                   
            elif pnm_test_type == DocsPnmCmCtlTest.DS_OFDM_MODULATION_PROFILE:
            
                if not await self.cm.setDocsPnmCmDsOfdmModProf(ofdm_idx=interface_index, mod_prof_file_name=pnm_filename):
                    self.logger.error(f"{self.log_prefix} - Failed to set PNM filename: {pnm_filename}")
                    return ServiceStatusCode.FILE_SET_FAIL, []
                                    
            elif pnm_test_type == DocsPnmCmCtlTest.SPECTRUM_ANALYZER:
                #Created generic to be used for PNM File and SNMP Return data
                 __status = await self._generic_spectrum_analyzer_operation(filename=pnm_filename)
                 if __status[0] != ServiceStatusCode.SUCCESS:
                    return __status
                 
        return ServiceStatusCode.SUCCESS, pnm_files

    async def _check_spectrum_amplitude_data_status(self, timeout_seconds: int = 300) -> ServiceStatusCode:
        """
        Polls the cable modem for spectrum amplitude data availability within a timeout period.

        This method repeatedly checks if `docsIf3CmSpectrumAnalysisMeasAmplitudeData` is present
        on the modem, and returns a success or timeout status accordingly.

        Args:
            timeout_seconds (int): Maximum number of seconds to wait before timing out. Default is 300.

        Returns:
            ServiceStatusCode: 
                - SUCCESS if data becomes available within the timeout period.
                - SPEC_ANALYZER_AMPLITUDE_DATA_TIMEOUT if the timeout is exceeded.
        """
        t_start = time.time()

        while True:
            if await self.cm.isAmplitudeDataPresent():
                return ServiceStatusCode.SUCCESS
            now:int = math.floor((time.time() - t_start))
            
            if now >= timeout_seconds:
                self.logger.warning(f'{self.log_prefix} - Timeout for Amplitude Data ({now} of {timeout_seconds} seconds)')
                return ServiceStatusCode.SPEC_ANALYZER_AMPLITUDE_DATA_TIMEOUT

            self.logger.info(f'{self.log_prefix} - Waiting for Amplitude Data ({now} of {timeout_seconds})')
            
            await asyncio.sleep(1)
           
    def _handle_local_fetch(self, pnm_file_name: str) -> bool:
        """
        Handles copying a specified PNM file from a local source directory to a configured save directory.

        This method looks up the source and destination paths from the application's system configuration 
        (under the "PnmFileRetrieval" section) and attempts to copy the file named `pnm_file_name` 
        from the source directory to the save directory.

        Configuration keys used:
            - PnmFileRetrieval.local.src_dir: Source directory where the PNM file resides.
            - PnmFileRetrieval.save_dir: Destination directory where the file should be saved.

        Args:
            pnm_file_name (str): The name of the file to copy.

        Returns:
            bool: True if the file was successfully copied; False otherwise.
        """
                
        src_dir = SystemConfigSettings.local_src_dir

        self.logger.info(
            f'{self.log_prefix} - Local Copy - SRC: {src_dir} - SAVE: {self.save_dir} - FN: {pnm_file_name}'
        )

        if not os.path.isdir(src_dir) or not os.path.isdir(self.save_dir):
            self.logger.error(f"{self.log_prefix} - Invalid source or destination directory")
            return False

        while True:
            sleep(1)
            file_found = False
            for filename in os.listdir(src_dir):
                if filename == pnm_file_name:
                    file_found = True
                    src_path = os.path.join(src_dir, filename)
                    dest_path = os.path.join(self.save_dir, filename)
                    try:
                        shutil.copy2(src_path, dest_path)
                        self.logger.debug(f"{self.log_prefix} - Copied {filename} to {self.save_dir}")
                        return True
                    except Exception as e:
                        self.logger.error(f"{self.log_prefix} - Copy failed for {filename}: {e}")
                        return False

            if not file_found:
                self.logger.warning(f"{self.log_prefix} - File not found in source directory: {pnm_file_name}")

            return False

    def _handle_scp_fetch(self, pnm_file_name: str) -> bool:
        """
        Fetch a file from remote SCP server.
        
        Args:
            pnm_file_name: Name of the file to fetch from remote server
            
        Returns:
            bool: True if file transfer successful, False otherwise
        """
        sys_config = SystemConfigSettings()
        
        self.logger.debug(f"{self.log_prefix} - SCP: Connecting to: {sys_config.scp_host}")
        
        scp = SSHConnector(hostname=sys_config.scp_host,
                            username=sys_config.scp_user,
                            port=sys_config.scp_port,
                            transfer_mode=SecureTransferMode.SCP)
        
        try:
            if not scp.connect(password=sys_config.scp_password):
                self.logger.error(f'{self.log_prefix} - SCP Connect Failure: Host: {sys_config.scp_host}')
                return False
            
            remote_file_path = f'{sys_config.scp_remote_dir}/{pnm_file_name}'
            if not scp.receive_file(remote_path=remote_file_path,
                                    local_path=sys_config.save_dir):
                self.logger.error(f'{self.log_prefix} - SCP Receive File Error (SRC:{remote_file_path} DST: {sys_config.save_dir})')
                return False
            
            self.logger.info(f'{self.log_prefix} - Successfully fetched file: {pnm_file_name}')
            return True
            
        except Exception as e:
            self.logger.error(f'{self.log_prefix} - SCP Fetch Exception: {e}')
            return False
            
        finally:
            scp.disconnect()

    def _handle_sftp_fetch(self, pnm_file_name: str) -> bool:
        """
        Fetch a file from remote SFTP server.
        
        Args:
            pnm_file_name: Name of the file to fetch from remote server
            
        Returns:
            bool: True if file transfer successful, False otherwise
        """
        sys_config = SystemConfigSettings()
        
        self.logger.debug(f"{self.log_prefix} - SFTP: Connecting to: {sys_config.sftp_host}")
        
        sftp = SSHConnector(hostname=sys_config.sftp_host,
                                username=sys_config.sftp_user,
                                port=sys_config.sftp_port,
                                transfer_mode=SecureTransferMode.SFTP)
        
        try:
            if not sftp.connect(password=sys_config.sftp_password):
                self.logger.error(f'{self.log_prefix} - SFTP Connect Failure: Host: {sys_config.sftp_host}')
                return False
            
            remote_file_path = f'{sys_config.sftp_remote_dir}/{pnm_file_name}'
            if not sftp.receive_file(remote_path=remote_file_path,
                                    local_path=sys_config.save_dir):
                self.logger.error(f'{self.log_prefix} - SFTP Receive File Error (SRC:{remote_file_path} DST: {sys_config.save_dir})')
                return False
            
            self.logger.info(f'{self.log_prefix} - Successfully fetched file: {pnm_file_name}')
            return True
            
        except Exception as e:
            self.logger.error(f'{self.log_prefix} - SFTP Fetch Exception: {e}')
            return False
            
        finally:
            sftp.disconnect()

    def _handle_tftp_fetch(self, pnm_file_name: str) -> bool:
        """
        Fetch the specified PNM file via TFTP.

        Assumes the following attributes on self:
        - self.pnm_local_dir (str)    # local directory to save the downloaded file
        - self.log_prefix (str)       # used for consistent logging

        TFTP settings are read from SystemConfigCommonSettings:
        - tftp_host (str)
        - tftp_port (int)
        - tftp_timeout (int)
        - tftp_remote_dir (str)   # remote directory where PNM files live (if applicable)
        """
        try:
            connector = TFTPConnector(
                host=SystemConfigSettings.tftp_host,
                port=int(SystemConfigSettings.tftp_port))

        except Exception as e:
            self.logger.error(f"{self.log_prefix} - Exception during TFTP connecting: {e}")
            return False

        try:
            
            self.logger.info(
                f"{self.log_prefix} - Starting TFTP download from "
                f"{SystemConfigSettings.tftp_host}:{SystemConfigSettings.tftp_port}"
            )

            # Build remote filename (some tftp servers require just the basename)
            remote_name = (
                f"{SystemConfigSettings.tftp_remote_dir.rstrip('/')}/{pnm_file_name}"
                if SystemConfigSettings.tftp_remote_dir else
                pnm_file_name
            )
            local_path = os.path.join(SystemConfigSettings.save_dir, pnm_file_name)

            success = connector.download_file(remote_name, local_path)

            if not success:
                self.logger.error(
                    f"{self.log_prefix} - TFTP download failed for '{remote_name}'"
                )
                return False

            self.logger.info(
                f"{self.log_prefix} - Successfully fetched '{pnm_file_name}' via TFTP"
            )
            return True

        except Exception as e:
            self.logger.error(f"{self.log_prefix} - Exception during TFTP downloading: {e}")
            return False

    def _handle_ftp_fetch(self, pnm_file_name: str) -> bool:
        """
        Fetch the specified PNM file via FTP.

        Assumes the following attributes exist on self:
        - self.pnm_local_dir (str)    # local directory to save the downloaded file
        - self.log_prefix (str)       # used for consistent logging

        All FTP-specific settings are read from SystemConfigCommonSettings:
        - ftp_host (str)
        - ftp_port (int)
        - ftp_user (str)
        - ftp_password (str)
        - ftp_use_tls (bool)
        - ftp_timeout (int)
        - ftp_remote_dir (str)   # remote directory where PNM files live
        """
        sys_config = SystemConfigSettings()

        try:
            connector = FTPConnector(
                host=sys_config.ftp_host,
                port=sys_config.ftp_port,
                username=sys_config.ftp_user,
                password=sys_config.ftp_password,
                use_tls=sys_config.ftp_use_tls,
                timeout=sys_config.ftp_timeout
            )

            self.logger.debug(
                f"{self.log_prefix} - Connecting to FTP server "
                f"{sys_config.ftp_host}:{sys_config.ftp_port}"
            )
            if not connector.connect():
                self.logger.error(f"{self.log_prefix} - FTP connection failed")
                return False

            # Build remote and local paths
            remote_base = sys_config.ftp_remote_dir.rstrip("/") if sys_config.ftp_remote_dir else ""
            remote_path = f"{remote_base}/{pnm_file_name}" if remote_base else pnm_file_name

            local_path = os.path.join(self.pnm_local_dir, pnm_file_name)

            self.logger.debug(
                f"{self.log_prefix} - Downloading '{remote_path}' to '{local_path}'"
            )
            success = connector.download_file(remote_path, local_path)
            connector.disconnect()

            if not success:
                self.logger.error(
                    f"{self.log_prefix} - FTP download failed for '{remote_path}'"
                )
                return False

            self.logger.info(
                f"{self.log_prefix} - Successfully fetched '{pnm_file_name}' via FTP"
            )
            return True

        except Exception as e:
            self.logger.error(f"{self.log_prefix} - Exception during FTP fetch: {e}")
            return False

    def _handle_http_fetch(self, pnm_file_name: str) -> bool:
        # TODO: implement HTTP file fetch logic
        self.logger.debug(f"{self.log_prefix} - HTTP fetch not yet implemented")
        return False

    def _handle_https_fetch(self, pnm_file_name: str) -> bool:
        # TODO: implement HTTPS file fetch logic
        self.logger.debug(f"{self.log_prefix} - HTTPS fetch not yet implemented")
        return False
   
    async def _pnm_file_generator(self, test_type: DocsPnmCmCtlTest, suffix: str = "", ext: str = ".bin") -> str:
        """
        Generates the PNM file name based on the provided DocsPnmCmCtlTest, with optional suffix and extension.

        Args:
            test_type (DocsPnmCmCtlTest): The type of the test to generate the prefix.
            suffix (str, optional): A suffix added to the file name. Defaults to an empty string.
            ext (str, optional): The file extension. Defaults to ".bin".

        Returns:
            str: The generated PNM file name.
        """
        test_prefix = test_type.name.lower()

        if suffix:
            suffix = f'_{suffix}'

        file_name = f"{test_prefix}_{self.cm.get_mac_address}{suffix}_{Utils.time_stamp()}{ext}"

        transaction_id = await PnmFileTransaction().insert(self.cm, test_type, file_name)
        
        self.logger.debug(f"Generated PNM file name: {file_name} -> TransID: {transaction_id}")
        
        self._transactionId_pnmFile[transaction_id] = file_name

        return file_name

    def _get_transaction_id_by_filename(self, file_name: str) -> Optional[str]:
        """
        Return the transaction ID associated with the given file name.
        Assumes file names are unique. Returns None if not found.
        """
        for transaction_id, name in self._transactionId_pnmFile.items():
            if name == file_name:
                return transaction_id
        return None

    async def _generic_spectrum_analyzer_operation(self, filename:str="") -> Tuple[ServiceStatusCode, List[str]]:
        """
        Perform a generic spectrum-analyzer operation on the cable modem, supporting two retrieval modes:
        1. SNMP-based amplitude data return (AmplitudeData textual convention)
        2. PNM file return (download via TFTP once the CM writes the file)

        The same set of control parameters (frequency range, bin count, windowing, etc.) is used
        in both cases—avoiding duplicate “control-command” logic (DRY). Downstream, a separate helper
        method is called based on `spectrum_retrieval_type`.

        Extra options (from self.extra_options):
            • inactivity_timeout             (int, default=100)
                - Maximum seconds to wait for the CM to complete the measurement
            • first_segment_center_freq      (int, default=300_000_000)
                - Starting center frequency in Hz
            • last_segment_center_freq       (int, default=900_000_000)
                - Ending center frequency in Hz
            • segment_freq_span              (int, default=7_500_000)
                - Frequency span per segment in Hz
            • num_bins_per_segment           (int, default=256)
                - Number of bins (samples) per segment
            • noise_bw                       (int, default=110)
                - Equivalent noise bandwidth in Hz
            • window_function                (WindowFunction, default=WindowFunction.HANN)
                - Window function to apply to each segment
            • num_averages                   (int, default=1)
                - Number of averages to take
            • spectrum_retrieval_type        (SpectrumRetrievalType, default=SpectrumRetrievalType.FILE)
                - FILE: write to PNM file via TFTP (requires pnm_filename)
                - SNMP: return amplitude data directly via SNMP (no file write)

        Returns:
            Tuple[ServiceStatusCode, List[str]]:
                • On success: (ServiceStatusCode.SUCCESS, [<PNM filename>]) for FILE mode,
                  or (ServiceStatusCode.SUCCESS, []) for SNMP mode.
                • On failure: (ServiceStatusCode.SPEC_ANALYZER_NOT_AVAILABLE, []).

        Raises:
            None directly—errors are mapped to a failure status code.
        """
        self.logger.info(f"{self.log_prefix} - Entering into SPECTRUM-ANALYZER Mode (filename: {filename})")

        # Default: only SNMP control-command, no file write
        ctl_cmd_filename = Snmp_v2c.TRUE

        # Read optional overrides from extra_options
        inactivity_timeout = self.extra_options.get("inactivity_timeout", 100)

        # Frequency range (first and last segment center frequencies)
        first_segment_center_frequency = self.extra_options.get("first_segment_center_freq", 300_000_000)
        last_segment_center_frequency = self.extra_options.get("last_segment_center_freq", 993_000_000)

        # Per-segment configuration
        segment_frequency_span = self.extra_options.get("segment_freq_span", 1_000_000)
        num_bins_per_segment = self.extra_options.get("num_bins_per_segment", 256)
        equivalent_noise_bandwidth = self.extra_options.get("noise_bw", 110)
        window_function = self.extra_options.get("window_function", WindowFunction.HANN)
        number_of_averages = self.extra_options.get("num_averages", 1)

        # Decide retrieval mode: SNMP vs. TFTP/PNM-file
        spectrum_retrieval_type = self.extra_options.get(
            "spectrum_retrieval_type",
            SpectrumRetrievalType.FILE
        )

        if spectrum_retrieval_type == SpectrumRetrievalType.SNMP:
            self.logger.info(f"{self.log_prefix} - SPECTRUM-ANALYZER - SNMP-AMPLITUDE-DATA-RETURN")
            ctl_cmd_filename = Snmp_v2c.FALSE
        
        else:
            if not filename:
                self.logger.error(f"{self.log_prefix} - Missing 'filename' for FILE retrieval mode")
                return ServiceStatusCode.MISSING_PNM_FILENAME, []

        # Create and populate the control-command object
        spectrum_cmd = DocsIf3CmSpectrumAnalysisCtrlCmd(
            docsIf3CmSpectrumAnalysisCtrlCmdInactivityTimeout=inactivity_timeout,
            docsIf3CmSpectrumAnalysisCtrlCmdFirstSegmentCenterFrequency=first_segment_center_frequency,
            docsIf3CmSpectrumAnalysisCtrlCmdLastSegmentCenterFrequency=last_segment_center_frequency,
            docsIf3CmSpectrumAnalysisCtrlCmdSegmentFrequencySpan=segment_frequency_span,
            docsIf3CmSpectrumAnalysisCtrlCmdNumBinsPerSegment=num_bins_per_segment,
            docsIf3CmSpectrumAnalysisCtrlCmdEquivalentNoiseBandwidth=equivalent_noise_bandwidth,
            docsIf3CmSpectrumAnalysisCtrlCmdWindowFunction=window_function,
            docsIf3CmSpectrumAnalysisCtrlCmdNumberOfAverages=number_of_averages,
            docsIf3CmSpectrumAnalysisCtrlCmdEnable=Snmp_v2c.TRUE,
            docsIf3CmSpectrumAnalysisCtrlCmdFileName=filename,
            docsIf3CmSpectrumAnalysisCtrlCmdFileEnable=ctl_cmd_filename,)

        # Issue the SNMP SET for the control-command. The downstream logic
        # (not shown here) will branch to either:
        #   • SNMP:  set FileEnable = FALSE → wait for measurement → walk AmplitudeData
        #   • FILE:  set FileEnable = TRUE  → wait for measurement status → TFTP download
        if not await self.cm.setDocsIf3CmSpectrumAnalysisCtrlCmd(spectrum_cmd, spectrum_retrieval_type):
            self.logger.error(f"{self.log_prefix} - Spectrum Analyzer is Not Available")
            return ServiceStatusCode.SPEC_ANALYZER_NOT_AVAILABLE, []

        # On success, return the filename (if FILE mode) or an empty list (SNMP mode)
        if spectrum_retrieval_type == SpectrumRetrievalType.FILE:
            return ServiceStatusCode.SUCCESS, [filename]
        else:
            return ServiceStatusCode.SUCCESS, []
