from __future__ import annotations

from enum import Enum
from typing import Literal

from mwongozo_smart.exam_lookup.crawler import DEFAULT_BASE_URL
from mwongozo_smart.exam_lookup.models import ExamType

TETEA_CSEE_BASE = "https://maktaba.tetea.org/exam-results"

# Official NECTA onlinesys carries recent CSEE; older years use TETEA mirror.
CSEE_NECTA_ONLINE_MIN_YEAR = 2023

# ACSEE: TETEA Maktaba archive for older years; recent cohorts on NECTA onlinesys.
# NECTA onlinesys publishes ACSEE results from 2023 onwards (2023, 2024, 2025+).
ACSEE_NECTA_ONLINE_MIN_YEAR = 2023


class CseeUpstream(str, Enum):
    NECTA_ONLINESYS = "necta_onlinesys"
    TETEA_MAKTABA = "tetea_maktaba"


class AcseeUpstream(str, Enum):
    NECTA_ONLINESYS = "necta_onlinesys"
    TETEA_MAKTABA = "tetea_maktaba"


def resolve_csee_data_source(exam_year: int) -> CseeUpstream:
    if exam_year >= CSEE_NECTA_ONLINE_MIN_YEAR:
        return CseeUpstream.NECTA_ONLINESYS
    return CseeUpstream.TETEA_MAKTABA


def csee_year_index_url_candidates(exam_year: int, *, necta_base_url: str = DEFAULT_BASE_URL) -> list[str]:
    """Candidate URLs for the CSEE year index. TETEA mixes ``.html`` and ``.htm`` per year."""
    base = necta_base_url.rstrip("/")
    if resolve_csee_data_source(exam_year) is CseeUpstream.NECTA_ONLINESYS:
        return [f"{base}/results/{exam_year}/csee/index.htm"]
    return [
        f"{TETEA_CSEE_BASE}/CSEE{exam_year}/olevel.html",
        f"{TETEA_CSEE_BASE}/CSEE{exam_year}/olevel.htm",
    ]


def csee_year_index_probe_url(exam_year: int, *, necta_base_url: str = DEFAULT_BASE_URL) -> str:
    """Representative CSEE year-index URL (first candidate)."""
    return csee_year_index_url_candidates(exam_year, necta_base_url=necta_base_url)[0]


def csee_centre_page_url_candidates(
    exam_year: int,
    centre_number: str,
    *,
    necta_base_url: str = DEFAULT_BASE_URL,
) -> list[str]:
    """Candidate centre/school page URLs for CSEE (TETEA falls back ``.html`` then ``.htm``)."""
    slug = centre_number.strip().lower()
    base = necta_base_url.rstrip("/")
    if resolve_csee_data_source(exam_year) is CseeUpstream.NECTA_ONLINESYS:
        return [f"{base}/results/{exam_year}/csee/results/{slug}.htm"]
    return [
        f"{TETEA_CSEE_BASE}/CSEE{exam_year}/{slug}.html",
        f"{TETEA_CSEE_BASE}/CSEE{exam_year}/{slug}.htm",
    ]


def csee_centre_page_url(
    exam_year: int,
    centre_number: str,
    *,
    necta_base_url: str = DEFAULT_BASE_URL,
) -> str:
    """Representative absolute school/centre URL for CSEE (first candidate)."""
    return csee_centre_page_url_candidates(exam_year, centre_number, necta_base_url=necta_base_url)[0]


def resolve_acsee_data_source(exam_year: int) -> AcseeUpstream:
    if exam_year >= ACSEE_NECTA_ONLINE_MIN_YEAR:
        return AcseeUpstream.NECTA_ONLINESYS
    return AcseeUpstream.TETEA_MAKTABA


def acsee_year_index_url_candidates(exam_year: int, *, necta_base_url: str = DEFAULT_BASE_URL) -> list[str]:
    """Candidate URLs for the ACSEE year index. TETEA mixes ``alevel.html`` and ``alevel.htm`` per year."""
    base = necta_base_url.rstrip("/")
    if resolve_acsee_data_source(exam_year) is AcseeUpstream.NECTA_ONLINESYS:
        return [f"{base}/results/{exam_year}/acsee/index.htm"]
    return [
        f"{TETEA_CSEE_BASE}/ACSEE{exam_year}/alevel.html",
        f"{TETEA_CSEE_BASE}/ACSEE{exam_year}/alevel.htm",
    ]


def acsee_year_index_probe_url(exam_year: int, *, necta_base_url: str = DEFAULT_BASE_URL) -> str:
    """Representative ACSEE year-index URL (first candidate)."""
    return acsee_year_index_url_candidates(exam_year, necta_base_url=necta_base_url)[0]


def acsee_centre_page_url_candidates(
    exam_year: int,
    centre_number: str,
    *,
    necta_base_url: str = DEFAULT_BASE_URL,
) -> list[str]:
    """Candidate centre/school page URLs for ACSEE (TETEA falls back ``.html`` then ``.htm``)."""
    slug = centre_number.strip().lower()
    base = necta_base_url.rstrip("/")
    if resolve_acsee_data_source(exam_year) is AcseeUpstream.NECTA_ONLINESYS:
        return [f"{base}/results/{exam_year}/acsee/results/{slug}.htm"]
    return [
        f"{TETEA_CSEE_BASE}/ACSEE{exam_year}/{slug}.html",
        f"{TETEA_CSEE_BASE}/ACSEE{exam_year}/{slug}.htm",
    ]


def acsee_centre_page_url(
    exam_year: int,
    centre_number: str,
    *,
    necta_base_url: str = DEFAULT_BASE_URL,
) -> str:
    """Representative absolute school/centre URL for ACSEE (first candidate)."""
    return acsee_centre_page_url_candidates(exam_year, centre_number, necta_base_url=necta_base_url)[0]


def exam_type_lookup_supported(exam: ExamType) -> bool:
    return exam in (ExamType.CSEE, ExamType.ACSEE)


def exam_type_future_only_message(exam: ExamType) -> str:
    return (
        f"Exam type '{exam.value}' is reserved for a future release (PSLE / FTNA wiring). "
        "Use csee or acsee for now."
    )


def assert_supported_exam(exam: ExamType) -> Literal[ExamType.CSEE, ExamType.ACSEE]:
    if exam == ExamType.CSEE:
        return ExamType.CSEE
    if exam == ExamType.ACSEE:
        return ExamType.ACSEE
    raise ValueError(exam_type_future_only_message(exam))
