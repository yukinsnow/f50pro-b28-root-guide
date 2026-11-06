#!/usr/bin/env python3
"""Read-only, case-specific backup checks. No USB, subprocess or network."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import struct
import sys
import zlib
import xml.etree.ElementTree as ET

EXCLUDED = {"userdata", "cache", "blackbox"}
RECEIPT = re.compile(r"Read Part Done: ([^+\r\n]+)\+0x([0-9a-f]+), target: 0x([0-9a-f]+), read: 0x([0-9a-f]+)", re.I)


def digest(path):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(4 * 1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def validate(directory, log):
    directory = Path(directory).resolve()
    table = ET.parse(directory / "partition_list.xml").getroot()
    ids = [p.attrib["id"] for p in table]
    if len(ids) != len(set(ids)) or any(not re.fullmatch(r"[A-Za-z0-9_-]+", n) for n in ids):
        raise ValueError("Duplicate or unsafe partition ID")
    names = set(ids) - EXCLUDED
    if len(names) != 80:
        raise ValueError("Not the audited 80-target layout; manual review required")
    manifest = {}
    for name in sorted(names):
        path = directory / name
        if path.is_symlink() or not path.is_file() or path.stat().st_size <= 0:
            raise ValueError("Missing/empty/linked target: " + name)
        manifest[name] = {"bytes": path.stat().st_size, "sha256": digest(path)}
    text = Path(log).read_text(encoding="utf-8", errors="replace")
    records = [(n, int(o, 16), int(t, 16), int(r, 16)) for n, o, t, r in RECEIPT.findall(text)]
    if any(t != r or t <= 0 for n, o, t, r in records if n in names and o == 0):
        raise ValueError("Incomplete target receipt")
    done = {n for n, o, t, r in records if o == 0 and t == r and r > 0}
    # A receipt cannot claim fewer bytes than the file attributed to that read.
    # Larger receipts are possible for documented NV-header/DHTB trimming only;
    # those remain explicit manual-review conditions, not automatic size proof.
    for name in names & done:
        sizes = [r for n, o, t, r in records if n == name and o == 0 and t == r and r > 0]
        if max(sizes) < manifest[name]["bytes"]:
            raise ValueError("Receipt smaller than target file: " + name)
    missing = names - done
    alias = []
    if missing == {"nr_runtimenv1"}:
        nvsize = 35 * 1024 * 1024 - 512
        count = sum(n == "nr_runtimenv2" and o == 0 and t == r == nvsize for n, o, t, r in records)
        if manifest["nr_runtimenv1"]["bytes"] != nvsize or count < 2:
            raise ValueError("Runtime-NV alias is not independently accounted for")
        alias = ["nr_runtimenv1 -> nr_runtimenv2 (two full receipts)"]
    elif missing:
        raise ValueError("Missing target receipts: " + ", ".join(sorted(missing)))
    misc = (directory / "misc").read_bytes()
    control = misc[2048:2080]
    if len(control) != 32 or control[:8] != b"_a\0\0BCAB":
        raise ValueError("Not the audited active-A boot control")
    if zlib.crc32(control[:28]) != struct.unpack_from("<I", control, 28)[0]:
        raise ValueError("Boot control CRC mismatch")
    if "Device is using slot a" not in text or "Device is using slot b" in text:
        raise ValueError("Slot log missing or conflicting")
    image = (directory / "init_boot_a").read_bytes()
    if len(image) != 8 * 1024 * 1024 or image[:8] != b"ANDROID!":
        raise ValueError("Unexpected active init_boot image")
    if struct.unpack_from("<I", image, 40)[0] != 4 or struct.unpack_from("<I", image, 1580)[0] != 0:
        raise ValueError("Unsupported header/signature")
    size = struct.unpack_from("<I", image, 12)[0]
    if not 0 < size < len(image) - 4096 - 64 or image[4096:4100] != bytes.fromhex("02214c18"):
        raise ValueError("Unsupported ramdisk bounds/format")
    if image[-64:-60] != b"AVBf":
        raise ValueError("Missing AVB footer")
    major, minor, original, offset, count = struct.unpack_from(">IIQQQ", image, len(image) - 60)
    if major != 1 or offset % 4096 or offset < 4096 + size or count < 4 or offset + count >= len(image) - 64:
        raise ValueError("Invalid vbmeta bounds")
    if image[offset:offset + 4] != b"AVB0" or any(image[offset + count:-64]):
        raise ValueError("Unexpected vbmeta/padding")
    return {"checks_passed": True, "scope": "local files/receipts only; not restore or boot proof",
            "targets": len(names), "bytes": sum(v["bytes"] for v in manifest.values()),
            "active_slot": "a", "receipt_aliases": alias, "manifest": manifest}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    parser.add_argument("--log", type=Path, required=True)
    args = parser.parse_args()
    try:
        print(json.dumps(validate(args.directory, args.log), indent=2))
    except (OSError, ValueError, KeyError, ET.ParseError) as exc:
        print("FAIL: " + str(exc), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
