# PyPNM System Web Service API

This document describes the **PyPNM System Web Service** endpoints used to manage the live FastAPI application, including triggering a hot reload in development mode.

## 🔄 Trigger Reload

**Endpoint:**

``` text
GET /pypnm/system/webService/reload
```

**Summary:**
Touch the source file at runtime to force Uvicorn (or Hypercorn) to reload the application when running in `--reload` mode. Only available in development.

**Access:**
No authentication required (development only).

### Response Codes

| HTTP Code | Description                                |
| --------- | ------------------------------------------ |
| 200       | Reload triggered successfully              |
| 500       | Failed to touch file; reload not triggered |

### Response Body

* **Success (200):**

  ```json
  {
    "status": "reload triggered"
  }
  ```

* **Failure (500):**

  ```json
  {
    "status": "reload failed",
    "error": "<error message>"
  }
  ```

### Example (cURL)

```bash
curl -X GET http://localhost:8000/pypnm/system/webService/reload
```

> **Note:** This endpoint only works if the FastAPI server is started with:
>
> ```bash
> uvicorn main:app --reload
> ```

**Author:** Maurice Garcia
**License:** MIT
