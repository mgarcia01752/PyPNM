# Generating SSL Certificates for PyPNM

This guide walks you through creating self-signed SSL/TLS certificates for use with the `pypnm` CLI’s `--ssl` option. Follow these steps exactly to generate a certificate and private key suitable for development or internal use.

## Prerequisites

* **OpenSSL** installed on your system.

  * On Ubuntu: `sudo apt update && sudo apt install -y openssl`
* A shell or terminal with write permissions in your chosen directory.

## Steps

### 1. Create a Directory for Certificates

Choose a secure location to store your certificates, e.g., `certs/` in your project root:

```bash
mkdir -p certs
cd certs
```

### 2. Generate a Private Key

Use a 2048‑bit RSA key (you can increase to 4096 bits if desired):

```bash
openssl genrsa -out pypnm.key 2048
```

* **`pypnm.key`** is your private key. Keep it secure and do **not** share it publicly.

### 3. Create a Certificate Signing Request (CSR)

The CSR includes information about your organization and the hostname the cert will serve. For local testing, set Common Name (CN) to `localhost`.

```bash
openssl req -new -key pypnm.key -out pypnm.csr \
  -subj "/C=US/ST=State/L=City/O=YourOrg/OU=IT/CN=localhost"
```

* Adjust `/C=`, `/ST=`, etc., as needed for your organization.

### 4. Generate a Self‑Signed Certificate

Sign the CSR to create a certificate valid for 1 year (365 days):

```bash
openssl x509 -req -in pypnm.csr -signkey pypnm.key -out pypnm.crt -days 365
```

* **`pypnm.crt`** is your public certificate. It can be shared with clients.

### 5. (Optional) Verify the Certificate Contents

Check that the CN and validity are as expected:

```bash
openssl x509 -in pypnm.crt -noout -text | grep -E "Subject:|Not Before|Not After"
```

### 6. Use with the `pypnm` CLI

When launching your service with HTTPS enabled, point `--cert` and `--key` to your new files:

```bash
pypnm serve --ssl --cert certs/pypnm.crt --key certs/pypnm.key
```

Your FastAPI service will now listen on HTTPS (default port 8000):

```
INFO:     Started server process [...] with HTTPS
INFO:     Uvicorn running on https://127.0.0.1:8000
```

---

**Security Note:** Self-signed certificates are suitable for development or internal use only. For production deployments, obtain certificates from a trusted Certificate Authority (CA) like [Let’s Encrypt](https://letsencrypt.org/).
