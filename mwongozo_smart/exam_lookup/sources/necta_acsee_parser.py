"""Official NECTA ACSEE centre-page parsing (thin wrapper for strategy / imports)."""

from __future__ import annotations

from mwongozo_smart.exam_lookup.models import NectaAcseeResult
from mwongozo_smart.exam_lookup.parser import parse_acsee_school_page
from mwongozo_smart.exam_lookup.sources.source_router import AcseeUpstream


def parse_necta_acsee_school_page(html: str, page_url: str, exam_year: int, candidate_norm: str) -> NectaAcseeResult:
    parsed = parse_acsee_school_page(html, page_url, exam_year, candidate_norm)
    return parsed.model_copy(update={"data_source": AcseeUpstream.NECTA_ONLINESYS.value})
