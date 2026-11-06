#!/usr/bin/env python3
"""Read-only physical TrustOS comparison; not a patch security audit."""
import argparse
import hashlib
from pathlib import Path
import sys
from assemble_trustos import SIZE


def compare(stock, derived, readback):
    if len(stock) != SIZE or len(readback) != SIZE:
        raise ValueError("Stock and readback must both be complete 6-MiB physical images")
    if not 512 <= len(derived) <= SIZE:
        raise ValueError("Derived image has invalid length")
    if any(data[:4] != b"DHTB" for data in (stock, derived, readback)):
        raise ValueError("Expected DHTB images")
    expected = derived + stock[len(derived):]
    if readback != expected:
        raise ValueError("Physical readback mismatch (including preserved tail)")
    return hashlib.sha256(expected).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("stock-raw", "derived", "readback"):
        parser.add_argument("--" + name, type=Path, required=True)
    args = parser.parse_args()
    try:
        result = compare(args.stock_raw.read_bytes(), args.derived.read_bytes(), args.readback.read_bytes())
        print("PASS full physical bytes; sha256=" + result)
        print("This does not establish that the derived payload is safe or bootable.")
    except (OSError, ValueError) as exc:
        print("FAIL: " + str(exc), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
