from mwongozo_smart.core.engine import RecommendationEngine
from mwongozo_smart.core.models import AdmissionPathway, ProgrammeCategory, StudentResult, SubjectGrade
from mwongozo_smart.core.rules import TCURuleEngine
from mwongozo_smart.data.guidebook_data import PROGRAMMES


def _weak_profile_2() -> StudentResult:
    return StudentResult(
        pathway=AdmissionPathway.A_LEVEL,
        a_level_subjects=[
            SubjectGrade(subject="General Studies", grade="S", principal=True),
            SubjectGrade(subject="Geography", grade="D", principal=True),
            SubjectGrade(subject="Chemistry", grade="E", principal=True),
            SubjectGrade(subject="Biology", grade="D", principal=True),
            SubjectGrade(subject="Basic Applied Mathematics", grade="F", principal=True),
        ],
    )


def _weak_profile_1() -> StudentResult:
    return StudentResult(
        pathway=AdmissionPathway.A_LEVEL,
        a_level_subjects=[
            SubjectGrade(subject="General Studies", grade="F", principal=True),
            SubjectGrade(subject="Geography", grade="E", principal=True),
            SubjectGrade(subject="Chemistry", grade="E", principal=True),
            SubjectGrade(subject="Biology", grade="E", principal=True),
            SubjectGrade(subject="Basic Applied Mathematics", grade="F", principal=True),
        ],
    )


def test_weak_profile_1_gets_no_recommendations():
    recs = RecommendationEngine().recommend(_weak_profile_1(), limit=40)
    assert recs == []


def test_weak_profile_2_blocks_clinical_and_stem():
    from mwongozo_smart.core.health_classification import is_clinical_health_programme

    student = _weak_profile_2()
    recs = RecommendationEngine().recommend(student, limit=60)
    clinical = [r for r in recs if r.programme.category == ProgrammeCategory.HEALTH and is_clinical_health_programme(r.programme)]
    general = [r for r in recs if r.programme.category == ProgrammeCategory.HEALTH and not is_clinical_health_programme(r.programme)]
    stem = [
        r
        for r in recs
        if r.programme.category
        in {ProgrammeCategory.ENGINEERING, ProgrammeCategory.TECH, ProgrammeCategory.COMPUTING}
    ]
    assert clinical == []
    assert stem == []
    for rec in general:
        assert rec.assessment.confidence <= 52.0


def test_weak_profile_2_clinical_health_programme_fails_rules():
    student = _weak_profile_2()
    clinical = next(p for p in PROGRAMMES if p.code == "MH009")
    result = TCURuleEngine().evaluate(student, clinical)
    assert result.eligible is False
    assert any(issue.rule_id in {"health_anchor", "health_clinical_grades", "health_points_floor"} for issue in result.issues)


def test_pcb_division_ii_gets_general_health_bachelor():
    student = StudentResult(
        pathway=AdmissionPathway.A_LEVEL,
        csee_division="II",
        combination="PCB",
        a_level_subjects=[
            SubjectGrade(subject="Physics", grade="B", principal=True),
            SubjectGrade(subject="Chemistry", grade="B", principal=True),
            SubjectGrade(subject="Biology", grade="B", principal=True),
        ],
    )
    recs = RecommendationEngine().recommend(student, limit=80)
    health = [r for r in recs if r.programme.category == ProgrammeCategory.HEALTH]
    general = [r for r in health if "environmental" in r.programme.name.lower() or "community" in r.programme.name.lower()]
    assert len(health) >= 5
    assert general
    assert max(r.assessment.confidence for r in general) > 55.0


def test_pcb_strong_profile_still_gets_health():
    student = StudentResult(
        pathway=AdmissionPathway.A_LEVEL,
        combination="PCB",
        a_level_subjects=[
            SubjectGrade(subject="Physics", grade="B", principal=True),
            SubjectGrade(subject="Chemistry", grade="B", principal=True),
            SubjectGrade(subject="Biology", grade="B", principal=True),
        ],
    )
    recs = RecommendationEngine().recommend(student, limit=40)
    health = [r for r in recs if r.programme.category == ProgrammeCategory.HEALTH]
    assert len(health) >= 3
