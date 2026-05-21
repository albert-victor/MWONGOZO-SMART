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
