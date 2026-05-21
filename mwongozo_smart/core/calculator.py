from __future__ import annotations

import re
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


@dataclass(slots=True)
class OLevelSummary:
    # CSEE-style summary for certificate and diploma pathway scoring.
    pass_count: int
    total_grade_points: float
    subjects_passing: list[str]


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


def get_o_level_summary(student: StudentResult) -> OLevelSummary:
    # Count O-Level passes (grade D or better in the shared point scale) and total strength.
    normalize_student_subjects(student)
    subjects_passing: list[str] = []
    total_grade_points = 0.0
    for subject in student.o_level_subjects:
        if not subject.grade or not subject.grade.strip():
            continue
        if not grade_at_least(subject.grade, "D", ALevelScheme.POST_2016):
            continue
        name = normalize_subject_name(subject.subject)
        subjects_passing.append(name)
        total_grade_points += grade_points(subject.grade, ALevelScheme.POST_2016)
    return OLevelSummary(
        pass_count=len(subjects_passing),
        total_grade_points=round(total_grade_points, 2),
        subjects_passing=subjects_passing,
    )


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


_DIVISION_NOTE_RE = re.compile(r"division\s*[:=]?\s*([^\s,;]+)", re.I)
_ROMAN_DIVISIONS = frozenset({"I", "II", "III", "IV"})
_FAIL_DIVISIONS = frozenset({"0", "00", "0.0", "FAIL", "F", "ABS", "ABSENT", "INC", "X"})
# NECTA CSEE bands used for health/TVET routing (TCU degree vs NACTVET/NACTE college).
_DIVISION_FAIL = frozenset({"0", "00", "0.0", "FAIL", "F", "ABS", "ABSENT", "INC", "X"})
_DIVISION_WEAK = frozenset({"IV"})
_DIVISION_BORDERLINE = frozenset({"III"})


def normalize_csee_division(raw: str | None) -> str | None:
    if raw is None:
        return None
    text = str(raw).strip().upper()
    if not text or text in {"-", "–", "N/A", "NA", "NONE"}:
        return None
    text = text.replace("DIVISION", "").replace("DIV", "").strip(" .:-")
    if text in _ROMAN_DIVISIONS or text in _FAIL_DIVISIONS:
        return text
    if text.isdigit():
        return "0" if int(text) == 0 else text
    roman = re.match(r"^(I{1,3}|IV|0+)$", text)
    if roman:
        return roman.group(1)
    return text


def extract_csee_division(student: StudentResult) -> str | None:
    direct = normalize_csee_division(getattr(student, "csee_division", None))
    if direct:
        return direct
    for note in student.notes or []:
        match = _DIVISION_NOTE_RE.search(str(note))
        if match:
            parsed = normalize_csee_division(match.group(1))
            if parsed:
                return parsed
    return None


def csee_division_is_passing(division: str | None) -> bool:
    normalized = normalize_csee_division(division)
    if not normalized:
        return True
    if normalized in _FAIL_DIVISIONS:
        return False
    if normalized in _ROMAN_DIVISIONS:
        return True
    if normalized.isdigit():
        return int(normalized) > 0
    return True


def csee_division_band(division: str | None) -> str:
    """NECTA CSEE band: fail | weak | borderline | good | unknown."""
    normalized = normalize_csee_division(division)
    if not normalized:
        return "unknown"
    if normalized in _DIVISION_FAIL:
        return "fail"
    if normalized in _DIVISION_WEAK:
        return "weak"
    if normalized in _DIVISION_BORDERLINE:
        return "borderline"
    if normalized in {"I", "II"}:
        return "good"
    if normalized in _ROMAN_DIVISIONS:
        return "good"
    return "unknown"


def csee_health_award_allowed(
    student: StudentResult,
    award_level_value: str,
) -> tuple[bool, float | None, str]:
    """
    Health-only award gate from CSEE division (O-Level or A-Level with CSEE on profile).
    Returns (allowed, max_confidence_percent or None, reason).
    """
    from mwongozo_smart.core.models import ProgrammeAwardLevel

    band = csee_division_band(extract_csee_division(student))
    award = award_level_value
    if band == "fail":
        return (
            False,
            None,
            "CSEE Division 0 — hakuna njia ya afya (cheti/diploma/shahada). Rudia mtihani wa Form 4.",
        )
    if band == "weak":
        if award == ProgrammeAwardLevel.BACHELOR.value:
            return (
                False,
                None,
                "CSEE Division IV — shahada ya afya haipendekezwi; angalia diploma/cheti (NACTVET/NACTE).",
            )
        return (
            True,
            48.0,
            "CSEE Division IV — diploma/cheti za afya pekee (NACTVET/NACTE), uwezekano mdogo.",
        )
    if band == "borderline":
        if award == ProgrammeAwardLevel.BACHELOR.value:
            if student.pathway.value == "a_level":
                readiness = a_level_sensitive_readiness(student)
                points = float(readiness["total_points"])
                has_science = bool(readiness["biology_d_plus"] or readiness["chemistry_d_plus"])
                if points >= 5.0 and has_science:
                    return (
                        True,
                        55.0,
                        "CSEE Division III — shahada ya afya inawezekana kwa alama nzuri za A-Level; uwezekano mdogo.",
                    )
                return (
                    False,
                    None,
                    "CSEE Division III — shahada ya afya haipendekezwi; angalia diploma za afya (NACTVET/NACTE).",
                )
            return (
                False,
                None,
                "CSEE Division III — shahada ya afya haipendekezwi; angalia diploma za afya.",
            )
        return (
            True,
            52.0,
            "CSEE Division III — diploma/cheti za afya zinafaa zaidi kuliko shahada.",
        )
    return True, None, ""


def csee_o_level_entry_gate(student: StudentResult) -> tuple[bool, str, str | None]:
    """Return (allowed, message, division) for overall O-Level entry."""
    if student.pathway.value != "o_level":
        return True, "", None
    division = extract_csee_division(student)
    summary = get_o_level_summary(student)
    band = csee_division_band(division)
    if band == "fail":
        return (
            False,
            (
                f"CSEE Division {division or '0'} haihitimu kujiunga na kozi za cheti/diploma "
                "(NECTA: Division I–IV pekee). Rudia mtihani au chagua njia nyingine."
            ),
            division,
        )
    if summary.pass_count < 2:
        return (
            False,
            f"Angalau masomo 2 ya CSEE yanayopita (daraja D au bora zaidi) yanahitajika; yamepatikana {summary.pass_count}.",
            division,
        )
    return True, "", division


def get_top_principal_grades(student: StudentResult, limit: int = 3) -> list[SubjectGrade]:
    """Return the strongest principal subjects used for TCU point totals."""
    normalize_student_subjects(student)
    scheme = student.a_level_scheme
    principals = [s for s in student.a_level_subjects if s.principal or is_principal_grade(s.grade, scheme)]
    principals.sort(key=lambda item: (grade_points(item.grade, scheme), item.subject), reverse=True)
    return principals[:limit]


_O_LEVEL_HEALTH_ESSENTIALS = ("Biology", "Chemistry", "Physics")


def o_level_health_science_eligible(student: StudentResult) -> tuple[bool, str]:
    """CSEE science foundation for college-level health programmes (certificate/diploma)."""
    if student.pathway.value != "o_level":
        return True, ""
    for name in _O_LEVEL_HEALTH_ESSENTIALS:
        if student_has_subject(student, name, "D"):
            continue
        if student_has_subject(student, name):
            return False, f"Health routes need {name} at grade D or better (F does not qualify)."
        return False, f"Health routes require {name} at CSEE level."
    return True, "CSEE science foundation met for health routes."


def o_level_stem_engineering_eligible(student: StudentResult) -> tuple[bool, str]:
    """CSEE math + science foundation for college-level engineering/tech/computing routes."""
    if student.pathway.value != "o_level":
        return True, ""
    math_names = ("Basic Mathematics", "Mathematics")
    math_ok = any(student_has_subject(student, name, "D") for name in math_names)
    if not math_ok:
        if any(student_has_subject(student, name) for name in math_names):
            return False, "Engineering/Tech routes need Mathematics at grade D or better (F does not qualify)."
        return False, "Engineering/Tech routes require CSEE Mathematics or Basic Mathematics."
    science_ok = student_has_subject(student, "Physics", "D") or student_has_subject(student, "Chemistry", "D")
    if not science_ok:
        if student_has_subject(student, "Physics") or student_has_subject(student, "Chemistry"):
            return False, "Engineering/Tech routes need Physics or Chemistry at grade D or better (F does not qualify)."
        return False, "Engineering/Tech routes require Physics or Chemistry at CSEE level."
    return True, "CSEE STEM foundation met for engineering/tech routes."


def a_level_points_margin(student: StudentResult, minimum_total_points: float) -> float:
    return get_principal_summary(student).total_points - float(minimum_total_points or 0)


def a_level_sensitive_readiness(student: StudentResult) -> dict[str, bool | float]:
    """TCU-aligned readiness flags for health and STEM bachelor routes."""
    summary = get_principal_summary(student)
    scheme = student.a_level_scheme
    top = get_top_principal_grades(student, 3)
    d_or_better = sum(1 for s in top if grade_at_least(s.grade, "D", scheme))
    return {
        "total_points": summary.total_points,
        "principal_count": summary.principal_count,
        "top_principals_at_d": d_or_better,
        "biology_d_plus": student_has_subject(student, "Biology", "D"),
        "chemistry_d_plus": student_has_subject(student, "Chemistry", "D"),
        "biology_c_plus": student_has_subject(student, "Biology", "C"),
        "chemistry_c_plus": student_has_subject(student, "Chemistry", "C"),
        "math_d_plus": student_has_subject(student, "Advanced Mathematics", "D")
        or student_has_subject(student, "Basic Applied Mathematics", "D"),
        "physics_d_plus": student_has_subject(student, "Physics", "D"),
        "health_science_ready": (
            (student_has_subject(student, "Biology", "D") and student_has_subject(student, "Chemistry", "D"))
            or (student_has_subject(student, "Biology", "D") and student_has_subject(student, "Physics", "D"))
            or (student_has_subject(student, "Chemistry", "D") and student_has_subject(student, "Physics", "D"))
        ),
        "stem_ready": (
            student_has_subject(student, "Advanced Mathematics", "D")
            or student_has_subject(student, "Basic Applied Mathematics", "D")
            or (
                student_has_subject(student, "Physics", "D")
                and student_has_subject(student, "Chemistry", "D")
            )
        ),
    }
