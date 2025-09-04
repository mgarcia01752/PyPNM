
from __future__ import annotations

# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia

from enum import IntEnum

class ServiceStatusCode(IntEnum):
    '''
    SKIP_MESSAGE is to indicat not process the MessageResponse
    '''
    SKIP_MESSAGE_RESPONSE                   = -2
    UNKNOWN                                 = -1
    SUCCESS                                 =  0
    UNREACHABLE_PING                        =  1
    UNREACHABLE_SNMP                        =  2
    NO_PLC_FOUND                            =  3
    INVALID_PLC                             =  4
    TFTP_INET_MISMATCH                      =  5
    FILE_SET_FAIL                           =  6
    TEST_ERROR                              =  7
    MEASUREMENT_TIMEOUT                     =  8
    TFTP_SERVER_PATH_SET_FAIL               =  9
    NOT_READY_AFTER_FILE_CAPTURE            = 10
    COPY_PNM_FILE_TO_LOCAL_SAVE_DIR_FAILED  = 11
    TRANSACTION_RECORD_SET_FAILED           = 12
    UNSUPPORTED_IF_TYPE                     = 13
    NO_OFDM_CHAN_ID_INDEX_FOUND             = 14
    NO_OFDMA_CHAN_ID_INDEX_FOUND            = 15
    INVALID_INTERFACE_PARAMETERS            = 16
    FAILURE                                 = 17
    RESET_NOW_FAILED                        = 18
    PING_FAILED                             = 19
    MISSING_PNM_FILENAME                    = 20
    TFTP_PNM_FILE_UPLOAD_FAILURE            = 21
    NO_SCQAM_CHAN_ID_INDEX_FOUND            = 22
    NO_ATDMA_CHAN_ID_INDEX_FOUND            = 23
    MISSING_PNM_TEST_TYPE                   = 24
    
    SCP_PNM_FILE_FETCH_ERROR                = 30
    TFTP_PNM_FILE_FETCH_ERROR               = 31
    FTP_PNM_FILE_FETCH_ERROR                = 32
    SFTP_PNM_FILE_FETCH_ERROR               = 33
    HTTP_PNM_FILE_FETCH_ERROR               = 34
    SHTTP_PNM_FILE_FETCH_ERROR              = 35
    
    INVALID_DOCSIS_VERSION                  = 40
    NO_OFDMA_CHANNELS_EXIST                 = 41
    NO_OFDM_CHANNELS_EXIST                  = 42
    
    TRANSACTION_RECORD_GET_FAILED           = 200
    UNSUPPORTED_TEST_TYPE                   = 201
    CAPTURE_GROUP_NOT_FOUND                 = 202
    
    INVALID_OUTPUT_TYPE                     = 220
    
    DS_OFDM_RXMER_NOT_AVAILABLE             = 300
    
    SPEC_ANALYZER_NOT_AVAILABLE             = 400
    SPEC_ANALYZER_AMPLITUDE_DATA_TIMEOUT    = 401
    SPEC_ANALYZER_AMPLITUDE_DATA_NOT_FOUND  = 402
    SPEC_ANALYZER_DATA_RETRIVAL_ERROR       = 403
    SPEC_ANALYZER_SET_CONFIG_ERROR          = 404    
    
    DS_OFDM_MULIT_RXMER_FAILED              = 500
    MEASURE_MODE_INVALID                    = 501
    
    DS_OFDM_CHAN_EST_NOT_AVAILABLE          = 600
    
    DS_OFDM_FEC_SUMMARY_NOT_AVALIABLE       = 700
    
    DS_OFDM_MOD_PROFILE_NOT_AVALAIBLE       = 800
