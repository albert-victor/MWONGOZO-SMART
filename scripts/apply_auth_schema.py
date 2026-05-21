#!/usr/bin/env python3
"""Apply auth tables to MySQL (or local SQLite fallback)."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from mwongozo_smart.services import auth_store
from mwongozo_smart.services.auth_service import seed_demo_user_if_empty


def main() -> int:
    auth_store.ensure_auth_schema()
    seed_demo_user_if_empty()
    print("Auth schema ready. Demo user: student@mwongozo.test / Mwongozo2026!")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
