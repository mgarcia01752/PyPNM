# DOCSIS 3.0 Upstream ATDMA Pre-Equalization API

## 📡 Endpoint

**POST** `/docs/if30/us/scqam/chan/preEqualization`

Retrieves pre-equalization coefficients and tap configuration for DOCSIS 3.0 upstream SC-QAM (ATDMA) channels.

## 📥 Request Body (JSON)

```json
{
  "mac_address": "aa:bb:cc:dd:ee:ff",
  "ip_address": "192.168.0.100",
  "snmp": {
    "snmpV2C": {
      "community": "private"
    },
    "snmpV3": {
      "username": "string",
      "securityLevel": "noAuthNoPriv",
      "authProtocol": "MD5",
      "authPassword": "string",
      "privProtocol": "DES",
      "privPassword": "string"
    }
  }
}
```

### 🔑 Fields

| Field        | Type   | Description                    |
| ------------ | ------ | ------------------------------ |
| mac\_address | string | MAC address of the cable modem |
| ip\_address  | string | IP address of the cable modem  |
| snmp         | object | SNMPv2c or SNMPv3 credentials  |

## 📤 Response Body (Per Channel)

```json
{
  "<ChannelID>": {
    "main_tap_location": 8,
    "forward_taps_per_symbol": 1,
    "num_forward_taps": 24,
    "num_reverse_taps": 0,
    "forward_coefficients": [
      {
        "real": 512,
        "imag": -15427,
        "magnitude": 15435.49,
        "magnitude_power_dB": 83.77
      },
      {
        "real": -15425,
        "imag": 768,
        "magnitude": 15444.11,
        "magnitude_power_dB": 83.78
      }
      // ... additional taps
    ],
    "reverse_coefficients": []
  }
}
```

### 📊 Key Response Fields

| Field                      | Type    | Description                                       |
| -------------------------- | ------- | ------------------------------------------------- |
| main\_tap\_location        | integer | Location of the main tap (usually near center)    |
| forward\_taps\_per\_symbol | integer | Forward taps per symbol                           |
| num\_forward\_taps         | integer | Number of forward equalizer taps                  |
| num\_reverse\_taps         | integer | Number of reverse equalizer taps                  |
| forward\_coefficients      | array   | List of complex coefficients in forward direction |
| reverse\_coefficients      | array   | List of complex coefficients in reverse direction |
| ↳ real                     | integer | Real part of tap coefficient                      |
| ↳ imag                     | integer | Imaginary part of tap coefficient                 |
| ↳ magnitude                | float   | Magnitude of the complex tap                      |
| ↳ magnitude\_power\_dB     | float   | Power of the tap in dB                            |

> ℹ️ Tap coefficient values are decoded from the upstream equalizer register and analyzed in-place.

## 📝 Notes

* Each top-level key in the response is a DOCSIS upstream channel ID.
* Forward taps are used to correct pre-echo distortion before transmission.
* Reverse taps are uncommon in ATDMA and may often be empty.
* Useful for diagnostics related to echo path delay, cable reflections, and plant distortion.

> 📂 For interpretation methods, see: `DOCS-IF3-MIB::docsIf3CmStatusUsEqData` and internal tap decoder specifications.
