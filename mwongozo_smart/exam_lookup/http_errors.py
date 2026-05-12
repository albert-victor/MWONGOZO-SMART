from __future__ import annotations

import httpx

NECTA_ONLINE_HINT_SW = (
    "NECTA online (onlinesys.necta.go.tz) huweka miaka ya karibu tu; miaka kama 2020 mara nyingi imeondolewa. "
    "Jaribu mwaka unaopatikana (mfano 2022–2026). Hakikisha umechagua Form 4 kwa CSEE au Form 6 kwa ACSEE."
)
NECTA_ONLINE_HINT_EN = (
    "The NECTA online portal often keeps only recent years; older years such as 2020 may return 404. "
    "Try an available year (e.g. 2022–2026). Confirm you use Form 4 / CSEE or Form 6 / ACSEE — centre URLs differ."
)

TETEA_HINT_SW = (
    "Maktaba ya TETEA inaweza kuwa na miaka fulani tu; ukikosa olevel.htm/alevel.html au ukurasa wa kituo, jaribu mwaka mwingine au "
    "hakikisha namba ya kituo na CNO ni sahihi."
)
TETEA_HINT_EN = (
    "The TETEA archive may not host every year; if the index or centre page is missing, try another year or verify "
    "the centre code and candidate number."
)


def raise_friendly_httpx_status(exc: httpx.HTTPStatusError, *, exam: str, year: int, centre: str, url: str) -> None:
    code = exc.response.status_code
    is_tetea = "maktaba.tetea.org" in url.lower()
    if code == 404:
        if is_tetea:
            raise ValueError(
                f"TETEA imerudisha 404 kwa {exam} mwaka {year}, kituo {centre}. {TETEA_HINT_SW} "
                f"\nEnglish: TETEA returned 404 for {exam} year {year}, centre {centre}. {TETEA_HINT_EN} URL: {url}"
            ) from exc
        raise ValueError(
            f"NECTA imerudisha 404 (Not Found) kwa {exam} mwaka {year}, kituo {centre}. "
            f"{NECTA_ONLINE_HINT_SW} "
            f"\nEnglish: NECTA returned 404 for {exam} year {year}, centre {centre}. {NECTA_ONLINE_HINT_EN} "
            f"URL: {url}"
        ) from exc
    raise ValueError(f"Upstream HTTP {code} for {url}: {exc}") from exc
