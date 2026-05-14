from __future__ import annotations

from pathlib import Path

from mwongozo_smart.exam_lookup.parser import (
    parse_acsee_index_school_links,
    parse_acsee_school_page,
)
from mwongozo_smart.exam_lookup.acsee_service import necta_acsee_to_student_result
from mwongozo_smart.utils.combination_helper import normalize_subject_name

FIXTURES = Path(__file__).resolve().parent / "fixtures"


def test_parse_acsee_school_page_official_fixture() -> None:
    html = (FIXTURES / "necta_acsee_s0140_2024.html").read_text(encoding="utf-8", errors="replace")
    url = "https://onlinesys.necta.go.tz/results/2024/acsee/results/s0140.htm"
    result = parse_acsee_school_page(html, url, 2024, "S0140/0538")
    assert result.candidate_number == "S0140/0538"
    assert result.center_number == "S0140"
    assert "MZUMBE" in result.school_name.upper()
    assert result.division == "I"
    assert result.aggregate_points == 4
    assert result.sex == "M"
    assert result.centre_gpa is not None and result.centre_gpa > 1.0
    codes = {s.code for s in result.subjects}
    assert "PHYSICS" in codes
    assert "CHEMISTRY" in codes
    assert "ADV/MATHS" in codes
    assert result.inferred_combination == "PCM"


def test_parse_acsee_index_snippet() -> None:
    html = '<a href="results/2024/acsee/results/s0140.htm">[S0140 MZUMBE SECONDARY SCHOOL]</a>'
    page = "https://onlinesys.necta.go.tz/results/2024/acsee/index.htm"
    links = parse_acsee_index_school_links(html, page, 2024)
    assert len(links) == 1
    assert links[0].center_number == "S0140"
    assert "MZUMBE" in links[0].school_name.upper()
    assert links[0].result_href == "results/2024/acsee/results/s0140.htm"


def test_necta_acsee_to_student_result_maps_pcm() -> None:
    html = (FIXTURES / "necta_acsee_s0140_2024.html").read_text(encoding="utf-8", errors="replace")
    url = "https://onlinesys.necta.go.tz/results/2024/acsee/results/s0140.htm"
    acsee = parse_acsee_school_page(html, url, 2024, "S0140/0538")
    student = necta_acsee_to_student_result(acsee)
    assert student.pathway.value == "a_level"
    names = {normalize_subject_name(s.subject) for s in student.a_level_subjects}
    assert "Physics" in names
    assert "Chemistry" in names
    assert "Advanced Mathematics" in names
