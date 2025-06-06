# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia

from pypnm.config.config_manager import ConfigManager

class SystemConfigCommonSettings:
    """Loads common defaults from system config at import time."""
    _cfg = ConfigManager()
    snmp_v2_write_comm: str   = _cfg.get("SNMP", "write_community")
    default_mac_address: str  = _cfg.get("FastApiRequestDefault", "mac_address")
    default_ip_address: str   = _cfg.get("FastApiRequestDefault", "ip_address")
    save_dir:str              = _cfg.get("PnmFileRetrieval", "save_dir")
    
    scp_host:str              = _cfg.get("PnmFileRetrieval", "scp", "host")
    scp_user:str              = _cfg.get("PnmFileRetrieval", "scp", "user")
    scp_port:int              = _cfg.get("PnmFileRetrieval", "scp", "port")
    scp_password:str          = _cfg.get("PnmFileRetrieval", "scp", "password")
    scp_remote_dir:str        = _cfg.get("PnmFileRetrieval", "scp", "remote_dir")
    
    sftp_host:str              = _cfg.get("PnmFileRetrieval", "sftp", "host")
    sftp_user:str              = _cfg.get("PnmFileRetrieval", "sftp", "user")
    sftp_port:int              = _cfg.get("PnmFileRetrieval", "sftp", "port")
    sftp_password:str          = _cfg.get("PnmFileRetrieval", "sftp", "password")
    sftp_remote_dir:str        = _cfg.get("PnmFileRetrieval", "sftp", "remote_dir")
    
    ftp_host: str            = _cfg.get("PnmFileRetrieval", "ftp", "host")
    ftp_user: str            = _cfg.get("PnmFileRetrieval", "ftp", "user")
    ftp_port: int            = _cfg.get("PnmFileRetrieval", "ftp", "port")
    ftp_password: str        = _cfg.get("PnmFileRetrieval", "ftp", "password")
    ftp_use_tls: bool        = _cfg.get("PnmFileRetrieval", "ftp", "use_tls")
    ftp_timeout: int         = _cfg.get("PnmFileRetrieval", "ftp", "timeout")
    ftp_remote_dir: str      = _cfg.get("PnmFileRetrieval", "ftp", "remote_dir")
    
    tftp_host: str            = _cfg.get("PnmFileRetrieval", "tftp", "host")
    tftp_user: str            = _cfg.get("PnmFileRetrieval", "tftp", "user")
    tftp_port: int            = _cfg.get("PnmFileRetrieval", "tftp", "port")
    tftp_timeout: int         = _cfg.get("PnmFileRetrieval", "tftp", "timeout")
    tftp_remote_dir:str       = _cfg.get("PnmFileRetrieval", "tftp", "remote_dir")