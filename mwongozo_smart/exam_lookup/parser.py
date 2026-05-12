from __future__ import annotations

import logging
import re
from collections.abc import Callable
from pathlib import PurePosixPath
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

from mwongozo_smart.exam_lookup.models import NectaAcseeResult, NectaCseeResult, NectaSchoolLink, NectaSubjectGrade
from mwongozo_smart.utils.combination_helper import infer_combination, normalize_subject_name

logger = logging.getLogger(__name__)

NECTA_SUBJECT_CODE_MAP: dict[str, str] = {
    "CIV": "Civics",
    "HIST": "History",
    "GEO": "Geography",
    "KISW": "Kiswahili",
    "ENGL": "English Language",
    "PHY": "Physics",
    "CHEM": "Chemistry",
    "BIO": "Biology",
    "B/MATH": "Mathematics",
    "MATH": "Mathematics",
    "ADD/MATH": "Basic Mathematics",
    "COMP": "Computer Studies",
    "COMP STUD": "Computer Studies",
    "CST": "Computer Studies",
    "ICS": "Information and Computer Studies",
    "COMM": "Commerce",
    "B/KEEP": "Book Keeping",
    "ECO": "Economics",
    "AGR": "Agriculture",
    "ARAB": "Arabic",
    "FRE": "French",
    "I/K": "Islamic Knowledge",
    "B/K": "Bible Knowledge",
    "PED": "Physical Education",
    "P.E": "Physical Education",
    "MUSIC": "Music",
    "THA": "Theatre Arts",
    "D&T": "Design and Technology",
    "CA": "Computer Applications",
    "FOOD & NUTR": "Food and Nutrition",
    "FOOD": "Food and Nutrition",
    "HOME": "Home Economics",
    "LIT IN ENGL": "English Language",
    "LIT ENG": "English Language",
    "F/ART": "Fine Arts",
    "BIBLE": "Bible Knowledge",
    "ISLAM": "Islamic Knowledge",
}

NECTA_ACSEE_SUBJECT_CODE_MAP: dict[str, str] = {
    "G/STUDIES": "General Studies",
    "GENERAL": "General Studies",
    "GEOGR": "Geography",
    "GEOGRAP": "Geography",
    "GEOGRAPHY": "Geography",
    "ENGLISH": "English Language",
    "ADV/MATHS": "Advanced Mathematics",
    "ADV MATHS": "Advanced Mathematics",
    "PHYSICS": "Physics",
    "CHEMISTRY": "Chemistry",
    "BIOLOGY": "Biology",
    "BAM": "Basic Applied Mathematics",
    "HISTORY": "History",
    "KISWAHILI": "Kiswahili",
    "KISW": "Kiswahili",
    "ECON": "Economics",
    "COMMERCE": "Commerce",
    "ACCOUNT": "Accountancy",
    "ACCOUNTANCY": "Accountancy",
    "NUTRITION": "Nutrition",
    "COMPUTER": "Computer Science",
    "COMPUTER SCIENCE": "Computer Science",
    "COMP STUD": "Computer Science",
    "DIVINITY": "Divinity",
    "FINE ART": "Fine Arts",
    "FINE ARTS": "Fine Arts",
    "ARABIC": "Arabic",
    "FRENCH": "French",
    "LITERATURE": "English Language",
}


def normalize_href(href: str) -> str:
    return href.strip().replace("\\", "/")


def parse_candidate_number(raw: str) -> tuple[str, str, str]:
    cleaned = " ".join(raw.strip().upper().split())
    cleaned = cleaned.replace("-", "/")
    match = re.match(r"^([A-Z]\d+)/(\d+)$", cleaned)
    if not match:
        raise ValueError("Candidate number must look like S0140-0012 or S0140/0012 (centre + serial).")
    centre, serial = match.group(1), match.group(2)
    serial_norm = serial.zfill(4) if len(serial) <= 4 else serial
    candidate_norm = f"{centre}/{serial_norm}"
    return centre, candidate_norm, serial_norm


def school_result_url(base_url: str, exam_year: int, centre_number: str) -> str:
    slug = centre_number.lower()
    return f"{base_url.rstrip('/')}/results/{exam_year}/csee/results/{slug}.htm"


def acsee_index_url(base_url: str, exam_year: int) -> str:
    return f"{base_url.rstrip('/')}/results/{exam_year}/acsee/index.htm"


def acsee_index_letter_url(base_url: str, exam_year: int, letter: str) -> str:
    ch = letter.lower()[0]
    return f"{base_url.rstrip('/')}/results/{exam_year}/acsee/index_{ch}.htm"


def acsee_school_result_url(base_url: str, exam_year: int, centre_number: str) -> str:
    slug = centre_number.lower()
    return f"{base_url.rstrip('/')}/results/{exam_year}/acsee/results/{slug}.htm"


def parse_index_school_links(html: str, page_url: str) -> list[NectaSchoolLink]:
    soup = BeautifulSoup(html, "html.parser")
    links: list[NectaSchoolLink] = []
    seen: set[str] = set()
    for anchor in soup.find_all("a", href=True):
        href = normalize_href(anchor["href"])
        if "results/" not in href.lower() or not href.lower().endswith(".htm"):
            continue
        absolute = urljoin(page_url, href)
        parsed = urlparse(absolute)
        name = " ".join(anchor.get_text(" ", strip=True).split())
        if not name:
            continue
        token = PurePosixPath(parsed.path).name.removesuffix(".htm").removesuffix(".HTM")
        if not re.fullmatch(r"[a-z]\d+", token, flags=re.IGNORECASE):
            continue
        center_number = token.upper()
        if center_number in seen:
            continue
        seen.add(center_number)
        rel = href if href.lower().startswith("results/") else f"results/{token.lower()}.htm"
        links.append(NectaSchoolLink(center_number=center_number, school_name=name, result_href=rel))
    links.sort(key=lambda item: item.center_number)
    return links


def parse_acsee_index_school_links(html: str, page_url: str, exam_year: int) -> list[NectaSchoolLink]:
    """Parse official ACSEE index HTML; only links under .../acsee/results/ are kept."""
    soup = BeautifulSoup(html, "html.parser")
    links: list[NectaSchoolLink] = []
    seen: set[str] = set()
    needle = f"/results/{exam_year}/acsee/results/"
    for anchor in soup.find_all("a", href=True):
        href = normalize_href(anchor["href"])
        if not href.lower().endswith(".htm"):
            continue
        absolute = urljoin(page_url, href)
        if needle.lower() not in absolute.lower():
            continue
        parsed = urlparse(absolute)
        name = " ".join(anchor.get_text(" ", strip=True).split())
        if not name:
            continue
        token = PurePosixPath(parsed.path).name.removesuffix(".htm").removesuffix(".HTM")
        if not re.fullmatch(r"[a-z]\d+", token, flags=re.IGNORECASE):
            continue
        center_number = token.upper()
        if center_number in seen:
            continue
        seen.add(center_number)
        rel_path = f"results/{exam_year}/acsee/results/{token.lower()}.htm"
        links.append(NectaSchoolLink(center_number=center_number, school_name=name, result_href=rel_path))
    links.sort(key=lambda item: item.center_number)
    return links


def _map_subject_code(code: str) -> str:
    key = " ".join(code.strip().upper().split())
    mapped = NECTA_SUBJECT_CODE_MAP.get(key) or NECTA_ACSEE_SUBJECT_CODE_MAP.get(key)
    if mapped:
        return mapped
    cleaned = code.replace("/", " ").strip()
    return normalize_subject_name(cleaned)


def parse_subject_blob(blob: str) -> list[NectaSubjectGrade]:
    subjects: list[NectaSubjectGrade] = []
    for match in re.finditer(r"([A-Z][A-Z0-9 /&']+?)\s*-\s*'([^']+)'", blob):
        code_raw, grade = match.group(1).strip(), match.group(2).strip().upper()
        name = _map_subject_code(code_raw)
        subjects.append(NectaSubjectGrade(code=code_raw.upper(), name=name, grade=grade))
    return subjects


def parse_subject_blob_tetea(blob: str) -> list[NectaSubjectGrade]:
    """TETEA archive lines use tokens like CIV-C or B/MATH-D (hyphen grade, no quotes)."""
    subjects: list[NectaSubjectGrade] = []
    for part in re.split(r"\s+", blob.strip()):
        if not part or part in {"-", "–"}:
            continue
        match = re.match(r"^(.+)-([A-Z0-9I]{1,3})$", part, flags=re.IGNORECASE)
        if not match:
            continue
        code_raw, grade = match.group(1).strip(), match.group(2).strip().upper()
        name = _map_subject_code(code_raw)
        subjects.append(NectaSubjectGrade(code=code_raw.upper(), name=name, grade=grade))
    return subjects


def _extract_region_from_csee_html(html: str) -> str:
    match = re.search(r"Region\s*:\s*([A-Za-z][A-Za-z\s'.-]*)", html, flags=re.IGNORECASE)
    if not match:
        return ""
    return " ".join(match.group(1).split()).strip()


def _parse_centre_gpa(html: str) -> float | None:
    soup = BeautifulSoup(html, "html.parser")
    for td in soup.find_all("td"):
        label = td.get_text(" ", strip=True).upper()
        if "EXAMINATION CENTRE GPA" not in label:
            continue
        sibling = td.find_next_sibling("td")
        if not sibling:
            continue
        raw = sibling.get_text(" ", strip=True)
        match = re.search(r"([\d.]+)", raw)
        if not match:
            return None
        try:
            return float(match.group(1))
        except ValueError:
            return None
    return None


def parse_school_page(
    html: str,
    page_url: str,
    exam_year: int,
    candidate_norm: str,
    *,
    parse_subjects: Callable[[str], list[NectaSubjectGrade]] | None = None,
) -> NectaCseeResult:
    soup = BeautifulSoup(html, "html.parser")
    region = _extract_region_from_csee_html(html)
    header = ""
    for heading in soup.find_all(["h1", "h2", "h3"]):
        text = heading.get_text(" ", strip=True)
        if "CSEE" in text.upper() and "EXAMINATION" in text.upper():
            continue
        if re.search(r"\b[A-Z]\d{3,}\b", text):
            header = text
            break
    center_number, school_name = "", ""
    header_match = re.match(r"^([A-Z]\d+)\s+(.+)$", header.strip())
    if header_match:
        center_number = header_match.group(1).upper()
        school_name = " ".join(header_match.group(2).split())

    target = candidate_norm.upper()
    target_serial = target.split("/")[-1].lstrip("0") or "0"
    target_serial_padded = target.split("/")[-1]
    row_cno, row_sex, row_agg, row_div, row_subjects, row_student_name = None, None, None, None, None, ""
    for table in soup.find_all("table"):
        rows = table.find_all("tr")
        if not rows:
            continue
        header_cells = [cell.get_text(" ", strip=True).upper() for cell in rows[0].find_all(["td", "th"])]
        joined = " ".join(header_cells)
        if "CNO" in joined and "DIV" in joined and "DETAILED" in joined:
            has_name_column = "NAME" in joined
            for tr in rows[1:]:
                cells = tr.find_all("td")
                need = 6 if has_name_column else 5
                if len(cells) < need:
                    continue
                raw_cno = cells[0].get_text(" ", strip=True).upper().replace("-", "/")
                cno_serial = raw_cno.split("/")[-1].lstrip("0") or "0"
                if raw_cno != target and raw_cno != target_serial_padded and cno_serial != target_serial:
                    continue
                row_cno = target  # always store canonical full form (e.g. S0140/0001)
                row_sex = cells[1].get_text(" ", strip=True) or None
                if has_name_column:
                    row_student_name = " ".join(cells[2].get_text(" ", strip=True).split())
                    agg_text = cells[3].get_text(" ", strip=True)
                    try:
                        row_agg = int(agg_text) if agg_text.strip() and agg_text.strip() not in {"-", "–"} else None
                    except ValueError:
                        row_agg = None
                    row_div = cells[4].get_text(" ", strip=True).upper()
                    row_subjects = cells[5].get_text(" ", strip=True)
                else:
                    agg_text = cells[2].get_text(" ", strip=True)
                    try:
                        row_agg = int(agg_text) if agg_text.strip() and agg_text.strip() not in {"-", "–"} else None
                    except ValueError:
                        row_agg = None
                    row_div = cells[3].get_text(" ", strip=True).upper()
                    row_subjects = cells[4].get_text(" ", strip=True)
                break
            if row_cno:
                break

    if not row_cno:
        raise ValueError(f"Candidate {candidate_norm} was not found on the centre results page.")

    subject_fn = parse_subjects or parse_subject_blob
    subjects = subject_fn(row_subjects or "")
    # Some TETEA archive years (e.g. CSEE 2019-2022) use NECTA-style quoted grades
    # instead of the older hyphen format, and vice versa. Fall back to the other parser.
    if not subjects and row_subjects:
        fallback = parse_subject_blob if subject_fn is parse_subject_blob_tetea else parse_subject_blob_tetea
        subjects = fallback(row_subjects)
    return NectaCseeResult(
        exam_year=exam_year,
        candidate_number=row_cno,
        student_name=row_student_name,
        school_name=school_name,
        center_number=center_number or row_cno.split("/")[0],
        region=region,
        division=row_div or "",
        sex=row_sex,
        aggregate=row_agg,
        subjects=subjects,
        source_url=page_url,
    )


def parse_acsee_school_page(html: str, page_url: str, exam_year: int, candidate_norm: str) -> NectaAcseeResult:
    soup = BeautifulSoup(html, "html.parser")
    region = _extract_region_from_csee_html(html)
    header = ""
    for heading in soup.find_all(["h1", "h2", "h3"]):
        text = heading.get_text(" ", strip=True)
        if "ACSEE" in text.upper() and "EXAMINATION" in text.upper():
            continue
        if re.search(r"\b[A-Z]\d{3,}\b", text):
            header = text
            break
    center_number, school_name = "", ""
    header_match = re.match(r"^([A-Z]\d+)\s+(.+)$", header.strip())
    if header_match:
        center_number = header_match.group(1).upper()
        school_name = " ".join(header_match.group(2).split())

    target = candidate_norm.upper()
    target_serial = target.split("/")[-1].lstrip("0") or "0"
    target_serial_padded = target.split("/")[-1]
    row_cno: str | None = None
    row_student_name: str = ""
    row_sex: str | None = None
    row_agg: int | None = None
    row_div: str = ""
    row_subjects: str = ""
    row_gpa: float | None = None

    def _cno_matches(raw: str) -> bool:
        raw = raw.upper().replace("-", "/").strip()
        serial = raw.split("/")[-1].lstrip("0") or "0"
        return raw == target or raw == target_serial_padded or serial == target_serial

    def try_necta_agg_layout() -> bool:
        nonlocal row_cno, row_sex, row_agg, row_div, row_subjects, row_gpa, row_student_name
        for table in soup.find_all("table"):
            rows = table.find_all("tr")
            if not rows:
                continue
            header_cells = [cell.get_text(" ", strip=True).upper() for cell in rows[0].find_all(["td", "th"])]
            joined = " ".join(header_cells)
            if "CNO" in joined and "AGGT" in joined and "DIV" in joined and "DETAILED" in joined:
                has_name_column = "NAME" in joined
                for tr in rows[1:]:
                    cells = tr.find_all("td")
                    need = 6 if has_name_column else 5
                    if len(cells) < need:
                        continue
                    if not _cno_matches(cells[0].get_text(" ", strip=True)):
                        continue
                    row_cno = target
                    row_sex = cells[1].get_text(" ", strip=True) or None
                    if has_name_column:
                        row_student_name = " ".join(cells[2].get_text(" ", strip=True).split())
                        agg_text = cells[3].get_text(" ", strip=True)
                        row_div = cells[4].get_text(" ", strip=True).upper()
                        row_subjects = cells[5].get_text(" ", strip=True)
                    else:
                        agg_text = cells[2].get_text(" ", strip=True)
                        row_div = cells[3].get_text(" ", strip=True).upper()
                        row_subjects = cells[4].get_text(" ", strip=True)
                    try:
                        row_agg = int(agg_text) if agg_text.strip() and agg_text.strip() not in {"-", "–"} else None
                    except ValueError:
                        row_agg = None
                    row_gpa = None
                    return True
        return False

    def try_tetea_gpa_layout() -> bool:
        nonlocal row_cno, row_sex, row_agg, row_div, row_subjects, row_gpa, row_student_name
        for table in soup.find_all("table"):
            rows = table.find_all("tr")
            if not rows:
                continue
            header_cells = [cell.get_text(" ", strip=True).upper() for cell in rows[0].find_all(["td", "th"])]
            joined = " ".join(header_cells)
            if "CNO" in joined and "GPA" in joined and "CLASS" in joined and "DETAILED" in joined:
                has_name_column = "NAME" in joined
                for tr in rows[1:]:
                    cells = tr.find_all("td")
                    need = 6 if has_name_column else 5
                    if len(cells) < need:
                        continue
                    if not _cno_matches(cells[0].get_text(" ", strip=True)):
                        continue
                    row_cno = target
                    row_sex = cells[1].get_text(" ", strip=True) or None
                    if has_name_column:
                        row_student_name = " ".join(cells[2].get_text(" ", strip=True).split())
                        gtext = cells[3].get_text(" ", strip=True)
                        row_div = cells[4].get_text(" ", strip=True).upper()
                        row_subjects = cells[5].get_text(" ", strip=True)
                    else:
                        gtext = cells[2].get_text(" ", strip=True)
                        row_div = cells[3].get_text(" ", strip=True).upper()
                        row_subjects = cells[4].get_text(" ", strip=True)
                    try:
                        row_gpa = float(gtext) if gtext.strip() and gtext.strip() not in {"-", "–"} else None
                    except ValueError:
                        row_gpa = None
                    row_agg = None
                    return True
        return False

    if not try_necta_agg_layout():
        row_cno = None
        if not try_tetea_gpa_layout():
            raise ValueError(f"Candidate {candidate_norm} was not found on the ACSEE centre results page.")

    subjects = parse_subject_blob(row_subjects or "")
    if not subjects and row_subjects:
        subjects = parse_subject_blob_tetea(row_subjects)
    principalish = [s.name for s in subjects if normalize_subject_name(s.name).lower() != "general studies"]
    inferred = infer_combination(principalish)
    centre_gpa = _parse_centre_gpa(html)

    return NectaAcseeResult(
        exam_year=exam_year,
        candidate_number=row_cno,
        student_name=row_student_name,
        school_name=school_name,
        center_number=center_number or row_cno.split("/")[0],
        region=region,
        inferred_combination=inferred,
        subjects=subjects,
        division=row_div or "",
        aggregate_points=row_agg,
        gpa=row_gpa,
        sex=row_sex,
        centre_gpa=centre_gpa,
        source_url=page_url,
    )
