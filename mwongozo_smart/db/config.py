from __future__ import annotations

import os
from enum import Enum


class CatalogueReadMode(str, Enum):
    SQLITE = "sqlite"
    MYSQL = "mysql"
    SQLITE_WITH_MYSQL_VERIFY = "sqlite_with_mysql_verify"


class CatalogueWriteMode(str, Enum):
    SQLITE = "sqlite"
    MYSQL = "mysql"
    DUAL = "dual"


def _env(name: str, default: str) -> str:
    return os.environ.get(name, default).strip()


def catalogue_read_mode() -> CatalogueReadMode:
    raw = _env("MWONGOZO_CATALOGUE_READ", "sqlite").lower()
    try:
        return CatalogueReadMode(raw)
    except ValueError:
        return CatalogueReadMode.SQLITE


def catalogue_write_mode() -> CatalogueWriteMode:
    raw = _env("MWONGOZO_CATALOGUE_WRITE", "sqlite").lower()
    try:
        return CatalogueWriteMode(raw)
    except ValueError:
        return CatalogueWriteMode.SQLITE


def mysql_host() -> str:
    return _env("MYSQL_HOST", "127.0.0.1")


def mysql_port() -> int:
    return int(_env("MYSQL_PORT", "3306"))


def mysql_user() -> str:
    return _env("MYSQL_USER", "root")


def mysql_password() -> str:
    return _env("MYSQL_PASSWORD", "")


def mysql_database() -> str:
    return _env("MYSQL_DATABASE", "mwongozo_smart")


def mysql_configured() -> bool:
    return bool(mysql_database())


def catalogue_seed_on_startup() -> bool:
    """Skip re-upserting hundreds of rows on every server start when MySQL already has data."""
    raw = _env("MWONGOZO_CATALOGUE_SEED_ON_STARTUP", "").lower()
    if raw in ("1", "true", "yes", "on"):
        return True
    if raw in ("0", "false", "no", "off"):
        return False
    if catalogue_read_mode() == CatalogueReadMode.MYSQL:
        from mwongozo_smart.db.session import mysql_catalogue_status

        ready, _ = mysql_catalogue_status()
        return not ready
    return True
