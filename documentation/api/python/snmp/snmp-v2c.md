# SNMPv2c Client — General Usage Guide

The `Snmp_v2c` class offers an asynchronous, Python-friendly interface for SNMP v2c **GET**, **WALK**, and **SET** operations using `pysnmp`. It optionally supports MIB compilation for faster lookups, includes robust error handling, and provides common utility methods.

---

## Table of Contents

1. [Initialization](#initialization)
2. [Basic Operations](#basic-operations)

   * [GET](#snmp-get)
   * [WALK](#snmp-walk)
   * [SET](#snmp-set)
3. [MIB Compilation](#mib-compilation)
4. [Utility Methods](#utility-methods)
5. [Closing the Client](#closing-the-client)
6. [Error Handling](#error-handling)

---

## Initialization

Instantiate an SNMPv2c client by providing:

* **host**: an `Inet` object encapsulating an IPv4 or IPv6 address
* **community**: SNMP community string (default: `"private"`)
* **port**: SNMP port number (default: `161`)

```python
from pypnm.lib.inet import Inet
from pypnm.snmp.snmp_module import Snmp_v2c

snmp = Snmp_v2c(host=Inet("192.168.0.10"), community="public")
```

---

## Basic Operations

### SNMP GET

Retrieve the value of a single OID:

```python
result = await snmp.get("1.3.6.1.2.1.1.1.0")
```

### SNMP WALK

Traverse an OID subtree and collect all entries:

```python
entries = await snmp.walk("1.3.6.1.2.1.2")
```

### SNMP SET

Assign a new value to a writable OID (explicit type required):

```python
from pysnmp.proto.rfc1902 import OctetString

varbinds = await snmp.set(
    "1.3.6.1.2.1.1.5.0",
    "NewHostName",
    OctetString
)
```

---

## MIB Compilation

To reduce runtime overhead, PyPNM includes a pre-compiled map from symbolic MIB names to numeric OIDs. This bypasses on-the-fly MIB parsing and accelerates SNMP operations.

* **Compiled OIDs module**: [snmp\_compiled\_oids.py](../../../../src/snmp/snmp_compiled_oids.py)

```python
from snmp.snmp_compiled_oids import COMPILED_OIDS

# Fast lookup for sysDescr OID
oid = f"{COMPILED_OIDS['sysDescr']}.0"
result = await snmp.get(oid)
```

---

## Utility Methods

* **`get_result_value(vb)`** — Convert an SNMP GET binding into a human-readable string.
* **`extract_last_oid_index(vb_list)`** — Return the final OID sub-identifier(s) from a list of bindings.
* **`snmp_get_result_last_idx_value(vb_list)`** — Pair each index with its value for table-style data.
* **`get_oid_index(oid_str)`** — Parse the last numeric component from an OID string.
* **`get_inet_address_type(ip)`** — Determine whether an address is IPv4 or IPv6.
* **`parse_snmp_datetime(data)`** — Convert SNMP DateAndTime bytes into an ISO 8601 timestamp.

---

## Closing the Client

After completing SNMP operations, release resources:

```python
snmp.close()
```

---

## Error Handling

* SNMP-level errors (`errorIndication`, `errorStatus`) raise `RuntimeError`.
* Invalid arguments (e.g. missing `value_type` for `set`) raise `ValueError`.

> **Tip:** Wrap SNMP calls in `try/except` blocks to gracefully handle unreachable hosts or authorization failures.
> Remember to run within an `asyncio` event loop, as all methods are asynchronous.

---

For comprehensive API details, refer to the [auto-generated documentation](doc/api/snmp/index.md).
