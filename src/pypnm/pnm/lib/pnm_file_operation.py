# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia

from enum import Enum

class PnmFileRetrievalMethod(Enum):
    LOCAL = "local"
    TFTP = "tftp"
    FTP = "ftp"
    SCP = "scp"
    SFTP = "sftp"
    HTTP = "http"
    HTTPS = "https"
