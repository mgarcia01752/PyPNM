import enum
import os
import subprocess
import shlex
import logging
import paramiko
from typing import Optional, Tuple, List


class SecureTransferMode(enum.Enum):
    SCP = 0
    SFTP = 1


class SSHConnector:
    """
    A class to handle SSH/SFTP or SCP file transfers and key exchange between hosts.

    Features:
    - Send and receive files via SFTP or SCP (configurable)
    - SSH key generation and exchange
    - Support for password and key-based authentication, with agent/default-key fallback
    - Automatic host key verification options
    """

    def __init__(
        self,
        hostname: str,
        username: str,
        port: int = 22,
        transfer_mode: SecureTransferMode = SecureTransferMode.SCP
    ):
        """
        Initialize SSH connection parameters.

        Args:
            hostname: Remote host IP or hostname.
            username: Username for SSH connection.
            port: SSH port (default 22).
            transfer_mode: SecureTransferMode.SCP or SecureTransferMode.SFTP.
        """
        self.logger = logging.getLogger(__name__)
        self.hostname = hostname
        self.username = username
        self.port = port

        if not isinstance(transfer_mode, SecureTransferMode):
            raise ValueError("transfer_mode must be a SecureTransferMode enum")
        self.transfer_mode = transfer_mode

        self.ssh_client: Optional[paramiko.SSHClient] = None
        self.sftp_client: Optional[paramiko.SFTPClient] = None
        self.private_key_path: Optional[str] = None
        self.password: Optional[str] = None

    def connect(
        self,
        password: Optional[str] = None,
        private_key_path: Optional[str] = None,
        auto_add_policy: bool = True
    ) -> bool:
        """
        Establish SSH connection (Paramiko) for SFTP or to prepare for SCP.

        Args:
            password: Password for authentication.
            private_key_path: Path to private key file.
            auto_add_policy: If True, automatically accept unknown host keys.

        Returns:
            bool: True if connection successful.
        """
        self.password = password
        self.private_key_path = private_key_path

        try:
            # Even for SCP, establish a Paramiko connection to verify credentials
            self.ssh_client = paramiko.SSHClient()
            self.ssh_client.load_system_host_keys()

            if auto_add_policy:
                self.ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            else:
                self.ssh_client.set_missing_host_key_policy(paramiko.RejectPolicy())

            if private_key_path and os.path.exists(private_key_path):
                pkey = paramiko.RSAKey.from_private_key_file(private_key_path)
                self.ssh_client.connect(
                    hostname=self.hostname,
                    port=self.port,
                    username=self.username,
                    pkey=pkey,
                    timeout=10,
                )
            elif password:
                self.ssh_client.connect(
                    hostname=self.hostname,
                    port=self.port,
                    username=self.username,
                    password=password,
                    timeout=10,
                )
            else:
                # Fallback to SSH agent or default key files (~/.ssh/id_rsa, etc.)
                self.ssh_client.connect(
                    hostname=self.hostname,
                    port=self.port,
                    username=self.username,
                    timeout=10,
                )

            if self.transfer_mode == SecureTransferMode.SFTP:
                transport = self.ssh_client.get_transport()
                if transport is None or not transport.is_active():
                    raise RuntimeError("SSH transport is not active after connect()")
                self.sftp_client = paramiko.SFTPClient.from_transport(transport)

            self.logger.debug(f"Connected to {self.hostname}:{self.port} via {self.transfer_mode.name}")
            return True

        except Exception as e:
            self.logger.error(f"Connection failed: {e}")
            return False

    def disconnect(self):
        """Close SFTP (if open) and SSH connections."""
        if self.sftp_client:
            try:
                self.sftp_client.close()
            except Exception:
                pass
        if self.ssh_client:
            try:
                self.ssh_client.close()
            except Exception:
                pass
        self.logger.debug("Disconnected")

    def send_file(self, local_path: str, remote_path: str) -> bool:
        """
        Send a file to the remote host, using either SFTP or SCP.

        Args:
            local_path: Path to the local file.
            remote_path: Full path on the remote host (including filename).

        Returns:
            bool: True if transfer successful.
        """
        if not self.ssh_client:
            raise ConnectionError("Not connected. Call connect() first.")

        if not os.path.isfile(local_path):
            self.logger.error(f"Local file not found: {local_path}")
            return False

        if self.transfer_mode == SecureTransferMode.SFTP:
            if not self.sftp_client:
                raise ConnectionError("SFTP client not initialized. Did you call connect()?")

            try:
                remote_dir = os.path.dirname(remote_path)
                if remote_dir:
                    self._ensure_remote_dir(remote_dir)

                self.sftp_client.put(local_path, remote_path)
                self.logger.debug(f"SFTP: Sent {local_path} -> {remote_path}")
                return True

            except Exception as e:
                self.logger.error(f"SFTP send failed: {e}")
                return False

        else:  # SCP
            try:
                remote_dir = os.path.dirname(remote_path)
                if remote_dir:
                    mkdir_cmd = f'mkdir -p "{remote_dir}"'
                    _, stderr, code = self.execute_command(mkdir_cmd)
                    if code != 0:
                        self.logger.error(f"Remote mkdir failed: {stderr.strip()}")

                scp_cmd = self._build_scp_command(
                    local_src=local_path,
                    remote_dest=f"{self.username}@{self.hostname}:{remote_path}"
                )
                self.logger.debug(f"SCP send cmd: {scp_cmd}")
                result = subprocess.run(shlex.split(scp_cmd), capture_output=True)
                if result.returncode != 0:
                    self.logger.error(f"SCP send failed: {result.stderr.decode().strip()}")
                    return False

                self.logger.debug(f"SCP: Sent {local_path} -> {remote_path}")
                return True

            except Exception as e:
                self.logger.error(f"SCP send exception: {e}")
                return False

    def receive_file(self, remote_path: str, local_path: str) -> bool:
        """
        Receive a file from the remote host, using either SFTP or SCP.

        Args:
            remote_path: Full path on the remote host (including filename).
            local_path: Local destination (directory or full file path).

        Returns:
            bool: True if transfer successful.
        """
        if not self.ssh_client:
            raise ConnectionError("Not connected. Call connect() first.")

        # Determine final local file path
        if os.path.isdir(local_path):
            remote_filename = os.path.basename(remote_path)
            local_file_path = os.path.join(local_path, remote_filename)
        else:
            local_file_path = local_path

        local_dir = os.path.dirname(local_file_path)
        if local_dir:
            os.makedirs(local_dir, exist_ok=True)

        if self.transfer_mode == SecureTransferMode.SFTP:
            if not self.sftp_client:
                raise ConnectionError("SFTP client not initialized. Did you call connect()?")

            try:
                self.sftp_client.get(remote_path, local_file_path)
                self.logger.debug(f"SFTP: Received {remote_path} -> {local_file_path}")
                return True

            except Exception as e:
                self.logger.error(f"SFTP receive failed: {e}")
                return False

        else:  # SCP
            try:
                scp_cmd = self._build_scp_command(
                    remote_src=f"{self.username}@{self.hostname}:{remote_path}",
                    local_dest=local_file_path
                )
                self.logger.debug(f"SCP receive cmd: {scp_cmd}")
                result = subprocess.run(shlex.split(scp_cmd), capture_output=True)
                if result.returncode != 0:
                    self.logger.error(f"SCP receive failed: {result.stderr.decode().strip()}")
                    return False

                self.logger.debug(f"SCP: Received {remote_path} -> {local_file_path}")
                return True

            except Exception as e:
                self.logger.error(f"SCP receive exception: {e}")
                return False

    def _build_scp_command(
        self,
        local_src: Optional[str] = None,
        remote_src: Optional[str] = None,
        remote_dest: Optional[str] = None,
        local_dest: Optional[str] = None
    ) -> str:
        """
        Construct an scp command string based on provided source/destination.

        Args:
            local_src: Local path to send.
            remote_src: Remote path to fetch (username@host:/path).
            remote_dest: Remote destination path (username@host:/path).
            local_dest: Local destination path.

        Returns:
            str: A fully formed scp command.
        """
        if local_src and remote_dest:
            src = local_src
            dest = remote_dest
        elif remote_src and local_dest:
            src = remote_src
            dest = local_dest
        else:
            raise ValueError("Provide either (local_src and remote_dest) or (remote_src and local_dest).")

        parts = ["scp", "-o", "StrictHostKeyChecking=no", "-P", str(self.port)]

        if self.private_key_path:
            parts += ["-i", shlex.quote(self.private_key_path)]
        elif self.password:
            parts = [
                "sshpass", "-p", shlex.quote(self.password),
                "scp", "-o", "StrictHostKeyChecking=no", "-P", str(self.port)
            ]

        parts += [shlex.quote(src), shlex.quote(dest)]
        return " ".join(parts)

    def execute_command(self, command: str) -> Tuple[str, str, int]:
        """
        Execute a shell command on the remote host.

        Args:
            command: Command to execute (e.g., "ls -la /tmp").

        Returns:
            tuple: (stdout, stderr, exit_code)
        """
        if not self.ssh_client:
            raise ConnectionError("Not connected. Call connect() first.")

        try:
            stdin, stdout, stderr = self.ssh_client.exec_command(command)
            exit_code = stdout.channel.recv_exit_status()
            stdout_data = stdout.read().decode()
            stderr_data = stderr.read().decode()
            return stdout_data, stderr_data, exit_code

        except Exception as e:
            self.logger.error(f"Command execution failed: {e}")
            return "", str(e), -1

    @staticmethod
    def generate_ssh_key_pair(
        key_path: str = "~/.ssh/id_rsa",
        key_size: int = 2048
    ) -> bool:
        """
        Generate an SSH key pair (RSA) locally.

        Args:
            key_path: Path for private key (public key will be key_path + ".pub").
            key_size: Key size in bits (e.g., 2048, 4096).

        Returns:
            bool: True if generation successful.
        """
        try:
            key_path = os.path.expanduser(key_path)
            ssh_dir = os.path.dirname(key_path)
            os.makedirs(ssh_dir, exist_ok=True)
            os.chmod(ssh_dir, 0o700)

            key = paramiko.RSAKey.generate(bits=key_size)
            key.write_private_key_file(key_path)
            os.chmod(key_path, 0o600)

            pub_key_path = f"{key_path}.pub"
            with open(pub_key_path, "w") as f:
                f.write(f"ssh-rsa {key.get_base64()} {os.getenv('USER', 'unknown')}@{os.uname().nodename}\n")
            os.chmod(pub_key_path, 0o644)

            logging.getLogger(__name__).debug(f"SSH key pair generated: {key_path}")
            return True

        except Exception as e:
            logging.getLogger(__name__).error(f"Key generation failed: {e}")
            return False

    def install_public_key(self, public_key_path: str) -> bool:
        """
        Install a public key into the remote host's ~/.ssh/authorized_keys, if not already present.

        Args:
            public_key_path: Local path to the public key file.

        Returns:
            bool: True if installation successful or key already exists.
        """
        if not self.ssh_client:
            raise ConnectionError("Not connected. Call connect() first.")

        try:
            if not os.path.exists(public_key_path):
                raise FileNotFoundError(f"Public key not found: {public_key_path}")

            with open(public_key_path, "r") as f:
                public_key = f.read().strip()

            self.execute_command("mkdir -p ~/.ssh && chmod 700 ~/.ssh")

            check_cmd = (
                f'grep -qxF "{public_key}" ~/.ssh/authorized_keys '
                f'|| echo "{public_key}" >> ~/.ssh/authorized_keys && chmod 600 ~/.ssh/authorized_keys'
            )
            stdout, stderr, exit_code = self.execute_command(check_cmd)

            if exit_code == 0:
                self.logger.debug("Public key installed (or already present) on remote host.")
                return True
            else:
                self.logger.error(f"Key installation command failed: {stderr}")
                return False

        except Exception as e:
            self.logger.error(f"Key installation failed: {e}")
            return False

    def list_remote_directory(self, remote_path: str = ".") -> List[str]:
        """
        List files in a remote directory via SFTP.

        Args:
            remote_path: Remote directory path.

        Returns:
            list[str]: List of filenames (empty list on failure).
        """
        if self.transfer_mode != SecureTransferMode.SFTP:
            raise RuntimeError("Directory listing requires SFTP mode")

        if not self.ssh_client or not self.sftp_client:
            raise ConnectionError("Not connected. Call connect() first.")

        try:
            return self.sftp_client.listdir(remote_path)
        except Exception as e:
            self.logger.error(f"Directory listing failed: {e}")
            return []

    def _ensure_remote_dir(self, remote_directory: str):
        """
        Create nested directories on the remote host via SFTP (mkdir -p style).

        Args:
            remote_directory: Absolute remote directory path.

        Raises:
            ConnectionError if not connected or IOError if creation fails.
        """
        if not self.ssh_client or not self.sftp_client:
            raise ConnectionError("Not connected. Call connect() first.")

        parts = remote_directory.strip("/").split("/")
        path_so_far = ""
        for part in parts:
            path_so_far = f"{path_so_far}/{part}"
            try:
                self.sftp_client.stat(path_so_far)
            except IOError:
                self.sftp_client.mkdir(path_so_far)
