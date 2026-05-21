from mwongozo_smart.core.engine import RecommendationEngine
from mwongozo_smart.core.health_classification import is_clinical_health_programme
from mwongozo_smart.core.models import AdmissionPathway, ProgrammeCategory, StudentResult, SubjectGrade
from mwongozo_smart.core.rules import TCURuleEngine
from mwongozo_smart.data.guidebook_data import PROGRAMMES


def _cbg_student(*, division: str = "II") -> StudentResult:
    return StudentResult(
        pathway=AdmissionPathway.A_LEVEL,
        csee_division=division,
        combination="CBG",
        a_level_subjects=[
            SubjectGrade(subject="Chemistry", grade="C", principal=True),
            SubjectGrade(subject="Biology", grade="C", principal=True),
            SubjectGrade(subject="Geography", grade="D", principal=True),
        ],
    )


def test_cbg_division_ii_eligible_for_many_health_bachelors():
    student = _cbg_student(division="II")
    engine = TCURuleEngine()
    eligible = sum(
        1
        for p in PROGRAMMES
        if p.category == ProgrammeCategory.HEALTH
        and p.award_level.value == "bachelor"
        and engine.evaluate(student, p).eligible
    )
    assert eligible >= 18


def test_cbg_division_ii_recommendations_are_varied():
    student = _cbg_student(division="II")
    recs = RecommendationEngine().recommend(student, limit=150)
    health = [r for r in recs if r.programme.category == ProgrammeCategory.HEALTH]
    institutions = {r.programme.institution_code for r in health}
    families = {
        "clinical" if is_clinical_health_programme(r.programme) else "general"
        for r in health
    }
    assert len(health) >= 20
    assert len(institutions) >= 8
    assert len(families) >= 2


def test_cbg_division_iii_gets_capped_health_bachelor():
    student = _cbg_student(division="III")
    recs = RecommendationEngine().recommend(student, limit=150)
    health_bach = [
        r
        for r in recs
        if r.programme.category == ProgrammeCategory.HEALTH and r.programme.award_level.value == "bachelor"
    ]
    assert len(health_bach) >= 8
    assert all(r.assessment.confidence <= 58.0 for r in health_bach)
