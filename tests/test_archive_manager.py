
from __future__ import annotations

# SPDX-License-Identifier: MIT
import io
import os
import unittest
from pathlib import Path

from pypnm.lib.archive.manager import ArchiveManager

def write_files(base: Path, mapping: dict[str, str]) -> list[Path]:
    """Create files under base with given {relative_path: content} and return Paths."""
    paths: list[Path] = []
    for rel, content in mapping.items():
        p = base / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
        paths.append(p)
    return paths


class TestArchiveManager(unittest.TestCase):
    def setUp(self) -> None:
        # Simpler: just make a per-test temp dir
        import tempfile
        self.workdir = Path(tempfile.mkdtemp(prefix="archmgr_"))

    def tearDown(self) -> None:
        # Clean up the temp directory tree
        if self.workdir and self.workdir.exists():
            for root, dirs, files in os.walk(self.workdir, topdown=False):
                for name in files:
                    try:
                        Path(root, name).unlink()
                    except Exception:
                        pass
                for name in dirs:
                    try:
                        Path(root, name).rmdir()
                    except Exception:
                        pass
            try:
                self.workdir.rmdir()
            except Exception:
                pass

    # ───────────────────────── Detect format ─────────────────────────
    def test_detect_format(self):
        cases = {
            "x.zip": "zip",
            "x.tar": "tar",
            "x.tar.gz": "gztar",
            "x.tgz": "gztar",
            "x.tar.bz2": "bztar",
            "x.tbz2": "bztar",
            "x.tar.xz": "xztar",
            "x.txz": "xztar",
            "x.unknown": None,
        }
        for name, expected in cases.items():
            ap = self.workdir / name
            ap.touch()
            with self.subTest(name=name):
                self.assertEqual(ArchiveManager.detect_format(ap), expected)

    # ───────────────────────── ZIP flow ─────────────────────────
    def test_zip_create_list_extract(self):
        src_dir = self.workdir / "src"
        files = write_files(src_dir, {"a.txt": "AAA", "dir/b.txt": "BBB"})
        zip_path = self.workdir / "bundle.zip"

        # create with preserved tree
        ArchiveManager.zip_files(
            files,
            zip_path,
            mode="w",
            compression="zipdeflated",
            arcbase=src_dir,
            preserve_tree=True,
        )
        names = ArchiveManager.list_contents(zip_path, fmt="zip")
        self.assertEqual(sorted(names), ["a.txt", "dir/b.txt"])

        # append another file
        c = src_dir / "c.md"
        c.write_text("# C", encoding="utf-8")
        ArchiveManager.zip_files([c], zip_path, mode="a")
        names2 = set(ArchiveManager.list_contents(zip_path, fmt="zip"))
        self.assertTrue({"a.txt", "dir/b.txt", "c.md"}.issubset(names2))

        # extract only b.txt
        out_dir = self.workdir / "out_zip"
        extracted = ArchiveManager.extract(zip_path, out_dir, members=["dir/b.txt"])
        self.assertEqual(extracted, [out_dir / "dir" / "b.txt"])
        self.assertEqual((out_dir / "dir" / "b.txt").read_text(encoding="utf-8"), "BBB")

    def test_zip_arcname_map_and_skip_missing(self):
        src_dir = self.workdir / "src2"
        paths = write_files(src_dir, {"x.csv": "x", "y.csv": "y"})
        missing = src_dir / "missing.bin"  # not created
        zip_path = self.workdir / "bundle2.zip"

        ArchiveManager.zip_files(
            files=[paths[0], paths[1], missing],
            archive_path=zip_path,
            arcname_map={paths[0]: "renamed.csv"},
            skip_missing=True,
        )
        names = set(ArchiveManager.list_contents(zip_path))
        self.assertIn("renamed.csv", names)
        self.assertIn("y.csv", names)
        self.assertNotIn("x.csv", names)

    # ───────────────────────── TAR flows ─────────────────────────
    def test_tar_create_and_extract_all_formats(self):
        # Determine supported formats (xz may be unavailable if lzma is missing)
        fmts = ["tar", "gztar", "bztar"]
        try:
            import lzma  # noqa: F401
            fmts.append("xztar")
        except Exception:
            pass

        for fmt in fmts:
            with self.subTest(fmt=fmt):
                src_dir = self.workdir / f"src_{fmt}"
                files = write_files(src_dir, {"a.bin": "A", "nested/b.bin": "B"})
                ext = {"tar": "tar", "gztar": "tar.gz", "bztar": "tar.bz2", "xztar": "tar.xz"}[fmt]
                tar_path = self.workdir / f"bundle.{ext}"

                ArchiveManager.tar_files(
                    files=files,
                    archive_path=tar_path,
                    fmt=fmt,
                    arcbase=src_dir,
                    preserve_tree=True,
                )
                names = set(ArchiveManager.list_contents(tar_path))
                self.assertTrue({"a.bin", "nested/b.bin"}.issubset(names))

                out_dir = self.workdir / f"out_{fmt}"
                extracted = ArchiveManager.extract(tar_path, out_dir)
                self.assertEqual((out_dir / "a.bin").read_text(encoding="utf-8"), "A")
                self.assertEqual((out_dir / "nested" / "b.bin").read_text(encoding="utf-8"), "B")
                self.assertGreaterEqual(len(extracted), 2)

    # ───────────────────────── Overwrite behavior ─────────────────────────
    def test_extract_overwrite_false_then_true(self):
        src_dir = self.workdir / "src_overwrite"
        files = write_files(src_dir, {"a.txt": "first"})
        z = self.workdir / "ow.zip"
        ArchiveManager.zip_files(files, z)

        out = self.workdir / "out_overwrite"
        out.mkdir(parents=True, exist_ok=True)
        (out / "a.txt").write_text("existing", encoding="utf-8")

        # no overwrite
        ArchiveManager.extract(z, out, overwrite=False)
        self.assertEqual((out / "a.txt").read_text(encoding="utf-8"), "existing")

        # overwrite
        ArchiveManager.extract(z, out, overwrite=True)
        self.assertEqual((out / "a.txt").read_text(encoding="utf-8"), "first")

    # ───────────────────────── Traversal protection ─────────────────────────
    def test_zip_traversal_protection_raises(self):
        import zipfile
        z = self.workdir / "evil.zip"
        with zipfile.ZipFile(z, "w") as zf:
            zf.writestr("../evil.txt", "EVIL")
        with self.assertRaises(RuntimeError):
            ArchiveManager.extract(z, self.workdir / "extract_zip")

    def test_tar_traversal_protection_raises(self):
        import tarfile
        t = self.workdir / "evil.tar"
        with tarfile.open(t, "w") as tf:
            data = b"EVIL"
            info = tarfile.TarInfo(name="../evil.txt")
            info.size = len(data)
            tf.addfile(info, io.BytesIO(data))
        with self.assertRaises(RuntimeError):
            ArchiveManager.extract(t, self.workdir / "extract_tar")

    # ───────────────────────── Error paths ─────────────────────────
    def test_list_contents_unsupported_format_raises(self):
        weird = self.workdir / "file.weird"
        weird.write_bytes(b"not an archive")
        with self.assertRaises(ValueError):
            ArchiveManager.list_contents(weird)

    def test_extract_unsupported_format_raises(self):
        weird = self.workdir / "file.weird"
        weird.write_bytes(b"nope")
        with self.assertRaises(ValueError):
            ArchiveManager.extract(weird, self.workdir / "out_weird")


if __name__ == "__main__":
    unittest.main(verbosity=2)
