# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia

from pypnm.config.config_manager import ConfigManager

class classproperty:
    """Descriptor for class-level properties that reload config on each access."""
    def __init__(self, f):
        self.f = f
    def __get__(self, instance, owner):
        return self.f(owner)

class SystemConfigSettings:
    """Provides dynamically reloaded system configuration via class properties."""
    _cfg = ConfigManager()

    # FastAPI defaults
    @classproperty
    def default_mac_address(cls) -> str:
        return cls._cfg.get("FastApiRequestDefault", "mac_address")

    @classproperty
    def default_ip_address(cls) -> str:
        return cls._cfg.get("FastApiRequestDefault", "ip_address")

    # SNMP v2 settings
    @classproperty
    def snmp_version(cls) -> str:
        return cls._cfg.get("SNMP", "version")

    @classproperty
    def snmp_retries(cls) -> int:
        return int(cls._cfg.get("SNMP", "retries"))

    @classproperty
    def snmp_read_community(cls) -> str:
        return cls._cfg.get("SNMP", "read_community")

    @classproperty
    def snmp_write_community(cls) -> str:
        return cls._cfg.get("SNMP", "write_community")

    # Bulk data transfer settings
    @classproperty
    def bulk_transfer_method(cls) -> str:
        return cls._cfg.get("PnmBulkDataTransfer", "method")

    @classproperty
    def bulk_tftp_ip_v4(cls) -> str:
        return cls._cfg.get("PnmBulkDataTransfer", "tftp", "ip_v4")

    @classproperty
    def bulk_tftp_ip_v6(cls) -> str:
        return cls._cfg.get("PnmBulkDataTransfer", "tftp", "ip_v6")

    @classproperty
    def bulk_tftp_remote_dir(cls) -> str:
        return cls._cfg.get("PnmBulkDataTransfer", "tftp", "remote_dir")

    @classproperty
    def bulk_http_base_url(cls) -> str:
        return cls._cfg.get("PnmBulkDataTransfer", "http", "base_url")

    @classproperty
    def bulk_http_port(cls) -> int:
        return int(cls._cfg.get("PnmBulkDataTransfer", "http", "port"))

    @classproperty
    def bulk_https_base_url(cls) -> str:
        return cls._cfg.get("PnmBulkDataTransfer", "https", "base_url")

    @classproperty
    def bulk_https_port(cls) -> int:
        return int(cls._cfg.get("PnmBulkDataTransfer", "https", "port"))

    # PNM file retrieval settings
    @classproperty
    def save_dir(cls) -> str:
        return cls._cfg.get("PnmFileRetrieval", "pnm_dir")
    
    @classproperty
    def csv_dir(cls) -> str:
        return cls._cfg.get("PnmFileRetrieval", "csv_dir")    

    @classproperty
    def json_dir(cls) -> str:
        return cls._cfg.get("PnmFileRetrieval", "json_dir") 

    @classproperty
    def xlsx_dir(cls) -> str:
        return cls._cfg.get("PnmFileRetrieval", "xlsx_dir") 

    @classproperty
    def transaction_db(cls) -> str:
        return cls._cfg.get("PnmFileRetrieval", "transaction_db")

    @classproperty
    def capture_group_db(cls) -> str:
        return cls._cfg.get("PnmFileRetrieval", "capture_group_db")

    @classproperty
    def session_group_db(cls) -> str:
        return cls._cfg.get("PnmFileRetrieval", "session_group_db")

    @classproperty
    def operation_db(cls) -> str:
        return cls._cfg.get("PnmFileRetrieval", "operation_db")

    @classproperty
    def file_retrieval_retries(cls) -> int:
        return int(cls._cfg.get("PnmFileRetrieval", "retries"))

    @classproperty
    def retrieval_method(cls) -> str:
        return cls._cfg.get("PnmFileRetrieval", "retrival_method", "method")

    # Local method
    @classproperty
    def local_src_dir(cls) -> str:
        return cls._cfg.get(
            "PnmFileRetrieval", "retrival_method", "methods", "local", "src_dir")

    # TFTP method
    @classproperty
    def tftp_host(cls) -> str:
        return cls._cfg.get(
            "PnmFileRetrieval", "retrival_method", "methods", "tftp", "host")

    @classproperty
    def tftp_port(cls) -> int:
        return int(cls._cfg.get(
            "PnmFileRetrieval", "retrival_method", "methods", "tftp", "port"))

    @classproperty
    def tftp_timeout(cls) -> int:
        return int(cls._cfg.get(
            "PnmFileRetrieval", "retrival_method", "methods", "tftp", "timeout"))

    @classproperty
    def tftp_remote_dir(cls) -> str:
        return cls._cfg.get(
            "PnmFileRetrieval", "retrival_method", "methods", "tftp", "remote_dir")

    # FTP method
    @classproperty
    def ftp_host(cls) -> str:
        return cls._cfg.get(
            "PnmFileRetrieval", "retrival_method", "methods", "ftp", "host")

    @classproperty
    def ftp_port(cls) -> int:
        return int(cls._cfg.get(
            "PnmFileRetrieval", "retrival_method", "methods", "ftp", "port"))

    @classproperty
    def ftp_use_tls(cls) -> bool:
        return cls._cfg.get(
            "PnmFileRetrieval", "retrival_method", "methods", "ftp", "tls")

    @classproperty
    def ftp_timeout(cls) -> int:
        return int(cls._cfg.get(
            "PnmFileRetrieval", "retrival_method", "methods", "ftp", "timeout"))

    @classproperty
    def ftp_user(cls) -> str:
        return cls._cfg.get(
            "PnmFileRetrieval", "retrival_method", "methods", "ftp", "user")

    @classproperty
    def ftp_password(cls) -> str:
        return cls._cfg.get(
            "PnmFileRetrieval", "retrival_method", "methods", "ftp", "password")

    @classproperty
    def ftp_remote_dir(cls) -> str:
        return cls._cfg.get(
            "PnmFileRetrieval", "retrival_method", "methods", "ftp", "remote_dir")

    # SCP method
    @classproperty
    def scp_host(cls) -> str:
        return cls._cfg.get(
            "PnmFileRetrieval", "retrival_method", "methods", "scp", "host")

    @classproperty
    def scp_port(cls) -> int:
        return int(cls._cfg.get(
            "PnmFileRetrieval", "retrival_method", "methods", "scp", "port"))

    @classproperty
    def scp_user(cls) -> str:
        return cls._cfg.get(
            "PnmFileRetrieval", "retrival_method", "methods", "scp", "user")

    @classproperty
    def scp_password(cls) -> str:
        return cls._cfg.get(
            "PnmFileRetrieval", "retrival_method", "methods", "scp", "password")

    @classproperty
    def scp_remote_dir(cls) -> str:
        return cls._cfg.get(
            "PnmFileRetrieval", "retrival_method", "methods", "scp", "remote_dir")

    # SFTP method
    @classproperty
    def sftp_host(cls) -> str:
        return cls._cfg.get(
            "PnmFileRetrieval", "retrival_method", "methods", "sftp", "host")

    @classproperty
    def sftp_port(cls) -> int:
        return int(cls._cfg.get(
            "PnmFileRetrieval", "retrival_method", "methods", "sftp", "port"))

    @classproperty
    def sftp_user(cls) -> str:
        return cls._cfg.get(
            "PnmFileRetrieval", "retrival_method", "methods", "sftp", "user")

    @classproperty
    def sftp_password(cls) -> str:
        return cls._cfg.get(
            "PnmFileRetrieval", "retrival_method", "methods", "sftp", "password")

    @classproperty
    def sftp_remote_dir(cls) -> str:
        return cls._cfg.get(
            "PnmFileRetrieval", "retrival_method", "methods", "sftp", "remote_dir")

    # HTTP method
    @classproperty
    def http_base_url(cls) -> str:
        return cls._cfg.get(
            "PnmFileRetrieval", "retrival_method", "methods", "http", "base_url")

    @classproperty
    def http_port(cls) -> int:
        return int(cls._cfg.get(
            "PnmFileRetrieval", "retrival_method", "methods", "http", "port"))

    # HTTPS method
    @classproperty
    def https_base_url(cls) -> str:
        return cls._cfg.get(
            "PnmFileRetrieval", "retrival_method", "methods", "https", "base_url")

    @classproperty
    def https_port(cls) -> int:
        return int(cls._cfg.get(
            "PnmFileRetrieval", "retrival_method", "methods", "https", "port"))

    # Logging
    @classproperty
    def log_level(cls) -> str:
        return cls._cfg.get("logging", "log_level")

    @classproperty
    def log_dir(cls) -> str:
        return cls._cfg.get("logging", "log_dir")

    @classproperty
    def log_filename(cls) -> str:
        return cls._cfg.get("logging", "log_filename")
