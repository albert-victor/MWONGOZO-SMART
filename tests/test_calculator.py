from mwongozo_smart.core.calculator import get_o_level_summary, get_principal_summary
from mwongozo_smart.core.models import AdmissionPathway, StudentResult, SubjectGrade
from mwongozo_smart.core.models import ALevelScheme
from mwongozo_smart.utils.grade_converter import grade_points


def test_principal_points_sum_top_three():
    student = StudentResult(
        pathway=AdmissionPathway.A_LEVEL,
        a_level_subjects=[
            SubjectGrade(subject="Physics", grade="A"),
            SubjectGrade(subject="Chemistry", grade="B"),
            SubjectGrade(subject="Biology", grade="C"),
            SubjectGrade(subject="English Language", grade="S", principal=False),
        ],
    )
    summary = get_principal_summary(student)
    assert summary.total_points == 12.0
    assert summary.principal_count == 3


def test_grade_points_support_multiple_schemes():
    assert grade_points("A", ALevelScheme.POST_2016) == 5.0
    assert grade_points("C", ALevelScheme.YEAR_2014_2015) == 2.0


def test_o_level_summary_ignores_fail_and_blank_grades():
    student = StudentResult(
        pathway=AdmissionPathway.O_LEVEL,
        o_level_subjects=[
            SubjectGrade(subject="Mathematics", grade="C", level="o_level"),
            SubjectGrade(subject="English Language", grade="F", level="o_level"),
            SubjectGrade(subject="Biology", grade="", level="o_level"),
        ],
    )
    summary = get_o_level_summary(student)
    assert summary.pass_count == 1
    assert summary.total_grade_points == 3.0
