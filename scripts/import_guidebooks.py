#!/usr/bin/env python3
"""Copy TCU guidebook JSON exports into data/guidebooks/ for catalog loading."""

from __future__ import annotations

import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TARGET_DIR = ROOT / "data" / "guidebooks"

SOURCES = [
    (
        "guidebook_2025_2026.json",
        Path.home() / "Downloads" / "Admission Guidebook for Holders of Secondary School Qualifications_2025_2026.json",
    ),
    (
        "guidebook_2024_2025.json",
        Path.home() / "Downloads" / "Admission Guidebook for Holders of Secondary School Qualifications_2024_2025.json",
    ),
    (
        "guidebook_2023_2024.json",
        Path.home() / "Downloads" / "Admission Guidebook for Holders of Secondary School Qualifications_2023_2024.json",
    ),
]


def main() -> None:
    TARGET_DIR.mkdir(parents=True, exist_ok=True)
    copied = 0
    for name, source in SOURCES:
        if not source.exists():
            print(f"skip (missing): {source}")
            continue
        dest = TARGET_DIR / name
        shutil.copy2(source, dest)
        print(f"copied -> {dest}")
        copied += 1
    if not copied:
        print("No guidebook JSON found in Downloads. Place exports in:")
        for _, source in SOURCES:
            print(f"  - {source}")
        return
    print(f"Done. {copied} file(s) ready for parser.")


if __name__ == "__main__":
    main()
