# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia

import logging
from typing import List, Optional, Tuple, Type, Union
from datetime import datetime, timedelta, timezone

from pysnmp.hlapi.v3arch.asyncio import (
    SnmpEngine, CommunityData, UdpTransportTarget,ContextData,
    ObjectType,ObjectIdentity, get_cmd,set_cmd, walk_cmd)

from pysnmp.proto.rfc1902 import (OctetString)
from pypnm.lib.inet import Inet
from pypnm.lib.inet_utils import InetUtils
from pypnm.snmp.modules import InetAddressType



class Snmp_v2c:
    """
    SNMPv2c Client for asynchronous GET, SET, and WALK operations.

    Attributes:
        host (str): Hostname or IP address of the SNMP agent.
        port (int): Port number used for SNMP (default is 161).
        community (str): Community string for SNMP authentication (default 'private').
        _snmp_engine (SnmpEngine): Instance of pysnmp SnmpEngine.
    
    Class Attributes:
        COMPILE_MIBS (bool): Whether to compile MIBs for OID resolution.
        SNMP_PORT (int): Default SNMP port.

    Example:
        >>> snmp = Snmp_v2c(Inet('192.168.1.1'), community='public')
        >>> await snmp.get('1.3.6.1.2.1.1.1.0')
        >>> await snmp.walk('1.3.6.1.2.1.2')
        >>> await snmp.set('1.3.6.1.2.1.1.5.0', 'NewHostName')
        >>> snmp.close()
    """

    DISABLE = 1
    ENABLE = 2
    
    TRUE = 1
    FALSE = 2

    SNMP_PORT = 161

    def __init__(self, host: Inet, community: str = "private", port: int = SNMP_PORT):
        """
        Initializes the SNMPv2c client.

        Args:
            host (Inet): Host address of the SNMP device.
            community (str): Community string for SNMP access.
            port (int): SNMP port (default 161).
        """
        self.logger = logging.getLogger(self.__class__.__name__)
        self._host = host.inet
        self._port = port
        self._community = community
        self._snmp_engine = SnmpEngine()

    async def get(self, oid: Union[str, Tuple[str, str, int]]):
        """
        Perform an SNMP GET operation.

        Args:
            oid (Union[str, Tuple[str, str, int]]): OID to fetch, either as string or tuple.

        Returns:
            List[ObjectType]: List of SNMP variable bindings.

        Raises:
            RuntimeError: On SNMP errors.
        """
        self.logger.debug(f'Input OID: {oid}')
        identity = self._resolve_oid(oid)

        obj = ObjectType(identity)

        errorIndication, errorStatus, errorIndex, varBinds = await get_cmd(
            self._snmp_engine,
            CommunityData(self._community),
            await UdpTransportTarget.create((self._host, self._port)),
            ContextData(),
            obj,
        )
        try:
            self._check_for_errors(errorIndication, errorStatus, errorIndex)
        except Exception as e:
            self.logger.error(f"Failed get : {e}")
  
        return varBinds

    async def walk(self, oid: Union[str, Tuple[str, str, int]]) -> Optional[List[ObjectType]]:
        """
        Perform an SNMP WALK operation.

        Args:
            oid (str | Tuple[str, str, int]): The starting OID for the walk.

        Returns:
            Optional[List[ObjectType]]: List of walked SNMP ObjectTypes, or None if no results.
        """
        self.logger.debug(f"Starting SNMP WALK with OID: {oid}")

        identity = self._resolve_oid(oid)
        obj = ObjectType(identity)
        results: List[ObjectType] = []

        transport = await UdpTransportTarget.create((self._host, self._port))

        objects = walk_cmd(
            self._snmp_engine,
            CommunityData(self._community, mpModel=1),
            transport,
            ContextData(),
            obj
        )

        async for item in objects:
            
            errorIndication, errorStatus, errorIndex, varBinds = item

            try:
                self._check_for_errors(errorIndication, errorStatus, errorIndex)
                
            except Exception as e:
                self.logger.error(f"Failed walk : {e}")
                continue    
            
            if not varBinds:
                continue

            for varBind in varBinds:
                oid_str = str(varBind[0])

                if not self._is_subtree_match(oid_str, str(identity)):
                    self.logger.debug(f"End of OID subtree reached at {oid_str} -> {varBind} - List size {len(results)}")
                    return results if results else None

                results.append(varBind)
                
        self.logger.debug(f'List size {len(results)}')
        
        return results if results else None

    async def set(self, oid: str, value: Union[str, int], value_type: Type)-> Optional[List[ObjectType]]:
        """
        Perform an SNMP SET operation with explicit value type.

        Args:
            oid (str): The OID to set.
            value (Union[str, int]): The value to set.
            value_type (Type): pysnmp value type class (no default).

                Examples:
                    OctetString, Integer, Integer32, Counter32, Counter64, Gauge32, IpAddress.

        Returns:
            Dict[str, str]: Mapping of OID to the set value.

        Raises:
            ValueError: If value type instantiation fails.
            RuntimeError: On SNMP errors.
        """
        if value_type is None:
            raise ValueError("value_type must be explicitly specified")

        self.logger.debug(f'SNMP-SET-OID: {oid} -> {value_type} -> {value}')

        transport = await UdpTransportTarget.create((self._host, self._port))

        try:
            snmp_value = value_type(value)
        except Exception as e:
            raise ValueError(f"Failed to create SNMP value of type {value_type}: {e}")

        errorIndication, errorStatus, errorIndex, varBinds = await set_cmd(
            self._snmp_engine,
            CommunityData(self._community, mpModel=1),
            transport,
            ContextData(),
            ObjectType(ObjectIdentity(oid), snmp_value),
        )
        try:
            self._check_for_errors(errorIndication, errorStatus, errorIndex)

        except Exception as e:
            self.logger.error(f"Error extracting SNMP value: {e}")
            return None
        
        return varBinds # type: ignore

    def close(self) -> None:
        """
        Close the SNMP engine dispatcher and release resources.
        """
        self._snmp_engine.close_dispatcher()

    @staticmethod
    def get_result_value(pysnmp_get_result) -> Optional[str]:
        """
        Extract the value from a pysnmp GET result.

        Args:
            pysnmp_get_result: SNMP response from get().

        Returns:
            Optional[str]: The extracted value as string, or None if not found.
        """
        try:
            if isinstance(pysnmp_get_result, tuple):
                pysnmp_get_result = pysnmp_get_result[0]

            if isinstance(pysnmp_get_result, ObjectType):
                value = pysnmp_get_result[1]
                if isinstance(value, OctetString):
                    return value.prettyPrint()
                return str(value)
            
            return None

        except Exception as e:
            logging.debug(f"Error extracting SNMP value: {e}")
            return None

    @staticmethod
    def extract_last_oid_index(snmp_responses: List[ObjectType]) -> List[int]:
        """
        Extract the last index from a list of SNMP responses.

        Parameters:
        - snmp_responses: List of SNMP responses.

        Returns:
        - List of extracted indices.
        """
        last_oid_indexes = []
        for response in snmp_responses:
            oid = response[0]
            index = Snmp_v2c.get_oid_index(oid)
            logging.debug(f'extract_last_oid_index-IN-LOOP -> {response} -> {oid} -> {index}')
            last_oid_indexes.append(index)
        return last_oid_indexes

    @staticmethod
    def extract_oid_indices(snmp_responses: List[ObjectType],num_indices: int = 1) -> List[List[int]]:
        """
        Extract the last `num_indices` components from the OID index of each SNMP response.

        Parameters:
        - snmp_responses: List of SNMP responses.
        - num_indices: Number of trailing OID index components to extract.

        Returns:
        - List of lists, each containing the extracted index components.
        """
        extracted_indices = []

        for response in snmp_responses:
            oid = response[0]
            full_index = Snmp_v2c.get_oid_index(oid)

            if isinstance(full_index, int):
                indices = [full_index]
            elif isinstance(full_index, (list, tuple)):
                indices = list(full_index)
            else:
                logging.warning(f"Unexpected OID index format: {full_index}")
                continue

            selected = indices[-num_indices:] if len(indices) >= num_indices else indices
            logging.debug(f"extract_oid_indices -> {response} -> {oid} -> {selected}")
            extracted_indices.append(selected)

        return extracted_indices

    @staticmethod
    def snmp_get_result_value(snmp_responses: List[ObjectType]) -> List[str]:
        """
        Extract the result value from a list of SNMP responses.

        Args:
            snmp_responses (List[ObjectType]): List of SNMP ObjectType responses.

        Returns:
            List[str]: List of extracted result values as strings.
        """
        return [str(value[1]) for value in snmp_responses]

    @staticmethod
    def snmp_get_result_bytes(snmp_responses: List[ObjectType]) -> List[bytes]:
        """
        Extract raw byte values from a list of SNMP ObjectType responses.

        Args:
            snmp_responses (List[ObjectType]): List of SNMP ObjectType responses.

        Returns:
            List[bytes]: List of extracted result values as bytes.
        """
        result = []
        for varbind in snmp_responses:
            value = varbind[1]
            # Attempt to get raw bytes directly if available
            if hasattr(value, 'asOctets'):
                result.append(value.asOctets())
            elif isinstance(value, bytes):
                result.append(value)
            else:
                # Fallback: try encoding string representation
                result.append(str(value).encode())
        return result

    @staticmethod
    def snmp_get_result_last_idx_value(snmp_responses: List[ObjectType]) -> List[Tuple[int, str]]:
        """
        Extract the last index and value from each SNMP response.

        Args:
            snmp_responses (List[ObjectType]): List of SNMP ObjectType responses.

        Returns:
            List[Tuple[int, str]]: List of (last index, value) pairs.
        """
        result = []
        for obj in snmp_responses:
            oid = obj[0]
            last_idx = int(str(oid).split('.')[-1])
            value = str(obj[1])
            result.append((last_idx, value))
        return result

    @staticmethod
    def snmp_set_result_value(snmp_set_response: str) -> List[str]:
        """
        Extracts value(s) from an SNMP SET response string.

        This method parses the raw SNMP SET response string and extracts the 
        returned value(s), if any, from the output. Useful for validating
        SNMP set operations.

        Parameters:
        - snmp_set_response (str): The raw SNMP SET response string, typically
        returned by an SNMP set operation.

        Returns:
        - List[str]: A list containing the parsed value(s) from the response.
                    If no value is found, returns an empty list.
        """
        if not snmp_set_response:
            return []
        
        logging.debug(f'snmp_set_result_value -> {snmp_set_response}')
        
        return  [str(value[1]) for value in snmp_set_response]

    @staticmethod
    def get_oid_index(oid: str) -> Optional[int]:
        """
        Extract the index (last sub-identifier) from an OID string.

        Args:
            oid (str): The OID in dot-separated format (e.g., '1.3.6.1.2.1.2.2.1.3.2').

        Returns:
            Optional[int]: The last part of the OID interpreted as an integer, or None if extraction fails.
        """
        if not isinstance(oid, str):
            oid = str(oid)

        try:
            parts = oid.strip().split('.')
            index = int(parts[-1])
            logging.debug(f"Extracted OID index: OID='{oid}', Parts={parts}, Index={index}")
            return index
        except (ValueError, IndexError) as e:
            logging.error(f"Failed to extract index from OID '{oid}': {e}")
            return None

    @staticmethod
    def get_inet_address_type(inet_address: str) -> InetAddressType:
        """
        Determine the InetAddressType of an IP address (IPv4 or IPv6).

        Args:
            inet_address (str): The IP address to check.

        Returns:
            InetAddressType: IPV4 (1) for IPv4 addresses, or IPV6 (2) for IPv6 addresses.

        Raises:
            ValueError: If the IP address is invalid.
        """
        binary = InetUtils.inet_to_binary(inet_address)

        if not binary:
            raise ValueError(f"Invalid IP address: {inet_address}")

        return InetAddressType.IPV6 if len(binary) > 4 else InetAddressType.IPV4

    @staticmethod
    def parse_snmp_datetime(data: bytes) -> str:
        """
        Parses SNMP DateAndTime byte array and returns an ISO 8601 datetime string.

        Args:
            data (bytes): SNMP DateAndTime value as a byte array.

        Returns:
            str: ISO 8601 formatted datetime string (e.g., "2025-05-02T13:15:00").
        """
        if len(data) < 8:
            raise ValueError("Invalid SNMP DateAndTime data (too short)")
        
        # Convert the raw bytes into integer values
        year = data[0] << 8 | data[1]
        month = data[2]
        day = data[3]
        hour = data[4]
        minute = data[5]
        second = data[6]
        decisecond = data[7]  # often ignored

        # Default: naive datetime (no timezone info)
        dt = datetime(year, month, day, hour, minute, second)

        if len(data) >= 11:
            # Timezone info exists
            direction = chr(data[8])
            tz_hours = data[9]
            tz_minutes = data[10]
            offset_minutes = tz_hours * 60 + tz_minutes
            if direction == '-':
                offset_minutes = -offset_minutes
            tz = timezone(timedelta(minutes=offset_minutes))
            dt = dt.replace(tzinfo=tz)

        return dt.isoformat()


###################
# Private Methods #
###################

    def _resolve_oid(self, oid: Union[str, Tuple[str, str, int]]) -> ObjectIdentity:
        """
        Internal helper to resolve an OID.

        Args:
            oid (Union[str, Tuple[str, str, int]]): OID to resolve.

        Returns:
            ObjectIdentity: pysnmp ObjectIdentity.
        """
        if isinstance(oid, tuple):
            self.logger.debug(f"Resolving OID tuple: {oid}")
            return ObjectIdentity(*oid)
        else:
            self.logger.debug(f"Resolving OID string: {oid}")
            return ObjectIdentity(oid)

    def _check_for_errors(self, errorIndication, errorStatus, errorIndex):
        """
        Internal helper to raise exceptions for SNMP errors.

        Args:
            errorIndication: SNMP error indication.
            errorStatus: SNMP error status.
            errorIndex: SNMP error index.

        Raises:
            RuntimeError: When SNMP errors are present.
        """
        if errorIndication:
            raise RuntimeError(f"SNMP operation failed: {errorIndication}")
        if errorStatus:
            raise RuntimeError(f"SNMP error {errorStatus.prettyPrint()} at index {errorIndex}")

    def _is_subtree_match(self, oid_str: str, obj_str: str) -> bool:
        """
        Check if an OID is part of the requested subtree.

        Args:
            oid_str (str): The current OID string.
            obj_str (str): The requested root OID string.

        Returns:
            bool: True if still within subtree, False otherwise.
        """
        oid_parts = oid_str.split('.')
        obj_parts = obj_str.split('.')
        # self.logger.debug(f'OBJ: {obj_parts} -> OID: {oid_parts}')
        return oid_parts[:len(obj_parts)] == obj_parts
    
    @staticmethod
    def truth_value(snmp_value) -> bool:
        """
        Converts SNMP TruthValue integer to a boolean.

        TruthValue ::= INTEGER { true(1), false(2) }

        Args:
            snmp_value (int or str): The raw SNMP integer value or string representation.

        Returns:
            bool: True if value is 1 (true), False if 2 (false).

        Raises:
            ValueError: If the value is not 1 or 2.
        """
        # Attempt to convert the snmp_value to an integer
        try:
            snmp_value = int(snmp_value)
        except ValueError:
            raise ValueError(f"Invalid input for TruthValue: {snmp_value}")

        if snmp_value == 1:
            return True
        elif snmp_value == 2:
            return False
        else:
            raise ValueError(f"Invalid TruthValue: {snmp_value}")

    @staticmethod
    def ticks_to_duration(ticks: int) -> str:
        """
        Converts SNMP sysUpTime ticks to a human-readable duration string.

        SNMP uptime ticks are measured in hundredths of a second.

        Args:
            ticks (int): The sysUpTime value in hundredths of a second.

        Returns:
            str: A formatted duration string like '3 days, 4:05:06.78'
        """
        if ticks < 0:
            raise ValueError("Ticks must be a non-negative integer")

        # Convert hundredths of a second to total seconds and microseconds
        total_seconds = ticks // 100
        remainder_hundredths = ticks % 100
        duration = timedelta(seconds=total_seconds, milliseconds=remainder_hundredths * 10)

        return str(duration)
