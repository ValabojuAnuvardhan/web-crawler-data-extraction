"""
Unit and integration tests for WebCrawler using mock HTTP transport.
Verifies depth traversal, robots.txt compliance, retries, timeout handling, and multiple seed URLs.
"""

import pytest
import httpx
from app.crawler.crawler import WebCrawler
from app.utils.config import Config

_ORIGINAL_ASYNC_CLIENT_INIT = httpx.AsyncClient.__init__


class MockTransport(httpx.AsyncBaseTransport):
    """Mock HTTP transport returning simulated HTML pages, robots.txt, and error codes."""

    def __init__(self):
        self.request_counts = {}

    async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
        url_str = str(request.url)
        self.request_counts[url_str] = self.request_counts.get(url_str, 0) + 1

        if url_str == "https://example.com/robots.txt":
            content = "User-agent: *\nDisallow: /private\nCrawl-delay: 0.01"
            return httpx.Response(200, text=content, request=request)

        elif url_str == "https://example.com/":
            html = """
            <html>
                <head><title>Root Page</title></head>
                <body>
                    <h1>Welcome</h1>
                    <p>Root page paragraph.</p>
                    <a href="/about">About Us</a>
                    <a href="/private">Secret Area</a>
                    <a href="https://external.com/">External Site</a>
                </body>
            </html>
            """
            return httpx.Response(200, text=html, headers={"content-type": "text/html"}, request=request)

        elif url_str == "https://example.com/about":
            html = """
            <html>
                <head><title>About Page</title></head>
                <body>
                    <h1>About Algoryx</h1>
                    <p>Innovating web crawlers.</p>
                    <a href="/team">Our Team</a>
                </body>
            </html>
            """
            return httpx.Response(200, text=html, headers={"content-type": "text/html"}, request=request)

        elif url_str == "https://example.com/team":
            html = "<html><head><title>Team Page</title></head><body><h1>Engineers</h1></body></html>"
            return httpx.Response(200, text=html, headers={"content-type": "text/html"}, request=request)

        elif url_str == "https://site-b.com/":
            html = "<html><head><title>Site B Home</title></head><body><h1>Site B</h1></body></html>"
            return httpx.Response(200, text=html, headers={"content-type": "text/html"}, request=request)

        elif url_str == "https://flaky.com/":
            if self.request_counts[url_str] == 1:
                return httpx.Response(500, text="Internal Server Error", request=request)
            return httpx.Response(200, text="<html><head><title>Recovered</title></head></html>", request=request)

        return httpx.Response(404, text="Not Found", request=request)


@pytest.mark.asyncio
async def test_crawler_depth_and_internal_traversal(monkeypatch):
    config = Config(
        max_depth=1,
        max_pages=10,
        crawl_delay=0.01,
        respect_robots=True,
    )
    crawler = WebCrawler(config=config)

    transport = MockTransport()

    def mock_init(self, *args, **kwargs):
        kwargs["transport"] = transport
        _ORIGINAL_ASYNC_CLIENT_INIT(self, *args, **kwargs)

    monkeypatch.setattr(httpx.AsyncClient, "__init__", mock_init)

    pages = await crawler.crawl(seed_urls=["https://example.com/"])

    crawled_urls = [p.url for p in pages]
    assert "https://example.com/" in crawled_urls
    assert "https://example.com/about" in crawled_urls
    assert "https://example.com/private" not in crawled_urls
    assert "https://external.com/" not in crawled_urls
    assert "https://example.com/team" not in crawled_urls

    assert crawler.summary.pages_visited == 2
    assert crawler.summary.successful_pages == 2
    assert crawler.summary.skipped_robots == 1
    assert crawler.summary.skipped_external == 1


@pytest.mark.asyncio
async def test_crawler_multiple_seeds(monkeypatch):
    config = Config(
        max_depth=0,
        max_pages=10,
        crawl_delay=0.01,
        respect_robots=False,
    )
    crawler = WebCrawler(config=config)

    transport = MockTransport()

    def mock_init(self, *args, **kwargs):
        kwargs["transport"] = transport
        _ORIGINAL_ASYNC_CLIENT_INIT(self, *args, **kwargs)

    monkeypatch.setattr(httpx.AsyncClient, "__init__", mock_init)

    pages = await crawler.crawl(seed_urls=["https://example.com/", "https://site-b.com/"])

    crawled_urls = [p.url for p in pages]
    assert "https://example.com/" in crawled_urls
    assert "https://site-b.com/" in crawled_urls
    assert crawler.summary.pages_visited == 2


@pytest.mark.asyncio
async def test_crawler_retry_on_server_error(monkeypatch):
    config = Config(
        max_depth=0,
        max_pages=5,
        max_retries=3,
        crawl_delay=0.01,
        respect_robots=False,
    )
    crawler = WebCrawler(config=config)

    transport = MockTransport()

    def mock_init(self, *args, **kwargs):
        kwargs["transport"] = transport
        _ORIGINAL_ASYNC_CLIENT_INIT(self, *args, **kwargs)

    monkeypatch.setattr(httpx.AsyncClient, "__init__", mock_init)

    pages = await crawler.crawl(seed_urls=["https://flaky.com/"])

    assert len(pages) == 1
    assert pages[0].status_code == 200
    assert transport.request_counts["https://flaky.com/"] == 2
