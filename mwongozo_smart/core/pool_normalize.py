"""Normalize TCU principal-subject pools and realistic health matching."""

from __future__ import annotations

from collections.abc import Iterable

from mwongozo_smart.core.models import Programme, ProgrammeCategory, StudentResult
from mwongozo_smart.utils.combination_helper import normalize_subject_name
from mwongozo_smart.utils.grade_converter import grade_at_least

HEALTH_SCIENCE_PRINCIPALS = frozenset(
    {
        "biology",
        "chemistry",
        "physics",
        "advanced mathematics",
    }
)

HEALTH_POOL_SUPPORT = HEALTH_SCIENCE_PRINCIPALS | {
    "geography",
    "economics",
    "computer science",
    "nutrition",
}

_POOL_JUNK = frozenset(
    {
        "c",
        "s",
        "one of the science",
        "subsidiary",
        "minimum",
        "history",
    }
)

_GRADE_LETTERS = frozenset({"a", "b", "c", "d", "e", "f", "s"})


def normalize_principal_subject_pool(pool: Iterable[str] | None) -> list[str]:
    if not pool:
        return []
    cleaned: list[str] = []
    for item in pool:
        name = normalize_subject_name(str(item).strip())
        if not name:
            continue
        low = name.lower()
        if low in _POOL_JUNK:
            continue
        if len(name) <= 2 and low in _GRADE_LETTERS:
            continue
        if "one of" in low:
            continue
        cleaned.append(name)
    return cleaned


def principal_pool_is_corrupt(pool: Iterable[str] | None) -> bool:
    if not pool:
        return False
    raw = [str(item).strip() for item in pool if str(item).strip()]
    if not raw:
        return False
    cleaned = normalize_principal_subject_pool(pool)
    return len(cleaned) < len(raw)


def count_science_principals(student: StudentResult, *, minimum_grade: str = "D") -> int:
    count = 0
    scheme = student.a_level_scheme
    for subject in student.a_level_subjects:
        if not subject.principal:
            continue
        if normalize_subject_name(subject.subject).lower() not in HEALTH_SCIENCE_PRINCIPALS:
            continue
        if grade_at_least(subject.grade, minimum_grade, scheme):
            count += 1
    return count


def effective_health_pool_min_count(pool: list[str], min_count: int) -> int:
    if not pool or min_count <= 0:
        return min_count
    lowered = {normalize_subject_name(item).lower() for item in pool}
    science_in_pool = lowered & HEALTH_SCIENCE_PRINCIPALS
    if not science_in_pool:
        return min_count
    if min_count >= 3 and len(science_in_pool) >= 2:
        return 2
    return min_count


def health_principal_pool_satisfied(
    student: StudentResult,
    programme: Programme,
    pool: Iterable[str] | None,
    min_count: int,
    *,
    matched_count: int,
    college_route: bool,
) -> tuple[bool, int, int]:
    """Return (ok, matched_count, effective_min_count) for health-aware pool checks."""
    if college_route or programme.category != ProgrammeCategory.HEALTH:
        return matched_count >= min_count, matched_count, min_count
    if student.pathway.value != "a_level":
        return matched_count >= min_count, matched_count, min_count

    cleaned = normalize_principal_subject_pool(pool)
    effective_min = effective_health_pool_min_count(cleaned, min_count)

    if matched_count >= effective_min:
        return True, matched_count, effective_min

    if principal_pool_is_corrupt(pool):
        science = count_science_principals(student)
        if science >= 2:
            return True, max(matched_count, science), max(2, effective_min)

    if cleaned:
        lowered = {normalize_subject_name(item).lower() for item in cleaned}
        if lowered <= HEALTH_POOL_SUPPORT and count_science_principals(student) >= 2:
            return True, max(matched_count, 2), effective_min

    return False, matched_count, effective_min
