# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia

from enum import Enum
import os
import shutil
import requests
import ftplib
import paramiko
import urllib.parse
from scp import SCPClient
from tftpy import TftpClient
from config.config_manager import ConfigManager

class PnmFileRetrievalMethod(Enum):
    LOCAL = "local"
    TFTP = "tftp"
    FTP = "ftp"
    SCP = "scp"
    SFTP = "sftp"
    HTTP = "http"
    HTTPS = "https"

class PnmRetrivalOperation:
    def __init__(self) -> None:
        # Use ConfigManager to load config if not provided
        self._config = ConfigManager().as_dict()
        
        # Retrieve the method and directory configuration from the config
        self.method = PnmFileRetrievalMethod(self._config.get("PnmFileRetrieval", {}).get("method", "local"))
        self.dest_dir = self._config.get("PnmFileRetrieval", {}).get("save_dir", "/tmp")

    def retrieve(self, filename: str) -> str:
        """Determines retrieval method and calls the appropriate method."""
        if self.method == PnmFileRetrievalMethod.LOCAL:
            return self._retrieve_local(filename)
        elif self.method == PnmFileRetrievalMethod.TFTP:
            return self._retrieve_tftp(filename)
        elif self.method == PnmFileRetrievalMethod.FTP:
            return self._retrieve_ftp(filename)
        elif self.method == PnmFileRetrievalMethod.SCP:
            return self._retrieve_scp(filename)
        elif self.method == PnmFileRetrievalMethod.SFTP:
            return self._retrieve_sftp(filename)
        elif self.method == PnmFileRetrievalMethod.HTTP or self.method == PnmFileRetrievalMethod.HTTPS:
            return self._retrieve_http_https(filename)
        else:
            raise ValueError(f"Unsupported retrieval method: {self.method}")

    def _retrieve_local(self, filename: str) -> str:
        """Retrieves a file using the local method."""
        local_dir = self._config.get("PnmFileRetrieval", {}).get("local", {}).get("src_dir", "/tmp")
        src = os.path.join(local_dir, filename)
        dst = os.path.join(self.dest_dir, filename)
        shutil.copy(src, dst)
        return dst

    def _retrieve_tftp(self, filename: str) -> str:
        """Retrieves a file using TFTP."""
        tftp_cfg = self._config.get("PnmFileRetrieval", {}).get("tftp", {})
        client = TftpClient(tftp_cfg["host"], tftp_cfg.get("port", 69))
        remote_path = os.path.join(tftp_cfg.get("remote_dir", ""), filename)
        local_path = os.path.join(self.dest_dir, filename)
        client.download(remote_path, local_path)
        return local_path

    def _retrieve_ftp(self, filename: str) -> str:
        """Retrieves a file using FTP."""
        ftp_cfg = self._config.get("PnmFileRetrieval", {}).get("ftp", {})
        ftp = ftplib.FTP()
        ftp.connect(ftp_cfg["host"], ftp_cfg.get("port", 21))
        ftp.login(ftp_cfg.get("user", ""), ftp_cfg.get("password", ""))
        ftp.cwd(ftp_cfg.get("remote_dir", ""))
        local_path = os.path.join(self.dest_dir, filename)
        with open(local_path, 'wb') as f:
            ftp.retrbinary(f'RETR {filename}', f.write)
        ftp.quit()
        return local_path

    def _retrieve_scp(self, filename: str) -> str:
        """Retrieves a file using SCP."""
        scp_cfg = self._config.get("PnmFileRetrieval", {}).get("scp", {})
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(
            hostname=scp_cfg["host"],
            port=int(scp_cfg.get("port", 22)),
            username=scp_cfg["user"],
            password=scp_cfg.get("password")
        )
        scp = SCPClient(ssh.get_transport())
        remote_path = os.path.join(scp_cfg.get("remote_dir", ""), filename)
        local_path = os.path.join(self.dest_dir, filename)
        scp.get(remote_path, local_path)
        scp.close()
        return local_path

    def _retrieve_sftp(self, filename: str) -> str:
        """Retrieves a file using SFTP."""
        sftp_cfg = self._config.get("PnmFileRetrieval", {}).get("sftp", {})
        transport = paramiko.Transport((sftp_cfg["host"], int(sftp_cfg.get("port", 22))))
        transport.connect(username=sftp_cfg["user"], password=sftp_cfg.get("password"))
        sftp = paramiko.SFTPClient.from_transport(transport)
        remote_path = os.path.join(sftp_cfg.get("remote_dir", ""), filename)
        local_path = os.path.join(self.dest_dir, filename)
        sftp.get(remote_path, local_path)
        sftp.close()
        return local_path

    def _retrieve_http_https(self, filename: str) -> str:
        """Retrieves a file using HTTP/HTTPS."""
        proto = self.method.value
        base_cfg = self._config.get("PnmFileRetrieval", {}).get(proto, {})
        url = urllib.parse.urljoin(base_cfg["base_url"], filename)
        local_path = os.path.join(self.dest_dir, filename)
        r = requests.get(url)
        r.raise_for_status()
        with open(local_path, 'wb') as f:
            f.write(r.content)
        return local_path
