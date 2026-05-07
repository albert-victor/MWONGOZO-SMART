from mwongozo_smart.core.models import ProgrammeAwardLevel, ProgrammeCategory
from mwongozo_smart.data.guidebook_data import PROGRAMMES
from mwongozo_smart.data.institutions import institution_index


def test_major_tanzania_institutions_are_seeded():
    index = institution_index()
    for code in ["DIT", "IFM", "CBE", "DUCE", "RUCU", "UOI", "SUA", "DMI", "MUHAS", "CUHAS", "KCMCU", "OUT"]:
        assert code in index
        assert index[code].apply_url


def test_new_groupings_exist_in_programme_catalog():
    categories = {programme.category for programme in PROGRAMMES}
    assert ProgrammeCategory.COMPUTING in categories
    assert ProgrammeCategory.ACCOUNTING_FINANCE in categories
    assert ProgrammeCategory.AGRICULTURE in categories
    assert ProgrammeCategory.LAW in categories
    assert ProgrammeCategory.HEALTH in categories


def test_catalog_includes_non_bachelor_routes():
    award_levels = {programme.award_level for programme in PROGRAMMES}
    assert ProgrammeAwardLevel.CERTIFICATE in award_levels
    assert ProgrammeAwardLevel.DIPLOMA in award_levels
    assert ProgrammeAwardLevel.BACHELOR in award_levels
