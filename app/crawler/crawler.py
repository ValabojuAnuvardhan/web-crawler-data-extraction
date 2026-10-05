"""
Core WebCrawler engine using httpx.AsyncClient, URLManager, RobotsManager, and RateLimiter.
"""

import asyncio
import time
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Callable, Set
import httpx

from app.models.page import CrawledPage, ExtractedContent
from app.crawler.url_manager import URLManager
from app.crawler.robots import RobotsManager
from app.crawler.rate_limiter import RateLimiter
from app.parser.html_parser import HTMLParser
from app.utils.config import Config, get_default_config
from app.utils.url_utils import get_domain, is_internal_url, normalize_url
from app.utils.logger import get_logger

logger = get_logger("crawler")


@dataclass
class CrawlSummary:
    """Summary statistics for a completed crawl session."""
    seed_urls: List[str]
    max_depth: int
    pages_discovered: int = 0
    pages_visited: int = 0
    successful_pages: int = 0
    failed_pages: int = 0
    skipped_urls: int = 0
    skipped_robots: int = 0
    skipped_external: int = 0
    execution_time: float = 0.0

    def print_summary(self) -> None:
        """Prints a readable summary report to stdout."""
        print("\n" + "=" * 50)
        print("                 CRAWL SUMMARY")
        print("=" * 50)
        print(f"Seed URLs:         {', '.join(self.seed_urls)}")
        print(f"Max Depth:         {self.max_depth}")
        print(f"Pages Discovered:  {self.pages_discovered}")
        print(f"Pages Visited:     {self.pages_visited}")
        print(f"Successful:        {self.successful_pages}")
        print(f"Failed:            {self.failed_pages}")
        print(f"Skipped (Total):   {self.skipped_urls}")
        print(f"  - Robots.txt:    {self.skipped_robots}")
        print(f"  - External:      {self.skipped_external}")
        print(f"Execution Time:    {self.execution_time:.2f} seconds")
        throughput = (
            round(self.pages_visited / self.execution_time, 2)
            if self.execution_time > 0 else 0
        )
        print(f"Throughput:        {throughput} pages/sec")
        print("=" * 50 + "\n")


class WebCrawler:
    """
    Scalable asynchronous web crawler with politeness, depth control,
    and automatic internal-link recursive discovery.
    """

    def __init__(self, config: Optional[Config] = None):
        self.config = config or get_default_config()

        self.url_manager = URLManager(max_depth=self.config.max_depth)
        self.robots_manager = RobotsManager(
            user_agent=self.config.user_agent,
            enabled=self.config.respect_robots,
        )
        self.rate_limiter = RateLimiter(default_delay=self.config.crawl_delay)
        self.parser = HTMLParser()

        self.crawled_pages: List[CrawledPage] = []
        self._seed_domains: Set[str] = set()

    async def crawl(
        self,
        seed_urls: List[str],
        on_page_crawled: Optional[Callable[[CrawledPage], None]] = None,
    ) -> List[CrawledPage]:
        """
        Executes the recursive crawl starting from one or more seed URLs.

        Args:
            seed_urls: List of initial entry URLs.
            on_page_crawled: Optional callback function triggered after each page is processed.

        Returns:
            List of all crawled CrawledPage instances.
        """
        start_time = time.time()
        self.crawled_pages.clear()

        # Seed the queue and register origin domains
        for url in seed_urls:
            canonical = normalize_url(url)
            self.url_manager.add_url(canonical, depth=0)
            domain = get_domain(canonical)
            if domain:
                self._seed_domains.add(domain)

        logger.info(
            f"Starting crawl for {len(seed_urls)} seed(s) [max_depth={self.config.max_depth}, "
            f"max_pages={self.config.max_pages}, delay={self.config.crawl_delay}s]"
        )

        timeout = httpx.Timeout(
            timeout=self.config.request_timeout,
            connect=min(10.0, self.config.request_timeout),
        )
        headers = {
            "User-Agent": self.config.user_agent,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
        }

        limits = httpx.Limits(
            max_connections=self.config.max_concurrency * 2,
            max_keepalive_connections=self.config.max_concurrency,
        )

        semaphore = asyncio.Semaphore(self.config.max_concurrency)
        skipped_robots = 0
        skipped_external = 0

        async with httpx.AsyncClient(headers=headers, timeout=timeout, limits=limits) as client:
            while self.url_manager.has_urls() and len(self.crawled_pages) < self.config.max_pages:
                item = self.url_manager.get_next_url()
                if item is None:
                    break

                url, depth = item

                # Check robots.txt
                if self.config.respect_robots:
                    allowed = await self.robots_manager.can_fetch(url, client)
                    if not allowed:
                        logger.info(f"Skipping disallowed URL by robots.txt: {url}")
                        skipped_robots += 1
                        continue

                # Wait for rate limiter delay
                custom_delay = self.robots_manager.get_crawl_delay(url)
                await self.rate_limiter.wait(url, delay=custom_delay)

                async with semaphore:
                    page = await self._fetch_and_process(client, url, depth)

                self.url_manager.mark_visited(url)
                self.crawled_pages.append(page)

                if on_page_crawled:
                    try:
                        on_page_crawled(page)
                    except Exception as cb_err:
                        logger.warning(f"Error in on_page_crawled callback: {cb_err}")

                # Enqueue internal child links if depth allows
                if page.content and depth < self.config.max_depth:
                    for link in page.content.links:
                        # Must be strictly internal
                        if not any(is_internal_url(link.url, seed) for seed in seed_urls):
                            skipped_external += 1
                            continue

                        self.url_manager.add_url(link.url, depth=depth + 1)

        elapsed = time.time() - start_time
        successful = sum(1 for p in self.crawled_pages if 200 <= p.status_code < 300)
        failed = len(self.crawled_pages) - successful

        self.summary = CrawlSummary(
            seed_urls=seed_urls,
            max_depth=self.config.max_depth,
            pages_discovered=self.url_manager.total_discovered,
            pages_visited=len(self.crawled_pages),
            successful_pages=successful,
            failed_pages=failed,
            skipped_urls=skipped_robots + skipped_external,
            skipped_robots=skipped_robots,
            skipped_external=skipped_external,
            execution_time=elapsed,
        )

        logger.info(
            f"Crawl completed: {self.summary.pages_visited} pages visited in {elapsed:.2f}s."
        )
        return self.crawled_pages

    async def _fetch_and_process(
        self, client: httpx.AsyncClient, url: str, depth: int
    ) -> CrawledPage:
        """
        Downloads a webpage with retries and timeout management, then parses content.
        """
        logger.info(f"Fetching [depth={depth}]: {url}")
        status_code = 0
        content_length = 0
        error_msg = None
        extracted_content = None
        final_url = url
        response_time_ms = 0.0

        for attempt in range(1, self.config.max_retries + 1):
            t_start = time.perf_counter()
            try:
                resp = await client.get(url, follow_redirects=True)
                response_time_ms = (time.perf_counter() - t_start) * 1000
                status_code = resp.status_code
                final_url = str(resp.url)
                content_length = len(resp.content)

                # Retry on server error status codes (5xx)
                if 500 <= status_code < 600 and attempt < self.config.max_retries:
                    wait_delay = attempt * 1.5
                    logger.warning(
                        f"Server error HTTP {status_code} for {url} (attempt {attempt}). Retrying in {wait_delay}s..."
                    )
                    await asyncio.sleep(wait_delay)
                    continue

                if 200 <= status_code < 300:
                    # Parse only HTML responses
                    content_type = resp.headers.get("content-type", "").lower()
                    if "text/html" in content_type or "application/xhtml" in content_type or not content_type:
                        extracted_content = self.parser.parse(resp.text, base_url=final_url)
                else:
                    error_msg = f"HTTP {status_code}"

                break

            except httpx.TimeoutException:
                response_time_ms = (time.perf_counter() - t_start) * 1000
                error_msg = f"Timeout after {self.config.request_timeout}s"
                logger.warning(f"Timeout on {url} (attempt {attempt}/{self.config.max_retries})")
            except httpx.ConnectError as e:
                response_time_ms = (time.perf_counter() - t_start) * 1000
                error_msg = f"Connection error: {e}"
                logger.warning(f"Connection failed on {url} (attempt {attempt}/{self.config.max_retries}): {e}")
            except httpx.HTTPError as e:
                response_time_ms = (time.perf_counter() - t_start) * 1000
                error_msg = f"HTTP client error: {e}"
                logger.warning(f"HTTP error on {url}: {e}")
            except Exception as e:
                response_time_ms = (time.perf_counter() - t_start) * 1000
                error_msg = f"Unexpected error: {e}"
                logger.error(f"Unexpected error crawling {url}: {e}")
                break

            if attempt < self.config.max_retries:
                await asyncio.sleep(attempt * 1.0)

        return CrawledPage(
            url=url,
            canonical_url=final_url,
            depth=depth,
            status_code=status_code,
            response_time_ms=response_time_ms,
            content_length=content_length,
            content=extracted_content,
            error=error_msg,
        )
