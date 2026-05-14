from __future__ import annotations

from pathlib import Path

import pytest

from mwongozo_smart.exam_lookup.models import ExamType
from mwongozo_smart.exam_lookup.parser import (
    parse_candidate_number,
    parse_index_school_links,
    parse_school_page,
    parse_subject_blob,
    parse_subject_blob_tetea,
)
from mwongozo_smart.exam_lookup.result_service import necta_result_to_student_payload
from mwongozo_smart.exam_lookup.sources.source_router import (
    CseeUpstream,
    assert_supported_exam,
    csee_centre_page_url,
    csee_year_index_probe_url,
    resolve_csee_data_source,
)
from mwongozo_smart.exam_lookup.sources.tetea_csee_parser import parse_tetea_csee_school_page

FIXTURES = Path(__file__).resolve().parent / "fixtures"


def test_assert_supported_exam_rejects_psle() -> None:
    with pytest.raises(ValueError, match="reserved"):
        assert_supported_exam(ExamType.PSLE)


def test_parse_candidate_number_slash_and_hyphen() -> None:
    centre, norm, serial = parse_candidate_number("s1027/34")
    assert centre == "S1027"
    assert norm == "S1027/0034"
    assert serial == "0034"
    centre2, norm2, _ = parse_candidate_number("S1027-0034")
    assert norm2 == norm
    assert centre2 == "S1027"


def test_parse_candidate_number_invalid() -> None:
    with pytest.raises(ValueError):
        parse_candidate_number("12345")


def test_parse_index_school_links_reads_backslash_href() -> None:
    html = (FIXTURES / "necta_index_snippet.html").read_text(encoding="utf-8")
    links = parse_index_school_links(html, "https://onlinesys.necta.go.tz/results/2022/csee/index.htm")
    codes = {link.center_number for link in links}
    assert "P0101" in codes
    assert "S1027" in codes
    assert any(link.result_href.lower().startswith("results/") for link in links)


def test_parse_school_page_official_fixture_snippet() -> None:
    html = (FIXTURES / "necta_school_snippet.html").read_text(encoding="utf-8")
    url = "https://onlinesys.necta.go.tz/results/2022/csee/results/s1027.htm"
    result = parse_school_page(html, url, 2022, "S1027/0034")
    assert result.candidate_number == "S1027/0034"
    assert result.center_number == "S1027"
    assert "CHAMWINO" in result.school_name.upper()
    assert result.division == "II"
    assert result.aggregate == 21
    assert result.sex == "F"
    codes = [s.code for s in result.subjects]
    assert "B/MATH" in codes
    assert any(s.name == "Mathematics" for s in result.subjects)


def test_parse_subject_blob_maps_known_codes() -> None:
    blob = "CIV - 'C'   ENGL - 'B'   B/MATH - 'D' "
    subjects = parse_subject_blob(blob)
    by_code = {s.code: s for s in subjects}
    assert by_code["CIV"].name == "Civics"
    assert by_code["ENGL"].name == "English Language"
    assert by_code["B/MATH"].name == "Mathematics"


def test_parse_subject_blob_tetea_hyphen_format() -> None:
    blob = "CIV-C HIST-D GEO-D B/MATH-C"
    subjects = parse_subject_blob_tetea(blob)
    by_code = {s.code: s for s in subjects}
    assert by_code["CIV"].grade == "C"
    assert by_code["HIST"].grade == "D"
    assert by_code["B/MATH"].name == "Mathematics"


def test_csee_source_router_urls() -> None:
    assert resolve_csee_data_source(2023) is CseeUpstream.NECTA_ONLINESYS
    assert resolve_csee_data_source(2022) is CseeUpstream.TETEA_MAKTABA
    assert "onlinesys.necta.go.tz" in csee_year_index_probe_url(2024)
    assert "maktaba.tetea.org" in csee_year_index_probe_url(2008).lower()
    tetea_centre = csee_centre_page_url(2008, "S1027")
    assert "maktaba.tetea.org" in tetea_centre.lower() and "/s1027.htm" in tetea_centre.lower()
    assert "results/2024/csee/results/s1027.htm" in csee_centre_page_url(2024, "S1027").lower()


def test_parse_tetea_csee_school_page_fixture() -> None:
    html = (FIXTURES / "tetea_school_snippet.html").read_text(encoding="utf-8")
    url = "https://maktaba.tetea.org/exam-results/CSEE2008/s1027.htm"
    result = parse_tetea_csee_school_page(html, url, 2008, "S1027/0034")
    assert result.data_source == "tetea_maktaba"
    assert result.candidate_number == "S1027/0034"
    assert result.division == "II"
    codes = {s.code for s in result.subjects}
    assert "CIV" in codes and "B/MATH" in codes


def test_necta_result_to_student_payload_shape() -> None:
    html = (FIXTURES / "necta_school_snippet.html").read_text(encoding="utf-8")
    url = "https://onlinesys.necta.go.tz/results/2022/csee/results/s1027.htm"
    result = parse_school_page(html, url, 2022, "S1027/0034")
    payload = necta_result_to_student_payload(result)
    assert payload["pathway"] == "o_level"
    assert payload["a_level_subjects"] == []
    assert len(payload["o_level_subjects"]) == len(result.subjects)
    assert any("Division:" in note for note in payload["notes"])
