"""
Per-domain rate limiter to enforce polite crawling delays.
"""

import asyncio
import time
from typing import Dict
from app.utils.url_utils import get_domain


class RateLimiter:
    """Ensures polite request spacing per target domain."""

    def __init__(self, default_delay: float = 1.0):
        self.default_delay = default_delay
        self._last_request: Dict[str, float] = {}
        self._locks: Dict[str, asyncio.Lock] = {}

    def _get_lock(self, domain: str) -> asyncio.Lock:
        """Returns or instantiates a lock for domain concurrency synchronization."""
        if domain not in self._locks:
            self._locks[domain] = asyncio.Lock()
        return self._locks[domain]

    async def wait(self, url: str, delay: float = None) -> None:
        """
        Pauses execution if necessary to respect the required delay since
        the last request to the same domain.

        Args:
            url: Target URL to crawl.
            delay: Optional custom delay (e.g. from robots.txt).
        """
        domain = get_domain(url)
        if not domain:
            return

        required_delay = delay if delay is not None else self.default_delay
        if required_delay <= 0:
            return

        lock = self._get_lock(domain)
        async with lock:
            last = self._last_request.get(domain, 0.0)
            now = time.time()
            elapsed = now - last

            if elapsed < required_delay:
                wait_time = required_delay - elapsed
                await asyncio.sleep(wait_time)

            self._last_request[domain] = time.time()
