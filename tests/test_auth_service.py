from __future__ import annotations

import pytest

from mwongozo_smart.services import auth_store
from mwongozo_smart.services.auth_service import (
    hash_password,
    register_user,
    validate_email,
    validate_password,
    verify_password,
)


def test_validate_email_and_password() -> None:
    assert validate_email("bad") is not None
    assert validate_email("ok@example.com") is None
    assert validate_password("short") is not None
    assert validate_password("Mwongozo1") is None


def test_password_hash_roundtrip() -> None:
    hashed = hash_password("Mwongozo2026!")
    assert verify_password("Mwongozo2026!", hashed)
    assert not verify_password("wrong", hashed)


def test_register_and_profile_upsert_sqlite_fallback() -> None:
    auth_store.SQLITE_AUTH_PATH.unlink(missing_ok=True)
    result = register_user(email="tester@mwongozo.local", password="TestPass1", full_name="Tester")
    assert result["user"]["email"] == "tester@mwongozo.local"
    profile_id = auth_store.upsert_student_profile(
        session_id="sess-test-001",
        user_id=int(result["user"]["id"]),
        combination="PCM",
        exam_number="S1027/0034",
        exam_year=2024,
        source="recommend_form",
        pathway="a_level",
        input_snapshot={"pathway": "a_level"},
    )
    assert profile_id > 0
