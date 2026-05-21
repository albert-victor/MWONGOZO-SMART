from mwongozo_smart.core.engine import RecommendationEngine
from mwongozo_smart.core.models import AdmissionPathway, StudentResult, SubjectGrade


def _arts_student(combination: str) -> StudentResult:
    profiles = {
        "HGE": [
            ("History", "B"),
            ("Geography", "B"),
            ("Economics", "C"),
        ],
        "HGL": [
            ("History", "B"),
            ("Geography", "B"),
            ("English Language", "C"),
        ],
        "HKL": [
            ("History", "B"),
            ("Kiswahili", "B"),
            ("English Language", "C"),
        ],
    }
    subjects = profiles[combination]
    return StudentResult(
        pathway=AdmissionPathway.A_LEVEL,
        combination=combination,
        a_level_subjects=[
            SubjectGrade(subject=name, grade=grade, principal=True) for name, grade in subjects
        ],
    )


def test_arts_combinations_never_get_eligible_health_programmes():
    engine = RecommendationEngine()
    for combo in ("HGE", "HGL", "HKL"):
        student = _arts_student(combo)
        recs = engine.recommend(student, limit=300)
        health_like = [
            r
            for r in recs
            if r.programme.category.value == "health"
            or "health" in r.programme.name.lower()
            or "nursing" in r.programme.name.lower()
            or "medicine" in r.programme.name.lower()
        ]
        assert health_like == [], f"{combo} should not receive health recommendations"


def test_arts_combinations_exclude_health_from_review_candidates():
    engine = RecommendationEngine()
    student = _arts_student("HGE")
    review = engine.review_candidates(student, limit=200)
    health_like = [
        r
        for r in review
        if r.programme.category.value == "health"
        or "health" in r.programme.name.lower()
        or "nursing" in r.programme.name.lower()
    ]
    assert health_like == []


def test_pcb_still_receives_health_recommendations():
    engine = RecommendationEngine()
    student = StudentResult(
        pathway=AdmissionPathway.A_LEVEL,
        combination="PCB",
        a_level_subjects=[
            SubjectGrade(subject="Physics", grade="B", principal=True),
            SubjectGrade(subject="Chemistry", grade="B", principal=True),
            SubjectGrade(subject="Biology", grade="B", principal=True),
        ],
    )
    recs = engine.recommend(student, limit=120)
    health = [r for r in recs if r.programme.category.value == "health"]
    assert len(health) >= 1
