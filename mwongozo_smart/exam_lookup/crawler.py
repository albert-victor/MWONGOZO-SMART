from __future__ import annotations

import asyncio
import logging
from collections.abc import Awaitable, Callable, Iterable
from typing import TypeVar

import httpx

logger = logging.getLogger(__name__)

T = TypeVar("T")

DEFAULT_BASE_URL = "https://onlinesys.necta.go.tz"
DEFAULT_TIMEOUT = httpx.Timeout(45.0, connect=15.0)
DEFAULT_MAX_RETRIES = 4
DEFAULT_MIN_INTERVAL = 0.35


class NectaCseeCrawler:
    def __init__(
        self,
        base_url: str = DEFAULT_BASE_URL,
        *,
        max_retries: int = DEFAULT_MAX_RETRIES,
        min_interval_seconds: float = DEFAULT_MIN_INTERVAL,
        max_concurrency: int = 3,
        headers: dict[str, str] | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.max_retries = max(1, max_retries)
        self.min_interval = max(0.0, min_interval_seconds)
        self._sem = asyncio.Semaphore(max(1, max_concurrency))
        self._rate_lock = asyncio.Lock()
        self._last_request_at = 0.0
        self._headers = headers or {
            "User-Agent": "MwongozoSmart/0.1 (+https://github.com) httpx",
            "Accept": "text/html,application/xhtml+xml",
        }

    async def _throttle(self) -> None:
        if self.min_interval <= 0:
            return
        async with self._rate_lock:
            loop = asyncio.get_running_loop()
            now = loop.time()
            wait = self.min_interval - (now - self._last_request_at)
            if wait > 0:
                await asyncio.sleep(wait)
            self._last_request_at = loop.time()

    async def fetch_text(self, url: str) -> str:
        async with self._sem:
            await self._throttle()
            last_error: Exception | None = None
            async with httpx.AsyncClient(
                headers=self._headers,
                timeout=DEFAULT_TIMEOUT,
                follow_redirects=True,
            ) as client:
                for attempt in range(1, self.max_retries + 1):
                    try:
                        response = await client.get(url)
                        response.raise_for_status()
                        return response.text
                    except httpx.HTTPStatusError as exc:
                        if exc.response.status_code == 404:
                            raise
                        last_error = exc
                        logger.warning("NECTA fetch failed (%s/%s): %s %s", attempt, self.max_retries, url, exc)
                        await asyncio.sleep(min(2.0, 0.4 * (2 ** (attempt - 1))))
                    except httpx.HTTPError as exc:
                        last_error = exc
                        logger.warning("NECTA fetch failed (%s/%s): %s %s", attempt, self.max_retries, url, exc)
                        await asyncio.sleep(min(2.0, 0.4 * (2 ** (attempt - 1))))
            assert last_error is not None
            raise last_error

    async def fetch_text_first_ok(self, urls: Iterable[str]) -> tuple[str, str]:
        """Try each URL in order, returning ``(final_url, html)`` for the first 200 response.

        Other 4xx (notably 404) on a non-final URL are skipped so we can fall back
        to the next candidate (TETEA mixes ``.html`` and ``.htm`` per year).
        """
        url_list = list(urls)
        if not url_list:
            raise ValueError("fetch_text_first_ok requires at least one URL")
        last_error: Exception | None = None
        for index, url in enumerate(url_list):
            is_last = index == len(url_list) - 1
            try:
                return url, await self.fetch_text(url)
            except httpx.HTTPStatusError as exc:
                last_error = exc
                if exc.response.status_code == 404 and not is_last:
                    logger.info("Fallback: %s returned 404, trying next candidate", url)
                    continue
                raise
            except httpx.HTTPError as exc:
                last_error = exc
                if not is_last:
                    logger.info("Fallback: %s failed (%s), trying next candidate", url, exc)
                    continue
                raise
        assert last_error is not None
        raise last_error

    async def head_ok_any(self, urls: Iterable[str]) -> tuple[bool, str | None]:
        """Return ``(True, first_ok_url)`` if any candidate URL responds < 400."""
        for url in urls:
            if await self.head_ok(url):
                return True, url
        return False, None

    async def head_ok(self, url: str) -> bool:
        async with self._sem:
            await self._throttle()
            try:
                async with httpx.AsyncClient(
                    headers=self._headers,
                    timeout=DEFAULT_TIMEOUT,
                    follow_redirects=True,
                ) as client:
                    response = await client.head(url)
                    if response.status_code == 405:
                        response = await client.get(url)
                    return response.status_code < 400
            except httpx.HTTPError as exc:
                logger.info("NECTA probe failed for %s: %s", url, exc)
                return False

    async def gather_urls(self, urls: Iterable[str], worker: Callable[[str], Awaitable[T]]) -> list[tuple[str, T | BaseException]]:
        async def run(url: str) -> tuple[str, T | BaseException]:
            try:
                return url, await worker(url)
            except BaseException as exc:
                return url, exc

        tasks = [asyncio.create_task(run(url)) for url in urls]
        return [await task for task in tasks]


# Shared async HTTP client used for both CSEE and ACSEE lookups.
NectaHttpCrawler = NectaCseeCrawler
