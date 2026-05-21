from __future__ import annotations

from mwongozo_smart.core.models import Institution, Programme, ProgrammeCategory, ProgrammeAwardLevel
from mwongozo_smart.db.catalogue_merge import merge_institution, merge_institutions, merge_programme, merge_programmes
from mwongozo_smart.db.config import CatalogueReadMode, CatalogueWriteMode
from mwongozo_smart.db.repositories.catalogue import CatalogueRepository


def test_merge_institution_prefers_loaded_non_empty_fields() -> None:
    default = Institution(code="UDSM", name="Default", city="Dar", region="Dar es Salaam")
    loaded = Institution(code="UDSM", name="University of Dar es Salaam", city="Dar", region="Dar es Salaam", website="https://udsm.ac.tz")
    merged = merge_institution(default, loaded)
    assert merged.name == "University of Dar es Salaam"
    assert merged.website == "https://udsm.ac.tz"


def test_merge_programmes_keeps_defaults_when_loaded_missing() -> None:
    defaults = [
        Programme(
            code="P1",
            name="Prog",
            institution_code="UDSM",
            institution_name="UDSM",
            city="Dar",
            region="Dar es Salaam",
        )
    ]
    merged = merge_programmes(defaults, [])
    assert len(merged) == 1
    assert merged[0].code == "P1"


def test_catalogue_repository_defaults_to_sqlite_modes() -> None:
    repo = CatalogueRepository()
    assert repo._read_mode == CatalogueReadMode.SQLITE
    assert repo._write_mode == CatalogueWriteMode.SQLITE


def test_requirement_roundtrip_helper() -> None:
    from mwongozo_smart.db.repositories.catalogue import _programme_to_rows, _row_to_programme

    programme = Programme(
        code="TEST-001",
        name="Test Programme",
        institution_code="UDSM",
        institution_name="UDSM",
        city="Dar",
        region="Dar es Salaam",
        category=ProgrammeCategory.COMPUTING,
        award_level=ProgrammeAwardLevel.BACHELOR,
        tags=["computing"],
    )
    row, req = _programme_to_rows(programme, institution_id=1)
    assert row["code"] == "TEST-001"
    assert req["minimum_principal_passes"] == programme.admission_requirement.minimum_principal_passes
    rebuilt = _row_to_programme(
        {
            **row,
            "institution_code": "UDSM",
            "institution_name": "UDSM",
            "category": programme.category.value,
            "award_level": programme.award_level.value,
        },
        req,
    )
    assert rebuilt.code == programme.code
    assert rebuilt.category == programme.category
