#!/usr/bin/env python3
"""Remove case-duplicate institution codes from SQLite (e.g. MOCU + MoCU).

MySQL treats institution.code as unique case-insensitively; SQLite does not.
Run this before backfill/parity if verify_catalogue_parity reports missing codes.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def main() -> int:
    from mwongozo_smart.data import sqlite_store
    from mwongozo_smart.data.guidebook_data import _CATALOG_PROGRAMMES
    from mwongozo_smart.data.institutions import _DEFAULT_INSTITUTIONS
    from mwongozo_smart.db.catalogue_merge import (
        dedupe_institutions_case_insensitive,
        normalize_programmes_institution_codes,
    )

    preferred = frozenset(i.code for i in _DEFAULT_INSTITUTIONS)
    institutions = sqlite_store.load_institutions(_DEFAULT_INSTITUTIONS, seed_defaults=False)
    programmes = sqlite_store.load_programmes(_CATALOG_PROGRAMMES, seed_defaults=False)

    before = len(institutions)
    institutions, alias_map = dedupe_institutions_case_insensitive(
        institutions, preferred_codes=preferred
    )
    programmes = normalize_programmes_institution_codes(programmes, alias_map)

    removed = before - len(institutions)
    if removed == 0:
        print("No duplicate institution codes in SQLite.")
        return 0

    canonical_codes = {item.code for item in institutions}
    programme_codes = {item.code for item in programmes}

    with sqlite_store._connect() as connection:
        for (code,) in connection.execute("SELECT code FROM institutions"):
            if code not in canonical_codes:
                connection.execute("DELETE FROM institutions WHERE code = ?", (code,))
        for (code,) in connection.execute("SELECT code FROM programmes"):
            if code not in programme_codes:
                connection.execute("DELETE FROM programmes WHERE code = ?", (code,))
        connection.commit()

    sqlite_store.seed_institutions(institutions)
    sqlite_store.seed_programmes(programmes)

    db_path = sqlite_store.DB_PATH
    merged_cache = 0
    with sqlite_store._connect() as connection:
        rows = list(
            connection.execute("SELECT institution_code, payload, updated_at FROM live_programme_cache")
        )
        by_upper: dict[str, list] = {}
        for code, payload, updated_at in rows:
            by_upper.setdefault(code.upper(), []).append((code, payload, updated_at))

        for variants in by_upper.values():
            if len(variants) <= 1:
                continue
            canonical = alias_map.get(variants[0][0].upper()) or variants[0][0].upper()
            canonical = alias_map.get(canonical, canonical)
            merged_payload: dict = {}
            latest = 0.0
            for code, payload, updated_at in variants:
                if code != canonical:
                    connection.execute(
                        "DELETE FROM live_programme_cache WHERE institution_code = ?",
                        (code,),
                    )
                    merged_cache += 1
                data = json.loads(payload)
                merged_payload.update(data)
                latest = max(latest, float(updated_at))
            connection.execute(
                """INSERT INTO live_programme_cache (institution_code, payload, updated_at)
                   VALUES (?, ?, ?)
                   ON CONFLICT(institution_code) DO UPDATE SET
                     payload = excluded.payload,
                     updated_at = excluded.updated_at""",
                (canonical, json.dumps(merged_payload, ensure_ascii=False), latest or time.time()),
            )
        connection.commit()

    print(f"Removed {removed} duplicate institution row(s); now {len(institutions)} institutions.")
    if merged_cache:
        print(f"Merged {merged_cache} duplicate live_programme_cache key(s).")
    print("Re-run: python scripts/backfill_catalogue_to_mysql.py")
    print("Then:  python scripts/verify_catalogue_parity.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
