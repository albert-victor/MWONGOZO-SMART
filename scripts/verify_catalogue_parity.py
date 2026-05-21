#!/usr/bin/env python3
"""Compare catalogue loaded from SQLite vs MySQL (canonical JSON per code).

Exit code 0 = parity OK, 1 = mismatches or MySQL unavailable.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _canonical_map(items: list, *, kind: str) -> dict[str, str]:
    out: dict[str, str] = {}
    for item in items:
        payload = item.model_dump(mode="json")
        if kind == "programmes":
            payload.pop("institution_name", None)
        out[item.code] = json.dumps(payload, sort_keys=True, ensure_ascii=False)
    return out


def _diff_maps(label: str, left: dict[str, str], right: dict[str, str]) -> list[str]:
    issues: list[str] = []
    left_codes = set(left)
    right_codes = set(right)
    missing = sorted(left_codes - right_codes)
    extra = sorted(right_codes - left_codes)
    if missing:
        issues.append(f"{label}: missing in MySQL ({len(missing)}): {missing[:5]}")
    if extra:
        issues.append(f"{label}: extra in MySQL ({len(extra)}): {extra[:5]}")
    for code in sorted(left_codes & right_codes):
        if left[code] != right[code]:
            issues.append(f"{label}: payload mismatch for {code}")
            if len(issues) >= 20:
                issues.append(f"{label}: ... more mismatches omitted")
                break
    return issues


def main() -> int:
    from mwongozo_smart.data.guidebook_data import _CATALOG_PROGRAMMES
    from mwongozo_smart.data.institutions import _DEFAULT_INSTITUTIONS
    from mwongozo_smart.db.config import CatalogueReadMode
    from mwongozo_smart.db.repositories.catalogue import CatalogueRepository
    from mwongozo_smart.db.session import mysql_catalogue_status, mysql_ping

    if not mysql_ping():
        print("ERROR: MySQL haipatikani — washa MySQL kwenye XAMPP.")
        return 1

    ready, status_message = mysql_catalogue_status()
    if not ready:
        print(f"ERROR: {status_message}")
        return 1
    print(f"MySQL: {status_message}")

    sqlite_repo = CatalogueRepository(read_mode=CatalogueReadMode.SQLITE, write_mode=CatalogueReadMode.SQLITE)
    mysql_repo = CatalogueRepository(read_mode=CatalogueReadMode.MYSQL, write_mode=CatalogueReadMode.SQLITE)

    sqlite_inst = sqlite_repo.load_institutions(_DEFAULT_INSTITUTIONS)
    mysql_inst = mysql_repo.load_institutions(_DEFAULT_INSTITUTIONS)
    sqlite_prog = sqlite_repo.load_programmes(_CATALOG_PROGRAMMES)
    mysql_prog = mysql_repo.load_programmes(_CATALOG_PROGRAMMES)

    issues = _diff_maps("institutions", _canonical_map(sqlite_inst, kind="institutions"), _canonical_map(mysql_inst, kind="institutions"))
    issues.extend(_diff_maps("programmes", _canonical_map(sqlite_prog, kind="programmes"), _canonical_map(mysql_prog, kind="programmes")))

    print(f"SQLite: {len(sqlite_inst)} institutions, {len(sqlite_prog)} programmes")
    print(f"MySQL:  {len(mysql_inst)} institutions, {len(mysql_prog)} programmes")

    if issues:
        print("PARITY FAILED:")
        for line in issues:
            print(f"  - {line}")
        return 1

    print("PARITY OK — SQLite and MySQL catalogues match.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
