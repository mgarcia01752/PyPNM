# PyPNM System Log Download API

## 📡 Endpoint

**POST** `/pypnm/system/log/download/log`

This endpoint allows clients to download the current PyPNM backend system log file for debugging or historical record purposes.

## 📅 Request Body (JSON)

This endpoint does **not** require any request body fields. Simply make a `POST` request to download the latest log.

## 📄 Response

Returns the PyPNM log file as a plain text attachment.

### 🔸 Example Response Headers

```
Content-Disposition: attachment; filename="pypnm.log"
Content-Type: text/plain
```

### 🔹 Example: Curl Usage

```bash
curl -X POST http://localhost:8000/pypnm/system/log/download/log -o pypnm.log
```

## 🖊️ Notes

* The log file name and path are determined by internal system settings defined in `SystemConfigSettings`.
* If the file cannot be found or accessed, a `500 Internal Server Error` will be returned with an appropriate message.
* This is intended for administrative use or advanced diagnostics.

> ⚠️ Ensure proper authentication or IP-based firewall rules are in place in production deployments to protect sensitive logs.

## 🔍 See Also

* `SystemConfigSettings.log_dir`
* `SystemConfigSettings.log_filename`
* `FileResponse` from FastAPI
