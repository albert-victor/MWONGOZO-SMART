from __future__ import annotations

from pathlib import Path

from mwongozo_smart.exam_lookup.cache import NectaLookupCache
from mwongozo_smart.exam_lookup.models import NectaCseeResult, NectaSchoolLink, NectaSubjectGrade


def test_cache_roundtrip_result(tmp_path: Path) -> None:
    db = tmp_path / "cache.sqlite3"
    cache = NectaLookupCache(db_path=db)
    result = NectaCseeResult(
        exam_year=2022,
        candidate_number="S1027/0001",
        school_name="CHAMWINO SECONDARY SCHOOL",
        center_number="S1027",
        division="II",
        subjects=[NectaSubjectGrade(code="CIV", name="Civics", grade="C")],
        source_url="https://example.invalid/results.htm",
    )
    cache.put_result(2022, "S1027/0001", result)
    loaded = cache.get_result(2022, "S1027/0001")
    assert loaded is not None
    assert loaded.model_dump() == result.model_dump()


def test_cache_upsert_school_links(tmp_path: Path) -> None:
    db = tmp_path / "cache.sqlite3"
    cache = NectaLookupCache(db_path=db)
    links = [
        NectaSchoolLink(center_number="P0101", school_name="AZANIA CENTRE", result_href="results/p0101.htm"),
    ]
    cache.upsert_school_links(2022, links, source_page="index.htm")
    rows = cache.list_school_links(2022)
    assert len(rows) == 1
    assert rows[0].center_number == "P0101"


def test_csee_lookup_falls_back_to_cache_on_network_error(tmp_path: Path) -> None:
    import asyncio
    from unittest.mock import AsyncMock, patch

    import httpx

    from mwongozo_smart.exam_lookup.result_service import CseeResultService

    db = tmp_path / "csee.sqlite3"
    cache = NectaLookupCache(db_path=db)
    stored = NectaCseeResult(
        exam_year=2024,
        candidate_number="S0140/0012",
        school_name="DEMO SCHOOL",
        center_number="S0140",
        division="II",
        subjects=[NectaSubjectGrade(code="PHY", name="Physics", grade="B")],
        source_url="https://example.invalid/demo.htm",
        data_source="necta_onlinesys",
    )
    cache.put_result(2024, "S0140/0012", stored)
    service = CseeResultService(cache=cache)

    async def run() -> NectaCseeResult:
        with (
            patch.object(service, "year_is_available", new=AsyncMock(return_value=True)),
            patch.object(service._crawler, "fetch_text_first_ok", new=AsyncMock(side_effect=httpx.ConnectError("offline"))),
        ):
            return await service.lookup(2024, "S0140/0012", skip_cache=True)

    loaded = asyncio.run(run())
    assert loaded.retrieved_via_cache_fallback is True
    assert loaded.candidate_number == "S0140/0012"
    assert loaded.division == "II"
