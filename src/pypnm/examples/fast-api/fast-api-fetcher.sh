#!/usr/bin/env bash
# SPDX-License-Identifier: MIT
# SNMP‐based PNM data fetcher via FastAPI endpoint.
#
# Usage:
#   ./fast-api-fetch.sh --url URL --mac MAC --inet INET --v2c COMMUNITY [OPTIONS]
#
#   -o, --output        File to write JSON (default stdout)
#   --v3-*              SNMPv3 parameters (optional)
#
# Example:
#   ./fast-api-fetch.sh \
#     --url http://localhost:8000/docs/pnm/us_ofdma_pre_eq \
#     --mac 0050.f112.df0c --inet 172.20.58.24 --v2c private \
#     -o result.json

set -euo pipefail

usage() {
  cat <<EOF
Usage: $(basename "$0") --url URL --mac MAC --inet INET --v2c COMMUNITY [OPTIONS]
Required:
  --url        FastAPI endpoint
  --mac        Cable modem MAC address
  --inet       IP address or interface
  --v2c        SNMPv2c community
Optional SNMPv3:
  --v3-username USER
  --v3-security-level LEVEL
  --v3-auth-protocol PROTO
  --v3-auth-password PASS
  --v3-priv-protocol PROTO
  --v3-priv-password PASS
Output:
  -o, --output  File to write JSON (else stdout)
EOF
  exit 1
}

# defaults
OUTPUT=""
declare URL MAC INET V2C_COMM
declare V3_USER V3_SEC V3_AUTH_PROTO V3_AUTH_PASS V3_PRIV_PROTO V3_PRIV_PASS

# parse args
while [[ $# -gt 0 ]]; do
  case $1 in
    --url)               URL=$2; shift 2;;
    --mac)               MAC=$2; shift 2;;
    --inet)              INET=$2; shift 2;;
    --v2c)               V2C_COMM=$2; shift 2;;
    --v3-username)       V3_USER=$2; shift 2;;
    --v3-security-level) V3_SEC=$2; shift 2;;
    --v3-auth-protocol)  V3_AUTH_PROTO=$2; shift 2;;
    --v3-auth-password)  V3_AUTH_PASS=$2; shift 2;;
    --v3-priv-protocol)  V3_PRIV_PROTO=$2; shift 2;;
    --v3-priv-password)  V3_PRIV_PASS=$2; shift 2;;
    -o|--output)         OUTPUT=$2; shift 2;;
    -h|--help)           usage;;
    *) echo "Unknown arg: $1" >&2; usage;;
  esac
done

: "${URL:?--url is required}"
: "${MAC:?--mac is required}"
: "${INET:?--inet is required}"
: "${V2C_COMM:?--v2c is required}"

# build SNMP object
SNMP_JSON=$(cat <<EOF
"snmp": {
  "snmpV2C": { "community": "${V2C_COMM}" },
  "snmpV3": {
    "username": "${V3_USER:-}",
    "securityLevel": "${V3_SEC:-noAuthNoPriv}",
    "authProtocol": "${V3_AUTH_PROTO:-MD5}",
    "authPassword": "${V3_AUTH_PASS:-}",
    "privProtocol": "${V3_PRIV_PROTO:-DES}",
    "privPassword": "${V3_PRIV_PASS:-}"
  }
}
EOF
)

# build full payload
PAYLOAD=$(cat <<EOF
{
  "mac_address": "${MAC}",
  "ip_address": "${INET}",
  ${SNMP_JSON}
}
EOF
)

# execute
if [[ -n $OUTPUT ]]; then
  curl -sSf -X POST "$URL" \
    -H "Content-Type: application/json" \
    -d "$PAYLOAD" \
    -o "$OUTPUT"
else
  curl -sSf -X POST "$URL" \
    -H "Content-Type: application/json" \
    -d "$PAYLOAD"
  echo
fi
