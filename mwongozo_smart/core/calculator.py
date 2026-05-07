from __future__ import annotations

from dataclasses import dataclass

from mwongozo_smart.core.models import ALevelScheme, StudentResult, SubjectGrade
from mwongozo_smart.utils.combination_helper import normalize_subject_name
from mwongozo_smart.utils.grade_converter import grade_at_least, grade_points, is_principal_grade


@dataclass(slots=True)
class PrincipalSummary:
    # Small summary object used by the engine and rule checker.
    principal_subjects: list[SubjectGrade]
    total_points: float
    principal_count: int


def _subject_points(subject: SubjectGrade, scheme: ALevelScheme) -> float:
    return grade_points(subject.grade, scheme)


def normalize_student_subjects(student: StudentResult) -> StudentResult:
    # Standardize subject names so matching works across spelling variants.
    student.a_level_subjects = [
        subject.model_copy(update={"subject": normalize_subject_name(subject.subject)})
        for subject in student.a_level_subjects
    ]
    student.o_level_subjects = [
        subject.model_copy(update={"subject": normalize_subject_name(subject.subject)})
        for subject in student.o_level_subjects
    ]
    return student


def get_principal_summary(student: StudentResult) -> PrincipalSummary:
    # Pick the strongest 3 principal subjects and total their points.
    normalize_student_subjects(student)
    scheme = student.a_level_scheme
    principal_subjects = [subject for subject in student.a_level_subjects if subject.principal or is_principal_grade(subject.grade, scheme)]
    principal_subjects.sort(key=lambda item: (_subject_points(item, scheme), item.subject), reverse=True)
    selected = principal_subjects[:3]
    total_points = round(sum(_subject_points(item, scheme) for item in selected), 2)
    return PrincipalSummary(principal_subjects=selected, total_points=total_points, principal_count=len(principal_subjects))


def student_has_subject(student: StudentResult, subject_name: str, minimum_grade: str | None = None) -> bool:
    # Check whether the student has a subject, optionally with a minimum grade.
    wanted = normalize_subject_name(subject_name)
    for subject in student.a_level_subjects:
        if normalize_subject_name(subject.subject) == wanted:
            if minimum_grade is None:
                return True
            return grade_at_least(subject.grade, minimum_grade, student.a_level_scheme)
    for subject in student.o_level_subjects:
        if normalize_subject_name(subject.subject) == wanted:
            if minimum_grade is None:
                return True
            return grade_at_least(subject.grade, minimum_grade, ALevelScheme.POST_2016)
    return False


def a_level_subject_grade_map(student: StudentResult) -> dict[str, str]:
    # Fast lookup map for A-Level grade checks.
    normalize_student_subjects(student)
    result: dict[str, str] = {}
    for item in student.a_level_subjects:
        result[normalize_subject_name(item.subject)] = item.grade
    return result


def o_level_subject_grade_map(student: StudentResult) -> dict[str, str]:
    # Fast lookup map for O-Level grade checks.
    normalize_student_subjects(student)
    result: dict[str, str] = {}
    for item in student.o_level_subjects:
        result[normalize_subject_name(item.subject)] = item.grade
    return result
