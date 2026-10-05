"""
Robots.txt parser and policy manager using urllib.robotparser.
"""

from typing import Dict, Optional
from urllib.parse import urlparse, urlunparse
from urllib.robotparser import RobotFileParser
import httpx

from app.utils.url_utils import get_domain
from app.utils.logger import get_logger

logger = get_logger("robots")


class RobotsManager:
    """Manages robots.txt downloading, parsing, and crawl authorization per domain."""

    def __init__(self, user_agent: str = "AlgoryxBot/1.0", enabled: bool = True):
        self.user_agent = user_agent
        self.enabled = enabled
        self._cache: Dict[str, Optional[RobotFileParser]] = {}

    async def can_fetch(self, url: str, client: httpx.AsyncClient) -> bool:
        """
        Checks whether crawling the given URL is permitted by robots.txt.

        Args:
            url: Target URL.
            client: Active httpx.AsyncClient instance.

        Returns:
            True if permitted or if robots.txt checking is disabled.
        """
        if not self.enabled:
            return True

        domain = get_domain(url)
        if not domain:
            return True

        parser = await self._get_parser(url, client)
        if parser is None:
            return True

        allowed = parser.can_fetch(self.user_agent, url)
        if not allowed:
            # Fallback to wildcard user-agent
            allowed = parser.can_fetch("*", url)

        return allowed

    async def _get_parser(self, url: str, client: httpx.AsyncClient) -> Optional[RobotFileParser]:
        """Fetches and parses robots.txt for a domain if not already cached."""
        domain = get_domain(url)
        if domain in self._cache:
            return self._cache[domain]

        parsed = urlparse(url)
        robots_url = urlunparse((parsed.scheme, parsed.netloc, "/robots.txt", "", "", ""))

        parser = RobotFileParser()
        parser.set_url(robots_url)

        try:
            logger.debug(f"Fetching robots.txt for {domain} from {robots_url}")
            resp = await client.get(robots_url, timeout=10.0, follow_redirects=True)
            if resp.status_code == 200:
                parser.parse(resp.text.splitlines())
                self._cache[domain] = parser
                logger.info(f"Loaded robots.txt for {domain}")
                return parser
            elif resp.status_code in (401, 403):
                # Forbidden robots.txt -> disallow all
                parser.parse(["User-agent: *", "Disallow: /"])
                self._cache[domain] = parser
                return parser
            else:
                self._cache[domain] = None
                return None
        except Exception as e:
            logger.debug(f"Could not load robots.txt for {domain}: {e}")
            self._cache[domain] = None
            return None

    def get_crawl_delay(self, url: str) -> Optional[float]:
        """Returns crawl-delay specified in robots.txt if available."""
        domain = get_domain(url)
        parser = self._cache.get(domain)
        if parser:
            try:
                delay = parser.crawl_delay(self.user_agent) or parser.crawl_delay("*")
                if delay:
                    return float(delay)
            except Exception:
                pass
        return None
