"""Heuristics for institution ownership and kind (TCU directory UI)."""
from __future__ import annotations

from mwongozo_smart.core.models import Institution

# Known private / faith-based universities (TCU-registered, non-public).
_PRIVATE_CODES: frozenset[str] = frozenset(
    {
        "AKU",
        "SAUT",
        "SAUT_ARU",
        "OUT",
        "TEKU",
        "KIUT",
        "UAUT",
        "ZU",
        "SUMAIT",
        "AMUCTA",
        "CUOM",
        "HIHS",
        "HKMU",
        "MWECAU",
        "SFUCHAS",
        "UOI",
        "PRIMUS",
        "STJCH",
        "OCEANIC",
        "BMC",
        "MARIST_HT",
    }
)

_PRIVATE_NAME_MARKERS: tuple[str, ...] = (
    "private",
    "international university",
    "aga khan",
    "catholic university",
    "islamic university",
    "muslim university",
    "st. augustine",
    "st augustine",
    "hubert kairuki",
    "mount meru",
    "out college",
    "zanzibar university",
)

_COLLEGE_MARKERS: tuple[str, ...] = (
    "technical college",
    "teachers college",
    "institute of",
    "institute for",
    "college of business",
    "college of african",
    "centre for",
    "center for",
    "school of",
    "polytechnic",
    "training centre",
    "training center",
)


def classify_institution(institution: Institution) -> dict[str, str]:
    """Return ownership (public|private) and kind (university|college|other)."""
    name_l = institution.name.lower()
    code = institution.code.upper()

    ownership = "private" if code in _PRIVATE_CODES else "public"
    if ownership == "public":
        if any(m in name_l for m in _PRIVATE_NAME_MARKERS):
            ownership = "private"
        elif "private" in name_l:
            ownership = "private"

    kind = "other"
    if "university college" in name_l or "university of" in name_l or name_l.endswith(" university"):
        kind = "university"
    elif "university" in name_l:
        kind = "university"
    elif any(m in name_l for m in _COLLEGE_MARKERS) or " college" in name_l:
        kind = "college"
    elif "institute" in name_l:
        kind = "college"

    return {"ownership": ownership, "kind": kind}
