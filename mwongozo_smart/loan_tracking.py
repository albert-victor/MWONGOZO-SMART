"""HESLB loan tracking — demo profiles + eligibility synthesis via loan_assistant.

Official process references (do not invent policy):
- HESLB: https://www.heslb.go.tz/
- OLAS: https://olas.heslb.go.tz/
- NIDA (NIN): https://www.nida.go.tz/
- RITA (birth certificate certification): https://www.rita.go.tz/
"""

from __future__ import annotations

import re
from datetime import UTC, datetime
from typing import Any

from mwongozo_smart.data.institution_classify import classify_institution
from mwongozo_smart.data.institutions import INSTITUTIONS
from mwongozo_smart.loan_assistant import (
    appeal_guidance,
    common_mistakes,
    evaluate_loan_eligibility,
    evaluate_programme_funding,
)

# Demo references only — not live HESLB data.
_DEMO_REF_PATTERN = re.compile(r"^HSL-\d{4}-\d{5}$", re.IGNORECASE)

OFFICIAL_LINKS: list[dict[str, str]] = [
    {
        "label": "HESLB — Application guidelines",
        "url": "https://www.heslb.go.tz/application_guideline",
        "logo": "/static/partners/heslb.png",
    },
    {
        "label": "OLAS (Online Loan Application & Management System)",
        "url": "https://olas.heslb.go.tz/",
        "logo": "/static/partners/heslb.png",
    },
    {
        "label": "HESLB — Loan application portal",
        "url": "https://www.heslb.go.tz/loanapplication/application-link",
        "logo": "/static/partners/heslb.png",
    },
    {
        "label": "NIDA — National Identification Authority",
        "url": "https://www.nida.go.tz/",
        "logo": "/static/partners/nida.png",
    },
    {
        "label": "RITA — Registration, Insolvency and Trusteeship Agency",
        "url": "https://www.rita.go.tz/",
        "logo": "/static/partners/rita.png",
    },
]

_DEMO_PROFILES: dict[str, dict[str, Any]] = {
    # 1 — Njiani (~nusu): amekamilisha wasifu na maombi, uthibitisho bado unaendelea
    "HSL-2026-00127": {
        "student_name": {"sw": "Amina Mwanga", "en": "Amina Mwanga"},
        "scenario": {
            "sw": "Njiani — uthibitisho unaendelea (demo)",
            "en": "Mid-way — verification in progress (demo)",
        },
        "funding_status": "in_progress",
        "exam_number": "S0123/0027/2024",
        "exam_level": "a_level",
        "programme": "Bachelor of Science in Computer Science",
        "institution": "University of Dar es Salaam",
        "institution_ownership": "public",
        "nin_verified": True,
        "special_categories": {
            "orphan": False,
            "disability": False,
            "low_income": True,
            "single_parent_household": False,
        },
        "completion_percent": 54,
        "current_stage": "verification",
        "timeline": [
            {"key": "account", "status": "complete"},
            {"key": "profile", "status": "complete"},
            {"key": "submitted", "status": "complete"},
            {"key": "verification", "status": "in_progress"},
            {"key": "batch", "status": "pending"},
            {"key": "appeal", "status": "locked"},
        ],
        "batch_one_probability": 74,
        "batch_two_note": True,
        "funding_confidence": 71,
        "appeal_eligible": False,
        "academic_grades": ["B", "B", "C"],
        "risk_flags": [],
        "insights": [
            {
                "sw": "Fuatilia OLAS kila wiki — uthibitisho wa NIDA na programu ndio hatua inayofuata.",
                "en": "Check OLAS weekly — NIDA and programme verification are the next gates.",
            },
        ],
    },
    # 2 — Amekamilisha na kupata mkopo (Batch One)
    "HSL-2026-00482": {
        "student_name": {"sw": "Baraka Komba", "en": "Baraka Komba"},
        "scenario": {
            "sw": "Amekamilisha — alipatiwa mkopo Batch One (demo)",
            "en": "Completed — approved in Batch One (demo)",
        },
        "funding_status": "approved",
        "exam_number": "P0412/0182/2024",
        "exam_level": "a_level",
        "programme": "Bachelor of Education",
        "institution": "University of Dodoma",
        "institution_ownership": "public",
        "nin_verified": True,
        "special_categories": {
            "orphan": True,
            "disability": False,
            "low_income": True,
            "single_parent_household": True,
        },
        "completion_percent": 100,
        "current_stage": "batch",
        "timeline": [
            {"key": "account", "status": "complete"},
            {"key": "profile", "status": "complete"},
            {"key": "submitted", "status": "complete"},
            {"key": "verification", "status": "complete"},
            {"key": "batch", "status": "complete"},
            {"key": "appeal", "status": "complete"},
        ],
        "batch_one_probability": 93,
        "batch_two_note": False,
        "funding_confidence": 90,
        "appeal_eligible": False,
        "academic_grades": ["B", "B", "C"],
        "risk_flags": [],
        "insights": [
            {
                "sw": "Akaunti ya OLAS ilikamilika mapema — hii ilisaidia kupata Batch One.",
                "en": "Early OLAS completion helped secure Batch One placement.",
            },
            {
                "sw": "Kundi maalum (yatima + kipato cha chini) liliongeza nafasi ya kupangiwa.",
                "en": "Special categories (orphan + low income) improved allocation chances.",
            },
        ],
    },
    # 3 — Amekamilisha lakini hakupangiwa mkopo — rufaa inafunguliwa
    "HSL-2026-00991": {
        "student_name": {"sw": "Neema Sudi", "en": "Neema Sudi"},
        "scenario": {
            "sw": "Amekamilisha — hakupangiwa mkopo, rufaa inapatikana (demo)",
            "en": "Completed — not allocated; appeal pathway open (demo)",
        },
        "funding_status": "denied",
        "exam_number": "S0788/0091/2023",
        "exam_level": "a_level",
        "programme": "Bachelor of Commerce (Accountancy)",
        "institution": "Mzumbe University",
        "institution_ownership": "public",
        "nin_verified": True,
        "special_categories": {
            "orphan": False,
            "disability": False,
            "low_income": True,
            "single_parent_household": False,
        },
        "completion_percent": 100,
        "current_stage": "appeal",
        "timeline": [
            {"key": "account", "status": "complete"},
            {"key": "profile", "status": "complete"},
            {"key": "submitted", "status": "complete"},
            {"key": "verification", "status": "complete"},
            {"key": "batch", "status": "complete"},
            {"key": "appeal", "status": "in_progress"},
        ],
        "batch_one_probability": 18,
        "batch_two_note": True,
        "funding_confidence": 32,
        "appeal_eligible": True,
        "appeal_reasons": {
            "sw": [
                "Kipaumbele cha chini cha ufadhili kwa programu iliyochaguliwa",
                "Nyaraka za uthibitisho wa kipato hazikukamilika kwa wakati",
                "Muda wa mwisho wa OLAS ulikaribia — uwasilishaji ulikamilika baada ya dirisha kuisha",
            ],
            "en": [
                "Lower funding priority for the selected programme",
                "Guardian income verification documents were incomplete on time",
                "OLAS deadline was tight — final submission completed just after the window",
            ],
        },
        "academic_grades": ["C", "C", "D"],
        "risk_flags": ["low_funding_priority_course", "late_submission_risk"],
        "insights": [
            {
                "sw": "Wanafunzi wenye programu za kipaumbele cha chini mara nyingi huandaa rufaa ikiwa wana nyaraka za ziada.",
                "en": "Students in lower-priority programmes often succeed on appeal with stronger documentation.",
            },
        ],
    },
}

_TIMELINE_LABELS: dict[str, dict[str, str]] = {
    "account": {"sw": "Akaunti imeundwa", "en": "Account Created"},
    "profile": {"sw": "Wasifu umekamilika", "en": "Profile Completed"},
    "submitted": {"sw": "Maombi yamewasilishwa", "en": "Application Submitted"},
    "verification": {"sw": "Uthibitisho", "en": "Verification"},
    "batch": {"sw": "Mgawanyo wa Batch", "en": "Batch Assignment"},
    "appeal": {"sw": "Dirisha la rufaa", "en": "Appeal Window"},
}

_SCHOLARSHIP_ALTERNATIVES: list[dict[str, str]] = [
    {
        "sw": "Ufadhili wa vyuo (university scholarships)",
        "en": "University scholarships",
        "url": "https://www.heslb.go.tz/",
    },
    {
        "sw": "Misaada ya NGO na mashirika ya kiraia",
        "en": "NGO sponsorships",
        "url": "https://www.heslb.go.tz/",
    },
    {
        "sw": "Ruzuku maalum (special grants) — thibitisha kwenye tovuti rasmi",
        "en": "Special grants — confirm on official sites",
        "url": "https://www.heslb.go.tz/",
    },
    {
        "sw": "Mikopo ya elimu binafsi / ufadhili wa wazazi",
        "en": "Private education funding / parent support",
        "url": "https://www.heslb.go.tz/",
    },
]

_PARENT_GUIDANCE: list[dict[str, str]] = [
    {
        "sw": "Uthibitisho wa kipato cha mzazi/mlezi (kama inahitajika na mchakato wa HESLB).",
        "en": "Guardian income verification (when required by the HESLB process).",
    },
    {
        "sw": "Uthibitisho wa uhusiano wa mzazi/mlezi na mwanafunzi.",
        "en": "Confirmation of guardian–student relationship.",
    },
    {
        "sw": "Nambari ya simu inayopatikana kwa uthibitisho wa mawasiliano.",
        "en": "Reachable mobile number for contact verification.",
    },
    {
        "sw": "Hakikisha majina kwenye vyeti vya RITA/NECTA yanalingana na NIDA (NIN).",
        "en": "Ensure RITA/NECTA certificate names match NIDA (NIN).",
    },
]


def normalize_heslb_ref(value: str) -> str:
    return value.strip().upper()


def is_demo_reference(value: str) -> bool:
    return bool(_DEMO_REF_PATTERN.match(normalize_heslb_ref(value)))


def list_demo_references() -> list[str]:
    return sorted(_DEMO_PROFILES.keys())


def list_demo_students(lang: str = "sw") -> list[dict[str, Any]]:
    """Cards for UI demo picker — three realistic HESLB journeys."""
    if lang not in {"sw", "en"}:
        lang = "sw"
    status_labels = {
        "in_progress": {"sw": "Njiani", "en": "In progress"},
        "approved": {"sw": "Alipatiwa mkopo", "en": "Funded"},
        "denied": {"sw": "Hakupangiwa — rufaa", "en": "Not allocated — appeal"},
    }
    cards: list[dict[str, Any]] = []
    for ref in sorted(_DEMO_PROFILES.keys()):
        profile = _DEMO_PROFILES[ref]
        fs = profile.get("funding_status", "in_progress")
        cards.append(
            {
                "reference": ref,
                "name": profile["student_name"][lang],
                "scenario": profile["scenario"][lang],
                "funding_status": fs,
                "funding_status_label": status_labels.get(fs, status_labels["in_progress"])[lang],
                "completion_percent": profile.get("completion_percent", 0),
                "exam_number": profile.get("exam_number", ""),
                "programme": profile.get("programme", ""),
                "institution": profile.get("institution", ""),
            }
        )
    return cards


def _institution_is_public(name: str) -> bool:
    normalized = " ".join(name.strip().lower().split())
    for inst in INSTITUTIONS:
        if inst.name.lower() == normalized:
            return classify_institution(inst)["ownership"] == "public"
    return "university of" in normalized or "college of" in normalized


def _build_risk_flags(
    payload: dict[str, Any],
    funding: dict[str, Any],
    eligibility_checks: dict[str, Any],
) -> list[str]:
    flags: list[str] = []
    if not eligibility_checks.get("citizenship_verified"):
        flags.append("nin_verification_pending")
    if payload.get("institution_ownership") == "private" or (
        payload.get("selected_university") and not _institution_is_public(str(payload.get("selected_university", "")))
    ):
        flags.append("private_institution")
    priority = funding.get("priority", "medium")
    if priority in {"limited", "unknown"}:
        flags.append("low_funding_priority_course")
    if payload.get("late_submission_risk"):
        flags.append("late_submission_risk")
    return flags


def _special_category_boost(categories: dict[str, bool]) -> int:
    boost = 0
    if categories.get("orphan"):
        boost += 6
    if categories.get("disability"):
        boost += 5
    if categories.get("low_income"):
        boost += 4
    if categories.get("single_parent_household"):
        boost += 3
    return min(boost, 12)


def _batch_prediction_label(
    lang: str,
    demo: dict[str, Any] | None,
    batch_prob: int | None,
) -> str:
    if demo:
        fs = demo.get("funding_status")
        if fs == "approved":
            return (
                "Batch One — umepangiwa mkopo (demo)"
                if lang == "sw"
                else "Batch One — loan allocated (demo)"
            )
        if fs == "denied":
            return (
                "Hakujapangiwa — rufaa inapatikana (demo)"
                if lang == "sw"
                else "Not allocated — appeal pathway open (demo)"
            )
        if batch_prob is not None:
            return (
                f"Batch One ~{batch_prob}% (inatarajiwa, demo)"
                if lang == "sw"
                else f"Batch One ~{batch_prob}% (expected, demo)"
            )
    if batch_prob is None:
        return "—"
    return f"Batch One {batch_prob}%"


def _demo_appeal_guidance(lang: str, demo: dict[str, Any]) -> dict[str, Any]:
    reasons = list(demo.get("appeal_reasons", {}).get(lang, []))
    appeal = appeal_guidance(reasons or ["Verification pending"])
    appeal["appeal_eligibility"] = True
    appeal["possible_reasons"] = reasons
    if lang == "sw":
        appeal["required_documents"] = [
            "Arifa rasmi ya HESLB kuhusu kukataliwa / kutopangiwa",
            "Nyaraka za kipato zilizorekebishwa (mzazi/mlezi)",
            "Nakala ya NIDA/NIN na cheti cha masomo",
            "Barua ya chuo inayothibitisha uandikishaji (ikiwa inahitajika)",
        ]
        appeal["next_steps"] = [
            "Soma sababu 3 zilizoorodheshwa hapo juu na uandae nyaraka za kila moja.",
            "Pakia nyaraka zilizorekebishwa kwenye OLAS ndani ya dirisha la rufaa.",
            "Fuatilia hali ya rufaa kila siku — mfano huu unaonyesha hatua ya rufaa inayoendelea.",
            "Ikiwa rufaa itakataliwa, tathmini scholarships na mipango ya kujifadhili.",
        ]
    else:
        appeal["required_documents"] = [
            "Official HESLB notice of non-allocation",
            "Corrected guardian income verification",
            "NIDA/NIN and academic certificate copies",
            "Institution enrolment letter (if required)",
        ]
        appeal["next_steps"] = [
            "Review the three listed reasons and gather evidence for each.",
            "Upload corrected documents on OLAS within the appeal window.",
            "Track appeal status daily — this demo shows an appeal in progress.",
            "If appeal is declined, review scholarships and self-funding options.",
        ]
    return appeal


def _build_alerts(
    lang: str,
    demo: dict[str, Any] | None,
    batch_prob: int | None,
    risk_flags: list[str],
) -> list[dict[str, str]]:
    alerts: list[dict[str, str]] = []
    if demo and demo.get("funding_status") == "approved":
        alerts.append(
            {
                "level": "ok",
                "text": (
                    "Hongera (demo) — umepangiwa mkopo Batch One. Fuatilia malipo na OLAS."
                    if lang == "sw"
                    else "Congratulations (demo) — Batch One loan allocated. Monitor disbursement on OLAS."
                ),
            }
        )
    if demo and demo.get("funding_status") == "denied":
        alerts.append(
            {
                "level": "urgent",
                "text": (
                    "Hujapangiwa mkopo katika Batch One (demo). Msaada wa rufaa uko wazi — angalia kichupo cha Support."
                    if lang == "sw"
                    else "Not allocated in Batch One (demo). Appeal guidance is available — see the Support tab."
                ),
            }
        )
    if demo and demo.get("funding_status") == "in_progress":
        alerts.append(
            {
                "level": "info",
                "text": (
                    "Maombi yamefika hatua ya uthibitisho (demo) — kamilisha NIDA na nyaraka za kipato."
                    if lang == "sw"
                    else "Your application reached verification (demo) — complete NIDA and income documents."
                ),
            }
        )
    if demo and demo.get("current_stage") == "verification":
        alerts.append(
            {
                "level": "info",
                "text": (
                    "Batch One inatarajiwa ndani ya siku 9 (demo) — thibitisha kwenye OLAS."
                    if lang == "sw"
                    else "Batch One expected in ~9 days (demo) — confirm on OLAS."
                ),
            }
        )
    if "nin_verification_pending" in risk_flags or "nin_pending" in risk_flags:
        alerts.append(
            {
                "level": "warn",
                "text": (
                    "Thibitisha NIN kwenye OLAS — HESLB na NIDA zinahitaji NIN kwenye maombi."
                    if lang == "sw"
                    else "Verify NIN on OLAS — HESLB and NIDA require NIN on applications."
                ),
            }
        )
    if (
        batch_prob is not None
        and batch_prob < 65
        and not (demo and demo.get("funding_status") == "denied")
    ):
        alerts.append(
            {
                "level": "warn",
                "text": (
                    "Jiandae kwa taarifa za rufaa ikiwa uthibitisho utachelewa."
                    if lang == "sw"
                    else "Appeal preparation may be needed if verification is delayed."
                ),
            }
        )
    alerts.append(
        {
            "level": "info",
            "text": (
                "Waombaji wanaofanana kwa kawaida hupata sasisho ndani ya wiki 2 (mfano wa demo)."
                if lang == "sw"
                else "Similar applicants usually receive updates within 2 weeks (demo insight)."
            ),
        }
    )
    return alerts


def _today_actions(
    lang: str,
    demo: dict[str, Any] | None,
    risk_flags: list[str],
    funding_prob: int,
) -> list[str]:
    if demo and demo.get("appeal_eligible"):
        if lang == "sw":
            return [
                "Kagua sababu 3 za kukataliwa na uandae nyaraka za kila moja",
                "Wasilisha rufaa kwenye OLAS ndani ya dirisha la muda",
                "Angalia scholarships kama mpango wa dharura",
            ]
        return [
            "Review the three rejection reasons and prepare matching documents",
            "Submit your appeal on OLAS within the official window",
            "Review scholarship alternatives as a backup plan",
        ]
    if demo and demo.get("funding_status") == "approved":
        if lang == "sw":
            return [
                "Thibitisha taarifa za malipo kwenye OLAS",
                "Hifadhi nakala ya arifa ya Batch One",
                "Wasiliana na chuo kuhusu uandikishaji baada ya ufadhili",
            ]
        return [
            "Confirm disbursement details on OLAS",
            "Save a copy of your Batch One allocation notice",
            "Coordinate enrolment with your institution after funding",
        ]
    actions: list[str] = []
    if "nin_verification_pending" in risk_flags or (demo and not demo.get("nin_verified")):
        actions.append("Thibitisha taarifa za NIDA/NIN kwenye OLAS" if lang == "sw" else "Verify NIDA/NIN on OLAS")
    if demo and demo.get("current_stage") in {"profile", "submitted", "verification"}:
        actions.append(
            "Thibitisha programu uliyochagua kwenye chuo"
            if lang == "sw"
            else "Confirm your selected programme at the institution"
        )
    if demo and demo.get("current_stage") == "verification":
        actions.append(
            "Fuatilia tangazo la Batch One"
            if lang == "sw"
            else "Monitor Batch One release"
        )
    if funding_prob < 70 or "low_funding_priority_course" in risk_flags:
        actions.append(
            "Angalia ufadhili mbadala (scholarships)"
            if lang == "sw"
            else "Review scholarship alternatives"
        )
    if len(actions) < 3:
        actions.append(
            "Kamilisha uwasilishaji wa mwisho kwenye OLAS kabla ya deadline rasmi"
            if lang == "sw"
            else "Complete final OLAS submission before the official deadline"
        )
    return actions[:3]


def _format_timeline(raw: list[dict[str, str]], lang: str) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for index, item in enumerate(raw, start=1):
        key = item.get("key", "")
        labels = _TIMELINE_LABELS.get(key, {"sw": key, "en": key})
        status = item.get("status", "pending")
        if status == "complete":
            icon = "fa-circle-check"
        elif status in {"in_progress", "pending"}:
            icon = "fa-hourglass-half"
        else:
            icon = "fa-lock"
        output.append(
            {
                "step": index,
                "key": key,
                "title": labels.get(lang, labels["en"]),
                "status": status,
                "icon": icon,
            }
        )
    return output


def build_loan_tracking(payload: dict[str, Any]) -> dict[str, Any]:
    """Build full tracking dashboard payload (demo DB + loan_assistant scoring)."""
    lang = str(payload.get("language", "sw")).lower()
    if lang not in {"sw", "en"}:
        lang = "sw"

    heslb_ref = normalize_heslb_ref(str(payload.get("heslb_reference", "")))
    demo = _DEMO_PROFILES.get(heslb_ref) if heslb_ref else None

    programme = str(
        payload.get("selected_programme")
        or (demo or {}).get("programme")
        or ""
    )
    university = str(
        payload.get("selected_university")
        or (demo or {}).get("institution")
        or ""
    )
    exam_number = str(payload.get("exam_number") or (demo or {}).get("exam_number") or "")
    exam_level = str(payload.get("exam_level") or (demo or {}).get("exam_level") or "a_level")
    is_o_level = exam_level == "o_level"
    is_preparation = is_o_level and not demo

    special = dict(payload.get("special_categories") or (demo or {}).get("special_categories") or {})
    grades = payload.get("academic_grades") or (demo or {}).get("academic_grades") or []

    ownership = payload.get("institution_ownership") or (demo or {}).get("institution_ownership")
    if not ownership and university:
        ownership = "public" if _institution_is_public(university) else "private"

    eligibility_payload = {
        "nin": str(payload.get("nin", "")),
        "academic_grades": grades,
        "selected_university": university,
        "selected_programme": programme,
        "institution_accredited": payload.get("institution_accredited", True),
        "special_categories": special,
    }
    eligibility = evaluate_loan_eligibility(eligibility_payload)
    funding = evaluate_programme_funding(programme)

    base_prob = eligibility.funding_probability
    boost = _special_category_boost({k: bool(v) for k, v in special.items()})
    funding_probability = min(99, base_prob + boost)

    risk_flags = _build_risk_flags(
        {
            **payload,
            "selected_university": university,
            "institution_ownership": ownership,
        },
        funding,
        eligibility.checks,
    )
    if demo:
        risk_flags = list(dict.fromkeys(demo.get("risk_flags", []) + risk_flags))

    batch_one = (
        demo["batch_one_probability"]
        if demo
        else (None if is_preparation else min(95, funding_probability + 8))
    )
    if demo:
        funding_confidence = demo["funding_confidence"]
    elif batch_one is None:
        funding_confidence = min(92, funding_probability)
    else:
        funding_confidence = min(92, int(round((funding_probability + batch_one) / 2)))

    if is_preparation:
        prep_done = sum(
            1
            for ok in (
                bool(str(payload.get("nin", "")).strip()),
                bool(exam_number),
                bool(university) or bool(programme),
            )
            if ok
        )
        completion = int(round((prep_done / 3) * 100)) if prep_done else 15
    else:
        completion = demo["completion_percent"] if demo else max(20, min(95, funding_probability - 5))

    if demo:
        timeline_raw = demo["timeline"]
    elif is_preparation:
        timeline_raw = [
            {"key": "account", "status": "complete" if exam_number else "in_progress"},
            {"key": "profile", "status": "complete" if payload.get("nin") else "pending"},
            {"key": "submitted", "status": "pending"},
            {"key": "verification", "status": "pending"},
            {"key": "batch", "status": "locked"},
            {"key": "appeal", "status": "locked"},
        ]
    else:
        timeline_raw = [
            {"key": "account", "status": "complete" if payload.get("nin") else "in_progress"},
            {"key": "profile", "status": "pending"},
            {"key": "submitted", "status": "pending"},
            {"key": "verification", "status": "pending"},
            {"key": "batch", "status": "pending"},
            {"key": "appeal", "status": "locked"},
        ]

    current_stage = demo["current_stage"] if demo else ("profile" if is_preparation else "profile")
    appeal_eligible = bool(demo.get("appeal_eligible")) if demo else False

    alerts = _build_alerts(lang, demo, batch_one, risk_flags)
    today = _today_actions(lang, demo, risk_flags, funding_probability)

    course_priority_msg = funding.get("message", "")
    if lang == "sw" and funding.get("priority") == "high":
        course_priority_msg = "Programu uliyochagua ina kipaumbele cha juu cha ufadhili (kulingana na catalog ya mfumo)."
    elif lang == "sw" and funding.get("priority") == "medium":
        course_priority_msg = "Programu uliyochagua inastahili ufadhili, lakini kipaumbele ni wastani."

    scholarship_note = None
    if demo and demo.get("funding_status") == "denied":
        scholarship_note = (
            "Hujapangiwa mkopo katika Batch One (demo). Tumia msaada wa rufaa na scholarships kama njia mbadala."
            if lang == "sw"
            else "Not allocated in Batch One (demo). Use appeal guidance and scholarships as backup paths."
        )
    elif funding_probability < 70:
        scholarship_note = (
            "Uwezekano wa ufadhili ni wastani. Unaweza pia kustahili fursa za scholarships."
            if lang == "sw"
            else "Your funding probability is moderate. You may also qualify for scholarship opportunities."
        )

    if demo and demo.get("appeal_eligible"):
        appeal = _demo_appeal_guidance(lang, demo)
    elif demo and demo.get("funding_status") == "approved":
        appeal = {
            "appeal_eligibility": False,
            "possible_reasons": [],
            "required_documents": [],
            "next_steps": [
                "Huna haja ya rufaa — umeshapangiwa mkopo Batch One (demo)."
                if lang == "sw"
                else "No appeal needed — you are already allocated in Batch One (demo)."
            ],
        }
    else:
        appeal = appeal_guidance(
            [
                "Document mismatch with NIDA"
                if not eligibility.checks.get("citizenship_verified")
                else "Verification pending"
            ]
        )
        if demo:
            appeal["appeal_eligibility"] = False

    batch_prediction_label = _batch_prediction_label(lang, demo, batch_one)

    demo_profile = None
    if demo and heslb_ref:
        fs = demo.get("funding_status", "in_progress")
        status_labels = {
            "in_progress": {"sw": "Njiani", "en": "In progress"},
            "approved": {"sw": "Alipatiwa mkopo", "en": "Funded"},
            "denied": {"sw": "Hakupangiwa — rufaa", "en": "Not allocated — appeal"},
        }
        demo_profile = {
            "reference": heslb_ref,
            "name": demo["student_name"][lang],
            "scenario": demo["scenario"][lang],
            "funding_status": fs,
            "funding_status_label": status_labels.get(fs, status_labels["in_progress"])[lang],
        }

    return {
        "demo_mode": True,
        "tracker_mode": "preparation" if is_preparation else "application",
        "heslb_reference": heslb_ref or None,
        "demo_profile_found": bool(demo),
        "demo_profile": demo_profile,
        "exam_number": exam_number,
        "exam_level": exam_level,
        "programme": programme,
        "institution": university,
        "institution_ownership": ownership,
        "official_links": OFFICIAL_LINKS,
        "funding_table": {
            "heslb_reference": heslb_ref or "—",
            "application_stage": current_stage,
            "completion_percent": completion,
            "batch_prediction": batch_prediction_label,
            "funding_probability": funding_probability,
            "alerts_count": len(alerts),
            "appeal_eligible": appeal_eligible,
        },
        "course_funding": {
            "priority": funding.get("priority"),
            "message": course_priority_msg,
            "funding_probability": funding.get("funding_probability", funding_probability),
        },
        "completion_percent": completion,
        "timeline": _format_timeline(timeline_raw, lang),
        "batch_prediction": {
            "batch_one_probability": batch_one,
            "preparation_mode": is_preparation,
            "alternative_note": (
                None
                if is_preparation
                else (
                    "Unaweza kuchakatwa Batch Two ikiwa uthibitisho utachelewa."
                    if lang == "sw"
                    else "May be processed in Batch Two depending on verification delays."
                )
                if (demo or {}).get("batch_two_note", batch_one is not None and batch_one < 80)
                else None
            ),
        },
        "funding_confidence": {
            "percent": funding_confidence,
            "factors": [
                "Academic background" if lang == "en" else "Mazingira ya masomo",
                "Program selected" if lang == "en" else "Programu uliyochagua",
                "Submission timing (demo)" if lang == "en" else "Muda wa uwasilishaji (demo)",
                "Historical simulation rules" if lang == "en" else "Kanuni za mfano wa kihistoria",
            ],
        },
        "citizenship": {
            "nin_provided": bool(str(payload.get("nin", "")).strip()),
            "nin_valid": eligibility.checks.get("citizenship_verified", False),
            "note": (
                "HESLB inahitaji NIN (Nambari ya Utambulisho wa Taifa) kupitia mchakato wa NIDA."
                if lang == "sw"
                else "HESLB requires NIN (National Identification Number) through the NIDA process."
            ),
        },
        "special_categories": {
            "orphan": bool(special.get("orphan")),
            "disability": bool(special.get("disability")),
            "low_income": bool(special.get("low_income")),
            "single_parent_household": bool(special.get("single_parent_household")),
            "boost_percent": boost,
        },
        "eligibility_checks": eligibility.checks,
        "missing_requirements": eligibility.missing_requirements,
        "alerts": alerts,
        "risk_flags": risk_flags,
        "common_mistakes": common_mistakes(lang),
        "scholarship_alternatives": _SCHOLARSHIP_ALTERNATIVES,
        "scholarship_note": scholarship_note,
        "parent_guidance": _PARENT_GUIDANCE,
        "success_insights": (demo or {}).get("insights", _DEMO_PROFILES["HSL-2026-00127"]["insights"]),
        "today_actions": today,
        "appeal_guidance": appeal,
        "deadline_hints": [
            {
                "text": (
                    "Angalia dirisha la maombi kwenye heslb.go.tz — tarehe hubadilika kila mwaka."
                    if lang == "sw"
                    else "Check the application window on heslb.go.tz — dates change each year."
                ),
            },
            {
                "text": (
                    "Thibitisha nyaraka za RITA (cheti cha kuzaliwa) kama inavyoelekezwa na miongozo ya HESLB."
                    if lang == "sw"
                    else "Confirm RITA-certified documents as directed in HESLB guidelines."
                ),
            },
        ],
        "demo_references": list_demo_references(),
        "demo_students": list_demo_students(lang),
    }
