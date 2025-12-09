# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia

from __future__ import annotations

import contextlib
import enum
import logging
import os
import shutil
import subprocess

import paramiko


class SecureTransferMode(enum.Enum):
    """Supported secure file transfer modes."""
    SCP = 0
    SFTP = 1


class SSHConnector:
    """
    Handles secure file transfers (SFTP/SCP) and SSH key management.

    Features:
      - Password or key-based authentication
      - SFTP transfers via Paramiko
      - SCP fallback using system scp or sshpass if available
      - SSH key pair generation and remote installation
      - Remote command execution
    """

    def __init__(
        self,
        hostname: str,
        username: str,
        port: int = 22,
        transfer_mode: SecureTransferMode = SecureTransferMode.SCP,
    ) -> None:
        """
        Initialize connection parameters.

        Args:
            hostname: Host or IP of the remote machine.
            username: SSH login user.
            port: SSH port, default 22.
            transfer_mode: SCP or SFTP mode.
        """
        self.logger = logging.getLogger(__name__)
        self.hostname = hostname
        self.username = username
        self.port = port
        if not isinstance(transfer_mode, SecureTransferMode):
            raise ValueError("transfer_mode must be a SecureTransferMode enum")
        self.transfer_mode = transfer_mode
        self.ssh_client: paramiko.SSHClient | None = None
        self.sftp_client: paramiko.SFTPClient | None = None
        self.private_key_path: str | None = None
        self.password: str | None = None

    def connect(
        self,
        password: str | None = None,
        private_key_path: str | None = None,
        auto_add_policy: bool = True,
    ) -> bool:
        """
        Establish SSH session for SFTP or to enable SCP fallback.

        Always initializes an SFTP client for fallback, regardless of mode.

        Args:
            password: Optional SSH password.
            private_key_path: Path to a private key file.
            auto_add_policy: If True, unknown host keys are accepted.

        Returns:
            True on success, False otherwise.
        """
        self.password         = password
        self.private_key_path = private_key_path
        try:
            client = paramiko.SSHClient()
            client.load_system_host_keys()
            policy = paramiko.AutoAddPolicy() if auto_add_policy else paramiko.RejectPolicy()
            client.set_missing_host_key_policy(policy)
            connect_kwargs = dict(
                hostname = self.hostname,
                port     = self.port,
                username = self.username,
                timeout  = 10,
            )
            if private_key_path:
                key_path = os.path.expanduser(private_key_path)
                if os.path.exists(key_path):
                    key = paramiko.RSAKey.from_private_key_file(key_path)
                    connect_kwargs["pkey"] = key                                    # type: ignore
                else:
                    self.logger.error("Private key file not found: %s", key_path)
            if password:
                connect_kwargs["password"] = password
            client.connect(**connect_kwargs)                                        # type: ignore
            self.ssh_client = client

            transport = client.get_transport()
            if transport and transport.is_active():
                self.sftp_client = paramiko.SFTPClient.from_transport(transport)

            self.logger.debug(f"Connected to {self.hostname}:{self.port} via {self.transfer_mode.name}")
            return True
        except Exception as e:
            self.logger.error(f"Connection failed: {e}")
            return False

    def disconnect(self) -> None:
        """Close any active SFTP and SSH sessions."""
        if self.sftp_client:
            with contextlib.suppress(Exception):
                self.sftp_client.close()
        if self.ssh_client:
            with contextlib.suppress(Exception):
                self.ssh_client.close()
        self.logger.debug("Disconnected from remote host")

    def send_file(self, local_path: str, remote_path: str) -> bool:
        """
        Transfer a local file to the remote host.

        Uses SFTP if configured; otherwise attempts SCP via system,
        with SFTP fallback if SCP is unavailable.
        """
        if not self.ssh_client:
            raise ConnectionError("Not connected - call connect() first")
        if not os.path.isfile(local_path):
            self.logger.error(f"Local file not found: {local_path}")
            return False

        # SFTP primary when requested
        if self.transfer_mode is SecureTransferMode.SFTP and self.sftp_client:
            try:
                self._ensure_remote_dir(os.path.dirname(remote_path))
                self.sftp_client.put(local_path, remote_path)
                self.logger.debug(f"SFTP: {local_path} -> {remote_path}")
                return True
            except Exception as e:
                self.logger.error(f"SFTP send failed: {e}")
                return False

        # SCP fallback
        cmd = self._build_scp_command(local_src=local_path, remote_dest=f"{self.username}@{self.hostname}:{remote_path}")
        if cmd:
            try:
                result = subprocess.run(cmd, capture_output=True)
                if result.returncode != 0:
                    self.logger.error(result.stderr.decode().strip())
                else:
                    self.logger.debug(f"SCP: {local_path} -> {remote_path}")
                    return True
            except FileNotFoundError:
                self.logger.warning("scp or sshpass not found; using SFTP fallback")

        # SFTP fallback
        if self.sftp_client:
            try:
                self._ensure_remote_dir(os.path.dirname(remote_path))
                self.sftp_client.put(local_path, remote_path)
                self.logger.debug(f"Fallback SFTP: {local_path} -> {remote_path}")
                return True
            except Exception as e:
                self.logger.error(f"Fallback SFTP send failed: {e}")

        self.logger.error("No transfer method available for send_file")
        return False

    def receive_file(self, remote_path: str, local_path: str) -> bool:
        """
        Fetch a remote file to the local filesystem.

        Uses SFTP if configured; otherwise attempts SCP via system,
        with SFTP fallback if SCP is unavailable.
        """
        if not self.ssh_client:
            raise ConnectionError("Not connected - call connect() first")

        # Determine local file path
        if os.path.isdir(local_path):
            fname = os.path.basename(remote_path)
            local_file = os.path.join(local_path, fname)
        else:
            local_file = local_path
        os.makedirs(os.path.dirname(local_file), exist_ok=True)

        # SFTP primary when requested
        if self.transfer_mode is SecureTransferMode.SFTP and self.sftp_client:
            try:
                self.sftp_client.get(remote_path, local_file)
                self.logger.debug(f"SFTP: {remote_path} -> {local_file}")
                return True
            except Exception as e:
                self.logger.error(f"SFTP receive failed: {e}")
                return False

        # SCP fallback
        cmd = self._build_scp_command(remote_src=f"{self.username}@{self.hostname}:{remote_path}", local_dest=local_file)
        if cmd:
            try:
                result = subprocess.run(cmd, capture_output=True)
                if result.returncode != 0:
                    self.logger.error(result.stderr.decode().strip())
                else:
                    self.logger.debug(f"SCP: {remote_path} -> {local_file}")
                    return True
            except FileNotFoundError:
                self.logger.warning("scp or sshpass not found; using SFTP fallback")

        # SFTP fallback
        if self.sftp_client:
            try:
                self.sftp_client.get(remote_path, local_file)
                self.logger.debug(f"Fallback SFTP: {remote_path} -> {local_file}")
                return True
            except Exception as e:
                self.logger.error(f"Fallback SFTP receive failed: {e}")

        self.logger.error("No transfer method available for receive_file")
        return False

    def _build_scp_command(
        self,
        local_src: str | None = None,
        remote_src: str | None = None,
        remote_dest: str | None = None,
        local_dest: str | None = None,
    ) -> list[str] | None:
        """
        Constructs a safe SCP command list or returns None if unavailable.
        """
        if local_src and remote_dest:
            src, dest = local_src, remote_dest
        elif remote_src and local_dest:
            src, dest = remote_src, local_dest
        else:
            raise ValueError("Provide either (local_src and remote_dest) or (remote_src and local_dest)")
        parts: list[str] = []
        if self.private_key_path:
            parts = ["scp", "-o", "StrictHostKeyChecking=no", "-i", self.private_key_path, "-P", str(self.port)]
        elif self.password and shutil.which("sshpass"):
            parts = ["sshpass", "-p", self.password, "scp", "-o", "StrictHostKeyChecking=no", "-P", str(self.port)]
        else:
            return None
        parts += [src, dest]
        return parts

    def execute_command(self, command: str) -> tuple[str, str, int]:
        """
        Runs a remote shell command via Paramiko.
        """
        if not self.ssh_client:
            raise ConnectionError("Not connected - call connect() first")
        try:
            stdin, stdout, stderr = self.ssh_client.exec_command(command)
            code = stdout.channel.recv_exit_status()
            out = stdout.read().decode()
            err = stderr.read().decode()
            return out, err, code
        except Exception as e:
            self.logger.error(f"Command failed: {e}")
            return "", str(e), -1

    @staticmethod
    def generate_ssh_key_pair(key_path: str = "~/.ssh/id_rsa", key_size: int = 2048) -> bool:
        """
        Generates an RSA key pair locally.
        """
        try:
            path = os.path.expanduser(key_path)
            os.makedirs(os.path.dirname(path), exist_ok=True)
            key = paramiko.RSAKey.generate(bits=key_size)
            key.write_private_key_file(path)
            pub = f"{path}.pub"
            with open(pub, "w") as f:
                f.write(f"ssh-rsa {key.get_base64()} {os.getenv('USER')}@{os.uname().nodename}\n")
            return True
        except Exception as e:
            logging.getLogger(__name__).error(f"Key gen failed: {e}")
            return False

    def install_public_key(self, public_key_path: str) -> bool:
        """
        Installs a public key in remote ~/.ssh/authorized_keys.
        """
        if not self.ssh_client:
            raise ConnectionError("Not connected - call connect() first")
        if not os.path.isfile(public_key_path):
            raise FileNotFoundError(f"Public key not found: {public_key_path}")
        with open(public_key_path) as f:
            key = f.read().strip()
        cmd = (
            f'grep -qxF "{key}" ~/.ssh/authorized_keys || '
            f'echo "{key}" >> ~/.ssh/authorized_keys'
        )
        out, err, code = self.execute_command(cmd)
        if code == 0:
            self.logger.debug("Public key installed or already present")
            return True
        self.logger.error(f"Key install failed: {err}")
        return False

    def list_remote_directory(self, remote_path: str = ".") -> list[str]:
        """
        Lists a directory via SFTP.
        """
        if not self.sftp_client:
            raise ConnectionError("Not connected - call connect() first")
        try:
            return self.sftp_client.listdir(remote_path)
        except Exception as e:
            self.logger.error(f"Listing failed: {e}")
            return []

    def _ensure_remote_dir(self, remote_dir: str) -> None:
        """
        Recursively creates remote directories via SFTP.
        """
        if not self.sftp_client:
            raise ConnectionError("Not connected - call connect() first")
        parts = remote_dir.strip("/").split("/")
        path = ""
        for part in parts:
            path += f"/{part}"
            try:
                self.sftp_client.stat(path)
            except OSError:
                self.sftp_client.mkdir(path)
