# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from pypnm.lib.secret.crypto_manager import SecretCryptoManager


def _write_json(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


@pytest.fixture()
def secret_env(monkeypatch: pytest.MonkeyPatch) -> str:
    env_name = "PYPNM_SECRET_KEY_TEST"
    key_b64  = SecretCryptoManager.generate_key_b64()
    monkeypatch.setenv(env_name, key_b64)
    return env_name


def test_encryptor_moves_password_to_password_enc_and_roundtrips(tmp_path: Path, secret_env: str) -> None:
    cfg_path  = tmp_path / "system.json"
    out_path  = tmp_path / "system.encrypted.json"
    tool_path = Path("tools") / "encrypt-system-config-secrets.py"

    config = {
        "PnmFileRetrieval": {
            "retrieval_method": {
                "methods": {
                    "ftp":  {"host": "ftp-host",  "user": "u", "password": "p"},
                    "scp":  {"host": "scp-host",  "user": "u", "password": "p"},
                    "sftp": {"host": "sftp-host", "user": "u", "password": "p"},
                }
            }
        },
        "SNMP": {"version": {"3": {"enable": True, "authPassword": "ap", "privPassword": "pp"}}},
    }
    _write_json(cfg_path, config)

    cmd = [
        sys.executable,
        str(tool_path),
        "--config", str(cfg_path),
        "--out", str(out_path),
        "--ack",
        "--env-var-name", secret_env,
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True, check=True)

    assert out_path.exists()
    data = json.loads(out_path.read_text(encoding="utf-8"))

    ftp  = data["PnmFileRetrieval"]["retrieval_method"]["methods"]["ftp"]
    scp  = data["PnmFileRetrieval"]["retrieval_method"]["methods"]["scp"]
    sftp = data["PnmFileRetrieval"]["retrieval_method"]["methods"]["sftp"]

    assert "password" not in ftp
    assert "password" not in scp
    assert "password" not in sftp

    assert ftp["password_enc"].startswith("ENC[")
    assert scp["password_enc"].startswith("ENC[")
    assert sftp["password_enc"].startswith("ENC[")

    snmp3 = data["SNMP"]["version"]["3"]
    assert snmp3["authPassword"].startswith("ENC[")
    assert snmp3["privPassword"].startswith("ENC[")

    assert "password -> password_enc (encrypted)" in proc.stdout

    assert SecretCryptoManager.decrypt_password(ftp["password_enc"],  env_var_name=secret_env) == "p"
    assert SecretCryptoManager.decrypt_password(scp["password_enc"],  env_var_name=secret_env) == "p"
    assert SecretCryptoManager.decrypt_password(sftp["password_enc"], env_var_name=secret_env) == "p"

    assert SecretCryptoManager.decrypt_password(snmp3["authPassword"], env_var_name=secret_env) == "ap"
    assert SecretCryptoManager.decrypt_password(snmp3["privPassword"], env_var_name=secret_env) == "pp"
