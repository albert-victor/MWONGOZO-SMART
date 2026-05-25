from __future__ import annotations

from mwongozo_smart.core.models import Institution, Programme


def merge_institution(default_item: Institution, loaded_item: Institution) -> Institution:
    payload = default_item.model_dump()
    loaded_payload = loaded_item.model_dump()
    for key in ("code", "name", "city", "region", "website", "apply_url", "cta_label"):
        value = loaded_payload.get(key)
        if value not in (None, ""):
            payload[key] = value
    return Institution.model_validate(payload)


def merge_programme(default_item: Programme, loaded_item: Programme) -> Programme:
    payload = default_item.model_dump()
    loaded_payload = loaded_item.model_dump()
    for key in (
        "code",
        "name",
        "institution_code",
        "institution_name",
        "city",
        "region",
        "category",
        "award_level",
        "duration_years",
        "capacity",
        "competition_tier",
        "tags",
    ):
        value = loaded_payload.get(key)
        if value not in (None, "", []):
            payload[key] = value
    return Programme.model_validate(payload)


def merge_institutions(defaults: list[Institution], loaded: list[Institution]) -> list[Institution]:
    default_by_code = {item.code: item for item in defaults}
    loaded_by_code = {item.code: item for item in loaded}
    merged: list[Institution] = []
    for default_item in defaults:
        loaded_item = loaded_by_code.get(default_item.code)
        merged.append(merge_institution(default_item, loaded_item) if loaded_item else default_item)
    for item in loaded:
        if item.code not in default_by_code:
            merged.append(item)
    return merged


def merge_programmes(defaults: list[Programme], loaded: list[Programme]) -> list[Programme]:
    default_by_code = {item.code: item for item in defaults}
    loaded_by_code = {item.code: item for item in loaded}
    merged: list[Programme] = []
    for default_item in defaults:
        loaded_item = loaded_by_code.get(default_item.code)
        merged.append(merge_programme(default_item, loaded_item) if loaded_item else default_item)
    return merged


def _institution_richness(institution: Institution) -> int:
    score = 0
    if institution.website:
        score += 4
    if institution.apply_url:
        score += 2
    if institution.city:
        score += 1
    return score


def pick_canonical_institution_code(
    codes: list[str],
    *,
    preferred_codes: frozenset[str] | None = None,
) -> str:
    """Pick one code when SQLite has case variants (e.g. MOCU vs MoCU)."""
    preferred_codes = preferred_codes or frozenset()
    for code in codes:
        if code in preferred_codes:
            return code
    upper = [code for code in codes if code.isupper()]
    if upper:
        return sorted(upper)[0]
    return sorted(codes)[0]


def dedupe_institutions_case_insensitive(
    institutions: list[Institution],
    *,
    preferred_codes: frozenset[str] | None = None,
) -> tuple[list[Institution], dict[str, str]]:
    """Collapse case variants for MySQL (unicode_ci unique on code).

    Returns deduped institutions and a map from any seen code -> canonical code.
    """
    groups: dict[str, list[Institution]] = {}
    for institution in institutions:
        groups.setdefault(institution.code.upper(), []).append(institution)

    deduped: list[Institution] = []
    alias_to_canonical: dict[str, str] = {}

    for group in groups.values():
        canonical_code = pick_canonical_institution_code(
            [item.code for item in group],
            preferred_codes=preferred_codes,
        )
        merged = group[0]
        for other in group[1:]:
            merged = merge_institution(merged, other)

        payload = merged.model_dump()
        payload["code"] = canonical_code
        canonical = Institution.model_validate(payload)
        deduped.append(canonical)

        for item in group:
            alias_to_canonical[item.code] = canonical_code
            alias_to_canonical[item.code.upper()] = canonical_code

    deduped.sort(key=lambda item: item.code)
    return deduped, alias_to_canonical


def normalize_programmes_institution_codes(
    programmes: list[Programme],
    alias_to_canonical: dict[str, str],
) -> list[Programme]:
    normalized: list[Programme] = []
    for programme in programmes:
        canonical = alias_to_canonical.get(programme.institution_code) or alias_to_canonical.get(
            programme.institution_code.upper()
        )
        if not canonical or canonical == programme.institution_code:
            normalized.append(programme)
            continue
        payload = programme.model_dump()
        payload["institution_code"] = canonical
        normalized.append(Programme.model_validate(payload))
    return normalized
