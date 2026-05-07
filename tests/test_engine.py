from mwongozo_smart.core.engine import RecommendationEngine
from mwongozo_smart.core.models import AdmissionPathway, StudentResult, SubjectGrade


def test_engine_returns_ranked_recommendations():
    student = StudentResult(
        pathway=AdmissionPathway.A_LEVEL,
        preferred_regions=["Dar es Salaam"],
        a_level_subjects=[
            SubjectGrade(subject="Physics", grade="A"),
            SubjectGrade(subject="Chemistry", grade="B"),
            SubjectGrade(subject="Biology", grade="B"),
        ],
    )
    recommendations = RecommendationEngine().recommend(student)
    assert recommendations
    assert recommendations[0].rank == 1
    assert recommendations[0].assessment.confidence >= recommendations[-1].assessment.confidence


def test_engine_suggests_combination_paths():
    student = StudentResult(
        pathway=AdmissionPathway.A_LEVEL,
        a_level_subjects=[
            SubjectGrade(subject="Physics", grade="A"),
            SubjectGrade(subject="Chemistry", grade="B"),
            SubjectGrade(subject="Biology", grade="B"),
        ],
    )
    suggestions = RecommendationEngine().suggest_combinations(student)
    assert suggestions
    assert suggestions[0].code == "PCB"
