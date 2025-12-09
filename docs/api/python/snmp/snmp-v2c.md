# SNMPv2c Client — General Usage Guide

Asynchronous SNMPv2c Get, Walk, And Set With Fast OID Resolution And Practical Utilities.

## Table of Contents

1. [Initialization](#initialization)
2. [Basic Operations](#basic-operations)

   * [GET](#snmp-get)
   * [WALK](#snmp-walk)
   * [SET](#snmp-set)

3. [MIB Compilation](#mib-compilation)
4. [Utility Methods](#utility-methods)
5. [Closing The Client](#closing-the-client)
6. [Error Handling](#error-handling)
7. [Additional Usage Patterns](#additional-usage-patterns)
8. [General, Non-DOCSIS Examples](#general-non-docsis-examples)

## Initialization

Instantiate an SNMPv2c client:

```python
import asyncio
from pypnm.lib.inet import Inet
from pypnm.snmp.snmp_v2c import Snmp_v2c  # adjust path to your project

async def main():
    snmp = Snmp_v2c(host=Inet("192.168.0.100"), community="public")  # default port 161
    try:
        rows = await snmp.get("sysName.0")
        print([Snmp_v2c.get_result_value(vb) for vb in rows])
    finally:
        snmp.close()

asyncio.run(main())
```

## Basic Operations

### SNMP GET

Accepts numeric OIDs, symbolic names (resolved via compiled map), or tuple segments:

```python
# Symbolic + instance
rows = await snmp.get("sysDescr.0")

# Numeric OID
rows = await snmp.get("1.3.6.1.2.1.1.1.0")

# Tuple form (base + suffix)
rows = await snmp.get(("1.3.6.1.2.1.1.5", "0"))

value = Snmp_v2c.get_result_value(rows[0]) if rows else None
```

### SNMP WALK

Traverse a subtree; returns `None` if empty:

```python
entries = await snmp.walk("ifDescr")  # 1.3.6.1.2.1.2.2.1.2
pairs = Snmp_v2c.snmp_get_result_last_idx_force_value_type(entries, str) if entries else []
idx_to_name = dict(pairs)  # {2: "GigabitEthernet0/1", ...}
```

### SNMP SET

Explicit pysnmp type is required:

```python
from pysnmp.proto.rfc1902 import OctetString, Integer32

# Strings
ack = await snmp.set("sysLocation.0", "MDF-Rack-A1", OctetString)

# Integers
ack = await snmp.set("snmpSetSerialNo.0", 42, Integer32)
```

## MIB Compilation

Use the precompiled symbol→OID map to avoid runtime MIB parsing:

```python
from pypnm.snmp.compiled_oids import COMPILED_OIDS

sysdescr_oid = f"{COMPILED_OIDS['sysDescr']}.0"
rows = await snmp.get(sysdescr_oid)
print([Snmp_v2c.get_result_value(vb) for vb in rows])
```

You can also pass symbolic names directly (e.g., `"sysDescr.0"`); the client resolves them internally.

## Utility Methods

| Method                                               | Input              | Output                | Description                                             |
| ---------------------------------------------------- | ------------------ | --------------------- | ------------------------------------------------------- |
| `get_result_value(vb)`                               | `ObjectType`/tuple | `string \| None`      | Human-readable conversion; pretty-prints `OctetString`. |
| `snmp_get_result_value(rows)`                        | `List[ObjectType]` | `List[string]`        | String values for each varbind.                         |
| `snmp_get_result_bytes(rows)`                        | `List[ObjectType]` | `List[bytes]`         | Raw bytes via `asOctets()` when available.              |
| `snmp_get_result_last_idx_value(rows)`               | `List[ObjectType]` | `List[(int, string)]` | `(last_index, value)` pairs per row.                    |
| `snmp_get_result_last_idx_force_value_type(rows, T)` | rows, `int`/`str`  | `List[(int, T)]`      | Same as above with value cast.                          |
| `get_oid_index(oid)`                                 | `string`           | `int \| None`         | Trailing numeric index from an OID.                     |
| `extract_last_oid_index(rows)`                       | rows               | `List[int]`           | Batch extract trailing indices.                         |
| `extract_oid_indices(rows, n=1)`                     | rows, `int`        | `List[List[int]]`     | Last `n` indices per row (for composite indexes).       |
| `parse_snmp_datetime(bytes)`                         | `bytes`            | `string`              | SNMP `DateAndTime` → ISO-8601 string.                   |
| `truth_value(v)`                                     | `int \| str`       | `bool`                | SNMP `TruthValue` (`1=true`, `2=false`).                |
| `ticks_to_duration(ticks)`                           | `int`              | `string`              | `sysUpTime` hundredths → duration.                      |
| `get_inet_address_type(ip)`                          | `string`           | `InetAddressType`     | `IPV4` or `IPV6`.                                       |

## Closing The Client

Always release resources:

```python
snmp.close()
```

## Error Handling

* Transport/engine or protocol errors raise `RuntimeError`.
* Invalid inputs (e.g., `set` without a type) raise `ValueError`.

Pattern:

```python
try:
    rows = await snmp.get("sysUpTime.0")
    ticks = int(Snmp_v2c.get_result_value(rows[0]))
    print(Snmp_v2c.ticks_to_duration(ticks))
except RuntimeError:
    ...
except ValueError:
    ...
```

## Additional Usage Patterns

### Map Interface Index → Name

```python
rows = await snmp.walk("ifDescr")
idx_to_name = dict(Snmp_v2c.snmp_get_result_last_idx_force_value_type(rows, str)) if rows else {}
```

### Extract Multiple Index Components (Composite Indexes)

```python
rows = await snmp.walk("1.3.6.1.2.1.10.7.2.1")  # example table
idx_pairs = Snmp_v2c.extract_oid_indices(rows, num_indices=2) if rows else []
# [[33, 1], [33, 2], [34, 1], ...]
```

### Force Integer Values From A Table

```python
rows = await snmp.walk("ifSpeed")
speed_pairs = Snmp_v2c.snmp_get_result_last_idx_force_value_type(rows, int) if rows else []
# [(2, 1000000000), (3, 100000000), ...]
```

### Handle `OctetString` As Bytes (e.g., MAC-Like Values)

```python
rows = await snmp.get("ifPhysAddress.2")
raw = Snmp_v2c.snmp_get_result_bytes(rows)[0]
mac = ":".join(f"{b:02x}" for b in raw)
```

### Symbolic OID With Instance Suffix

```python
name = Snmp_v2c.get_result_value((await snmp.get("sysName.0"))[0])
descr = Snmp_v2c.get_result_value((await snmp.get("sysDescr.0"))[0])
```

### Parse `DateAndTime` To ISO-8601

```python
rows = await snmp.get("hrSystemDate.0")
ts = Snmp_v2c.parse_snmp_datetime(Snmp_v2c.snmp_get_result_bytes(rows)[0])
```

### Convert `sysUpTime` Ticks To Human Duration

```python
ticks = int(Snmp_v2c.get_result_value((await snmp.get("sysUpTime.0"))[0]))
print(Snmp_v2c.ticks_to_duration(ticks))
```

### IPv6 Targets

```python
snmp_v6 = Snmp_v2c(host=Inet("2001:db8::100"), community="public")
rows = await snmp_v6.get("sysObjectID.0")
snmp_v6.close()
```

### Batch GETs With `asyncio.gather`

```python
import asyncio

oids = ["sysName.0", "sysLocation.0", "sysContact.0", "sysObjectID.0"]
results = await asyncio.gather(*[snmp.get(oid) for oid in oids], return_exceptions=True)

values = []
for res in results:
    if isinstance(res, Exception) or not res:
        values.append(None)
    else:
        values.append(Snmp_v2c.get_result_value(res[0]))
print(dict(zip(oids, values)))
```

## General, Non-DOCSIS Examples

Simple, device-agnostic snippets that you can lift into scripts or notebooks.

### 1) Read System Info (Name, Description, Uptime)

```python
async def read_system_info():
    snmp = Snmp_v2c(Inet("192.168.0.100"), community="public")
    try:
        name  = Snmp_v2c.get_result_value((await snmp.get("sysName.0"))[0])
        descr = Snmp_v2c.get_result_value((await snmp.get("sysDescr.0"))[0])
        ut    = Snmp_v2c.get_result_value((await snmp.get("sysUpTime.0"))[0])
        uptime = Snmp_v2c.ticks_to_duration(int(ut))
        print({"sysName": name, "sysDescr": descr, "sysUpTime": uptime})
    finally:
        snmp.close()
```

### 2) Walk Interface Names

```python
async def map_ifindex_to_name():
    snmp = Snmp_v2c(Inet("192.168.0.100"), community="public")
    try:
        rows = await snmp.walk("ifDescr")
        mapping = dict(Snmp_v2c.snmp_get_result_last_idx_force_value_type(rows, str)) if rows else {}
        print(mapping)
    finally:
        snmp.close()
```

### 3) Get Interface Speeds As Integers

```python
async def interface_speeds():
    snmp = Snmp_v2c(Inet("192.168.0.100"), community="public")
    try:
        rows = await snmp.walk("ifSpeed")
        speeds = Snmp_v2c.snmp_get_result_last_idx_force_value_type(rows, int) if rows else []
        print(speeds)  # [(2, 1_000_000_000), ...]
    finally:
        snmp.close()
```

### 4) Set sysLocation/sysContact

```python
from pysnmp.proto.rfc1902 import OctetString

async def set_location_and_contact():
    snmp = Snmp_v2c(Inet("192.168.0.100"), community="private")
    try:
        await snmp.set("sysLocation.0", "MDF-Rack-A1", OctetString)
        await snmp.set("sysContact.0", "noc@example.com", OctetString)
    finally:
        snmp.close()
```

### 5) Parse `hrSystemDate.0` `DateAndTime`

```python
async def parse_hr_system_date():
    snmp = Snmp_v2c(Inet("192.168.0.100"), community="public")
    try:
        rows = await snmp.get("hrSystemDate.0")
        raw = Snmp_v2c.snmp_get_result_bytes(rows)[0]
        print(Snmp_v2c.parse_snmp_datetime(raw))
    finally:
        snmp.close()
```

### 6) Use Compiled OIDs Directly

```python
from pypnm.snmp.compiled_oids import COMPILED_OIDS

async def compiled_oid_lookup():
    snmp = Snmp_v2c(Inet("192.168.0.100"), community="public")
    try:
        sysdescr_oid = f"{COMPILED_OIDS['sysDescr']}.0"
        val = Snmp_v2c.get_result_value((await snmp.get(sysdescr_oid))[0])
        print(val)
    finally:
        snmp.close()
```

### 7) Minimal Robust GET Wrapper

```python
async def robust_get(oid: str):
    snmp = Snmp_v2c(Inet("192.168.0.100"), community="public")
    try:
        try:
            rows = await snmp.get(oid)
            return Snmp_v2c.get_result_value(rows[0]) if rows else None
        except (RuntimeError, ValueError):
            return None
    finally:
        snmp.close()

# Example
# print(asyncio.run(robust_get("sysObjectID.0")))
```
