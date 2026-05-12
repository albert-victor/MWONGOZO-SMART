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


def _seed_table(table: str, items: list[T], key_getter: Callable[[T], str]) -> None:
    ensure_schema()
    items = _unique_by_code(items)
    with _connect() as connection:
        existing = {
            row["code"]
            for row in connection.execute(f"SELECT code FROM {table}")
        }
        for item in items:
            code = key_getter(item)
            if code in existing:
                continue
            connection.execute(
                f"INSERT INTO {table} (code, payload) VALUES (?, ?)",
                (code, json.dumps(item.model_dump(mode="json"), ensure_ascii=False)),
            )
            existing.add(code)
        connection.commit()


def seed_institutions(items: list[Institution]) -> None:
    _seed_table("institutions", items, lambda item: item.code)


def seed_programmes(items: list[Programme]) -> None:
    _seed_table("programmes", items, lambda item: item.code)


def load_institutions(defaults: list[Institution] | None = None) -> list[Institution]:
    ensure_schema()
    defaults = _unique_by_code(list(defaults or []))
    if defaults:
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


def load_programmes(defaults: list[Programme] | None = None) -> list[Programme]:
    ensure_schema()
    defaults = _unique_by_code(list(defaults or []))
    if defaults:
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
            for key in ("code", "name", "institution_code", "institution_name", "city", "region", "category", "award_level", "duration_years", "capacity", "competition_tier", "tags"):
                value = loaded_payload.get(key)
                if value not in (None, "", []):
                    payload[key] = value
            return Programme.model_validate(payload)

        for default_item in defaults:
            loaded_item = loaded_by_code.get(default_item.code)
            merged.append(merge(default_item, loaded_item) if loaded_item else default_item)

        for item in loaded:
            if item.code not in default_by_code:
                merged.append(item)

        return merged
    return defaults
