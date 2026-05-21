from __future__ import annotations

from fastapi.testclient import TestClient

from backend.app import app
from mwongozo_smart.services import auth_service, auth_store
from mwongozo_smart.services.admin_service import build_dashboard_overview


client = TestClient(app)


def _admin_login() -> None:
    auth_store.ensure_auth_schema()
    auth_service.seed_demo_user_if_empty()
    res = client.post(
        "/auth/admin/login",
        json={"email": "admin@mwongozo.test", "password": "AdminMwongozo2026!"},
    )
    assert res.status_code == 200


def test_admin_overview_requires_auth() -> None:
    res = client.get("/admin/api/overview")
    assert res.status_code == 401


def test_admin_overview_ok_for_admin() -> None:
    _admin_login()
    res = client.get("/admin/api/overview")
    assert res.status_code == 200
    data = res.json()
    assert data["catalogue"]["programmes"] >= 100
    assert "frequent_programmes" in data
    assert len(data["frequent_programmes"]) >= 5


def test_admin_users_crud() -> None:
    _admin_login()
    create = client.post(
        "/admin/api/users",
        json={
            "email": "crud.test@mwongozo.test",
            "password": "TestPass2026!",
            "full_name": "CRUD Test",
            "role": "student",
        },
    )
    assert create.status_code == 200
    user_id = create.json()["user"]["id"]

    listing = client.get("/admin/api/users")
    assert listing.status_code == 200
    emails = [u["email"] for u in listing.json()["items"]]
    assert "crud.test@mwongozo.test" in emails

    patch = client.patch(
        f"/admin/api/users/{user_id}",
        json={"full_name": "CRUD Updated", "role": "staff"},
    )
    assert patch.status_code == 200
    assert patch.json()["user"]["role"] == "staff"

    delete = client.delete(f"/admin/api/users/{user_id}")
    assert delete.status_code == 200
    assert delete.json()["user"]["is_active"] is False


def test_build_dashboard_has_synthetic_trends() -> None:
    data = build_dashboard_overview()
    assert len(data["trends"]["daily_recommendations"]) == 14
    assert data["users"]["total_display"] >= data["users"]["total_real"]
