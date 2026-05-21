from __future__ import annotations

import html as html_lib
import re
import time
from dataclasses import dataclass
from typing import Any

import httpx
from bs4 import BeautifulSoup

from mwongozo_smart.core.models import Institution
from mwongozo_smart.data.institution_profiles import profile_for
from mwongozo_smart.data.live_programme_sources import candidate_urls_for_institution
from mwongozo_smart.data.sqlite_store import get_live_programme_cache, set_live_programme_cache

_CACHE_TTL_SECONDS = 12 * 60 * 60
_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)
_RAW_PROGRAMME_RE = re.compile(
    r"((?:Bachelor|Master|Doctor|Diploma|Certificate|Ordinary\s+Diploma|Advanced\s+Diploma)"
    r"[^<\n]{8,120}?)"
    r"(?:\s*-\s*[A-Z][A-Za-z0-9.&]{1,12})?",
    re.IGNORECASE,
)
_TIMEOUT = httpx.Timeout(18.0, connect=8.0)

_PROGRAMME_START = re.compile(
    r"^(?:"
    r"Bachelor(?:\s+of|\s+Degree|\s+in)?|"
    r"Master(?:\s+of|\s+in)?|"
    r"Doctor(?:\s+of|\s+in)?|"
    r"Diploma(?:\s+in|\s+of)?|"
    r"Ordinary\s+Diploma|"
    r"Advanced\s+Diploma|"
    r"Certificate(?:\s+in|\s+of)?|"
    r"Postgraduate\s+Diploma|"
    r"BSc\.?|BA\.?|LLB|MBA|BEd|B\.Ed|MD|PhD"
    r")",
    re.IGNORECASE,
)

_NOISE = re.compile(
    r"\b(?:click here|read more|apply now|home|contact us|menu|copyright|login|admission requirements)\b",
    re.IGNORECASE,
)


@dataclass(slots=True)
class LiveProgrammeSnapshot:
    institution_code: str
    programmes: list[str]
    programme_count: int
    source_url: str
    source_label: str
    fetched_at: float
    status: str
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "institution_code": self.institution_code,
            "programmes": self.programmes,
            "programme_count": self.programme_count,
            "source_url": self.source_url,
            "source_label": self.source_label,
            "fetched_at": self.fetched_at,
            "status": self.status,
            "error": self.error,
        }


def _normalize_name(text: str) -> str:
    cleaned = " ".join(text.split())
    cleaned = cleaned.strip(" ·|–—-•")
    return cleaned


def _looks_like_programme(text: str) -> bool:
    if len(text) < 12 or len(text) > 160:
        return False
    if _NOISE.search(text):
        return False
    if text.count("http") > 0:
        return False
    lower = text.lower()
    keywords = (
        "bachelor",
        "master",
        "doctor",
        "diploma",
        "certificate",
        "degree",
        "programme",
        "bsc",
        " llb",
        "mba",
        "phd",
        "ordinary diploma",
    )
    if not any(token in lower for token in keywords):
        return False
    if not _PROGRAMME_START.search(text) and "bachelor of" not in lower and "diploma in" not in lower:
        return False
    if lower.count("bachelor") > 2 or lower.count("diploma") > 2:
        return False
    parts = text.split()
    if parts and len(text) < 22:
        last = parts[-1].rstrip(".,)")
        short_ok = {"laws", "llb", "mba", "mit", "ict", "it", "phd", "md", "bba", "bsc", "nursing"}
        if len(last) <= 4 and last.lower() not in short_ok:
            return False
    if text.lower().startswith("mba-student"):
        return False
    return True


def _dedupe_longest(names: list[str]) -> list[str]:
    ordered = sorted(names, key=len, reverse=True)
    kept: list[str] = []
    seen: set[str] = set()
    for name in ordered:
        key = name.lower()
        if key in seen:
            continue
        if any(key != other.lower() and key in other.lower() for other in kept):
            continue
        kept = [other for other in kept if other.lower() not in key or other.lower() == key]
        seen.add(key)
        kept.append(name)
    return sorted(kept, key=str.lower)


def extract_programme_names(html: str) -> list[str]:
    found: list[str] = []
    seen: set[str] = set()

    def push(raw: str) -> None:
        decoded = html_lib.unescape(raw)
        name = _normalize_name(decoded)
        name = re.sub(r"\s*-\s*[A-Z][A-Za-z0-9.&]{1,14}$", "", name).strip()
        if not _looks_like_programme(name):
            return
        key = name.lower()
        if key in seen:
            return
        seen.add(key)
        found.append(name)

    for match in _RAW_PROGRAMME_RE.finditer(html):
        push(match.group(1))

    soup = BeautifulSoup(html, "html.parser")
    for option in soup.find_all("option"):
        push(option.get_text(" ", strip=True))

    for tag in soup(["script", "style", "nav", "footer", "header", "noscript"]):
        tag.decompose()

    for node in soup.find_all(["h1", "h2", "h3", "h4", "h5", "li", "a", "p", "td", "strong", "span", "div"]):
        text = _normalize_name(node.get_text(" ", strip=True))
        if not text:
            continue
        push(text)
        for part in re.split(r"[|;]", text):
            part = _normalize_name(part)
            if part:
                push(part)

    return _dedupe_longest(found)[:60]


def _fetch_html(client: httpx.Client, url: str) -> str | None:
    try:
        response = client.get(url, follow_redirects=True)
        if response.status_code >= 400:
            return None
        content_type = (response.headers.get("content-type") or "").lower()
        if "html" not in content_type and "text" not in content_type:
            return None
        return response.text
    except httpx.HTTPError:
        return None


def fetch_live_programmes(institution: Institution) -> LiveProgrammeSnapshot:
    profile = profile_for(institution, programme_count=0)
    urls = candidate_urls_for_institution(
        institution.code,
        institution.website,
        profile.get("programmes_url"),
    )
    now = time.time()
    if not urls:
        snap = LiveProgrammeSnapshot(
            institution_code=institution.code,
            programmes=[],
            programme_count=0,
            source_url="",
            source_label="Tovuti rasmi",
            fetched_at=now,
            status="no_url",
            error="No official website configured.",
        )
        set_live_programme_cache(institution.code, snap.to_dict())
        return snap

    best: list[str] = []
    best_url = urls[0]

    with httpx.Client(
        timeout=_TIMEOUT,
        headers={
            "User-Agent": _USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        },
    ) as client:
        for url in urls:
            html = _fetch_html(client, url)
            if not html:
                continue
            names = extract_programme_names(html)
            if len(names) > len(best):
                best = names
                best_url = url
            if len(best) >= 8:
                break

    status = "ok" if best else "empty"
    label = f"Tovuti rasmi · {best_url}" if best else f"Tovuti rasmi (hakuna orodha iliyotambuliwa) · {urls[0]}"
    snap = LiveProgrammeSnapshot(
        institution_code=institution.code,
        programmes=best,
        programme_count=len(best),
        source_url=best_url if best else urls[0],
        source_label=label,
        fetched_at=now,
        status=status,
        error=None if best else "Could not parse programme list from official pages.",
    )
    set_live_programme_cache(institution.code, snap.to_dict())
    return snap


def snapshot_from_cache(payload: dict[str, Any]) -> LiveProgrammeSnapshot:
    return LiveProgrammeSnapshot(
        institution_code=str(payload.get("institution_code", "")),
        programmes=list(payload.get("programmes") or []),
        programme_count=int(payload.get("programme_count") or 0),
        source_url=str(payload.get("source_url") or ""),
        source_label=str(payload.get("source_label") or "Tovuti rasmi"),
        fetched_at=float(payload.get("fetched_at") or 0),
        status=str(payload.get("status") or "unknown"),
        error=payload.get("error"),
    )


def get_cached_live(institution_code: str) -> LiveProgrammeSnapshot | None:
    payload = get_live_programme_cache(institution_code)
    if not payload:
        return None
    snap = snapshot_from_cache(payload)
    if time.time() - snap.fetched_at > _CACHE_TTL_SECONDS:
        return None
    return snap


def get_or_fetch_live(institution: Institution, *, force: bool = False) -> LiveProgrammeSnapshot:
    if not force:
        cached = get_cached_live(institution.code)
        if cached is not None:
            return cached
    return fetch_live_programmes(institution)


def refresh_live_batch(institutions: list[Institution], *, limit: int = 10, force: bool = False) -> dict[str, LiveProgrammeSnapshot]:
    refreshed: dict[str, LiveProgrammeSnapshot] = {}
    count = 0
    for institution in institutions:
        if count >= limit:
            break
        if not force and get_cached_live(institution.code) is not None:
            continue
        refreshed[institution.code] = fetch_live_programmes(institution)
        count += 1
    return refreshed


def all_cached_summaries(institution_codes: list[str]) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for code in institution_codes:
        payload = get_live_programme_cache(code)
        if payload:
            out[code] = payload
    return out
