from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, HTTPException, Request, Response
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel, Field

from mwongozo_smart.services import auth_service, auth_store
from mwongozo_smart.services.auth_deps import (
    AUTH_COOKIE,
    clear_auth_cookie,
    get_auth_token,
    get_or_set_session_id,
    set_auth_cookie,
)

auth_router = APIRouter(prefix="/auth", tags=["auth"])
_auth_ready = False


def _ensure_auth_ready() -> None:
    global _auth_ready
    if _auth_ready:
        return
    auth_store.ensure_auth_schema()
    auth_service.seed_demo_user_if_empty()
    _auth_ready = True


class RegisterBody(BaseModel):
    email: str = Field(min_length=5, max_length=255)
    password: str = Field(min_length=8, max_length=128)
    full_name: str = Field(default="", max_length=255)


class LoginBody(BaseModel):
    email: str = Field(min_length=5, max_length=255)
    password: str = Field(min_length=1, max_length=128)


class SavedProgrammeBody(BaseModel):
    programme_code: str = Field(min_length=2, max_length=64)
    snapshot: dict = Field(default_factory=dict)


class SavedRecommendationBody(BaseModel):
    title: str = Field(default="", max_length=255)
    input_snapshot: dict = Field(default_factory=dict)
    results_snapshot: dict = Field(default_factory=dict)
    recommend_count: int = Field(default=0, ge=0)
    direct_count: int = Field(default=0, ge=0)
    review_count: int = Field(default=0, ge=0)


def _require_logged_in_user(request: Request, response: Response) -> tuple[dict, str]:
    session_id = get_or_set_session_id(request, response)
    user = auth_service.resolve_user(get_auth_token(request))
    if not user:
        raise HTTPException(status_code=401, detail="Ingia kwanza ili kuona au kuhifadhi.")
    return user, session_id


@auth_router.get("/login", response_class=HTMLResponse)
def login_page() -> str:
    _ensure_auth_ready()
    template = Path(__file__).resolve().parent / "templates" / "login.html"
    return template.read_text(encoding="utf-8")


@auth_router.get("/admin/login", response_class=HTMLResponse)
def admin_login_page() -> str:
    _ensure_auth_ready()
    template = Path(__file__).resolve().parent / "templates" / "login-admin.html"
    return template.read_text(encoding="utf-8")


@auth_router.post("/register")
def register(body: RegisterBody, request: Request, response: Response) -> dict:
    _ensure_auth_ready()
    try:
        session_id = get_or_set_session_id(request, response)
        result = auth_service.register_user(
            email=body.email,
            password=body.password,
            full_name=body.full_name.strip() or None,
        )
        set_auth_cookie(response, result["token"])
        auth_store.attach_session_to_user(session_id, int(result["user"]["id"]))
        return {"ok": True, "user": result["user"]}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@auth_router.post("/login")
def login(body: LoginBody, request: Request, response: Response) -> dict:
    _ensure_auth_ready()
    try:
        session_id = get_or_set_session_id(request, response)
        result = auth_service.login_user(email=body.email, password=body.password)
        set_auth_cookie(response, result["token"])
        auth_store.attach_session_to_user(session_id, int(result["user"]["id"]))
        return {"ok": True, "user": result["user"]}
    except ValueError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc


@auth_router.post("/admin/login")
def admin_login(body: LoginBody, request: Request, response: Response) -> dict:
    _ensure_auth_ready()
    try:
        session_id = get_or_set_session_id(request, response)
        result = auth_service.login_user(
            email=body.email,
            password=body.password,
            required_role="admin",
        )
        set_auth_cookie(response, result["token"])
        auth_store.attach_session_to_user(session_id, int(result["user"]["id"]))
        return {"ok": True, "user": result["user"]}
    except ValueError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc


@auth_router.post("/logout")
def logout(request: Request, response: Response) -> dict:
    _ensure_auth_ready()
    auth_service.logout_user(get_auth_token(request))
    clear_auth_cookie(response)
    return {"ok": True}


@auth_router.get("/me")
def me(request: Request, response: Response) -> dict:
    get_or_set_session_id(request, response)
    user = auth_service.resolve_user(get_auth_token(request))
    return {"authenticated": user is not None, "user": user}


@auth_router.get("/saved-programmes")
def list_saved(request: Request, response: Response) -> dict:
    _ensure_auth_ready()
    user, session_id = _require_logged_in_user(request, response)
    user_id = int(user["id"])
    items = auth_store.list_saved_programmes(session_id=session_id, user_id=user_id)
    merged = []
    for item in items:
        snap = item.get("snapshot") or {}
        merged.append(
            {
                "code": item["code"],
                "name": snap.get("name", item["code"]),
                "institution_name": snap.get("institution_name", ""),
                "region": snap.get("region", ""),
                "category": snap.get("category", ""),
                "apply_url": snap.get("apply_url", ""),
                "saved_at": item.get("saved_at"),
            }
        )
    return {"items": merged}


@auth_router.post("/saved-programmes")
def save_programme(body: SavedProgrammeBody, request: Request, response: Response) -> dict:
    _ensure_auth_ready()
    user, session_id = _require_logged_in_user(request, response)
    user_id = int(user["id"])
    auth_store.upsert_saved_programme(
        session_id=session_id,
        user_id=user_id,
        programme_code=body.programme_code,
        snapshot=body.snapshot,
    )
    return {"ok": True}


@auth_router.delete("/saved-programmes/{programme_code}")
def unsave_programme(programme_code: str, request: Request, response: Response) -> dict:
    _ensure_auth_ready()
    user, session_id = _require_logged_in_user(request, response)
    user_id = int(user["id"])
    auth_store.remove_saved_programme(session_id=session_id, user_id=user_id, programme_code=programme_code)
    return {"ok": True}


@auth_router.get("/saved-recommendations")
def list_saved_recommendations(request: Request, response: Response) -> dict:
    _ensure_auth_ready()
    user, _session_id = _require_logged_in_user(request, response)
    items = auth_store.list_saved_recommendations(user_id=int(user["id"]))
    summary = []
    for item in items:
        summary.append(
            {
                "id": item["id"],
                "title": item.get("title") or "",
                "recommend_count": item.get("recommend_count") or 0,
                "direct_count": item.get("direct_count") or 0,
                "review_count": item.get("review_count") or 0,
                "saved_at": item.get("saved_at"),
                "input_snapshot": item.get("input_snapshot") or {},
            }
        )
    return {"items": summary}


@auth_router.get("/saved-recommendations/{reco_id}")
def get_saved_recommendation(reco_id: int, request: Request, response: Response) -> dict:
    _ensure_auth_ready()
    user, _session_id = _require_logged_in_user(request, response)
    item = auth_store.get_saved_recommendation(user_id=int(user["id"]), reco_id=reco_id)
    if not item:
        raise HTTPException(status_code=404, detail="Uchambuzi haujapatikana.")
    return {"item": item}


@auth_router.post("/saved-recommendations")
def save_recommendation(body: SavedRecommendationBody, request: Request, response: Response) -> dict:
    _ensure_auth_ready()
    user, session_id = _require_logged_in_user(request, response)
    reco_id = auth_store.insert_saved_recommendation(
        user_id=int(user["id"]),
        session_id=session_id,
        title=body.title,
        input_snapshot=body.input_snapshot,
        results_snapshot=body.results_snapshot,
        recommend_count=body.recommend_count,
        direct_count=body.direct_count,
        review_count=body.review_count,
    )
    return {"ok": True, "id": reco_id}


@auth_router.delete("/saved-recommendations/{reco_id}")
def delete_saved_recommendation(reco_id: int, request: Request, response: Response) -> dict:
    _ensure_auth_ready()
    user, _session_id = _require_logged_in_user(request, response)
    auth_store.remove_saved_recommendation(user_id=int(user["id"]), reco_id=reco_id)
    return {"ok": True}
