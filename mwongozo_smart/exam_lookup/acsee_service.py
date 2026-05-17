from __future__ import annotations

import asyncio
import logging
import string

import httpx

from mwongozo_smart.core.calculator import get_principal_summary
from mwongozo_smart.core.engine import RecommendationEngine
from mwongozo_smart.core.models import AdmissionPathway, ALevelScheme, StudentResult, SubjectGrade
from mwongozo_smart.data.guidebook_data import PROGRAMMES
from mwongozo_smart.exam_lookup.cache import NectaAcseeCache
from mwongozo_smart.exam_lookup.crawler import NectaHttpCrawler
from mwongozo_smart.exam_lookup.http_errors import (
    NECTA_ONLINE_HINT_EN,
    NECTA_ONLINE_HINT_SW,
    TETEA_HINT_EN,
    TETEA_HINT_SW,
    raise_friendly_httpx_status,
)
from mwongozo_smart.exam_lookup.models import NectaAcseeResult
from mwongozo_smart.exam_lookup.parser import (
    acsee_index_letter_url,
    acsee_index_url,
    acsee_school_result_url,
    parse_acsee_index_school_links,
    parse_candidate_number,
)
from mwongozo_smart.exam_lookup.sources.acsee_parse_strategy import acsee_parser_strategy_for_year
from mwongozo_smart.exam_lookup.sources.source_router import (
    AcseeUpstream,
    acsee_centre_page_url,
    acsee_centre_page_url_candidates,
    acsee_year_index_probe_url,
    acsee_year_index_url_candidates,
    resolve_acsee_data_source,
)
from mwongozo_smart.exam_lookup.sources.tetea_acsee_parser import parse_tetea_acsee_index_links
from mwongozo_smart.utils.combination_helper import infer_combination, normalize_subject_name

logger = logging.getLogger(__name__)


def necta_acsee_to_student_result(
    acsee: NectaAcseeResult,
    *,
    preferred_regions: list[str] | None = None,
    preferred_institutions: list[str] | None = None,
    language: str = "english",
    a_level_scheme: ALevelScheme = ALevelScheme.POST_2016,
) -> StudentResult:
    """Map parsed ACSEE subjects into the internal StudentResult used by the recommendation engine."""
    notes: list[str] = [
        f"ACSEE {acsee.exam_year}",
        f"Data source: {acsee.data_source}",
        f"Candidate {acsee.candidate_number}",
        f"Centre {acsee.center_number}",
    ]
    if acsee.student_name:
        notes.append(f"Student: {acsee.student_name}")
    if acsee.school_name:
        notes.append(f"School: {acsee.school_name}")
    if acsee.region:
        notes.append(f"Region: {acsee.region}")
    if acsee.division:
        notes.append(f"Division / class: {acsee.division}")
    if acsee.aggregate_points is not None:
        notes.append(f"Points (AGGT): {acsee.aggregate_points}")
    if acsee.gpa is not None:
        notes.append(f"GPA: {acsee.gpa}")
    if acsee.centre_gpa is not None:
        notes.append(f"Centre GPA: {acsee.centre_gpa}")

    a_level_subjects: list[SubjectGrade] = []
    for item in acsee.subjects:
        norm = normalize_subject_name(item.name)
        is_general_studies = norm.lower() == "general studies"
        a_level_subjects.append(
            SubjectGrade(
                subject=item.name,
                grade=item.grade,
                principal=not is_general_studies,
                level="a_level",
            )
        )

    combo = acsee.inferred_combination
    if combo is None:
        principal_names = [
            normalize_subject_name(s.name)
            for s in acsee.subjects
            if normalize_subject_name(s.name).lower() != "general studies"
        ]
        combo = infer_combination(principal_names)

    return StudentResult(
        pathway=AdmissionPathway.A_LEVEL,
        a_level_scheme=a_level_scheme,
        a_level_subjects=a_level_subjects,
        o_level_subjects=[],
        combination=combo,
        preferred_regions=preferred_regions or [],
        preferred_institutions=preferred_institutions or [],
        language=language,
        equivalent_qualification=None,
        notes=notes,
    )


def student_result_to_api_input(student: StudentResult) -> dict[str, object]:
    """JSON shape compatible with the existing /recommend StudentInput contract."""
    return {
        "pathway": student.pathway.value,
        "a_level_scheme": student.a_level_scheme.value,
        "a_level_subjects": [
            {"subject": s.subject, "grade": s.grade, "principal": s.principal, "level": s.level} for s in student.a_level_subjects
        ],
        "o_level_subjects": [
            {"subject": s.subject, "grade": s.grade, "principal": s.principal, "level": s.level} for s in student.o_level_subjects
        ],
        "combination": student.combination,
        "preferred_regions": list(student.preferred_regions),
        "preferred_institutions": list(student.preferred_institutions),
        "language": student.language,
        "equivalent_qualification": student.equivalent_qualification,
        "notes": list(student.notes),
    }


class AcseeResultService:
    """ACSEE lookup: NECTA onlinesys (recent years) or TETEA Maktaba archive (older years)."""

    def __init__(
        self,
        *,
        crawler: NectaHttpCrawler | None = None,
        cache: NectaAcseeCache | None = None,
        base_url: str | None = None,
    ) -> None:
        self._crawler = crawler or NectaHttpCrawler()
        self._cache = cache or NectaAcseeCache()
        self._base = base_url or self._crawler.base_url

    async def year_has_acsee(self, exam_year: int) -> bool:
        candidates = acsee_year_index_url_candidates(exam_year, necta_base_url=self._base)
        ok, hit_url = await self._crawler.head_ok_any(candidates)
        logger.info("ACSEE year probe %s -> %s (%s)", candidates, ok, hit_url)
        return ok

    async def refresh_centre_index(self, exam_year: int) -> int:
        upstream = resolve_acsee_data_source(exam_year)
        if upstream is AcseeUpstream.TETEA_MAKTABA:
            candidates = acsee_year_index_url_candidates(exam_year, necta_base_url=self._base)
            try:
                url, html = await self._crawler.fetch_text_first_ok(candidates)
            except httpx.HTTPError as exc:  # noqa: BLE001
                logger.debug("Skip TETEA ACSEE index %s: %s", candidates, exc)
                return 0
            links = parse_tetea_acsee_index_links(html, url)
            if not links:
                return 0
            return self._cache.upsert_school_links(exam_year, links, source_page=url)

        urls: list[str] = [acsee_index_url(self._base, exam_year)]
        for ch in string.ascii_lowercase:
            urls.append(acsee_index_letter_url(self._base, exam_year, ch))

        async def ingest(url: str) -> int:
            try:
                html = await self._crawler.fetch_text(url)
            except httpx.HTTPStatusError as exc:
                if exc.response.status_code == 404:
                    logger.debug("Missing ACSEE index %s", url)
                    return 0
                raise
            except httpx.HTTPError as exc:  # noqa: BLE001
                logger.debug("Skip ACSEE index %s: %s", url, exc)
                return 0
            links = parse_acsee_index_school_links(html, url, exam_year)
            if not links:
                return 0
            return self._cache.upsert_school_links(exam_year, links, source_page=url)

        results = await asyncio.gather(*[ingest(url) for url in urls])
        return sum(results)

    def _cached_fallback(self, exam_year: int, candidate_norm: str, exc: Exception) -> NectaAcseeResult | None:
        cached = self._cache.get_result(exam_year, candidate_norm)
        if not cached:
            return None
        logger.warning(
            "ACSEE live lookup failed (%s); serving cached result for %s %s",
            exc,
            exam_year,
            candidate_norm,
        )
        return cached.model_copy(update={"retrieved_via_cache_fallback": True})

    async def lookup(
        self,
        exam_year: int,
        candidate_number: str,
        *,
        refresh_centre_index: bool = False,
        skip_cache: bool = False,
    ) -> NectaAcseeResult:
        centre, candidate_norm, _ = parse_candidate_number(candidate_number)
        cached = self._cache.get_result(exam_year, candidate_norm)
        if cached and not refresh_centre_index and not skip_cache:
            logger.info("ACSEE cache hit %s %s", exam_year, candidate_norm)
            return cached

        try:
            if refresh_centre_index:
                await self.refresh_centre_index(exam_year)

            upstream = resolve_acsee_data_source(exam_year)
            # NECTA reliably publishes a year index; TETEA stopped publishing year indices for recent years
            # (e.g. ACSEE 2020) even though individual centre pages still exist, so we skip the probe.
            if upstream is AcseeUpstream.NECTA_ONLINESYS and not await self.year_has_acsee(exam_year):
                raise ValueError(
                    f"Matokeo ya ACSEE mwaka {exam_year} hayapatikani kwenye mfumo wa NECTA online. {NECTA_ONLINE_HINT_SW} "
                    f"\nEnglish: ACSEE results for {exam_year} are not published on the NECTA online portal. "
                    f"{NECTA_ONLINE_HINT_EN}"
                )

            candidates = acsee_centre_page_url_candidates(exam_year, centre, necta_base_url=self._base)
            logger.info("Fetching ACSEE centre page candidates %s", candidates)
            try:
                page_url, html = await self._crawler.fetch_text_first_ok(candidates)
            except httpx.HTTPStatusError as exc:
                if exc.response.status_code == 404 and upstream is AcseeUpstream.TETEA_MAKTABA:
                    raise ValueError(
                        f"Matokeo ya ACSEE mwaka {exam_year} kwa kituo {centre} hayapatikani kwenye maktaba ya TETEA "
                        f"(ukurasa wa kituo haupo). Hakikisha namba ya kituo na mwaka ni sahihi. {TETEA_HINT_SW} "
                        f"\nEnglish: ACSEE results for {exam_year} centre {centre} are not available on the TETEA archive "
                        f"(centre page missing). Verify the centre code and year. {TETEA_HINT_EN}"
                    ) from exc
                raise_friendly_httpx_status(exc, exam="ACSEE", year=exam_year, centre=centre, url=candidates[-1])
            strategy = acsee_parser_strategy_for_year(exam_year)
            parsed = strategy.parse(html, page_url, exam_year, candidate_norm)
            self._cache.put_result(exam_year, candidate_norm, parsed)
            return parsed
        except (httpx.HTTPError, httpx.RequestError) as exc:
            fallback = self._cached_fallback(exam_year, candidate_norm, exc)
            if fallback is not None:
                return fallback
            raise

    def recommend_from_acsee(
        self,
        acsee: NectaAcseeResult,
        engine: RecommendationEngine,
        *,
        limit: int = 120,
        preferred_regions: list[str] | None = None,
        preferred_institutions: list[str] | None = None,
        language: str = "english",
        a_level_scheme: ALevelScheme = ALevelScheme.POST_2016,
    ) -> dict[str, object]:
        student_result = necta_acsee_to_student_result(
            acsee,
            preferred_regions=preferred_regions,
            preferred_institutions=preferred_institutions,
            language=language,
            a_level_scheme=a_level_scheme,
        )
        principal = get_principal_summary(student_result)
        recs = engine.recommend(student_result, limit=limit)
        review_limit = min(180, max(80, limit + 40))
        review = engine.review_candidates(student_result, limit=review_limit)
        combinations = engine.suggest_combinations(student_result)
        return {
            "necta": acsee.model_dump(mode="json"),
            "input": student_result_to_api_input(student_result),
            "tcu_points": principal.total_points,
            "principal_count": principal.principal_count,
            "loaded_programmes": len(PROGRAMMES),
            "count": len(recs),
            "recommendations": [item.model_dump(mode="json") for item in recs],
            "review_candidates": [item.model_dump(mode="json") for item in review],
            "combination_suggestions": [item.model_dump(mode="json") for item in combinations],
        }
