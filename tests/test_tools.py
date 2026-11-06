"""Synthetic/offline tests. No device, credentials or firmware inputs."""
import contextlib
import io
from pathlib import Path
import struct
import sys
import tempfile
import unittest
import zlib

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from assemble_trustos import SIZE, assemble
from compare_trustos import compare
from validate_backup import validate


class TrustOSTests(unittest.TestCase):
    def setUp(self):
        self.stock = b"DHTB" + b"\0" * (SIZE - 4)

    def test_assemble(self):
        self.assertEqual(assemble(self.stock[:1024], self.stock[512:], self.stock[:4096]), self.stock)

    def test_short_tail(self):
        with self.assertRaises(ValueError):
            assemble(self.stock[:512], b"x", self.stock[:4096])

    def test_prefix_mismatch(self):
        with self.assertRaises(ValueError):
            assemble(self.stock[:512], self.stock[512:], b"DHTB" + b"x" * 600)

    def test_comparison_keeps_tail(self):
        patch = b"DHTB" + b"p" * 1020
        expected = patch + self.stock[len(patch):]
        self.assertEqual(len(compare(self.stock, patch, expected)), 64)
        with self.assertRaises(ValueError):
            compare(self.stock, patch, expected[:-1] + b"x")

    def test_overwrite_refused(self):
        import assemble_trustos
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            inputs = {"head": self.stock[:512], "tail": self.stock[512:], "signed": self.stock[:4096], "output": b"keep"}
            args = ["assemble_trustos.py"]
            for name, data in inputs.items():
                path = root / name
                path.write_bytes(data)
                args += ["--" + name, str(path)]
            old = sys.argv
            sys.argv = args
            try:
                with contextlib.redirect_stderr(io.StringIO()):
                    self.assertEqual(assemble_trustos.main(), 1)
            finally:
                sys.argv = old
            self.assertEqual((root / "output").read_bytes(), b"keep")


class BackupTests(unittest.TestCase):
    def fixture(self, root):
        names = ["misc", "init_boot_a"] + [f"part{i}" for i in range(78)]
        xml = "<Partitions>" + "".join(f'<Partition id="{n}" size="1"/>' for n in names + ["userdata", "cache", "blackbox"]) + "</Partitions>"
        (root / "partition_list.xml").write_text(xml)
        for name in names:
            (root / name).write_bytes(b"x")
        misc = bytearray(2080)
        control = bytearray(32)
        control[:8] = b"_a\0\0BCAB"
        struct.pack_into("<I", control, 28, zlib.crc32(control[:28]))
        misc[2048:2080] = control
        (root / "misc").write_bytes(misc)
        image = bytearray(8 * 1024 * 1024)
        image[:8] = b"ANDROID!"
        struct.pack_into("<I", image, 12, 4)
        struct.pack_into("<I", image, 40, 4)
        image[4096:4100] = bytes.fromhex("02214c18")
        image[8192:8196] = b"AVB0"
        image[-64:-60] = b"AVBf"
        struct.pack_into(">IIQQQ", image, len(image) - 60, 1, 0, 8192, 8192, 4)
        (root / "init_boot_a").write_bytes(image)
        log = root / "receipts.txt"
        log.write_text("Device is using slot a\n" + "\n".join(f"Read Part Done: {n}+0x0, target: 0x{(root / n).stat().st_size:x}, read: 0x{(root / n).stat().st_size:x}" for n in names))
        return log

    def test_valid_synthetic_layout(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            result = validate(root, self.fixture(root))
            self.assertEqual(result["targets"], 80)
            self.assertEqual(result["active_slot"], "a")

    def test_missing_receipt(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            log = self.fixture(root)
            log.write_text(log.read_text().replace("Read Part Done: part77+0x0, target: 0x1, read: 0x1", ""))
            with self.assertRaisesRegex(ValueError, "Missing target"):
                validate(root, log)

    def test_undersized_receipt_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            log = self.fixture(root)
            log.write_text(log.read_text().replace("target: 0x800000, read: 0x800000", "target: 0x1, read: 0x1"))
            with self.assertRaisesRegex(ValueError, "Receipt smaller"):
                validate(root, log)

    def test_crc_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            log = self.fixture(root)
            misc = bytearray((root / "misc").read_bytes())
            misc[-1] ^= 1
            (root / "misc").write_bytes(misc)
            with self.assertRaisesRegex(ValueError, "CRC"):
                validate(root, log)

    def test_unsafe_xml_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            log = self.fixture(root)
            xml = root / "partition_list.xml"
            xml.write_text(xml.read_text().replace('id="part0"', 'id="../part0"'))
            with self.assertRaisesRegex(ValueError, "unsafe"):
                validate(root, log)


if __name__ == "__main__":
    unittest.main()
