# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia

import json
from typing import Any, List, Dict, Optional
from struct import unpack, calcsize
import logging

from pypnm.pnm.process.pnm_file_type import PnmFileType
from pypnm.pnm.process.pnm_header import PnmHeader

class CmDsOfdmFecSummary(PnmHeader):
    def __init__(self, binary_data: bytes):
        super().__init__(binary_data)
        self.logger = logging.getLogger(self.__class__.__name__)

        self._channel_id: Optional[int] = None
        self._mac_address: Optional[str] = None
        self._summary_type: Optional[int] = None
        self._num_profiles: Optional[int] = None
        self.fec_summary_data: Optional[List[Dict[str, Any]]] = None
        self.__process()

    def __process(self) -> None:
        """
        Processes FEC Summary information:
        - DS Channel Id         (1 byte)
        - CM MAC Address        (6 bytes)
        - Summary Type          (1 byte)
        - Number of Profiles    (1 byte)
        - FEC Data              (FecSummaryData)
        """
        if self.get_pnm_file_type() != PnmFileType.OFDM_FEC_SUMMARY:
            cann = PnmFileType.OFDM_FEC_SUMMARY.get_pnm_cann()
            raise ValueError(f"PNM File Stream is not RxMER file type: {cann}, Error: {self.get_pnm_file_type().get_pnm_cann()}")
                
        fec_summary_format = '!B6sBB'
        fec_summary_size = calcsize(fec_summary_format)
        unpacked_data = unpack(fec_summary_format, self.pnm_data[:fec_summary_size])

        self.logger.debug(f"FEC Summary Header Data: {self.pnm_data[:fec_summary_size].hex()}")

        self._channel_id = unpacked_data[0]
        self._mac_address = unpacked_data[1].hex(':')
        self._summary_type = unpacked_data[2]
        self._num_profiles = unpacked_data[3]

        fec_data_start = fec_summary_size
        self.fec_summary_data = []

        for profile_index in range(self._num_profiles):
            profile_format = '!B H'
            profile_size = calcsize(profile_format)

            if len(self.pnm_data) >= fec_data_start + profile_size:
                profile_data = unpack(profile_format, self.pnm_data[fec_data_start:fec_data_start + profile_size])
                profile_id = profile_data[0]
                number_of_sets = profile_data[1]
                self.logger.debug(f"Profile {profile_id} has {number_of_sets} sets of codeword entries.")

                fec_summary_for_profile = {
                    "profile_id":       profile_id,
                    "number_of_sets":   number_of_sets,
                    "codeword_entries": []
                }

                fec_data_start += profile_size
                for _ in range(number_of_sets):
                    codeword_set_format = '!I 3I'
                    codeword_set_size = calcsize(codeword_set_format)

                    if len(self.pnm_data) >= fec_data_start + codeword_set_size:
                        codeword_set = unpack(codeword_set_format, self.pnm_data[fec_data_start:fec_data_start + codeword_set_size])
                        timestamp, total_codewords, corrected_codewords, uncorrectable_codewords = codeword_set
                        fec_summary_for_profile["codeword_entries"].append({
                            "timestamp":                timestamp,
                            "total_codewords":          total_codewords,
                            "corrected_codewords":      corrected_codewords,
                            "uncorrectable_codewords":  uncorrectable_codewords
                        })
                        self.logger.debug(f"Codeword set: timestamp={timestamp}, total={total_codewords}, corrected={corrected_codewords}, uncorrectable={uncorrectable_codewords}")
                        fec_data_start += codeword_set_size
                    else:
                        self.logger.error(f"Not enough data to parse codeword set for profile {profile_id} at position {fec_data_start}")
                        break

                self.fec_summary_data.append(fec_summary_for_profile)
            else:
                self.logger.error(f"Not enough data to parse profile {profile_index} starting at {fec_data_start}")
                break

        self.logger.debug(f"Parsed {len(self.fec_summary_data)} profiles from FEC summary.")

    def to_dict(self) -> Dict[str, Any]:
        """
        Converts the processed FEC summary data to a dictionary.
        
        {
            "status": "SUCCESS",
            "channel_id": 34,
            "mac_address": "00:50:f1:12:dc:c3",
            "summary_type": 2,
            "num_profiles": 5,
            "fec_summary_data": [
                {
                    "profile_id": 255,
                    "number_of_sets": 600,
                    "codeword_entries": [
                        {
                            "timestamp": 626563,
                            "total_codewords": 44444,
                            "corrected_codewords": 0,
                            "uncorrectable_codewords": 0
                        }
                    ]
                }
            ]
        }        
        
        """
        out:Dict[str, Any] = {}

        out = self.getPnmHeader()
        out.update ({
                "channel_id":       self._channel_id,
                "mac_address":      self._mac_address,
                "summary_type":     self._summary_type,
                "num_profiles":     self._num_profiles,
                "fec_summary_data": self.fec_summary_data
        })

        return out

    def to_json(self) -> str:
        """
        Converts the processed FEC summary data to a JSON string.
        """
        return json.dumps(self.to_dict(), indent=4)
