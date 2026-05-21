from __future__ import annotations

import re
from typing import Any

import bcrypt

from mwongozo_smart.services import auth_store

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
    except ValueError:
        return False


def validate_email(email: str) -> str | None:
    value = email.strip().lower()
    if not value or not _EMAIL_RE.match(value):
        return "Barua pepe si sahihi."
    return None


def validate_password(password: str) -> str | None:
    if len(password) < 8:
        return "Nenosiri lazima liwe angalau herufi 8."
    if not re.search(r"[A-Za-z]", password) or not re.search(r"\d", password):
        return "Nenosiri lazima liwe na herufi na nambari."
    return None


def register_user(*, email: str, password: str, full_name: str | None = None) -> dict[str, Any]:
    if err := validate_email(email):
        raise ValueError(err)
    if err := validate_password(password):
        raise ValueError(err)
    if auth_store.get_user_by_email(email):
        raise ValueError("Barua pepe tayari imesajiliwa.")
    user = auth_store.create_user(email=email, password_hash=hash_password(password), full_name=full_name)
    token = auth_store.create_auth_session(user["id"])
    return {"user": _public_user(user), "token": token}


def login_user(*, email: str, password: str, required_role: str | None = None) -> dict[str, Any]:
    if err := validate_email(email):
        raise ValueError(err)
    row = auth_store.get_user_by_email(email)
    if not row or not verify_password(password, row["password_hash"]):
        raise ValueError("Barua pepe au nenosiri si sahihi.")
    if required_role and row.get("role") != required_role:
        raise ValueError("Akaunti hii haina ruhusa ya kuingia hapa.")
    token = auth_store.create_auth_session(int(row["id"]))
    return {"user": _public_user(row), "token": token}


def logout_user(token: str | None) -> None:
    auth_store.delete_auth_session(token)


def resolve_user(token: str | None) -> dict[str, Any] | None:
    user_id = auth_store.get_user_id_for_token(token)
    if not user_id:
        return None
    return auth_store.get_user_by_id(user_id)


def _public_user(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": row["id"],
        "uuid": row.get("uuid"),
        "email": row["email"],
        "full_name": row.get("full_name"),
        "role": row.get("role", "student"),
        "preferred_language": row.get("preferred_language", "both"),
    }


def seed_demo_user_if_empty() -> None:
    auth_store.ensure_auth_schema()
    if not auth_store.get_user_by_email("student@mwongozo.test"):
        auth_store.create_user(
            email="student@mwongozo.test",
            password_hash=hash_password("Mwongozo2026!"),
            full_name="Mwanafunzi wa Demo",
            role="student",
        )
    if not auth_store.get_user_by_email("admin@mwongozo.test"):
        auth_store.create_user(
            email="admin@mwongozo.test",
            password_hash=hash_password("AdminMwongozo2026!"),
            full_name="Mwongozo Admin",
            role="admin",
        )
