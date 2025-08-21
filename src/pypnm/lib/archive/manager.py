# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia

from __future__ import annotations

import logging
from pypnm.lib.types import PathLike
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Literal

import tarfile
import zipfile

__all__ = ["ArchiveManager"]

class ArchiveManager:
    """
    Static utilities to archive/extract file collections using Python stdlib.

    Supported formats
    -----------------
    - zip  : appendable (modes "w" or "a"), compression = deflate/bzip2/lzma/store
    - tar  : fresh write each call (modes: tar, gztar=.tar.gz, bztar=.tar.bz2, xztar=.tar.xz)

    Security
    --------
    - extract() defends against path traversal ("../" or absolute paths).
    """

    _ZIP_COMP: Dict[str, int] = {
        "zipstore": zipfile.ZIP_STORED,
        "zipdeflated": zipfile.ZIP_DEFLATED,
        "zipbz2": zipfile.ZIP_BZIP2,
        "ziplzma": zipfile.ZIP_LZMA,
    }

    _TAR_MODE: Dict[str, str] = {
        "tar": "w",
        "gztar": "w:gz",
        "bztar": "w:bz2",
        "xztar": "w:xz",
    }

    _LOG = logging.getLogger("ArchiveManager")

    # ──────────────────────────────────────────────────────────────────────────
    # Detection / Listing
    # ──────────────────────────────────────────────────────────────────────────
    @staticmethod
    def detect_format(archive_path: PathLike) -> Optional[str]:
        """
        Guess format from file suffix.
        Returns one of: "zip","tar","gztar","bztar","xztar" or None.
        """
        p = Path(archive_path)
        suf = "".join(p.suffixes).lower()
        if suf.endswith(".zip"):
            return "zip"
        if suf.endswith(".tar.gz") or suf.endswith(".tgz"):
            return "gztar"
        if suf.endswith(".tar.bz2") or suf.endswith(".tbz2"):
            return "bztar"
        if suf.endswith(".tar.xz") or suf.endswith(".txz"):
            return "xztar"
        if suf.endswith(".tar"):
            return "tar"
        return None

    @staticmethod
    def list_contents(archive_path: PathLike, fmt: Optional[str] = None) -> List[str]:
        """
        Return member names in the archive.
        """
        fmt = fmt or ArchiveManager.detect_format(archive_path)
        if fmt == "zip":
            with zipfile.ZipFile(archive_path, "r") as zf:
                return zf.namelist()
        elif fmt in ArchiveManager._TAR_MODE:
            with tarfile.open(archive_path, "r:*") as tf:
                return [m.name for m in tf.getmembers()]
        raise ValueError(f"Unsupported or undetected archive format for: {archive_path}")

    # ──────────────────────────────────────────────────────────────────────────
    # Create archives
    # ──────────────────────────────────────────────────────────────────────────
    @staticmethod
    def zip_files(
        files: Iterable[PathLike],
        archive_path: PathLike,
        *,
        mode: Literal["w", "a"] = "w",
        compression: Literal["zipdeflated", "zipbz2", "ziplzma", "zipstore"] = "zipdeflated",
        arcbase: Optional[PathLike] = None,
        preserve_tree: bool = False,
        arcname_map: Optional[Dict[PathLike, str]] = None,
        skip_missing: bool = True,
        remove_duplicate_files: bool = True,
    ) -> Path:
        """
        Write (or append) files to a ZIP archive.

        arcname resolution order:
            arcname_map[src] -> relative_to(arcbase) if preserve_tree -> basename
        """
        comp = ArchiveManager._ZIP_COMP[compression]
        ap = Path(archive_path)
        ap.parent.mkdir(parents=True, exist_ok=True)

        if remove_duplicate_files:
            files = ArchiveManager.__remove_duplicates(files)   

        with zipfile.ZipFile(ap, mode=mode, compression=comp) as zf:
            for f in files:
                src = Path(f)
                if not src.exists():
                    if skip_missing:
                        ArchiveManager._LOG.warning("zip_files: missing: %s (skipped)", src)
                        continue
                    raise FileNotFoundError(src)

                if arcname_map and f in arcname_map:
                    arcname = arcname_map[f]  # type: ignore[index]
                elif preserve_tree and arcbase is not None:
                    try:
                        arcname = str(Path(src).resolve().relative_to(Path(arcbase).resolve()))
                    except Exception:
                        arcname = src.name
                else:
                    arcname = src.name

                zf.write(src, arcname)
        return ap

    @staticmethod
    def tar_files(
        files: Iterable[PathLike],
        archive_path: PathLike,
        *,
        fmt: Literal["tar", "gztar", "bztar", "xztar"] = "gztar",
        arcbase: Optional[PathLike] = None,
        preserve_tree: bool = False,
        arcname_map: Optional[Dict[PathLike, str]] = None,
        skip_missing: bool = True,
        overwrite: bool = True,
    ) -> Path:
        """
        Create a new tar-based archive (no append for compressed tars).

        fmt controls compression: tar|gztar|bztar|xztar
        """
        mode = ArchiveManager._TAR_MODE[fmt]
        ap = Path(archive_path)
        ap.parent.mkdir(parents=True, exist_ok=True)
        if overwrite and ap.exists():
            ap.unlink(missing_ok=True)

        with tarfile.open(ap, str(mode)) as tf:
            for f in files:
                src = Path(f)
                if not src.exists():
                    if skip_missing:
                        ArchiveManager._LOG.warning("tar_files: missing: %s (skipped)", src)
                        continue
                    raise FileNotFoundError(src)

                if arcname_map and f in arcname_map:
                    arcname = arcname_map[f]  # type: ignore[index]
                elif preserve_tree and arcbase is not None:
                    try:
                        arcname = str(Path(src).resolve().relative_to(Path(arcbase).resolve()))
                    except Exception:
                        arcname = src.name
                else:
                    arcname = src.name

                tf.add(src, arcname=arcname)
        return ap

    # ──────────────────────────────────────────────────────────────────────────
    # Extraction
    # ──────────────────────────────────────────────────────────────────────────
    @staticmethod
    def _is_safe_member(base_dir: Path, target_path: Path) -> bool:
        """
        Ensure target_path stays inside base_dir (prevents path traversal).
        """
        try:
            base_dir = base_dir.resolve(strict=False)
            target_path = target_path.resolve(strict=False)
            return str(target_path).startswith(str(base_dir))
        except Exception:
            return False

    @staticmethod
    def _safe_join(base: Path, name: str) -> Path:
        # Avoid absolute paths and drive letters; normalize
        name = name.replace("\\", "/")
        name = name.lstrip("/")  # drop leading slash
        return (base / name).resolve(strict=False)

    @staticmethod
    def extract(
        archive_path: PathLike,
        dest_dir: PathLike,
        *,
        fmt: Optional[str] = None,
        members: Optional[Iterable[str]] = None,
        overwrite: bool = True,
    ) -> List[Path]:
        """
        Extract archive into dest_dir with path traversal protection.

        - fmt auto-detected if not provided.
        - members can filter which names to extract.
        - overwrite=True will replace existing files; otherwise skips them.
        """
        ap = Path(archive_path)
        out = Path(dest_dir)
        out.mkdir(parents=True, exist_ok=True)
        fmt = fmt or ArchiveManager.detect_format(ap)

        extracted: List[Path] = []

        if fmt == "zip":
            with zipfile.ZipFile(ap, "r") as zf:
                names = members or zf.namelist()
                for name in names:
                    tgt = ArchiveManager._safe_join(out, name)
                    if not ArchiveManager._is_safe_member(out, tgt):
                        raise RuntimeError(f"Unsafe path in zip: {name}")
                    if tgt.exists() and not overwrite:
                        continue
                    if name.endswith("/"):
                        tgt.mkdir(parents=True, exist_ok=True)
                        continue
                    tgt.parent.mkdir(parents=True, exist_ok=True)
                    with zf.open(name) as src, open(tgt, "wb") as dst:
                        dst.write(src.read())
                    extracted.append(tgt)
            return extracted

        if fmt in ArchiveManager._TAR_MODE:
            with tarfile.open(ap, "r:*") as tf:
                all_members = tf.getmembers()
                sel = (
                    [m for m in all_members if m.name in set(members)]  # type: ignore[arg-type]
                    if members
                    else all_members
                )
                for m in sel:
                    # Normalize and validate
                    tgt = ArchiveManager._safe_join(out, m.name)
                    if not ArchiveManager._is_safe_member(out, tgt):
                        raise RuntimeError(f"Unsafe path in tar: {m.name}")
                    if m.isdir():
                        tgt.mkdir(parents=True, exist_ok=True)
                        continue
                    if tgt.exists() and not overwrite:
                        continue
                    tgt.parent.mkdir(parents=True, exist_ok=True)
                    src_file = tf.extractfile(m)
                    if src_file is None:
                        continue
                    with src_file as src, open(tgt, "wb") as dst:
                        dst.write(src.read())
                    extracted.append(tgt)
            return extracted

        raise ValueError(f"Unsupported or undetected archive format for: {archive_path}")

    @staticmethod
    def __remove_duplicates(files: Iterable[PathLike]) -> List[Path]:
        """Ensure each path exists and appears only once (order preserved)."""
        seen: set[Path] = set()
        out: List[Path] = []
        for f in files:
            p = Path(f)
            if not p.exists():
                raise FileNotFoundError(p)
            rp = p.resolve()
            if rp not in seen:
                seen.add(rp)
                out.append(rp)
        return out
