"""TETEA / Maktaba ACSEE archive HTML (same quoted subject layout as NECTA for many years)."""

from __future__ import annotations

import re
from pathlib import PurePosixPath
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

from mwongozo_smart.exam_lookup.models import NectaSchoolLink
from mwongozo_smart.exam_lookup.parser import normalize_href, parse_acsee_school_page
from mwongozo_smart.exam_lookup.sources.source_router import AcseeUpstream


def parse_tetea_acsee_index_links(html: str, page_url: str) -> list[NectaSchoolLink]:
    """Parse ACSEE alevel.html index: relative links like s0140.htm."""
    soup = BeautifulSoup(html, "html.parser")
    links: list[NectaSchoolLink] = []
    seen: set[str] = set()
    for anchor in soup.find_all("a", href=True):
        href = normalize_href(anchor["href"])
        if not href.lower().endswith(".htm"):
            continue
        if "/" in href and not href.lower().startswith(("http://", "https://")):
            token = PurePosixPath(href.split("/")[-1]).name
        else:
            absolute = urljoin(page_url, href)
            token = PurePosixPath(urlparse(absolute).path).name
        token = token.removesuffix(".htm").removesuffix(".HTM")
        if not re.fullmatch(r"[a-z]\d+", token, flags=re.IGNORECASE):
            continue
        center_number = token.upper()
        if center_number in seen:
            continue
        seen.add(center_number)
        name = " ".join(anchor.get_text(" ", strip=True).split())
        if not name:
            continue
        rel = f"{token.lower()}.htm"
        links.append(NectaSchoolLink(center_number=center_number, school_name=name, result_href=rel))
    links.sort(key=lambda item: item.center_number)
    return links


def parse_tetea_acsee_school_page(html: str, page_url: str, exam_year: int, candidate_norm: str):
    parsed = parse_acsee_school_page(html, page_url, exam_year, candidate_norm)
    return parsed.model_copy(update={"data_source": AcseeUpstream.TETEA_MAKTABA.value})
