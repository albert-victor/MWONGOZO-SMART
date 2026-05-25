#!/usr/bin/env python3
"""Backfill MySQL catalogue tables from the current SQLite merged catalogue.

Usage (XAMPP MySQL running, database created):
  set MYSQL_DATABASE=mwongozo_smart
  python scripts/backfill_catalogue_to_mysql.py

Optional:
  python scripts/backfill_catalogue_to_mysql.py --dry-run
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def main() -> int:
    parser = argparse.ArgumentParser(description="Backfill MySQL catalogue from SQLite.")
    parser.add_argument("--dry-run", action="store_true", help="Count rows only; do not write MySQL.")
    args = parser.parse_args()

    from mwongozo_smart.data import sqlite_store
    from mwongozo_smart.data.guidebook_data import _CATALOG_PROGRAMMES
    from mwongozo_smart.data.institutions import _DEFAULT_INSTITUTIONS
    from mwongozo_smart.db.catalogue_merge import dedupe_institutions_case_insensitive
    from mwongozo_smart.db.repositories.catalogue import MysqlCatalogueStore
    from mwongozo_smart.db.session import mysql_ping

    if not mysql_ping():
        print("ERROR: MySQL is not reachable. Check XAMPP, database name, and MYSQL_* env vars.")
        return 1

    institutions = sqlite_store.load_institutions(_DEFAULT_INSTITUTIONS, seed_defaults=True)
    programmes = sqlite_store.load_programmes(_CATALOG_PROGRAMMES, seed_defaults=True)
    raw_inst = len(institutions)
    preferred = frozenset(i.code for i in _DEFAULT_INSTITUTIONS)
    institutions, alias_map = dedupe_institutions_case_insensitive(
        institutions, preferred_codes=preferred
    )
    if raw_inst != len(institutions):
        print(
            f"Collapsed {raw_inst - len(institutions)} duplicate institution code(s) "
            f"(case variants) before MySQL upsert."
        )
        if alias_map:
            collapsed = sorted({k for k, v in alias_map.items() if k != v and k.upper() == v})
            if collapsed:
                print(f"  Aliases -> canonical: {', '.join(f'{k}->{alias_map[k]}' for k in collapsed[:12])}")
    print(f"Loaded {len(institutions)} institutions, {len(programmes)} programmes from SQLite.")

    if args.dry_run:
        print("Dry run — no MySQL writes.")
        return 0

    store = MysqlCatalogueStore()
    store.ensure_schema()
    n_inst = store.upsert_institutions(institutions)
    n_prog = store.upsert_programmes(programmes)
    print(f"Upserted {n_inst} institutions, {n_prog} programmes into MySQL.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
