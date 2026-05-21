from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

from mwongozo_smart.services import auth_service, auth_store
from mwongozo_smart.services.admin_service import build_dashboard_overview
from mwongozo_smart.services.auth_deps import get_auth_token

admin_router = APIRouter(prefix="/admin", tags=["admin"])
_admin_ready = False


def _ensure_ready() -> None:
    global _admin_ready
    if _admin_ready:
        return
    auth_store.ensure_auth_schema()
    auth_service.seed_demo_user_if_empty()
    _admin_ready = True


def require_admin(request: Request) -> dict:
    _ensure_ready()
    user = auth_service.resolve_user(get_auth_token(request))
    if not user or user.get("role") != "admin":
        raise HTTPException(status_code=401, detail="Ingia kama admin kwanza.")
    return user


@admin_router.get("", response_class=HTMLResponse)
@admin_router.get("/", response_class=HTMLResponse)
def admin_dashboard_page() -> str:
    _ensure_ready()
    template = Path(__file__).resolve().parent / "templates" / "admin.html"
    return template.read_text(encoding="utf-8")


@admin_router.get("/api/overview")
def admin_overview(_: dict = Depends(require_admin)) -> dict:
    return build_dashboard_overview()


@admin_router.get("/api/users")
def admin_list_users(_: dict = Depends(require_admin)) -> dict:
    users = auth_store.list_users_for_admin(include_inactive=True)
    return {"items": users, "total": len(users)}


class AdminUserCreate(BaseModel):
    email: str = Field(min_length=5, max_length=255)
    password: str = Field(min_length=8, max_length=128)
    full_name: str = Field(default="", max_length=255)
    role: str = Field(default="student")


class AdminUserUpdate(BaseModel):
    email: str | None = Field(default=None, min_length=5, max_length=255)
    password: str | None = Field(default=None, min_length=8, max_length=128)
    full_name: str | None = Field(default=None, max_length=255)
    role: str | None = None
    is_active: bool | None = None


@admin_router.post("/api/users")
def admin_create_user(body: AdminUserCreate, admin: dict = Depends(require_admin)) -> dict:
    if err := auth_service.validate_email(body.email):
        raise HTTPException(status_code=400, detail=err)
    if err := auth_service.validate_password(body.password):
        raise HTTPException(status_code=400, detail=err)
    if auth_store.email_taken_by_other(body.email):
        raise HTTPException(status_code=400, detail="Barua pepe tayari imesajiliwa.")
    role = body.role if body.role in ("student", "staff", "admin") else "student"
    user = auth_store.create_user(
        email=body.email,
        password_hash=auth_service.hash_password(body.password),
        full_name=body.full_name.strip() or None,
        role=role,
    )
    return {"ok": True, "user": user}


@admin_router.patch("/api/users/{user_id}")
def admin_update_user(
    user_id: int,
    body: AdminUserUpdate,
    admin: dict = Depends(require_admin),
) -> dict:
    existing = auth_store.get_user_by_id_admin(user_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Mtumiaji hajapatikana.")
    if int(admin["id"]) == user_id and body.is_active is False:
        raise HTTPException(status_code=400, detail="Huwezi kuzima akaunti yako mwenyewe.")
    if body.email:
        if err := auth_service.validate_email(body.email):
            raise HTTPException(status_code=400, detail=err)
        if auth_store.email_taken_by_other(body.email, exclude_user_id=user_id):
            raise HTTPException(status_code=400, detail="Barua pepe tayari imesajiliwa.")
    password_hash = None
    if body.password:
        if err := auth_service.validate_password(body.password):
            raise HTTPException(status_code=400, detail=err)
        password_hash = auth_service.hash_password(body.password)
    updated = auth_store.update_user_record(
        user_id,
        email=body.email,
        full_name=body.full_name,
        role=body.role,
        is_active=body.is_active,
        password_hash=password_hash,
    )
    return {"ok": True, "user": updated}


@admin_router.delete("/api/users/{user_id}")
def admin_deactivate_user(user_id: int, admin: dict = Depends(require_admin)) -> dict:
    if int(admin["id"]) == user_id:
        raise HTTPException(status_code=400, detail="Huwezi kufuta akaunti yako mwenyewe.")
    existing = auth_store.get_user_by_id_admin(user_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Mtumiaji hajapatikana.")
    updated = auth_store.update_user_record(user_id, is_active=False)
    return {"ok": True, "user": updated}
