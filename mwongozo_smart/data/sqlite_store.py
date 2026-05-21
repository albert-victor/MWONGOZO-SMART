from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Callable, TypeVar

from mwongozo_smart.core.models import Institution, Programme

T = TypeVar("T")

DB_PATH = Path(__file__).with_name("mwongozo_smart.sqlite3")


def _unique_by_code(items: list[T]) -> list[T]:
    unique: dict[str, T] = {}
    for item in items:
        unique[getattr(item, "code")] = item
    return list(unique.values())


def _connect() -> sqlite3.Connection:
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def ensure_schema() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with _connect() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS institutions (
                code TEXT PRIMARY KEY,
                payload TEXT NOT NULL
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS programmes (
                code TEXT PRIMARY KEY,
                payload TEXT NOT NULL
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS live_programme_cache (
                institution_code TEXT PRIMARY KEY,
                payload TEXT NOT NULL,
                updated_at REAL NOT NULL
            )
            """
        )


def _seed_table(table: str, items: list[T], key_getter: Callable[[T], str]) -> None:
    ensure_schema()
    items = _unique_by_code(items)
    with _connect() as connection:
        for item in items:
            code = key_getter(item)
            connection.execute(
                f"""INSERT INTO {table} (code, payload) VALUES (?, ?)
                    ON CONFLICT(code) DO UPDATE SET payload = excluded.payload""",
                (code, json.dumps(item.model_dump(mode="json"), ensure_ascii=False)),
            )
        connection.commit()


def seed_institutions(items: list[Institution]) -> None:
    _seed_table("institutions", items, lambda item: item.code)


def delete_programmes_for_institution(
    institution_code: str,
    *,
    except_codes: frozenset[str] | None = None,
) -> int:
    """Remove cached programmes for an institution (e.g. after catalogue correction)."""
    ensure_schema()
    except_codes = except_codes or frozenset()
    removed = 0
    with _connect() as connection:
        rows = list(connection.execute("SELECT code, payload FROM programmes"))
        for row in rows:
            payload = json.loads(row["payload"])
            if payload.get("institution_code", "").upper() != institution_code.upper():
                continue
            if row["code"] in except_codes:
                continue
            connection.execute("DELETE FROM programmes WHERE code = ?", (row["code"],))
            removed += 1
        connection.commit()
    return removed


def purge_programmes_failing_institution_scope() -> int:
    from mwongozo_smart.data.institution_catalog import is_programme_allowed_for_institution

    ensure_schema()
    removed = 0
    with _connect() as connection:
        rows = list(connection.execute("SELECT code, payload FROM programmes"))
        for row in rows:
            programme = Programme.model_validate(json.loads(row["payload"]))
            if is_programme_allowed_for_institution(programme):
                continue
            connection.execute("DELETE FROM programmes WHERE code = ?", (row["code"],))
            removed += 1
        connection.commit()
    return removed


def seed_programmes(items: list[Programme]) -> None:
    _seed_table("programmes", items, lambda item: item.code)
    purge_programmes_failing_institution_scope()


def load_institutions(defaults: list[Institution] | None = None, *, seed_defaults: bool = True) -> list[Institution]:
    ensure_schema()
    defaults = _unique_by_code(list(defaults or []))
    if seed_defaults and defaults:
        seed_institutions(defaults)
    with _connect() as connection:
        rows = list(connection.execute("SELECT payload FROM institutions ORDER BY code"))
    if rows:
        loaded = [Institution.model_validate(json.loads(row["payload"])) for row in rows]
        default_by_code = {item.code: item for item in defaults}
        loaded_by_code = {item.code: item for item in loaded}
        merged: list[Institution] = []

        def merge(default_item: Institution, loaded_item: Institution) -> Institution:
            payload = default_item.model_dump()
            loaded_payload = loaded_item.model_dump()
            for key in ("code", "name", "city", "region", "website", "apply_url", "cta_label"):
                value = loaded_payload.get(key)
                if value not in (None, ""):
                    payload[key] = value
            return Institution.model_validate(payload)

        for default_item in defaults:
            loaded_item = loaded_by_code.get(default_item.code)
            merged.append(merge(default_item, loaded_item) if loaded_item else default_item)

        for item in loaded:
            if item.code not in default_by_code:
                merged.append(item)

        return merged
    return defaults


def load_programmes(defaults: list[Programme] | None = None, *, seed_defaults: bool = True) -> list[Programme]:
    ensure_schema()
    defaults = _unique_by_code(list(defaults or []))
    if seed_defaults and defaults:
        seed_programmes(defaults)
    with _connect() as connection:
        rows = list(connection.execute("SELECT payload FROM programmes ORDER BY code"))
    if rows:
        loaded = [Programme.model_validate(json.loads(row["payload"])) for row in rows]
        default_by_code = {item.code: item for item in defaults}
        loaded_by_code = {item.code: item for item in loaded}
        merged: list[Programme] = []

        def merge(default_item: Programme, loaded_item: Programme) -> Programme:
            payload = default_item.model_dump()
            loaded_payload = loaded_item.model_dump()
            # Institution and category always follow the curated catalogue (fixes stale DB rows).
            for key in (
                "code",
                "name",
                "institution_code",
                "institution_name",
                "city",
                "region",
                "category",
                "award_level",
            ):
                value = default_item.model_dump().get(key)
                if value not in (None, "", []):
                    payload[key] = value
            for key in ("duration_years", "capacity", "competition_tier", "tags"):
                value = loaded_payload.get(key)
                if value not in (None, "", []):
                    payload[key] = value
            return Programme.model_validate(payload)

        for default_item in defaults:
            loaded_item = loaded_by_code.get(default_item.code)
            merged.append(merge(default_item, loaded_item) if loaded_item else default_item)

        return merged
    return defaults


def set_live_programme_cache(institution_code: str, payload: dict[str, object]) -> None:
    import time

    ensure_schema()
    with _connect() as connection:
        connection.execute(
            """INSERT INTO live_programme_cache (institution_code, payload, updated_at)
               VALUES (?, ?, ?)
               ON CONFLICT(institution_code) DO UPDATE SET
                 payload = excluded.payload,
                 updated_at = excluded.updated_at""",
            (institution_code, json.dumps(payload, ensure_ascii=False), time.time()),
        )
        connection.commit()


def get_live_programme_cache(institution_code: str) -> dict[str, object] | None:
    ensure_schema()
    with _connect() as connection:
        row = connection.execute(
            "SELECT payload FROM live_programme_cache WHERE institution_code = ?",
            (institution_code,),
        ).fetchone()
    if not row:
        return None
    return json.loads(row["payload"])
