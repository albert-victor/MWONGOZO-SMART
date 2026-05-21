from __future__ import annotations

from fastapi.testclient import TestClient

from backend.app import app
from mwongozo_smart.services import auth_service, auth_store


client = TestClient(app)


def _student_login(email: str = "saved.test@mwongozo.local") -> None:
    auth_store.ensure_auth_schema()
    existing = auth_store.get_user_by_email(email)
    if not existing:
        auth_service.register_user(
            email=email,
            password="TestPass1",
            full_name="Saved Tester",
        )
    res = client.post(
        "/auth/login",
        json={"email": email, "password": "TestPass1"},
    )
    assert res.status_code == 200


def test_saved_endpoints_require_login() -> None:
    auth_store.ensure_auth_schema()
    client.post("/auth/logout")
    res = client.get("/auth/saved-programmes")
    assert res.status_code == 401
    res = client.get("/auth/saved-recommendations")
    assert res.status_code == 401


def test_saved_recommendations_crud() -> None:
    _student_login("saved.reco@mwongozo.local")
    payload = {
        "title": "PCM · 2024",
        "input_snapshot": {"pathway": "a_level", "combination": "PCM"},
        "results_snapshot": {
            "recommendations": [
                {
                    "rank": 1,
                    "programme": {"code": "TEST1", "name": "Test Programme"},
                    "assessment": {"confidence": 88, "confidence_band": "high"},
                }
            ],
            "review_candidates": [],
        },
        "recommend_count": 1,
        "direct_count": 1,
        "review_count": 0,
    }
    create = client.post("/auth/saved-recommendations", json=payload)
    assert create.status_code == 200
    reco_id = create.json()["id"]
    assert reco_id > 0

    listing = client.get("/auth/saved-recommendations")
    assert listing.status_code == 200
    items = listing.json()["items"]
    assert len(items) == 1
    assert items[0]["title"] == "PCM · 2024"
    assert items[0]["direct_count"] == 1

    detail = client.get(f"/auth/saved-recommendations/{reco_id}")
    assert detail.status_code == 200
    assert detail.json()["item"]["results_snapshot"]["recommendations"][0]["programme"]["code"] == "TEST1"

    deleted = client.delete(f"/auth/saved-recommendations/{reco_id}")
    assert deleted.status_code == 200
    listing_after = client.get("/auth/saved-recommendations")
    assert listing_after.json()["items"] == []


def test_saved_programmes_require_login() -> None:
    _student_login("saved.prog@mwongozo.local")
    save = client.post(
        "/auth/saved-programmes",
        json={
            "programme_code": "CS101",
            "snapshot": {"name": "Computer Science", "institution_name": "UDSM"},
        },
    )
    assert save.status_code == 200
    listing = client.get("/auth/saved-programmes")
    assert listing.status_code == 200
    assert len(listing.json()["items"]) == 1
    assert listing.json()["items"][0]["code"] == "CS101"
