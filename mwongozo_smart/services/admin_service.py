"""Admin dashboard — real catalogue/user stats blended with deterministic synthetic analytics."""

from __future__ import annotations

import hashlib
import math
from collections import Counter
from datetime import date, timedelta
from typing import Any

from mwongozo_smart.core.models import ProgrammeAwardLevel
from mwongozo_smart.data.guidebook_data import PROGRAMMES
from mwongozo_smart.data.institutions import INSTITUTIONS
from mwongozo_smart.services import auth_store


def _stable_int(seed: str, lo: int, hi: int) -> int:
    digest = hashlib.md5(seed.encode("utf-8")).hexdigest()
    span = max(1, hi - lo + 1)
    return lo + int(digest[:8], 16) % span


def _award_breakdown() -> dict[str, int]:
    counts = Counter(p.award_level.value for p in PROGRAMMES)
    return {
        "bachelor": counts.get(ProgrammeAwardLevel.BACHELOR.value, 0),
        "diploma": counts.get(ProgrammeAwardLevel.DIPLOMA.value, 0),
        "certificate": counts.get(ProgrammeAwardLevel.CERTIFICATE.value, 0),
        "postgraduate": counts.get(ProgrammeAwardLevel.POSTGRADUATE.value, 0),
    }


def _category_top(n: int = 8) -> list[dict[str, Any]]:
    counts = Counter(p.category.value for p in PROGRAMMES)
    items = []
    for cat, total in counts.most_common(n):
        items.append({"category": cat, "programmes": total, "views": _stable_int(f"cat-{cat}", 120, 2400)})
    return items


def _frequent_programmes(n: int = 12) -> list[dict[str, Any]]:
    scored: list[tuple[int, Any]] = []
    for prog in PROGRAMMES:
        weight = 1
        if prog.award_level in (ProgrammeAwardLevel.CERTIFICATE, ProgrammeAwardLevel.DIPLOMA):
            weight = 3
        if prog.category.value == "health":
            weight += 2
        score = _stable_int(prog.code, 40, 900) * weight
        scored.append((score, prog))
    scored.sort(key=lambda item: item[0], reverse=True)
    output: list[dict[str, Any]] = []
    for score, prog in scored[:n]:
        inst = next((i for i in INSTITUTIONS if i.code == prog.institution_code), None)
        output.append(
            {
                "code": prog.code,
                "name": prog.name,
                "institution_code": prog.institution_code,
                "institution_name": inst.name if inst else prog.institution_code,
                "award_level": prog.award_level.value,
                "category": prog.category.value,
                "recommendations": score,
                "saves": _stable_int(f"save-{prog.code}", 8, score // 3),
            }
        )
    return output


def _daily_series(base: int, days: int = 14, label: str = "sessions") -> list[dict[str, Any]]:
    today = date.today()
    series: list[dict[str, Any]] = []
    for offset in range(days - 1, -1, -1):
        day = today - timedelta(days=offset)
        wave = 1.0 + 0.35 * math.sin(offset * 0.65 + 0.4)
        weekend = 0.82 if day.weekday() >= 5 else 1.0
        value = max(1, int(base * wave * weekend) + _stable_int(f"{label}-{day.isoformat()}", -6, 18))
        series.append({"date": day.isoformat(), "value": value})
    return series


def build_dashboard_overview() -> dict[str, Any]:
    inst_codes = {p.institution_code for p in PROGRAMMES}
    awards = _award_breakdown()
    real_users = auth_store.count_users()
    roles = auth_store.count_users_by_role()
    profiles = auth_store.count_student_profiles()

    institutions_total = max(len(INSTITUTIONS), len(inst_codes))
    programmes_total = len(PROGRAMMES)

    display_users = max(real_users, 48)
    display_sessions = max(profiles, 186)
    display_recommendations_today = _stable_int("today-rec", 42, 128)

    return {
        "generated_at": date.today().isoformat(),
        "data_mode": "live_blend",
        "catalogue": {
            "institutions": institutions_total,
            "programmes": programmes_total,
            "institutions_in_programmes": len(inst_codes),
            "award_levels": awards,
            "categories_top": _category_top(8),
        },
        "users": {
            "total_real": real_users,
            "total_display": display_users,
            "by_role_real": roles,
            "by_role_display": {
                "student": max(roles.get("student", 0), 38),
                "staff": max(roles.get("staff", 0), 6),
                "admin": max(roles.get("admin", 0), 2),
            },
            "active_today_display": _stable_int("active-today", 12, 34),
            "new_this_week_display": _stable_int("new-week", 5, 18),
        },
        "activity": {
            "student_profiles_real": profiles,
            "recommend_sessions_display": display_sessions,
            "recommendations_today_display": display_recommendations_today,
            "saved_programmes_display": _stable_int("saved-all", 64, 420),
            "necta_lookups_display": _stable_int("necta", 88, 520),
        },
        "trends": {
            "daily_recommendations": _daily_series(max(24, display_sessions // 12), 14, "rec"),
            "daily_signups": _daily_series(max(3, real_users // 3 + 2), 14, "signup"),
            "pathway_split": {
                "a_level": _stable_int("path-a", 58, 72),
                "o_level": _stable_int("path-o", 22, 38),
                "equivalent": _stable_int("path-eq", 4, 12),
            },
            "regions_top": [
                {"region": "Dar es Salaam", "share": 34},
                {"region": "Dodoma", "share": 12},
                {"region": "Mwanza", "share": 11},
                {"region": "Arusha", "share": 10},
                {"region": "Morogoro", "share": 9},
                {"region": "Zanzibar", "share": 8},
                {"region": "Mbeya", "share": 7},
                {"region": "Nyingine", "share": 9},
            ],
        },
        "frequent_programmes": _frequent_programmes(12),
        "recent_events": _synthetic_recent_events(10),
    }


def _synthetic_recent_events(n: int) -> list[dict[str, Any]]:
    templates = [
        ("recommend", "Orodha ya mapendekezo — {name}"),
        ("save", "Programme imehifadhiwa — {prog}"),
        ("lookup", "NECTA lookup — {exam}"),
        ("register", "Akaunti mpya — {email}"),
        ("login", "Kuingia — {email}"),
    ]
    names = ["Amina J.", "Baraka M.", "Christina K.", "Daudi P.", "Ester N.", "Faraji H.", "Grace L.", "Hassan O."]
    progs = [p.name[:48] for p in PROGRAMMES[:40:3]]
    events: list[dict[str, Any]] = []
    for i in range(n):
        kind, tmpl = templates[i % len(templates)]
        name = names[i % len(names)]
        prog = progs[i % len(progs)]
        exam = f"S0{i + 1:04d}/00{i + 3:04d}"
        email = f"user{i + 1}@example.co.tz"
        msg = tmpl.format(name=name, prog=prog, exam=exam, email=email)
        minutes_ago = (i + 1) * _stable_int(f"evt-{i}", 4, 55)
        events.append({"type": kind, "message": msg, "minutes_ago": minutes_ago})
    return events
