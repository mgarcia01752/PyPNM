# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia

import logging
from pypnm.snmp.snmp_v2c import Snmp_v2c
from pypnm.snmp.compiled_oids import COMPILED_OIDS

class DocsIfUpstreamChannelEntry:

    index: int
    docsIfUpChannelId: int = 0
    docsIfUpChannelFrequency: int = 0
    docsIfUpChannelWidth: int = 0
    docsIfUpChannelModulationProfile: int = 0
    docsIfUpChannelSlotSize: int = 0
    docsIfUpChannelTxTimingOffset: int = 0
    docsIfUpChannelRangingBackoffStart: int = 0
    docsIfUpChannelRangingBackoffEnd: int = 0
    docsIfUpChannelTxBackoffStart: int = 0
    docsIfUpChannelTxBackoffEnd: int = 0
    docsIfUpChannelType: int = 0
    docsIfUpChannelCloneFrom: int = 0
    docsIfUpChannelUpdate: bool = False
    docsIfUpChannelStatus: int = 0
    docsIfUpChannelPreEqEnable: bool = False

    # Additional fields from DOCS-IF3-MIB
    docsIf3CmStatusUsTxPower: float = 0.0
    docsIf3CmStatusUsT3Timeouts: int = 0
    docsIf3CmStatusUsT4Timeouts: int = 0
    docsIf3CmStatusUsRangingAborteds: int = 0
    docsIf3CmStatusUsModulationType: int = 0
    docsIf3CmStatusUsEqData: str = None
    docsIf3CmStatusUsT3Exceededs: int = 0
    docsIf3CmStatusUsIsMuted: bool = False
    docsIf3CmStatusUsRangingStatus: int = 0

    def __init__(self, index: int, snmp: Snmp_v2c):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.index = index
        self.snmp = snmp

    async def start(self) -> bool:
        """
        Asynchronously populates the channel data from SNMP.

        Returns:
            bool: True if SNMP queries complete successfully, False otherwise.
        """
        def tenthdBmV_to_float(value: str) -> float | None:
            try:
                return float(value) / 10.0
            except Exception:
                return None
            
        fields = {
            # Base DOCSIS Upstream Channel Fields
            "docsIfUpChannelId": int,
            "docsIfUpChannelFrequency": int,
            "docsIfUpChannelWidth": int,
            "docsIfUpChannelModulationProfile": int,
            "docsIfUpChannelSlotSize": int,
            "docsIfUpChannelTxTimingOffset": int,
            "docsIfUpChannelRangingBackoffStart": int,
            "docsIfUpChannelRangingBackoffEnd": int,
            "docsIfUpChannelTxBackoffStart": int,
            "docsIfUpChannelTxBackoffEnd": int,
            "docsIfUpChannelType": int,
            "docsIfUpChannelCloneFrom": int,
            "docsIfUpChannelUpdate": Snmp_v2c.truth_value,
            "docsIfUpChannelStatus": int,
            "docsIfUpChannelPreEqEnable": Snmp_v2c.truth_value,

            # DOCS-IF3-MIB Fields
            "docsIf3CmStatusUsTxPower": tenthdBmV_to_float,
            "docsIf3CmStatusUsT3Timeouts": int,
            "docsIf3CmStatusUsT4Timeouts": int,
            "docsIf3CmStatusUsRangingAborteds": int,
            "docsIf3CmStatusUsModulationType": int,
            "docsIf3CmStatusUsEqData": str,
            "docsIf3CmStatusUsT3Exceededs": int,
            "docsIf3CmStatusUsIsMuted": Snmp_v2c.truth_value,
            "docsIf3CmStatusUsRangingStatus": int,
        }

        try:
            for attr, transform in fields.items():
                oid_key = attr
                try:
                    result = await self.snmp.get(f"{COMPILED_OIDS[oid_key]}.{self.index}")
                    value_list = Snmp_v2c.get_result_value(result)

                    if not value_list:
                        self.logger.warning(f"No value for {oid_key}.{self.index}")
                        setattr(self, attr, None)
                        continue

                    if isinstance(transform, type) and hasattr(transform, "from_snmp"):
                        value = transform.from_snmp(value_list)
                    else:
                        value = transform(value_list)

                    setattr(self, attr, value)

                except Exception as e:
                    self.logger.warning(f"Error fetching {attr}: {e}")
                    setattr(self, attr, None)

            return True

        except Exception as e:
            self.logger.exception("Error populating DocsIfUpstreamChannelEntry")
            return False

    def to_dict(self) -> dict:
        """
        Converts the instance into a standardized dictionary format.

        Returns:
            dict: {
                "index": int,
                "channel_id": int,
                "entry": {field: value, ...}
            }
        """
        entry_data = {}
        channel_id = None

        for attr in self.__annotations__:
            if attr == "index":
                continue
            value = getattr(self, attr, None)
            if attr == "docsIfUpChannelId":
                channel_id = value
            entry_data[attr] = value

        return {
            "index": self.index,
            "channel_id": channel_id if channel_id is not None else 0,
            "entry": entry_data
        }
