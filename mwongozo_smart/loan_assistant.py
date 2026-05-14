from __future__ import annotations

from dataclasses import dataclass
from difflib import SequenceMatcher
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from mwongozo_smart.data.guidebook_data import PROGRAMMES
from mwongozo_smart.data.institutions import INSTITUTIONS


_FUNDING_PRIORITY_BY_CATEGORY: dict[str, int] = {
    "health": 95,
    "engineering": 92,
    "science": 88,
    "education": 86,
    "computing": 85,
    "tech": 83,
    "agriculture": 80,
    "law": 77,
    "business": 70,
    "accounting_finance": 68,
    "arts": 55,
    "other": 50,
}

_COMMON_MISTAKES: list[dict[str, str]] = [
    {"title": "Names do not match", "detail": "Names in certificates differ from NIDA/NIN spelling."},
    {"title": "Wrong index number", "detail": "NECTA index number format is incorrect or belongs to another student."},
    {"title": "Blurred documents", "detail": "Uploaded files are unreadable due to blur or low light."},
    {"title": "Missing guardian verification", "detail": "Guardian identity or supporting documents are incomplete."},
    {"title": "Late submission", "detail": "Application was submitted after the HESLB or institution deadline."},
]


def _normalize_text(value: str) -> str:
    return " ".join(value.strip().lower().split())


def _nin_valid(nin: str) -> bool:
    compact = "".join(ch for ch in nin if ch.isdigit())
    return len(compact) == 20


def _institution_index() -> dict[str, str]:
    return {_normalize_text(item.name): item.code for item in INSTITUTIONS}


def _programme_index() -> dict[str, dict[str, str]]:
    output: dict[str, dict[str, str]] = {}
    for programme in PROGRAMMES:
        output[_normalize_text(programme.name)] = {
            "category": programme.category.value,
            "institution_code": programme.institution_code,
        }
    return output


def _infer_grade_points(grade: str) -> int:
    table = {"A": 5, "B": 4, "C": 3, "D": 2, "E": 1, "S": 0, "F": 0}
    return table.get(grade.strip().upper(), 0)


def _base_probability(category: str) -> int:
    return _FUNDING_PRIORITY_BY_CATEGORY.get(category, 50)


def _scan_dependency_message() -> str | None:
    missing: list[str] = []
    try:
        import cv2  # noqa: F401
    except ImportError:
        missing.append("opencv-python-headless")
    try:
        import easyocr  # noqa: F401
    except ImportError:
        missing.append("easyocr")
    try:
        import numpy  # noqa: F401
    except ImportError:
        missing.append("numpy")
    try:
        from PIL import Image, ImageOps  # noqa: F401
    except ImportError:
        missing.append("pillow")
    if missing:
        unique = ", ".join(dict.fromkeys(missing))
        return f"Document scanning is disabled until these optional packages are installed: {unique}."
    return None


def _reader() -> Any:
    # EasyOCR is only loaded when a document scan is actually requested.
    import easyocr

    return easyocr.Reader(["en"], gpu=False, verbose=False)


@dataclass(slots=True)
class LoanEligibilityResult:
    eligible: bool
    funding_probability: int
    missing_requirements: list[str]
    checks: dict[str, Any]


def evaluate_loan_eligibility(payload: dict[str, Any]) -> LoanEligibilityResult:
    nin = str(payload.get("nin", ""))
    academic_grades = payload.get("academic_grades", [])
    university_name = str(payload.get("selected_university", ""))
    programme_name = str(payload.get("selected_programme", ""))
    institution_accredited = bool(payload.get("institution_accredited", True))
    special_categories = payload.get("special_categories", {})

    missing: list[str] = []
    institutions = _institution_index()
    programmes = _programme_index()

    citizenship_ok = _nin_valid(nin)
    if not citizenship_ok:
        missing.append("Provide a valid Tanzanian NIN (20 digits).")

    grade_points = [_infer_grade_points(str(item)) for item in academic_grades]
    grade_avg = (sum(grade_points) / len(grade_points)) if grade_points else 0
    academic_ok = grade_avg >= 2.5
    if not academic_ok:
        missing.append("Academic qualification threshold not met for funding consideration.")

    university_ok = _normalize_text(university_name) in institutions
    if not university_ok:
        missing.append("Selected university is not found in the accredited institution directory.")

    programme_match = programmes.get(_normalize_text(programme_name))
    programme_ok = bool(programme_match)
    if not programme_ok:
        missing.append("Selected programme is not found in the current programme catalog.")

    course_funding_ok = False
    category = "other"
    if programme_match:
        category = programme_match["category"]
        course_funding_ok = _base_probability(category) >= 60
        if not course_funding_ok:
            missing.append("Selected course has low funding priority.")

    if not institution_accredited:
        missing.append("Institution accreditation requirement is not met.")

    special_ok = any(bool(value) for value in special_categories.values()) if special_categories else True

    score = 0
    score += 20 if citizenship_ok else 0
    score += 20 if academic_ok else 0
    score += 15 if university_ok else 0
    score += 20 if programme_ok else 0
    score += 15 if institution_accredited else 0
    score += 10 if special_ok else 0

    score = int(round(score * (_base_probability(category) / 100)))
    score = max(0, min(99, score))

    eligible = citizenship_ok and academic_ok and university_ok and programme_ok and institution_accredited and course_funding_ok
    if eligible:
        score = max(score, 75)

    return LoanEligibilityResult(
        eligible=eligible,
        funding_probability=score,
        missing_requirements=missing,
        checks={
            "citizenship_verified": citizenship_ok,
            "academic_qualification": academic_ok,
            "selected_university_eligibility": university_ok,
            "selected_course_funding_eligibility": course_funding_ok,
            "institution_accreditation": institution_accredited,
            "special_category_eligibility": special_ok,
        },
    )


def evaluate_programme_funding(programme_name: str) -> dict[str, Any]:
    programme = _programme_index().get(_normalize_text(programme_name))
    if not programme:
        return {
            "eligible": False,
            "priority": "unknown",
            "message": "The selected program is not in the current funding catalog.",
        }

    probability = _base_probability(programme["category"])
    if probability >= 75:
        message = "Your selected program is eligible for funding."
        priority = "high"
    elif probability >= 60:
        message = "Your selected program is eligible, but has moderate funding priority."
        priority = "medium"
    else:
        message = "This program has limited funding priority."
        priority = "limited"
    return {"eligible": probability >= 60, "priority": priority, "message": message, "funding_probability": probability}


def _read_image(image_path: str) -> Any:
    import cv2
    import numpy as np
    from PIL import Image, ImageOps

    with Image.open(image_path) as image:
        normalized = ImageOps.exif_transpose(image.convert("RGB"))
        return cv2.cvtColor(np.array(normalized), cv2.COLOR_RGB2BGR)


def _blur_score(gray: Any) -> float:
    import cv2

    return float(cv2.Laplacian(gray, cv2.CV_64F).var())


def _cropping_confidence(gray: Any) -> float:
    import cv2

    edges = cv2.Canny(gray, 60, 160)
    border = 12
    if gray.shape[0] <= border * 2 or gray.shape[1] <= border * 2:
        return 0.0
    top = edges[:border, :].mean()
    bottom = edges[-border:, :].mean()
    left = edges[:, :border].mean()
    right = edges[:, -border:].mean()
    return float((top + bottom + left + right) / 4.0)


def _orientation_from_boxes(boxes: list[Any]) -> str:
    if not boxes:
        return "unknown"
    tall_count = 0
    for item in boxes:
        points = item[0]
        width = abs(points[1][0] - points[0][0])
        height = abs(points[3][1] - points[0][1])
        if height > width * 1.2:
            tall_count += 1
    return "rotated" if tall_count > max(1, len(boxes) // 2) else "upright"


def _name_similarity(expected_name: str, extracted_text: str) -> float:
    expected = _normalize_text(expected_name)
    extracted = _normalize_text(extracted_text)
    try:
        from rapidfuzz import fuzz
    except ImportError:
        return round(SequenceMatcher(None, expected, extracted).ratio() * 100.0, 2)
    return float(fuzz.token_set_ratio(expected, extracted))


def scan_document(
    image_path: str,
    expected_name: str,
) -> dict[str, Any]:
    if not Path(image_path).exists():
        raise ValueError("Uploaded file not found.")

    dependency_message = _scan_dependency_message()
    if dependency_message:
        return {
            "blur_score": 0.0,
            "cropping_score": 0.0,
            "orientation": "unavailable",
            "readability_score": 0,
            "name_similarity": 0.0,
            "extracted_text_preview": "",
            "quality_flags": [dependency_message],
            "passed": False,
            "scan_available": False,
        }

    image = _read_image(image_path)
    import cv2

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blur_metric = _blur_score(gray)
    crop_metric = _cropping_confidence(gray)

    reader = _reader()
    ocr_items = reader.readtext(gray, detail=1, paragraph=False)
    extracted = " ".join(str(item[1]) for item in ocr_items).strip()
    orientation = _orientation_from_boxes(ocr_items)
    readability = min(100, int(len([token for token in extracted.split() if token]) * 3.5))
    name_similarity = _name_similarity(expected_name, extracted)

    quality_flags: list[str] = []
    if blur_metric < 85:
        quality_flags.append("Blur detected")
    if crop_metric > 25:
        quality_flags.append("Potential cropping detected")
    if orientation == "rotated":
        quality_flags.append("Potential rotation/orientation issue")
    if readability < 30:
        quality_flags.append("Low text readability")
    if name_similarity < 65:
        quality_flags.append("Name mismatch with expected student name")

    return {
        "blur_score": round(blur_metric, 2),
        "cropping_score": round(crop_metric, 2),
        "orientation": orientation,
        "readability_score": readability,
        "name_similarity": round(float(name_similarity), 2),
        "extracted_text_preview": extracted[:600],
        "quality_flags": quality_flags,
        "passed": len(quality_flags) == 0,
    }


def calculate_progress(steps: dict[str, bool]) -> dict[str, Any]:
    ordered = [
        ("account_setup", "Account setup"),
        ("personal_details", "Personal details"),
        ("academic_verification", "Academic verification"),
        ("document_upload", "Document upload"),
        ("final_submission", "Final submission"),
    ]
    completed = sum(1 for key, _ in ordered if steps.get(key))
    percent = int(round((completed / len(ordered)) * 100))
    checklist = [{"key": key, "label": label, "done": bool(steps.get(key))} for key, label in ordered]
    return {"percent_complete": percent, "checklist": checklist}


def timeline(steps: list[dict[str, Any]]) -> list[dict[str, Any]]:
    now = datetime.now(UTC)
    output: list[dict[str, Any]] = []
    for index, item in enumerate(steps, start=1):
        deadline_raw = item.get("deadline")
        days_left: int | None = None
        if deadline_raw:
            try:
                deadline = datetime.fromisoformat(str(deadline_raw)).astimezone(UTC)
                days_left = (deadline - now).days
            except ValueError:
                days_left = None
        output.append(
            {
                "step_number": index,
                "title": item.get("title", f"Step {index}"),
                "checklist": item.get("checklist", []),
                "done": bool(item.get("done", False)),
                "deadline": deadline_raw,
                "days_left": days_left,
            }
        )
    return output


def common_mistakes() -> list[dict[str, str]]:
    return list(_COMMON_MISTAKES)


def appeal_guidance(rejection_reasons: list[str]) -> dict[str, Any]:
    normalized = {_normalize_text(reason) for reason in rejection_reasons}
    eligibility = any("late" not in reason for reason in normalized)
    required_docs = [
        "Application rejection notice",
        "Corrected supporting documents",
        "NIDA/NIN verification copy",
        "Academic certificate copies",
    ]
    return {
        "possible_reasons": rejection_reasons,
        "appeal_eligibility": eligibility,
        "required_documents": required_docs,
        "next_steps": [
            "Review all rejection reasons and map each to a corrective action.",
            "Prepare corrected documents and merge into a single clear upload set.",
            "Submit appeal within the allowed HESLB/partner deadline window.",
            "Track status daily in the application dashboard.",
        ],
    }
