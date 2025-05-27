
# DOCSIS 3.0 Upstream SC-QAM Channel Stats

This section describes the functionality of the DOCSIS 3.0 Upstream SC-QAM Channel Stats API endpoint.

## Request Schema

### UsScQamChannelRequest

The request schema expects the following input:

```python
from pydantic import BaseModel, Field

class UsScQamChannelRequest(BaseModel):
    mac_address: str = Field(..., example="a0:b1:c2:d3:e4:f5")
    ip_address: str = Field(..., example="192.168.100.1")
```

- `mac_address`: The MAC address of the cable modem.
- `ip_address`: The IP address of the cable modem.

## Response Schema

### UsScQamChannelEntryResponse

The response schema will return a list of upstream SC-QAM channel entries:

```python
from pydantic import BaseModel, Field
from typing import Dict, Any

class UsScQamChannelEntryResponse(BaseModel):
    index: int = Field(..., description="Upstream channel table index")
    channel_id: int = Field(..., description="docsIfUpChannelId")
    entry: Dict[str, Any] = Field(..., description="All other DOCSIS Upstream channel fields")
```

- `index`: The table index for the upstream channel.
- `channel_id`: The ID of the upstream channel.
- `entry`: A dictionary of additional fields related to the upstream channel.

## Service

### UsScQamChannelService

The service that processes the request and fetches upstream SC-QAM channel stats from the cable modem is defined as follows:

```python
from typing import List
from pypnm.docsis.cable_modem import CableModem
from pypnm.docsis.data_type import DocsIfUpstreamChannelEntry
from pypnm.lib.inet import Inet
from pypnm.lib.mac_address import MacAddress

class UsScQamChannelService:

    def __init__(self, mac_address: str, ip_address: str):
        self.cm = CableModem(mac_address=MacAddress(mac_address), inet=Inet(ip_address))

    async def get_upstream_entries(self) -> List[dict]:
        entries = await self.cm.getDocsIfUpstreamChannelEntry()
        result = []

        for entry in entries:
            success = await entry.start()
            if success:
                result.append(entry.to_dict())

        return result
```

The `UsScQamChannelService` fetches the upstream channel entries and processes them to return the data in the expected dictionary format.

## Router

### UsScQamChannel Router

The following router defines the `/stats` endpoint for fetching upstream SC-QAM channel stats:

```python
from fastapi import APIRouter
from fastapi.responses import JSONResponse
from typing import List

from pypnm.api.routes.docs.if30.ds.scqam.chan.stats.schemas import UsScQamChannelEntryResponse, UsScQamChannelRequest
from pypnm.api.routes.docs.if30.ds.scqam.chan.stats.service import UsScQamChannelService

router = APIRouter(prefix="/docs/if/us/scqam/chan", tags=["DOCSIS 3.0 US SC-QAM Channel Stats"])

@router.post("/stats", response_model=List[UsScQamChannelEntryResponse])
async def get_upstream_channels(req: UsScQamChannelRequest):
    service = UsScQamChannelService(mac_address=req.mac_address, ip_address=req.ip_address)
    data = await service.get_upstream_entries()
    return JSONResponse(content=data)
```

### Endpoint Details

- **Method**: `POST`
- **URL**: `/docs/if/us/scqam/chan/stats`
- **Request**: Expects a `UsScQamChannelRequest` containing `mac_address` and `ip_address`.
- **Response**: Returns a list of `UsScQamChannelEntryResponse` objects representing the upstream SC-QAM channel stats.

## Example

### Request

```json
{
  "mac_address": "a0:b1:c2:d3:e4:f5",
  "ip_address": "192.168.100.1"
}
```

### Response

```json
[
  {
    "index": 1,
    "channel_id": 101,
    "entry": {
      "docsIfUpChannelFrequency": "1000000",
      "docsIfUpChannelPower": "-5.0"
      // other fields...
    }
  }
]
