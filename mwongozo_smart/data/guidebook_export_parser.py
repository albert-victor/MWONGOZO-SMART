from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from pathlib import Path

from mwongozo_smart.core.models import AdmissionRequirement, ConditionalRequirement, Programme, ProgrammeAwardLevel, ProgrammeCategory
from mwongozo_smart.utils.combination_helper import normalize_subject_name


_HEADING_RE = re.compile(r"^(?P<name>.+?) \((?P<code>[A-Z0-9]{2,10})\), (?P<city>.+)$")
_CODE_RE = re.compile(r"^(?P<code>[A-Z]{2,5}\d{2,3})\s+(?P<rest>.+)$")

_HEADER_MARKERS = {
    "sn",
    "programme",
    "code",
    "admission requirements",
    "minimum institutional admission points",
    "capacity",
    "duration (yrs)",
    "duration",
}

_REQUIREMENT_HINTS = (
    "principal",
    "pass",
    "grade",
    "minimum",
    "candidate",
    "applicant",
    "credit",
    "subsidiary",
    "o-level",
    "a-level",
    "subject",
    "subjects",
    "must",
    "without",
    "with a minimum",
    "unless",
    "following subjects",
    "one of which",
    "two principal",
    "three principal",
)

_NAME_START_HINTS = (
    "bachelor",
    "doctor of",
    "master of",
    "diploma in",
    "ordinary diploma in",
    "certificate in",
    "technician certificate in",
    "bsc",
    "bachelor degree",
)


@dataclass(slots=True)
class ParsedProgrammeDraft:
    code: str
    name: str
    institution_code: str
    institution_name: str
    city: str
    region: str
    requirement_text: str
    category: ProgrammeCategory
    duration_years: int | None
    competition_tier: int
    tags: list[str]
    requirement: AdmissionRequirement


def default_guidebook_json_paths() -> list[Path]:
    candidates: list[Path] = []
    env_path = os.getenv("MWONGOZO_GUIDEBOOK_JSON")
    if env_path:
        candidates.append(Path(env_path))
    candidates.extend(
        [
            Path.cwd() / "data" / "guidebook_2025_2026.json",
            Path.cwd() / "guidebook_2025_2026.json",
            Path.home() / "Downloads" / "Admission Guidebook for Holders of Secondary School Qualifications_2025_2026.json",
        ]
    )
    return candidates


def find_guidebook_json_path() -> Path | None:
    for candidate in default_guidebook_json_paths():
        if candidate.exists():
            return candidate
    return None


def load_guidebook_lines(path: str | Path) -> list[str]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    lines = data.get("lines", [])
    return [str(line).strip() for line in lines]


def load_parsed_programmes(path: str | Path | None = None) -> list[Programme]:
    export_path = Path(path) if path is not None else find_guidebook_json_path()
    if export_path is None or not export_path.exists():
        return []
    lines = load_guidebook_lines(export_path)
    drafts = parse_guidebook_lines(lines)
    return [draft.to_programme() for draft in drafts]


def parse_guidebook_lines(lines: list[str]) -> list[ParsedProgrammeDraft]:
    drafts: list[ParsedProgrammeDraft] = []
    current_heading: tuple[str, str, str, str] | None = None
    current_name_lines: list[str] = []
    current_code: str | None = None
    current_req_lines: list[str] = []
    pending_name_lines: list[str] = []

    def flush_current() -> None:
        nonlocal current_name_lines, current_code, current_req_lines, pending_name_lines
        if current_heading and current_code and current_name_lines:
            draft = _build_draft(current_heading, current_code, current_name_lines, current_req_lines)
            if draft is not None:
                drafts.append(draft)
        current_name_lines = []
        current_code = None
        current_req_lines = []
        pending_name_lines = []

    for raw_line in lines:
        line = raw_line.strip()
        if not line:
            continue

        heading_match = _HEADING_RE.match(line)
        if heading_match:
            flush_current()
            current_heading = (
                heading_match.group("name").strip(),
                heading_match.group("code").strip(),
                heading_match.group("city").strip(),
                heading_match.group("city").strip(),
            )
            current_name_lines = []
            current_code = None
            current_req_lines = []
            pending_name_lines = []
            continue

        if current_heading is None:
            continue

        lower = line.lower()
        if _is_footer_or_header(line):
            continue

        code_match = _CODE_RE.match(line)
        if code_match:
            if current_code is None:
                current_code = code_match.group("code").strip()
                current_req_lines = [_clean_req_fragment(code_match.group("rest"))]
            else:
                if current_name_lines:
                    draft = _build_draft(current_heading, current_code, current_name_lines, current_req_lines)
                    if draft is not None:
                        drafts.append(draft)
                current_name_lines = pending_name_lines[:] if pending_name_lines else []
                current_code = code_match.group("code").strip()
                current_req_lines = [_clean_req_fragment(code_match.group("rest"))]
                pending_name_lines = []
            continue

        if current_code is None:
            if not current_name_lines and _looks_like_name_start(line):
                current_name_lines.append(line)
            elif current_name_lines and _looks_like_name_continuation(line):
                current_name_lines.append(line)
            continue

        if not pending_name_lines and _looks_like_name_start(line):
            pending_name_lines = [line]
            continue

        if pending_name_lines and _looks_like_name_continuation(line):
            pending_name_lines.append(line)
            continue

        if _looks_like_requirement_line(line):
            current_req_lines.append(line)
            continue

    if current_heading and current_code and current_name_lines:
        draft = _build_draft(current_heading, current_code, current_name_lines, current_req_lines)
        if draft is not None:
            drafts.append(draft)

    return drafts


def _is_footer_or_header(line: str) -> bool:
    lower = " ".join(line.lower().split())
    if lower.isdigit():
        return True
    if lower in _HEADER_MARKERS:
        return True
    if lower.startswith("bachelor’s degree admission guidebook"):
        return True
    if lower.startswith("for holders of secondary school qualifications"):
        return True
    if lower.startswith("minimum institutional admission points"):
        return True
    return False


def _looks_like_name_start(line: str) -> bool:
    lower = line.lower()
    if any(token in lower for token in _REQUIREMENT_HINTS):
        return False
    return any(lower.startswith(prefix) for prefix in _NAME_START_HINTS)


def _looks_like_name_continuation(line: str) -> bool:
    lower = line.lower()
    if any(token in lower for token in _REQUIREMENT_HINTS):
        return False
    if lower.startswith(("in ", "and ", "of ", "for ", "with ")):
        return True
    if len(line.split()) <= 4 and not any(ch.isdigit() for ch in line) and "," not in line:
        return True
    return False


def _looks_like_requirement_line(line: str) -> bool:
    lower = line.lower()
    return any(token in lower for token in _REQUIREMENT_HINTS)


def _clean_req_fragment(text: str) -> str:
    return " ".join(text.strip().split())


def _normalize_subjects(raw: str) -> list[str]:
    text = raw.replace(";", ",")
    text = text.replace("/", ",")
    parts = re.split(r",|\bor\b|\band\b", text, flags=re.IGNORECASE)
    subjects = []
    for part in parts:
        cleaned = " ".join(part.strip().split())
        cleaned = cleaned.strip(" .")
        if not cleaned:
            continue
        if cleaned.lower() in {"subjects", "subject", "the following subjects", "following subjects"}:
            continue
        cleaned = cleaned.replace("A-Level", "").replace("O-Level", "").strip()
        cleaned = cleaned.strip('"“”')
        if cleaned:
            subjects.append(normalize_subject_name(cleaned))
    return subjects


def _category_for(name: str, requirement_text: str) -> ProgrammeCategory:
    text = f"{name} {requirement_text}".lower()
    if any(keyword in text for keyword in ("medicine", "nursing", "dental", "dentistry", "pharmacy", "optometry", "physiotherapy", "radiography", "health", "biomedical")):
        return ProgrammeCategory.HEALTH
    if any(keyword in text for keyword in ("architecture", "engineering", "civil", "electrical", "chemical", "mechanical", "computer engineering", "survey", "landscape", "interior design")):
        return ProgrammeCategory.ENGINEERING
    if any(keyword in text for keyword in ("education", "teacher", "special needs")):
        return ProgrammeCategory.EDUCATION
    if any(keyword in text for keyword in ("business", "management", "account", "commerce", "econom", "finance", "banking")):
        return ProgrammeCategory.BUSINESS
    if any(keyword in text for keyword in ("accountancy", "accounting and finance", "banking and finance", "taxation", "financial")):
        return ProgrammeCategory.ACCOUNTING_FINANCE
    if any(keyword in text for keyword in ("law", "legal", "llb", "juris")):
        return ProgrammeCategory.LAW
    if any(keyword in text for keyword in ("agriculture", "agro", "crop", "farming", "animal science", "food science", "aquaculture", "forestry")):
        return ProgrammeCategory.AGRICULTURE
    if any(keyword in text for keyword in ("computer science", "information technology", "statistics", "informatics", "data science")):
        return ProgrammeCategory.COMPUTING
    if any(keyword in text for keyword in ("physics", "chemistry", "biology", "agriculture", "nutrition", "science")):
        return ProgrammeCategory.SCIENCE
    if any(keyword in text for keyword in ("history", "geography", "language", "political", "heritage", "literature", "counselling", "psychology", "arts")):
        return ProgrammeCategory.ARTS
    return ProgrammeCategory.OTHER


def _duration_for(category: ProgrammeCategory, name: str) -> int | None:
    text = name.lower()
    if category == ProgrammeCategory.HEALTH:
        return 4 if "nursing" in text else 5
    if category == ProgrammeCategory.ENGINEERING:
        return 4 if "architecture" not in text and "design" not in text else 5
    if category == ProgrammeCategory.EDUCATION:
        return 3
    if category in {ProgrammeCategory.BUSINESS, ProgrammeCategory.ACCOUNTING_FINANCE, ProgrammeCategory.LAW, ProgrammeCategory.ARTS, ProgrammeCategory.SCIENCE, ProgrammeCategory.TECH, ProgrammeCategory.COMPUTING, ProgrammeCategory.AGRICULTURE}:
        return 3 if "engineering" not in text else 4
    return None


def _competition_tier(category: ProgrammeCategory, name: str) -> int:
    text = name.lower()
    if category == ProgrammeCategory.HEALTH:
        return 5
    if category == ProgrammeCategory.ENGINEERING:
        return 5 if any(keyword in text for keyword in ("civil", "architecture", "electrical", "mechanical", "chemical")) else 4
    if category in {ProgrammeCategory.TECH, ProgrammeCategory.COMPUTING}:
        return 4
    if category in {ProgrammeCategory.ACCOUNTING_FINANCE, ProgrammeCategory.LAW, ProgrammeCategory.AGRICULTURE}:
        return 3
    if category == ProgrammeCategory.BUSINESS:
        return 3
    if category == ProgrammeCategory.EDUCATION:
        return 2
    if category == ProgrammeCategory.SCIENCE:
        return 3
    return 3


def _award_level_for(name: str) -> ProgrammeAwardLevel:
    lower = name.lower()
    if lower.startswith("certificate in") or lower.startswith("technician certificate in"):
        return ProgrammeAwardLevel.CERTIFICATE
    if lower.startswith("diploma in") or lower.startswith("ordinary diploma in"):
        return ProgrammeAwardLevel.DIPLOMA
    if lower.startswith("doctor of") or lower.startswith("master of"):
        return ProgrammeAwardLevel.POSTGRADUATE
    return ProgrammeAwardLevel.BACHELOR


def _parse_requirement(name: str, requirement_text: str, category: ProgrammeCategory) -> AdmissionRequirement:
    text = " ".join(requirement_text.split())
    lower = text.lower()

    minimum_principal_passes = 2
    minimum_total_points = 4.0
    minimum_o_level_passes = 0
    principal_subject_pool: list[str] = []
    principal_pool_min_count = 0
    minimum_a_level_subject_grades: dict[str, str] = {}
    minimum_o_level_subject_grades: dict[str, str] = {}
    conditional_requirements: list[ConditionalRequirement] = []
    notes: list[str] = []
    strict = False

    m = re.search(r"(?i)three principal passes in ([^.]+?)(?: with a minimum of (\d+(?:\.\d+)?) points)?", text)
    if m:
        minimum_principal_passes = 3
        principal_subject_pool = _normalize_subjects(m.group(1))
        principal_pool_min_count = 3
        if m.group(2):
            minimum_total_points = float(m.group(2))
    else:
        m = re.search(r"(?i)two principal passes one of which must be in ([^.]+?)(?:\.|$)", text)
        if m:
            principal_subject_pool = _normalize_subjects(m.group(1))
            principal_pool_min_count = 1
        else:
            m = re.search(r"(?i)two principal passes, one of which must be history", text)
            if m:
                principal_subject_pool = ["History"]
                principal_pool_min_count = 1
            else:
                m = re.search(r"(?i)two principal passes, one in geography with a minimum of \"?c\"? grade and one from the following subjects: ([^.]+)", text)
                if m:
                    principal_subject_pool = _normalize_subjects(m.group(1))
                    principal_pool_min_count = 2
                    minimum_a_level_subject_grades["Geography"] = "C"
                else:
                    m = re.search(r"(?i)two principal passes in the following subjects: ([^.]+)", text)
                    if m:
                        principal_subject_pool = _normalize_subjects(m.group(1))
                        principal_pool_min_count = 2
                    else:
                        m = re.search(r"(?i)two principal passes in ([^.]+)", text)
                        if m:
                            principal_subject_pool = _normalize_subjects(m.group(1))
                            principal_pool_min_count = 2

    m = re.search(r"(?i)minimum of (\d+(?:\.\d+)?) points", text)
    if m:
        minimum_total_points = float(m.group(1))

    m = re.search(r"(?i)at least (\d+) passes", text)
    if m:
        minimum_o_level_passes = int(m.group(1))

    if "chemistry" in lower and "biology" in lower and "physics" in lower and "minimum of 6 points" in lower:
        minimum_principal_passes = max(minimum_principal_passes, 3)
        principal_subject_pool = ["Chemistry", "Biology", "Physics"]
        principal_pool_min_count = 3
        minimum_total_points = max(minimum_total_points, 6.0)
        minimum_a_level_subject_grades.update({"Chemistry": "C", "Biology": "C", "Physics": "D"})
        strict = True

    if "without advanced mathematics must have a credit pass or above in basic mathematics at o-level" in lower:
        conditional_requirements.append(
            ConditionalRequirement(
                unless_any_principal=["Advanced Mathematics", "Basic Applied Mathematics"],
                require_o_level_subject_grades={"Basic Mathematics": "C"},
                message="Candidates without Advanced Mathematics must have Basic Mathematics at O-Level with a credit pass or above.",
            )
        )

    if "if one of the passes is not in mathematics" in lower:
        conditional_requirements.append(
            ConditionalRequirement(
                unless_any_principal=["Advanced Mathematics", "Basic Mathematics"],
                require_o_level_subject_grades={"Basic Mathematics": "C"},
                message="Mathematics at O-Level is required when Mathematics is not one of the principal passes.",
            )
        )

    if "subsidiary or pass in mathematics at o-level is required" in lower:
        conditional_requirements.append(
            ConditionalRequirement(
                unless_any_principal=["Advanced Mathematics", "Basic Applied Mathematics", "Mathematics"],
                require_o_level_subject_grades={"Basic Mathematics": "C"},
                message="A subsidiary pass in Mathematics or O-Level Mathematics credit is required.",
            )
        )

    if "must be a minimum of 'c' grade" in lower and "kiswahili, english or french" in lower:
        principal_subject_pool = ["Kiswahili", "English Language", "French"]
        principal_pool_min_count = 1
        minimum_a_level_subject_grades.update({"Kiswahili": "C", "English Language": "C", "French": "C"})

    if "one of which must be at “c” grade or above in kiswahili, english or french" in lower:
        principal_subject_pool = ["Kiswahili", "English Language", "French"]
        principal_pool_min_count = 1
        minimum_a_level_subject_grades.update({"Kiswahili": "C", "English Language": "C", "French": "C"})

    if "one in geography with a minimum of \"c\" grade" in lower:
        minimum_a_level_subject_grades["Geography"] = "C"

    if "a minimum of c grade in chemistry and biology and at least d grade in physics" in lower:
        minimum_a_level_subject_grades.update({"Chemistry": "C", "Biology": "C", "Physics": "D"})
        minimum_total_points = max(minimum_total_points, 6.0)
        strict = True

    if category in {ProgrammeCategory.HEALTH, ProgrammeCategory.ENGINEERING}:
        strict = True

    if category == ProgrammeCategory.HEALTH and not principal_subject_pool:
        principal_subject_pool = ["Chemistry", "Biology", "Physics"]
        principal_pool_min_count = 3

    if category == ProgrammeCategory.ENGINEERING and not principal_subject_pool:
        principal_subject_pool = ["Advanced Mathematics", "Basic Applied Mathematics", "Physics", "Chemistry", "Computer Science"]
        principal_pool_min_count = 2

    if category == ProgrammeCategory.COMPUTING and not principal_subject_pool:
        principal_subject_pool = ["Advanced Mathematics", "Computer Science", "Physics", "Economics", "Commerce", "Accountancy"]
        principal_pool_min_count = 2

    if category == ProgrammeCategory.ACCOUNTING_FINANCE and not principal_subject_pool:
        principal_subject_pool = ["Economics", "Commerce", "Accountancy", "Advanced Mathematics", "Computer Science"]
        principal_pool_min_count = 2

    if category == ProgrammeCategory.AGRICULTURE and not principal_subject_pool:
        principal_subject_pool = ["Biology", "Chemistry", "Agriculture", "Physics", "Geography"]
        principal_pool_min_count = 2

    if category == ProgrammeCategory.LAW and not principal_subject_pool:
        principal_subject_pool = ["History", "Geography", "Kiswahili", "English Language", "Economics", "Commerce", "Accountancy"]
        principal_pool_min_count = 2

    notes = [note for note in notes if note]
    return AdmissionRequirement(
        minimum_principal_passes=minimum_principal_passes,
        minimum_total_points=minimum_total_points,
        minimum_o_level_passes=minimum_o_level_passes,
        principal_subject_pool=principal_subject_pool,
        principal_pool_min_count=principal_pool_min_count,
        minimum_a_level_subject_grades=minimum_a_level_subject_grades,
        minimum_o_level_subject_grades=minimum_o_level_subject_grades,
        conditional_requirements=conditional_requirements,
        notes=notes,
        strict=strict,
    )


def _build_draft(
    heading: tuple[str, str, str, str],
    code: str,
    name_lines: list[str],
    req_lines: list[str],
) -> ParsedProgrammeDraft | None:
    institution_name, institution_code, city, region = heading
    name = _normalize_joined_lines(name_lines)
    req_text = _normalize_joined_lines(req_lines)
    if not _is_valid_programme_name(name):
        return None
    category = _category_for(name, req_text)
    requirement = _parse_requirement(name, req_text, category)
    return ParsedProgrammeDraft(
        code=code,
        name=name,
        institution_code=institution_code,
        institution_name=institution_name,
        city=city,
        region=region,
        requirement_text=req_text,
        category=category,
        duration_years=_duration_for(category, name),
        competition_tier=_competition_tier(category, name),
        tags=_infer_tags(name, req_text, category),
        requirement=requirement,
    )


def _is_valid_programme_name(name: str) -> bool:
    lower = name.lower()
    if not name or len(name) < 10:
        return False
    if any(token in lower for token in _REQUIREMENT_HINTS):
        return False
    title_hits = sum(1 for token in ("bachelor", "doctor", "master") if token in lower)
    if title_hits > 1:
        return False
    if lower.count("bachelor") > 1 or lower.count("doctor") > 1 or lower.count("master") > 1:
        return False
    if any(ch.isdigit() for ch in name):
        return False
    if not lower.startswith(("bachelor", "doctor of", "master of", "diploma in", "ordinary diploma in", "certificate in", "technician certificate in", "bsc", "bachelor degree")):
        return False
    if lower.count(",") > 1:
        return False
    if lower.endswith((" in", " and", " of", " for", ",")):
        return False
    words = name.split()
    if len(words) > 18:
        return False
    return True


def _normalize_joined_lines(lines: list[str]) -> str:
    text = " ".join(line.strip() for line in lines if line.strip())
    return " ".join(text.split())


def _infer_tags(name: str, req_text: str, category: ProgrammeCategory) -> list[str]:
    text = f"{name} {req_text}".lower()
    tags: list[str] = [category.value]
    for keyword in (
        "medicine",
        "nursing",
        "dental",
        "dentistry",
        "pharmacy",
        "optometry",
        "physiotherapy",
        "biomedical",
        "civil",
        "electrical",
        "chemical",
        "computer",
        "architecture",
        "design",
        "economics",
        "commerce",
        "accountancy",
        "statistics",
        "it",
        "information technology",
        "history",
        "geography",
        "languages",
        "psychology",
        "counselling",
    ):
        if keyword in text:
            tags.append(keyword.replace(" ", "-"))
    return sorted(set(tags))


def _build_draft_to_programme(self: ParsedProgrammeDraft) -> Programme:
    return Programme(
        code=self.code,
        name=self.name,
        institution_code=self.institution_code,
        institution_name=self.institution_name,
        city=self.city,
        region=self.region,
        category=self.category,
        award_level=_award_level_for(self.name),
        duration_years=self.duration_years,
        competition_tier=self.competition_tier,
        admission_requirement=self.requirement,
        tags=self.tags,
        source_reference="TCU Bachelor's Degree Admission Guidebook 2025/2026 (parsed export)",
    )


ParsedProgrammeDraft.to_programme = _build_draft_to_programme  # type: ignore[attr-defined]
