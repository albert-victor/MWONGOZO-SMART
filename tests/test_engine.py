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


def test_o_level_three_passes_can_still_get_college_recommendations():
    student = StudentResult(
        pathway=AdmissionPathway.O_LEVEL,
        o_level_subjects=[
            SubjectGrade(subject="Mathematics", grade="D", level="o_level"),
            SubjectGrade(subject="English Language", grade="D", level="o_level"),
            SubjectGrade(subject="Kiswahili", grade="D", level="o_level"),
        ],
    )
    recommendations = RecommendationEngine().recommend(student, limit=50)
    assert len(recommendations) >= 5


def test_o_level_recommendations_rank_by_confidence_and_use_csee_points():
    student = StudentResult(
        pathway=AdmissionPathway.O_LEVEL,
        o_level_subjects=[
            SubjectGrade(subject="Mathematics", grade="B", level="o_level"),
            SubjectGrade(subject="English Language", grade="B", level="o_level"),
            SubjectGrade(subject="Biology", grade="B", level="o_level"),
            SubjectGrade(subject="Chemistry", grade="B", level="o_level"),
            SubjectGrade(subject="Physics", grade="C", level="o_level"),
        ],
    )
    recommendations = RecommendationEngine().recommend(student, limit=150)
    assert len(recommendations) >= 25
    assert recommendations[0].assessment.confidence >= recommendations[-1].assessment.confidence
    assert recommendations[0].student_points > 0


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
