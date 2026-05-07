from __future__ import annotations

from mwongozo_smart.core.models import ALevelScheme

ALPHABETICAL_GRADE_ORDER = {
    "A": 5.0,
    "B": 4.0,
    "C": 3.0,
    "D": 2.0,
    "E": 1.0,
    "S": 0.5,
    "F": 0.0,
}

PRE_2014_POINTS = {
    "A": 5.0,
    "B": 4.0,
    "C": 3.0,
    "D": 2.0,
    "E": 1.0,
    "S": 0.5,
}

Y2014_2015_POINTS = {
    "A": 5.0,
    "B+": 4.0,
    "B": 3.0,
    "C": 2.0,
    "D": 1.0,
    "E": 0.5,
    "S": 0.0,
}

POST_2016_POINTS = {
    "A": 5.0,
    "B": 4.0,
    "C": 3.0,
    "D": 2.0,
    "E": 1.0,
    "S": 0.5,
}


def normalize_grade(grade: str) -> str:
    # Keep grade text consistent before looking it up in point tables.
    return grade.strip().upper().replace(" ", "")


def grade_points(grade: str, scheme: ALevelScheme = ALevelScheme.POST_2016) -> float:
    # Convert an exam grade into points using the selected A-Level scheme.
    normalized = normalize_grade(grade)
    if scheme == ALevelScheme.YEAR_2014_2015:
        return Y2014_2015_POINTS.get(normalized, 0.0)
    if scheme == ALevelScheme.PRE_2014:
        return PRE_2014_POINTS.get(normalized, 0.0)
    return POST_2016_POINTS.get(normalized, 0.0)


def principal_grade_threshold(scheme: ALevelScheme) -> float:
    # Minimum grade score needed to count as a principal pass.
    return 2.0 if scheme == ALevelScheme.YEAR_2014_2015 else 1.0


def is_principal_grade(grade: str, scheme: ALevelScheme = ALevelScheme.POST_2016) -> bool:
    # True when the grade is strong enough to count as principal.
    return grade_points(grade, scheme) >= principal_grade_threshold(scheme)


def grade_at_least(actual: str, minimum: str, scheme: ALevelScheme = ALevelScheme.POST_2016) -> bool:
    # Compare two grades after converting both to points.
    return grade_points(actual, scheme) >= grade_points(minimum, scheme)


def confidence_band_from_score(score: float) -> str:
    # Human-friendly label for the final confidence value.
    if score >= 72:
        return "High"
    if score >= 50:
        return "Medium"
    if score >= 30:
        return "Low"
    return "Very Low"
