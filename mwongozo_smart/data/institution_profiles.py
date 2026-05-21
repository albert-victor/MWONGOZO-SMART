from __future__ import annotations

from mwongozo_smart.core.models import Institution

# Short blurbs and official programme pages (where known). Counts come from the live catalogue.
_PROFILE_OVERRIDES: dict[str, dict[str, str]] = {
    "RUCU": {
        "summary_sw": "Chuo Kikuu cha Kikatoliki cha Ruaha, Iringa — hutoa sheria, elimu, biashara, ICT, uhasibu, uuguzi na zaidi kulingana na TCU Guidebook 2025/26.",
        "summary_en": "Ruaha Catholic University in Iringa — law, education, business, ICT, accounting, nursing and more per the TCU 2025/26 Guidebook.",
        "programmes_url": "https://www.rucu.ac.tz/",
    },
    "UDSM": {
        "summary_sw": "Chuo kikuu kikuu cha Tanzania, Dar es Salaam — programme nyingi za sayansi, ubunifu, sheria na sanaa.",
        "summary_en": "Tanzania's oldest public university in Dar es Salaam — broad science, engineering, law and arts portfolio.",
        "programmes_url": "https://www.udsm.ac.tz/",
    },
    "UDOM": {
        "summary_sw": "Chuo kikuu cha Dodoma — kipaumbele katika elimu, afya, sheria na taaluma za jamii.",
        "summary_en": "University of Dodoma — strong education, health, law and social sciences offering.",
        "programmes_url": "https://www.udom.ac.tz/",
    },
    "SUA": {
        "summary_sw": "Chuo kikuu cha Kilimo, Morogoro — shahada za kilimo, mifugo, misitu na sayansi ya mazingira.",
        "summary_en": "Sokoine University of Agriculture — agriculture, veterinary, forestry and environmental sciences.",
        "programmes_url": "https://www.sua.ac.tz/",
    },
    "MUHAS": {
        "summary_sw": "Chuo cha afya cha umma, Dar — dawa, uuguzi, udaktari wa meno na taaluma za afya.",
        "summary_en": "Muhimbili University of Health and Allied Sciences — medicine, nursing, dentistry and allied health.",
        "programmes_url": "https://www.muhas.ac.tz/",
    },
    "CUHAS": {
        "summary_sw": "Chuo Kikuu cha Kikatoliki cha Afya na Sayansi Shirikishi, Mwanza — udaktari, uuguzi, pharmacy na maabara pekee (hakuna sheria wala sanaa).",
        "summary_en": "Catholic University of Health and Allied Sciences, Mwanza — medicine, nursing, pharmacy and laboratory sciences only (no law or arts).",
        "programmes_url": "https://osim.bugando.ac.tz/apply/bachelor?step=2",
    },
    "OUT": {
        "summary_sw": "Chuo Huria cha Tanzania — masomo kwa umbali na mchanganyiko katika taaluma mbalimbali.",
        "summary_en": "Open University of Tanzania — distance and blended learning across many disciplines.",
        "programmes_url": "https://www.out.ac.tz/",
    },
}

_SOURCE_LABEL = "TCU Guidebook 2025/2026"


def profile_for(institution: Institution, *, programme_count: int = 0) -> dict[str, str]:
    override = _PROFILE_OVERRIDES.get(institution.code, {})
    if override.get("summary_sw"):
        summary_sw = override["summary_sw"]
    else:
        summary_sw = (
            f"{institution.name} — {institution.city}, {institution.region}. "
            f"Katalogi ina programme {programme_count} zilizosajiliwa kutoka mwongozo wa TCU."
        )
    if override.get("summary_en"):
        summary_en = override["summary_en"]
    else:
        summary_en = (
            f"{institution.name} — {institution.city}, {institution.region}. "
            f"This catalogue lists {programme_count} programmes sourced from the TCU guidebook."
        )
    programmes_url = override.get("programmes_url") or institution.website or institution.apply_url or ""
    return {
        "summary": summary_sw,
        "summary_en": summary_en,
        "programmes_url": programmes_url,
        "source_label": _SOURCE_LABEL,
    }
