from __future__ import annotations

import uuid

from fastapi import Request, Response

SESSION_COOKIE = "mwongozo_sid"
AUTH_COOKIE = "mwongozo_auth"
COOKIE_MAX_AGE = 60 * 60 * 24 * 365


def get_or_set_session_id(request: Request, response: Response) -> str:
    session_id = (request.cookies.get(SESSION_COOKIE) or "").strip()
    if not session_id or len(session_id) < 8:
        session_id = str(uuid.uuid4())
        response.set_cookie(
            SESSION_COOKIE,
            session_id,
            max_age=COOKIE_MAX_AGE,
            httponly=True,
            samesite="lax",
            path="/",
        )
    return session_id


def get_auth_token(request: Request) -> str | None:
    token = (request.cookies.get(AUTH_COOKIE) or "").strip()
    return token or None


def set_auth_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        AUTH_COOKIE,
        token,
        max_age=60 * 60 * 24 * 14,
        httponly=True,
        samesite="lax",
        path="/",
    )


def clear_auth_cookie(response: Response) -> None:
    response.delete_cookie(AUTH_COOKIE, path="/")
