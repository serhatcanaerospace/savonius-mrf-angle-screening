#!/usr/bin/env python3
"""Repository structure checks for the Savonius MRF public repo."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    manifest = json.loads((ROOT / "cases.json").read_text(encoding="utf-8"))
    missing: list[str] = []
    for case in manifest["cases"]:
        case_dir = ROOT / case["path"]
        for rel in ("0", "constant", "system", "Allrun", "Allrun-pre", "Allclean"):
            path = case_dir / rel
            if not path.exists():
                missing.append(str(path.relative_to(ROOT)))
    if missing:
        print("Missing expected files:")
        for path in missing:
            print(f"  - {path}")
        return 1
    print("Savonius MRF public repo structure OK.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

