"""NECTA onlinesys CSEE centre-page HTML → structured result (quoted subject grades)."""

from __future__ import annotations

from mwongozo_smart.exam_lookup.models import NectaCseeResult
from mwongozo_smart.exam_lookup.parser import parse_school_page
from mwongozo_smart.exam_lookup.sources.source_router import CseeUpstream


def parse_necta_csee_school_page(html: str, page_url: str, exam_year: int, candidate_norm: str) -> NectaCseeResult:
    parsed = parse_school_page(html, page_url, exam_year, candidate_norm)
    return parsed.model_copy(
        update={
            "data_source": CseeUpstream.NECTA_ONLINESYS.value,
        }
    )
