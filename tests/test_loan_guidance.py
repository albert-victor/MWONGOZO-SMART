import pytest

from mwongozo_smart.loan_assistant import common_mistakes
from mwongozo_smart.loan_guidance import build_loan_guidance
from mwongozo_smart.loan_tracking import (
    build_loan_tracking,
    list_demo_references,
    list_demo_students,
)


def test_loan_guidance_o_level_sw():
    data = build_loan_guidance("o_level", "sw")
    assert data["exam_level"] == "o_level"
    assert data["language"] == "sw"
    assert len(data["sections"]) >= 3
    assert len(data["document_checklist"]) >= 5
    assert len(data["faq"]) >= 8
    assert data["olas_steps"] == []


def test_loan_guidance_a_level_en():
    data = build_loan_guidance("a_level", "en")
    assert data["exam_level"] == "a_level"
    assert len(data["olas_steps"]) >= 4
    assert data["sections"][0]["id"] == "olas"


def test_loan_guidance_api_route():
    pytest.importorskip("bcrypt")
    from fastapi.testclient import TestClient

    from backend.app import app

    client = TestClient(app)
    response = client.get("/loan/guidance", params={"exam_level": "o_level", "language": "sw"})
    assert response.status_code == 200
    body = response.json()
    assert body["exam_level"] == "o_level"
    assert "official_links" in body


def test_loan_track_demo_reference_payload():
    ref = list_demo_references()[0]
    body = build_loan_tracking({"heslb_reference": ref, "language": "sw"})
    assert body["demo_profile_found"] is True
    assert body["tracker_mode"] == "application"
    assert body["funding_table"]["heslb_reference"] == ref


def test_loan_track_o_level_preparation_mode():
    body = build_loan_tracking(
        {
            "exam_level": "o_level",
            "exam_number": "P1234/0001/2024",
            "language": "sw",
        }
    )
    assert body["tracker_mode"] == "preparation"
    assert body["batch_prediction"]["preparation_mode"] is True
    assert body["batch_prediction"]["batch_one_probability"] is None


def test_common_mistakes_swahili():
    mistakes = common_mistakes("sw")
    assert mistakes
    assert any("Majina" in item["title"] for item in mistakes)


def test_list_demo_students_three_journeys():
    students = list_demo_students("sw")
    assert len(students) == 3
    statuses = {s["funding_status"] for s in students}
    assert statuses == {"in_progress", "approved", "denied"}


def test_demo_student_midway_verification():
    body = build_loan_tracking({"heslb_reference": "HSL-2026-00127", "language": "sw"})
    assert body["demo_profile_found"] is True
    assert body["completion_percent"] == 54
    assert body["funding_table"]["application_stage"] == "verification"
    assert body["funding_table"]["appeal_eligible"] is False
    assert body["demo_profile"]["funding_status"] == "in_progress"


def test_demo_student_funded_batch_one():
    body = build_loan_tracking({"heslb_reference": "HSL-2026-00482", "language": "sw"})
    assert body["completion_percent"] == 100
    assert "umepangiwa" in body["funding_table"]["batch_prediction"]
    assert body["appeal_guidance"]["appeal_eligibility"] is False
    assert body["demo_profile"]["funding_status"] == "approved"


def test_demo_student_denied_with_appeal_guidance():
    body = build_loan_tracking({"heslb_reference": "HSL-2026-00991", "language": "sw"})
    assert body["completion_percent"] == 100
    assert body["funding_table"]["appeal_eligible"] is True
    assert body["appeal_guidance"]["appeal_eligibility"] is True
    assert len(body["appeal_guidance"]["possible_reasons"]) == 3
    assert body["demo_profile"]["funding_status"] == "denied"
    assert any(a["level"] == "urgent" for a in body["alerts"])
