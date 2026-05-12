"""Strategy objects for CSEE centre-page HTML parsing (NECTA vs TETEA subject formats)."""

from __future__ import annotations

from typing import Protocol

from mwongozo_smart.exam_lookup.models import NectaCseeResult
from mwongozo_smart.exam_lookup.sources.necta_csee_parser import parse_necta_csee_school_page
from mwongozo_smart.exam_lookup.sources.source_router import CseeUpstream, resolve_csee_data_source
from mwongozo_smart.exam_lookup.sources.tetea_csee_parser import parse_tetea_csee_school_page


class CseeCentrePageParser(Protocol):
    def parse(self, html: str, page_url: str, exam_year: int, candidate_norm: str) -> NectaCseeResult: ...


class NectaCseeHtmlStrategy:
    def parse(self, html: str, page_url: str, exam_year: int, candidate_norm: str) -> NectaCseeResult:
        return parse_necta_csee_school_page(html, page_url, exam_year, candidate_norm)


class TeteaCseeHtmlStrategy:
    def parse(self, html: str, page_url: str, exam_year: int, candidate_norm: str) -> NectaCseeResult:
        return parse_tetea_csee_school_page(html, page_url, exam_year, candidate_norm)


def csee_parser_strategy_for_year(exam_year: int) -> CseeCentrePageParser:
    if resolve_csee_data_source(exam_year) is CseeUpstream.NECTA_ONLINESYS:
        return NectaCseeHtmlStrategy()
    return TeteaCseeHtmlStrategy()
