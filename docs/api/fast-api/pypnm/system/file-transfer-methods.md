# PyPNM PNM File Retrieval Methods

PyPNM supports several ways to fetch Proactive Network Maintenance (PNM) files—whether they’re uploaded by a cable modem (CM) or staged on a remote host. This guide explains the `system.json` settings and details setup, security, and trade-offs for each retrieval method.

## System Configuration

`system.json` (see `src/pypnm/settings/system.json`) controls how PyPNM fetches files. Verify the retrieval block is correct:

```json
"retrival_method": {
  "method": "local",
  "methods": {
    "local": { "src_dir": "/srv/tftp" },
    "tftp":  { "host": "localhost", "port": 69, "timeout": 5, "remote_dir": "" },
    "ftp":   { "host": "localhost", "port": 21, "tls": false, "timeout": 5, "user": "test", "password": "tftp", "remote_dir": "/srv/tftp" },
    "scp":   { "host": "localhost", "port": 22, "user": "test", "password": "tftp", "remote_dir": "/srv/tftp" },
    "sftp":  { "host": "localhost", "port": 22, "user": "test", "password": "tftp", "remote_dir": "/srv/tftp" },
    "http":  { "base_url": "http://STUB/",  "port": 80 },
    "https": { "base_url": "https://STUB/", "port": 443 }
  }
}
```

> Note: The key is spelled `retrival_method` in the current schema. Keep this exact spelling unless you update the code paths that read it.

## Local Transfer

### Description

* PyPNM ingests files from a local directory (e.g., `.data/pnm`) or a mounted share.
* Optionally, a local TFTP daemon writes CM uploads into the watched directory.

### Setup Complexity

* Low (watched folder).
* Moderate if hosting TFTP locally (daemon install + UDP/69 firewall).

### Pros

* Minimal moving parts; no credentials beyond filesystem permissions.
* Immediate processing once files land.

### Cons

* No transport encryption.
* Careful permissioning required on the incoming directory.

### Security

* Restrict directory permissions and ownership.
* If using TFTP, bind to a management interface and firewall source IPs.

## Secure Copy (SCP)

### Description

* PyPNM pulls files via `scp` from a remote host.

### Setup Complexity

* Moderate: SSH key setup, authorized_keys, and host key management.

### Pros

* Encrypted; widely available.
* No additional server software beyond OpenSSH.

### Cons

* No native resume.
* Coarse-grained error reporting compared to SFTP.

### Security

* Prefer key-based auth with a restricted account.
* Limit SSH exposure (firewall to known IPs, command restrictions in `authorized_keys`).

## Secure File Transfer Protocol (SFTP)

### Description

* PyPNM uses SSH/SFTP (e.g., Paramiko) to list, fetch, and resume file transfers.

### Setup Complexity

* Moderate: same SSH prerequisites as SCP.

### Pros

* Resume support; directory listing and existence checks.
* Encrypted and single port (22).

### Cons

* Requires a Python SFTP library on the PyPNM host.

### Security

* Same best practices as SCP; consider `ForceCommand internal-sftp` and chroot.

## FTP with TLS (FTPS)

### Description

* PyPNM pulls from TLS-enabled FTP servers.

### Setup Complexity

* Moderate–High: server certificate, passive port range, firewall/NAT.

### Pros

* Common in legacy environments; encrypted control/data channels when enforced.

### Cons

* Firewall complexity (port 21 plus passive range).
* Certificate lifecycle management.

### Security

* Enforce TLS on login and data (`PROT P`).
* Chroot and least-privilege accounts; restrict passive port range.

## Trivial File Transfer Protocol (TFTP)

### Description

* CMs natively upload PNM files via TFTP to a configured server.
* Unauthenticated, UDP-based, and simple.

### Setup Complexity

* Moderate: daemon install, writable root, firewall for UDP/69 and ephemeral data ports.

### Pros

* Native to CM/CMTS workflows; minimal overhead.

### Cons

* No authentication or encryption.
* Less reliable over lossy links; risk of overwrites if naming isn’t unique.

### Security

* Bind to a management VLAN/interface.
* Strict ACLs on UDP/69; chroot the TFTP root; monitor and purge unexpected files.

## Summary Comparison

| Method              | Encryption | Authentication    | Setup Complexity | Resume/Listing | Typical Ports          |
| ------------------- | ---------- | ----------------- | ---------------- | -------------- | ---------------------- |
| Local Transfer      | None       | Filesystem perms  | Low              | N/A            | N/A                    |
| SCP                 | SSH        | Keys/Passwords    | Moderate         | No             | TCP 22                 |
| SFTP                | SSH        | Keys/Passwords    | Moderate         | Yes            | TCP 22                 |
| FTP with TLS (FTPS) | TLS        | Username/Password | Moderate–High    | Partial        | TCP 21 + passive range |
| TFTP                | None       | None              | Moderate         | No             | UDP 69 + ephemeral     |

**Recommendation:** For production, SFTP typically offers the best blend of security, reliability, and operational control. Use TFTP where required by CM workflows, but confine it to trusted segments and monitor closely. SCP is fine for simple scripted pulls; FTPS fits environments already standardized on FTP with TLS.
