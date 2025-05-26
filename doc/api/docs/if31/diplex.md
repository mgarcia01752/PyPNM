## 📡 `POST /docs/if31/system/diplexer`

Retrieves the DOCSIS 3.1 diplexer configuration and capabilities from a cable modem. The diplexer defines the frequency split between upstream and downstream channels, helping determine how the modem partitions RF spectrum for transmission and reception.

---

### 🔧 Request

**Content-Type:** `application/json`

#### JSON Body

```json
{
  "mac_address": "00:11:22:33:44:55",
  "ip_address": "192.168.100.1"
}
```

| Field        | Type   | Description                            |
| ------------ | ------ | -------------------------------------- |
| mac\_address | string | MAC address of the target cable modem. |
| ip\_address  | string | IP address used to reach the modem.    |

---

### 📤 Response

**Content-Type:** `application/json`

```json
{
  "status": "0",
  "diplexer_capability": 1,
  "cfg_band_edge": 85,
  "ds_lower_capability": 108,
  "cfg_ds_lower_band_edge": 108,
  "ds_upper_capability": 1218,
  "cfg_ds_upper_band_edge": 1218
}
```

| Field                      | Type   | Description                                                  |
| -------------------------- | ------ | ------------------------------------------------------------ |
| status                     | string | `"0"` indicates success; non-zero values indicate failure.   |
| diplexer\_capability       | int    | Bitmask or value indicating supported diplexer capabilities. |
| cfg\_band\_edge            | int    | Configured upstream-to-downstream band edge in MHz.          |
| ds\_lower\_capability      | int    | Maximum supported downstream lower frequency in MHz.         |
| cfg\_ds\_lower\_band\_edge | int    | Configured downstream lower band edge in MHz.                |
| ds\_upper\_capability      | int    | Maximum supported downstream upper frequency in MHz.         |
| cfg\_ds\_upper\_band\_edge | int    | Configured downstream upper band edge in MHz.                |

---

### ✅ Example

#### Request

```bash
curl -X POST http://<server>/docs/if31/system/diplexer \
     -H "Content-Type: application/json" \
     -d '{"mac_address": "00:11:22:33:44:55", "ip_address": "192.168.100.1"}'
```

#### Response

```json
{
  "status": "0",
  "diplexer_capability": 5,
  "cfg_band_edge": 85,
  "ds_lower_capability": 1,
  "cfg_ds_lower_band_edge": 108,
  "ds_upper_capability": 4,
  "cfg_ds_upper_band_edge": 1002
}
```