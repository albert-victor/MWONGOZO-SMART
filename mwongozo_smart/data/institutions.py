from __future__ import annotations

from mwongozo_smart.core.models import Institution
from mwongozo_smart.db.config import catalogue_seed_on_startup
from mwongozo_smart.db.repositories.catalogue import get_catalogue_repository

_catalogue_repo = get_catalogue_repository()


_DEFAULT_INSTITUTIONS: list[Institution] = [
    Institution(
        code="SUMAIT",
        name="Abdulrahman Al- Sumait University",
        city="Zanzibar",
        region="Zanzibar",
        website="https://www.sumait.ac.tz/",
        apply_url="https://www.sumait.ac.tz/",
    ),
    Institution(
        code="AKU",
        name="Aga Khan University",
        city="Dar es Salaam",
        region="Dar es Salaam",
        website="https://www.aku.edu/",
        apply_url="https://www.aku.edu/admissions/Pages/home.aspx",
    ),
    Institution(
        code="CUHAS",
        name="Catholic University of Health and Allied Sciences",
        city="Mwanza",
        region="Mwanza",
        website="https://bugando.ac.tz/",
        apply_url="https://osim.bugando.ac.tz/apply/bachelor?step=2",
    ),
    Institution(
        code="CUOM",
        name="Catholic University of Mbeya",
        city="Mbeya",
        region="Mbeya",
        website="https://www.cuom.ac.tz/",
        apply_url="https://oas.cuom.ac.tz/",
    ),
    Institution(
        code="A3IPS",
        name="A3 Institute of Professional Studies",
        city="Kibaha",
        region="Pwani",
        website="https://wipahs.co.tz/",
        apply_url="https://wipahs.co.tz/",
    ),
    Institution(
        code="HIHS",
        name="Haydom Institute of Health Sciences",
        city="Haydom",
        region="Manyara",
        website="https://www.hihs.ac.tz/",
        apply_url="https://www.hihs.ac.tz/",
    ),
    Institution(
        code="AMUCTA",
        name="Archbishop Mihayo University College of Tabora",
        city="Tabora",
        region="Tabora",
        website="https://www.amucta.ac.tz/",
        apply_url="https://www.amucta.ac.tz/",
    ),
    Institution(
        code="ARU",
        name="Ardhi University",
        city="Dar es Salaam",
        region="Dar es Salaam",
        website="https://www.aru.ac.tz/",
        apply_url="https://admission.aru.ac.tz/",
    ),
    Institution(
        code="CBE",
        name="College of Business Education",
        city="Dar es Salaam",
        region="Dar es Salaam",
        website="https://www.cbe.ac.tz/",
        apply_url="https://www.cbe.ac.tz/admission/online-application",
    ),
    Institution(
        code="ATC",
        name="Arusha Technical College",
        city="Arusha",
        region="Arusha",
        website="https://www.atc.ac.tz/",
        apply_url="https://www.atc.ac.tz/",
    ),
    Institution(
        code="CAWM",
        name="College of African Wildlife Management, Mweka",
        city="Moshi",
        region="Kilimanjaro",
    ),
    Institution(
        code="CFR",
        name="Centre for Foreign Relations",
        city="Dar es Salaam",
        region="Dar es Salaam",
        website="https://www.cfr.ac.tz/",
        apply_url="https://www.cfr.ac.tz/",
    ),
    Institution(
        code="EASTC",
        name="Eastern Africa Statistical Training Centre",
        city="Dar es Salaam",
        region="Dar es Salaam",
        website="https://www.eastc.ac.tz/",
        apply_url="https://www.eastc.ac.tz/",
    ),
    Institution(
        code="ESAMI",
        name="Eastern and Southern African Management Institute",
        city="Arusha",
        region="Arusha",
        website="https://esami-africa.org/",
        apply_url="https://esami-africa.org/",
    ),
    Institution(
        code="DIT",
        name="Dar es Salaam Institute of Technology",
        city="Dar es Salaam",
        region="Dar es Salaam",
        website="https://www.dit.ac.tz/",
        apply_url="https://admission.dit.ac.tz/",
    ),
    Institution(
        code="DMI",
        name="Dar es Salaam Maritime Institute",
        city="Dar es Salaam",
        region="Dar es Salaam",
        website="https://www.dmi.ac.tz/",
        apply_url="https://www.dmi.ac.tz/welcome",
    ),
    Institution(
        code="DUCE",
        name="Dar es Salaam University College of Education",
        city="Dar es Salaam",
        region="Dar es Salaam",
        website="https://duce.ac.tz/duce",
        apply_url="https://duce.ac.tz/duce/undergraduate-programmes",
    ),
    Institution(
        code="IFM",
        name="Institute of Finance Management",
        city="Dar es Salaam",
        region="Dar es Salaam",
        website="https://www.ifm.ac.tz/",
        apply_url="https://ems.ifm.ac.tz/application",
    ),
    Institution(
        code="MUHAS",
        name="Muhimbili University of Health and Allied Sciences",
        city="Dar es Salaam",
        region="Dar es Salaam",
        website="https://www.muhas.ac.tz/",
        apply_url="https://admission.muhas.ac.tz/",
    ),
    Institution(
        code="KCMCU",
        name="Kilimanjaro Christian Medical University College",
        city="Moshi",
        region="Kilimanjaro",
        website="https://kcmuco.ac.tz/",
        apply_url="https://osim.kcmuco.ac.tz/apply/bachelor?step=2",
    ),
    Institution(
        code="RUCU",
        name="Ruaha Catholic University",
        city="Iringa",
        region="Iringa",
        website="https://www.rucu.ac.tz/",
        apply_url="https://oas.rucu.ac.tz/login",
    ),
    Institution(
        code="SUA",
        name="Sokoine University of Agriculture",
        city="Morogoro",
        region="Morogoro",
        website="https://www.sua.ac.tz/",
        apply_url="https://esb.sua.ac.tz/login",
    ),
    Institution(
        code="UDSM",
        name="University of Dar es Salaam",
        city="Dar es Salaam",
        region="Dar es Salaam",
        website="https://www.udsm.ac.tz/",
        apply_url="https://admission.udsm.ac.tz/",
    ),
    Institution(
        code="OUT",
        name="Open University of Tanzania",
        city="Dar es Salaam",
        region="Dar es Salaam",
        website="https://www.out.ac.tz/",
        apply_url="https://www.out.ac.tz/",
    ),
    Institution(
        code="MUDCCO",
        name="Mzumbe University Dar es Salaam Campus College",
        city="Dar es Salaam",
        region="Dar es Salaam",
    ),
    Institution(
        code="MUMCCO",
        name="Mzumbe University Mbeya Campus College",
        city="Mbeya",
        region="Mbeya",
    ),
    Institution(
        code="SAUT_ARU",
        name="St. Augustine University of Tanzania Arusha Centre",
        city="Arusha",
        region="Arusha",
        website="https://sautarusha.ac.tz/",
        apply_url="https://sautarusha.ac.tz/",
    ),
    Institution(
        code="SFUCHAS",
        name="St. Francis University College of Health and Allied Sciences",
        city="Ifakara",
        region="Morogoro",
    ),
    Institution(
        code="MNMA_PEMBA",
        name="Mwalimu Nyerere Memorial Academy Pemba Campus",
        city="Pemba",
        region="Zanzibar",
        website="https://www.mnma.ac.tz/",
        apply_url="https://www.mnma.ac.tz/pba",
    ),
    Institution(
        code="SUA_KATAVI",
        name="Sokoine University of Agriculture Mizengo Pinda Campus College",
        city="Mpanda",
        region="Katavi",
    ),
    Institution(
        code="UOI",
        name="University of Iringa",
        city="Iringa",
        region="Iringa",
        website="https://www.uoi.ac.tz/",
        apply_url="https://oas.uoi.ac.tz/login/",
    ),
    Institution(
        code="UDOM",
        name="University of Dodoma",
        city="Dodoma",
        region="Dodoma",
        website="https://www.udom.ac.tz/",
        apply_url="https://sr2.udom.ac.tz/",
    ),
    Institution(
        code="SUZA",
        name="State University of Zanzibar",
        city="Zanzibar",
        region="Zanzibar",
        website="https://www.suza.ac.tz/",
        apply_url="https://admission.suza.ac.tz/",
    ),
    Institution(
        code="SAUT",
        name="St. Augustine University of Tanzania",
        city="Mwanza",
        region="Mwanza",
        website="https://www.saut.ac.tz/",
        apply_url="https://admission.saut.ac.tz/",
    ),
    Institution(
        code="HKMU",
        name="Hubert Kairuki Memorial University",
        city="Dar es Salaam",
        region="Dar es Salaam",
        website="https://hkmu.ac.tz/",
        apply_url="https://admission.hkmu.ac.tz/",
    ),
    Institution(
        code="MU",
        name="Mzumbe University",
        city="Morogoro",
        region="Morogoro",
        website="https://www.mzumbe.ac.tz/",
        apply_url="https://admission.mzumbe.ac.tz/",
    ),
    Institution(
        code="MUST",
        name="Mbeya University of Science and Technology",
        city="Mbeya",
        region="Mbeya",
        website="https://www.must.ac.tz/",
        apply_url="https://oas.must.ac.tz/",
    ),
    Institution(
        code="MOCU",
        name="Moshi Co-operative University",
        city="Moshi",
        region="Kilimanjaro",
        website="https://www.mocu.ac.tz/",
        apply_url="https://admission.mocu.ac.tz/",
    ),
    Institution(
        code="TEKU",
        name="Teofilo Kisanji University",
        city="Mbeya",
        region="Mbeya",
        website="https://www.teku.ac.tz/",
        apply_url="https://admission.teku.ac.tz/",
    ),
    Institution(
        code="IAA",
        name="Institute of Accountancy Arusha",
        city="Arusha",
        region="Arusha",
    ),
    Institution(
        code="IAE",
        name="Institute of Adult Education",
        city="Dar es Salaam",
        region="Dar es Salaam",
    ),
    Institution(
        code="IPA",
        name="Institute of Public Administration",
        city="Zanzibar",
        region="Zanzibar",
    ),
    Institution(
        code="IRDP",
        name="Institute of Rural Development Planning",
        city="Dodoma",
        region="Dodoma",
    ),
    Institution(
        code="ISW",
        name="Institute of Social Work",
        city="Dar es Salaam",
        region="Dar es Salaam",
    ),
    Institution(
        code="ITA",
        name="Institute of Tax Administration",
        city="Dar es Salaam",
        region="Dar es Salaam",
    ),
    Institution(
        code="KIUT",
        name="Kampala International University in Tanzania",
        city="Dar es Salaam",
        region="Dar es Salaam",
    ),
    Institution(
        code="MNMA",
        name="Mwalimu Nyerere Memorial Academy",
        city="Dar es Salaam",
        region="Dar es Salaam",
    ),
    Institution(
        code="MNUAT",
        name="Mwalimu Nyerere University of Agriculture and Technology",
        city="Musoma",
        region="Musoma",
    ),
    Institution(
        code="MUCE",
        name="Mkwawa University College of Education",
        city="Iringa",
        region="Iringa",
    ),
    Institution(
        code="MWECAU",
        name="Mwenge Catholic University",
        city="Kilimanjaro",
        region="Kilimanjaro",
    ),
    Institution(
        code="NIT",
        name="National Institute of Transport",
        city="Dar es Salaam",
        region="Dar es Salaam",
    ),
    Institution(
        code="SJCET",
        name="St. Joseph University College of Engineering and Technology",
        city="Dar es Salaam",
        region="Dar es Salaam",
    ),
    Institution(
        code="TIA",
        name="Tanzania Institute of Accountancy",
        city="Dar es Salaam",
        region="Dar es Salaam",
    ),
    Institution(
        code="TICD",
        name="Tengeru Institute of Community Development",
        city="Arusha",
        region="Arusha",
    ),
    Institution(
        code="TIPM",
        name="Tanzania Institute of Project Management",
        city="Dar es Salaam",
        region="Dar es Salaam",
    ),
    Institution(
        code="UAUT",
        name="United African University of Tanzania",
        city="Dar es Salaam",
        region="Dar es Salaam",
    ),
    Institution(
        code="WI",
        name="Water Institute",
        city="Dar es Salaam",
        region="Dar es Salaam",
    ),
    Institution(
        code="ZU",
        name="Zanzibar University",
        city="Zanzibar",
        region="Zanzibar",
    ),
    # NACTVET / NACTE health & private TVET (O-Level certificate & diploma routes)
    Institution(
        code="PRIMUS",
        name="Primus Health Care College",
        city="Dar es Salaam",
        region="Dar es Salaam",
        website="https://primushealth.ac.tz/",
    ),
    Institution(
        code="STJCH",
        name="St. Joseph College of Health and Allied Sciences",
        city="Ifakara",
        region="Morogoro",
    ),
    Institution(
        code="OCEANIC",
        name="Oceanic College of Health Sciences",
        city="Dar es Salaam",
        region="Dar es Salaam",
    ),
    Institution(
        code="BMC",
        name="Benedictine Medical College",
        city="Hulungu",
        region="Ruvuma",
    ),
    Institution(
        code="KCMC_TVET",
        name="Kilimanjaro Christian Medical College (TVET)",
        city="Moshi",
        region="Kilimanjaro",
        website="https://www.kcmc.ac.tz/",
    ),
    Institution(
        code="MARIST_HT",
        name="Marist Health Training Institute",
        city="Morogoro",
        region="Morogoro",
    ),
    Institution(
        code="MUHIMBILI_CT",
        name="Muhimbili College of Health and Allied Sciences",
        city="Dar es Salaam",
        region="Dar es Salaam",
        website="https://www.muhimbili.ac.tz/",
    ),
    Institution(
        code="TANZ_NURSING",
        name="Tanzania Nurses and Midwives Council Training Cluster",
        city="Dar es Salaam",
        region="Dar es Salaam",
    ),
    Institution(
        code="VETA_MS",
        name="VETA Morogoro Regional Centre",
        city="Morogoro",
        region="Morogoro",
    ),
    Institution(
        code="VETA_DS",
        name="VETA Dar es Salaam Regional Centre",
        city="Dar es Salaam",
        region="Dar es Salaam",
    ),
]


if catalogue_seed_on_startup():
    _catalogue_repo.seed_institutions(_DEFAULT_INSTITUTIONS)
INSTITUTIONS: list[Institution] = _catalogue_repo.load_institutions(_DEFAULT_INSTITUTIONS)


def expand_institutions_from_programmes(
    base: list[Institution],
    programmes: list,
) -> list[Institution]:
    from mwongozo_smart.core.models import Programme

    by_code = {item.code: item for item in base}
    for programme in programmes:
        if not isinstance(programme, Programme):
            continue
        if programme.institution_code in by_code:
            continue
        by_code[programme.institution_code] = Institution(
            code=programme.institution_code,
            name=programme.institution_name,
            city=programme.city,
            region=programme.region,
        )
    return list(by_code.values())


def refresh_from_programmes(programmes: list) -> None:
    """Add institutions discovered in the programme catalog (e.g. parsed TCU exports)."""
    global INSTITUTIONS
    expanded = expand_institutions_from_programmes(_DEFAULT_INSTITUTIONS, programmes)
    _catalogue_repo.seed_institutions(expanded)
    INSTITUTIONS = _catalogue_repo.load_institutions(expanded)


def institution_index() -> dict[str, Institution]:
    return {institution.code: institution for institution in INSTITUTIONS}
