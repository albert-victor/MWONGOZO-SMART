from mwongozo_smart.core.models import ProgrammeCategory
from mwongozo_smart.data.guidebook_data import PROGRAMMES
from mwongozo_smart.data.guidebook_export_parser import load_parsed_programmes
from mwongozo_smart.data.institution_catalog import apply_institution_catalog_rules


def test_cuhas_has_no_law_or_arts_programmes():
    cuhas = [p for p in PROGRAMMES if p.institution_code == "CUHAS"]
    assert cuhas
    assert all(p.category == ProgrammeCategory.HEALTH for p in cuhas)
    names = " ".join(p.name.lower() for p in cuhas)
    assert "laws" not in names
    assert "social work" not in names


def test_cm_codes_map_to_cuom_not_cuhas():
    parsed = {p.code: p for p in load_parsed_programmes()}
    assert parsed["CM003"].institution_code == "CUOM"
    assert parsed["CM003"].category == ProgrammeCategory.LAW
    fixed = apply_institution_catalog_rules(parsed["CM003"])
    assert fixed is not None
    assert fixed.institution_code == "CUOM"


def test_law_at_cuhas_is_dropped():
    from mwongozo_smart.core.models import Programme, ProgrammeAwardLevel
    from mwongozo_smart.data.institutions import institution_index

    cuhas = institution_index()["CUHAS"]
    rogue = Programme(
        code="BAD01",
        name="Bachelor of Laws",
        institution_code="CUHAS",
        institution_name=cuhas.name,
        city=cuhas.city,
        region=cuhas.region,
        category=ProgrammeCategory.LAW,
        award_level=ProgrammeAwardLevel.BACHELOR,
    )
    assert apply_institution_catalog_rules(rogue) is None
