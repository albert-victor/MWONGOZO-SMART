from __future__ import annotations

from collections.abc import Iterable

SUBJECT_ALIASES = {
    # Common shorthand and spelling variants that should map to one standard subject name.
    "MATH": "Advanced Mathematics",
    "MATHEMATICS": "Basic Mathematics",
    "ADVANCED MATHEMATICS": "Advanced Mathematics",
    "BAM": "Basic Applied Mathematics",
    "BASIC APPLIED MATHEMATICS": "Basic Applied Mathematics",
    "BASIC MATHEMATICS": "Basic Mathematics",
    "BIO": "Biology",
    "CHEM": "Chemistry",
    "PHY": "Physics",
    "ENG": "English Language",
    "ENGLISH": "English Language",
    "KISWAHILI": "Kiswahili",
    "HISTORY": "History",
    "GEOGRAPHY": "Geography",
    "ECONOMICS": "Economics",
    "ACCOUNTANCY": "Accountancy",
    "COMMERCE": "Commerce",
    "BOOK KEEPING": "Book Keeping",
    "BOOKKEEPING": "Book Keeping",
    "COMPUTER SCIENCE": "Computer Science",
    "COMPUTER STUDIES": "Computer Science",
    "INFORMATION AND COMPUTER STUDIES": "Computer Science",
    "NUTRITION": "Nutrition",
    "FINE ARTS": "Fine Arts",
    "ARABIC": "Arabic",
    "FRENCH": "French",
    "DIVINITY": "Divinity",
}

# Arts / humanities & business combinations — must not route into health or STEM programmes.
ARTS_HUMANITIES_COMBINATIONS: frozenset[str] = frozenset({"HGE", "HGL", "HKL", "HGK"})
NON_SCIENCE_COMBINATIONS: frozenset[str] = frozenset({"HGE", "HGL", "HKL", "HGK", "ECA", "CBE"})
SCIENCE_COMBINATIONS: frozenset[str] = frozenset({"PCB", "PCM", "PGM", "CBG", "CBN"})

COMBINATION_MAP = {
    # Common A-Level combinations used in the UI and matching logic.
    "PCB": ["Physics", "Chemistry", "Biology"],
    "PCM": ["Physics", "Chemistry", "Advanced Mathematics"],
    "PGM": ["Physics", "Geography", "Advanced Mathematics"],
    "CBG": ["Chemistry", "Biology", "Geography"],
    "CBN": ["Chemistry", "Biology", "Nutrition"],
    "HGE": ["History", "Geography", "Economics"],
    "ECA": ["Economics", "Commerce", "Accountancy"],
    "CBE": ["Commerce", "Book Keeping", "Economics"],
    "HKL": ["History", "Kiswahili", "English Language"],
    "HGL": ["History", "Geography", "English Language"],
    "HGK": ["History", "Geography", "Kiswahili"],
    "PCM/PCB": ["Physics", "Chemistry", "Advanced Mathematics"],
}


def normalize_subject_name(subject: str) -> str:
    # Collapse extra spaces, uppercase the key, then map aliases to the standard label.
    cleaned = " ".join(subject.strip().upper().split())
    return SUBJECT_ALIASES.get(cleaned, " ".join(word.capitalize() for word in cleaned.split()))


def normalize_subjects(subjects: Iterable[str]) -> list[str]:
    return [normalize_subject_name(subject) for subject in subjects]


def expand_combination(combination: str | None) -> list[str]:
    # Convert a combination code like PCB into the subject list it represents.
    if not combination:
        return []
    key = "".join(ch for ch in combination.upper() if ch.isalpha() or ch == "/")
    if key in COMBINATION_MAP:
        return COMBINATION_MAP[key][:]
    if len(key) == 3:
        mapped = []
        for letter in key:
            mapped.extend(COMBINATION_MAP.get(letter, []))
        if mapped:
            return mapped
    return []


def normalize_combination_code(combination: str | None) -> str:
    return "".join(ch for ch in (combination or "").upper() if ch.isalpha())


def is_arts_humanities_combination(combination: str | None) -> bool:
    return normalize_combination_code(combination) in ARTS_HUMANITIES_COMBINATIONS


def is_non_science_combination(combination: str | None) -> bool:
    return normalize_combination_code(combination) in NON_SCIENCE_COMBINATIONS


def is_science_combination(combination: str | None) -> bool:
    return normalize_combination_code(combination) in SCIENCE_COMBINATIONS


def resolve_student_combination(
    combination: str | None,
    a_level_subjects: Iterable[object],
) -> str:
    """Resolve A-Level combination from explicit code or principal subjects."""
    explicit = normalize_combination_code(combination)
    if explicit:
        return explicit
    principals: list[str] = []
    for item in a_level_subjects:
        subject = getattr(item, "subject", item)
        is_principal = getattr(item, "principal", True)
        if is_principal:
            principals.append(str(subject))
    if not principals:
        principals = [str(getattr(item, "subject", item)) for item in a_level_subjects]
    inferred = infer_combination(principals)
    return normalize_combination_code(inferred)


def infer_combination(subjects: Iterable[str]) -> str | None:
    # Try to guess the combination from a set of subjects (exact cluster match first).
    normalized = {normalize_subject_name(subject) for subject in subjects}
    best: str | None = None
    best_size = 0
    for code, cluster in COMBINATION_MAP.items():
        cluster_set = {normalize_subject_name(item) for item in cluster}
        if cluster_set.issubset(normalized):
            if len(cluster_set) > best_size:
                best = code
                best_size = len(cluster_set)
    return best


def combination_blocks_stem_programme(combination: str | None, category_value: str) -> bool:
    """True when a non-science combination must not enter health/STEM programme categories."""
    if not is_non_science_combination(combination):
        return False
    return category_value in {"health", "science", "engineering", "computing", "tech"}
