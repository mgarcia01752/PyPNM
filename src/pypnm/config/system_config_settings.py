# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia
from __future__ import annotations

import logging
from pathlib import Path
from typing import cast

from pypnm.config.config_manager import ConfigManager
from pypnm.lib.mac_address import MacAddress
from pypnm.lib.types import InetAddressStr, IPv4Str, IPv6Str, MacAddressStr


class SystemConfigSettings:
    """Provides dynamically reloaded system configuration via class properties."""
    _cfg        = ConfigManager()
    _logger     = logging.getLogger("SystemConfigSettings")

    _DEFAULT_IP_ADDRESS: InetAddressStr = cast(InetAddressStr, "192.168.0.100")
    _DEFAULT_SNMP_RETRIES: int              = 5
    _DEFAULT_SNMP_TIMEOUT: int              = 2
    _DEFAULT_FILE_RETRIEVAL_RETRIES: int    = 5
    _DEFAULT_HTTP_PORT: int                 = 80
    _DEFAULT_HTTPS_PORT: int                = 443
    _DEFAULT_TFTP_PORT: int                 = 69
    _DEFAULT_FTP_PORT: int                  = 21
    _DEFAULT_SCP_PORT: int                  = 22
    _DEFAULT_SFTP_PORT: int                 = 22
    _DEFAULT_LOG_LEVEL: str                 = "INFO"
    _DEFAULT_LOG_DIR: str                   = "logs"
    _DEFAULT_LOG_FILENAME: str              = "pypnm.log"
    _DEFAULT_SNMP_READ_COMMUNITY: str       = "public"
    _DEFAULT_SNMP_WRITE_COMMUNITY: str      = "private"
    _DEFAULT_PNM_DIR: str                   = ".data/pnm"
    _DEFAULT_CSV_DIR: str                   = ".data/csv"
    _DEFAULT_JSON_DIR: str                  = ".data/json"
    _DEFAULT_XLSX_DIR: str                  = ".data/xlsx"
    _DEFAULT_PNG_DIR: str                   = ".data/png"
    _DEFAULT_ARCHIVE_DIR: str               = ".data/archive"
    _DEFAULT_MSG_RSP_DIR: str               = ".data/msg_rsp"

    @classmethod
    def _config_path(cls, *path: str) -> str:
        """Return dotted path for logging."""
        return ".".join(path)

    @classmethod
    def _get_str(cls, default: str, *path: str) -> str:
        value = cls._cfg.get(*path)
        if value is None:
            cls._logger.error(
                "Missing configuration value for '%s'; using default '%s'",
                cls._config_path(*path),
                default,
            )
            return default
        if not isinstance(value, str):
            coerced = str(value)
            cls._logger.error(
                "Non-string configuration value for '%s': %r; using coerced '%s'",
                cls._config_path(*path),
                value,
                coerced,
            )
            return coerced
        if value == "":
            cls._logger.error(
                "Empty configuration value for '%s'; using default '%s'",
                cls._config_path(*path),
                default,
            )
            return default
        return value

    @classmethod
    def _get_int(cls, default: int, *path: str) -> int:
        value = cls._cfg.get(*path)
        if value is None:
            cls._logger.error(
                "Missing configuration value for '%s'; using default %d",
                cls._config_path(*path),
                default,
            )
            return default
        try:
            return int(value)
        except (TypeError, ValueError):
            cls._logger.error(
                "Invalid integer configuration value for '%s': %r; using default %d",
                cls._config_path(*path),
                value,
                default,
            )
            return default

    @classmethod
    def _get_bool(cls, default: bool, *path: str) -> bool:
        value = cls._cfg.get(*path)
        if isinstance(value, bool):
            return value
        if value is None:
            cls._logger.error(
                "Missing configuration value for '%s'; using default %s",
                cls._config_path(*path),
                default,
            )
            return default

        text = str(value).strip().lower()
        if text in ("1", "true", "yes", "on"):
            return True
        if text in ("0", "false", "no", "off"):
            return False

        cls._logger.error(
            "Invalid boolean configuration value for '%s': %r; using default %s",
            cls._config_path(*path),
            value,
            default,
        )
        return default

    @classmethod
    def get_config_path(cls) -> str:
        return cls._cfg.get_config_path()

    @classmethod
    def default_mac_address(cls) -> MacAddressStr:
        mac = cls._cfg.get("FastApiRequestDefault", "mac_address")
        if not mac:
            cls._logger.error(
                "Missing configuration value for '%s'; using MacAddress.null()",
                cls._config_path("FastApiRequestDefault", "mac_address"),
            )
            return cast(MacAddressStr, MacAddress.null())
        return cast(MacAddressStr, mac)

    @classmethod
    def default_ip_address(cls) -> InetAddressStr:
        return cast(
            InetAddressStr,
            cls._get_str(cls._DEFAULT_IP_ADDRESS, "FastApiRequestDefault", "ip_address"),
        )

    # SNMP v2 settings
    @classmethod
    def snmp_enable(cls) -> bool:
        return cls._get_bool(True, "SNMP", "version", "2c", "enable")

    @classmethod
    def snmp_retries(cls) -> int:
        return cls._get_int(cls._DEFAULT_SNMP_RETRIES, "SNMP", "version", "2c", "retries")

    @classmethod
    def snmp_read_community(cls) -> str:
        return cls._get_str(cls._DEFAULT_SNMP_READ_COMMUNITY, "SNMP", "version", "2c", "read_community")

    @classmethod
    def snmp_write_community(cls) -> str:
        return cls._get_str(cls._DEFAULT_SNMP_WRITE_COMMUNITY, "SNMP", "version", "2c", "write_community")

    # SNMP v3 settings

    @classmethod
    def snmp_v3_enable(cls) -> bool:
        return cls._get_bool(False, "SNMP", "version", "3", "enable")

    @classmethod
    def snmp_v3_username(cls) -> str:
        return cls._get_str("", "SNMP", "version", "3", "username")

    @classmethod
    def snmp_v3_auth_protocol(cls) -> str:
        return cls._get_str("", "SNMP", "version", "3", "auth_protocol")

    @classmethod
    def snmp_v3_auth_password(cls) -> str:
        return cls._get_str("", "SNMP", "version", "3", "auth_password")

    @classmethod
    def snmp_v3_priv_protocol(cls) -> str:
        return cls._get_str("", "SNMP", "version", "3", "priv_protocol")

    @classmethod
    def snmp_v3_priv_password(cls) -> str:
        return cls._get_str("", "SNMP", "version", "3", "priv_password")

    # SNMP general settings
    @classmethod
    def snmp_timeout(cls) -> int:
        return cls._get_int(cls._DEFAULT_SNMP_TIMEOUT, "SNMP", "timeout")

    # Bulk data transfer settings
    @classmethod
    def bulk_transfer_method(cls) -> str:
        return cls._get_str("", "PnmBulkDataTransfer", "method")

    @classmethod
    def bulk_tftp_ip_v4(cls) -> IPv4Str:
        return cast(
            IPv4Str,
            cls._get_str("", "PnmBulkDataTransfer", "tftp", "ip_v4"),
        )

    @classmethod
    def bulk_tftp_ip_v6(cls) -> IPv6Str:
        return cast(
            IPv6Str,
            cls._get_str("", "PnmBulkDataTransfer", "tftp", "ip_v6"),
        )

    @classmethod
    def bulk_tftp_remote_dir(cls) -> str:
        return cls._get_str("", "PnmBulkDataTransfer", "tftp", "remote_dir")

    @classmethod
    def bulk_http_base_url(cls) -> str:
        return cls._get_str("", "PnmBulkDataTransfer", "http", "base_url")

    @classmethod
    def bulk_http_port(cls) -> int:
        return cls._get_int(cls._DEFAULT_HTTP_PORT, "PnmBulkDataTransfer", "http", "port")

    @classmethod
    def bulk_https_base_url(cls) -> str:
        return cls._get_str("", "PnmBulkDataTransfer", "https", "base_url")

    @classmethod
    def bulk_https_port(cls) -> int:
        return cls._get_int(cls._DEFAULT_HTTPS_PORT, "PnmBulkDataTransfer", "https", "port")

    # PNM file retrieval/storage settings
    @classmethod
    def save_dir(cls) -> str:
        return cls._get_str(cls._DEFAULT_PNM_DIR, "PnmFileRetrieval", "pnm_dir")

    @classmethod
    def pnm_dir(cls) -> str:
        return cls._get_str(cls._DEFAULT_PNM_DIR, "PnmFileRetrieval", "pnm_dir")

    @classmethod
    def csv_dir(cls) -> str:
        return cls._get_str(cls._DEFAULT_CSV_DIR, "PnmFileRetrieval", "csv_dir")

    @classmethod
    def json_dir(cls) -> str:
        return cls._get_str(cls._DEFAULT_JSON_DIR, "PnmFileRetrieval", "json_dir")

    @classmethod
    def xlsx_dir(cls) -> str:
        return cls._get_str(cls._DEFAULT_XLSX_DIR, "PnmFileRetrieval", "xlsx_dir")

    @classmethod
    def png_dir(cls) -> str:
        return cls._get_str(cls._DEFAULT_PNG_DIR, "PnmFileRetrieval", "png_dir")

    @classmethod
    def archive_dir(cls) -> str:
        return cls._get_str(cls._DEFAULT_ARCHIVE_DIR, "PnmFileRetrieval", "archive_dir")

    @classmethod
    def message_response_dir(cls) -> str:
        return cls._get_str(cls._DEFAULT_MSG_RSP_DIR, "PnmFileRetrieval", "msg_rsp_dir")

    @classmethod
    def transaction_db(cls) -> str:
        return cls._get_str("", "PnmFileRetrieval", "transaction_db")

    @classmethod
    def capture_group_db(cls) -> str:
        return cls._get_str("", "PnmFileRetrieval", "capture_group_db")

    @classmethod
    def session_group_db(cls) -> str:
        return cls._get_str("", "PnmFileRetrieval", "session_group_db")

    @classmethod
    def operation_db(cls) -> str:
        return cls._get_str("", "PnmFileRetrieval", "operation_db")

    @classmethod
    def json_db(cls) -> str:
        return cls._get_str("", "PnmFileRetrieval", "json_transaction_db")

    @classmethod
    def file_retrieval_retries(cls) -> int:
        return cls._get_int(cls._DEFAULT_FILE_RETRIEVAL_RETRIES, "PnmFileRetrieval", "retries")

    @classmethod
    def retrieval_method(cls) -> str:
        return cls._get_str("", "PnmFileRetrieval", "retrival_method", "method")

    # Local method
    @classmethod
    def local_src_dir(cls) -> str:
        return cls._get_str(
            "",
            "PnmFileRetrieval", "retrival_method", "methods", "local", "src_dir",
        )

    # TFTP method
    @classmethod
    def tftp_host(cls) -> InetAddressStr:
        return InetAddressStr(cls._get_str(
            "",
            "PnmFileRetrieval", "retrival_method", "methods", "tftp", "host",
        ))

    @classmethod
    def tftp_port(cls) -> int:
        return cls._get_int(
            cls._DEFAULT_TFTP_PORT,
            "PnmFileRetrieval", "retrival_method", "methods", "tftp", "port",
        )

    @classmethod
    def tftp_timeout(cls) -> int:
        return cls._get_int(
            cls._DEFAULT_SNMP_TIMEOUT,
            "PnmFileRetrieval", "retrival_method", "methods", "tftp", "timeout",
        )

    @classmethod
    def tftp_remote_dir(cls) -> str:
        return cls._get_str(
            "",
            "PnmFileRetrieval", "retrival_method", "methods", "tftp", "remote_dir",
        )

    # FTP method
    @classmethod
    def ftp_host(cls) -> str:
        return cls._get_str(
            "",
            "PnmFileRetrieval", "retrival_method", "methods", "ftp", "host",
        )

    @classmethod
    def ftp_port(cls) -> int:
        return cls._get_int(
            cls._DEFAULT_FTP_PORT,
            "PnmFileRetrieval", "retrival_method", "methods", "ftp", "port",
        )

    @classmethod
    def ftp_use_tls(cls) -> bool:
        return cls._get_bool(
            False,
            "PnmFileRetrieval", "retrival_method", "methods", "ftp", "tls",
        )

    @classmethod
    def ftp_timeout(cls) -> int:
        return cls._get_int(
            cls._DEFAULT_SNMP_TIMEOUT,
            "PnmFileRetrieval", "retrival_method", "methods", "ftp", "timeout",
        )

    @classmethod
    def ftp_user(cls) -> str:
        return cls._get_str(
            "",
            "PnmFileRetrieval", "retrival_method", "methods", "ftp", "user",
        )

    @classmethod
    def ftp_password(cls) -> str:
        return cls._get_str(
            "",
            "PnmFileRetrieval", "retrival_method", "methods", "ftp", "password",
        )

    @classmethod
    def ftp_remote_dir(cls) -> str:
        return cls._get_str(
            "",
            "PnmFileRetrieval", "retrival_method", "methods", "ftp", "remote_dir",
        )

    # SCP method
    @classmethod
    def scp_host(cls) -> str:
        return cls._get_str(
            "",
            "PnmFileRetrieval", "retrival_method", "methods", "scp", "host",
        )

    @classmethod
    def scp_port(cls) -> int:
        return cls._get_int(
            cls._DEFAULT_SCP_PORT,
            "PnmFileRetrieval", "retrival_method", "methods", "scp", "port",
        )

    @classmethod
    def scp_user(cls) -> str:
        return cls._get_str(
            "",
            "PnmFileRetrieval", "retrival_method", "methods", "scp", "user",
        )

    @classmethod
    def scp_password(cls) -> str:
        return cls._get_str(
            "",
            "PnmFileRetrieval", "retrival_method", "methods", "scp", "password",
        )

    @classmethod
    def scp_private_key_path(cls) -> str:
        return cls._get_str(
            "",
            "PnmFileRetrieval", "retrival_method", "methods", "scp", "private_key_path",
        )

    @classmethod
    def scp_remote_dir(cls) -> str:
        return cls._get_str(
            "",
            "PnmFileRetrieval", "retrival_method", "methods", "scp", "remote_dir",
        )

    # SFTP method
    @classmethod
    def sftp_host(cls) -> str:
        return cls._get_str(
            "",
            "PnmFileRetrieval", "retrival_method", "methods", "sftp", "host",
        )

    @classmethod
    def sftp_port(cls) -> int:
        return cls._get_int(
            cls._DEFAULT_SFTP_PORT,
            "PnmFileRetrieval", "retrival_method", "methods", "sftp", "port",
        )

    @classmethod
    def sftp_user(cls) -> str:
        return cls._get_str(
            "",
            "PnmFileRetrieval", "retrival_method", "methods", "sftp", "user",
        )

    @classmethod
    def sftp_password(cls) -> str:
        return cls._get_str(
            "",
            "PnmFileRetrieval", "retrival_method", "methods", "sftp", "password",
        )

    @classmethod
    def sftp_private_key_path(cls) -> str:
        return cls._get_str(
            "",
            "PnmFileRetrieval", "retrival_method", "methods", "sftp", "private_key_path",
        )

    @classmethod
    def sftp_remote_dir(cls) -> str:
        return cls._get_str(
            "",
            "PnmFileRetrieval", "retrival_method", "methods", "sftp", "remote_dir",
        )

    # HTTP method
    @classmethod
    def http_base_url(cls) -> str:
        return cls._get_str(
            "",
            "PnmFileRetrieval", "retrival_method", "methods", "http", "base_url",
        )

    @classmethod
    def http_port(cls) -> int:
        return cls._get_int(
            cls._DEFAULT_HTTP_PORT,
            "PnmFileRetrieval", "retrival_method", "methods", "http", "port",
        )

    # HTTPS method
    @classmethod
    def https_base_url(cls) -> str:
        return cls._get_str(
            "",
            "PnmFileRetrieval", "retrival_method", "methods", "https", "base_url",
        )

    @classmethod
    def https_port(cls) -> int:
        return cls._get_int(
            cls._DEFAULT_HTTPS_PORT,
            "PnmFileRetrieval", "retrival_method", "methods", "https", "port",
        )

    # Logging
    @classmethod
    def log_level(cls) -> str:
        return cls._get_str(cls._DEFAULT_LOG_LEVEL, "logging", "log_level")

    @classmethod
    def log_dir(cls) -> str:
        return cls._get_str(cls._DEFAULT_LOG_DIR, "logging", "log_dir")

    @classmethod
    def log_filename(cls) -> str:
        return cls._get_str(cls._DEFAULT_LOG_FILENAME, "logging", "log_filename")

    @classmethod
    def initialize_directories(cls) -> None:
        """
        Create necessary directories if they do not exist.
        """
        directories = [
            cls.pnm_dir(),
            cls.csv_dir(),
            cls.json_dir(),
            cls.xlsx_dir(),
            cls.png_dir(),
            cls.archive_dir(),
            cls.message_response_dir(),
            cls.log_dir(),
        ]
        for directory in directories:
            Path(directory).mkdir(parents=True, exist_ok=True)

    @classmethod
    def reload(cls) -> None:
        """
        Reload the configuration settings.
        """
        cls._cfg.reload()
        cls.initialize_directories()
