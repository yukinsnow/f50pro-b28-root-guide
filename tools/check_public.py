#!/usr/bin/env python3
"""Conservative public-tree hygiene scan. No remote calls; not a DLP guarantee."""
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
PATTERNS = {
    "Windows user path": r"[A-Za-z]:\\Users\\[^\\\s]+",
    "private PEM": r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----",
    "ADB public key payload": r"\b[A-Za-z0-9+/]{500,}={0,2}(?:\s|$)",
    "GitHub token": r"\b(?:gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,})\b",
    "API secret": r"\bsk-[A-Za-z0-9_-]{20,}\b",
    "device network address": r"\b192\.168\.\d+\.\d+(?::\d+)?\b",
}
FORBIDDEN = {".img", ".bin", ".raw", ".apk", ".zip", ".7z", ".exe", ".dll", ".pem", ".key", ".log"}


def main():
    count, failures = 0, []
    for path in sorted(ROOT.rglob("*")):
        relative = path.relative_to(ROOT)
        if any(p in {".git", "__pycache__", ".venv"} for p in relative.parts) or not path.is_file():
            continue
        count += 1
        if path.suffix.lower() in FORBIDDEN or path.name.startswith("adbkey"):
            failures.append(str(relative) + ": forbidden artifact")
            continue
        try:
            content = path.read_text(encoding="utf-8")
        except UnicodeError:
            failures.append(str(relative) + ": non-text file")
            continue
        for label, pattern in PATTERNS.items():
            if re.search(pattern, content):
                failures.append(str(relative) + ": " + label)
    if failures:
        print("\n".join(failures))
        return 1
    print(f"PASS: {count} text files checked; no configured secret/artifact patterns found")
    return 0


if __name__ == "__main__":
    sys.exit(main())
