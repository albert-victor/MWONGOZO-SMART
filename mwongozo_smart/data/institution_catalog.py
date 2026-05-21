"""Institution-specific catalogue rules (TCU guidebook corrections)."""

from __future__ import annotations

from mwongozo_smart.core.models import Programme, ProgrammeCategory

# Programme code prefixes that always belong to a given institution (guidebook TCU codes).
_CODE_PREFIX_INSTITUTION: dict[str, str] = {
    "CM": "CUOM",
    "CUH": "CUHAS",
    "CUOM": "CUOM",
}

# Health-only universities — no law, arts, or general business under these codes.
_HEALTH_ONLY_INSTITUTIONS: frozenset[str] = frozenset(
    {
        "CUHAS",
        "MUHAS",
        "KCMCU",
        "HKMU",
        "HIHS",
        "SFUCHAS",
        "BMC",
    }
)

_INSTITUTION_ALLOWED_CATEGORIES: dict[str, frozenset[ProgrammeCategory]] = {
    code: frozenset({ProgrammeCategory.HEALTH}) for code in _HEALTH_ONLY_INSTITUTIONS
}


def normalize_institution_code(raw: str) -> str:
    return raw.strip().upper().replace(" ", "")


def institution_for_programme_code(code: str) -> str | None:
    upper = code.strip().upper()
    for prefix, institution_code in sorted(_CODE_PREFIX_INSTITUTION.items(), key=lambda item: -len(item[0])):
        if upper.startswith(prefix):
            return institution_code
    return None


def is_programme_allowed_for_institution(programme: Programme) -> bool:
    allowed = _INSTITUTION_ALLOWED_CATEGORIES.get(programme.institution_code.upper())
    if allowed is None:
        return True
    return programme.category in allowed


def apply_institution_catalog_rules(programme: Programme) -> Programme | None:
    """Reassign institution from TCU code prefix and drop programmes that violate scope."""
    code = programme.code.strip().upper()
    forced = institution_for_programme_code(code)
    institution_code = forced or programme.institution_code.upper()

    if forced:
        from mwongozo_smart.data.institutions import institution_index

        institution = institution_index().get(forced)
        if institution:
            programme = programme.model_copy(
                update={
                    "institution_code": institution.code,
                    "institution_name": institution.name,
                    "city": institution.city,
                    "region": institution.region,
                }
            )
        else:
            programme = programme.model_copy(update={"institution_code": forced})

    if not is_programme_allowed_for_institution(programme):
        return None
    return programme


def filter_catalog_programmes(programmes: list[Programme]) -> list[Programme]:
    kept: list[Programme] = []
    for programme in programmes:
        fixed = apply_institution_catalog_rules(programme)
        if fixed is not None:
            kept.append(fixed)
    return kept
