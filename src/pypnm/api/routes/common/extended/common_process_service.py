# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia


import json
import logging

from pypnm.api.routes.common.classes.file_capture.pnm_file_transaction import PnmFileTransaction
from pypnm.api.routes.common.extended.common_messaging_service import (
    CommonMessagingService, MessageResponse, MessageResponseType)
from pypnm.api.routes.common.service.status_codes import ServiceStatusCode
from pypnm.config.config_manager import ConfigManager
from pypnm.lib.file_processor import FileProcessor
from pypnm.lib.utils import Utils
from pypnm.pnm.data_type.pnm_test_types import DocsPnmCmCtlTest
from pypnm.pnm.process.CmDsConstDispMeas import CmDsConstDispMeas
from pypnm.pnm.process.CmDsHist import CmDsHist
from pypnm.pnm.process.CmDsOfdmChanEstimateCoef import CmDsOfdmChanEstimateCoef
from pypnm.pnm.process.CmDsOfdmFecSummary import CmDsOfdmFecSummary
from pypnm.pnm.process.CmDsOfdmModulationProfile import CmDsOfdmModulationProfile
from pypnm.pnm.process.CmDsOfdmRxMer import CmDsOfdmRxMer
from pypnm.pnm.process.CmSpectrumAnalysis import CmSpectrumAnalysis
from pypnm.pnm.process.CmSpectrumAnalysisSnmp import CmSpectrumAnalysisSnmp
from pypnm.pnm.process.CmUsPreEq import CmUsPreEq

class CommonProcessService(CommonMessagingService):
    def __init__(self, message_response:MessageResponse, **extra_options):
        super().__init__()
        self.logger = logging.getLogger(self.__class__.__name__)
        self.pnm_file_dir = self.config_mgr = ConfigManager().get("PnmFileRetrieval", "save_dir")
        self._msg_rsp = message_response
        self.logger.info(f'CommonProcessService: {self._msg_rsp}')

    def process(self) -> MessageResponse:
        """
        Processes each item in the MessageResponse payload.

        Expected payload format:
            {
                "payload": [
                    {
                        "status": "SUCCESS",
                        "message_type": "PNM_FILE_TRANSACTION",
                        "message": {
                            "transaction_id": "275de83146e904d7",
                            "filename": "ds_ofdm_rxmer_per_subcar_00:50:f1:12:e2:63_954000000_1746501260.bin"
                        }
                    },
                    ...
                ]
            }

        Returns:
            MessageResponse: A success message if all payloads are processed,
                            or an error message if a transaction record is missing.
        """
        for payload in self._msg_rsp.payload: 
            status, message_type, message = MessageResponse.get_payload_msg(payload)

            self.logger.info(f'CommonProcessService.MessageResponse: MSG-TYPE: {message_type}')
            
            if status != ServiceStatusCode.SUCCESS.name:
                self.logger.error(f"Status Error: {status}")
                continue

            if message_type == MessageResponseType.PNM_FILE_TRANSACTION.name:
                transaction_id = message.get('transaction_id')
                transaction_record = PnmFileTransaction().get_record(transaction_id)

                if not transaction_record:
                    self.build_msg(ServiceStatusCode.TRANSACTION_RECORD_GET_FAILED)
                    pass

                self._process_pnm_measure_test(transaction_record)
   
            elif message_type == MessageResponseType.SNMP_DATA_RTN_SPEC_ANALYSIS.name:                             
                transaction_id = message.get('transaction_id')
                self.logger.info(f'process() -> Found TransactionID: {transaction_id}')
                
                transaction_record = PnmFileTransaction().get_record(transaction_id)
                self._process_pnm_measure_test(transaction_record)

        return self.send_msg()

    def _process_pnm_measure_test(self, transaction_record: dict) -> ServiceStatusCode:
        """
        Processes the provided PNM transaction record based on its test type.

        Args:
            transaction_record (dict): The transaction metadata including test type and filename.

        Returns:
            ServiceStatusCode: The result of the operation, indicating success or error type.
        """
        pnm_test_type = transaction_record[PnmFileTransaction().PNM_TEST_TYPE]

        if pnm_test_type == DocsPnmCmCtlTest.DS_OFDM_RXMER_PER_SUBCAR.name:
            self.logger.info(f"Processing {pnm_test_type} PNM data")
            
            file_name_dst = f'{self.pnm_file_dir}/{transaction_record[PnmFileTransaction.FILE_NAME]}'
            data = FileProcessor(file_name_dst).read_file()
            pnm_obj = CmDsOfdmRxMer(binary_data=data)            
            self.build_msg(ServiceStatusCode.SUCCESS, pnm_obj.to_dict())
            
        elif pnm_test_type == DocsPnmCmCtlTest.DS_OFDM_CODEWORD_ERROR_RATE.name:
            self.logger.info(f"Processing {pnm_test_type} PNM data")
            
            file_name_dst = f'{self.pnm_file_dir}/{transaction_record[PnmFileTransaction.FILE_NAME]}'
            data = FileProcessor(file_name_dst).read_file()
            pnm_obj = CmDsOfdmFecSummary(binary_data=data)            
            self.build_msg(ServiceStatusCode.SUCCESS, pnm_obj.to_dict())
            
        elif pnm_test_type == DocsPnmCmCtlTest.DS_OFDM_CHAN_EST_COEF.name:
            self.logger.info(f"Processing {pnm_test_type} PNM data")
            
            file_name_dst = f'{self.pnm_file_dir}/{transaction_record[PnmFileTransaction.FILE_NAME]}'
            data = FileProcessor(file_name_dst).read_file()
            pnm_obj = CmDsOfdmChanEstimateCoef(binary_data=data)            
            self.build_msg(ServiceStatusCode.SUCCESS, pnm_obj.to_dict())
            
        elif pnm_test_type == DocsPnmCmCtlTest.DS_CONSTELLATION_DISP.name:
            self.logger.info(f"Processing {pnm_test_type} PNM data")
            
            file_name_dst = f'{self.pnm_file_dir}/{transaction_record[PnmFileTransaction.FILE_NAME]}'
            data = FileProcessor(file_name_dst).read_file()
            pnm_obj = CmDsConstDispMeas(binary_data=data)            
            self.build_msg(ServiceStatusCode.SUCCESS, pnm_obj.to_dict())
            
        elif pnm_test_type == DocsPnmCmCtlTest.DS_HISTOGRAM.name:
            self.logger.info(f"Processing {pnm_test_type} PNM data")
            
            file_name_dst = f'{self.pnm_file_dir}/{transaction_record[PnmFileTransaction.FILE_NAME]}'
            data = FileProcessor(file_name_dst).read_file()
            pnm_obj = CmDsHist(binary_data=data)            
            self.build_msg(ServiceStatusCode.SUCCESS, pnm_obj.to_dict())
            
        elif pnm_test_type == DocsPnmCmCtlTest.DS_OFDM_MODULATION_PROFILE.name:
            self.logger.info(f"Processing {pnm_test_type} PNM data")
            
            file_name_dst = f'{self.pnm_file_dir}/{transaction_record[PnmFileTransaction.FILE_NAME]}'
            data = FileProcessor(file_name_dst).read_file()
            pnm_obj = CmDsOfdmModulationProfile(binary_data=data)            
            self.build_msg(ServiceStatusCode.SUCCESS, pnm_obj.to_dict())
            
        elif pnm_test_type == DocsPnmCmCtlTest.SPECTRUM_ANALYZER.name:
            self.logger.info("Processing DS_SPECTRUM_ANALYZER PNM data")

            file_name_dst = f'{self.pnm_file_dir}/{transaction_record[PnmFileTransaction.FILE_NAME]}'
            data = FileProcessor(file_name_dst).read_file()
            pnm_obj = CmSpectrumAnalysis(binary_data=data)            
            self.build_msg(ServiceStatusCode.SUCCESS, pnm_obj.to_dict())            
            
        elif pnm_test_type == DocsPnmCmCtlTest.US_PRE_EQUALIZER_COEF.name:
            self.logger.info(f"Processing {pnm_test_type} PNM data")
            
            file_name_dst = f'{self.pnm_file_dir}/{transaction_record[PnmFileTransaction.FILE_NAME]}'
            data = FileProcessor(file_name_dst).read_file()
            pnm_obj = CmUsPreEq(binary_data=data)            
            self.build_msg(ServiceStatusCode.SUCCESS, pnm_obj.to_dict())
        
        elif pnm_test_type == DocsPnmCmCtlTest.SPECTRUM_ANALYZER_SNMP_AMP_DATA.name:
            self.logger.info(f"Processing {pnm_test_type} PNM data")

            file_name_dst = f'{self.pnm_file_dir}/{transaction_record[PnmFileTransaction.FILE_NAME]}'
            data = FileProcessor(file_name_dst).read_file()
            pnm_obj = CmSpectrumAnalysisSnmp(data)
            FileProcessor(f'output/spec-ana-{Utils.time_stamp()}.json').write_file(json.dumps(pnm_obj.to_dict()))
            self.build_msg(ServiceStatusCode.SUCCESS, pnm_obj.to_dict())
            
        else:
            self.logger.error(f"Unsupported PNM test type: {pnm_test_type}")
            return ServiceStatusCode.UNSUPPORTED_TEST_TYPE

        return ServiceStatusCode.SUCCESS
