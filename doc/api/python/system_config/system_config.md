### 📘 PyPNM System Configuration API

Manage the system configuration for the PyPNM application using the following endpoints.

---

#### 📍 Base URL

```
/pypnm/system/config
```

---

### 🚀 Endpoints

| Endpoint                            | Description                             |
|-------------------------------------|-----------------------------------------|
| `POST /pypnm/system/config/get`     | Retrieve current system configuration.  |
| `POST /pypnm/system/config/update`  | Update the system configuration.        |


---

### 📥 Request Examples

#### 🔍 `POST /pypnm/system/config/get`

Retrieve the current configuration.

**Request:**

```http
POST /pypnm/system/config/get
Content-Type: application/json
```

**Response:**

```json
{
  "status": "success",
  "data": {
    "snmp_timeout": 5,
    "tftp_server": "192.168.100.10",
    "log_level": "INFO"
    // ... more fields
  }
}
```

---

#### ✏️ `POST /pypnm/system/config/update`

Update the PyPNM configuration settings.

**Request:**

```http
POST /pypnm/system/config/update
Content-Type: application/json

{
  "snmp_timeout": 10,
  "tftp_server": "192.168.100.20",
  "log_level": "DEBUG"
}
```

**Response:**

```json
{
  "status": "success",
  "message": "Configuration updated"
}
```

---

### 🔐 Notes

* Only valid keys from `SystemConfigModel` can be updated.
* Any update triggers a reload of the live configuration via `PnmConfigManager`.
