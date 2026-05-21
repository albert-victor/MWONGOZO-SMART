from __future__ import annotations

import json
from pathlib import Path

import httpx
from fastapi import APIRouter, FastAPI, HTTPException, Query, Request, Response
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse, Response
from pydantic import BaseModel, Field

from mwongozo_smart.core.calculator import csee_o_level_entry_gate, get_principal_summary
from mwongozo_smart.core.engine import RecommendationEngine
from mwongozo_smart.core.models import AdmissionPathway, ALevelScheme, StudentResult, SubjectGrade
from mwongozo_smart.data.guidebook_data import PROGRAMMES
from mwongozo_smart.data.institutions import INSTITUTIONS
from mwongozo_smart.exam_lookup import CseeResultService, StudentLookupRequest, necta_result_to_student_payload
from mwongozo_smart.exam_lookup.discovery_service import ExamDiscoveryService
from mwongozo_smart.exam_lookup.models import (
    AcseeLookupRequest,
    AcseeRecommendRequest,
    StudentResultsLookupRequest,
    StudentResultsRecommendRequest,
)
from mwongozo_smart.exam_lookup.acsee_service import (
    AcseeResultService,
    necta_acsee_to_student_result,
    student_result_to_api_input,
)
from mwongozo_smart.loan_guidance import build_loan_guidance
from mwongozo_smart.loan_tracking import (
    build_loan_tracking,
    list_demo_references,
    list_demo_students,
    normalize_heslb_ref,
)
from mwongozo_smart.utils.combination_helper import COMBINATION_MAP
from mwongozo_smart.services.auth_deps import get_auth_token, get_or_set_session_id
from mwongozo_smart.services.auth_service import resolve_user
from mwongozo_smart.services.profile_service import capture_after_recommend
from backend.auth_routes import auth_router
from backend.admin_routes import admin_router


engine = RecommendationEngine()
csee_result_service = CseeResultService()
acsee_service = AcseeResultService()
exam_discovery_service = ExamDiscoveryService()
student_router = APIRouter(prefix="/student", tags=["student"])
app = FastAPI(title="Mwongozo Smart", version="0.1.0")


def get_engine() -> RecommendationEngine:
    # Single shared engine instance used by all API routes.
    return engine


def get_csee_result_service() -> CseeResultService:
    return csee_result_service


def build_recommendation_response(
    student: StudentInput,
    limit: int,
    *,
    session_id: str | None = None,
    user_id: int | None = None,
) -> dict[str, object]:
    student_result = student.to_student_result()
    entry_ok, entry_msg, csee_div = csee_o_level_entry_gate(student_result)
    result = engine.recommend(student_result, limit=limit)
    review_limit = min(180, max(80, limit + 40))
    review = engine.review_candidates(student_result, limit=review_limit)
    combinations = engine.suggest_combinations(student_result)
    payload: dict[str, object] = {
        "input": student.model_dump(),
        "loaded_programmes": len(PROGRAMMES),
        "count": len(result),
        "recommendations": [item.model_dump(mode="json") for item in result],
        "review_candidates": [item.model_dump(mode="json") for item in review],
        "combination_suggestions": [item.model_dump(mode="json") for item in combinations],
    }
    if student_result.pathway == AdmissionPathway.O_LEVEL:
        payload["csee_division"] = csee_div
        if not entry_ok:
            payload["csee_entry_blocked"] = True
            payload["csee_entry_message"] = entry_msg
    if session_id:
        profile_meta = capture_after_recommend(
            session_id=session_id,
            user_id=user_id,
            student=student_result,
            source=student.source,
            exam_number=student.exam_number,
            exam_year=student.exam_year,
        )
        if profile_meta:
            payload["profile"] = profile_meta
    return payload


class LoanTrackRequest(BaseModel):
    heslb_reference: str = ""
    exam_number: str = ""
    exam_level: str = Field(default="a_level", pattern="^(a_level|o_level)$")
    selected_programme: str = ""
    selected_university: str = ""
    institution_ownership: str | None = None
    nin: str = ""
    academic_grades: list[str] = Field(default_factory=list)
    institution_accredited: bool = True
    late_submission_risk: bool = False
    special_categories: dict[str, bool] = Field(default_factory=dict)
    language: str = "sw"


class SubjectInput(BaseModel):
    # One subject row from the frontend form.
    subject: str
    grade: str
    principal: bool = True
    level: str = Field(default="a_level", pattern="^(a_level|o_level)$")


class StudentInput(BaseModel):
    # Full student payload sent from the browser to /recommend.
    pathway: AdmissionPathway = AdmissionPathway.A_LEVEL
    a_level_scheme: ALevelScheme = ALevelScheme.POST_2016
    a_level_subjects: list[SubjectInput] = Field(default_factory=list)
    o_level_subjects: list[SubjectInput] = Field(default_factory=list)
    combination: str | None = None
    preferred_regions: list[str] = Field(default_factory=list)
    preferred_institutions: list[str] = Field(default_factory=list)
    language: str = "english"
    equivalent_qualification: str | None = None
    csee_division: str | None = None
    notes: list[str] = Field(default_factory=list)
    exam_number: str | None = None
    exam_year: int | None = Field(default=None, ge=1990, le=2100)
    source: str = Field(default="recommend_form", max_length=64)

    def to_student_result(self) -> StudentResult:
        # Convert request JSON into the internal model used by the engine.
        return StudentResult(
            pathway=self.pathway,
            a_level_scheme=self.a_level_scheme,
            a_level_subjects=[SubjectGrade(**item.model_dump()) for item in self.a_level_subjects],
            o_level_subjects=[SubjectGrade(**item.model_dump()) for item in self.o_level_subjects],
            combination=self.combination,
            preferred_regions=self.preferred_regions,
            preferred_institutions=self.preferred_institutions,
            language=self.language,
            equivalent_qualification=self.equivalent_qualification,
            csee_division=self.csee_division,
            notes=self.notes,
        )


@app.get("/", response_class=HTMLResponse)
def home() -> str:
    # Prefer the external template so the frontend stays out of the backend file.
    template_path = Path(__file__).resolve().parent / "templates" / "home.html"
    # The homepage serves the entire frontend UI.
    sample_payload = {
        "pathway": "a_level",
        "combination": "PCB",
        "a_level_subjects": [
            {"subject": "Physics", "grade": "A", "principal": True, "level": "a_level"},
            {"subject": "Chemistry", "grade": "B", "principal": True, "level": "a_level"},
            {"subject": "Biology", "grade": "B", "principal": True, "level": "a_level"},
        ],
        "o_level_subjects": [
            {"subject": "Mathematics", "grade": "C", "principal": True, "level": "o_level"},
            {"subject": "English Language", "grade": "C", "principal": True, "level": "o_level"},
        ],
        "language": "english",
    }

    a_level_subjects_catalog = [
        "Physics",
        "Chemistry",
        "Biology",
        "General Studies",
        "Advanced Mathematics",
        "Basic Applied Mathematics",
        "Basic Mathematics",
        "English Language",
        "Kiswahili",
        "Geography",
        "History",
        "Economics",
        "Commerce",
        "Accountancy",
        "Book Keeping",
        "Nutrition",
        "Computer Studies",
    ]

    o_level_subjects_catalog = [
        "Mathematics",
        "English Language",
        "Kiswahili",
        "Biology",
        "Chemistry",
        "Physics",
        "History",
        "Geography",
        "Civics",
        "Commerce",
        "Book Keeping",
        "Economics",
        "Agriculture",
        "Computer Studies",
        "Information and Computer Studies",
        "Food and Nutrition",
        "Home Economics",
        "Fine Arts",
        "French",
        "Arabic",
        "Islamic Knowledge",
        "Bible Knowledge",
        "Civics and Moral Education",
        "Computer Applications",
        "Design and Technology",
        "Nutrition",
        "Physical Education",
        "Music",
        "Theatre Arts",
    ]

    default_o_level_subjects = [
        "Mathematics",
        "English Language",
        "Kiswahili",
        "Biology",
        "Chemistry",
        "Physics",
        "History",
        "Geography",
        "Civics",
        "Commerce",
        "Book Keeping",
        "Economics",
        "Agriculture",
        "Computer Studies",
        "Information and Computer Studies",
        "Food and Nutrition",
        "Bible Knowledge",
        "Islamic Knowledge",
        "Civics and Moral Education",
        "Nutrition",
        "Physical Education",
    ]

    grades = ["", "A", "B", "C", "D", "E", "S"]
    combo_options = "".join(f'<option value="{code}">{code}</option>' for code in sorted(COMBINATION_MAP.keys()))

    return (
        template_path.read_text(encoding="utf-8")
        .replace("__ASUBJECTS_JSON__", json.dumps(a_level_subjects_catalog))
        .replace("__OSUBJECTS_JSON__", json.dumps(o_level_subjects_catalog))
        .replace("__ODEFAULTS_JSON__", json.dumps(default_o_level_subjects))
        .replace("__GRADES_JSON__", json.dumps(grades))
        .replace("__SAMPLE_JSON__", json.dumps(sample_payload))
        .replace("__COMBO_OPTIONS__", combo_options)
    )


@app.get("/health")
def health() -> dict[str, object]:
    # Simple liveness check for deployment and debugging.
    payload: dict[str, object] = {"status": "ok", "engine": "mwongozo-smart"}
    try:
        from mwongozo_smart.db.config import catalogue_read_mode, catalogue_write_mode
        from mwongozo_smart.db.session import mysql_ping

        payload["catalogue_read"] = catalogue_read_mode().value
        payload["catalogue_write"] = catalogue_write_mode().value
        payload["mysql"] = "reachable" if mysql_ping() else "unavailable"
    except Exception:
        pass
    return payload


@app.get("/favicon.ico", include_in_schema=False)
def favicon() -> Response:
    return Response(status_code=204)


@app.get("/meta")
def meta() -> dict[str, object]:
    # Basic catalog statistics for debugging and quick inspection.
    payload: dict[str, object] = {
        "programmes_loaded": len(PROGRAMMES),
        "institutions_in_memory": len(INSTITUTIONS),
        "institutions_covered": sorted({programme.institution_code for programme in PROGRAMMES}),
        "pathways_supported": [item.value for item in AdmissionPathway],
        "a_level_schemes": [item.value for item in ALevelScheme],
    }
    try:
        from mwongozo_smart.db.config import catalogue_read_mode, catalogue_write_mode
        from mwongozo_smart.db.session import mysql_catalogue_counts

        payload["catalogue_read"] = catalogue_read_mode().value
        payload["catalogue_write"] = catalogue_write_mode().value
        payload["mysql_row_counts"] = mysql_catalogue_counts()
    except Exception:
        pass
    return payload


@app.get("/programmes")
def programmes() -> list[dict[str, object]]:
    # Public list of all loaded programmes with the most important fields.
    institution_map = {item.code: item for item in INSTITUTIONS}
    return [
        {
            "code": programme.code,
            "name": programme.name,
            "institution_code": programme.institution_code,
            "institution_name": programme.institution_name,
            "award_level": programme.award_level.value,
            "website": institution_map.get(programme.institution_code).website if institution_map.get(programme.institution_code) else None,
            "apply_url": institution_map.get(programme.institution_code).website if institution_map.get(programme.institution_code) else None,
            "cta_label": institution_map.get(programme.institution_code).cta_label if institution_map.get(programme.institution_code) else "Apply Now",
            "region": programme.region,
            "category": programme.category.value,
            "duration_years": programme.duration_years,
            "competition_tier": programme.competition_tier,
            "minimum_points": programme.admission_requirement.minimum_total_points,
        }
        for programme in PROGRAMMES
    ]


@app.post("/recommend")
def recommend(
    student: StudentInput,
    request: Request,
    response: Response,
    limit: int = Query(150, ge=1, le=250, description="Max eligible recommendations to return"),
) -> dict[str, object]:
    # Main API: evaluate the student and return ranked eligible programmes.
    try:
        session_id = get_or_set_session_id(request, response)
        user = resolve_user(get_auth_token(request))
        user_id = int(user["id"]) if user else None
        return build_recommendation_response(student, limit=limit, session_id=session_id, user_id=user_id)
    except Exception as exc:  # pragma: no cover - defensive API guard
        return JSONResponse(status_code=500, content={"detail": f"Recommendation engine failed: {exc}"})


@app.post("/student/lookup")
async def student_lookup(body: StudentLookupRequest) -> dict[str, object]:
    service = get_csee_result_service()
    try:
        result = await service.lookup(body.year, body.candidate_number)
        student_payload = necta_result_to_student_payload(result)
        response: dict[str, object] = {
            "necta": result.model_dump(mode="json"),
            "student_input": student_payload,
        }
        if body.include_recommendations:
            student_model = StudentInput.model_validate(student_payload)
            response["recommendations_bundle"] = build_recommendation_response(student_model, limit=body.recommend_limit)
        return response
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except httpx.HTTPStatusError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except httpx.RequestError as exc:
        raise HTTPException(status_code=502, detail=f"NECTA upstream request failed: {exc}") from exc


@app.post("/student/results/lookup")
async def student_results_lookup(body: StudentResultsLookupRequest) -> dict[str, object]:
    """CSEE / ACSEE lookup with automatic NECTA vs TETEA source selection (same-origin as `/`)."""
    try:
        return await exam_discovery_service.lookup(body)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except httpx.HTTPStatusError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except httpx.RequestError as exc:
        raise HTTPException(status_code=502, detail=f"Upstream request failed: {exc}") from exc


@app.post("/student/results/recommend")
async def student_results_recommend(body: StudentResultsRecommendRequest) -> dict[str, object]:
    """CSEE / ACSEE lookup then TCU recommendations."""
    try:
        return await exam_discovery_service.recommend(body, get_engine())
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except httpx.HTTPStatusError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except httpx.RequestError as exc:
        raise HTTPException(status_code=502, detail=f"Upstream request failed: {exc}") from exc


@app.post("/student/profile/recommend")
def student_profile_recommend(
    student: StudentInput,
    request: Request,
    response: Response,
    limit: int = Query(150, ge=1, le=250, description="Max eligible recommendations to return"),
) -> dict[str, object]:
    try:
        session_id = get_or_set_session_id(request, response)
        user = resolve_user(get_auth_token(request))
        user_id = int(user["id"]) if user else None
        return build_recommendation_response(student, limit=limit, session_id=session_id, user_id=user_id)
    except Exception as exc:  # pragma: no cover - defensive API guard
        return JSONResponse(status_code=500, content={"detail": f"Recommendation engine failed: {exc}"})


@app.post("/recommend/grouped")
def recommend_grouped(
    student: StudentInput,
    limit: int = Query(120, ge=1, le=250),
) -> dict[str, object]:
    # Same recommendations, but grouped by programme section.
    grouped = engine.recommend_grouped(student.to_student_result(), limit=limit)
    return {
        "input": student.model_dump(),
        "loaded_programmes": len(PROGRAMMES),
        "sections": {
            section: [item.model_dump(mode="json") for item in items]
            for section, items in grouped.items()
        },
    }


@app.get("/loan/demo-references")
def loan_demo_references(
    language: str = Query("sw", pattern="^(sw|en)$"),
) -> dict[str, object]:
    return {
        "references": list_demo_references(),
        "students": list_demo_students(language),
        "demo_mode": True,
    }


@app.get("/loan/guidance")
def loan_guidance(
    exam_level: str = Query("o_level", pattern="^(a_level|o_level)$"),
    language: str = Query("sw", pattern="^(sw|en)$"),
) -> dict[str, object]:
    return build_loan_guidance(exam_level=exam_level, language=language)


@app.post("/loan/track")
def loan_track(body: LoanTrackRequest) -> dict[str, object]:
    payload = body.model_dump()
    if body.heslb_reference:
        payload["heslb_reference"] = normalize_heslb_ref(body.heslb_reference)
    return build_loan_tracking(payload)


def _catalogue_institution_rows() -> list[dict[str, object]]:
    from mwongozo_smart.data.institution_classify import classify_institution
    from mwongozo_smart.data.institution_profiles import profile_for

    prog_counts: dict[str, int] = {}
    prog_previews: dict[str, list[str]] = {}
    for programme in PROGRAMMES:
        code = programme.institution_code
        prog_counts[code] = prog_counts.get(code, 0) + 1
        bucket = prog_previews.setdefault(code, [])
        if len(bucket) < 5:
            bucket.append(programme.name)

    rows: list[dict[str, object]] = []
    for institution in INSTITUTIONS:
        meta = classify_institution(institution)
        count = prog_counts.get(institution.code, 0)
        profile = profile_for(institution, programme_count=count)
        rows.append(
            {
                "code": institution.code,
                "name": institution.name,
                "city": institution.city,
                "region": institution.region,
                "website": institution.website,
                "apply_url": institution.apply_url or institution.website,
                "cta_label": institution.cta_label,
                "ownership": meta["ownership"],
                "kind": meta["kind"],
                "programme_count": count,
                "catalogue_programme_count": count,
                "summary": profile["summary"],
                "summary_en": profile["summary_en"],
                "programme_preview": prog_previews.get(institution.code, []),
                "programmes_url": profile["programmes_url"],
                "source_label": profile["source_label"],
                "programme_source": "catalogue",
            }
        )
    return rows


def _merge_live_row(row: dict[str, object], live_payload: dict[str, object] | None) -> dict[str, object]:
    if not live_payload:
        return row
    status = str(live_payload.get("status") or "")
    count = int(live_payload.get("programme_count") or 0)
    programmes = list(live_payload.get("programmes") or [])
    if status != "ok" or count <= 0:
        return row
    row = dict(row)
    row["programme_count"] = count
    row["programme_preview"] = programmes[:5]
    row["programme_source"] = "official"
    row["source_label"] = str(live_payload.get("source_label") or "Tovuti rasmi")
    source_url = str(live_payload.get("source_url") or "")
    if source_url:
        row["programmes_url"] = source_url
    row["live_fetched_at"] = live_payload.get("fetched_at")
    return row


@app.get("/institutions")
def institutions(
    source: str = Query(
        "auto",
        description="auto = official site when cached, else catalogue; official = catalogue only until live fetch; catalogue = TCU only",
    ),
) -> list[dict[str, object]]:
    from mwongozo_smart.services.live_programmes import get_cached_live

    rows = _catalogue_institution_rows()
    if source == "catalogue":
        return rows

    if source == "official":
        merged: list[dict[str, object]] = []
        for row in rows:
            cached = get_cached_live(str(row["code"]))
            if cached is not None and cached.status == "ok" and cached.programme_count > 0:
                merged.append(_merge_live_row(row, cached.to_dict()))
            else:
                merged.append(row)
        return merged

    merged_auto: list[dict[str, object]] = []
    for row in rows:
        cached = get_cached_live(str(row["code"]))
        merged_auto.append(_merge_live_row(row, cached.to_dict() if cached else None))
    return merged_auto


@app.get("/institutions/live-summaries")
def institutions_live_summaries(
    refresh: int = Query(0, ge=0, le=25, description="Fetch up to N institutions from official websites now"),
) -> dict[str, object]:
    from mwongozo_smart.services.live_programmes import all_cached_summaries, refresh_live_batch

    codes = [inst.code for inst in INSTITUTIONS]
    refreshed_codes: list[str] = []
    if refresh > 0:
        batch = refresh_live_batch(INSTITUTIONS, limit=refresh, force=False)
        refreshed_codes = list(batch.keys())
    summaries = all_cached_summaries(codes)
    return {
        "summaries": summaries,
        "refreshed": refreshed_codes,
        "cache_ttl_hours": 12,
    }


@app.get("/institutions/{institution_code}/programmes/live")
def institution_live_programmes(
    institution_code: str,
    force: bool = Query(False, description="Bypass cache and fetch again from official site"),
) -> dict[str, object]:
    from mwongozo_smart.services.live_programmes import get_or_fetch_live

    institution = next((item for item in INSTITUTIONS if item.code == institution_code), None)
    if institution is None:
        raise HTTPException(status_code=404, detail=f"Institution {institution_code} not found.")
    snapshot = get_or_fetch_live(institution, force=force)
    return snapshot.to_dict()


@app.exception_handler(ValueError)
def value_error_handler(_: Request, exc: ValueError) -> JSONResponse:
    # Convert validation/runtime value errors into a clean JSON response.
    return JSONResponse(status_code=400, content={"detail": str(exc)})


@student_router.post("/acsee/lookup")
async def student_acsee_lookup(payload: AcseeLookupRequest) -> dict[str, object]:
    # Resolve a candidate from official NECTA ACSEE HTML and map to the same JSON shape as /recommend.
    try:
        parsed = await acsee_service.lookup(
            payload.year,
            payload.candidate_number,
            refresh_centre_index=payload.refresh_centre_index,
        )
        student_result = necta_acsee_to_student_result(parsed)
        principal = get_principal_summary(student_result)
        return {
            "necta": parsed.model_dump(mode="json"),
            "input": student_result_to_api_input(student_result),
            "tcu_points": principal.total_points,
            "principal_count": principal.principal_count,
        }
    except ValueError as exc:
        return JSONResponse(status_code=400, content={"detail": str(exc)})
    except Exception as exc:  # pragma: no cover
        return JSONResponse(status_code=502, content={"detail": f"NECTA lookup failed: {exc}"})


@student_router.post("/acsee/recommend")
async def student_acsee_recommend(payload: AcseeRecommendRequest) -> dict[str, object]:
    # Lookup ACSEE results then run the same recommendation pipeline as POST /recommend.
    try:
        parsed = await acsee_service.lookup(
            payload.year,
            payload.candidate_number,
            refresh_centre_index=payload.refresh_centre_index,
        )
        return acsee_service.recommend_from_acsee(
            parsed,
            engine,
            limit=payload.recommend_limit,
            preferred_regions=payload.preferred_regions,
            preferred_institutions=payload.preferred_institutions,
            language=payload.language,
            a_level_scheme=payload.a_level_scheme,
        )
    except ValueError as exc:
        return JSONResponse(status_code=400, content={"detail": str(exc)})
    except Exception as exc:  # pragma: no cover
        return JSONResponse(status_code=502, content={"detail": f"NECTA recommend failed: {exc}"})


app.include_router(student_router)
app.include_router(auth_router)
app.include_router(admin_router)

_STATIC_DIR = Path(__file__).resolve().parent / "static"
if _STATIC_DIR.is_dir():
    app.mount("/static", StaticFiles(directory=str(_STATIC_DIR)), name="static")

