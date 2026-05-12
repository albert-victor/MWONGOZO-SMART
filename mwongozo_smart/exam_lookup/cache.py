from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

from mwongozo_smart.exam_lookup.models import NectaAcseeResult, NectaCseeResult, NectaSchoolLink

DEFAULT_CSEE_CACHE_PATH = Path(__file__).resolve().parent.parent / "data" / "necta_csee_cache.sqlite3"
DEFAULT_ACSEE_CACHE_PATH = Path(__file__).resolve().parent.parent / "data" / "necta_acsee_cache.sqlite3"


class NectaLookupCache:
    def __init__(self, db_path: Path | None = None) -> None:
        self._db_path = db_path or DEFAULT_CSEE_CACHE_PATH

    def _connect(self) -> sqlite3.Connection:
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(self._db_path)
        connection.row_factory = sqlite3.Row
        return connection

    def ensure_schema(self) -> None:
        with self._connect() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS necta_csee_results (
                    exam_year INTEGER NOT NULL,
                    candidate_norm TEXT NOT NULL,
                    payload TEXT NOT NULL,
                    fetched_at TEXT NOT NULL DEFAULT (datetime('now')),
                    PRIMARY KEY (exam_year, candidate_norm)
                );
                CREATE TABLE IF NOT EXISTS necta_centre_index (
                    exam_year INTEGER NOT NULL,
                    center_number TEXT NOT NULL,
                    school_name TEXT NOT NULL,
                    result_href TEXT NOT NULL,
                    source_page TEXT NOT NULL DEFAULT '',
                    indexed_at TEXT NOT NULL DEFAULT (datetime('now')),
                    PRIMARY KEY (exam_year, center_number)
                );
                """
            )
            connection.commit()

    def get_result(self, exam_year: int, candidate_norm: str) -> NectaCseeResult | None:
        self.ensure_schema()
        with self._connect() as connection:
            row = connection.execute(
                "SELECT payload FROM necta_csee_results WHERE exam_year = ? AND candidate_norm = ?",
                (exam_year, candidate_norm),
            ).fetchone()
        if not row:
            return None
        return NectaCseeResult.model_validate_json(row["payload"])

    def put_result(self, exam_year: int, candidate_norm: str, result: NectaCseeResult) -> None:
        self.ensure_schema()
        payload = result.model_dump_json()
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO necta_csee_results (exam_year, candidate_norm, payload, fetched_at)
                VALUES (?, ?, ?, datetime('now'))
                ON CONFLICT(exam_year, candidate_norm) DO UPDATE SET
                    payload = excluded.payload,
                    fetched_at = excluded.fetched_at
                """,
                (exam_year, candidate_norm, payload),
            )
            connection.commit()

    def upsert_school_links(self, exam_year: int, links: list[NectaSchoolLink], source_page: str) -> int:
        self.ensure_schema()
        count = 0
        with self._connect() as connection:
            for link in links:
                connection.execute(
                    """
                    INSERT INTO necta_centre_index (exam_year, center_number, school_name, result_href, source_page, indexed_at)
                    VALUES (?, ?, ?, ?, ?, datetime('now'))
                    ON CONFLICT(exam_year, center_number) DO UPDATE SET
                        school_name = excluded.school_name,
                        result_href = excluded.result_href,
                        source_page = excluded.source_page,
                        indexed_at = excluded.indexed_at
                    """,
                    (exam_year, link.center_number, link.school_name, link.result_href, source_page),
                )
                count += 1
            connection.commit()
        return count

    def list_school_links(self, exam_year: int) -> list[NectaSchoolLink]:
        self.ensure_schema()
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT center_number, school_name, result_href FROM necta_centre_index WHERE exam_year = ? ORDER BY center_number",
                (exam_year,),
            ).fetchall()
        return [
            NectaSchoolLink(center_number=row["center_number"], school_name=row["school_name"], result_href=row["result_href"])
            for row in rows
        ]

    def clear_year(self, exam_year: int) -> None:
        self.ensure_schema()
        with self._connect() as connection:
            connection.execute("DELETE FROM necta_centre_index WHERE exam_year = ?", (exam_year,))
            connection.commit()

    def stats(self) -> dict[str, Any]:
        self.ensure_schema()
        with self._connect() as connection:
            centres = connection.execute("SELECT COUNT(*) FROM necta_centre_index").fetchone()[0]
            results = connection.execute("SELECT COUNT(*) FROM necta_csee_results").fetchone()[0]
        return {"centre_rows": centres, "cached_results": results}


class NectaAcseeCache:
    """SQLite cache for ACSEE centre index rows and per-candidate parsed payloads."""

    def __init__(self, db_path: Path | None = None) -> None:
        self._db_path = db_path or DEFAULT_ACSEE_CACHE_PATH

    def _connect(self) -> sqlite3.Connection:
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(self._db_path)
        connection.row_factory = sqlite3.Row
        return connection

    def ensure_schema(self) -> None:
        with self._connect() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS necta_acsee_results (
                    exam_year INTEGER NOT NULL,
                    candidate_norm TEXT NOT NULL,
                    payload TEXT NOT NULL,
                    fetched_at TEXT NOT NULL DEFAULT (datetime('now')),
                    PRIMARY KEY (exam_year, candidate_norm)
                );
                CREATE TABLE IF NOT EXISTS necta_acsee_centre_index (
                    exam_year INTEGER NOT NULL,
                    center_number TEXT NOT NULL,
                    school_name TEXT NOT NULL,
                    result_href TEXT NOT NULL,
                    source_page TEXT NOT NULL DEFAULT '',
                    indexed_at TEXT NOT NULL DEFAULT (datetime('now')),
                    PRIMARY KEY (exam_year, center_number)
                );
                """
            )
            connection.commit()

    def get_result(self, exam_year: int, candidate_norm: str) -> NectaAcseeResult | None:
        self.ensure_schema()
        with self._connect() as connection:
            row = connection.execute(
                "SELECT payload FROM necta_acsee_results WHERE exam_year = ? AND candidate_norm = ?",
                (exam_year, candidate_norm),
            ).fetchone()
        if not row:
            return None
        return NectaAcseeResult.model_validate_json(row["payload"])

    def put_result(self, exam_year: int, candidate_norm: str, result: NectaAcseeResult) -> None:
        self.ensure_schema()
        payload = result.model_dump_json()
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO necta_acsee_results (exam_year, candidate_norm, payload, fetched_at)
                VALUES (?, ?, ?, datetime('now'))
                ON CONFLICT(exam_year, candidate_norm) DO UPDATE SET
                    payload = excluded.payload,
                    fetched_at = excluded.fetched_at
                """,
                (exam_year, candidate_norm, payload),
            )
            connection.commit()

    def upsert_school_links(self, exam_year: int, links: list[NectaSchoolLink], source_page: str) -> int:
        self.ensure_schema()
        count = 0
        with self._connect() as connection:
            for link in links:
                connection.execute(
                    """
                    INSERT INTO necta_acsee_centre_index (exam_year, center_number, school_name, result_href, source_page, indexed_at)
                    VALUES (?, ?, ?, ?, ?, datetime('now'))
                    ON CONFLICT(exam_year, center_number) DO UPDATE SET
                        school_name = excluded.school_name,
                        result_href = excluded.result_href,
                        source_page = excluded.source_page,
                        indexed_at = excluded.indexed_at
                    """,
                    (exam_year, link.center_number, link.school_name, link.result_href, source_page),
                )
                count += 1
            connection.commit()
        return count

    def list_school_links(self, exam_year: int) -> list[NectaSchoolLink]:
        self.ensure_schema()
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT center_number, school_name, result_href FROM necta_acsee_centre_index WHERE exam_year = ? ORDER BY center_number",
                (exam_year,),
            ).fetchall()
        return [
            NectaSchoolLink(center_number=row["center_number"], school_name=row["school_name"], result_href=row["result_href"])
            for row in rows
        ]

    def stats(self) -> dict[str, Any]:
        self.ensure_schema()
        with self._connect() as connection:
            centres = connection.execute("SELECT COUNT(*) FROM necta_acsee_centre_index").fetchone()[0]
            results = connection.execute("SELECT COUNT(*) FROM necta_acsee_results").fetchone()[0]
        return {"centre_rows": centres, "cached_results": results, "db_path": str(self._db_path)}
