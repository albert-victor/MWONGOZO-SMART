from __future__ import annotations

import hashlib
import json
import re
import secrets
import sqlite3
import uuid
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from mwongozo_smart.db.session import apply_sql_file, mysql_connection, mysql_ping, migrations_dir

SQLITE_AUTH_PATH = Path(__file__).resolve().parent.parent / "data" / "auth_local.sqlite3"
SESSION_DAYS = 14
_TOKEN_RE = re.compile(r"^[a-f0-9]{64}$", re.I)


def _utcnow() -> datetime:
    return datetime.now(UTC)


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _use_mysql() -> bool:
    try:
        return mysql_ping()
    except Exception:
        return False


def _sqlite_connect() -> sqlite3.Connection:
    SQLITE_AUTH_PATH.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(SQLITE_AUTH_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def _apply_sqlite_auth_schema(connection: sqlite3.Connection) -> None:
    connection.executescript(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            uuid TEXT NOT NULL UNIQUE,
            email TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            full_name TEXT,
            role TEXT NOT NULL DEFAULT 'student',
            preferred_language TEXT NOT NULL DEFAULT 'both',
            is_active INTEGER NOT NULL DEFAULT 1,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS auth_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            token_hash TEXT NOT NULL UNIQUE,
            user_id INTEGER NOT NULL,
            expires_at TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        );
        CREATE TABLE IF NOT EXISTS student_profiles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER UNIQUE,
            session_id TEXT NOT NULL UNIQUE,
            combination TEXT,
            exam_number TEXT,
            exam_year INTEGER,
            source TEXT NOT NULL DEFAULT 'recommend_form',
            pathway TEXT NOT NULL DEFAULT 'a_level',
            input_snapshot TEXT,
            last_recommend_at TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
        );
        CREATE TABLE IF NOT EXISTS saved_programmes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            session_id TEXT,
            programme_code TEXT NOT NULL,
            snapshot TEXT,
            saved_at TEXT NOT NULL,
            UNIQUE(user_id, programme_code),
            UNIQUE(session_id, programme_code),
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        );
        CREATE TABLE IF NOT EXISTS saved_recommendations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            session_id TEXT,
            title TEXT,
            input_snapshot TEXT,
            results_snapshot TEXT,
            recommend_count INTEGER NOT NULL DEFAULT 0,
            direct_count INTEGER NOT NULL DEFAULT 0,
            review_count INTEGER NOT NULL DEFAULT 0,
            saved_at TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        );
        CREATE INDEX IF NOT EXISTS idx_saved_reco_user ON saved_recommendations(user_id, saved_at DESC);
        """
    )
    connection.commit()


def ensure_auth_schema() -> None:
    if _use_mysql():
        with mysql_connection() as connection:
            apply_sql_file(connection, migrations_dir() / "002_auth.sql")
            apply_sql_file(connection, migrations_dir() / "003_saved_recommendations.sql")
        return
    with _sqlite_connect() as connection:
        _apply_sqlite_auth_schema(connection)


def _row_user(row: Any) -> dict[str, Any]:
    return {
        "id": int(row["id"] if isinstance(row, dict) else row["id"]),
        "uuid": row["uuid"],
        "email": row["email"],
        "full_name": row.get("full_name") if isinstance(row, dict) else row["full_name"],
        "role": row["role"],
        "preferred_language": row.get("preferred_language") or "both",
    }


def create_user(
    *,
    email: str,
    password_hash: str,
    full_name: str | None = None,
    role: str = "student",
) -> dict[str, Any]:
    ensure_auth_schema()
    user_uuid = str(uuid.uuid4())
    now = _utcnow().isoformat()
    email_norm = email.strip().lower()
    safe_role = role if role in ("student", "staff", "admin") else "student"
    if _use_mysql():
        with mysql_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO users (uuid, email, password_hash, full_name, role, created_at, updated_at)
                    VALUES (%s, %s, %s, %s, %s, CURRENT_TIMESTAMP(3), CURRENT_TIMESTAMP(3))
                    """,
                    (user_uuid, email_norm, password_hash, full_name, safe_role),
                )
                user_id = int(cursor.lastrowid)
            connection.commit()
        return {
            "id": user_id,
            "uuid": user_uuid,
            "email": email_norm,
            "full_name": full_name,
            "role": safe_role,
            "preferred_language": "both",
        }
    with _sqlite_connect() as connection:
        cursor = connection.execute(
            """
            INSERT INTO users (uuid, email, password_hash, full_name, role, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (user_uuid, email_norm, password_hash, full_name, safe_role, now, now),
        )
        connection.commit()
        return {
            "id": int(cursor.lastrowid),
            "uuid": user_uuid,
            "email": email_norm,
            "full_name": full_name,
            "role": safe_role,
            "preferred_language": "both",
        }


def get_user_by_email_and_role(email: str, role: str) -> dict[str, Any] | None:
    row = get_user_by_email(email)
    if not row:
        return None
    if row.get("role") != role:
        return None
    return row


def get_user_by_email(email: str) -> dict[str, Any] | None:
    ensure_auth_schema()
    email_norm = email.strip().lower()
    if _use_mysql():
        with mysql_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute("SELECT * FROM users WHERE email = %s AND is_active = 1", (email_norm,))
                row = cursor.fetchone()
        return ({**_row_user(row), "password_hash": row["password_hash"]}) if row else None
    with _sqlite_connect() as connection:
        row = connection.execute("SELECT * FROM users WHERE email = ? AND is_active = 1", (email_norm,)).fetchone()
        if not row:
            return None
        payload = dict(row)
        return _row_user(payload) | {"password_hash": payload["password_hash"]}


def get_user_by_id(user_id: int) -> dict[str, Any] | None:
    ensure_auth_schema()
    if _use_mysql():
        with mysql_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute("SELECT * FROM users WHERE id = %s AND is_active = 1", (user_id,))
                row = cursor.fetchone()
        return _row_user(row) if row else None
    with _sqlite_connect() as connection:
        row = connection.execute("SELECT * FROM users WHERE id = ? AND is_active = 1", (user_id,)).fetchone()
        return _row_user(dict(row)) if row else None


def create_auth_session(user_id: int) -> str:
    ensure_auth_schema()
    token = secrets.token_hex(32)
    token_hash = _hash_token(token)
    expires = _utcnow() + timedelta(days=SESSION_DAYS)
    if _use_mysql():
        with mysql_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO auth_sessions (token_hash, user_id, expires_at)
                    VALUES (%s, %s, %s)
                    """,
                    (token_hash, user_id, expires.strftime("%Y-%m-%d %H:%M:%S")),
                )
            connection.commit()
        return token
    with _sqlite_connect() as connection:
        connection.execute(
            "INSERT INTO auth_sessions (token_hash, user_id, expires_at, created_at) VALUES (?, ?, ?, ?)",
            (token_hash, user_id, expires.isoformat(), _utcnow().isoformat()),
        )
        connection.commit()
    return token


def get_user_id_for_token(token: str | None) -> int | None:
    if not token or not _TOKEN_RE.match(token.strip()):
        return None
    ensure_auth_schema()
    token_hash = _hash_token(token.strip())
    now = _utcnow()
    if _use_mysql():
        with mysql_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT user_id, expires_at FROM auth_sessions
                    WHERE token_hash = %s
                    """,
                    (token_hash,),
                )
                row = cursor.fetchone()
        if not row:
            return None
        expires = row["expires_at"]
        if expires < now.replace(tzinfo=None):
            return None
        return int(row["user_id"])
    with _sqlite_connect() as connection:
        row = connection.execute(
            "SELECT user_id, expires_at FROM auth_sessions WHERE token_hash = ?",
            (token_hash,),
        ).fetchone()
        if not row:
            return None
        expires = datetime.fromisoformat(row["expires_at"])
        if expires.tzinfo is None:
            expires = expires.replace(tzinfo=UTC)
        if expires < now:
            return None
        return int(row["user_id"])


def delete_auth_session(token: str | None) -> None:
    if not token:
        return
    token_hash = _hash_token(token.strip())
    if _use_mysql():
        with mysql_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute("DELETE FROM auth_sessions WHERE token_hash = %s", (token_hash,))
            connection.commit()
        return
    with _sqlite_connect() as connection:
        connection.execute("DELETE FROM auth_sessions WHERE token_hash = ?", (token_hash,))
        connection.commit()


def upsert_student_profile(
    *,
    session_id: str,
    user_id: int | None,
    combination: str | None,
    exam_number: str | None,
    exam_year: int | None,
    source: str,
    pathway: str,
    input_snapshot: dict[str, Any],
) -> int:
    ensure_auth_schema()
    payload_json = json.dumps(input_snapshot, ensure_ascii=False)
    if _use_mysql():
        with mysql_connection() as connection:
            with connection.cursor() as cursor:
                if user_id is not None:
                    cursor.execute(
                        "SELECT id FROM student_profiles WHERE user_id = %s",
                        (user_id,),
                    )
                    existing_user = cursor.fetchone()
                    if existing_user:
                        cursor.execute(
                            """
                            UPDATE student_profiles SET
                              session_id = %s, combination = %s, exam_number = %s, exam_year = %s,
                              source = %s, pathway = %s, input_snapshot = %s,
                              last_recommend_at = CURRENT_TIMESTAMP(3), updated_at = CURRENT_TIMESTAMP(3)
                            WHERE user_id = %s
                            """,
                            (session_id, combination, exam_number, exam_year, source, pathway, payload_json, user_id),
                        )
                        connection.commit()
                        return int(existing_user["id"])
                cursor.execute(
                    """
                    INSERT INTO student_profiles (
                        user_id, session_id, combination, exam_number, exam_year,
                        source, pathway, input_snapshot, last_recommend_at
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP(3))
                    ON DUPLICATE KEY UPDATE
                        user_id = COALESCE(VALUES(user_id), user_id),
                        combination = VALUES(combination),
                        exam_number = VALUES(exam_number),
                        exam_year = VALUES(exam_year),
                        source = VALUES(source),
                        pathway = VALUES(pathway),
                        input_snapshot = VALUES(input_snapshot),
                        last_recommend_at = CURRENT_TIMESTAMP(3),
                        updated_at = CURRENT_TIMESTAMP(3)
                    """,
                    (user_id, session_id, combination, exam_number, exam_year, source, pathway, payload_json),
                )
                profile_id = int(cursor.lastrowid)
            connection.commit()
        return profile_id
    now = _utcnow().isoformat()
    with _sqlite_connect() as connection:
        row = connection.execute(
            "SELECT id FROM student_profiles WHERE session_id = ?",
            (session_id,),
        ).fetchone()
        if row:
            connection.execute(
                """
                UPDATE student_profiles SET
                  user_id = ?, combination = ?, exam_number = ?, exam_year = ?,
                  source = ?, pathway = ?, input_snapshot = ?, last_recommend_at = ?, updated_at = ?
                WHERE session_id = ?
                """,
                (user_id, combination, exam_number, exam_year, source, pathway, payload_json, now, now, session_id),
            )
            connection.commit()
            return int(row["id"])
        cursor = connection.execute(
            """
            INSERT INTO student_profiles (
                user_id, session_id, combination, exam_number, exam_year,
                source, pathway, input_snapshot, last_recommend_at, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (user_id, session_id, combination, exam_number, exam_year, source, pathway, payload_json, now, now, now),
        )
        connection.commit()
        return int(cursor.lastrowid)


def attach_session_to_user(session_id: str, user_id: int) -> None:
    ensure_auth_schema()
    if _use_mysql():
        with mysql_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    "UPDATE student_profiles SET user_id = %s WHERE session_id = %s",
                    (user_id, session_id),
                )
                cursor.execute(
                    "UPDATE saved_programmes SET user_id = %s WHERE session_id = %s AND user_id IS NULL",
                    (user_id, session_id),
                )
            connection.commit()
        return
    with _sqlite_connect() as connection:
        connection.execute("UPDATE student_profiles SET user_id = ? WHERE session_id = ?", (user_id, session_id))
        connection.execute(
            "UPDATE saved_programmes SET user_id = ? WHERE session_id = ? AND user_id IS NULL",
            (user_id, session_id),
        )
        connection.commit()


def upsert_saved_programme(
    *,
    session_id: str | None,
    user_id: int | None,
    programme_code: str,
    snapshot: dict[str, Any],
) -> None:
    ensure_auth_schema()
    snap = json.dumps(snapshot, ensure_ascii=False)
    code = programme_code.strip()
    if not code:
        return
    if _use_mysql():
        with mysql_connection() as connection:
            with connection.cursor() as cursor:
                if user_id is not None:
                    cursor.execute(
                        """
                        INSERT INTO saved_programmes (user_id, session_id, programme_code, snapshot)
                        VALUES (%s, %s, %s, %s)
                        ON DUPLICATE KEY UPDATE snapshot = VALUES(snapshot), saved_at = CURRENT_TIMESTAMP(3)
                        """,
                        (user_id, session_id, code, snap),
                    )
                elif session_id:
                    cursor.execute(
                        """
                        INSERT INTO saved_programmes (user_id, session_id, programme_code, snapshot)
                        VALUES (NULL, %s, %s, %s)
                        ON DUPLICATE KEY UPDATE snapshot = VALUES(snapshot), saved_at = CURRENT_TIMESTAMP(3)
                        """,
                        (session_id, code, snap),
                    )
            connection.commit()
        return
    now = _utcnow().isoformat()
    with _sqlite_connect() as connection:
        if user_id is not None:
            connection.execute(
                """
                INSERT INTO saved_programmes (user_id, session_id, programme_code, snapshot, saved_at)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(user_id, programme_code) DO UPDATE SET snapshot = excluded.snapshot, saved_at = excluded.saved_at
                """,
                (user_id, session_id, code, snap, now),
            )
        elif session_id:
            connection.execute(
                """
                INSERT INTO saved_programmes (user_id, session_id, programme_code, snapshot, saved_at)
                VALUES (NULL, ?, ?, ?, ?)
                ON CONFLICT(session_id, programme_code) DO UPDATE SET snapshot = excluded.snapshot, saved_at = excluded.saved_at
                """,
                (session_id, code, snap, now),
            )
        connection.commit()


def list_saved_programmes(*, session_id: str | None, user_id: int | None) -> list[dict[str, Any]]:
    ensure_auth_schema()
    if _use_mysql():
        with mysql_connection() as connection:
            with connection.cursor() as cursor:
                if user_id is not None:
                    cursor.execute(
                        """
                        SELECT programme_code, snapshot, saved_at FROM saved_programmes
                        WHERE user_id = %s ORDER BY saved_at DESC
                        """,
                        (user_id,),
                    )
                elif session_id:
                    cursor.execute(
                        """
                        SELECT programme_code, snapshot, saved_at FROM saved_programmes
                        WHERE session_id = %s ORDER BY saved_at DESC
                        """,
                        (session_id,),
                    )
                else:
                    return []
                rows = cursor.fetchall()
    else:
        with _sqlite_connect() as connection:
            if user_id is not None:
                rows = connection.execute(
                    "SELECT programme_code, snapshot, saved_at FROM saved_programmes WHERE user_id = ? ORDER BY saved_at DESC",
                    (user_id,),
                ).fetchall()
            elif session_id:
                rows = connection.execute(
                    "SELECT programme_code, snapshot, saved_at FROM saved_programmes WHERE session_id = ? ORDER BY saved_at DESC",
                    (session_id,),
                ).fetchall()
            else:
                return []
    items: list[dict[str, Any]] = []
    for row in rows:
        snap = row["snapshot"]
        if isinstance(snap, str):
            snap = json.loads(snap)
        items.append(
            {
                "code": row["programme_code"],
                "snapshot": snap or {},
                "saved_at": str(row["saved_at"]),
            }
        )
    return items


def remove_saved_programme(*, session_id: str | None, user_id: int | None, programme_code: str) -> None:
    ensure_auth_schema()
    code = programme_code.strip()
    if _use_mysql():
        with mysql_connection() as connection:
            with connection.cursor() as cursor:
                if user_id is not None:
                    cursor.execute(
                        "DELETE FROM saved_programmes WHERE user_id = %s AND programme_code = %s",
                        (user_id, code),
                    )
                elif session_id:
                    cursor.execute(
                        "DELETE FROM saved_programmes WHERE session_id = %s AND programme_code = %s",
                        (session_id, code),
                    )
            connection.commit()
        return
    with _sqlite_connect() as connection:
        if user_id is not None:
            connection.execute("DELETE FROM saved_programmes WHERE user_id = ? AND programme_code = ?", (user_id, code))
        elif session_id:
            connection.execute(
                "DELETE FROM saved_programmes WHERE session_id = ? AND programme_code = ?",
                (session_id, code),
            )
        connection.commit()


def insert_saved_recommendation(
    *,
    user_id: int,
    session_id: str | None,
    title: str | None,
    input_snapshot: dict[str, Any],
    results_snapshot: dict[str, Any],
    recommend_count: int,
    direct_count: int,
    review_count: int,
) -> int:
    ensure_auth_schema()
    input_json = json.dumps(input_snapshot, ensure_ascii=False)
    results_json = json.dumps(results_snapshot, ensure_ascii=False)
    safe_title = (title or "").strip()[:255] or None
    if _use_mysql():
        with mysql_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO saved_recommendations (
                        user_id, session_id, title, input_snapshot, results_snapshot,
                        recommend_count, direct_count, review_count
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        user_id,
                        session_id,
                        safe_title,
                        input_json,
                        results_json,
                        int(recommend_count),
                        int(direct_count),
                        int(review_count),
                    ),
                )
                reco_id = int(cursor.lastrowid)
            connection.commit()
        return reco_id
    now = _utcnow().isoformat()
    with _sqlite_connect() as connection:
        cursor = connection.execute(
            """
            INSERT INTO saved_recommendations (
                user_id, session_id, title, input_snapshot, results_snapshot,
                recommend_count, direct_count, review_count, saved_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                user_id,
                session_id,
                safe_title,
                input_json,
                results_json,
                int(recommend_count),
                int(direct_count),
                int(review_count),
                now,
            ),
        )
        connection.commit()
        return int(cursor.lastrowid)


def list_saved_recommendations(*, user_id: int) -> list[dict[str, Any]]:
    ensure_auth_schema()
    if _use_mysql():
        with mysql_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT id, title, input_snapshot, results_snapshot,
                           recommend_count, direct_count, review_count, saved_at
                    FROM saved_recommendations
                    WHERE user_id = %s
                    ORDER BY saved_at DESC
                    """,
                    (user_id,),
                )
                rows = cursor.fetchall()
    else:
        with _sqlite_connect() as connection:
            rows = connection.execute(
                """
                SELECT id, title, input_snapshot, results_snapshot,
                       recommend_count, direct_count, review_count, saved_at
                FROM saved_recommendations
                WHERE user_id = ?
                ORDER BY saved_at DESC
                """,
                (user_id,),
            ).fetchall()
    items: list[dict[str, Any]] = []
    for row in rows:
        payload = dict(row)
        input_snap = payload.get("input_snapshot")
        results_snap = payload.get("results_snapshot")
        if isinstance(input_snap, str):
            input_snap = json.loads(input_snap)
        if isinstance(results_snap, str):
            results_snap = json.loads(results_snap)
        items.append(
            {
                "id": int(payload["id"]),
                "title": payload.get("title") or "",
                "input_snapshot": input_snap or {},
                "results_snapshot": results_snap or {},
                "recommend_count": int(payload.get("recommend_count") or 0),
                "direct_count": int(payload.get("direct_count") or 0),
                "review_count": int(payload.get("review_count") or 0),
                "saved_at": str(payload.get("saved_at") or ""),
            }
        )
    return items


def get_saved_recommendation(*, user_id: int, reco_id: int) -> dict[str, Any] | None:
    ensure_auth_schema()
    if _use_mysql():
        with mysql_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT id, title, input_snapshot, results_snapshot,
                           recommend_count, direct_count, review_count, saved_at
                    FROM saved_recommendations
                    WHERE user_id = %s AND id = %s
                    """,
                    (user_id, reco_id),
                )
                row = cursor.fetchone()
    else:
        with _sqlite_connect() as connection:
            row = connection.execute(
                """
                SELECT id, title, input_snapshot, results_snapshot,
                       recommend_count, direct_count, review_count, saved_at
                FROM saved_recommendations
                WHERE user_id = ? AND id = ?
                """,
                (user_id, reco_id),
            ).fetchone()
    if not row:
        return None
    payload = dict(row)
    input_snap = payload.get("input_snapshot")
    results_snap = payload.get("results_snapshot")
    if isinstance(input_snap, str):
        input_snap = json.loads(input_snap)
    if isinstance(results_snap, str):
        results_snap = json.loads(results_snap)
    return {
        "id": int(payload["id"]),
        "title": payload.get("title") or "",
        "input_snapshot": input_snap or {},
        "results_snapshot": results_snap or {},
        "recommend_count": int(payload.get("recommend_count") or 0),
        "direct_count": int(payload.get("direct_count") or 0),
        "review_count": int(payload.get("review_count") or 0),
        "saved_at": str(payload.get("saved_at") or ""),
    }


def remove_saved_recommendation(*, user_id: int, reco_id: int) -> None:
    ensure_auth_schema()
    if _use_mysql():
        with mysql_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    "DELETE FROM saved_recommendations WHERE user_id = %s AND id = %s",
                    (user_id, reco_id),
                )
            connection.commit()
        return
    with _sqlite_connect() as connection:
        connection.execute(
            "DELETE FROM saved_recommendations WHERE user_id = ? AND id = ?",
            (user_id, reco_id),
        )
        connection.commit()


def count_users() -> int:
    ensure_auth_schema()
    if _use_mysql():
        with mysql_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute("SELECT COUNT(*) AS c FROM users WHERE is_active = 1")
                return int(cursor.fetchone()["c"])
    with _sqlite_connect() as connection:
        return int(connection.execute("SELECT COUNT(*) FROM users WHERE is_active = 1").fetchone()[0])


def _row_user_admin(row: Any) -> dict[str, Any]:
    payload = dict(row) if not isinstance(row, dict) else row
    active = payload.get("is_active", 1)
    return _row_user(payload) | {
        "is_active": bool(int(active)),
        "created_at": str(payload.get("created_at") or ""),
        "updated_at": str(payload.get("updated_at") or ""),
    }


def list_users_for_admin(*, include_inactive: bool = True) -> list[dict[str, Any]]:
    ensure_auth_schema()
    sql = "SELECT * FROM users"
    if not include_inactive:
        sql += " WHERE is_active = 1"
    sql += " ORDER BY created_at DESC, id DESC"
    if _use_mysql():
        with mysql_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(sql)
                rows = cursor.fetchall()
        return [_row_user_admin(dict(row)) for row in rows]
    with _sqlite_connect() as connection:
        rows = connection.execute(sql).fetchall()
        return [_row_user_admin(dict(row)) for row in rows]


def get_user_by_id_admin(user_id: int) -> dict[str, Any] | None:
    ensure_auth_schema()
    if _use_mysql():
        with mysql_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
                row = cursor.fetchone()
        return _row_user_admin(dict(row)) if row else None
    with _sqlite_connect() as connection:
        row = connection.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        return _row_user_admin(dict(row)) if row else None


def update_user_record(
    user_id: int,
    *,
    email: str | None = None,
    full_name: str | None = None,
    role: str | None = None,
    is_active: bool | None = None,
    password_hash: str | None = None,
) -> dict[str, Any] | None:
    ensure_auth_schema()
    existing = get_user_by_id_admin(user_id)
    if not existing:
        return None
    email_norm = email.strip().lower() if email else None
    safe_role = role if role in ("student", "staff", "admin") else None
    now = _utcnow().isoformat()
    if _use_mysql():
        sets: list[str] = []
        params: list[Any] = []
        if email_norm:
            sets.append("email = %s")
            params.append(email_norm)
        if full_name is not None:
            sets.append("full_name = %s")
            params.append(full_name.strip() or None)
        if safe_role:
            sets.append("role = %s")
            params.append(safe_role)
        if is_active is not None:
            sets.append("is_active = %s")
            params.append(1 if is_active else 0)
        if password_hash:
            sets.append("password_hash = %s")
            params.append(password_hash)
        if not sets:
            return existing
        sets.append("updated_at = CURRENT_TIMESTAMP(3)")
        params.append(user_id)
        with mysql_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(f"UPDATE users SET {', '.join(sets)} WHERE id = %s", params)
            connection.commit()
        return get_user_by_id_admin(user_id)
    sets_sql: list[str] = []
    params_sql: list[Any] = []
    if email_norm:
        sets_sql.append("email = ?")
        params_sql.append(email_norm)
    if full_name is not None:
        sets_sql.append("full_name = ?")
        params_sql.append(full_name.strip() or None)
    if safe_role:
        sets_sql.append("role = ?")
        params_sql.append(safe_role)
    if is_active is not None:
        sets_sql.append("is_active = ?")
        params_sql.append(1 if is_active else 0)
    if password_hash:
        sets_sql.append("password_hash = ?")
        params_sql.append(password_hash)
    if not sets_sql:
        return existing
    sets_sql.append("updated_at = ?")
    params_sql.append(now)
    params_sql.append(user_id)
    with _sqlite_connect() as connection:
        connection.execute(f"UPDATE users SET {', '.join(sets_sql)} WHERE id = ?", params_sql)
        connection.commit()
    return get_user_by_id_admin(user_id)


def email_taken_by_other(email: str, exclude_user_id: int | None = None) -> bool:
    ensure_auth_schema()
    email_norm = email.strip().lower()
    if _use_mysql():
        with mysql_connection() as connection:
            with connection.cursor() as cursor:
                if exclude_user_id:
                    cursor.execute(
                        "SELECT id FROM users WHERE email = %s AND id <> %s LIMIT 1",
                        (email_norm, exclude_user_id),
                    )
                else:
                    cursor.execute("SELECT id FROM users WHERE email = %s LIMIT 1", (email_norm,))
                return cursor.fetchone() is not None
    with _sqlite_connect() as connection:
        if exclude_user_id:
            row = connection.execute(
                "SELECT id FROM users WHERE email = ? AND id <> ? LIMIT 1",
                (email_norm, exclude_user_id),
            ).fetchone()
        else:
            row = connection.execute("SELECT id FROM users WHERE email = ? LIMIT 1", (email_norm,)).fetchone()
        return row is not None


def count_users_by_role() -> dict[str, int]:
    ensure_auth_schema()
    if _use_mysql():
        with mysql_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT role, COUNT(*) AS c FROM users WHERE is_active = 1 GROUP BY role"
                )
                rows = cursor.fetchall()
        return {str(row["role"]): int(row["c"]) for row in rows}
    with _sqlite_connect() as connection:
        rows = connection.execute(
            "SELECT role, COUNT(*) AS c FROM users WHERE is_active = 1 GROUP BY role"
        ).fetchall()
        return {str(row["role"]): int(row["c"]) for row in rows}


def count_student_profiles() -> int:
    ensure_auth_schema()
    if _use_mysql():
        with mysql_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute("SELECT COUNT(*) AS c FROM student_profiles")
                return int(cursor.fetchone()["c"])
    with _sqlite_connect() as connection:
        return int(connection.execute("SELECT COUNT(*) FROM student_profiles").fetchone()[0])


def _row_user_admin(row: Any) -> dict[str, Any]:
    active = row.get("is_active") if isinstance(row, dict) else row["is_active"]
    if active is None:
        active = 1
    return _row_user(row) | {
        "is_active": bool(int(active)),
        "created_at": str(row.get("created_at") or row["created_at"] if not isinstance(row, dict) else row.get("created_at") or ""),
        "updated_at": str(row.get("updated_at") or row["updated_at"] if not isinstance(row, dict) else row.get("updated_at") or ""),
    }


def list_users_for_admin(*, include_inactive: bool = True) -> list[dict[str, Any]]:
    ensure_auth_schema()
    where = "" if include_inactive else " WHERE is_active = 1"
    if _use_mysql():
        with mysql_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(f"SELECT * FROM users{where} ORDER BY created_at DESC")
                rows = cursor.fetchall()
        return [_row_user_admin(row) for row in rows]
    with _sqlite_connect() as connection:
        rows = connection.execute(f"SELECT * FROM users{where} ORDER BY created_at DESC").fetchall()
        return [_row_user_admin(dict(row)) for row in rows]


def get_user_by_id_admin(user_id: int) -> dict[str, Any] | None:
    ensure_auth_schema()
    if _use_mysql():
        with mysql_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
                row = cursor.fetchone()
        return _row_user_admin(row) if row else None
    with _sqlite_connect() as connection:
        row = connection.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        return _row_user_admin(dict(row)) if row else None


def count_users_by_role() -> dict[str, int]:
    ensure_auth_schema()
    counts = {"student": 0, "staff": 0, "admin": 0}
    if _use_mysql():
        with mysql_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT role, COUNT(*) AS c FROM users WHERE is_active = 1 GROUP BY role"
                )
                rows = cursor.fetchall()
    else:
        with _sqlite_connect() as connection:
            rows = connection.execute(
                "SELECT role, COUNT(*) AS c FROM users WHERE is_active = 1 GROUP BY role"
            ).fetchall()
            rows = [dict(row) for row in rows]
    for row in rows:
        role = row["role"]
        if role in counts:
            counts[role] = int(row["c"])
    return counts


def update_user_record(
    user_id: int,
    *,
    email: str | None = None,
    full_name: str | None = None,
    role: str | None = None,
    is_active: bool | None = None,
    password_hash: str | None = None,
) -> dict[str, Any] | None:
    ensure_auth_schema()
    existing = get_user_by_id_admin(user_id)
    if not existing:
        return None
    email_norm = email.strip().lower() if email else None
    safe_role = role if role in ("student", "staff", "admin") else None
    now = _utcnow().isoformat()
    if _use_mysql():
        sets: list[str] = []
        params: list[Any] = []
        if email_norm:
            sets.append("email = %s")
            params.append(email_norm)
        if full_name is not None:
            sets.append("full_name = %s")
            params.append(full_name.strip() or None)
        if safe_role:
            sets.append("role = %s")
            params.append(safe_role)
        if is_active is not None:
            sets.append("is_active = %s")
            params.append(1 if is_active else 0)
        if password_hash:
            sets.append("password_hash = %s")
            params.append(password_hash)
        if not sets:
            return existing
        sets.append("updated_at = CURRENT_TIMESTAMP(3)")
        params.append(user_id)
        with mysql_connection() as connection:
            with connection.cursor() as cursor:
                if email_norm:
                    cursor.execute(
                        "SELECT id FROM users WHERE email = %s AND id <> %s",
                        (email_norm, user_id),
                    )
                    if cursor.fetchone():
                        raise ValueError("Barua pepe tayari inatumika.")
                cursor.execute(f"UPDATE users SET {', '.join(sets)} WHERE id = %s", params)
            connection.commit()
        return get_user_by_id_admin(user_id)
    sets_sqlite: list[str] = []
    params_sqlite: list[Any] = []
    if email_norm:
        sets_sqlite.append("email = ?")
        params_sqlite.append(email_norm)
    if full_name is not None:
        sets_sqlite.append("full_name = ?")
        params_sqlite.append(full_name.strip() or None)
    if safe_role:
        sets_sqlite.append("role = ?")
        params_sqlite.append(safe_role)
    if is_active is not None:
        sets_sqlite.append("is_active = ?")
        params_sqlite.append(1 if is_active else 0)
    if password_hash:
        sets_sqlite.append("password_hash = ?")
        params_sqlite.append(password_hash)
    if not sets_sqlite:
        return existing
    sets_sqlite.append("updated_at = ?")
    params_sqlite.append(now)
    params_sqlite.append(user_id)
    with _sqlite_connect() as connection:
        if email_norm:
            clash = connection.execute(
                "SELECT id FROM users WHERE email = ? AND id <> ?",
                (email_norm, user_id),
            ).fetchone()
            if clash:
                raise ValueError("Barua pepe tayari inatumika.")
        connection.execute(
            f"UPDATE users SET {', '.join(sets_sqlite)} WHERE id = ?",
            params_sqlite,
        )
        connection.commit()
    return get_user_by_id_admin(user_id)


def email_exists(email: str, *, exclude_user_id: int | None = None) -> bool:
    ensure_auth_schema()
    email_norm = email.strip().lower()
    if _use_mysql():
        with mysql_connection() as connection:
            with connection.cursor() as cursor:
                if exclude_user_id:
                    cursor.execute(
                        "SELECT id FROM users WHERE email = %s AND id <> %s",
                        (email_norm, exclude_user_id),
                    )
                else:
                    cursor.execute("SELECT id FROM users WHERE email = %s", (email_norm,))
                return cursor.fetchone() is not None
    with _sqlite_connect() as connection:
        if exclude_user_id:
            row = connection.execute(
                "SELECT id FROM users WHERE email = ? AND id <> ?",
                (email_norm, exclude_user_id),
            ).fetchone()
        else:
            row = connection.execute("SELECT id FROM users WHERE email = ?", (email_norm,)).fetchone()
        return row is not None
