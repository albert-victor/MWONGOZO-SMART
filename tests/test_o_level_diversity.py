from collections import Counter

from mwongozo_smart.core.engine import RecommendationEngine
from mwongozo_smart.core.models import AdmissionPathway, StudentResult, SubjectGrade


def test_o_level_recommendations_are_category_diverse():
    student = StudentResult(
        pathway=AdmissionPathway.O_LEVEL,
        csee_division="III",
        o_level_subjects=[
            SubjectGrade(subject="Biology", grade="D", level="o_level"),
            SubjectGrade(subject="Chemistry", grade="D", level="o_level"),
            SubjectGrade(subject="English Language", grade="D", level="o_level"),
            SubjectGrade(subject="Basic Mathematics", grade="D", level="o_level"),
            SubjectGrade(subject="Computer Studies", grade="D", level="o_level"),
        ],
    )
    recs = RecommendationEngine().recommend(student, limit=24)
    top = recs[:12]
    cats = Counter(r.programme.category.value for r in top)
    assert len(cats) >= 4
    assert cats.get("computing", 0) <= 4
