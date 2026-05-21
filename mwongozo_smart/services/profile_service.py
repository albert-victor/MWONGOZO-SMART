from __future__ import annotations

import re
from typing import Any

from mwongozo_smart.core.models import StudentResult
from mwongozo_smart.services import auth_store

_CNO_RE = re.compile(r"(?:NECTA\s+CNO|CNO)\s*:\s*([A-Z0-9/\-]+)", re.I)
_YEAR_RE = re.compile(r"(?:exam\s*year|mwaka)\s*:\s*(\d{4})", re.I)


def extract_exam_fields(
    *,
    exam_number: str | None,
    exam_year: int | None,
    notes: list[str],
) -> tuple[str | None, int | None]:
    number = exam_number.strip().upper() if exam_number else None
    year = exam_year
    for note in notes:
        if not number:
            match = _CNO_RE.search(note)
            if match:
                number = match.group(1).strip().upper()
        if not year:
            match = _YEAR_RE.search(note)
            if match:
                year = int(match.group(1))
    return number, year


def capture_after_recommend(
    *,
    session_id: str,
    user_id: int | None,
    student: StudentResult,
    source: str,
    exam_number: str | None = None,
    exam_year: int | None = None,
) -> dict[str, Any] | None:
    try:
        number, year = extract_exam_fields(
            exam_number=exam_number,
            exam_year=exam_year,
            notes=list(student.notes),
        )
        profile_id = auth_store.upsert_student_profile(
            session_id=session_id,
            user_id=user_id,
            combination=student.combination,
            exam_number=number,
            exam_year=year,
            source=source or "recommend_form",
            pathway=student.pathway.value,
            input_snapshot=student.model_dump(mode="json"),
        )
        return {"profile_id": profile_id, "session_id": session_id, "exam_number": number, "exam_year": year}
    except Exception:
        return None
