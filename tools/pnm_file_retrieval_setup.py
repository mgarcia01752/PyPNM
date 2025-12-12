#!/usr/bin/env python3

# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia

from __future__ import annotations

import getpass
import json
import logging
import os
import sys
import time
from typing import Any

from pypnm.config.system_config_settings import SystemConfigSettings
from pypnm.lib.secret_crypto_manager import SecretCryptoError, SecretCryptoManager
from pypnm.lib.ssh.ssh_connector import SSHConnector, SecureTransferMode


class PnmFileRetrievalConfigurator:
    """
    Interactive Helper To Configure PNM File Retrieval Settings.

    This tool updates the ``PnmFileRetrieval`` section in ``system.json`` and
    lets the user choose which retrieval method is active:

        - local  → Copy from local src_dir
        - tftp   → Download from a TFTP server
        - scp    → Download from an SCP server
        - sftp   → Download from an SFTP server

    For SCP/SFTP, the script can configure host, port, username, and
    authentication (password token and/or private key), then perform a simple
    SSH connectivity test.

    Password Handling
    -----------------
    - Passwords are stored encrypted in the config (ENC[v1]:...).
    - The encrypted token is kept throughout the workflow.
    - Decryption is deferred to the SSH connector at connection time.
    """

    DEFAULT_LOCAL_SRC_DIR: str        = "/srv/tftp"
    DEFAULT_TFTP_HOST: str            = "localhost"
    DEFAULT_TFTP_PORT: int            = 69
    DEFAULT_TFTP_TIMEOUT_SEC: int     = 5
    DEFAULT_SSH_HOST: str             = "localhost"
    DEFAULT_SSH_PORT: int             = 22
    DEFAULT_SSH_KEY_PATH: str         = "~/.ssh/id_rsa_pypnm"
    DEFAULT_SSH_REMOTE_DIR: str       = "/srv/tftp"

    ENCRYPTED_TOKEN_PREFIX: str       = "ENC["

    def __init__(self) -> None:
        """
        Initialize The Configurator And Resolve The System Configuration Path.
        """
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.setLevel(logging.INFO)

        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(logging.INFO)

        formatter = logging.Formatter("%(levelname)s %(name)s: %(message)s")
        handler.setFormatter(formatter)

        if not self.logger.handlers:
            self.logger.addHandler(handler)

        SystemConfigSettings.reload()
        self.config_path = SystemConfigSettings.get_config_path()

        self.logger.info("Using configuration file: %s", self.config_path)

        self.config: dict[str, Any] = {}

        self._load_config()
        self._backup_config()

    def run(self) -> None:
        """
        Run The Interactive PNM File Retrieval Configuration Workflow.
        """
        method_key = self._prompt_method_choice()
        if not method_key:
            self.logger.info("No retrieval method selected; exiting without changes.")
            return

        self.logger.info("Selected retrieval method: %s", method_key)

        retrieval           = self._ensure_pnm_retrieval_section()
        retrieval["method"] = method_key

        methods    = retrieval.setdefault("methods", {})
        method_cfg = methods.setdefault(method_key, {})

        if method_key == "local":
            self._configure_local(method_cfg)
        elif method_key == "tftp":
            self._configure_tftp(method_cfg)
        elif method_key == "scp":
            self._configure_ssh_method(method_cfg, "scp", SecureTransferMode.SCP)
        elif method_key == "sftp":
            self._configure_ssh_method(method_cfg, "sftp", SecureTransferMode.SFTP)

        self._save_config()
        self.logger.info("PNM file retrieval configuration complete.")

        if method_key in ("scp", "sftp"):
            self._maybe_show_public_key(method_cfg, method_key)

    def _load_config(self) -> None:
        if not os.path.exists(self.config_path):
            raise FileNotFoundError(f"Config file not found: {self.config_path}")

        with open(self.config_path, "r", encoding="utf-8") as handle:
            self.config = json.load(handle)

    def _save_config(self) -> None:
        with open(self.config_path, "w", encoding="utf-8") as handle:
            json.dump(self.config, handle, indent=4)
            handle.write("\n")

    def _backup_config(self) -> None:
        ts          = int(time.time())
        base, ext   = os.path.splitext(self.config_path)
        backup_path = f"{base}.bak.{ts}{ext}"

        try:
            with open(self.config_path, "rb") as src, open(backup_path, "wb") as dst:
                dst.write(src.read())
            self.logger.info("Created backup: %s", backup_path)
        except OSError as exc:
            self.logger.error("Failed to create backup %s: %s", backup_path, exc)

    def _ensure_pnm_retrieval_section(self) -> dict[str, Any]:
        pnm       = self.config.setdefault("PnmFileRetrieval", {})
        retrieval = pnm.setdefault("retrival_method", {})

        retrieval.setdefault("method", "local")
        retrieval.setdefault("methods", {})

        return retrieval

    def _prompt_method_choice(self) -> str:
        print()
        print("Select PNM File Retrieval Method:")
        print("  1) local  - Copy from local src_dir")
        print("  2) tftp   - Download from TFTP server")
        print("  3) scp    - Download from SCP server")
        print("  4) sftp   - Download from SFTP server")
        print("  q) Quit   - Exit without changes")
        print()

        choices: dict[str, str] = {
            "1": "local",
            "2": "tftp",
            "3": "scp",
            "4": "sftp",
        }

        while True:
            choice = input("Enter choice [1-4 or q to quit]: ").strip().lower()
            if choice in choices:
                return choices[choice]
            if choice == "" or choice == "q":
                return ""
            print("Invalid selection. Please enter 1-4 or 'q' to quit.")

    def _prompt_yes_no(self, message: str, default: bool = False) -> bool:
        default_str = "Y/n" if default else "y/N"

        while True:
            answer = input(f"{message} [{default_str}]: ").strip()
            if not answer:
                return default
            if answer.lower() == "y":
                return True
            if answer.lower() == "n":
                return False
            print("Please answer 'y' or 'n'.")

    def _configure_local(self, cfg: dict[str, Any]) -> None:
        default_src = str(cfg.get("src_dir", self.DEFAULT_LOCAL_SRC_DIR))
        src         = input(f"Enter local src_dir [{default_src}]: ").strip()

        if not src:
            src = default_src

        cfg["src_dir"] = src
        self.logger.info("Configured local.src_dir = %s", src)

    def _configure_tftp(self, cfg: dict[str, Any]) -> None:
        default_host       = str(cfg.get("host", self.DEFAULT_TFTP_HOST))
        default_port       = int(cfg.get("port", self.DEFAULT_TFTP_PORT))
        default_timeout    = int(cfg.get("timeout", self.DEFAULT_TFTP_TIMEOUT_SEC))
        default_remote_dir = str(cfg.get("remote_dir", ""))

        host = input(f"Enter TFTP host [{default_host}]: ").strip()
        if not host:
            host = default_host

        port_str = input(f"Enter TFTP port for {host} [{default_port}]: ").strip()
        if port_str:
            try:
                port = int(port_str)
            except ValueError:
                port = default_port
        else:
            port = default_port

        timeout_str = input(f"Enter TFTP timeout seconds [{default_timeout}]: ").strip()
        if timeout_str:
            try:
                timeout = int(timeout_str)
            except ValueError:
                timeout = default_timeout
        else:
            timeout = default_timeout

        remote_dir = input(f"Enter TFTP remote_dir [{default_remote_dir}]: ").strip()
        if not remote_dir:
            remote_dir = default_remote_dir

        cfg["host"]       = host
        cfg["port"]       = port
        cfg["timeout"]    = timeout
        cfg["remote_dir"] = remote_dir

        self.logger.info("Configured TFTP host=%s port=%d remote_dir=%s", host, port, remote_dir)

    def _configure_ssh_method(
        self,
        cfg: dict[str, Any],
        method_name: str,
        transfer_mode: SecureTransferMode,
    ) -> None:
        default_host       = str(cfg.get("host", self.DEFAULT_SSH_HOST))
        default_port       = int(cfg.get("port", self.DEFAULT_SSH_PORT))
        default_user       = str(cfg.get("user", getpass.getuser() or "user"))
        default_remote_dir = str(cfg.get("remote_dir", self.DEFAULT_SSH_REMOTE_DIR))

        print()
        print(f"Configure {method_name.upper()} PNM File Retrieval:")

        host = input(f"Enter SSH host [{default_host}]: ").strip()
        if not host:
            host = default_host

        port_str = input(f"Enter SSH port for {host} [{default_port}]: ").strip()
        if port_str:
            try:
                port = int(port_str)
            except ValueError:
                port = default_port
        else:
            port = default_port

        user = input(f"Enter SSH username [{default_user}]: ").strip()
        if not user:
            user = default_user

        remote_dir = input(f"Enter remote_dir [{default_remote_dir}]: ").strip()
        if not remote_dir:
            remote_dir = default_remote_dir

        print()
        print("Authentication Options:")
        print("  You may configure password, private key, or both.")
        print("  At least one of them must be provided.")
        print("  Passwords are stored encrypted as ENC[v1]:... in system.json.")
        print()

        use_password = self._prompt_yes_no("Configure password authentication?", default=False)
        use_key      = self._prompt_yes_no("Configure private key authentication?", default=False)

        existing_password_token = str(cfg.get("password", "") or "")
        existing_key_path       = str(cfg.get("private_key_path", "") or "")

        password_token = existing_password_token
        key_path       = existing_key_path

        if use_password:
            pw = getpass.getpass("Enter SSH password (leave blank to clear, or paste ENC[...] token): ").strip()
            if pw == "":
                password_token = ""
            elif pw.startswith(self.ENCRYPTED_TOKEN_PREFIX):
                password_token = pw
            else:
                try:
                    password_token = SecretCryptoManager.encrypt_password(pw)
                except SecretCryptoError as exc:
                    self.logger.error("Failed to encrypt password: %s", exc)
                    raise SystemExit(1) from exc

        if use_key:
            default_key = existing_key_path or self.DEFAULT_SSH_KEY_PATH
            key_input   = input(f"Enter private key path [{default_key}]: ").strip()
            if not key_input:
                key_path = default_key
            else:
                key_path = key_input

        if password_token == "" and key_path == "":
            self.logger.error(
                "Neither password nor private_key_path configured for %s; "
                "at least one authentication method is required.",
                method_name,
            )
            raise SystemExit(1)

        cfg["host"]             = host
        cfg["port"]             = port
        cfg["user"]             = user
        cfg["password"]         = password_token
        cfg["private_key_path"] = key_path
        cfg["remote_dir"]       = remote_dir

        self._test_ssh_connection(
            method_name=method_name,
            host=host,
            port=port,
            user=user,
            password_token=password_token,
            private_key_path=key_path,
            transfer_mode=transfer_mode,
        )

    def _test_ssh_connection(
        self,
        method_name: str,
        host: str,
        port: int,
        user: str,
        password_token: str,
        private_key_path: str,
        transfer_mode: SecureTransferMode,
    ) -> None:
        self.logger.info(
            "Testing %s connection to %s@%s:%d ...",
            method_name.upper(),
            user,
            host,
            port,
        )

        connector = SSHConnector(
            hostname=host,
            username=user,
            port=port,
            transfer_mode=transfer_mode,
        )

        try:
            ok = connector.connect(
                password_enc=password_token,
                private_key_path=private_key_path,
            )
            if not ok:
                self.logger.error("%s connection test failed.", method_name.upper())
                raise SystemExit(1)

            self.logger.info("SSH connection test succeeded.")

        finally:
            connector.disconnect()

    def _maybe_show_public_key(self, cfg: dict[str, Any], method_name: str) -> None:
        key_path = str(cfg.get("private_key_path", "") or "")
        if not key_path:
            self.logger.info("No private_key_path configured for %s; skipping public key display.", method_name)
            return

        expanded = os.path.expanduser(key_path)
        pub_path = f"{expanded}.pub"

        if not os.path.exists(pub_path):
            self.logger.info(
                "Private key path is configured for %s, but no public key file found at: %s",
                method_name,
                pub_path,
            )
            self.logger.info(
                "If you have not generated a key pair yet, run your SSH key setup helper "
                "and then re-run this script to review the public key."
            )
            return

        try:
            with open(pub_path, "r", encoding="utf-8") as handle:
                pub_key = handle.read().strip()
        except OSError as exc:
            self.logger.error("Failed to read public key file %s: %s", pub_path, exc)
            return

        if not pub_key:
            self.logger.error("Public key file %s is empty.", pub_path)
            return

        print()
        print("======================================================================")
        print(f" {method_name.upper()} Public Key (Add To Your PNM File Server)")
        print("======================================================================")
        print(pub_key)
        print()
        print("Add this key to the remote user's ~/.ssh/authorized_keys on the host(s)")
        print(f"you configured for {method_name} file retrieval.")
        print("======================================================================")
        print()


def main() -> None:
    configurator = PnmFileRetrievalConfigurator()
    configurator.run()


if __name__ == "__main__":
    main()
