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

COMBINATION_MAP = {
    # Common A-Level combinations used in the UI and matching logic.
    "PCB": ["Physics", "Chemistry", "Biology"],
    "PCM": ["Physics", "Chemistry", "Advanced Mathematics"],
    "PGM": ["Physics", "Geography", "Advanced Mathematics"],
    "CBG": ["Chemistry", "Biology", "Geography"],
    "CBN": ["Commerce", "Book Keeping", "Nutrition"],
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


def infer_combination(subjects: Iterable[str]) -> str | None:
    # Try to guess the combination from a set of subjects.
    normalized = {normalize_subject_name(subject) for subject in subjects}
    for code, cluster in COMBINATION_MAP.items():
        if set(cluster).issubset(normalized):
            return code
    return None
