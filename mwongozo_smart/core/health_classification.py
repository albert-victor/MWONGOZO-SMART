"""TCU 2025/26 health programme tiers — clinical core vs general health sciences."""

from __future__ import annotations

from mwongozo_smart.core.models import Programme, StudentResult
from mwongozo_smart.core.calculator import a_level_sensitive_readiness, csee_division_band, extract_csee_division

_LAB_NOT_CLINICAL = frozenset(
    {
        "medical laboratory",
        "health laboratory",
        "laboratory sciences",
        "laboratory science",
        "biomedical science",
        "biomedical sciences",
    }
)

_CLINICAL_TOKENS = frozenset(
    {
        "nursing",
        "midwifery",
        "medicine",
        "pharmacy",
        "pharmaceutical",
        "clinical medicine",
        "dentistry",
        "dental surgery",
        "doctor of medicine",
        "doctor of dental",
        "mbchb",
        "school of medicine",
        "doctor of pharmacy",
    }
)

_GENERAL_HEALTH_TOKENS = frozenset(
    {
        "environmental health",
        "community health",
        "public health",
        "health systems",
        "health services",
        "health management",
        "health information",
        "food",
        "nutrition",
        "physiotherapy",
        "occupational therapy",
        "radiography",
        "optometry",
        "laboratory sciences",
        "health laboratory",
        "biomedical",
        "therapeutic",
        "diagnostic",
    }
)


def _programme_text(programme: Programme) -> str:
    name = programme.name.lower()
    tags = " ".join(programme.tags).lower()
    return f"{name} {tags}"


def is_clinical_health_programme(programme: Programme) -> bool:
    text = _programme_text(programme)
    if any(g in text for g in ("environmental health", "community health", "public health", "health systems")):
        return False
    if any(token in text for token in _LAB_NOT_CLINICAL):
        return False
    if any(token in text for token in _GENERAL_HEALTH_TOKENS):
        if not any(c in text for c in ("nursing", "midwifery", "medicine", "pharmacy", "dentistry")):
            return False
    if any(token in text for token in _CLINICAL_TOKENS):
        return True
    if "clinical" in text and "clinical medicine" in text:
        return True
    if " surgery" in text or text.endswith("surgery"):
        return True
    return False


def is_general_health_programme(programme: Programme) -> bool:
    if programme.category.value != "health":
        return False
    if is_clinical_health_programme(programme):
        return False
    text = _programme_text(programme)
    return any(token in text for token in _GENERAL_HEALTH_TOKENS) or "health" in text


def health_bachelor_confidence_cap(student: StudentResult, programme: Programme) -> float | None:
    """Max confidence % for health bachelor (None = no extra cap beyond engine)."""
    if programme.award_level.value != "bachelor" or student.pathway.value != "a_level":
        return None
    band = csee_division_band(extract_csee_division(student))
    readiness = a_level_sensitive_readiness(student)
    points = float(readiness["total_points"])
    clinical = is_clinical_health_programme(programme)

    if band == "borderline" and student.pathway.value == "a_level":
        if clinical:
            if points >= 7.0 and readiness["biology_c_plus"] and readiness["chemistry_c_plus"]:
                return 55.0
            return 42.0
        if points >= 5.5:
            return 58.0
        return 48.0

    if band in {"fail", "weak"}:
        return 38.0 if clinical else 48.0

    if clinical:
        if not readiness["biology_c_plus"] or not readiness["chemistry_c_plus"]:
            return 38.0
        if points < 7.0:
            return 42.0
        if points < 8.0:
            return 58.0
        return None

    # General health (environmental, community, management, food-related)
    if points < 4.5:
        return 35.0
    if points < 5.5:
        return 48.0
    if points < 6.0:
        return 62.0
    return None
