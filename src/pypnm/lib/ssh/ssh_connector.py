# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia

from __future__ import annotations

import contextlib
import enum
import logging
import os

import paramiko

from pypnm.lib.secret_crypto_manager import SecretCryptoError, SecretCryptoManager


class SecureTransferMode(enum.Enum):
    """
    Supported Secure File Transfer Modes.

    Attributes
    ----------
    SCP:
        Secure copy protocol via SSH.
    SFTP:
        SSH file transfer protocol.
    """

    SCP  = 0
    SFTP = 1


class SSHConnector:
    """
    SSH Connector For Secure File Transfer And Remote Commands.

    This connector supports both SFTP (Paramiko) and SCP (Python SCP client
    over Paramiko transport). Passwords may be provided as encrypted tokens
    (ENC[v1]:...) and are decrypted only inside connect().

    Security Notes
    --------------
    - Encrypted password tokens may be stored in configuration.
    - Decryption happens only at connect time.
    - Plaintext password is not stored on the instance.
    """

    DEFAULT_SSH_PORT: int                = 22
    DEFAULT_CONNECT_TIMEOUT_SEC: int     = 10
    DEFAULT_RSA_KEY_BITS: int            = 2048

    ENCRYPTED_TOKEN_PREFIX: str          = "ENC["

    def __init__(
        self,
        hostname: str,
        username: str,
        port: int = DEFAULT_SSH_PORT,
        transfer_mode: SecureTransferMode = SecureTransferMode.SFTP,
    ) -> None:
        """
        Initialize Connection Parameters.

        Parameters
        ----------
        hostname:
            Hostname or IP address of the remote machine.
        username:
            SSH login username.
        port:
            SSH port (default: 22).
        transfer_mode:
            Transfer mode (SCP or SFTP).
        """
        self.logger = logging.getLogger(f"{self.__class__.__name__}")

        self.hostname      = hostname
        self.username      = username
        self.port          = int(port)
        self.transfer_mode = transfer_mode

        self.ssh_client: paramiko.SSHClient | None  = None
        self.sftp_client: paramiko.SFTPClient | None = None

        self.private_key_path: str = ""
        self.password_enc: str     = ""

    def connect(
        self,
        password_enc: str = "",
        private_key_path: str = "",
        auto_add_policy: bool = True,
    ) -> bool:
        """
        Establish An SSH Session And Initialize Transfer Clients.

        Parameters
        ----------
        password_enc:
            Encrypted password token (ENC[v1]:...) or plaintext password for
            backward compatibility. The plaintext password is not stored.
        private_key_path:
            Private key path for key-based authentication. Empty disables key auth.
        auto_add_policy:
            If True, unknown host keys are accepted.

        Returns
        -------
        bool
            True on success, False on failure.
        """
        self.password_enc     = password_enc.strip()
        self.private_key_path = private_key_path.strip()

        password_clear = ""
        if self.password_enc != "":
            if self.password_enc.startswith(self.ENCRYPTED_TOKEN_PREFIX):
                try:
                    password_clear = SecretCryptoManager.decrypt_password(self.password_enc)
                except SecretCryptoError as exc:
                    self.logger.error("Failed to decrypt password token: %s", exc)
                    return False
            else:
                password_clear = self.password_enc

        try:
            client = paramiko.SSHClient()
            client.load_system_host_keys()
            policy = paramiko.AutoAddPolicy() if auto_add_policy else paramiko.RejectPolicy()
            client.set_missing_host_key_policy(policy)

            connect_kwargs: dict[str, object] = {
                "hostname": self.hostname,
                "port":     self.port,
                "username": self.username,
                "timeout":  float(self.DEFAULT_CONNECT_TIMEOUT_SEC),
            }

            key_filename = ""
            if self.private_key_path != "":
                key_filename = os.path.expanduser(self.private_key_path)
                connect_kwargs["key_filename"] = key_filename

            if password_clear != "":
                connect_kwargs["password"] = password_clear

            client.connect(**connect_kwargs)  # type: ignore[arg-type]
            self.ssh_client = client

            transport = client.get_transport()
            if transport is None or not transport.is_active():
                self.logger.error("SSH transport is not active after connect().")
                self.disconnect()
                return False

            self.sftp_client = paramiko.SFTPClient.from_transport(transport)

            self.logger.debug("Connected to %s:%d via %s", self.hostname, self.port, self.transfer_mode.name)
            return True

        except Exception as exc:
            self.logger.error("Connection failed: %s", exc)
            self.disconnect()
            return False

        finally:
            password_clear = ""

    def disconnect(self) -> None:
        """
        Close Any Active SFTP And SSH Sessions.
        """
        if self.sftp_client is not None:
            with contextlib.suppress(Exception):
                self.sftp_client.close()
            self.sftp_client = None

        if self.ssh_client is not None:
            with contextlib.suppress(Exception):
                self.ssh_client.close()
            self.ssh_client = None

        self.logger.debug("Disconnected from remote host")

    def send_file(self, local_path: str, remote_path: str) -> bool:
        """
        Transfer A Local File To The Remote Host.

        Parameters
        ----------
        local_path:
            Local path to the file to send.
        remote_path:
            Remote destination path.

        Returns
        -------
        bool
            True on success, False on failure.
        """
        if self.ssh_client is None:
            raise ConnectionError("Not connected - call connect() first")

        if not os.path.isfile(local_path):
            self.logger.error("Local file not found: %s", local_path)
            return False

        remote_dir = os.path.dirname(remote_path)
        if remote_dir != "":
            self._ensure_remote_dir(remote_dir)

        if self.transfer_mode is SecureTransferMode.SFTP:
            return self._sftp_put(local_path=local_path, remote_path=remote_path)

        return self._scp_put(local_path=local_path, remote_path=remote_path)

    def receive_file(self, remote_path: str, local_path: str) -> bool:
        """
        Fetch A Remote File To The Local Filesystem.

        Parameters
        ----------
        remote_path:
            Remote path of the file to retrieve.
        local_path:
            Local destination path (directory or full file path).

        Returns
        -------
        bool
            True on success, False on failure.
        """
        if self.ssh_client is None:
            raise ConnectionError("Not connected - call connect() first")

        local_file = local_path
        if os.path.isdir(local_path):
            local_file = os.path.join(local_path, os.path.basename(remote_path))

        local_dir = os.path.dirname(local_file)
        if local_dir != "":
            os.makedirs(local_dir, exist_ok=True)

        if self.transfer_mode is SecureTransferMode.SFTP:
            return self._sftp_get(remote_path=remote_path, local_path=local_file)

        return self._scp_get(remote_path=remote_path, local_path=local_file)

    def execute_command(self, command: str) -> tuple[str, str, int]:
        """
        Run A Remote Shell Command Via SSH.

        Parameters
        ----------
        command:
            Shell command to execute.

        Returns
        -------
        tuple[str, str, int]
            (stdout, stderr, exit_code)
        """
        if self.ssh_client is None:
            raise ConnectionError("Not connected - call connect() first")

        try:
            _stdin, stdout, stderr = self.ssh_client.exec_command(command)
            code                  = stdout.channel.recv_exit_status()
            out                   = stdout.read().decode(errors="replace")
            err                   = stderr.read().decode(errors="replace")
            return out, err, int(code)
        except Exception as exc:
            self.logger.error("Command failed: %s", exc)
            return "", str(exc), -1

    def list_remote_directory(self, remote_path: str = ".") -> list[str]:
        """
        List A Remote Directory Via SFTP.

        Parameters
        ----------
        remote_path:
            Remote directory path.

        Returns
        -------
        list[str]
            Directory entry names. Empty list on failure.
        """
        if self.sftp_client is None:
            raise ConnectionError("Not connected - call connect() first")

        try:
            return list(self.sftp_client.listdir(remote_path))
        except Exception as exc:
            self.logger.error("Listing failed: %s", exc)
            return []

    @staticmethod
    def generate_ssh_key_pair(key_path: str = "~/.ssh/id_rsa", key_size: int = DEFAULT_RSA_KEY_BITS) -> bool:
        """
        Generate An RSA Key Pair Locally.

        Parameters
        ----------
        key_path:
            Private key output path.
        key_size:
            RSA key size in bits.

        Returns
        -------
        bool
            True on success, False on failure.
        """
        logger = logging.getLogger("SSHConnector")

        try:
            path = os.path.expanduser(key_path)

            key_dir = os.path.dirname(path)
            if key_dir != "":
                os.makedirs(key_dir, exist_ok=True)

            key = paramiko.RSAKey.generate(bits=int(key_size))
            key.write_private_key_file(path)

            pub_path = f"{path}.pub"
            user     = os.getenv("USER", "user")
            host     = os.uname().nodename

            with open(pub_path, "w", encoding="utf-8") as handle:
                handle.write(f"ssh-rsa {key.get_base64()} {user}@{host}\n")

            return True

        except Exception as exc:
            logger.error("Key gen failed: %s", exc)
            return False

    def install_public_key(self, public_key_path: str) -> bool:
        """
        Install A Public Key Into Remote ~/.ssh/authorized_keys.

        Parameters
        ----------
        public_key_path:
            Local public key file path.

        Returns
        -------
        bool
            True on success, False on failure.
        """
        if self.ssh_client is None:
            raise ConnectionError("Not connected - call connect() first")

        if not os.path.isfile(public_key_path):
            raise FileNotFoundError(f"Public key not found: {public_key_path}")

        with open(public_key_path, "r", encoding="utf-8") as handle:
            key = handle.read().strip()

        cmd = (
            "mkdir -p ~/.ssh && chmod 700 ~/.ssh && "
            f'grep -qxF "{key}" ~/.ssh/authorized_keys || '
            f'echo "{key}" >> ~/.ssh/authorized_keys && '
            "chmod 600 ~/.ssh/authorized_keys"
        )

        _out, err, code = self.execute_command(cmd)
        if code == 0:
            self.logger.debug("Public key installed or already present")
            return True

        self.logger.error("Key install failed: %s", err)
        return False

    def _ensure_remote_dir(self, remote_dir: str) -> None:
        """
        Recursively Create Remote Directories Via SFTP.

        Parameters
        ----------
        remote_dir:
            Remote directory path.
        """
        if self.sftp_client is None:
            raise ConnectionError("Not connected - call connect() first")

        cleaned = remote_dir.strip()
        if cleaned == "" or cleaned == "/":
            return

        parts = cleaned.strip("/").split("/")
        path  = ""

        for part in parts:
            if part == "":
                continue

            path += f"/{part}"
            try:
                self.sftp_client.stat(path)
            except OSError:
                self.sftp_client.mkdir(path)

    def _sftp_put(self, local_path: str, remote_path: str) -> bool:
        if self.sftp_client is None:
            raise ConnectionError("Not connected - call connect() first")

        try:
            self.sftp_client.put(local_path, remote_path)
            self.logger.debug("SFTP: %s -> %s", local_path, remote_path)
            return True
        except Exception as exc:
            self.logger.error("SFTP send failed: %s", exc)
            return False

    def _sftp_get(self, remote_path: str, local_path: str) -> bool:
        if self.sftp_client is None:
            raise ConnectionError("Not connected - call connect() first")

        try:
            self.sftp_client.get(remote_path, local_path)
            self.logger.debug("SFTP: %s -> %s", remote_path, local_path)
            return True
        except Exception as exc:
            self.logger.error("SFTP receive failed: %s", exc)
            return False

    def _scp_put(self, local_path: str, remote_path: str) -> bool:
        try:
            scp = self._scp_client()
            scp.put(local_path, remote_path=remote_path)
            self.logger.debug("SCP: %s -> %s", local_path, remote_path)
            return True
        except Exception as exc:
            self.logger.error("SCP send failed: %s", exc)
            return False

    def _scp_get(self, remote_path: str, local_path: str) -> bool:
        try:
            scp = self._scp_client()
            scp.get(remote_path, local_path=local_path)
            self.logger.debug("SCP: %s -> %s", remote_path, local_path)
            return True
        except Exception as exc:
            self.logger.error("SCP receive failed: %s", exc)
            return False

    def _scp_client(self):
        if self.ssh_client is None:
            raise ConnectionError("Not connected - call connect() first")

        transport = self.ssh_client.get_transport()
        if transport is None or not transport.is_active():
            raise ConnectionError("SSH transport is not active; cannot create SCP client.")

        try:
            from scp import SCPClient  # type: ignore[import-not-found]
        except Exception as exc:
            raise RuntimeError("Missing dependency for SCP. Install with: pip install scp") from exc

        return SCPClient(transport)
