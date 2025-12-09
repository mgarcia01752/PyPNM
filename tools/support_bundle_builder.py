#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia

from __future__ import annotations

import argparse
import json
import logging
import re
import shutil
import subprocess
import sys
from collections.abc import Iterable
from pathlib import Path
from typing import cast

from pypnm.api.routes.common.classes.file_capture.pnm_file_opearation import (
    OperationCaptureGroupResolver,
)
from pypnm.api.routes.common.classes.file_capture.pnm_file_transaction import (
    PnmFileTransaction,
)
from pypnm.config.system_config_settings import SystemConfigSettings
from pypnm.lib.mac_address import MacAddress
from pypnm.lib.types import (
    GroupId,
    MacAddressStr,
    OperationId,
    TransactionId,
)
from pypnm.lib.archive.manager import ArchiveManager

SYSTEM_DESCRIPTION: dict[str, str] = {
    "HW_REV":  "1.0",
    "VENDOR":  "LANCity",
    "BOOTR":   "NONE",
    "SW_REV":  "1.0.0",
    "MODEL":   "LCPET-3",
}

SUPPORT_MAC: MacAddressStr = cast(MacAddressStr, "aa:bb:cc:dd:ee:ff")

FILENAME_MAC_PATTERN = re.compile(
    r"^(?P<prefix>.+?)_(?P<mac>[0-9a-fA-F]{12})(?P<suffix>_.+)?$"
)

MAC_TOKEN_PATTERN = re.compile(
    r"(?:[0-9a-f]{2}[:\-_]?){5}[0-9a-f]{2}",
    re.IGNORECASE,
)


class SupportBundleBuilder:
    """
    Build A Sanitized Support Bundle For PyPNM PNM Files.

    Selection Modes
    ---------------
    - TransactionId(s)
    - OperationId(s)
    - MacAddress(es)

    Sanitization (default)
    ----------------------
    - mac_address in JSON           -> aa:bb:cc:dd:ee:ff
    - filename MAC segment          -> aa:bb:cc:dd:ee:ff (compact form in filename)
    - device_details.system_description
        -> SYSTEM_DESCRIPTION template

    Optional Flags
    --------------
    - keep_original_mac:
        Preserve mac_address in JSON, filenames, and skip pnm-mac-updater.
    - keep_original_sysdescr:
        Preserve device_details.system_description.

    Output
    ------
    - A ZIP file containing a `.data/...` tree rooted at support_root, with:
        * Trimmed + sanitized transaction DB
        * Trimmed capture group DB
        * Trimmed operation DB
        * Relevant PNM capture files copied under .data/pnm
    """

    def __init__(
        self,
        support_root: Path,
        output_zip: Path,
        mac_updater: Path | None,
        verbose: bool,
    ) -> None:
        self.logger = logging.getLogger(self.__class__.__name__)
        self.support_root: Path = support_root
        self.output_zip: Path = output_zip
        self.mac_updater: Path | None = mac_updater
        self.verbose: bool = verbose

        self.transaction_store = PnmFileTransaction()
        self.operation_resolver = OperationCaptureGroupResolver()

        self._new_mac: MacAddressStr = SUPPORT_MAC
        self._new_mac_variants: tuple[str, str, str, str] = self._build_mac_variants(
            str(self._new_mac)
        )

        self._src_pnm_dir: Path = Path(SystemConfigSettings.pnm_dir())
        self._src_transaction_db_path: Path = Path(SystemConfigSettings.transaction_db())
        self._src_capture_group_db_path: Path = Path(SystemConfigSettings.capture_group_db())
        self._src_operation_db_path: Path = Path(SystemConfigSettings.operation_db())

    def _vprint(self, message: str) -> None:
        if self.verbose:
            print(message)

    @staticmethod
    def _build_mac_variants(mac: str) -> tuple[str, str, str, str]:
        compact = mac.replace(":", "").replace("-", "").replace("_", "").lower()
        if len(compact) != 12:
            raise ValueError(f"Expected 12 hex characters for MAC, got '{compact}'")

        colon = ":".join(compact[i : i + 2] for i in range(0, 12, 2))
        dash = "-".join(compact[i : i + 2] for i in range(0, 12, 2))
        underscore = "_".join(compact[i : i + 2] for i in range(0, 12, 2))

        return colon, dash, underscore, compact

    @staticmethod
    def _normalize_mac_str(mac: str) -> str:
        compact = mac.replace(":", "").replace("-", "").replace("_", "").lower()
        if len(compact) != 12:
            return mac
        return ":".join(compact[i : i + 2] for i in range(0, 12, 2))

    def _rewrite_filename_mac(self, filename: str, old_mac: str) -> str:
        """
        Rewrite The MAC Portion Of A Filename Using Naming Convention And Old MAC.

        Primary path:
            - Expect filenames of the form "<prefix>_<12-hex MAC><suffix>".
            - Replace the 12-hex MAC only if it matches the old MAC compact form.

        Fallback:
            - Replace the first MAC-like token using MAC_TOKEN_PATTERN.
        """
        new_name = filename

        old_compact = old_mac.replace(":", "").replace("-", "").replace("_", "").lower()
        if len(old_compact) != 12:
            old_compact = ""

        match = FILENAME_MAC_PATTERN.match(filename)
        if match and old_compact:
            mac_part = match.group("mac").lower()
            prefix = match.group("prefix")
            suffix = match.group("suffix") or ""
            if mac_part == old_compact:
                new_compact = self._new_mac_variants[3]
                return f"{prefix}_{new_compact}{suffix}"

        new_variants = self._new_mac_variants

        def _force_replace(match_obj: re.Match[str]) -> str:
            token = match_obj.group(0)
            if ":" in token:
                return new_variants[0]
            if "-" in token:
                return new_variants[1]
            if "_" in token:
                return new_variants[2]
            return new_variants[3]

        forced_name = MAC_TOKEN_PATTERN.sub(_force_replace, new_name)
        return forced_name

    @staticmethod
    def _load_json(path: Path) -> dict[str, object]:
        try:
            text = path.read_text(encoding="utf-8")
            data = json.loads(text)
            if not isinstance(data, dict):
                return {}
            return data
        except (OSError, json.JSONDecodeError):
            return {}

    def _run_mac_updater(self, capture_path: Path, sanitize_mac: bool) -> bool:
        """
        Optionally Invoke pnm-mac-updater.py To Rewrite The Binary MAC.

        Uses:
            pnm-mac-updater.py --mac-address SUPPORT_MAC --file CAPTURE

        Disabled when sanitize_mac is False.
        """
        if not sanitize_mac:
            return False

        if self.mac_updater is None:
            return False

        if not self.mac_updater.exists():
            self.logger.warning(
                "pnm-mac-updater.py not found at '%s'; skipping binary MAC rewrite for '%s'",
                self.mac_updater,
                capture_path,
            )
            return False

        cmd: list[str] = [
            sys.executable,
            str(self.mac_updater),
            "--mac-address",
            str(self._new_mac),
            "--file",
            str(capture_path),
        ]
        try:
            subprocess.run(cmd, check=True)
        except subprocess.CalledProcessError as exc:
            self.logger.error(
                "pnm-mac-updater failed for '%s': %s",
                capture_path,
                exc,
            )
            return False

        self._vprint(f"Updated capture MAC via pnm-mac-updater: {capture_path}")
        return True

    def _resolve_transactions(
        self,
        transaction_ids: Iterable[TransactionId],
        operation_ids: Iterable[OperationId],
        mac_addresses: Iterable[MacAddressStr],
    ) -> set[TransactionId]:
        """
        Resolve The Full Set Of TransactionIds From The Requested Inputs.
        """
        selected: set[TransactionId] = set()
        txn_db = self._load_json(self._src_transaction_db_path)

        for tid in transaction_ids:
            tid_str = str(tid)
            if tid_str in txn_db:
                selected.add(TransactionId(tid_str))
            else:
                self.logger.warning(
                    "Requested TransactionId '%s' not found in transaction DB", tid_str
                )

        for op in operation_ids:
            op_tid_list = self.operation_resolver.get_transaction_ids_for_operation(op)
            if not op_tid_list:
                self.logger.warning(
                    "No transactions found for OperationId '%s'", op
                )
                continue
            for tid in op_tid_list:
                tid_str = str(tid)
                if tid_str in txn_db:
                    selected.add(TransactionId(tid_str))

        for mac_str in mac_addresses:
            try:
                mac_obj = MacAddress(str(mac_str))
            except ValueError:
                self.logger.warning(
                    "Skipping invalid MAC address input: %s", mac_str
                )
                continue

            records = self.transaction_store.get_file_info_via_macaddress(mac_obj)
            if not records:
                self.logger.warning(
                    "No transactions found for MAC address '%s'", mac_str
                )
                continue

            for rec in records:
                tid_val = getattr(rec, "transaction_id", "")
                if tid_val and tid_val in txn_db:
                    selected.add(TransactionId(tid_val))

        return selected

    def _sanitize_and_copy_transactions(
        self,
        txn_ids: set[TransactionId],
        sanitize_mac: bool,
        sanitize_sysdescr: bool,
    ) -> dict[TransactionId, dict[str, object]]:
        """
        Sanitize Transaction Records And Copy PNM Files Into Support Tree.

        Returns
        -------
        Dict[TransactionId, Dict[str, object]]
            New transaction DB mapping for the support bundle.
        """
        src_db = self._load_json(self._src_transaction_db_path)
        sanitized_db: dict[TransactionId, dict[str, object]] = {}

        dest_pnm_dir = self.support_root / Path(SystemConfigSettings.pnm_dir())
        dest_pnm_dir.mkdir(parents=True, exist_ok=True)

        for tid in sorted(txn_ids, key=str):
            tid_str = str(tid)
            raw_rec = src_db.get(tid_str)
            if not isinstance(raw_rec, dict):
                self.logger.warning(
                    "TransactionId '%s' missing or malformed in DB; skipping", tid_str
                )
                continue

            rec: dict[str, object] = dict(raw_rec)

            mac_value = str(rec.get("mac_address", ""))
            old_mac_norm = self._normalize_mac_str(mac_value)
            filename = str(rec.get("filename", "")).strip()
            if not filename:
                self.logger.warning(
                    "TransactionId '%s' has no filename; skipping file copy", tid_str
                )

            if sanitize_mac and filename and old_mac_norm:
                new_filename = self._rewrite_filename_mac(filename, old_mac_norm)
            else:
                new_filename = filename

            if filename:
                src_capture = self._src_pnm_dir / filename
                if src_capture.exists():
                    dest_capture = dest_pnm_dir / new_filename
                    dest_capture.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(src_capture, dest_capture)
                    self._vprint(f"Copied capture: {src_capture} -> {dest_capture}")
                    self._run_mac_updater(dest_capture, sanitize_mac=sanitize_mac)
                else:
                    self.logger.warning(
                        "PNM file '%s' for TransactionId '%s' not found at '%s'",
                        filename,
                        tid_str,
                        src_capture,
                    )

            sanitized_rec: dict[str, object] = dict(rec)

            if sanitize_mac:
                sanitized_rec["mac_address"] = str(self._new_mac)
                sanitized_rec["filename"] = new_filename
            else:
                sanitized_rec["mac_address"] = rec.get("mac_address", "")
                sanitized_rec["filename"] = filename

            if sanitize_sysdescr:
                device_details_obj = rec.get("device_details") or {}
                device_details: dict[str, object]
                if isinstance(device_details_obj, dict):
                    device_details = dict(device_details_obj)
                else:
                    device_details = {}
                device_details["system_description"] = dict(SYSTEM_DESCRIPTION)
                sanitized_rec["device_details"] = device_details
            else:
                if "device_details" in rec:
                    sanitized_rec["device_details"] = rec["device_details"]
                else:
                    sanitized_rec.pop("device_details", None)

            sanitized_db[tid] = sanitized_rec

        return sanitized_db

    def _trim_capture_group_db(
        self,
        selected_txn_ids: set[TransactionId],
    ) -> dict[GroupId, dict[str, object]]:
        """
        Build A Trimmed Capture Group DB Containing Only Selected Transactions.
        """
        src_cg = self._load_json(self._src_capture_group_db_path)
        trimmed: dict[GroupId, dict[str, object]] = {}

        selected_strs: set[str] = {str(tid) for tid in selected_txn_ids}

        for group_id_str, rec_obj in src_cg.items():
            if not isinstance(rec_obj, dict):
                continue

            group_id = GroupId(group_id_str)
            txns_obj = rec_obj.get("transactions") or []
            if not isinstance(txns_obj, list):
                continue

            txns_list: list[str] = [str(t) for t in txns_obj if isinstance(t, str) and t]
            filtered = [t for t in txns_list if t in selected_strs]
            if not filtered:
                continue

            new_rec: dict[str, object] = dict(rec_obj)
            new_rec["transactions"] = filtered
            trimmed[group_id] = new_rec

        return trimmed

    def _trim_operation_db(
        self,
        used_capture_group_ids: set[GroupId],
    ) -> dict[OperationId, dict[str, object]]:
        """
        Build A Trimmed Operation DB Containing Only Used Capture Groups.
        """
        src_op = self._load_json(self._src_operation_db_path)
        trimmed: dict[OperationId, dict[str, object]] = {}

        used_ids_str: set[str] = {str(gid) for gid in used_capture_group_ids}

        for op_id_str, rec_obj in src_op.items():
            if not isinstance(rec_obj, dict):
                continue
            cg_id = rec_obj.get("capture_group_id")
            if not isinstance(cg_id, str) or cg_id not in used_ids_str:
                continue
            op_id = OperationId(op_id_str)
            trimmed[op_id] = dict(rec_obj)

        return trimmed

    def _write_json_under_support_root(self, rel_path: Path, data: dict[object, object]) -> Path:
        """
        Write A JSON File Under The Support Root Using The Relative Path.
        """
        dest = self.support_root / rel_path
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(json.dumps(data, indent=2, sort_keys=True), encoding="utf-8")
        self._vprint(f"Wrote JSON: {dest}")
        return dest

    def build_bundle(
        self,
        transaction_ids: Iterable[TransactionId],
        operation_ids: Iterable[OperationId],
        mac_addresses: Iterable[MacAddressStr],
        clean_output: bool,
        sanitize_mac: bool,
        sanitize_sysdescr: bool,
    ) -> Path:
        """
        Build The Support Bundle ZIP For The Requested Selection.

        Returns
        -------
        Path
            Path to the created ZIP archive.
        """
        if clean_output and self.support_root.exists():
            shutil.rmtree(self.support_root)

        self.support_root.mkdir(parents=True, exist_ok=True)

        selected_txns = self._resolve_transactions(transaction_ids, operation_ids, mac_addresses)
        if not selected_txns:
            raise RuntimeError("No transactions resolved from the supplied IDs/MACs; nothing to bundle.")

        self._vprint(f"Resolved {len(selected_txns)} transaction(s) for support bundle")

        sanitized_txn_db = self._sanitize_and_copy_transactions(
            selected_txns,
            sanitize_mac=sanitize_mac,
            sanitize_sysdescr=sanitize_sysdescr,
        )
        self._write_json_under_support_root(
            self._src_transaction_db_path,
            sanitized_txn_db,
        )

        trimmed_cg_db = self._trim_capture_group_db(selected_txns)
        self._write_json_under_support_root(
            self._src_capture_group_db_path,
            trimmed_cg_db,
        )

        used_cg_ids: set[GroupId] = set(trimmed_cg_db.keys())
        trimmed_op_db = self._trim_operation_db(used_cg_ids)
        self._write_json_under_support_root(
            self._src_operation_db_path,
            trimmed_op_db,
        )

        files_to_zip: list[Path] = [
            p for p in self.support_root.rglob("*") if p.is_file()
        ]

        ArchiveManager.zip_files(
            files=files_to_zip,
            archive_path=self.output_zip,
            mode="w",
            compression="zipdeflated",
            arcbase=self.support_root,
            preserve_tree=True,
        )

        self._vprint(f"Support bundle created at: {self.output_zip}")
        return self.output_zip


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Build a sanitized PyPNM support bundle containing only the PNM files and\n"
            "transaction metadata relevant to the specified TransactionId(s), OperationId(s),\n"
            "and/or MAC address(es). The bundle is written as a ZIP with a .data tree that\n"
            "can be unpacked into a clean PyPNM environment."
        ),
    )
    parser.add_argument(
        "--transaction-id",
        dest="transaction_ids",
        action="append",
        help="TransactionId to include (may be specified multiple times).",
    )
    parser.add_argument(
        "--operation-id",
        dest="operation_ids",
        action="append",
        help="OperationId to include (may be specified multiple times).",
    )
    parser.add_argument(
        "--mac-address",
        dest="mac_addresses",
        action="append",
        help="MAC address to include (all related transactions will be bundled).",
    )
    parser.add_argument(
        "--output-zip",
        type=Path,
        default=Path("pypnm_support_bundle.zip"),
        help="Name or path of the output ZIP archive (default: pypnm_support_bundle.zip).",
    )
    parser.add_argument(
        "--support-root",
        type=Path,
        default=Path(".support_bundle"),
        help="Temporary root directory for constructing the .data tree (default: .support_bundle).",
    )
    parser.add_argument(
        "--mac-updater",
        type=Path,
        default=None,
        help=(
            "Optional path to pnm-mac-updater.py for rewriting the binary MAC in copied PNM files. "
            "If omitted, only JSON metadata and filenames are sanitized."
        ),
    )
    parser.add_argument(
        "--keep-original-mac",
        action="store_true",
        help=(
            "Preserve original MAC addresses in JSON and filenames, and skip binary MAC rewriting. "
            "By default, MACs are sanitized to aa:bb:cc:dd:ee:ff."
        ),
    )
    parser.add_argument(
        "--keep-original-sysdescr",
        action="store_true",
        help=(
            "Preserve original device_details.system_description. "
            "By default, sysDescr fields are sanitized to the generic LANCity/LCPET-3 template."
        ),
    )
    parser.add_argument(
        "--clean-output",
        action="store_true",
        help="Remove any existing support-root directory before building the bundle.",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging.",
    )
    return parser.parse_args(argv)


def main(argv: list[str]) -> int:
    args = parse_args(argv)

    transaction_ids: list[TransactionId] = [
        TransactionId(t) for t in (args.transaction_ids or [])
    ]
    operation_ids: list[OperationId] = [
        OperationId(o) for o in (args.operation_ids or [])
    ]
    mac_addresses: list[MacAddressStr] = [
        cast(MacAddressStr, m) for m in (args.mac_addresses or [])
    ]

    if not transaction_ids and not operation_ids and not mac_addresses:
        print(
            "ERROR: At least one of --transaction-id, --operation-id, or --mac-address "
            "must be provided.",
            file=sys.stderr,
        )
        return 1

    # Ensure issues/ exists and place the ZIP there for relative paths
    issues_dir = Path("issues")
    issues_dir.mkdir(parents=True, exist_ok=True)

    output_zip: Path = args.output_zip
    if not output_zip.is_absolute():
        output_zip = issues_dir / output_zip.name

    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    sanitize_mac = not args.keep_original_mac
    sanitize_sysdescr = not args.keep_original_sysdescr

    builder = SupportBundleBuilder(
        support_root=args.support_root,
        output_zip=output_zip,
        mac_updater=args.mac_updater,
        verbose=args.verbose,
    )

    try:
        bundle_path = builder.build_bundle(
            transaction_ids=transaction_ids,
            operation_ids=operation_ids,
            mac_addresses=mac_addresses,
            clean_output=args.clean_output,
            sanitize_mac=sanitize_mac,
            sanitize_sysdescr=sanitize_sysdescr,
        )
    except Exception as exc:
        logging.getLogger("SupportBundle").error("Failed to build support bundle: %s", exc)
        return 1

    print(f"Support bundle created at: {bundle_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
