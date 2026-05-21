from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any

from mwongozo_smart.db.config import mysql_database, mysql_host, mysql_password, mysql_port, mysql_user


def migrations_dir() -> Path:
    return Path(__file__).resolve().parent.parent.parent / "migrations" / "mysql"


def apply_sql_file(connection: Any, path: Path) -> None:
    sql = path.read_text(encoding="utf-8")
    statements = [chunk.strip() for chunk in sql.split(";") if chunk.strip()]
    with connection.cursor() as cursor:
        for statement in statements:
            cursor.execute(statement)
    connection.commit()


def apply_catalogue_schema(connection: Any) -> None:
    schema_path = migrations_dir() / "001_catalogue.sql"
    if not schema_path.is_file():
        raise FileNotFoundError(f"Missing MySQL schema: {schema_path}")
    apply_sql_file(connection, schema_path)


@contextmanager
def mysql_connection(*, autocommit: bool = False) -> Iterator[Any]:
    try:
        import pymysql
    except ImportError as exc:
        raise RuntimeError("Install pymysql to use MySQL (pip install pymysql).") from exc

    connection = pymysql.connect(
        host=mysql_host(),
        port=mysql_port(),
        user=mysql_user(),
        password=mysql_password(),
        database=mysql_database(),
        charset="utf8mb4",
        autocommit=autocommit,
        cursorclass=pymysql.cursors.DictCursor,
        connect_timeout=3,
        read_timeout=10,
        write_timeout=10,
    )
    try:
        yield connection
    finally:
        connection.close()


def mysql_ping() -> bool:
    try:
        with mysql_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1 AS ok")
                row = cursor.fetchone()
            return bool(row and row.get("ok") == 1)
    except Exception:
        return False


def mysql_table_exists(table_name: str) -> bool:
    try:
        with mysql_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT COUNT(*) AS n
                    FROM information_schema.tables
                    WHERE table_schema = %s AND table_name = %s
                    """,
                    (mysql_database(), table_name),
                )
                row = cursor.fetchone()
        return bool(row and int(row["n"]) > 0)
    except Exception:
        return False


def mysql_catalogue_status() -> tuple[bool, str]:
    """Return (ready, message). Ready means schema exists and institutions has rows."""
    if not mysql_ping():
        return False, "MySQL haipatikani — washa MySQL kwenye XAMPP na angalia MYSQL_* env."

    required = ("institutions", "programmes", "programme_requirements")
    missing = [name for name in required if not mysql_table_exists(name)]
    if missing:
        return (
            False,
            f"Jedwali halipo kwenye database '{mysql_database()}': {', '.join(missing)}. "
            "Endesha: python scripts/backfill_catalogue_to_mysql.py",
        )

    try:
        with mysql_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute("SELECT COUNT(*) AS c FROM institutions WHERE deleted_at IS NULL")
                institution_count = int(cursor.fetchone()["c"])
    except Exception as exc:
        return False, f"Imeshindwa kusoma institutions: {exc}"

    if institution_count == 0:
        return (
            False,
            f"Database '{mysql_database()}' ipo lakini haija jazwa. "
            "Endesha: python scripts/backfill_catalogue_to_mysql.py",
        )

    return True, f"catalogue ready ({institution_count} institutions)"


def mysql_catalogue_counts() -> dict[str, int] | None:
    """Row counts for phpMyAdmin cross-check; None if MySQL unavailable."""
    if not mysql_ping():
        return None
    if not mysql_table_exists("institutions"):
        return {"institutions": 0, "programmes": 0, "programme_requirements": 0}
    try:
        with mysql_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute("SELECT COUNT(*) AS c FROM institutions WHERE deleted_at IS NULL")
                institutions = int(cursor.fetchone()["c"])
                cursor.execute("SELECT COUNT(*) AS c FROM programmes WHERE deleted_at IS NULL")
                programmes = int(cursor.fetchone()["c"])
                cursor.execute("SELECT COUNT(*) AS c FROM programme_requirements")
                requirements = int(cursor.fetchone()["c"])
        return {
            "institutions": institutions,
            "programmes": programmes,
            "programme_requirements": requirements,
        }
    except Exception:
        return None
