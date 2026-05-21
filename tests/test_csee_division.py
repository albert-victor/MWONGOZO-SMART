from mwongozo_smart.core.calculator import (
    csee_division_is_passing,
    csee_o_level_entry_gate,
    extract_csee_division,
    normalize_csee_division,
)
from mwongozo_smart.core.engine import RecommendationEngine
from mwongozo_smart.core.models import AdmissionPathway, StudentResult, SubjectGrade


def _o_level_student(
    *,
    division: str | None,
    subjects: list[tuple[str, str]],
) -> StudentResult:
    return StudentResult(
        pathway=AdmissionPathway.O_LEVEL,
        csee_division=division,
        notes=[f"Division: {division}"] if division else [],
        o_level_subjects=[
            SubjectGrade(subject=name, grade=grade, level="o_level") for name, grade in subjects
        ],
    )


def test_normalize_csee_division_zero():
    assert normalize_csee_division("0") == "0"
    assert normalize_csee_division("DIVISION 0") == "0"
    assert normalize_csee_division("IV") == "IV"
    assert csee_division_is_passing("0") is False
    assert csee_division_is_passing("III") is True


def test_division_zero_blocks_recommendations_even_with_tech_passes():
    student = _o_level_student(
        division="0",
        subjects=[
            ("Basic Mathematics", "D"),
            ("English Language", "D"),
            ("Computer Studies", "D"),
            ("Physics", "F"),
            ("Chemistry", "F"),
        ],
    )
    allowed, message, div = csee_o_level_entry_gate(student)
    assert allowed is False
    assert div == "0"
    assert "Division 0" in message
    assert RecommendationEngine().recommend(student, limit=50) == []
    assert RecommendationEngine().review_candidates(student, limit=20) == []


def test_division_four_with_passes_still_recommends():
    student = _o_level_student(
        division="IV",
        subjects=[
            ("Basic Mathematics", "D"),
            ("English Language", "D"),
            ("Kiswahili", "D"),
            ("History", "F"),
        ],
    )
    allowed, _, _ = csee_o_level_entry_gate(student)
    assert allowed is True
    recs = RecommendationEngine().recommend(student, limit=40)
    assert len(recs) >= 3


def test_division_four_health_diploma_not_bachelor():
    student = _o_level_student(
        division="IV",
        subjects=[
            ("Biology", "D"),
            ("Chemistry", "D"),
            ("Physics", "D"),
            ("English Language", "D"),
            ("Kiswahili", "D"),
        ],
    )
    recs = RecommendationEngine().recommend(student, limit=200)
    health = [r for r in recs if r.programme.category.value == "health"]
    assert health
    assert all(r.programme.award_level.value != "bachelor" for r in health)
    diplomas = [r for r in health if r.programme.award_level.value == "diploma"]
    assert diplomas
    assert all(r.assessment.confidence <= 52.0 for r in health)


def test_division_zero_blocks_all_health():
    student = _o_level_student(
        division="0",
        subjects=[
            ("Biology", "D"),
            ("Chemistry", "D"),
            ("English Language", "D"),
        ],
    )
    recs = RecommendationEngine().recommend(student, limit=80)
    assert not [r for r in recs if r.programme.category.value == "health"]


def test_a_level_with_csee_iv_can_see_health_diploma():
    student = StudentResult(
        pathway=AdmissionPathway.A_LEVEL,
        csee_division="IV",
        a_level_subjects=[
            SubjectGrade(subject="Biology", grade="D", principal=True),
            SubjectGrade(subject="Chemistry", grade="D", principal=True),
            SubjectGrade(subject="Geography", grade="D", principal=True),
        ],
        o_level_subjects=[
            SubjectGrade(subject="Biology", grade="D", level="o_level"),
            SubjectGrade(subject="Chemistry", grade="D", level="o_level"),
            SubjectGrade(subject="English Language", grade="D", level="o_level"),
        ],
    )
    recs = RecommendationEngine().recommend(student, limit=80)
    health_bach = [
        r for r in recs if r.programme.category.value == "health" and r.programme.award_level.value == "bachelor"
    ]
    health_dip = [
        r for r in recs if r.programme.category.value == "health" and r.programme.award_level.value == "diploma"
    ]
    assert not health_bach
    assert health_dip
    assert all(r.assessment.confidence <= 52.0 for r in health_dip)


def test_extract_division_from_notes():
    student = StudentResult(
        pathway=AdmissionPathway.O_LEVEL,
        notes=["Division: 0", "NECTA lookup"],
        o_level_subjects=[SubjectGrade(subject="English Language", grade="D", level="o_level")],
    )
    assert extract_csee_division(student) == "0"
