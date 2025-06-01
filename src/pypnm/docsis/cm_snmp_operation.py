# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia

from enum import Enum
import logging
import time
from typing import List, Tuple, Union
from pysnmp.proto.rfc1902 import (OctetString, Counter32, Bits, 
                                  Counter64, Gauge32, Integer, 
                                  Integer32, IpAddress)
from pypnm.docsis.data_type.DocsDevEventEntry import DocsDevEventEntry
from pypnm.docsis.data_type.DocsIf31CmDsOfdmChanEntry import DocsIf31CmDsOfdmChanEntry
from pypnm.docsis.data_type.DocsIf31CmDsOfdmProfileStatsEntry import DocsIf31CmDsOfdmProfileStatsEntry
from pypnm.docsis.data_type.DocsIf31CmSystemCfgState import DocsIf31CmSystemCfgDiplexState
from pypnm.docsis.data_type.DocsIf31CmUsOfdmaChanEntry import DocsIf31CmUsOfdmaChanEntry
from pypnm.docsis.data_type.DocsIfDownstreamChannel import DocsIfDownstreamChannel
from pypnm.docsis.data_type.DocsIfSignalQualityEntry import DocsIfSignalQuality
from pypnm.docsis.data_type.DocsIfUpstreamChannelEntry import DocsIfUpstreamChannelEntry
from pypnm.docsis.data_type.DsCmConstDisplay import CmDsConstellationDisplayConst
from pypnm.docsis.data_type.sysDescr import SystemDescriptor
from pypnm.docsis.lib.pnm_bulk_data import DocsPnmBulkDataGroup, DocsPnmBulkFileEntry
from pypnm.lib.inet import Inet
from pypnm.lib.inet_utils import InetUtils
from pypnm.lib.mac_address import MacAddress
from pypnm.pnm.data_type.DocsEqualizerData import DocsEqualizerData
from pypnm.pnm.data_type.DocsIf3CmSpectrumAnalysisCtrlCmd import (
    DocsIf3CmSpectrumAnalysisCtrlCmd, SpectrumRetrievalType)
from pypnm.pnm.data_type.pnm_test_types import DocsPnmCmCtlTest
from pypnm.snmp.compiled_oids import COMPILED_OIDS
from pypnm.snmp.snmp_v2c import Snmp_v2c
from typing import Optional

from pypnm.snmp.modules import DocsPnmBulkUploadControl, DocsisIfType

class DocsPnmBulkFileUploadStatus(Enum):
    """Represents the upload status of a DOCSIS PNM bulk data file."""
    OTHER = 1
    AVAILABLE_FOR_UPLOAD = 2
    UPLOAD_IN_PROGRESS = 3
    UPLOAD_COMPLETED = 4
    UPLOAD_PENDING = 5
    UPLOAD_CANCELLED = 6
    ERROR = 7

    def describe(self) -> str:
        """Returns a human-readable description of the enum value."""
        return {
            self.OTHER: "Other: unspecified condition",
            self.AVAILABLE_FOR_UPLOAD: "Available: ready for upload",
            self.UPLOAD_IN_PROGRESS: "In progress: upload ongoing",
            self.UPLOAD_COMPLETED: "Completed: upload successful",
            self.UPLOAD_PENDING: "Pending: blocked until conditions clear",
            self.UPLOAD_CANCELLED: "Cancelled: upload was stopped",
            self.ERROR: "Error: upload failed",
        }.get(self, "Unknown status")

    def to_dict(self) -> dict:
        """Serializes the status for API or JSON usage."""
        return {"name": self.name, "value": self.value, "description": self.describe()}

    def __str__(self):
        return super().__str__()

    @classmethod
    def from_value(cls, value: int):
        """Helper method to get the enum member from an integer value"""
        if value == 1:
            return cls.TFTP
        elif value == 2:
            return cls.HTTP
        elif value == 3:
            return cls.HTTPS
        else:
            raise ValueError(f"Unsupported value: {value}")

class MeasStatusType(Enum):
    """
    Enumeration of measurement status types as defined in DOCSIS 3.1 CM-OSSI.
    """
    OTHER = 1                     # Any state not described below
    INACTIVE = 2                  # Test not started or in progress
    BUSY = 3                      # Test is in progress
    SAMPLE_READY = 4              # Test completed, data ready
    ERROR = 5                     # Error occurred, data may be invalid
    RESOURCE_UNAVAILABLE = 6      # Test could not start due to lack of resources
    SAMPLE_TRUNCATED = 7          # Requested data exceeds supported file size
    INTERFACE_MODIFICATION = 8    # Interface numbering changed due to DBC or primary backup switch
   
    def __str__(self) -> str:
        return self.name.lower()    

class DocsPnmCmCtlStatus(Enum):
    """
    Enum representing the overall status of the PNM test platform.

    Based on the SNMP object `docsPnmCmCtlStatus`, this enum is used to manage
    test initiation constraints on the Cable Modem (CM).
    """

    OTHER = 1
    READY = 2
    TEST_IN_PROGRESS = 3
    TEMP_REJECT = 4
    SNMP_ERROR = 255

    def __str__(self) -> str:
        return self.name.lower()

class FecSummaryType(Enum):
    """
    Enum for FEC Summary Type used in DOCSIS PNM SNMP operations.
    """
    TEN_MIN = 2
    TWENTY_FOUR_HOUR = 3

    @classmethod
    def choices(cls):
        return {e.name: e.value for e in cls}

    @classmethod
    def from_value(cls, value: int):
        try:
            return cls(value)
        except ValueError:
            raise ValueError(f"Invalid FEC Summary Type value: {value}")

class CmSnmpOperation:
    """
    Cable Modem SNMP Operation Handler.

    This class provides methods to perform SNMP operations 
    (GET, WALK, etc.) specifically for Cable Modems.

    Attributes:
        _inet (str): IP address of the Cable Modem.
        _community (str): SNMP community string used for authentication.
        _port (int): SNMP port (default: 161).
        _snmp (Snmp_v2c): SNMP client instance for communication.
        logger (logging.Logger): Logger instance for this class.
    """

    def __init__(self, inet: Inet, write_community: str, port: int = Snmp_v2c.SNMP_PORT):
        """
        Initialize a CmSnmpOperation instance.

        Args:
            inet (str): IP address of the Cable Modem.
            write_community (str): SNMP community string (usually 'private' for read/write access).
            port (int, optional): SNMP port number. Defaults to standard SNMP port 161.

        """
        self.logger = logging.getLogger(self.__class__.__name__)

        if not isinstance(inet, Inet):
            self.logger.error(f'CmSnmpOperation() inet is of an Invalid Type: {type(inet)} , expecting Inet')
            exit(1)
        
        self._inet:Inet = inet
        self._community = write_community
        self._port = port
        self._snmp = Snmp_v2c(host=inet, community=write_community)
  
    async def _get_value(self, oid_suffix: str, value_type: Union[type, str] = str) -> Optional[Union[str, bytes, int]]:
        """
        Retrieves a value from SNMP for the given OID suffix, processes the value based on the expected type,
        and handles any error cases that may arise during the process.

        Parameters:
        - oid_suffix (str): The suffix of the OID to query.
        - value_type (type or str): The type to which the value should be converted. Defaults to `str`.

        Returns:
        - Optional[Union[str, bytes, int]]: The value retrieved from SNMP, converted to the specified type, 
          or `None` if there was an error or no value could be obtained.
        """
        result = await self._snmp.get(f"{COMPILED_OIDS[oid_suffix]}.0")
        
        if result is None:
            logging.warning(f"Failed to get value for {oid_suffix}")
            return None
        
        val = Snmp_v2c.snmp_get_result_value(result)[0]
        logging.debug(f"get_value() -> Val:{val}")
        
        # Check if the result is an error message, and return None if it is
        if isinstance(val, str) and "No Such Instance currently exists at this OID" in val:
            logging.warning(f"SNMP error for {oid_suffix}: {val}")
            return None
        
        # Handle string and bytes conversions explicitly
        if value_type == str:
            if isinstance(val, bytes):  # if val is bytes, decode it
                return val.decode('utf-8', errors='ignore')  # or replace with appropriate encoding
            return str(val)
        
        if value_type == bytes:
            if isinstance(val, str):  # if val is a string, convert to bytes
                # Remove any '0x' prefix or spaces before converting
                val = val.strip().lower()
                if val.startswith('0x'):
                    val = val[2:]  # Remove '0x' prefix
                
                # Ensure the string is a valid hex format
                try:
                    return bytes.fromhex(val)  # convert the cleaned hex string to bytes
                except ValueError as e:
                    logging.error(f"Invalid hex string: {val}. Error: {e}")
                    return None
            return val  # assuming it's already in bytes
        
        # Default case (int conversion)
        try:
            return value_type(val)
        except ValueError as e:
            logging.error(f"Failed to convert value for {oid_suffix}: {val}. Error: {e}")
            return None

######################
# SNMP Get Operation #
######################
    
    def getWriteCommunity(self) -> str:
        return self._community
    
    async def getIfTypeIndex(self, doc_if_type: DocsisIfType) -> List[int]:
        """
        Retrieve interface indexes that match the specified DOCSIS IANA ifType.

        Args:
            doc_if_type (DocsisIfType): The DOCSIS interface type to filter by.

        Returns:
            List[int]: A list of interface indexes matching the given ifType.
        """
        self.logger.debug(f"Starting getIfTypeIndex for ifType: {doc_if_type}")

        indexes: List[int] = []

        # Perform SNMP walk
        results = await self._snmp.walk(COMPILED_OIDS["ifType"])

        if not results:
            self.logger.warning("No results found during SNMP walk for ifType.")
            return indexes

        # Iterate through results and filter by the specified DOCSIS interface type
        for result in results:
            try:
                ifType_name = doc_if_type.name
                ifType_value = doc_if_type.value

                # Compare ifType value with the result value
                if ifType_value == int(result[1]):
                    self.logger.debug(f"ifType-Name: ({ifType_name}) -> ifType-Value: ({ifType_value}) -> Found: {result}")
                    
                    # Extract index using a helper method (ensure it returns a valid index)
                    index = Snmp_v2c.get_oid_index(str(result[0]))
                    if index is not None:
                        indexes.append(index)
                    else:
                        self.logger.warning(f"Invalid OID index for result: {result}")
            except Exception as e:
                self.logger.error(f"Error processing result {result}: {e}")
        
        # Return the list of found indexes
        return indexes

    async def getSysDescr(self) -> SystemDescriptor:
        """
        Retrieves and parses the sysDescr SNMP value into a SysDescr dataclass.

        Returns:
            SysDescr if successful, otherwise empty SysDescr.empty().
        """
        self.logger.debug("Starting getSysDescr...")

        result = await self._snmp.get(f'{COMPILED_OIDS["sysDescr"]}.0')

        if not result:
            self.logger.warning("SNMP get failed or returned empty for sysDescr.")
            return SystemDescriptor.empty()

        values = Snmp_v2c.get_result_value(result)
        
        if not values:
            self.logger.warning("No sysDescr value parsed.")
            return SystemDescriptor.empty()
        
        self.logger.debug(f"SysDescr: {values}")
        
        try:
            parsed = SystemDescriptor.parse(values)
            self.logger.debug(f"Successfully parsed sysDescr: {parsed}")
            return parsed
        except ValueError as e:
            self.logger.error(f"Failed to parse sysDescr: {values}. Error: {e}")
            return SystemDescriptor.empty()

    async def getDocsPnmBulkDataGroup(self) -> DocsPnmBulkDataGroup:
        """
        Retrieves the current DocsPnmBulkDataGroup SNMP configuration from the device.

        Returns:
            DocsPnmBulkDataGroup: A dataclass populated with SNMP values.
        """
        
        return DocsPnmBulkDataGroup(
            docsPnmBulkDestIpAddrType=await self._get_value("docsPnmBulkDestIpAddrType", int),
            docsPnmBulkDestIpAddr=InetUtils.binary_to_inet(await self._get_value("docsPnmBulkDestIpAddr", bytes)),
            docsPnmBulkDestPath=await self._get_value("docsPnmBulkDestPath", str),
            docsPnmBulkUploadControl=await self._get_value("docsPnmBulkUploadControl", int)
        )
  
    async def _get_docs_pnm_bulk_file_group(self) -> List[DocsPnmBulkFileEntry]:
        """
        Asynchronously retrieves a bulk list of PNM file entries from SNMP.

        This method performs an SNMP walk on the OID specified by `COMPILED_OIDS["docsPnmBulkFileEntry"]` 
        and processes the resulting entries. Each entry is fetched using the SNMP `walk` operation, 
        and its value is extracted using the `Snmp_v2c.snmp_get_result_value()` function.

        Currently, this method does not return the processed results. The functionality is a placeholder
        and needs further implementation for handling the results properly. 

        TODO:
            - Implement result handling for SNMP entries.
            - Return a list of processed `DocsPnmBulkFileEntry` objects.

        Returns:
            List[DocsPnmBulkFileEntry]: An empty list is returned for now, as result handling is pending.
        """
        
        # Perform SNMP walk to retrieve the bulk file entries
        result = self._snmp.walk(f'{COMPILED_OIDS["docsPnmBulkFileEntry"]}')
        
        # Initialize a list to store processed entries (for future use)
        entries = []
        
        for entry in result:
            
            # Extract the value from the SNMP entry
            value = Snmp_v2c.snmp_get_result_value(entry)
            
            # Future code will process the value into a DocsPnmBulkFileEntry instance
            # entries.append(DocsPnmBulkFileEntry(...))
        
        # TODO: Return processed list of entries once functionality is implemented
        return entries
        
    async def getDocsPnmCmCtlStatus(self, max_retry:int=1) -> DocsPnmCmCtlStatus:
        """
        Fetches the current Docs PNM CmCtlStatus.

        This method retrieves the Docs PNM CmCtlStatus and retries up to a specified number of times 
        if the response is not valid. The possible statuses are:
        - 1: other
        - 2: ready
        - 3: testInProgress
        - 4: tempReject

        Parameters:
        - max_retry (int, optional): The maximum number of retries to obtain the status (default is 1).

        Returns:
        - DocsPnmCmCtlStatus: The Docs PNM CmCtlStatus as an enum value. Possible values:
        - DocsPnmCmCtlStatus.OTHER
        - DocsPnmCmCtlStatus.READY
        - DocsPnmCmCtlStatus.TEST_IN_PROGRESS
        - DocsPnmCmCtlStatus.TEMP_REJECT

        If the status cannot be retrieved after the specified retries, the method will return `DocsPnmCmCtlStatus.TEMP_REJECT`.
        """
        count = 1
        while True:
            
            result = await self._snmp.get(f'{COMPILED_OIDS["docsPnmCmCtlStatus"]}.0')
            
            if result is None:
                time.sleep(2)
                self.logger.warning(f"Not getting a proper docsPnmCmCtlStatus response, retrying: ({count} of {max_retry})")

                if count >= max_retry:
                    self.logger.error(f"Reached max retries: ({max_retry})")
                    return DocsPnmCmCtlStatus.TEMP_REJECT

                count += 1
                continue
            else:
                break
            
        if not result:
            self.logger.error(f'No results found for docsPnmCmCtlStatus: {DocsPnmCmCtlStatus.SNMP_ERROR}')
            return DocsPnmCmCtlStatus.SNMP_ERROR
            
        status_value = int(Snmp_v2c.snmp_get_result_value(result)[0])

        return DocsPnmCmCtlStatus(status_value)

    async def getIfPhysAddress(self, if_type: DocsisIfType = DocsisIfType.docsCableMaclayer) -> MacAddress:
        """
        Get the physical MAC address for the specified DOCSIS interface type.

        Args:
            if_type (DocsisIfType, optional): DOCSIS interface type to query. Defaults to docsCableMaclayer.

        Returns:
            MacAddress: The MAC address object representing the IfPhysAddress.
        """
        if_indexes = await self.getIfTypeIndex(if_type)
        self.logger.debug(f"{if_type.name} -> {if_indexes}")

        if not if_indexes:
            raise RuntimeError(f"No interfaces found for {if_type.name}")

        result = await self._snmp.get(f'{COMPILED_OIDS["ifPhysAddress"]}.{if_indexes[0]}')
        self.logger.debug(f"getIfPhysAddress() -> {result}")

        # Extract and normalize MAC address value
        mac_address_value = Snmp_v2c.snmp_get_result_value(result)[0]
        if isinstance(mac_address_value, OctetString):
            mac_address_value = bytes(mac_address_value)

        return MacAddress(mac_address_value)
    
    async def getDocsIfCmDsScQamChanChannelIdIndex(self) -> List[int]:
        """
        Retrieve the list of DOCSIS 3.0 downstream SC-QAM channel indices (i.e., QAM64 or QAM256).

        Returns:
            List[int]: A list of SC-QAM channel indices present on the device.
        """
        sq_qam_idx_list: List[int] = []
        oid_channel_id = COMPILED_OIDS["docsIfDownChannelId"]
        
        try:
            results = await self._snmp.walk(oid_channel_id)
            if not results:
                self.logger.warning(f"No results found for OID {oid_channel_id}")
                return []

            idx_list = Snmp_v2c.extract_last_oid_index(results)

            oid_modulation = COMPILED_OIDS["docsIfDownChannelModulation"]
            for idx in idx_list:
                result = await self._snmp.get(f'{oid_modulation}.{idx}')
                
                if not result:
                    self.logger.warning(f"SNMP get failed or returned empty docsIfDownChannelModulation for index {idx}.")
                    continue

                # Assuming the result is a tuple (oid, value)
                val = Snmp_v2c.snmp_get_result_value(result)[0]
                try:
                    modulation = int(val)
                except ValueError:
                    self.logger.warning(f"Failed to convert modulation value '{val}' to int for index {idx}. Skipping.")
                    continue

                if modulation in (3, 4):  # QAM64 or QAM256
                    sq_qam_idx_list.append(idx)

            return sq_qam_idx_list

        except Exception as e:
            self.logger.error(f"Failed to retrieve SC-QAM channel indices from {oid_channel_id}: {e}")
            return []

    async def getDocsIfCmUsTdmaChanChannelIdIndex(self) -> List[int]:
        """
        Retrieve the list of DOCSIS 3.0 upstream TDMA/ATDMA channel indices (i.e., TDMA or ATDMA).

        Returns:
            List[int]: A list of TDMA/ATDMA channel indices present on the device.
        """
        idx_list: List[int] = []
        oid_channel_id = COMPILED_OIDS["docsIfUpChannelId"]
        
        try:
            results = await self._snmp.walk(oid_channel_id)
            if not results:
                self.logger.warning(f"No results found for OID {oid_channel_id}")
                return []

            index_list = Snmp_v2c.extract_last_oid_index(results)

            oid_modulation = COMPILED_OIDS["docsIfUpChannelType"]
            
            for idx in index_list:
                
                result = await self._snmp.get(f'{oid_modulation}.{idx}')
                
                if not result:
                    self.logger.warning(f"SNMP get failed or returned empty docsIfUpChannelType for index {idx}.")
                    continue

                val = Snmp_v2c.snmp_get_result_value(result)[0]

                try:
                    channel_type = int(val)
                    
                except ValueError:
                    self.logger.warning(f"Failed to convert channel-type value '{val}' to int for index {idx}. Skipping.")
                    continue
                
                '''
                    DocsisUpstreamType ::= TEXTUAL-CONVENTION
                    STATUS          current
                    DESCRIPTION
                            "Indicates the DOCSIS Upstream Channel Type.
                            'unknown' means information not available.
                            'tdma' is related to TDMA, Time Division
                            Multiple Access; 'atdma' is related to A-TDMA,
                            Advanced Time Division Multiple Access,
                            'scdma' is related to S-CDMA, Synchronous
                            Code Division Multiple Access.
                            'tdmaAndAtdma is related to simultaneous support of
                            TDMA and A-TDMA modes."
                    SYNTAX INTEGER {
                        unknown(0),
                        tdma(1),
                        atdma(2),
                        scdma(3),
                        tdmaAndAtdma(4)
                    }
         
                '''
                
                if channel_type != 0: # 0 means OFDMA in this case
                    idx_list.append(idx)

            return idx_list

        except Exception as e:
            self.logger.error(f"Failed to retrieve SC-QAM channel indices from {oid_channel_id}: {e}")
            return []

    async def getDocsIf31CmDsOfdmChannelIdIndex(self) -> List[int]:
        """
        Retrieve the list of Docsis 3.1 downstream OFDM channel indices.

        Returns:
            List[int]: A list of channel indices present on the device.
        """
        oid = COMPILED_OIDS["docsIf31CmDsOfdmChanChannelId"]
        try:
            results = await self._snmp.walk(oid)
            if not results:
                self.logger.warning(f"No results found for OID {oid}")
                return []
            return Snmp_v2c.extract_last_oid_index(results)
        except Exception as e:
            self.logger.error(f"Failed to retrieve OFDM channel indices from {oid}: {e}")
            return []

    async def getDocsIf31CmUsOfdmaChanChannelIdIndex(self) -> List[int]:
        """
        Get the Docsis 3.1 upstream OFDMA channels.

        Returns:
            List[int]: A list of OFDMA channel indices present on the device.
        """
        oid = COMPILED_OIDS["docsIf31CmUsOfdmaChanChannelId"]
        try:
            results = await self._snmp.walk(oid)
            if not results:
                self.logger.warning(f"No results found for OID {oid}")
                return []
            return Snmp_v2c.extract_last_oid_index(results)
        except Exception as e:
            self.logger.error(f"Failed to retrieve OFDMA channel indices from {oid}: {e}")
            return []

    async def getDocsIf31CmDsOfdmChanPlcFreq(self) -> List[Tuple[int, int]]:
        """
        Retrieve the PLC frequencies of DOCSIS 3.1 downstream OFDM channels.

        Returns:
            List[Tuple[int, int]]: A list of tuples where each tuple contains:
                - the index (int) of the OFDM channel
                - the PLC frequency (int, in Hz)
        """
        oid = COMPILED_OIDS["docsIf31CmDsOfdmChanPlcFreq"]
        self.logger.debug(f"Walking OID for PLC frequencies: {oid}")

        try:
            results = await self._snmp.walk(oid)
            idx_plc_freqs = Snmp_v2c.snmp_get_result_last_idx_value(results)

            self.logger.debug(f"Retrieved PLC Frequencies: {idx_plc_freqs}")
            return idx_plc_freqs
        except Exception as e:
            self.logger.error(f"Failed to retrieve PLC frequencies from OID {oid}: {e}")
            return []

    async def getDocsPnmCmOfdmChEstCoefMeasStatus(self, ofdm_idx: int) -> int:
        '''
        Retrieves the measurement status of OFDM channel estimation coefficients.

        Parameters:
        - ofdm_idx (int): The OFDM index.

        Returns:
        int: The measurement status.
        '''
        result = await self._snmp.get(f'{COMPILED_OIDS["docsPnmCmOfdmChEstCoefMeasStatus"]}.{ofdm_idx}')
        return int(Snmp_v2c.snmp_get_result_value(result)[0])

    async def getCmDsOfdmProfileStatsConfigChangeCt(self, ofdm_idx: int) -> dict[int,dict[int,int]]:
        """
        Retrieve the count of configuration change events for a specific OFDM profile.

        Parameters:
        - ofdm_idx (int): The index of the OFDM profile.

        Returns:
            dict[ofdm_idx, dict[profile_id, count_change]]
        
        TODO: Need to get back, not really working
        
        """
        result = self._snmp.walk(f'{COMPILED_OIDS["docsIf31CmDsOfdmProfileStatsConfigChangeCt"]}.{ofdm_idx}')
        profile_change_count = Snmp_v2c.snmp_get_result_value(result)[0]
        return profile_change_count
      
    async def _getDocsIf31CmDsOfdmChanEntry(self) -> List[DocsIf31CmDsOfdmChanEntry]:
        """
        Asynchronously retrieve all DOCSIS 3.1 downstream OFDM channel entries.

        This method queries SNMP for each available OFDM channel index
        and populates a DocsIf31CmDsOfdmChanEntry object with its SNMP attributes.

        NOTE:
            This is an async method. You must use 'await' when calling it.

        Returns:
            List[DocsIf31CmDsOfdmChanEntry]: 
                A list of populated DocsIf31CmDsOfdmChanEntry objects, 
                each representing one OFDM downstream channel.

        Raises:
            Exception: If SNMP queries fail or unexpected errors occur.
        """
        entries: List[DocsIf31CmDsOfdmChanEntry] = []

        # Get all OFDM Channel Indexes
        channel_indices = await self.getDocsIf31CmDsOfdmChannelIdIndex()

        for idx in channel_indices:
            self.logger.debug(f"Processing OFDM Channel Index: {idx}")
            oce = DocsIf31CmDsOfdmChanEntry(ofdm_idx=idx)

            # Iterate over all member attributes
            for member_name in oce.get_member_list():
                oid_base = COMPILED_OIDS.get(member_name)

                if not oid_base:
                    self.logger.warning(f"OID base not found for {member_name}")
                    continue

                oid = f"{oid_base}.{idx}"
                result = await self._snmp.get(oid)

                if result is not None:
                    self.logger.debug(f"Retrieved SNMP value for Member: {member_name} -> OID: {oid}")
                    try:
                        value = Snmp_v2c.snmp_get_result_value(result)
                        setattr(oce, member_name, value)
                    except (ValueError, TypeError) as e:
                        self.logger.error(f"Failed to set '{member_name}' with value '{result}': {e}")
                else:
                    self.logger.warning(f"No SNMP response received for OID: {oid}")

            entries.append(oce)

        return entries

    async def getDocsIfSignalQuality(self) -> List[DocsIfSignalQuality]:
        """
        Retrieves signal quality metrics for all downstream QAM channels.

        This method queries the SNMP agent for the list of downstream QAM channel indexes,
        and for each index, creates a `DocsIfSignalQuality` instance, populates it with SNMP data,
        and collects it into a list.

        Returns:
            List[DocsIfSignalQuality]: A list of signal quality objects, one per downstream channel.
        """
        sig_qual_list: List[DocsIfSignalQuality] = []

        indices = await self.getDocsIfCmDsScQamChanChannelIdIndex()
        if not indices:
            self.logger.warning("No downstream channel indices found.")
            return sig_qual_list

        for idx in indices:
            obj = DocsIfSignalQuality(index=idx, snmp=self._snmp)
            await obj.start()
            sig_qual_list.append(obj)

        return sig_qual_list

    async def getDocsIfDownstreamChannel(self) -> List[DocsIfDownstreamChannel]:
        """
        Retrieves signal quality metrics for all downstream QAM channels.

        This method queries the SNMP agent for the list of downstream QAM channel indexes,
        and for each index, creates a `DocsIfDownstreamChannel` instance, populates it with SNMP data,
        and collects it into a list.

        Returns:
            List[DocsIfDownstreamChannel]: A list of signal quality objects, one per downstream channel.
        """
        channel_list: List[DocsIfDownstreamChannel] = []

        indices = await self.getDocsIfCmDsScQamChanChannelIdIndex()
        if not indices:
            self.logger.warning("No downstream sc-qam channel indices found.")
            return channel_list

        for idx in indices:
            obj = DocsIfDownstreamChannel(index=idx, snmp=self._snmp)
            await obj.start()
            channel_list.append(obj)

        return channel_list

    async def getDocsIf31CmUsOfdmaChanEntry(self) -> List[DocsIf31CmUsOfdmaChanEntry]:
        """
        Retrieves and initializes all OFDMA channel entries from Snmp_v2c.

        Returns:
            List[DocsIf31CmUsOfdmaChanEntry]: List of populated OFDMA channel objects.
        """
        channel_list: List[DocsIf31CmUsOfdmaChanEntry] = []

        try:
            indices = await self.getDocsIf31CmUsOfdmaChanChannelIdIndex()
            if not indices:
                self.logger.warning("No upstream OFDMA indices found.")
                return channel_list

            for idx in indices:
                entry = DocsIf31CmUsOfdmaChanEntry(index=idx, snmp=self._snmp)
                await entry.start()
                channel_list.append(entry)

        except Exception as e:
            self.logger.exception("Failed to retrieve OFDMA channel entries")

        return channel_list

    async def getDocsIfUpstreamChannelEntry(self) -> List[DocsIfUpstreamChannelEntry]:
        """
        Retrieves and initializes all ATDMA US channel entries from Snmp_v2c.

        Returns:
            List[DocsIfUpstreamChannelEntry]: List of populated ATDMA channel objects.
        """
        channel_list: List[DocsIfUpstreamChannelEntry] = []

        try:
            indices = await self.getDocsIfCmUsTdmaChanChannelIdIndex()
            
            if not indices:
                self.logger.warning("No upstream ATDMA indices found.")
                return channel_list
            
            for idx in indices:
                entry = DocsIfUpstreamChannelEntry(index=idx, snmp=self._snmp)
                await entry.start()
                channel_list.append(entry)

        except Exception as e:
            self.logger.exception("Failed to retrieve ATDMA channel entries")

        return channel_list  

    async def getEventEntryIndex(self) -> List[int]:
        """
        Retrieves the list of index values for the docsDevEventEntry table.

        Returns:
            List[int]: A list of SNMP index integers.
        """
        oid = COMPILED_OIDS["docsDevEvId"]

        results = await self._snmp.walk(oid)

        if not results:
            self.logger.warning(f"No results found for OID {oid}")
            return []

        return Snmp_v2c.extract_last_oid_index(results)

    async def getDocsDevEventEntry(self, to_dict: bool = False) -> Union[List['DocsDevEventEntry'], List[dict]]:
        """
        Retrieves all DocsDevEventEntry SNMP table entries.

        Args:
            to_dict (bool): If True, returns a list of dictionaries instead of DocsDevEventEntry instances.

        Returns:
            Union[List[DocsDevEventEntry], List[dict]]: A list of event log entries.
        """
        event_entries = []

        try:
            indices = await self.getEventEntryIndex()

            if not indices:
                self.logger.warning("No DocsDevEventEntry indices found.")
                return event_entries

            for idx in indices:
                entry = DocsDevEventEntry(index=idx, snmp=self._snmp)
                await entry.start()
                event_entries.append(entry.to_dict() if to_dict else entry)

        except Exception as e:
            self.logger.exception("Failed to retrieve DocsDevEventEntry entries")

        return event_entries

    async def getDocsIf31CmDsOfdmChanEntry(self) -> List[DocsIf31CmDsOfdmChanEntry]:
        """
        Asynchronously retrieves and populates a list of `DocsIf31CmDsOfdmChanEntry` entries.

        This method fetches the indices of the DOCSIS 3.1 CM DS OFDM channels, creates
        `DocsIf31CmDsOfdmChanEntry` objects for each index, and populates their attributes
        by making SNMP queries. The entries are returned as a list.

        Returns:
            List[DocsIf31CmDsOfdmChanEntry]: A list of `DocsIf31CmDsOfdmChanEntry` objects.

        Raises:
            Exception: If any unexpected error occurs during the process of fetching or processing.
        """
        
        ofdm_chan_entry: List[DocsIf31CmDsOfdmChanEntry] = []

        try:
            indices = await self.getDocsIf31CmDsOfdmChannelIdIndex()

            if not indices:
                self.logger.warning("No DocsIf31CmDsOfdmChanChannelId indices found.")
                return ofdm_chan_entry

            for idx in indices:
                entry = DocsIf31CmDsOfdmChanEntry(index=idx, snmp=self._snmp)
                await entry.start()
                ofdm_chan_entry.append(entry)

        except Exception as e:
            self.logger.exception("Failed to retrieve DocsIf31CmDsOfdmChanEntry entries")

        return ofdm_chan_entry
    
    async def getDocsIf31CmSystemCfgDiplexState(self) -> DocsIf31CmSystemCfgDiplexState:
        """
        Asynchronously retrieves the DOCS-IF31-MIB system configuration state and populates the `DocsIf31CmSystemCfgState` object.

        This method will fetch the necessary MIB data, populate the attributes of the
        `DocsIf31CmSystemCfgState` object, and return the object.

        Returns:
            DocsIf31CmSystemCfgState: An instance of the `DocsIf31CmSystemCfgState` class with populated data.
        """
        obj = DocsIf31CmSystemCfgDiplexState(self._snmp)
        await obj.start()
        
        return obj
    
    async def getDocsIf31CmDsOfdmProfileStatsEntry(self) -> List[DocsIf31CmDsOfdmProfileStatsEntry]:
        """
        Asynchronously retrieves the DOCS-IF31-MIB system configuration state and populates the `DocsIf31CmSystemCfgState` object.

        This method will fetch the necessary MIB data, populate the attributes of the
        `DocsIf31CmSystemCfgState` object, and return the object.

        Returns:
            DocsIf31CmSystemCfgState: An instance of the `DocsIf31CmSystemCfgState` class with populated data.
        """
        
        ofdm_profile_entry: List[DocsIf31CmDsOfdmProfileStatsEntry] = []

        try:
            indices = await self.getDocsIf31CmDsOfdmChannelIdIndex()

            if not indices:
                self.logger.warning("No DocsIf31CmDsOfdmChanChannelIdIndex indices found.")
                return ofdm_profile_entry

            for idx in indices:
                entry = DocsIf31CmDsOfdmProfileStatsEntry(index=idx, snmp=self._snmp)
                await entry.start()
                ofdm_profile_entry.append(entry)

        except Exception as e:
            self.logger.exception("Failed to retrieve DocsIf31CmDsOfdmProfileStatsEntry entries")        
                
        return ofdm_profile_entry

    async def getPnmMeasurementStatus(self, test_type: DocsPnmCmCtlTest, ofdm_ifindex: int = 0) -> MeasStatusType:
        """
        Retrieve the measurement status for a given PNM test type.

        Depending on the test type, the appropriate SNMP OID is selected,
        and the required interface index is either used directly or derived
        based on DOCSIS interface type conventions.

        Args:
            test_type (DocsPnmCmCtlTest): Enum specifying the PNM test type.
            ofdm_ifindex (int): Interface index for OFDM-based tests. This may be
                                ignored or overridden for specific test types.

        Returns:
            MeasStatusType: Parsed status value from SNMP response.

        Notes:
            - `DS_SPECTRUM_ANALYZER` uses a fixed ifIndex of 0.
            - `LATENCY_REPORT` dynamically resolves the ifIndex of the DOCSIS MAC layer.
            - If the test type is unsupported or SNMP fails, `MeasStatusType.OTHER | ERROR` is returned.
        """

        oid_key_map = {
            DocsPnmCmCtlTest.SPECTRUM_ANALYZER: "docsIf3CmSpectrumAnalysisCtrlCmdMeasStatus",
            DocsPnmCmCtlTest.DS_OFDM_SYMBOL_CAPTURE: "docsPnmCmDsOfdmSymMeasStatus",
            DocsPnmCmCtlTest.DS_OFDM_CHAN_EST_COEF: "docsPnmCmOfdmChEstCoefMeasStatus",
            DocsPnmCmCtlTest.DS_CONSTELLATION_DISP: "docsPnmCmDsConstDispMeasStatus",
            DocsPnmCmCtlTest.DS_OFDM_RXMER_PER_SUBCAR: "docsPnmCmDsOfdmRxMerMeasStatus",
            DocsPnmCmCtlTest.DS_OFDM_CODEWORD_ERROR_RATE: "docsPnmCmDsOfdmFecMeasStatus",
            DocsPnmCmCtlTest.DS_HISTOGRAM: "docsPnmCmDsHistMeasStatus",
            DocsPnmCmCtlTest.US_PRE_EQUALIZER_COEF: "docsPnmCmUsPreEqMeasStatus",
            DocsPnmCmCtlTest.DS_OFDM_MODULATION_PROFILE: "docsPnmCmDsOfdmModProfMeasStatus",
            DocsPnmCmCtlTest.LATENCY_REPORT: "docsCmLatencyRptCfgMeasStatus",
        }

        if test_type == DocsPnmCmCtlTest.SPECTRUM_ANALYZER:
            ofdm_ifindex = 0
        elif test_type == DocsPnmCmCtlTest.LATENCY_REPORT:
            ofdm_ifindex = await self.getIfTypeIndex(DocsisIfType.docsCableMaclayer)[0]

        oid = oid_key_map.get(test_type)
        if not oid:
            logging.warning(f"Unsupported test type provided: {test_type}")
            return MeasStatusType.OTHER

        oid = f"{COMPILED_OIDS[oid]}.{ofdm_ifindex}"

        try:
            result = await self._snmp.get(oid)
            status_value = int(Snmp_v2c.snmp_get_result_value(result)[0])
            return MeasStatusType(status_value)

        except Exception as e:
            logging.error(f"[{test_type.name}] SNMP fetch failed on OID {oid}: {e}")
            logging.error(f'[{test_type.name}] {result}')
            return MeasStatusType.ERROR

    async def getDocsIf31DsOfdmChannelIdIndex(self) -> List[Tuple[int, int]]:
        """
        Retrieve a list of tuples representing OFDM channel index and their associated channel IDs
        for DOCSIS 3.1 downstream OFDM channels.

        Returns:
            List[Tuple[int, int]]: Each tuple contains (index, channelId). Returns an empty list if no data is found.
        """
        result = await self._snmp.walk(f'{COMPILED_OIDS["docsIf31CmDsOfdmChanChannelId"]}')
        
        if not result:
            return []

        idx_channelId = Snmp_v2c.snmp_get_result_last_idx_value(result)

        return idx_channelId or []
        
    async def getDocsIf31CmUsOfdmaChannelIdIndex(self) -> List[Tuple[int, int]]:
        """
        Retrieve a list of tuples representing OFDMA channel index and their associated channel IDs
        for DOCSIS 3.1 upstream OFDMA channels.

        Returns:
            List[Tuple[int, int]]: Each tuple contains (index, channelId). Returns an empty list if no data is found.
        """
        result = await self._snmp.walk(f'{COMPILED_OIDS["docsIf31CmUsOfdmaChanChannelId"]}')
        
        if not result:
            return []

        idx_channelId = Snmp_v2c.snmp_get_result_last_idx_value(result)

        return idx_channelId or []        

    async def getSysUpTime(self) -> Optional[str]:
        """
        Retrieves the system uptime of the SNMP target device.

        This method performs an SNMP GET operation on the `sysUpTime` OID (1.3.6.1.2.1.1.3.0),
        which returns the time (in hundredths of a second) since the network management portion
        of the system was last re-initialized.

        Returns:
            Optional[int]: The system uptime in hundredths of a second if successful, 
            otherwise `None` if the SNMP request fails or the result cannot be parsed.

        Logs:
            - A warning if the SNMP GET fails or returns no result.
            - An error if the value cannot be converted to an integer.
        """
        result = await self._snmp.get(f'{COMPILED_OIDS["sysUpTime"]}.0')

        if not result:
            self.logger.warning("SNMP get failed or returned empty for sysUpTime.")
            return None

        try:
            value = Snmp_v2c.get_result_value(result)
            return Snmp_v2c.ticks_to_duration(int(value))
        
        except (ValueError, TypeError) as e:
            self.logger.error(f"Failed to parse sysUpTime value: {value} - {e}")
            return None

    async def isAmplitudeDataPresent(self) -> bool:
        """
        Check if DOCSIS spectrum amplitude data is available via SNMP.

        Returns:
            bool: True if amplitude data exists; False otherwise.
        """
        oid = COMPILED_OIDS.get("docsIf3CmSpectrumAnalysisMeasAmplitudeData")
        if not oid:
            return False

        try:
            results = await self._snmp.walk(oid)
        except Exception:
            return False

        return bool(results)

    async def getSpectrumAmplitudeData(self) -> bytes:
        """
        Retrieve and return the raw spectrum analyzer amplitude data from the cable modem via SNMP.

        This method queries the 'docsIf3CmSpectrumAnalysisMeasAmplitudeData' table, collects all
        returned byte-chunks, and concatenates them into a single byte stream. It logs a warning
        if no data is found, and logs the first 128 bytes of the raw result (in hex) for inspection.

        Returns:
            A bytes object containing the full amplitude data stream. If no data is returned, an
            empty bytes object is returned.

        Raises:
            RuntimeError: If SNMP walk returns an unexpected data type or if any underlying SNMP
                          operation fails.
        """
        # OID for the amplitude data (should be a ByteString/Textual convention)
        oid = COMPILED_OIDS.get("docsIf3CmSpectrumAnalysisMeasAmplitudeData")
        if oid is None:
            msg = "OID 'docsIf3CmSpectrumAnalysisMeasAmplitudeData' is not defined in COMPILED_OIDS."
            self.logger.error(msg)
            raise RuntimeError(msg)

        # Perform SNMP WALK asynchronously
        try:
            results = await self._snmp.walk(oid)
        except Exception as e:
            self.logger.error(f"SNMP walk for OID {oid} failed: {e}")
            raise RuntimeError(f"SNMP walk failed: {e}")

        # If the SNMP WALK returned no varbinds, warn and return empty bytes
        if not results:
            self.logger.warning(f"No results found for OID {oid}")
            return b""

        # Extract raw byte-chunks from the SNMP results
        raw_chunks = []
        for idx, chunk in enumerate(Snmp_v2c.snmp_get_result_bytes(results)):
            # Ensure we got a bytes-like object
            if not isinstance(chunk, (bytes, bytearray)):
                self.logger.error(
                    f"Unexpected data type for chunk #{idx}: {type(chunk).__name__}. "
                    "Expected bytes or bytearray."
                )
                raise RuntimeError(f"Invalid SNMP result type: {type(chunk)}")

            # Log the first 128 bytes of each chunk (hex) for debugging
            preview = chunk[:128].hex()
            self.logger.debug(f"Raw SNMP chunk #{idx} (first 128 bytes): {preview}")

            raw_chunks.append(bytes(chunk))  # ensure immutability

        # Concatenate all chunks into a single bytes object
        varbind_bytes = b"".join(raw_chunks)

        # Log total length for reference
        total_length = len(varbind_bytes)
        if total_length == 0:
            self.logger.warning(f"OID {oid} returned an empty byte stream after concatenation.")
        else:
            self.logger.info(f"Retrieved {total_length} bytes of amplitude data for OID {oid}.")

        return varbind_bytes
    
######################
# SNMP Set Operation #
######################

    async def setDocsDevResetNow(self) -> bool:
        """
        Triggers an immediate device reset using the SNMP `docsDevResetNow` object.

        Returns:
        - bool: True if the SNMP set operation is successful, False otherwise.
        """
        try:
            oid = f'{COMPILED_OIDS["docsDevResetNow"]}.0'
            self.logger.debug(f'Sending device reset via SNMP SET: {oid} = 1')

            response = await self._snmp.set(oid, Snmp_v2c.TRUE, Integer32)
            result = Snmp_v2c.snmp_set_result_value(response)
            print(result)
            self.logger.debug(f'Device reset command issued. SNMP response: {result}')
            return True

        except Exception as e:
            self.logger.exception(f'Failed to send device reset command: {e}')
            return False

    async def setDocsPnmBulk(self, tftp_server: str, tftp_path: str = "") -> bool:
        """
        Set Docs PNM Bulk SNMP parameters.

        Args:
            tftp_server (str): TFTP server IP address.
            tftp_path (str, optional): TFTP server path. Defaults to empty string.

        Returns:
            bool: True if all SNMP set operations succeed, False if any fail.
        """
        try:
            ip_type = Snmp_v2c.get_inet_address_type(tftp_server).value
            set_response = await self._snmp.set(f'{COMPILED_OIDS["docsPnmBulkDestIpAddrType"]}.0', ip_type, Integer32)
            self.logger.debug(f'docsPnmBulkDestIpAddrType set: {set_response}')

            set_response = await self._snmp.set(f'{COMPILED_OIDS["docsPnmBulkUploadControl"]}.0', 
                                          DocsPnmBulkUploadControl.AUTO_UPLOAD.value, Integer32)
            self.logger.debug(f'docsPnmBulkUploadControl set: {set_response}')

            set_response = await self._snmp.set(f'{COMPILED_OIDS["docsPnmBulkDestIpAddr"]}.0', 
                                          InetUtils.inet_to_binary(tftp_server), OctetString)
            self.logger.debug(f'docsPnmBulkDestIpAddr set: {set_response}')

            tftp_path = tftp_path or ""
            set_response = await self._snmp.set(f'{COMPILED_OIDS["docsPnmBulkDestPath"]}.0', tftp_path, OctetString)
            self.logger.debug(f'docsPnmBulkDestPath set: {set_response}')

            return True

        except Exception as e:
            self.logger.error(f"Failed to set DocsPnmBulk parameters: {e}")
            return False

    async def setDocsIf3CmSpectrumAnalysisCtrlCmd(
            self,
            spec_ana_cmd: DocsIf3CmSpectrumAnalysisCtrlCmd,
            spectrum_retrieval_type: SpectrumRetrievalType = SpectrumRetrievalType.FILE,
            set_and_go: bool = True
        ) -> bool:
        """
        Sets all DocsIf3CmSpectrumAnalysisCtrlCmd parameters via SNMP using index 0.

        Parameters:
        - spec_ana_cmd (DocsIf3CmSpectrumAnalysisCtrlCmd): The control command object to apply.
        - spectrum_retrieval_type (SpectrumRetrieval): Determines the method of spectrum retrieval.
            - SpectrumRetrieval.FILE: File-based retrieval, in which case `docsIf3CmSpectrumAnalysisCtrlCmdFileEnable` is set to ENABLE.
            - SpectrumRetrieval.SNMP: SNMP-based retrieval, in which case `docsIf3CmSpectrumAnalysisCtrlCmdEnable` is set to ENABLE.
        - set_and_go (bool): Whether to include the 'Enable' field in the set request.
            - If `data_retrival_opt = SpectrumRetrieval.FILE`, then `docsIf3CmSpectrumAnalysisCtrlCmdFileEnable` is set to ENABLE and `docsIf3CmSpectrumAnalysisCtrlCmdEnable` is skipped.
            - If `data_retrival_opt = SpectrumRetrieval.SNMP`, then `docsIf3CmSpectrumAnalysisCtrlCmdEnable` is set to ENABLE.

        Returns:
        - bool: True if all parameters were set successfully and confirmed, False otherwise.

        Raises:
        - Exception: If any error occurs during the SNMP set operations.
        """
        
        self.logger.debug(f'SpectrumAnalyzerPara: {spec_ana_cmd.to_dict()}')
        
        '''
            Custom SNMP SET for Spectrum Analyzer
        '''
        async def __snmp_set(field_name:str, obj_value, snmp_type) -> bool:
            base_oid = COMPILED_OIDS.get(field_name)
            if not base_oid:
                self.logger.warning(f'OID not found for field "{field_name}", skipping.')
                return False

            oid = f"{base_oid}.0"
            logging.debug(f'Field-OID: {field_name} -> OID: {oid} -> {obj_value} -> Type: {snmp_type}')
            
            set_response = await self._snmp.set(oid, obj_value, snmp_type)
            logging.debug(f'Set {field_name} [{oid}] = {obj_value}: {set_response}')
            
            if not set_response:
                logging.error(f'Failed to set {field_name} to ({obj_value})')
                return False
                            
            result = Snmp_v2c.snmp_set_result_value(set_response)[0]
            
            if not result:
                logging.error(f'Failed to set {field_name} to ({obj_value})')
                return False
                            
            logging.debug(f"Result({result}): {type(result)} -> Value({obj_value}): {type(obj_value)}")

            if str(result) != str(obj_value):
                logging.error(f'Failed to set {field_name}. Expected ({obj_value}), got ({result})')
                return False
            return True 
        
        # Need to get Diplex Setting to make sure that the Spec Analyzer setting are within the band
        cscs:DocsIf31CmSystemCfgDiplexState = await self.getDocsIf31CmSystemCfgDiplexState()
        diplex_dict = cscs.to_dict()[0]
        lower_edge = int(diplex_dict["docsIf31CmSystemCfgStateDiplexerCfgDsLowerBandEdge"]) * 1_000_000 
        upper_edge = diplex_dict["docsIf31CmSystemCfgStateDiplexerCfgDsUpperBandEdge"] * 1_000_000
        
        try:
            field_type_map = {
                "docsIf3CmSpectrumAnalysisCtrlCmdInactivityTimeout": Integer32,
                "docsIf3CmSpectrumAnalysisCtrlCmdFirstSegmentCenterFrequency": Gauge32,
                "docsIf3CmSpectrumAnalysisCtrlCmdLastSegmentCenterFrequency": Gauge32,
                "docsIf3CmSpectrumAnalysisCtrlCmdSegmentFrequencySpan": Gauge32,
                "docsIf3CmSpectrumAnalysisCtrlCmdNumBinsPerSegment": Gauge32,
                "docsIf3CmSpectrumAnalysisCtrlCmdEquivalentNoiseBandwidth": Gauge32,
                "docsIf3CmSpectrumAnalysisCtrlCmdWindowFunction": Integer32,
                "docsIf3CmSpectrumAnalysisCtrlCmdNumberOfAverages": Gauge32,
                "docsIf3CmSpectrumAnalysisCtrlCmdFileName": OctetString,
                "docsIf3CmSpectrumAnalysisCtrlCmdEnable": Integer32,
                "docsIf3CmSpectrumAnalysisCtrlCmdFileEnable": Integer32,
            }

            '''
                Note: MUST BE THE LAST 2 AND IN THIS ORDER:
                    docsIf3CmSpectrumAnalysisCtrlCmdEnable      <- Triggers SNMP AMPLITUDE DATA RETURN
                    docsIf3CmSpectrumAnalysisCtrlCmdFileEnable  <- Trigger PNM FILE RETURN, OVERRIDES SNMP AMPLITUDE DATA RETURN
            '''
            
            # Iterating through the fields and setting their values via SNMP
            for field_name, snmp_type in field_type_map.items():
                obj_value = getattr(spec_ana_cmd, field_name)
                
                self.logger.debug(f'FieldName: {field_name} -> SNMP-Type: {snmp_type}')

                ##############################################################
                # OVERRIDE SECTION TO MAKE SURE WE FOLLOW THE SPEC-ANA RULES #
                ##############################################################
                
                # Need to make sure that SpecAnaTuner is within the Diplex Bandwide Range
                if field_name == "docsIf3CmSpectrumAnalysisCtrlCmdFirstSegmentCenterFrequency":
                    seg_freq_span = spec_ana_cmd.__getattribute__('docsIf3CmSpectrumAnalysisCtrlCmdSegmentFrequencySpan')
                    obj_value = getattr(spec_ana_cmd, field_name)
                    spec_lower_edge = (int(obj_value) - (int(seg_freq_span)/2))
                    
                    if spec_lower_edge < lower_edge:
                        self.logger.error(f'SpecAnalyzer({obj_value})-LowerEdge ({spec_lower_edge}) is lower than Diplex Lower Edge: ({lower_edge})')
                        return False
                     
                # Need to make sure that SpecAnaTuner is within the Diplex Bandwide Range
                elif field_name == "docsIf3CmSpectrumAnalysisCtrlCmdLastSegmentCenterFrequency":
                    seg_freq_span = spec_ana_cmd.__getattribute__('docsIf3CmSpectrumAnalysisCtrlCmdSegmentFrequencySpan')
                    obj_value = getattr(spec_ana_cmd, field_name)
                    spec_upper_edge = (int(obj_value) + (int(seg_freq_span)/2))
                    
                    if spec_upper_edge > upper_edge:
                        self.logger.error(f'SpecAnalyzer({obj_value})-UpperEdge ({spec_lower_edge}) is larger than Diplex Upper Edge: ({lower_edge})')
                        return False
                                     
                #######################################################################################
                #                                                                                     # 
                #                   START SPECTRUM ANALYZER MEASURING PROCESS                         #
                #                                                                                     #
                # This OID Triggers the start of the Spectrum Analysis for SNMP-AMPLITUDE-DATA RETURN #
                #######################################################################################
                elif field_name == "docsIf3CmSpectrumAnalysisCtrlCmdEnable":
                    
                    obj_value = Snmp_v2c.TRUE
                    self.logger.debug(f'FieldName: {field_name} -> SNMP-Type: {snmp_type}')
                    
                    # Need to toggle ? -> FALSE -> TRUE
                    if not await __snmp_set(field_name, Snmp_v2c.FALSE, snmp_type):
                        self.logger.error(f'Fail to set {field_name} to {Snmp_v2c.FALSE}')
                        return False
                    
                    time.sleep(1)
                    
                    if not await __snmp_set(field_name, Snmp_v2c.TRUE, snmp_type):
                        self.logger.error(f'Fail to set {field_name} to {Snmp_v2c.TRUE}')
                        return False
                                        
                    continue

                ######################################################################################
                #
                #                   CHECK SPECTRUM ANALYZER MEASURING PROCESS
                #                           FOR PNM FILE RETRIVAL
                #                
                # This OID Triggers the start of the Spectrum Analysis for PNM-FILE RETURN
                # Override SNMP-AMPLITUDE-DATA RETURN
                ######################################################################################    
                elif field_name == "docsIf3CmSpectrumAnalysisCtrlCmdFileEnable":
                    obj_value = Snmp_v2c.TRUE if spectrum_retrieval_type == SpectrumRetrievalType.FILE else Snmp_v2c.FALSE
                    self.logger.debug(f'Setting File Retrival, Set-And-Go({set_and_go}) -> Value: {obj_value}')
                
                ###############################################
                # Set Field setting not change by above rules #
                ###############################################
                if isinstance(obj_value, Enum):
                    obj_value = str(obj_value.value)
                    self.logger.debug(f'ENUM Found: Set Value Type: {obj_value} -> {type(obj_value)}')
                else:
                    obj_value = str(obj_value)
                
                self.logger.debug(f'{field_name} -> Set Value Type: {obj_value} -> {type(obj_value)}')

                if not await __snmp_set(field_name, obj_value, snmp_type):
                    self.logger.error(f'Fail to set {field_name} to {obj_value}')
                    return False
                                                
            return True

        except Exception:
            logging.exception("Exception while setting DocsIf3CmSpectrumAnalysisCtrlCmd")
            return False

    async def setDocsPnmCmUsPreEq(self, ofdma_idx: int, filename:str, last_pre_eq_filename:str, set_and_go:bool=True) -> bool:
        """
        Set the upstream Pre-EQ file name and enable Pre-EQ capture for a specified OFDMA channel index.

        Args:
            ofdma_idx (int): Index in the DocsPnmCmUsPreEq SNMP table.
            file_name (str): Desired file name to use for Pre-EQ capture.

        Returns:
            bool: True if both SNMP set operations succeed and verify expected values; False otherwise.
        """
        try:
            oid = f'{COMPILED_OIDS["docsPnmCmUsPreEqFileName"]}.{ofdma_idx}'
            self.logger.info(f'Setting Pre-EQ filename: [{oid}] = "{filename}"')
            response = await self._snmp.set(oid, filename, OctetString)
            result = Snmp_v2c.snmp_set_result_value(response)

            if not result or str(result[0]) != filename:
                self.logger.error(f'Filename mismatch. Expected "{filename}", got "{result[0] if result else "None"}"')
                return False

            oid = f'{COMPILED_OIDS["docsPnmCmUsPreEqLastUpdateFileName"]}.{ofdma_idx}'
            self.logger.info(f'Setting Last-Pre-EQ filename: [{oid}] = "{last_pre_eq_filename}"')
            response = await self._snmp.set(oid, last_pre_eq_filename, OctetString)
            result = Snmp_v2c.snmp_set_result_value(response)

            if not result or str(result[0]) != last_pre_eq_filename:
                self.logger.error(f'Filename mismatch. Expected "{last_pre_eq_filename}", got "{result[0] if result else "None"}"')
                return False            
            
            if set_and_go:
                time.sleep(1)
                enable_oid = f'{COMPILED_OIDS["docsPnmCmUsPreEqFileEnable"]}.{ofdma_idx}'
                self.logger.info(f'Enabling Pre-EQ capture [{enable_oid}] = {Snmp_v2c.TRUE}')
                response = await self._snmp.set(enable_oid, Snmp_v2c.TRUE, Integer32)
                result = Snmp_v2c.snmp_set_result_value(response)

                if not result or int(result[0]) != Snmp_v2c.TRUE:
                    self.logger.error(f'Failed to enable Pre-EQ capture. Expected 1, got "{result[0] if result else "None"}"')
                    return False

            return True

        except Exception as e:
            self.logger.exception(f'Exception during setDocsPnmCmUsPreEq for index {ofdma_idx}: {e}')
            return False

    async def setDocsPnmCmDsOfdmModProf(self, ofdm_idx: int, mod_prof_file_name: str, set_and_go:bool=True) -> bool:
        """
        Set the DocsPnmCmDsOfdmModProf parameters for a given OFDM index.

        Parameters:
        - ofdm_idx (int): The index of the OFDM channel.
        - mod_prof_file_name (str): The filename to set for the modulation profile.

        Returns:
        - bool: True if both SNMP sets were successful, False otherwise.
        """
        try:
            file_oid = f'{COMPILED_OIDS["docsPnmCmDsOfdmModProfFileName"]}.{ofdm_idx}'
            enable_oid = f'{COMPILED_OIDS["docsPnmCmDsOfdmModProfFileEnable"]}.{ofdm_idx}'

            file_response = await self._snmp.set(file_oid, mod_prof_file_name, OctetString)
            self.logger.debug(f'Set {file_oid} to {mod_prof_file_name}: {file_response}')

            if set_and_go:
                enable_response = await self._snmp.set(enable_oid, Snmp_v2c.TRUE, Integer32)
                self.logger.debug(f'Set {enable_oid} to 1 (enable): {enable_response}')

            return True
        
        except Exception as e:
            self.logger.error(f"Failed to set DocsPnmCmDsOfdmModProf for index {ofdm_idx}: {e}")
            return False

    async def setDocsPnmCmDsOfdmRxMer(self, ofdm_idx: int, rxmer_file_name: str, set_and_go:bool=True) -> bool:
        """
        Sets the RxMER file name and enables file capture for a specified OFDM channel index.

        Parameters:
        - ofdm_idx (str): The index in the DocsPnmCmDsOfdmRxMer SNMP table.
        - rxmer_file_name (str): Desired file name to assign for RxMER capture.

        Returns:
        - bool: True if both SNMP set operations succeed and return expected values, False otherwise.
        """
        try:
            oid_file_name = f'{COMPILED_OIDS["docsPnmCmDsOfdmRxMerFileName"]}.{ofdm_idx}'
            set_response = await self._snmp.set(oid_file_name, rxmer_file_name, OctetString)
            self.logger.debug(f'Setting RxMER file name [{oid_file_name}] = "{rxmer_file_name}"')

            result = Snmp_v2c.snmp_set_result_value(set_response)
            if not result or str(result[0]) != rxmer_file_name:
                self.logger.error(f'File name mismatch. Expected "{rxmer_file_name}", got "{result[0] if result else "None"}"')
                return False

            if set_and_go:
                oid_file_enable = f'{COMPILED_OIDS["docsPnmCmDsOfdmRxMerFileEnable"]}.{ofdm_idx}'
                set_response = await self._snmp.set(oid_file_enable, 1, Integer32)
                self.logger.debug(f'Enabling RxMER capture [{oid_file_enable}] = 1')

                result = Snmp_v2c.snmp_set_result_value(set_response)
                if not result or int(result[0]) != 1:
                    self.logger.error(f'Failed to enable RxMER capture. Expected 1, got "{result[0] if result else "None"}"')
                    return False

            return True

        except Exception as e:
            self.logger.exception(f'Exception during setDocsPnmCmDsOfdmRxMer for index {ofdm_idx}: {e}')
            return False

    async def setDocsPnmCmDsOfdmFecSum(self, ofdm_idx: int, 
                                       fec_sum_file_name: str, 
                                       fec_sum_type: FecSummaryType = FecSummaryType.TEN_MIN, 
                                       set_and_go:bool=True) -> bool:
        """
        Sets SNMP parameters for FEC summary of an OFDM channel.

        Parameters:
        - ofdm_idx (str): The OFDM index.
        - fec_sum_file_name (str): The file name associated with FEC sum.
        - fec_sum_type (FecSummaryType): The type of FEC summary (default is 10 minutes).

        Returns:
        - bool: True if successful, False if any error occurs during SNMP operations.
        """
        try:
            oid_file_name = f'{COMPILED_OIDS["docsPnmCmDsOfdmFecFileName"]}.{ofdm_idx}'
            self.logger.debug(f'Setting FEC file name [{oid_file_name}] = "{fec_sum_file_name}"')
            set_response = await self._snmp.set(oid_file_name, fec_sum_file_name, OctetString)
            result = Snmp_v2c.snmp_set_result_value(set_response)
            if not result or str(result[0]) != fec_sum_file_name:
                self.logger.error(f'File name mismatch. Expected "{fec_sum_file_name}", got "{result[0] if result else "None"}"')
                return False

            oid_sum_type = f'{COMPILED_OIDS["docsPnmCmDsOfdmFecSumType"]}.{ofdm_idx}'
            self.logger.debug(f'Setting FEC sum type [{oid_sum_type}] = {fec_sum_type.name} -> {type(fec_sum_type.value)}')
            set_response = await self._snmp.set(oid_sum_type, fec_sum_type.value, Integer32)
            result = Snmp_v2c.snmp_set_result_value(set_response)
            if not result or int(result[0]) != fec_sum_type.value:
                self.logger.error(f'FEC sum type mismatch. Expected {fec_sum_type.value}, got "{result[0] if result else "None"}"')
                return False

            if set_and_go:
                oid_file_enable = f'{COMPILED_OIDS["docsPnmCmDsOfdmFecFileEnable"]}.{ofdm_idx}'
                self.logger.debug(f'Enabling FEC file capture [{oid_file_enable}] = 1')
                set_response = await self._snmp.set(oid_file_enable, 1, Integer32)
                result = Snmp_v2c.snmp_set_result_value(set_response)
                if not result or int(result[0]) != 1:
                    self.logger.error(f'Failed to enable FEC capture. Expected 1, got "{result[0] if result else "None"}"')
                    return False

            self.logger.debug(f'Successfully configured FEC summary capture for OFDM index {ofdm_idx}')
            return True

        except Exception as e:
            self.logger.exception(f'Exception during setDocsPnmCmDsOfdmFecSum for index {ofdm_idx}: {e}')
            return False

    async def setDocsPnmCmOfdmChEstCoef(self, ofdm_idx: int, chan_est_file_name: str, set_and_go:bool=True) -> bool:
        """
        Sets SNMP parameters for OFDM channel estimation coefficients.

        Parameters:
        - ofdm_idx (str): The OFDM index.
        - chan_est_file_name (str): The file name associated with the OFDM Channel Estimation.

        Returns:
        - bool: True if the SNMP set operations were successful, False otherwise.
        """
        try:
            oid_file_name = f'{COMPILED_OIDS["docsPnmCmOfdmChEstCoefFileName"]}.{ofdm_idx}'
            self.logger.debug(f'Setting OFDM Channel Estimation File Name [{oid_file_name}] = "{chan_est_file_name}"')
            set_response = await self._snmp.set(oid_file_name, chan_est_file_name, OctetString)

            result = Snmp_v2c.snmp_set_result_value(set_response)
            if not result or str(result[0]) != chan_est_file_name:
                self.logger.error(f'Failed to set channel estimation file name. Expected "{chan_est_file_name}", got "{result[0] if result else "None"}"')
                return False

            if set_and_go:
                oid_trigger_enable = f'{COMPILED_OIDS["docsPnmCmOfdmChEstCoefTrigEnable"]}.{ofdm_idx}'
                self.logger.debug(f'Setting Channel Estimation Trigger Enable [{oid_trigger_enable}] = 1')
                set_response = await self._snmp.set(oid_trigger_enable, Snmp_v2c.TRUE, Integer32)

                result = Snmp_v2c.snmp_set_result_value(set_response)
                if not result or int(result[0]) != 1:
                    self.logger.error(f'Failed to enable channel estimation trigger. Expected 1, got "{result[0] if result else "None"}"')
                    return False

            self.logger.debug(f'Successfully configured OFDM channel estimation for index {ofdm_idx} with file name "{chan_est_file_name}"')
            
        except Exception as e:
            self.logger.exception(f'Exception occurred while setting OFDM Channel Estimation coefficients for index {ofdm_idx}: {e}')
            return False

        return True

    async def setDocsPnmCmDsConstDisp(
        self,
        ofdm_idx: int,
        const_disp_name: str,
        modulation_order_offset: int = CmDsConstellationDisplayConst.MODULATION_OFFSET.value,
        number_sample_symbol: int = CmDsConstellationDisplayConst.NUM_SAMPLE_SYMBOL.value,
        set_and_go: bool = True
    ) -> bool:
        """
        Configures SNMP parameters for the OFDM Downstream Constellation Display.

        Args:
            ofdm_idx (int): Index of the downstream OFDM channel.
            const_disp_name (str): Desired filename to store the constellation display data.
            modulation_offset (int, optional): Modulation order offset. Defaults to standard constant value.
            num_sample_symb (int, optional): Number of sample symbols. Defaults to standard constant value.
            set_and_go (bool, optional): If True, triggers immediate measurement start. Defaults to True.

        Returns:
            bool: True if all SNMP SET operations succeed; False otherwise.
        """
        try:
            # Set file name
            oid = f'{COMPILED_OIDS["docsPnmCmDsConstDispFileName"]}.{ofdm_idx}'
            self.logger.debug(f'Setting FileName [{oid}] = "{const_disp_name}"')
            set_response = await self._snmp.set(oid, const_disp_name, OctetString)
            result = Snmp_v2c.snmp_set_result_value(set_response)
            if not result or str(result[0]) != const_disp_name:
                self.logger.error(f'Failed to set FileName. Expected "{const_disp_name}", got "{result[0] if result else "None"}"')
                return False

            # Set modulation order offset
            oid = f'{COMPILED_OIDS["docsPnmCmDsConstDispModOrderOffset"]}.{ofdm_idx}'
            self.logger.debug(f'Setting ModOrderOffset [{oid}] = {modulation_order_offset}')
            set_response = await self._snmp.set(oid, modulation_order_offset, Gauge32)
            result = Snmp_v2c.snmp_set_result_value(set_response)
            if not result or int(result[0]) != modulation_order_offset:
                self.logger.error(f'Failed to set ModOrderOffset. Expected {modulation_order_offset}, got "{result[0] if result else "None"}"')
                return False

            # Set number of sample symbols
            oid = f'{COMPILED_OIDS["docsPnmCmDsConstDispNumSampleSymb"]}.{ofdm_idx}'
            self.logger.debug(f'Setting NumSampleSymb [{oid}] = {number_sample_symbol}')
            set_response = await self._snmp.set(oid, number_sample_symbol, Gauge32)
            result = Snmp_v2c.snmp_set_result_value(set_response)
            if not result or int(result[0]) != number_sample_symbol:
                self.logger.error(f'Failed to set NumSampleSymb. Expected {number_sample_symbol}, got "{result[0] if result else "None"}"')
                return False

            if set_and_go:
                # Trigger measurement
                oid = f'{COMPILED_OIDS["docsPnmCmDsConstDispTrigEnable"]}.{ofdm_idx}'
                self.logger.debug(f'Setting TrigEnable [{oid}] = 1')
                set_response = await self._snmp.set(oid, Snmp_v2c.TRUE, Integer32)
                result = Snmp_v2c.snmp_set_result_value(set_response)
                if not result or int(result[0]) != 1:
                    self.logger.error(f'Failed to trigger measurement. Expected 1, got "{result[0] if result else "None"}"')
                    return False

            self.logger.debug(
                f'Successfully configured Constellation Display for OFDM index {ofdm_idx} with file name "{const_disp_name}"'
            )
            return True

        except Exception as e:
            self.logger.exception(
                f'Exception occurred while setting Constellation Display for OFDM index {ofdm_idx}: {e}'
            )
            return False

    async def setDocsCmLatencyRptCfg(self, latency_rpt_file_name: str, num_of_reports: int = 1, set_and_go:bool=True) -> bool:
        """
        Configures the CM upstream latency reporting feature. This enables 
        the creation of latency report files containing per-Service Flow 
        latency measurements over a defined period of time.

        Parameters:
        - latency_rpt_file_name (str): The filename to store the latency report.
        - num_of_reports (int): Number of report files to generate.

        Returns:
        - bool: True if configuration is successful, False otherwise.
        """
        
        mac_idx = self.getIfTypeIndex(DocsisIfType.docsCableMaclayer)[0]
        
        try:
            oid_file_name = f'{COMPILED_OIDS["docsCmLatencyRptCfgFileName"]}.{mac_idx}'
            self.logger.debug(f'Setting US Latency Report file name [{oid_file_name}] = "{latency_rpt_file_name}"')
            set_response = await self._snmp.set(oid_file_name, latency_rpt_file_name, OctetString)
            result = Snmp_v2c.snmp_set_result_value(set_response)

            if not result or str(result[0]) != latency_rpt_file_name:
                self.logger.error(f'File name mismatch. Expected "{latency_rpt_file_name}", got "{result[0] if result else "None"}"')
                return False

            if set_and_go:
                oid_num_reports = f'{COMPILED_OIDS["docsCmLatencyRptCfgNumFiles"]}.{mac_idx}'
                self.logger.debug(f'Setting number of latency reports [{oid_num_reports}] = {num_of_reports}')
                set_response = await self._snmp.set(oid_num_reports, num_of_reports, Gauge32)
                result = Snmp_v2c.snmp_set_result_value(set_response)

                if not result or int(result[0]) != num_of_reports:
                    self.logger.error(f'Failed to enable latency report capture. Expected {num_of_reports}, got "{result[0] if result else "None"}"')
                    return False

            return True

        except Exception as e:
            self.logger.exception(f'Exception during setDocsCmLatencyRptCfg: {e}')
            return False

    async def setDocsPnmCmDsHist(self, ds_histogram_file_name: str, set_and_go:bool=True, timeout:int=10) -> bool:
        """
        Configure and enable downstream histogram capture for the CM MAC layer interface.

        This method performs the following steps:
        1. Retrieves the index for the `docsCableMaclayer` interface.
        2. Sets the histogram file name via Snmp_v2c.
        3. Enables histogram data capture via Snmp_v2c.

        Args:
            ds_histogram_file_name (str): The name of the file where the downstream histogram will be saved.

        Returns:
            bool: True if the file name was set and capture was successfully enabled, False otherwise.

        Logs:
            - debug: Index being used.
            - Debug: SNMP set operations for file name and capture enable.
            - Error: Mismatched response or SNMP failure.
            - Exception: Any exception that occurs during the SNMP operations.
        """
        idx_list = await self.getIfTypeIndex(DocsisIfType.docsCableMaclayer)

        if not idx_list:
            self.logger.error("No index found for docsCableMaclayer interface type.")
            return False

        if len(idx_list) > 1:
            self.logger.error(f"Expected a single index for docsCableMaclayer, but found multiple: {idx_list}")
            return False

        idx = idx_list[0]

        self.logger.debug(f'setDocsPnmCmDsHist -> idx: {idx}')

        try:
            # TODO: Need to make this dynamic
            set_response = await self._snmp.set(f'{COMPILED_OIDS["docsPnmCmDsHistTimeOut"]}.{idx}', timeout, Gauge32)
            self.logger.debug(f'Setting Histogram Timeout: {timeout}')

            oid_file_name = f'{COMPILED_OIDS["docsPnmCmDsHistFileName"]}.{idx}'
            set_response = await self._snmp.set( oid_file_name, ds_histogram_file_name, OctetString)
            self.logger.debug(f'Setting Histogram file name [{oid_file_name}] = "{ds_histogram_file_name}"')

            result = Snmp_v2c.snmp_set_result_value(set_response)
            if not result or str(result[0]) != ds_histogram_file_name:
                self.logger.error(f'File name mismatch. Expected "{ds_histogram_file_name}", got "{result[0] if result else "None"}"')
                return False

            if set_and_go:
                oid_file_enable = f'{COMPILED_OIDS["docsPnmCmDsHistEnable"]}.{idx}'
                set_response = await self._snmp.set(oid_file_enable, Snmp_v2c.TRUE, Integer32)
                self.logger.debug(f'Enabling Histogram capture [{oid_file_enable}] = 1')

                result = Snmp_v2c.snmp_set_result_value(set_response)
                if not result or int(result[0]) != 1:
                    self.logger.error(f'Failed to enable Histogram capture. Expected 1, got "{result[0] if result else "None"}"')
                    return False

        except Exception as e:
            self.logger.exception(f'Exception during setDocsPnmCmDsHist for index {idx}: {e}')
            return False

        return True

    async def setDocsPnmCmDsOfdmSymTrig(self, ofdm_idx: int, symbol_trig_file_name: str) -> bool:
        """
        Sets SNMP parameters for OFDM Downstream Symbol Capture.

        Parameters:
        - ofdm_idx (str): The OFDM index.
        - symbol_trig_file_name (str): The file name associated with the OFDM Downstream Symbol Capture

        Returns:
        - bool: True if the SNMP set operations were successful, False otherwise.
        TODO: NOT ABLE TO TEST DUE TO CMTS DOES NOT SUPPORT
        """
        try:
            oid_file_name = f'{COMPILED_OIDS["docsPnmCmDsOfdmSymCaptFileName"]}.{ofdm_idx}'
            self.logger.debug(f'Setting OFDM Downstream Symbol Capture File Name [{oid_file_name}] = "{symbol_trig_file_name}"')
            set_response = await self._snmp.set(oid_file_name, symbol_trig_file_name, OctetString)

            result = Snmp_v2c.snmp_set_result_value(set_response)
            if not result or str(result[0]) != symbol_trig_file_name:
                self.logger.error(f'Failed to set Downstream Symbol Capture file name. Expected "{symbol_trig_file_name}", got "{result[0] if result else "None"}"')
                return False

            oid_trigger_enable = f'{COMPILED_OIDS["docsPnmCmDsConstDispTrigEnable"]}.{ofdm_idx}'
            self.logger.debug(f'Setting OFDM Downstream Symbol Capture Trigger Enable [{oid_trigger_enable}] = 1')
            set_response = await self._snmp.set(oid_trigger_enable, 1, Integer32)

            result = Snmp_v2c.snmp_set_result_value(set_response)
            if not result or int(result[0]) != 1:
                self.logger.error(f'Failed to enable OFDM Downstream Symbol Capture trigger. Expected 1, got "{result[0] if result else "None"}"')
                return False

            self.logger.debug(f'Successfully configured OFDM Downstream Symbol Capturey for index {ofdm_idx} with file name "{symbol_trig_file_name}"')
            return True

        except Exception as e:
            self.logger.exception(f'Exception occurred while setting OFDM Downstream Symbol Capture for index {ofdm_idx}: {e}')
            return False

    async def getDocsIf3CmStatusUsEqData(self) -> DocsEqualizerData:
        """
        Retrieve and parse DOCSIS 3.0/3.1 upstream equalizer data via Snmp_v2c.

        This method performs an SNMP walk on the OID corresponding to 
        `docsIf3CmStatusUsEqData`, which contains the pre-equalization 
        coefficient data for upstream channels.

        It parses the SNMP response into a structured `DocsEqualizerData` object.

        Returns:
            DocsEqualizerData: Parsed equalizer data including real/imaginary tap coefficients
            for each upstream channel index.
            Returns None if SNMP walk fails, no data is returned, or parsing fails.
        """
        oid = "docsIf3CmStatusUsEqData"
        oid_path = COMPILED_OIDS.get(oid)

        if not oid_path:
            self.logger.error(f"OID path not found for {oid}. Check DOCS_OIDS configuration.")
            return DocsEqualizerData()

        try:
            result = await self._snmp.walk(oid_path)
            
        except Exception as e:
            self.logger.error(f"SNMP walk failed for {oid}: {e}")
            return DocsEqualizerData()

        if not result:
            self.logger.warning(f"No data returned from SNMP walk for {oid}.")
            return DocsEqualizerData()

        ded = DocsEqualizerData()

        try:
            for varbind in result:
                us_idx = Snmp_v2c.extract_last_oid_index([varbind])[0]
                eq_data = Snmp_v2c.snmp_get_result_value([varbind])[0]
                eq_data = Format.non_ascii_to_hex(eq_data)              
                self.logger.debug(f'idx: {us_idx} -> eq-data: ({eq_data})')
                ded.add(us_idx, eq_data)

        except ValueError as e:
            self.logger.error(f"Failed to parse equalizer data. Error: {e}")
            return None

        if not ded.coefficients_found():
            self.logger.warning(
                "No upstream pre-equalization coefficients found. "
                "Ensure Pre-Equalization is enabled on the upstream interface(s)."
            )

        return ded

             