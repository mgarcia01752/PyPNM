# FastAPI overview

## Contents

| Subsection | Purpose | Common actions |
|------------|---------|----------------|
| [PyPNM](pypnm/index.md)                               | Service/system endpoints (health, status, operations).   | Check health; list operations; fetch service status.   |
| [Single Capture](single/index.md)                     | One-shot capture/queries (downstream, upstream, system). | Pull RxMER/FEC once; read event log; spectrum/histogram. |
| [Multi Capture](multi/index.md)                       | Scheduled or multi-snapshot workflows and analysis.      | Start capture; poll status; download ZIP; stop early.  |
| [File Management](file-manager/file-manager-api.md)   | Upload/download files to/from the system.                | Upload config; download logs; list stored files.       |
| [Common Schemas](common/index.md)                     | Request/response conventions and shared schemas.         | Review request schema; response wrapper; error model.  |
| [Status Codes](../fast-api/status/fast-api-status-codes.md) | API status and error codes.                        | Map errors to fixes; see retry/validation guidance.    |
