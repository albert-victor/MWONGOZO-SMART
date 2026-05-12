"""Strategy objects for ACSEE centre-page HTML parsing (NECTA onlinesys vs TETEA archive)."""

from __future__ import annotations

from typing import Protocol

from mwongozo_smart.exam_lookup.models import NectaAcseeResult
from mwongozo_smart.exam_lookup.sources.necta_acsee_parser import parse_necta_acsee_school_page
from mwongozo_smart.exam_lookup.sources.source_router import AcseeUpstream, resolve_acsee_data_source
from mwongozo_smart.exam_lookup.sources.tetea_acsee_parser import parse_tetea_acsee_school_page


class AcseeCentrePageParser(Protocol):
    def parse(self, html: str, page_url: str, exam_year: int, candidate_norm: str) -> NectaAcseeResult: ...


class NectaAcseeHtmlStrategy:
    def parse(self, html: str, page_url: str, exam_year: int, candidate_norm: str) -> NectaAcseeResult:
        return parse_necta_acsee_school_page(html, page_url, exam_year, candidate_norm)


class TeteaAcseeHtmlStrategy:
    def parse(self, html: str, page_url: str, exam_year: int, candidate_norm: str) -> NectaAcseeResult:
        return parse_tetea_acsee_school_page(html, page_url, exam_year, candidate_norm)


def acsee_parser_strategy_for_year(exam_year: int) -> AcseeCentrePageParser:
    if resolve_acsee_data_source(exam_year) is AcseeUpstream.NECTA_ONLINESYS:
        return NectaAcseeHtmlStrategy()
    return TeteaAcseeHtmlStrategy()
