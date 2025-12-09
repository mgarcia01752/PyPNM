# SCP | SFTP PNM File Retrieval Setup (Config Menu)

This example shows how to configure **SCP** or **SFTP** PNM file retrieval using the
PyPNM System Configuration Menu. The workflow is identical for both methods – the
only difference is whether you select option `3) scp` or `4) sftp`. Whichever you
select becomes the active `PnmFileRetrieval.retrival_method.method` in
`src/pypnm/settings/system.json`.

When you provide a **username/password**, the script will automatically test the
SSH connection and report success or failure. If you also configure a private key
path, the script will display the corresponding **RSA public key** and you must
install it on the remote host following your security procedures (see SOP at the
end of this document).

```bash
source PyPNM/.env/bin/activate
PyPNM$ source PyPNM/.env/bin/activate
(.env) PyPNM$ config-menu

PyPNM System Configuration Menu
================================
Select an option:
  1) Edit FastApiRequestDefault
  2) Edit SNMP
  3) Edit PnmBulkDataTransfer
  4) Edit PnmFileRetrieval (retrival_method only)
  5) Edit Logging
  6) Edit TestMode
  7) Run PnmFileRetrieval Setup (directory initialization)
  q) Quit
Enter selection: 7

Running: PyPNM/tools/pnm_file_retrieval_setup.py

INFO PnmFileRetrievalConfigurator: Using configuration file: PyPNM/src/pypnm/settings/system.json
INFO PnmFileRetrievalConfigurator: Created backup: PyPNM/src/pypnm/settings/system.bak.1765156354.json

Select PNM File Retrieval Method:
  1) local  - Copy from local src_dir
  2) tftp   - Download from TFTP server
  3) scp    - Download from SCP server
  4) sftp   - Download from SFTP server
  q) Quit   - Exit without changes

Enter choice [1-4 or q to quit]: 3
INFO PnmFileRetrievalConfigurator: Selected retrieval method: scp

Configure SCP PNM File Retrieval:
Enter SSH host [localhost]: 
Enter SSH port for localhost [22]: 
Enter SSH username [user]: dev01

Authentication Options:
  You may configure password, private key, or both.
  At least one of them must be provided.

Configure password authentication? [y/N]: y
Configure private key authentication? [y/N]: y
Enter SSH password (leave blank to clear): 
Enter private key path [~/.ssh/id_rsa_pypnm]: 
INFO PnmFileRetrievalConfigurator: Testing SCP connection to dev01@localhost:22 ...
INFO PnmFileRetrievalConfigurator: SSH connection test succeeded.
INFO PnmFileRetrievalConfigurator: PNM file retrieval configuration complete.

======================================================================
 SCP Public Key (Add To Your PNM File Server)
======================================================================
ssh-rsa <RSA-KEY> dev01@dev01

Add this key to the remote users ~/.ssh/authorized_keys on the host(s)
you configured for scp file retrieval.
======================================================================


Script completed successfully.


PyPNM System Configuration Menu
================================
Select an option:
  1) Edit FastApiRequestDefault
  2) Edit SNMP
  3) Edit PnmBulkDataTransfer
  4) Edit PnmFileRetrieval (retrival_method only)
  5) Edit Logging
  6) Edit TestMode
  7) Run PnmFileRetrieval Setup (directory initialization)
  q) Quit
Enter selection: q
Exiting System Configuration Menu.
(.env) PyPNM$ 
```

## Notes On SCP vs SFTP Behavior

- The **menu flow is identical** for `scp` and `sftp`; the script just writes different
  configuration keys under:

  - `PnmFileRetrieval.retrival_method.methods.scp.*`
  - `PnmFileRetrieval.retrival_method.methods.sftp.*`

- Whichever method you select (SCP or SFTP) becomes the **active** retrieval method via:

  - `PnmFileRetrieval.retrival_method.method = "scp"`  
    or  
  - `PnmFileRetrieval.retrival_method.method = "sftp"`

- For both SCP and SFTP, the configured `remote_dir` is the directory on the PNM file
  server where the modem writes PNM files and where PyPNM will retrieve them from
  (for example, `/srv/tftp`).

## Authentication & Connection Testing

When you enable **password authentication**:

- The script will immediately attempt an SSH connection using the supplied:
  - host
  - port
  - username
  - password
- The result is logged clearly:
  - On success: `SSH connection test succeeded.`  
  - On failure: a descriptive error message is printed and you can re-run the setup.

When you enable **private key authentication**:

- The script expects a path to a private key (default: `~/.ssh/id_rsa_pypnm`).  
- If the key does not exist, it may be created by your own standard process or via
  `ssh-keygen` outside of PyPNM.  
- After configuration, the script will display the **public key** that corresponds
  to the configured private key so you can install it on the remote server.

You may configure **both** password and private key. At least one must be provided.
In most production environments, key-based authentication is preferred; passwords
are primarily for initial testing or lab-only setups.

## SOP: Installing The PyPNM Public Key On The Remote PNM File Server (Ubuntu/OpenSSH)

The following standard operating procedure applies to both SCP and SFTP, since both
use the same underlying SSH server and account permissions.

1. **Log Into The Remote PNM File Server**  
   Use a privileged account (for example, via SSH or console) to access the host
   where PNM files are stored (for example `/srv/tftp`).

2. **Identify The Target User Account**  
   Decide which user will own the SSH session for file retrieval, for example:
   - `dev01`
   - `pypnm`
   - `tftp-user`  
   This must match the **username** you configured in the PyPNM setup script.

3. **Create The .ssh Directory (If Needed)**  

   ```bash
   sudo -u <remote-user> mkdir -p /home/<remote-user>/.ssh
   sudo -u <remote-user> chmod 700 /home/<remote-user>/.ssh
   ```

4. **Append The PyPNM Public Key To authorized_keys**  

   Take the `ssh-rsa ...` line printed by the PyPNM setup script and append it to
   the remote user's `authorized_keys` file:

   ```bash
   sudo -u <remote-user> bash -c 'echo "ssh-rsa <RSA-KEY> dev01@dev01" >> /home/<remote-user>/.ssh/authorized_keys'
   sudo -u <remote-user> chmod 600 /home/<remote-user>/.ssh/authorized_keys
   ```

   Replace `<RSA-KEY>` and `dev01@dev01` with the literal values printed by the
   configurator, and `<remote-user>` with your chosen account.

5. **Verify Ownership And Permissions**  

   ```bash
   ls -ld /home/<remote-user>/.ssh
   ls -l /home/<remote-user>/.ssh/authorized_keys
   ```

   Ensure the directory and files are owned by `<remote-user>` and have secure
   permissions (`700` for `.ssh`, `600` for `authorized_keys`).

6. **Confirm SSH Access Using The PyPNM Key (Optional But Recommended)**  

   From the PyPNM host, run:

   ```bash
   ssh -i ~/.ssh/id_rsa_pypnm <remote-user>@<remote-host>
   ```

   If the login succeeds without prompting for a password (or only asks on first
   use to accept the host key), then key-based authentication is correctly
   configured for both SCP and SFTP retrieval.

7. **Re-run Or Test PyPNM Retrieval**  

   After the key is installed and verified, re-run your PNM capture flow in PyPNM.
   The SCP/SFTP method should now be able to pull PNM files from the configured
   `remote_dir` without interactive prompts.
