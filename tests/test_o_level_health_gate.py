from __future__ import annotations

from mwongozo_smart.core.engine import RecommendationEngine
from mwongozo_smart.core.models import AdmissionPathway, StudentResult, SubjectGrade
from mwongozo_smart.data.guidebook_data import PROGRAMMES


def _o_level_student(subjects: list[tuple[str, str]], notes: str = "") -> StudentResult:
    return StudentResult(
        pathway=AdmissionPathway.O_LEVEL,
        o_level_subjects=[
            SubjectGrade(subject=name, grade=grade, level="o_level") for name, grade in subjects
        ],
        notes=notes,
    )


def test_o_level_health_f_grades_blocked_from_review() -> None:
    student = _o_level_student(
        [
            ("Biology", "F"),
            ("Chemistry", "F"),
            ("Physics", "F"),
            ("English Language", "C"),
            ("Basic Mathematics", "C"),
        ],
        notes="P0138/0005",
    )
    engine = RecommendationEngine(PROGRAMMES)
    direct = [r for r in engine.recommend(student, limit=200) if r.programme.category.value == "health"]
    review = [r for r in engine.review_candidates(student, limit=200) if r.programme.category.value == "health"]
    assert direct == []
    assert review == []


def test_o_level_health_missing_science_blocked() -> None:
    student = _o_level_student(
        [
            ("Biology", "D"),
            ("English Language", "C"),
            ("Basic Mathematics", "C"),
        ]
    )
    engine = RecommendationEngine(PROGRAMMES)
    direct = [r for r in engine.recommend(student, limit=200) if r.programme.category.value == "health"]
    review = [r for r in engine.review_candidates(student, limit=200) if r.programme.category.value == "health"]
    assert direct == []
    assert review == []


def test_o_level_health_valid_science_still_allowed() -> None:
    student = _o_level_student(
        [
            ("Biology", "D"),
            ("Chemistry", "D"),
            ("Physics", "D"),
            ("English Language", "C"),
            ("Basic Mathematics", "C"),
        ]
    )
    engine = RecommendationEngine(PROGRAMMES)
    direct = [r for r in engine.recommend(student, limit=200) if r.programme.category.value == "health"]
    assert len(direct) >= 1


def test_o_level_engineering_f_math_no_physics_blocked() -> None:
    student = _o_level_student(
        [
            ("Basic Mathematics", "F"),
            ("Biology", "F"),
            ("Chemistry", "F"),
            ("English Language", "C"),
            ("Computer Studies", "D"),
        ],
        notes="P0138/0005",
    )
    engine = RecommendationEngine(PROGRAMMES)
    stem = {"engineering", "tech", "computing"}
    direct = [r for r in engine.recommend(student, limit=200) if r.programme.category.value in stem]
    review = [r for r in engine.review_candidates(student, limit=200) if r.programme.category.value in stem]
    assert direct == []
    assert review == []


def test_o_level_engineering_d_math_f_science_blocked() -> None:
    student = _o_level_student(
        [
            ("Basic Mathematics", "D"),
            ("Physics", "F"),
            ("Chemistry", "F"),
            ("English Language", "C"),
        ]
    )
    engine = RecommendationEngine(PROGRAMMES)
    stem = {"engineering", "tech", "computing"}
    direct = [r for r in engine.recommend(student, limit=200) if r.programme.category.value in stem]
    review = [r for r in engine.review_candidates(student, limit=200) if r.programme.category.value in stem]
    assert direct == []
    assert review == []


def test_o_level_engineering_valid_stem_still_allowed() -> None:
    student = _o_level_student(
        [
            ("Basic Mathematics", "D"),
            ("Physics", "D"),
            ("English Language", "C"),
            ("Chemistry", "D"),
        ]
    )
    engine = RecommendationEngine(PROGRAMMES)
    stem = {"engineering", "tech", "computing"}
    direct = [r for r in engine.recommend(student, limit=200) if r.programme.category.value in stem]
    assert len(direct) >= 1
