#!/usr/bin/env python
# SPDX-License-Identifier: MIT

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Final, Mapping, MutableMapping

from pypnm.lib.secret.crypto_manager import SecretCryptoManager


JsonValue = Any
JsonDict  = MutableMapping[str, JsonValue]


@dataclass(frozen=True, slots=True)
class EncryptResult:
    changed: bool
    changes: list[str]


class ConfigSecretEncryptor:
    _ENC_PREFIX: Final[str] = "ENC["

    def __init__(
        self,
        *,
        key_path: Path | None,
        env_var_name: str,
        version: str,
    ) -> None:
        self._key_path     = key_path
        self._env_var_name = env_var_name
        self._version      = version

    @staticmethod
    def _is_encrypted(value: str) -> bool:
        return value.strip().startswith(ConfigSecretEncryptor._ENC_PREFIX)

    def _encrypt(self, value: str) -> str:
        text = value.strip()
        if text == "":
            return ""
        if self._is_encrypted(text):
            return text
        return SecretCryptoManager.encrypt_password(
            text,
            key_path      = self._key_path,
            env_var_name  = self._env_var_name,
            version       = self._version,
        )

    @staticmethod
    def _get_dict(root: JsonDict, *path: str) -> JsonDict:
        node: JsonDict = root
        for key in path:
            value = node.get(key)
            if not isinstance(value, dict):
                created: JsonDict = {}
                node[key] = created
                node = created
                continue
            node = value
        return node

    @staticmethod
    def _peek_str(root: Mapping[str, JsonValue], *path: str) -> str:
        node: Mapping[str, JsonValue] = root
        for key in path[:-1]:
            value = node.get(key)
            if not isinstance(value, dict):
                return ""
            node = value
        leaf = node.get(path[-1])
        if leaf is None:
            return ""
        if isinstance(leaf, str):
            return leaf
        return str(leaf)

    @staticmethod
    def _set_str(root: JsonDict, value: str, *path: str) -> None:
        node = ConfigSecretEncryptor._get_dict(root, *path[:-1])
        node[path[-1]] = value

    @staticmethod
    def _del_key(root: JsonDict, *path: str) -> None:
        node: JsonDict = root
        for key in path[:-1]:
            value = node.get(key)
            if not isinstance(value, dict):
                return
            node = value
        node.pop(path[-1], None)

    def _encrypt_method_passwords(self, cfg: JsonDict) -> EncryptResult:
        changes: list[str] = []
        changed            = False

        base        = ("PnmFileRetrieval",)
        method_keys = ("retrieval_method", "retrival_method")
        methods     = ("ftp", "scp", "sftp")

        for method_key in method_keys:
            for method in methods:
                root_path = base + (method_key, "methods", method)

                password_enc = self._peek_str(cfg, *root_path, "password_enc").strip()
                if password_enc != "":
                    if not self._is_encrypted(password_enc):
                        enc = self._encrypt(password_enc)
                        self._set_str(cfg, enc, *root_path, "password_enc")
                        changes.append(f"{'.'.join(root_path)}.password_enc -> encrypted")
                        changed = True
                    continue

                password = self._peek_str(cfg, *root_path, "password").strip()
                if password == "":
                    continue

                enc = self._encrypt(password)
                self._set_str(cfg, enc, *root_path, "password_enc")
                self._del_key(cfg, *root_path, "password")
                changes.append(f"{'.'.join(root_path)}.password -> password_enc (encrypted)")
                changed = True

        return EncryptResult(changed=changed, changes=changes)

    def _encrypt_snmpv3_passwords(self, cfg: JsonDict) -> EncryptResult:
        changes: list[str] = []
        changed            = False

        base   = ("SNMP", "version", "3")
        fields = ("authPassword", "privPassword")

        for field in fields:
            current = self._peek_str(cfg, *base, field).strip()
            if current == "":
                continue
            if self._is_encrypted(current):
                continue

            enc = self._encrypt(current)
            self._set_str(cfg, enc, *base, field)
            changes.append(f"{'.'.join(base)}.{field} -> encrypted")
            changed = True

        return EncryptResult(changed=changed, changes=changes)

    def run(self, cfg: JsonDict) -> EncryptResult:
        r1 = self._encrypt_method_passwords(cfg)
        r2 = self._encrypt_snmpv3_passwords(cfg)

        changed = r1.changed or r2.changed
        changes = [*r1.changes, *r2.changes]

        return EncryptResult(changed=changed, changes=changes)


class Cli:
    @staticmethod
    def _read_json(path: Path) -> JsonDict:
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise ValueError("Top-level JSON must be an object")
        return data

    @staticmethod
    def _write_json(path: Path, data: JsonDict) -> None:
        text = json.dumps(data, indent=2, ensure_ascii=False)
        path.write_text(text + "\n", encoding="utf-8")

    @staticmethod
    def main(argv: list[str] | None = None) -> int:
        parser = argparse.ArgumentParser(
            prog="encrypt-system-config-secrets",
            description="Encrypt secrets in PyPNM system.json (writes password_enc / ENC[...] tokens).",
        )
        parser.add_argument("--config", required=True, help="Path to config/system.json")
        parser.add_argument("--out", default="", help="Output path. Default: <config>.encrypted.json")
        parser.add_argument("--in-place", action="store_true", help="Overwrite the input config file")
        parser.add_argument("--dry-run", action="store_true", help="Show what would change without writing")
        parser.add_argument("--ack", action="store_true", help="Acknowledge that this will modify stored secrets")

        parser.add_argument("--env-var-name", default=SecretCryptoManager.DEFAULT_ENV_VAR_NAME, help="Secret key env var name")
        parser.add_argument("--key-path", default="", help="Optional key file path (default: ~/.ssh/pypnm_secrets.key)")
        parser.add_argument("--version", default=SecretCryptoManager.DEFAULT_TOKEN_VERSION, help="Token version label (default: v1)")

        args = parser.parse_args(argv)

        config_path = Path(args.config).expanduser().resolve()
        if not config_path.exists():
            raise FileNotFoundError(str(config_path))

        out_path = config_path
        if not args.in_place:
            if args.out.strip() != "":
                out_path = Path(args.out).expanduser().resolve()
            else:
                out_path = config_path.with_suffix(".encrypted.json")

        if not args.dry_run and not args.ack:
            parser.error("--ack is required unless --dry-run is set")

        key_path = Path(args.key_path).expanduser().resolve() if args.key_path.strip() != "" else None

        cfg = Cli._read_json(config_path)

        encryptor = ConfigSecretEncryptor(
            key_path      = key_path,
            env_var_name  = args.env_var_name,
            version       = args.version,
        )

        result = encryptor.run(cfg)

        if not result.changes:
            print("No secrets needed encryption.")
            return 0

        for item in result.changes:
            print(item)

        if args.dry_run:
            print("Dry-run: no files written.")
            return 0

        Cli._write_json(out_path, cfg)
        print(f"Wrote: {out_path}")
        return 0


if __name__ == "__main__":
    raise SystemExit(Cli.main())
