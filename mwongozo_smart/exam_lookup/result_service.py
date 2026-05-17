from __future__ import annotations

import logging
import string
from typing import Any

import httpx

from mwongozo_smart.core.models import AdmissionPathway, ALevelScheme, StudentResult, SubjectGrade
from mwongozo_smart.exam_lookup.cache import NectaLookupCache
from mwongozo_smart.exam_lookup.crawler import DEFAULT_BASE_URL, NectaCseeCrawler
from mwongozo_smart.exam_lookup.models import NectaCseeResult
from mwongozo_smart.exam_lookup.parser import parse_candidate_number, parse_index_school_links
from mwongozo_smart.exam_lookup.sources.csee_parse_strategy import csee_parser_strategy_for_year
from mwongozo_smart.exam_lookup.sources.source_router import (
    CseeUpstream,
    CSEE_NECTA_ONLINE_MIN_YEAR,
    csee_centre_page_url,
    csee_centre_page_url_candidates,
    csee_year_index_probe_url,
    csee_year_index_url_candidates,
    resolve_csee_data_source,
)

from mwongozo_smart.exam_lookup.http_errors import (
    NECTA_ONLINE_HINT_EN,
    NECTA_ONLINE_HINT_SW,
    TETEA_HINT_EN,
    TETEA_HINT_SW,
    raise_friendly_httpx_status as _raise_friendly_httpx_status,
)

logger = logging.getLogger(__name__)


def necta_result_to_student_payload(result: NectaCseeResult) -> dict[str, Any]:
    o_level_subjects = [
        {"subject": item.name, "grade": item.grade, "principal": True, "level": "o_level"} for item in result.subjects
    ]
    notes = [
        f"Division: {result.division}",
        "Result model: necta_csee_official",
        f"Data source: {result.data_source}",
        f"School: {result.school_name}",
        f"Centre: {result.center_number}",
        f"NECTA CNO: {result.candidate_number}",
        f"Result page: {result.source_url}",
    ]
    if result.region:
        notes.append(f"Region: {result.region}")
    return {
        "pathway": "o_level",
        "a_level_scheme": "2016_plus",
        "a_level_subjects": [],
        "o_level_subjects": o_level_subjects,
        "combination": None,
        "preferred_regions": [],
        "preferred_institutions": [],
        "language": "english",
        "equivalent_qualification": None,
        "notes": notes,
    }


def necta_csee_result_to_student_result(
    result: NectaCseeResult,
    *,
    preferred_regions: list[str] | None = None,
    preferred_institutions: list[str] | None = None,
    language: str = "english",
    a_level_scheme: ALevelScheme = ALevelScheme.POST_2016,
) -> StudentResult:
    """Map a parsed CSEE row into StudentResult (same semantics as StudentInput for o_level pathway)."""
    o_level_subjects = [
        SubjectGrade(subject=item.name, grade=item.grade, principal=True, level="o_level") for item in result.subjects
    ]
    notes = list(necta_result_to_student_payload(result)["notes"])
    return StudentResult(
        pathway=AdmissionPathway.O_LEVEL,
        a_level_scheme=a_level_scheme,
        a_level_subjects=[],
        o_level_subjects=o_level_subjects,
        combination=None,
        preferred_regions=preferred_regions or [],
        preferred_institutions=preferred_institutions or [],
        language=language,
        equivalent_qualification=None,
        notes=notes,
    )


class CseeResultService:
    def __init__(
        self,
        *,
        base_url: str = DEFAULT_BASE_URL,
        cache: NectaLookupCache | None = None,
        crawler: NectaCseeCrawler | None = None,
    ) -> None:
        self._base = base_url.rstrip("/")
        self._cache = cache or NectaLookupCache()
        self._crawler = crawler or NectaCseeCrawler(base_url=self._base)

    def year_index_url(self, year: int) -> str:
        return f"{self._base}/results/{year}/csee/index.htm"

    async def year_is_available(self, year: int) -> bool:
        ok, _ = await self._crawler.head_ok_any(
            csee_year_index_url_candidates(year, necta_base_url=self._base)
        )
        return ok

    def _cached_fallback(self, year: int, candidate_norm: str, exc: Exception) -> NectaCseeResult | None:
        cached = self._cache.get_result(year, candidate_norm)
        if not cached:
            return None
        logger.warning(
            "CSEE live lookup failed (%s); serving cached result for %s %s",
            exc,
            year,
            candidate_norm,
        )
        return cached.model_copy(update={"retrieved_via_cache_fallback": True})

    async def lookup(self, year: int, candidate_number: str, *, skip_cache: bool = False) -> NectaCseeResult:
        centre, candidate_norm, _serial = parse_candidate_number(candidate_number)
        if not skip_cache:
            cached = self._cache.get_result(year, candidate_norm)
            if cached:
                logger.info("CSEE cache hit for %s %s", year, candidate_norm)
                return cached

        try:
            upstream = resolve_csee_data_source(year)
            # NECTA reliably publishes a year index; for TETEA we skip the index probe
            # (TETEA stopped publishing year indices for 2019+ even though centre pages still exist).
            if upstream is CseeUpstream.NECTA_ONLINESYS and not await self.year_is_available(year):
                raise ValueError(
                    f"Matokeo ya CSEE mwaka {year} hayapatikani kwenye mfumo wa NECTA online (rejeleo limeondolewa au halipo). "
                    f"{NECTA_ONLINE_HINT_SW} "
                    f"\nEnglish: CSEE results for {year} are not available on the NECTA online portal (index missing). "
                    f"{NECTA_ONLINE_HINT_EN}"
                )

            candidates = csee_centre_page_url_candidates(year, centre, necta_base_url=self._base)
            logger.info("Fetching CSEE centre page candidates %s", candidates)
            try:
                page_url, html = await self._crawler.fetch_text_first_ok(candidates)
            except httpx.HTTPStatusError as exc:
                if exc.response.status_code == 404 and upstream is CseeUpstream.TETEA_MAKTABA:
                    raise ValueError(
                        f"Matokeo ya CSEE mwaka {year} kwa kituo {centre} hayapatikani kwenye maktaba ya TETEA "
                        f"(ukurasa wa kituo haupo). Hakikisha namba ya kituo na mwaka ni sahihi. {TETEA_HINT_SW} "
                        f"\nEnglish: CSEE results for {year} centre {centre} are not available on the TETEA archive "
                        f"(centre page missing). Verify the centre code and year. {TETEA_HINT_EN}"
                    ) from exc
                _raise_friendly_httpx_status(exc, exam="CSEE", year=year, centre=centre, url=candidates[-1])
            strategy = csee_parser_strategy_for_year(year)
            result = strategy.parse(html, page_url, year, candidate_norm)
            self._cache.put_result(year, candidate_norm, result)
            return result
        except (httpx.HTTPError, httpx.RequestError) as exc:
            fallback = self._cached_fallback(year, candidate_norm, exc)
            if fallback is not None:
                return fallback
            raise

    async def build_centre_index(self, year: int, *, clear_existing: bool = False) -> int:
        if year < CSEE_NECTA_ONLINE_MIN_YEAR:
            raise ValueError(
                "Kituo-crawl ya CSEE inapatikana tu kwa miaka ya NECTA online (>= 2023). "
                "Kwa miaka ya zamani tumia utafutaji wa moja kwa moja (TETEA) kupitia nambari ya kituo."
                "\nEnglish: CSEE centre index crawl is only supported for NECTA online years (>= 2023). "
                "For older years use direct lookup via centre number (TETEA archive)."
            )
        if not await self.year_is_available(year):
            raise ValueError(
                f"Matokeo ya CSEE mwaka {year} hayapatikani kwenye mfumo wa NECTA online. {NECTA_ONLINE_HINT_SW} "
                f"\nEnglish: CSEE results for {year} are not available. {NECTA_ONLINE_HINT_EN}"
            )

        if clear_existing:
            self._cache.clear_year(year)

        letter_urls = [f"{self._base}/results/{year}/csee/index_{letter}.htm" for letter in string.ascii_lowercase]
        main_url = self.year_index_url(year)

        async def ingest(url: str) -> int:
            try:
                html = await self._crawler.fetch_text(url)
            except httpx.HTTPStatusError as exc:
                if exc.response.status_code == 404:
                    logger.info("Skipping missing NECTA index page %s", url)
                    return 0
                raise
            links = parse_index_school_links(html, url)
            if not links:
                return 0
            source = url.rsplit("/", maxsplit=1)[-1]
            inserted = self._cache.upsert_school_links(year, links, source_page=source)
            logger.info("Indexed %s centres from %s", inserted, url)
            return inserted

        for url in [*letter_urls, main_url]:
            await ingest(url)
        return len(self._cache.list_school_links(year))
