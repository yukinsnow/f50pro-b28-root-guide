#!/usr/bin/env python3
"""Offline reconstruction of the audited 6-MiB TrustOS split read. Never flashes."""
import argparse
import hashlib
from pathlib import Path
import sys

SIZE = 6 * 1024 * 1024


def assemble(head, tail, signed):
    if len(head) < 512 or head[:4] != b"DHTB":
        raise ValueError("Missing complete DHTB header")
    if len(tail) != SIZE - 512:
        raise ValueError("Tail must be exactly 6 MiB minus 512 bytes")
    if not 512 <= len(signed) <= SIZE or signed[:4] != b"DHTB":
        raise ValueError("Invalid original signed image")
    raw = head[:512] + tail
    if raw[:len(signed)] != signed:
        raise ValueError("Reconstructed raw does not match original signed prefix")
    return raw


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("head", "tail", "signed", "output"):
        parser.add_argument("--" + name, type=Path, required=True)
    args = parser.parse_args()
    try:
        raw = assemble(args.head.read_bytes(), args.tail.read_bytes(), args.signed.read_bytes())
        # Exclusive creation: never truncate/replace an original or existing output.
        with args.output.open("xb") as stream:
            stream.write(raw)
        print("bytes=" + str(len(raw)))
        print("sha256=" + hashlib.sha256(raw).hexdigest())
        print("Local reconstruction only; receipts and recovery remain operator checks.")
    except (OSError, ValueError) as exc:
        print("FAIL: " + str(exc), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
