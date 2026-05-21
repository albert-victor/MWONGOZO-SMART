from __future__ import annotations

# Official programme listing pages (curated). Generic paths are tried when not listed.
LIVE_PROGRAMME_URLS: dict[str, list[str]] = {
    "RUCU": [
        "https://www.rucu.ac.tz/",
        "https://www.rucu.ac.tz/academics",
        "https://www.rucu.ac.tz/programmes",
    ],
    "UDSM": [
        "https://www.udsm.ac.tz/en/programmes",
        "https://www.udsm.ac.tz/en/academics",
    ],
    "UDOM": [
        "https://www.udom.ac.tz/programmes",
        "https://www.udom.ac.tz/academics",
    ],
    "SUA": [
        "https://www.sua.ac.tz/programmes",
        "https://www.sua.ac.tz/academics",
    ],
    "MUHAS": [
        "https://www.muhas.ac.tz/programmes",
        "https://muhas.ac.tz/",
    ],
    "OUT": [
        "https://www.out.ac.tz/programmes",
        "https://www.out.ac.tz/academics",
    ],
    "NM-AIST": [
        "https://www.nm-aist.ac.tz/programmes",
    ],
    "DUCE": [
        "https://www.duce.ac.tz/programmes",
    ],
    "SUMAIT": [
        "https://www.sumait.ac.tz/programmes",
    ],
    "CUOM": [
        "https://www.cuom.ac.tz/programmes",
    ],
    "UOI": [
        "https://www.uoi.ac.tz/programmes",
    ],
    "SAUT": [
        "https://www.saut.ac.tz/programmes",
    ],
    "TEKU": [
        "https://www.teku.ac.tz/programmes",
    ],
    "MZUMBE": [
        "https://www.mzumbe.ac.tz/programmes",
    ],
}

_GENERIC_PATH_SUFFIXES = (
    "/programmes",
    "/programs",
    "/academics",
    "/academic-programmes",
    "/courses",
    "/study-programmes",
    "/index.php/programmes",
)


def candidate_urls_for_institution(code: str, website: str | None, programmes_url: str | None) -> list[str]:
    ordered: list[str] = []
    seen: set[str] = set()

    def add(url: str | None) -> None:
        if not url:
            return
        clean = url.strip().rstrip("/")
        if not clean.startswith("http"):
            return
        if clean in seen:
            return
        seen.add(clean)
        ordered.append(clean)

    for url in LIVE_PROGRAMME_URLS.get(code, []):
        add(url)
    add(programmes_url)
    if website:
        base = website.strip().rstrip("/")
        add(base)
        for suffix in _GENERIC_PATH_SUFFIXES:
            add(f"{base}{suffix}")
    return ordered[:8]
