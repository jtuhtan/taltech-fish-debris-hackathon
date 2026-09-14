#!/usr/bin/env python3
"""Write a deterministic SHA-256 manifest for every release payload file."""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            value.update(chunk)
    return value.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("dataset", type=Path)
    args = parser.parse_args()
    root = args.dataset.resolve()
    output = root / "SHA256SUMS"
    files = sorted(path for path in root.rglob("*") if path.is_file() and path != output)
    lines = [f"{digest(path)}  {path.relative_to(root).as_posix()}" for path in files]
    output.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    print(f"Wrote {output} with {len(lines)} entries")


if __name__ == "__main__":
    main()
