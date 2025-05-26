# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia

import json
import logging
from struct import unpack, calcsize
from typing import Any, Optional, List, Dict, Union
from dataclasses import dataclass, field
from enum import IntEnum
from venv import logger
from pnm.process.pnm_file_type import PnmFileType
from pnm.process.pnm_header import PnmHeader

class ModulationOrderType(IntEnum):
    zero_bit_loaded = 0
    continuous_pilot = 1
    qpsk = 2
    reserved_3 = 3
    qam_16 = 4
    reserved_5 = 5
    qam_64 = 6
    qam_128 = 7
    qam_256 = 8
    qam_512 = 9
    qam_1024 = 10
    qam_2048 = 11
    qam_4096 = 12
    qam_8192 = 13
    qam_16384 = 14
    exclusion = 16
    plc = 20

@dataclass
class ModulationProfileData:
    profile: List[ModulationOrderType] = field(default_factory=list)

    def add(self, modulation: ModulationOrderType):
        self.profile.append(modulation)

    def get(self, index: int) -> ModulationOrderType:
        return self.profile[index]

    def set(self, index: int, modulation: ModulationOrderType):
        self.profile[index] = modulation

    def length(self) -> int:
        return len(self.profile)

@dataclass
class ModulationScheme:
    profile_id: int
    data: Union[dict, None]

class CmDsOfdmModulationProfile(PnmHeader):
    def __init__(self, binary_data: bytes):
        super().__init__(binary_data)
        self.logger = logging.getLogger(self.__class__.__name__)
        
        self.channel_id: Optional[int] = None
        self.mac_address: Optional[str] = None
        self.num_profiles: Optional[int] = None
        self.subcarrier_zero_frequency: Optional[int] = None
        self.first_active_subcarrier_index: Optional[int] = None
        self.subcarrier_spacing: Optional[int] = None
        self.profile_data_length: Optional[int] = None
        self.modulation_profile_data: Optional[bytes] = None
        self.parsed_profiles: List[ModulationScheme] = []

        self._process_modulation_profile()

    def _process_modulation_profile(self) -> None:
        if self.get_pnm_file_type() != PnmFileType.OFDM_MODULATION_PROFILE:
            cann = PnmFileType.OFDM_MODULATION_PROFILE.get_pnm_cann()
            raise ValueError(f"PNM File Stream is not RxMER file type: {cann}, Error: {self.get_pnm_file_type().get_pnm_cann()}")
                
        header_format = '>B6sBIHBI'
        header_size = calcsize(header_format)
        try:
            unpacked = unpack(header_format, self.pnm_data[:header_size])
        except Exception as e:
            raise ValueError(f"Failed to unpack modulation profile header: {e}")

        self.channel_id = unpacked[0]
        self.mac_address = unpacked[1].hex(':')
        self.num_profiles = unpacked[2]
        self.subcarrier_zero_frequency = unpacked[3]
        self.first_active_subcarrier_index = unpacked[4]
        self.subcarrier_spacing = unpacked[5]
        self.profile_data_length = unpacked[6]
        self.modulation_profile_data = self.pnm_data[header_size:]
               
        self._process_modulation_profile_data()

    def _process_modulation_profile_data(self) -> None:
        offset = 0
        data = self.modulation_profile_data
        self.profile_info_list = []

        while offset < len(data):
            try:
                header_format = '>BH'
                header_size = calcsize(header_format)
                profile_id, length = unpack(header_format, data[offset:offset + header_size])
                offset += header_size + length
            except Exception as e:
                raise ValueError(f"Failed to unpack profile header at offset {offset}: {e}")

            profile_info = {
                "profile_id": profile_id,
                "length": length,
                "modulation_profile_data": data[offset - length:offset]
            }

            self.profile_info_list.append(profile_info)
            
        for profile_dict in self.profile_info_list:
            mod_profile_data = profile_dict["modulation_profile_data"]
            offset = 0

            # Save multiple schemas found
            modulation_schema = []

            while offset < len(mod_profile_data):

                try:
                    # First byte in profile data is the scheme type
                    scheme_type = mod_profile_data[offset]
                    offset += 1

                    if scheme_type == 0:  # Subcarrier Range Modulation
                        fmt = '>BH'
                        size = calcsize(fmt)
                        modulation_order, num_subcarriers = unpack(fmt, mod_profile_data[offset:offset + size])
                        offset += size

                        modulation_schema.append({
                            "schema_type": scheme_type,
                            "modulation_order": ModulationOrderType(modulation_order).name.lower(),
                            "num_subcarriers": num_subcarriers
                        })
                        
                    elif scheme_type == 1:  # Subcarrier Skip Modulation
                        fmt = '>BBH'
                        size = calcsize(fmt)
                        main_order, skip_order, num_skipped = unpack(fmt, mod_profile_data[offset:offset + size])
                        offset += size

                        modulation_schema.append({
                            "schema_type": scheme_type,
                            "main_modulation_order": ModulationOrderType(main_order).name.lower(),
                            "skip_modulation_order": ModulationOrderType(skip_order).name.lower(),
                            "num_subcarriers": num_skipped
                        })

                    else:
                        self.logger.warning(f"Skipping unknown scheme type {scheme_type} for profile ID {profile_dict['profile_id']}")
                        continue

                    self.logger.debug(f'{modulation_schema[-1]}')

                except Exception as e:
                    logging.error(f"Error decoding modulation scheme for profile ID {profile_dict['profile_id']}: {e}")

            # Append once per profile (outside the while loop)
            self.parsed_profiles.append(ModulationScheme(
                profile_id=profile_dict["profile_id"],
                data=modulation_schema
            ))

    def get_modulation_profile(self) -> Dict[str, Union[str, int, List[dict]]]:
        """
        Returns the modulation profile information along with basic PNM header metadata.

        This includes details such as:
        - MAC address
        - Channel ID
        - Number of profiles
        - Frequency and subcarrier info
        - Parsed modulation profiles per profile ID

        Returns:
            Dict[str, Union[str, int, List[dict]]]: A dictionary with PNM header fields and
            downstream modulation profile structure, including modulation schemes.
            
            {
                "channel_id": ,
                "mac_address":,
                "num_profiles":,
                "zero_frequency":,
                "first_active_subcarrier_index":,
                "subcarrier_spacing":,
                "profile_data_length_bytes":,
                "profiles": [                
                    'profile_id': , 
                    'schemes': [
                        {
                            'schema_type': , 
                            'modulation_order':, 
                            'num_subcarriers':
                        }
                    ]
                }
            }
            
        """
        data: Dict[str, Any] = self.getPnmHeader(header_only=True)

        # Add modulation profile metadata and parsed content
        data.update({
            "channel_id": self.channel_id,
            "mac_address": self.mac_address,
            "num_profiles": self.num_profiles,
            "zero_frequency": self.subcarrier_zero_frequency,
            "first_active_subcarrier_index": self.first_active_subcarrier_index,
            "subcarrier_spacing": self.subcarrier_spacing * 1000,
            "profile_data_length_bytes": self.profile_data_length,
            "profiles": [
                {
                    "profile_id": p.profile_id,
                    "schemes": p.data
                }
                for p in self.parsed_profiles
            ]
        })

        return data

    def to_dict(self) -> dict:
        """
            Returns a dictionary of the parsed modulation profile data.

            Returns:
            dict: Parsed modulation profile details.
        
            {
                "channel_id": ,
                "mac_address":,
                "num_profiles":,
                "zero_frequency":,
                "first_active_subcarrier_index":,
                "subcarrier_spacing":,
                "profile_data_length_bytes":,
                "profiles": [                
                    'profile_id': , 
                    'schemes': [
                        {
                            'schema_type': , 
                            'modulation_order':, 
                            'num_subcarriers':
                        }
                    ]
                }
            }          
            
        """
        return self.get_modulation_profile()

    def to_json(self, pretty: bool = True) -> str:
        """
        Serialize the parsed modulation profile data to a JSON-formatted string.

        Args:
            pretty (bool): If True, the JSON output will be indented for readability.

        Returns:
            str: JSON string of the modulation profile data.
        """
        return json.dumps(self.to_dict(), indent=4 if pretty else None)

    def __str__(self) -> str:
        return f'{self.__class__.__name__}'