"""
URL Manager responsible for frontier queue management, visited tracking, and duplicate prevention.
"""

from collections import deque
from typing import Tuple, Set, Optional, List
from app.utils.url_utils import normalize_url, is_valid_url, is_crawlable_resource


class URLManager:
    """Manages queue of URLs to crawl and prevents redundant visits."""

    def __init__(self, max_depth: int = 2):
        self.max_depth = max_depth
        self._queue: deque[Tuple[str, int]] = deque()
        self._seen: Set[str] = set()
        self._visited: Set[str] = set()

    def add_url(self, url: str, depth: int = 0) -> bool:
        """
        Adds a candidate URL to the crawl queue if valid, crawlable, and not yet seen.

        Args:
            url: Target URL string.
            depth: Traversal depth relative to seed (0 = seed).

        Returns:
            True if URL was queued, False if discarded or duplicate.
        """
        if not is_valid_url(url):
            return False

        if not is_crawlable_resource(url):
            return False

        if depth > self.max_depth:
            return False

        canonical = normalize_url(url)
        if canonical in self._seen:
            return False

        self._seen.add(canonical)
        self._queue.append((canonical, depth))
        return True

    def add_urls(self, urls: List[str], depth: int = 0) -> int:
        """Adds a list of candidate URLs, returning the count of accepted new URLs."""
        added = 0
        for u in urls:
            if self.add_url(u, depth):
                added += 1
        return added

    def get_next_url(self) -> Optional[Tuple[str, int]]:
        """Retrieves and pops the next (url, depth) item from the front of the queue."""
        if not self._queue:
            return None
        return self._queue.popleft()

    def mark_visited(self, url: str) -> None:
        """Marks a normalized URL as visited."""
        canonical = normalize_url(url)
        self._visited.add(canonical)

    def is_visited(self, url: str) -> bool:
        """Checks if a URL has already been crawled."""
        return normalize_url(url) in self._visited

    def has_urls(self) -> bool:
        """Returns True if there are pending URLs in the queue."""
        return len(self._queue) > 0

    @property
    def queue_size(self) -> int:
        """Returns number of remaining queued items."""
        return len(self._queue)

    @property
    def total_discovered(self) -> int:
        """Returns total unique URLs tracked so far."""
        return len(self._seen)

    @property
    def total_visited(self) -> int:
        """Returns count of visited URLs."""
        return len(self._visited)
