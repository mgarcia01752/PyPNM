# FAST-API Endpoints Overview

This section provides general documentation and link stubs for the core FastAPI endpoint categories in PyPNM, along with guidance on launching the service and interacting via common HTTP clients and tools.


## Getting Started with FastAPI

1. **Explore interactive docs**

   * **Swagger UI**: [http://localhost:8000/docs](http://localhost:8000/docs)
   * **ReDoc**: [http://localhost:8000/redoc](http://localhost:8000/redoc)

2. **Official references**

   * FastAPI documentation: [https://fastapi.tiangolo.com](https://fastapi.tiangolo.com)
   * Uvicorn server docs: [https://www.uvicorn.org/](https://www.uvicorn.org/)


## Tools & Clients

You can use any HTTP client to interact with the API. Examples:

* **curl** (command-line):

  ```bash
  curl -X POST "http://localhost:8000/advance/multiRxMer/start" \
       -H "Content-Type: application/json" \
       -d @request.json
  ```

* **Postman**:
  Import the `postman_collection.json` provided in the repo root for pre-configured endpoints.

* **Swagger UI**:
  Use the interactive forms to explore request schemas and execute operations directly from the browser.

## Single-Capture

Handles one-off PNM or SNMP operations, such as:

* Retrieving a single RxMER or sysDescr measurement via `POST /system/sysDescr`.

* Fetching one-time histograms or modulation profiles.

* **Guide:** [Single-Capture API Guide](single/index.md)


## Multi-Capture

* **Operation**
Theroy of Operation
  **Guide:** [Multi-Capture Operation](multi/capture-operation.md)

Manages long-running, threaded capture sessions that periodically collect PNM data:

* **Multi-RxMER Capture:**
  Periodic downstream OFDM RxMER sampling and post-capture analysis.
  **Guide:** [Multi-RxMER Capture API Guide](multi/multi-capture-rxmer.md)

* **Multi-DS Channel Estimation:**
  Periodic estimation coefficient collection for multiple OFDM channels.
  **Guide:** [Multi-DS Channel Estimation API Guide](multi/multi-capture-chan-est.md)


## Service Status Code

Defines standardized status codes returned by both SNMP and PNM operations, such as `SUCCESS`, `FAILURE`, `PING_FAILED`, and custom measurement states.

* **Reference:** [Service Status Codes](status/fast-api-status-codes.md)


> **Note:** Update link stubs above to match your documentation structure once the detailed guides exist.
