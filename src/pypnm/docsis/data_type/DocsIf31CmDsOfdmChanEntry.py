
from __future__ import annotations

# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia

import logging
from pypnm.snmp.compiled_oids import COMPILED_OIDS
from pypnm.snmp.snmp_v2c import Snmp_v2c

class DocsIf31CmDsOfdmChanEntry:
    """
    Represents a DOCSIS 3.1 Cable Modem Downstream OFDM Channel Entry, as defined in the 
    `docsIf31CmDsOfdmChanTable` from the DOCSIS MIB.

    This class encapsulates all relevant channel parameters for a specific OFDM channel index
    and provides methods to populate these attributes via SNMP queries.
    """
    
    index: int
    docsIf31CmDsOfdmChanChannelId: int = 0
    docsIf31CmDsOfdmChanChanIndicator: int = 0
    docsIf31CmDsOfdmChanSubcarrierZeroFreq: int = 0
    docsIf31CmDsOfdmChanFirstActiveSubcarrierNum: int = 0
    docsIf31CmDsOfdmChanLastActiveSubcarrierNum: int = 0
    docsIf31CmDsOfdmChanNumActiveSubcarriers: int = 0
    docsIf31CmDsOfdmChanSubcarrierSpacing: int = 0
    docsIf31CmDsOfdmChanCyclicPrefix: int = 0
    docsIf31CmDsOfdmChanRollOffPeriod: int = 0
    docsIf31CmDsOfdmChanPlcFreq: int = 0
    docsIf31CmDsOfdmChanNumPilots: int = 0
    docsIf31CmDsOfdmChanTimeInterleaverDepth: int = 0
    docsIf31CmDsOfdmChanPlcTotalCodewords: int = 0
    docsIf31CmDsOfdmChanPlcUnreliableCodewords: int = 0
    docsIf31CmDsOfdmChanNcpTotalFields: int = 0
    docsIf31CmDsOfdmChanNcpFieldCrcFailures: int = 0

    def __init__(self, index: int, snmp: Snmp_v2c):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.index = index
        self.snmp = snmp

    async def start(self) -> bool:
        """
        Asynchronously populates the channel data from SNMP.

        Returns:
            bool: True if SNMP queries complete successfully (even if some values are None), False otherwise.
        """
        fields = {
            "docsIf31CmDsOfdmChanChannelId": ("docsIf31CmDsOfdmChanChannelId", int),
            "docsIf31CmDsOfdmChanChanIndicator": ("docsIf31CmDsOfdmChanChanIndicator", int),
            "docsIf31CmDsOfdmChanSubcarrierZeroFreq": ("docsIf31CmDsOfdmChanSubcarrierZeroFreq", int),
            "docsIf31CmDsOfdmChanFirstActiveSubcarrierNum": ("docsIf31CmDsOfdmChanFirstActiveSubcarrierNum", int),
            "docsIf31CmDsOfdmChanLastActiveSubcarrierNum": ("docsIf31CmDsOfdmChanLastActiveSubcarrierNum", int),
            "docsIf31CmDsOfdmChanNumActiveSubcarriers": ("docsIf31CmDsOfdmChanNumActiveSubcarriers", int),
            "docsIf31CmDsOfdmChanSubcarrierSpacing": ("docsIf31CmDsOfdmChanSubcarrierSpacing", int),
            "docsIf31CmDsOfdmChanCyclicPrefix": ("docsIf31CmDsOfdmChanCyclicPrefix", int),
            "docsIf31CmDsOfdmChanRollOffPeriod": ("docsIf31CmDsOfdmChanRollOffPeriod", int),
            "docsIf31CmDsOfdmChanPlcFreq": ("docsIf31CmDsOfdmChanPlcFreq", int),
            "docsIf31CmDsOfdmChanNumPilots": ("docsIf31CmDsOfdmChanNumPilots", int),
            "docsIf31CmDsOfdmChanTimeInterleaverDepth": ("docsIf31CmDsOfdmChanTimeInterleaverDepth", int),
            "docsIf31CmDsOfdmChanPlcTotalCodewords": ("docsIf31CmDsOfdmChanPlcTotalCodewords", int),
            "docsIf31CmDsOfdmChanPlcUnreliableCodewords": ("docsIf31CmDsOfdmChanPlcUnreliableCodewords", int),
            "docsIf31CmDsOfdmChanNcpTotalFields": ("docsIf31CmDsOfdmChanNcpTotalFields", int),
            "docsIf31CmDsOfdmChanNcpFieldCrcFailures": ("docsIf31CmDsOfdmChanNcpFieldCrcFailures", int),
        }

        try:
            for attr, (oid_key, transform) in fields.items():
                try:
                    result = await self.snmp.get(f"{COMPILED_OIDS[oid_key]}.{self.index}")
                    value_list = Snmp_v2c.get_result_value(result)

                    if not value_list:
                        self.logger.warning(f"Invalid value returned for {oid_key}.{self.index}: {value_list}")
                        setattr(self, attr, None)
                        continue

                    value = transform(value_list)
                    setattr(self, attr, value)
                except Exception as e:
                    self.logger.warning(f"Failed to fetch or transform {attr} ({oid_key}): {e}")
                    setattr(self, attr, None)

            return True

        except Exception as e:
            self.logger.exception("Unexpected error during SNMP population")
            return False

    def to_dict(self) -> dict:
        """
        Converts the instance into a dictionary structured as:
            {
                "index": <int>,
                "channel_id": <int>,
                "entry": {
                    ...remaining OFDM fields...
                }
            }
        """
        data = {attr: getattr(self, attr, None) for attr in self.__annotations__}

        missing = [k for k, v in data.items() if v is None]
        if missing:
            raise ValueError(f"Attributes not populated (call start() first): {missing}")

        index = data["index"]
        channel_id = data["docsIf31CmDsOfdmChanChannelId"]
        entry_fields = {
            k: v for k, v in data.items()
            if k not in ("index", "docsIf31CmDsOfdmChanChannelId")
        }

        return {
            "index": index,
            "channel_id": channel_id,
            "entry": entry_fields
        }
